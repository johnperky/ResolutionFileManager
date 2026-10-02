from __future__ import annotations

# Copyright (C) 2026 JohnPerky
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import hashlib
import csv
import fnmatch
import functools
import html
import os
import queue
import re
import shutil
import sqlite3
import struct
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
import tkinter.font as tkfont
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinterdnd2 import ASK, COPY, DND_FILES, LINK, MOVE, REFUSE_DROP, TkinterDnD
from send2trash import send2trash
from PIL import ExifTags, Image, ImageDraw, ImageFont, ImageOps, ImageSequence
try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:  # Keep source startup graceful if optional dependencies are incomplete.
    FileSystemEventHandler = object
    Observer = None


VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v", ".wmv", ".mpg", ".mpeg"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp", ".gif", ".heic", ".heif", ".avif"}
SUPPORTED_EXTENSIONS = VIDEO_EXTENSIONS | IMAGE_EXTENSIONS
APP_VERSION = "12.3.0"
SUPPORT_URL = "https://buymeacoffee.com/johnperky"
CODEC_LABELS = {"h264": "H.264", "hevc": "H.265 / HEVC", "av1": "AV1", "vp9": "VP9", "vp8": "VP8", "mpeg4": "MPEG-4", "mpeg2video": "MPEG-2", "mjpeg": "Motion JPEG"}
COLOR_LABEL_HEX = {"Red": "#d9534f", "Yellow": "#d8aa18", "Green": "#4b9b57", "Blue": "#4a90e2", "Purple": "#8c62b8"}
TRANSCODE_PRESETS = {
    "H.264 MP4 (compatible)": {"suffix": "H264", "extension": ".mp4", "arguments": ("-map", "0:v:0", "-map", "0:a?", "-map_metadata", "0", "-c:v", "libx264", "-preset", "medium", "-crf", "{crf}", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart")},
    "H.265 MP4 (smaller)": {"suffix": "H265", "extension": ".mp4", "arguments": ("-map", "0:v:0", "-map", "0:a?", "-map_metadata", "0", "-c:v", "libx265", "-preset", "medium", "-crf", "{crf}", "-tag:v", "hvc1", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart")},
    "AV1 MKV (smallest)": {"suffix": "AV1", "extension": ".mkv", "arguments": ("-map", "0:v:0", "-map", "0:a?", "-map_metadata", "0", "-c:v", "libsvtav1", "-preset", "8", "-crf", "{crf}", "-pix_fmt", "yuv420p", "-c:a", "libopus", "-b:a", "128k")},
    "720p H.264 proxy": {"suffix": "Proxy", "extension": ".mp4", "arguments": ("-map", "0:v:0", "-map", "0:a?", "-map_metadata", "0", "-vf", "scale=-2:min(720\\,ih)", "-c:v", "libx264", "-preset", "veryfast", "-crf", "{crf}", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart")},
    "Remux to MKV (no re-encoding)": {"suffix": "Remux", "extension": ".mkv", "arguments": ("-map", "0", "-map_metadata", "0", "-c", "copy")},
}
TRANSCODE_PRESET_CODEC_FAMILY = {
    "H.264 MP4 (compatible)": "h264",
    "H.265 MP4 (smaller)": "hevc",
    "AV1 MKV (smallest)": "av1",
    "720p H.264 proxy": "h264",
    "Remux to MKV (no re-encoding)": None,
}
TRANSCODE_ENGINE_ENCODERS = {
    "NVIDIA NVENC": {"h264": "h264_nvenc", "hevc": "hevc_nvenc", "av1": "av1_nvenc"},
    "Intel Quick Sync": {"h264": "h264_qsv", "hevc": "hevc_qsv", "av1": "av1_qsv"},
    "AMD AMF": {"h264": "h264_amf", "hevc": "hevc_amf", "av1": "av1_amf"},
    "VA-API (Linux)": {"h264": "h264_vaapi", "hevc": "hevc_vaapi", "av1": "av1_vaapi"},
}
TRANSCODE_AUTOMATIC = "Automatic (recommended)"
TRANSCODE_SOFTWARE = "Software / CPU"
TRANSCODE_SOURCE_RESOLUTION = "Keep source resolution"
TRANSCODE_RESOLUTIONS = {
    TRANSCODE_SOURCE_RESOLUTION: None,
    "1080p": 1080,
    "720p": 720,
}


def application_data_directory() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    path = base / "ResolutionFileManager"
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return default


def save_json(path: Path, value) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temporary.replace(path)


@dataclass(frozen=True)
class MediaItem:
    path: Path
    width: int | None
    height: int | None
    size: int
    modified: float
    duration: float | None = None
    error: str = ""
    codec: str = "Unknown"
    bitrate: int | None = None
    frame_rate: float | None = None
    audio_codec: str = "—"
    audio_channels: int | None = None
    pixel_format: str = "—"
    hdr: str = "SDR"
    rating: int = 0
    color_label: str = ""
    tags: tuple[str, ...] = ()

    @property
    def resolution(self) -> str:
        return f"{self.width} × {self.height}" if self.width and self.height else "Unknown"

    @property
    def pixels(self) -> int:
        return (self.width or 0) * (self.height or 0)

    @property
    def megabytes_per_minute(self) -> float | None:
        if not self.duration or self.duration <= 0 or self.path.suffix.lower() not in VIDEO_EXTENSIONS:
            return None
        return (self.size / (1024 * 1024)) / (self.duration / 60)


def jpeg_dimensions(path: Path) -> tuple[int, int]:
    """Read JPEG dimensions without third-party packages."""
    with path.open("rb") as stream:
        if stream.read(2) != b"\xff\xd8":
            raise ValueError("Not a JPEG file")
        while True:
            byte = stream.read(1)
            if not byte:
                break
            if byte != b"\xff":
                continue
            while byte == b"\xff":
                byte = stream.read(1)
            marker = byte[0]
            if marker in (0xD8, 0xD9):
                continue
            raw_length = stream.read(2)
            if len(raw_length) != 2:
                break
            length = struct.unpack(">H", raw_length)[0]
            if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                data = stream.read(5)
                if len(data) != 5:
                    break
                height, width = struct.unpack(">HH", data[1:])
                return width, height
            stream.seek(length - 2, os.SEEK_CUR)
    raise ValueError("JPEG dimensions not found")


def bundled_command(name: str) -> str:
    bundled_root = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    executable = bundled_root / (f"{name}.exe" if sys.platform == "win32" else name)
    return str(executable) if executable.exists() else name


def apply_application_icon(window: tk.Misc) -> None:
    """Apply the packaged media-manager icon to the main and child windows."""
    bundled_root = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    icon_path = bundled_root / "app_icon.png"
    try:
        if icon_path.exists():
            photo = tk.PhotoImage(file=icon_path)
            window.iconphoto(True, photo)
            window._application_icon_photo = photo
    except (tk.TclError, OSError):
        pass


def codec_label(value: object) -> str:
    name = str(value or "").strip().lower()
    return CODEC_LABELS.get(name, name.upper() if name else "Unknown")


def parse_rate(value: object) -> float | None:
    try:
        numerator, denominator = str(value).split("/", 1)
        return float(numerator) / float(denominator) if float(denominator) else None
    except (ValueError, TypeError, ZeroDivisionError):
        return None


def probed_metadata(path: Path) -> dict:
    command = [
        bundled_command("ffprobe"), "-v", "error",
        "-show_entries", "stream=index,codec_type,codec_name,width,height,duration,bit_rate,avg_frame_rate,channels,pix_fmt,color_transfer:format=duration,bit_rate",
        "-of", "json", str(path),
    ]
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    result = subprocess.run(command, capture_output=True, text=True, timeout=30, creationflags=flags)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "ffprobe could not read the file")
    metadata = json.loads(result.stdout)
    streams = metadata.get("streams", [])
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    if not video:
        raise ValueError("No video stream found")
    raw_duration = video.get("duration") or metadata.get("format", {}).get("duration")
    duration = float(raw_duration) if raw_duration not in (None, "N/A") else None
    raw_bitrate = video.get("bit_rate") or metadata.get("format", {}).get("bit_rate")
    transfer = str(video.get("color_transfer", "")).lower()
    return {
        "width": int(video["width"]), "height": int(video["height"]), "duration": duration,
        "codec": codec_label(video.get("codec_name")),
        "bitrate": int(raw_bitrate) if raw_bitrate not in (None, "N/A") else None,
        "frame_rate": parse_rate(video.get("avg_frame_rate")),
        "audio_codec": codec_label(audio.get("codec_name")) if audio else "—",
        "audio_channels": int(audio["channels"]) if audio and audio.get("channels") else None,
        "pixel_format": str(video.get("pix_fmt") or "—"),
        "hdr": "HDR" if transfer in {"smpte2084", "arib-std-b67"} else "SDR",
    }


def inspect_media(path: Path) -> MediaItem:
    stat = path.stat()
    try:
        if path.suffix.lower() in {".jpg", ".jpeg"}:
            width, height = jpeg_dimensions(path)
            data = {"width": width, "height": height, "duration": None, "codec": "JPEG"}
        elif path.suffix.lower() in IMAGE_EXTENSIONS:
            data = probed_metadata(path)
            data["duration"] = None
            data["codec"] = path.suffix[1:].upper()
        else:
            data = probed_metadata(path)
        return MediaItem(path, data["width"], data["height"], stat.st_size, stat.st_mtime, data.get("duration"), "", data.get("codec", "Unknown"), data.get("bitrate"), data.get("frame_rate"), data.get("audio_codec", "—"), data.get("audio_channels"), data.get("pixel_format", "—"), data.get("hdr", "SDR"))
    except Exception as exc:
        return MediaItem(path, None, None, stat.st_size, stat.st_mtime, None, str(exc))


class MetadataCache:
    """Thread-safe, indexed media metadata store with legacy JSON migration."""

    SCHEMA = 2

    def __init__(self, path: Path, legacy_json_path: Path | None = None):
        self.path = path
        self.legacy_json_path = legacy_json_path
        self.lock = threading.RLock()
        self.dirty = False
        self.pending_writes = 0
        self.connection = sqlite3.connect(path, check_same_thread=False, timeout=15)
        # A single application connection avoids cross-thread WAL contention;
        # NORMAL synchronous mode keeps local incremental commits efficient.
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self.connection.execute("PRAGMA temp_store=MEMORY")
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS media_metadata (
                path TEXT PRIMARY KEY,
                schema_version INTEGER NOT NULL,
                size INTEGER NOT NULL,
                modified REAL NOT NULL,
                width INTEGER,
                height INTEGER,
                duration REAL,
                error TEXT NOT NULL DEFAULT '',
                codec TEXT NOT NULL DEFAULT 'Unknown',
                bitrate INTEGER,
                frame_rate REAL,
                audio_codec TEXT NOT NULL DEFAULT '—',
                audio_channels INTEGER,
                pixel_format TEXT NOT NULL DEFAULT '—',
                hdr TEXT NOT NULL DEFAULT 'SDR'
            )
        """)
        self.connection.execute("CREATE INDEX IF NOT EXISTS media_metadata_size_modified ON media_metadata(size, modified)")
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS file_hashes (
                path TEXT PRIMARY KEY,
                size INTEGER NOT NULL,
                modified REAL NOT NULL,
                quick_hash TEXT,
                full_sha256 TEXT
            )
        """)
        self.connection.execute("CREATE INDEX IF NOT EXISTS file_hashes_size_quick ON file_hashes(size, quick_hash)")
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS image_hashes (
                path TEXT PRIMARY KEY,
                size INTEGER NOT NULL,
                modified REAL NOT NULL,
                difference_hash TEXT NOT NULL
            )
        """)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS user_labels (
                path TEXT PRIMARY KEY,
                rating INTEGER NOT NULL DEFAULT 0 CHECK(rating BETWEEN 0 AND 5),
                color_label TEXT NOT NULL DEFAULT ''
            )
        """)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS user_tags (
                path TEXT NOT NULL,
                tag TEXT NOT NULL COLLATE NOCASE,
                PRIMARY KEY(path, tag)
            )
        """)
        self.connection.execute("CREATE INDEX IF NOT EXISTS user_tags_tag ON user_tags(tag)")
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS integrity_checks (
                path TEXT PRIMARY KEY,
                size INTEGER NOT NULL,
                modified REAL NOT NULL,
                status TEXT NOT NULL,
                details TEXT NOT NULL DEFAULT '',
                checked REAL NOT NULL
            )
        """)
        self.connection.execute("CREATE TABLE IF NOT EXISTS cache_state (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        self.connection.commit()
        self.migrated_count = self._migrate_legacy_json()

    @staticmethod
    def _item_from_row(path: Path, stat: os.stat_result, row: tuple) -> MediaItem:
        return MediaItem(path, row[0], row[1], stat.st_size, stat.st_mtime, row[2], row[3] or "", row[4] or "Unknown", row[5], row[6], row[7] or "—", row[8], row[9] or "—", row[10] or "SDR")

    def _migrate_legacy_json(self) -> int:
        already_migrated = self.connection.execute("SELECT 1 FROM cache_state WHERE key = 'legacy_json_migrated'").fetchone()
        if already_migrated or not self.legacy_json_path or not self.legacy_json_path.exists():
            return 0
        records = load_json(self.legacy_json_path, {})
        if not isinstance(records, dict):
            return 0
        rows = []
        for key, value in records.items():
            if not isinstance(value, dict) or value.get("_schema") != self.SCHEMA:
                continue
            try:
                rows.append((key, self.SCHEMA, int(value["size"]), float(value["modified"]), value.get("width"), value.get("height"), value.get("duration"), value.get("error", ""), value.get("codec", "Unknown"), value.get("bitrate"), value.get("frame_rate"), value.get("audio_codec", "—"), value.get("audio_channels"), value.get("pixel_format", "—"), value.get("hdr", "SDR")))
            except (KeyError, TypeError, ValueError):
                continue
        if rows:
            with self.connection:
                self.connection.executemany("""
                    INSERT OR REPLACE INTO media_metadata
                    (path, schema_version, size, modified, width, height, duration, error, codec, bitrate, frame_rate, audio_codec, audio_channels, pixel_format, hdr)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, rows)
        with self.connection:
            self.connection.execute("INSERT OR REPLACE INTO cache_state(key, value) VALUES ('legacy_json_migrated', '1')")
        return len(rows)

    def inspect(self, path: Path) -> tuple[MediaItem, bool]:
        stat = path.stat()
        key = str(path.resolve())
        with self.lock:
            cached = self.connection.execute("""
                SELECT width, height, duration, error, codec, bitrate, frame_rate,
                       audio_codec, audio_channels, pixel_format, hdr
                FROM media_metadata
                WHERE path = ? AND schema_version = ? AND size = ? AND modified = ?
            """, (key, self.SCHEMA, stat.st_size, stat.st_mtime)).fetchone()
        if cached:
            return self.with_user_labels(self._item_from_row(path, stat, cached)), True
        item = inspect_media(path)
        with self.lock:
            self.connection.execute("""
                INSERT OR REPLACE INTO media_metadata
                (path, schema_version, size, modified, width, height, duration, error, codec, bitrate, frame_rate, audio_codec, audio_channels, pixel_format, hdr)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (key, self.SCHEMA, item.size, item.modified, item.width, item.height, item.duration, item.error, item.codec, item.bitrate, item.frame_rate, item.audio_codec, item.audio_channels, item.pixel_format, item.hdr))
            self.dirty = True
            self.pending_writes += 1
            if self.pending_writes >= 250:
                self.connection.commit()
                self.dirty = False
                self.pending_writes = 0
        return self.with_user_labels(item), False

    def with_user_labels(self, item: MediaItem) -> MediaItem:
        key = str(item.path.resolve())
        with self.lock:
            label = self.connection.execute("SELECT rating, color_label FROM user_labels WHERE path = ?", (key,)).fetchone()
            tags = tuple(row[0] for row in self.connection.execute("SELECT tag FROM user_tags WHERE path = ? ORDER BY tag COLLATE NOCASE", (key,)))
        return replace(item, rating=int(label[0]) if label else 0, color_label=str(label[1]) if label else "", tags=tags)

    def set_rating(self, paths: list[Path], rating: int):
        rating = max(0, min(5, int(rating)))
        with self.lock, self.connection:
            for path in paths:
                key = str(path.resolve())
                self.connection.execute("INSERT INTO user_labels(path, rating) VALUES (?, ?) ON CONFLICT(path) DO UPDATE SET rating=excluded.rating", (key, rating))

    def set_color_label(self, paths: list[Path], color: str):
        color = color if color in {"Red", "Yellow", "Green", "Blue", "Purple"} else ""
        with self.lock, self.connection:
            for path in paths:
                key = str(path.resolve())
                self.connection.execute("INSERT INTO user_labels(path, color_label) VALUES (?, ?) ON CONFLICT(path) DO UPDATE SET color_label=excluded.color_label", (key, color))

    def set_tags(self, paths: list[Path], tags: list[str]):
        unique = {}
        for tag in tags:
            value = tag.strip()
            if value: unique.setdefault(value.casefold(), value)
        cleaned = sorted(unique.values(), key=str.casefold)
        with self.lock, self.connection:
            for path in paths:
                key = str(path.resolve())
                self.connection.execute("DELETE FROM user_tags WHERE path = ?", (key,))
                self.connection.executemany("INSERT INTO user_tags(path, tag) VALUES (?, ?)", ((key, tag) for tag in cleaned))

    def move_user_data(self, old_path: Path, new_path: Path):
        old_key, new_key = str(old_path.resolve()), str(new_path.resolve())
        with self.lock, self.connection:
            label = self.connection.execute("SELECT rating, color_label FROM user_labels WHERE path = ?", (old_key,)).fetchone()
            if label:
                self.connection.execute("INSERT OR REPLACE INTO user_labels(path, rating, color_label) VALUES (?, ?, ?)", (new_key, *label))
                self.connection.execute("DELETE FROM user_labels WHERE path = ?", (old_key,))
            self.connection.execute("UPDATE OR REPLACE user_tags SET path = ? WHERE path = ?", (new_key, old_key))

    def copy_user_data(self, old_path: Path, new_path: Path):
        old_key, new_key = str(old_path.resolve()), str(new_path.resolve())
        with self.lock, self.connection:
            label = self.connection.execute("SELECT rating, color_label FROM user_labels WHERE path = ?", (old_key,)).fetchone()
            if label: self.connection.execute("INSERT OR REPLACE INTO user_labels(path, rating, color_label) VALUES (?, ?, ?)", (new_key, *label))
            self.connection.execute("DELETE FROM user_tags WHERE path = ?", (new_key,))
            self.connection.execute("INSERT INTO user_tags(path, tag) SELECT ?, tag FROM user_tags WHERE path = ?", (new_key, old_key))

    def delete_user_data(self, path: Path):
        key = str(path.resolve())
        with self.lock, self.connection:
            self.connection.execute("DELETE FROM user_labels WHERE path = ?", (key,))
            self.connection.execute("DELETE FROM user_tags WHERE path = ?", (key,))

    def cached_integrity(self, item: MediaItem) -> tuple[str, str, float] | None:
        with self.lock:
            row = self.connection.execute("SELECT status, details, checked FROM integrity_checks WHERE path = ? AND size = ? AND modified = ?", (str(item.path.resolve()), item.size, item.modified)).fetchone()
        return (str(row[0]), str(row[1]), float(row[2])) if row else None

    def store_integrity(self, item: MediaItem, status: str, details: str, checked: float | None = None):
        with self.lock, self.connection:
            self.connection.execute("INSERT OR REPLACE INTO integrity_checks(path, size, modified, status, details, checked) VALUES (?, ?, ?, ?, ?, ?)", (str(item.path.resolve()), item.size, item.modified, status, details, checked or time.time()))

    def is_current(self, path: Path) -> bool:
        try:
            stat = path.stat()
            key = str(path.resolve())
        except OSError:
            return False
        with self.lock:
            return self.connection.execute(
                "SELECT 1 FROM media_metadata WHERE path = ? AND schema_version = ? AND size = ? AND modified = ?",
                (key, self.SCHEMA, stat.st_size, stat.st_mtime),
            ).fetchone() is not None

    def save(self):
        with self.lock:
            if not self.dirty:
                return
            self.connection.commit()
            self.dirty = False
            self.pending_writes = 0

    def count(self) -> int:
        with self.lock:
            return int(self.connection.execute("SELECT COUNT(*) FROM media_metadata").fetchone()[0])

    def cached_file_hash(self, path: Path, size: int, modified: float, full: bool = False) -> str | None:
        column = "full_sha256" if full else "quick_hash"
        with self.lock:
            row = self.connection.execute(
                f"SELECT {column} FROM file_hashes WHERE path = ? AND size = ? AND modified = ?",
                (str(path.resolve()), size, modified),
            ).fetchone()
        return row[0] if row and row[0] else None

    def store_file_hash(self, path: Path, size: int, modified: float, value: str, full: bool = False) -> bool:
        try:
            current = path.stat()
        except OSError:
            return False
        if current.st_size != size or current.st_mtime != modified:
            return False
        column = "full_sha256" if full else "quick_hash"
        invalidate_full = "" if full else ", full_sha256 = NULL"
        with self.lock:
            self.connection.execute(f"""
                INSERT INTO file_hashes(path, size, modified, {column}) VALUES (?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    size = excluded.size,
                    modified = excluded.modified,
                    {column} = excluded.{column}
                    {invalidate_full}
            """, (str(path.resolve()), size, modified, value))
            self.dirty = True
            self.pending_writes += 1
            if self.pending_writes >= 250:
                self.connection.commit()
                self.dirty = False
                self.pending_writes = 0
        return True

    def cached_image_hash(self, item: MediaItem) -> int | None:
        with self.lock:
            row = self.connection.execute("SELECT difference_hash FROM image_hashes WHERE path = ? AND size = ? AND modified = ?", (str(item.path.resolve()), item.size, item.modified)).fetchone()
        try: return int(row[0], 16) if row else None
        except (TypeError, ValueError): return None

    def store_image_hash(self, item: MediaItem, value: int) -> bool:
        try: current = item.path.stat()
        except OSError: return False
        if current.st_size != item.size or current.st_mtime != item.modified: return False
        with self.lock:
            self.connection.execute("INSERT OR REPLACE INTO image_hashes(path, size, modified, difference_hash) VALUES (?, ?, ?, ?)", (str(item.path.resolve()), item.size, item.modified, f"{value:016x}"))
            self.dirty = True; self.pending_writes += 1
            if self.pending_writes >= 250:
                self.connection.commit(); self.dirty = False; self.pending_writes = 0
        return True

    def prune(self) -> int:
        with self.lock:
            stale = [row[0] for row in self.connection.execute("SELECT path FROM media_metadata") if not Path(row[0]).exists()]
            for key in stale:
                self.connection.execute("DELETE FROM media_metadata WHERE path = ?", (key,))
                self.connection.execute("DELETE FROM file_hashes WHERE path = ?", (key,))
                self.connection.execute("DELETE FROM image_hashes WHERE path = ?", (key,))
                self.connection.execute("DELETE FROM integrity_checks WHERE path = ?", (key,))
            if stale:
                self.connection.commit()
            self.dirty = False
            self.pending_writes = 0
        return len(stale)

    def clear(self) -> int:
        with self.lock:
            count = self.count()
            self.connection.execute("DELETE FROM media_metadata")
            self.connection.execute("DELETE FROM file_hashes")
            self.connection.execute("DELETE FROM image_hashes")
            self.connection.execute("DELETE FROM integrity_checks")
            self.connection.commit()
            self.dirty = False
            self.pending_writes = 0
        return count

    def close(self):
        with self.lock:
            if self.dirty:
                self.connection.commit()
            self.connection.close()


def human_size(value: int) -> str:
    amount = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if amount < 1024 or unit == "TB":
            return f"{amount:.1f} {unit}" if unit != "B" else f"{int(amount)} B"
        amount /= 1024
    return f"{amount:.1f} TB"


def human_duration(value: float | None) -> str:
    if value is None:
        return "—"
    total = max(0, round(value))
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"


class PaneChangeHandler(FileSystemEventHandler):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def on_any_event(self, event):
        self.callback(bool(getattr(event, "is_directory", False)))


PERFORMANCE_PROFILES = {
    "Quiet": {"scan_workers": 1, "thumbnail_workers": 1, "preview_fps": 8.0, "interactive_delay": 2.0},
    "Balanced": {"scan_workers": 2, "thumbnail_workers": 3, "preview_fps": 12.0, "interactive_delay": 0.75},
    "Fast": {"scan_workers": min(8, max(4, os.cpu_count() or 4)), "thumbnail_workers": 5, "preview_fps": 15.0, "interactive_delay": 0.0},
}


class WorkloadController:
    """Throttle expensive background starts while an interactive preview is active."""

    def __init__(self, profile: str = "Balanced"):
        self.profile = profile if profile in PERFORMANCE_PROFILES else "Balanced"
        self.condition = threading.Condition()
        self.interactive_sources: set[str] = set()
        self.last_background_start = 0.0

    @property
    def settings(self) -> dict:
        return PERFORMANCE_PROFILES[self.profile]

    def set_profile(self, profile: str):
        with self.condition:
            self.profile = profile if profile in PERFORMANCE_PROFILES else "Balanced"
            self.condition.notify_all()

    def set_interactive(self, source: str, active: bool):
        with self.condition:
            if active:
                self.interactive_sources.add(source)
            else:
                self.interactive_sources.discard(source)
            self.condition.notify_all()

    def wait_for_background(self, cancel_event: threading.Event | None = None) -> bool:
        with self.condition:
            while self.interactive_sources and self.settings["interactive_delay"] > 0:
                if cancel_event and cancel_event.is_set():
                    return False
                delay = float(self.settings["interactive_delay"])
                remaining = delay - (time.monotonic() - self.last_background_start)
                if remaining <= 0:
                    self.last_background_start = time.monotonic()
                    return True
                self.condition.wait(timeout=min(0.2, remaining))
            self.last_background_start = time.monotonic()
            return not cancel_event or not cancel_event.is_set()


def compact_relative_path(path: Path, maximum: int) -> str:
    """Keep the filename visible when a recursive relative path is too long."""
    text = str(path)
    if len(text) <= maximum:
        return text
    parts = path.parts
    if len(parts) > 2:
        candidate = str(Path(parts[0]) / "…" / parts[-1])
        if len(candidate) <= maximum:
            return candidate
    filename = path.name
    if len(filename) + 2 <= maximum:
        return f"…{os.sep}{filename}"
    # Extremely long filenames cannot fit in full; retain both identifying ends.
    remaining = max(8, maximum - 3)
    left = max(4, remaining // 3)
    return f"{filename[:left]}…{filename[-(remaining-left):]}"


class FilePane(ttk.Frame):
    def __init__(self, master: tk.Misc, title: str, start_path: Path, active_callback, transfer_callback, preview_callback, preview_toggle_callback, metadata_cache: MetadataCache, saved_state: dict | None = None):
        super().__init__(master, padding=8)
        saved_state = saved_state or {}
        self.title = title
        self.app = master.winfo_toplevel()
        self.current_path = start_path
        self.metadata_cache = metadata_cache
        self.items: dict[str, MediaItem] = {}
        # Ticks are an action queue, independent from the ordinary highlight
        # used for browsing and previewing.  They intentionally are not saved
        # in workspaces and are cleared when this pane navigates elsewhere.
        self.checked_paths: set[str] = set()
        self.results: queue.Queue = queue.Queue()
        self.scan_generation = 0
        self.scan_active = False
        self.last_view_refresh = 0.0
        self.sort_column = saved_state.get("sort_column", "name")
        self.sort_reverse = bool(saved_state.get("sort_reverse", False))
        self.sort_label_var = tk.StringVar()
        self.active_callback = active_callback
        self.transfer_callback = transfer_callback
        self.preview_callback = preview_callback
        self.preview_toggle_callback = preview_toggle_callback
        self.preview_enabled_var = tk.BooleanVar(value=False)
        self.inspector_enabled_var = tk.BooleanVar(value=bool(saved_state.get("inspector_enabled", False)))
        self.live_updates_var = tk.BooleanVar(value=bool(saved_state.get("live_updates", False)))
        self.live_observer = None
        self.live_refresh_job: str | None = None
        self.live_tree_changed = False
        self.recursive_var = tk.BooleanVar(value=bool(saved_state.get("recursive", False)))
        self.show_videos_var = tk.BooleanVar(value=bool(saved_state.get("show_videos", True)))
        self.show_images_var = tk.BooleanVar(value=bool(saved_state.get("show_images", True)))
        self.outlier_sensitivity_var = tk.StringVar(value=saved_state.get("outlier_sensitivity", "Large (1.75×)"))
        self.search_var = tk.StringVar(value=saved_state.get("search", ""))
        self.advanced_filters = dict(saved_state.get("advanced_filters", {}))
        self.view_mode_var = tk.StringVar(value=saved_state.get("view_mode", "Details"))
        self.thumbnail_size_var = tk.StringVar(value=saved_state.get("thumbnail_size", "Medium"))
        self.thumbnail_generation = 0
        self.thumbnail_page = 0
        self.thumbnail_page_size_mode = str(saved_state.get("thumbnail_page_size_mode", "Auto"))
        if self.thumbnail_page_size_mode not in {"Auto", "200", "500", "1000"}: self.thumbnail_page_size_mode = "Auto"
        self.thumbnail_page_size = 500
        self.thumbnail_page_size_var = tk.StringVar(value=self.thumbnail_page_size_mode)
        self.thumbnail_browse_mode = str(saved_state.get("thumbnail_browse_mode", "Continuous"))
        if self.thumbnail_browse_mode not in {"Continuous", "Paged"}: self.thumbnail_browse_mode = "Continuous"
        self.thumbnail_browse_mode_var = tk.StringVar(value=self.thumbnail_browse_mode)
        self.thumbnail_filter_signature = None
        self.thumbnail_layout_job: str | None = None
        self.thumbnail_columns = 0
        self.thumbnail_images = []
        self.thumbnail_cells: dict[str, tk.Widget] = {}
        self.virtual_thumbnail_cards: dict[int, tuple] = {}
        self.virtual_row_height = 0
        self.virtual_cell_width = 0
        self.virtual_dimensions = (160, 110)
        self.virtual_resize_anchor: int | None = None
        self.visible_items: list[MediaItem] = []
        self.view_generation = 0
        self.preferred_selection_path: str | None = None
        self.scan_cancel_event = threading.Event()
        self.dragged_column: str | None = None
        self.column_drag_moved = False
        self.resizing_column: str | None = None
        self.resize_start_x = 0
        self.resize_start_width = 0
        self.right_drag_completed = False
        initial_path = start_path.expanduser().resolve()
        self.navigation_history: list[Path] = [initial_path]
        self.navigation_index = 0

        heading = ttk.Frame(self)
        heading.pack(fill="x", pady=(0, 6))
        ttk.Label(heading, text=title, style="PaneTitle.TLabel").pack(side="left")
        view_box = ttk.Combobox(heading, textvariable=self.view_mode_var, state="readonly", width=11, values=("Details", "Thumbnails"))
        view_box.pack(side="left", padx=8)
        view_box.bind("<<ComboboxSelected>>", lambda _event: self.set_view_mode(self.view_mode_var.get()))
        size_box = ttk.Combobox(heading, textvariable=self.thumbnail_size_var, state="readonly", width=8, values=("Small", "Medium", "Large"))
        size_box.pack(side="left")
        size_box.bind("<<ComboboxSelected>>", lambda _event: self.render_thumbnail_grid())
        ttk.Checkbutton(heading, text="▶ Preview", style="PaneToggle.Toolbutton", variable=self.preview_enabled_var, command=self.toggle_preview).pack(side="left", padx=(10, 0))
        ttk.Checkbutton(heading, text="ⓘ Info", style="PaneToggle.Toolbutton", variable=self.inspector_enabled_var, command=self.toggle_inspector).pack(side="left", padx=(7, 0))
        ttk.Button(heading, text="Browse…", command=self.choose_folder).pack(side="right")

        navigation = ttk.Frame(self)
        navigation.pack(fill="x", pady=(0, 5))
        self.back_button = ttk.Button(navigation, text="←", width=4, command=self.go_back)
        self.back_button.pack(side="left")
        self.forward_button = ttk.Button(navigation, text="→", width=4, command=self.go_forward)
        self.forward_button.pack(side="left", padx=(4, 0))
        self.up_button = ttk.Button(navigation, text="↑", width=4, command=self.go_up)
        self.up_button.pack(side="left", padx=(4, 0))
        ttk.Button(navigation, text="↻", width=4, command=self.refresh_browser).pack(side="left", padx=(4, 0))
        self.drag_selected_button = ttk.Button(navigation, text="↗ Drag selected", style="PaneToggle.Toolbutton")
        self.drag_selected_button.pack(side="right")
        self.drag_selected_button.drag_source_register(1, DND_FILES)
        self.drag_selected_button.dnd_bind("<<DragInitCmd>>", self.start_selected_drag)
        self.drag_selected_button.dnd_bind("<<DragEndCmd>>", self.end_file_drag)

        self.path_var = tk.StringVar(value=str(start_path))
        path_entry = ttk.Entry(self, textvariable=self.path_var)
        path_entry.pack(fill="x", pady=(0, 6))
        path_entry.bind("<Return>", lambda _event: self.navigate(Path(self.path_var.get())))

        type_row = ttk.Frame(self)
        type_row.pack(fill="x", pady=(0, 5))
        ttk.Label(type_row, text="Show:").pack(side="left")
        ttk.Checkbutton(type_row, text="Videos", variable=self.show_videos_var, command=self.refresh_view).pack(side="left", padx=(5, 0))
        ttk.Checkbutton(type_row, text="Images", variable=self.show_images_var, command=self.refresh_view).pack(side="left", padx=(5, 0))
        ttk.Checkbutton(type_row, text="Include subfolders", variable=self.recursive_var, command=self.recursive_changed).pack(side="right")
        ttk.Checkbutton(type_row, text="Live", variable=self.live_updates_var, command=self.toggle_live_updates).pack(side="right", padx=(0, 8))
        ttk.Label(type_row, text="Find:").pack(side="left", padx=(12, 2))
        search_entry = ttk.Entry(type_row, textvariable=self.search_var, width=18)
        search_entry.pack(side="left")
        search_entry.bind("<KeyRelease>", lambda _event: self.refresh_view())

        filter_row = ttk.Frame(self)
        filter_row.pack(fill="x", pady=(0, 6))
        ttk.Label(filter_row, text="Resolution:").pack(side="left")
        self.filter_var = tk.StringVar(value=saved_state.get("resolution_filter", "All"))
        self.filter_box = ttk.Combobox(filter_row, textvariable=self.filter_var, state="readonly", width=18)
        self.filter_box.pack(side="left", padx=5)
        self.filter_box.bind("<<ComboboxSelected>>", lambda _event: self.refresh_view())
        ttk.Button(filter_row, text="Select matching", command=self.select_matching).pack(side="left")
        ttk.Button(filter_row, text="More filters…", command=self.edit_advanced_filters).pack(side="left", padx=(5, 0))
        ttk.Button(filter_row, text="Select size outliers", command=self.select_size_outliers).pack(side="left", padx=5)
        self.outlier_box = ttk.Combobox(filter_row, textvariable=self.outlier_sensitivity_var, state="readonly", width=15, values=("Moderate (1.4×)", "Large (1.75×)", "Extreme (2.5×)"))
        self.outlier_box.pack(side="left")

        columns = ("name", "codec", "resolution", "duration", "size", "rate", "fps", "modified", "type", "bitrate", "audio", "hdr", "pixels", "color", "tags", "rating")
        content = ttk.Panedwindow(self, orient="horizontal")
        self.content_panes = content
        content.pack(fill="both", expand=True)

        folder_frame = ttk.Frame(content)
        self.folder_tree = ttk.Treeview(folder_frame, show="tree", selectmode="browse", height=10)
        folder_scroll = ttk.Scrollbar(folder_frame, orient="vertical", command=self.folder_tree.yview)
        self.folder_tree.configure(yscrollcommand=folder_scroll.set)
        folder_scroll.pack(side="right", fill="y")
        self.folder_tree.pack(fill="both", expand=True)
        self.folder_tree.bind("<<TreeviewOpen>>", self.expand_folder)
        self.folder_tree.bind("<<TreeviewSelect>>", self.folder_selected)
        self.folder_tree.bind("<Button-3>", self.show_folder_context)

        media_frame = ttk.Frame(content)
        self.media_frame = media_frame
        details_frame = ttk.Frame(media_frame)
        self.details_frame = details_frame
        labels = {"name": "Name / relative path", "rating": "Rating", "color": "Label", "tags": "Tags", "type": "Type", "codec": "Codec", "resolution": "Resolution", "pixels": "Megapixels", "size": "File size", "rate": "MB/min", "bitrate": "Bitrate", "fps": "FPS", "audio": "Audio", "hdr": "HDR", "modified": "Date modified", "duration": "Video length"}
        widths = {"name": 230, "rating": 75, "color": 75, "tags": 170, "type": 60, "codec": 105, "resolution": 110, "pixels": 85, "size": 85, "rate": 75, "bitrate": 90, "fps": 60, "audio": 110, "hdr": 55, "modified": 135, "duration": 90}
        saved_widths = saved_state.get("column_widths", {})
        if isinstance(saved_widths, dict):
            valid_saved = [value for value in saved_widths.values() if isinstance(value, (int, float))]
            if len(valid_saved) >= len(columns) - 1 and sum(value <= 65 for value in valid_saved) >= len(columns) - 2:
                saved_widths = {}
        else:
            saved_widths = {}
        if self.sort_column not in columns: self.sort_column = "name"
        saved_order = saved_state.get("column_order", [])
        compatible_order = list(columns)
        if isinstance(saved_order, list):
            compatible_order = [column for column in saved_order if column in columns]
            compatible_order.extend(column for column in columns if column not in compatible_order)
        self.tree = ttk.Treeview(details_frame, columns=columns, displaycolumns=compatible_order, show="tree headings", selectmode="extended")
        self.tree.heading("#0", text="✓", command=self.toggle_all_checks)
        self.tree.column("#0", width=38, minwidth=38, stretch=False, anchor="center")
        for column in columns:
            self.tree.heading(column, text=labels[column], command=lambda c=column: self.set_sort(c))
            try: saved_width = int(saved_widths.get(column, widths[column]))
            except (ValueError, TypeError): saved_width = widths[column]
            self.tree.column(column, width=max(55, min(2000, saved_width)), minwidth=55, stretch=False, anchor="w" if column == "name" else "center")
        scroll = ttk.Scrollbar(details_frame, orient="vertical", command=self.tree.yview)
        horizontal_scroll = ttk.Scrollbar(details_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll.set, xscrollcommand=horizontal_scroll.set)
        scroll.pack(side="right", fill="y")
        horizontal_scroll.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<ButtonPress-1>", self.media_button_pressed)
        self.tree.bind("<B1-Motion>", self.media_button_dragged)
        self.tree.bind("<ButtonRelease-1>", self.media_button_released)
        self.tree.bind("<Motion>", self.media_header_motion)
        self.tree.bind("<Leave>", lambda _event: self.tree.configure(cursor="") if not self.dragged_column and not self.resizing_column else None)
        self.tree.bind("<ButtonRelease-3>", self.show_context_menu)
        self.tree.bind("<<TreeviewSelect>>", self.selection_changed)
        self.tree.bind("<Double-1>", self.open_on_double_click)
        self.tree.bind("<F2>", lambda _event: self.rename_selected())
        self.tree.bind("<space>", self.toggle_focused_check)
        # Registering the entire Treeview for left-button DnD steals native
        # header resize/reorder drags after a few pixels. Details view uses
        # right-button file dragging; thumbnail cards can safely use left drag.
        self.tree.drag_source_register(3, DND_FILES)
        self.tree.dnd_bind("<<DragInitCmd>>", self.start_file_drag)
        self.tree.dnd_bind("<<DragEndCmd>>", self.end_file_drag)
        self.tree.drop_target_register(DND_FILES)
        self.tree.dnd_bind("<<Drop:DND_Files>>", self.drop_files_in_current_folder)
        self.folder_tree.drop_target_register(DND_FILES)
        self.folder_tree.dnd_bind("<<Drop:DND_Files>>", self.drop_files_on_folder_tree)

        self.thumbnail_frame = ttk.Frame(media_frame)
        thumbnail_navigation = ttk.Frame(self.thumbnail_frame)
        thumbnail_navigation.pack(fill="x", pady=(0, 4))
        self.thumbnail_sort_button = ttk.Menubutton(thumbnail_navigation, textvariable=self.sort_label_var)
        self.thumbnail_sort_menu = tk.Menu(self.thumbnail_sort_button, tearoff=False)
        self.thumbnail_sort_button.configure(menu=self.thumbnail_sort_menu)
        self.build_sort_menu()
        self.thumbnail_sort_button.pack(side="left", padx=(0, 6))
        ttk.Button(thumbnail_navigation, text="✓ All shown", command=self.toggle_all_checks).pack(side="left", padx=(0, 6))
        mode_box = ttk.Combobox(thumbnail_navigation, textvariable=self.thumbnail_browse_mode_var, state="readonly", width=10, values=("Continuous", "Paged"))
        mode_box.pack(side="left", padx=(0, 6)); mode_box.bind("<<ComboboxSelected>>", self.change_thumbnail_browse_mode)
        self.thumbnail_previous_button = ttk.Button(thumbnail_navigation, text="←", width=4, command=lambda: self.change_thumbnail_page(-1))
        self.thumbnail_previous_button.pack(side="left")
        self.thumbnail_next_button = ttk.Button(thumbnail_navigation, text="→", width=4, command=lambda: self.change_thumbnail_page(1))
        self.thumbnail_next_button.pack(side="left", padx=(4, 0))
        self.thumbnail_page_var = tk.StringVar(value="Page 1 of 1")
        ttk.Label(thumbnail_navigation, textvariable=self.thumbnail_page_var).pack(side="left", padx=8)
        page_size_box = ttk.Combobox(thumbnail_navigation, textvariable=self.thumbnail_page_size_var, state="readonly", width=6, values=("Auto", "200", "500", "1000"))
        self.thumbnail_page_size_box = page_size_box
        page_size_box.pack(side="right")
        ttk.Label(thumbnail_navigation, text="Per page:").pack(side="right", padx=(8, 3))
        page_size_box.bind("<<ComboboxSelected>>", self.change_thumbnail_page_size)
        self.thumbnail_canvas = tk.Canvas(self.thumbnail_frame, highlightthickness=0)
        thumbnail_scroll = ttk.Scrollbar(self.thumbnail_frame, orient="vertical", command=self.thumbnail_yview)
        self.thumbnail_canvas.configure(yscrollcommand=thumbnail_scroll.set)
        thumbnail_scroll.pack(side="right", fill="y")
        self.thumbnail_canvas.pack(fill="both", expand=True)
        self.thumbnail_grid = ttk.Frame(self.thumbnail_canvas)
        self.thumbnail_window = self.thumbnail_canvas.create_window((0, 0), window=self.thumbnail_grid, anchor="nw")
        self.thumbnail_grid.bind("<Configure>", self.thumbnail_grid_configured)
        self.thumbnail_canvas.bind("<Configure>", self.thumbnail_canvas_configured)
        for widget in (self.thumbnail_canvas, self.thumbnail_grid):
            widget.bind("<MouseWheel>", self.scroll_thumbnail_grid)
            widget.bind("<Button-4>", self.scroll_thumbnail_grid)
            widget.bind("<Button-5>", self.scroll_thumbnail_grid)
        self.thumbnail_canvas.bind("<Button-3>", lambda event: self.background_menu.tk_popup(event.x_root, event.y_root))
        self.thumbnail_canvas.drop_target_register(DND_FILES)
        self.thumbnail_canvas.dnd_bind("<<Drop:DND_Files>>", self.drop_files_in_current_folder)

        self.context_menu = tk.Menu(self, tearoff=False)
        self.context_menu.add_command(label="Copy to other pane", command=lambda: self.transfer_callback(self, False))
        self.context_menu.add_command(label="Move to other pane", command=lambda: self.transfer_callback(self, True))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Open", command=self.open_selected)
        self.context_menu.add_command(label="Show in File Explorer", command=self.reveal_selected)
        self.context_menu.add_command(label="Rename…", command=self.rename_selected)
        rating_menu = tk.Menu(self.context_menu, tearoff=False)
        rating_menu.add_command(label="Clear rating", command=lambda: self.assign_rating(0))
        rating_menu.add_separator()
        for rating in range(1, 6): rating_menu.add_command(label="★" * rating, command=lambda value=rating: self.assign_rating(value))
        self.context_menu.add_cascade(label="Rating", menu=rating_menu)
        color_menu = tk.Menu(self.context_menu, tearoff=False)
        color_menu.add_command(label="None", command=lambda: self.assign_color_label(""))
        color_menu.add_separator()
        for color in ("Red", "Yellow", "Green", "Blue", "Purple"): color_menu.add_command(label=color, command=lambda value=color: self.assign_color_label(value))
        self.context_menu.add_cascade(label="Colour label", menu=color_menu)
        self.context_menu.add_command(label="Edit tags…", command=self.edit_tags)
        self.context_menu.add_command(label="Move to Recycle Bin", command=lambda: self.app.delete_selected(self))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Select all shown", command=self.select_matching)
        self.context_menu.add_command(label="Clear ticks", command=self.clear_checks)
        self.context_menu.add_command(label="Find duplicates", command=lambda: self.app.find_duplicates(self))
        self.context_menu.add_command(label="Compare selected", command=lambda: self.app.compare_selected(self))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Refresh this pane", command=self.refresh_browser)
        self.background_menu = tk.Menu(self, tearoff=False)
        self.background_menu.add_command(label="Refresh this pane", command=self.refresh_browser)
        self.background_menu.add_command(label="Refresh both panes", command=self.app.refresh)
        self.folder_context_menu = tk.Menu(self, tearoff=False)
        self.folder_context_menu.add_command(label="Open folder", command=self.open_folder_context)
        self.folder_context_menu.add_command(label="Refresh this pane", command=self.refresh_browser)
        self.folder_context_path: Path | None = None
        self.header_menu = tk.Menu(self, tearoff=False)
        self.header_menu.add_command(label="Configure columns…", command=self.configure_columns)
        self.header_menu.add_command(label="Reset column widths", command=self.reset_column_widths)
        content.add(folder_frame, weight=0)
        content.add(media_frame, weight=1)

        self.inspector_frame = ttk.Frame(content, padding=8)
        ttk.Label(self.inspector_frame, text="Inspector", style="PaneTitle.TLabel").pack(anchor="w", pady=(0, 6))
        self.inspector_name_var = tk.StringVar(value="No file selected")
        ttk.Label(self.inspector_frame, textvariable=self.inspector_name_var, font=("Segoe UI", 10, "bold"), wraplength=260, justify="left").pack(fill="x", anchor="w")
        self.inspector_path_var = tk.StringVar(value="")
        ttk.Label(self.inspector_frame, textvariable=self.inspector_path_var, wraplength=260, justify="left").pack(fill="x", anchor="w", pady=(3, 8))
        self.inspector_details_var = tk.StringVar(value="Select a media file to see its details.")
        ttk.Label(self.inspector_frame, textvariable=self.inspector_details_var, wraplength=260, justify="left").pack(fill="both", expand=True, anchor="nw")
        inspector_buttons = ttk.Frame(self.inspector_frame); inspector_buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(inspector_buttons, text="Copy path", command=self.copy_inspector_path).pack(side="left")
        ttk.Button(inspector_buttons, text="Open", command=self.open_selected).pack(side="left", padx=4)
        ttk.Button(inspector_buttons, text="Reveal", command=self.reveal_selected).pack(side="left")
        if self.inspector_enabled_var.get(): content.add(self.inspector_frame, weight=0)

        status_row = ttk.Frame(self)
        status_row.pack(fill="x", pady=(5, 0))
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_row, textvariable=self.status_var).pack(side="left", fill="x", expand=True)
        self.checked_label_var = tk.StringVar(value="0 ticked")
        ttk.Label(status_row, textvariable=self.checked_label_var).pack(side="left", padx=(6, 4))
        ttk.Button(status_row, text="Clear ticks", command=self.clear_checks).pack(side="left", padx=(0, 5))
        self.scan_progress = ttk.Progressbar(status_row, mode="determinate", length=110)
        self.scan_progress.pack(side="left", padx=5)
        self.cancel_button = ttk.Button(status_row, text="Cancel", width=7, command=self.cancel_scan, state="disabled")
        self.cancel_button.pack(side="right")
        self.after(100, self.poll_results)
        self.build_folder_roots()
        self.navigate(start_path)
        self.after(200, lambda: self.restore_folder_width(saved_state.get("folder_width")))
        self.after_idle(lambda: self.set_view_mode(self.view_mode_var.get()))
        self.update_sort_label()

    def build_folder_roots(self):
        self.folder_tree.delete(*self.folder_tree.get_children())
        if sys.platform == "win32":
            roots = [Path(f"{letter}:\\") for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if Path(f"{letter}:\\").exists()]
        else:
            roots = [Path("/")]
        for root in roots:
            node = self.folder_tree.insert("", "end", text=str(root), tags=(str(root),))
            self.add_folder_placeholder(node, root)

    def refresh_browser(self):
        self.build_folder_roots()
        self.sync_folder_tree()
        self.scan()

    def show_folder_context(self, event):
        self.active_callback(self)
        row = self.folder_tree.identify_row(event.y)
        tags = self.folder_tree.item(row, "tags") if row else ()
        self.folder_context_path = Path(tags[0]) if tags and tags[0] != "__placeholder__" else None
        self.folder_context_menu.entryconfigure(0, state="normal" if self.folder_context_path else "disabled")
        self.folder_context_menu.tk_popup(event.x_root, event.y_root)

    def open_folder_context(self):
        if self.folder_context_path and self.folder_context_path.is_dir(): self.navigate(self.folder_context_path)

    def add_folder_placeholder(self, node: str, path: Path):
        # Do not probe every sibling directory just to decide whether to draw
        # an expansion arrow. On large disks that turns one tree expansion into
        # hundreds of extra directory reads. Empty folders simply clear the
        # placeholder when opened.
        self.folder_tree.insert(node, "end", text="Loading…", tags=("__placeholder__",))

    def expand_folder(self, _event=None):
        node = self.folder_tree.focus()
        self.populate_folder_node(node)

    def populate_folder_node(self, node: str):
        tags = self.folder_tree.item(node, "tags")
        if not tags or tags[0] == "__placeholder__":
            return
        children = self.folder_tree.get_children(node)
        if children and self.folder_tree.item(children[0], "tags") == ("__placeholder__",):
            self.folder_tree.delete(*children)
            path = Path(tags[0])
            try:
                folders = sorted((p for p in path.iterdir() if p.is_dir()), key=lambda p: p.name.lower())
                for folder in folders:
                    child = self.folder_tree.insert(node, "end", text=folder.name, tags=(str(folder),))
                    self.add_folder_placeholder(child, folder)
            except (OSError, PermissionError):
                pass

    @staticmethod
    def folder_key(path: Path | str) -> str:
        return os.path.normcase(os.path.normpath(str(path)))

    def sync_folder_tree(self):
        """Expand the tree to the actual pane folder and select that node."""
        target = self.current_path
        parts = target.parts
        if not parts:
            return
        wanted = Path(parts[0])
        node = next((candidate for candidate in self.folder_tree.get_children("")
                     if self.folder_tree.item(candidate, "tags")
                     and self.folder_key(self.folder_tree.item(candidate, "tags")[0]) == self.folder_key(wanted)), None)
        if not node:
            return
        self.folder_tree.item(node, open=bool(parts[1:]))
        for index, part in enumerate(parts[1:]):
            self.populate_folder_node(node)
            wanted = wanted / part
            child = next((candidate for candidate in self.folder_tree.get_children(node)
                          if self.folder_tree.item(candidate, "tags")
                          and self.folder_tree.item(candidate, "tags")[0] != "__placeholder__"
                          and self.folder_key(self.folder_tree.item(candidate, "tags")[0]) == self.folder_key(wanted)), None)
            if not child:
                break
            node = child
            # Expand only ancestors needed to reveal the target. Keeping the
            # selected folder closed avoids displaying its lazy "Loading…"
            # placeholder before the user actually expands it.
            self.folder_tree.item(node, open=index < len(parts[1:]) - 1)
        self.folder_tree.selection_set(node)
        self.folder_tree.focus(node)
        self.folder_tree.see(node)

    def folder_selected(self, _event=None):
        selection = self.folder_tree.selection()
        if not selection:
            return
        tags = self.folder_tree.item(selection[0], "tags")
        if tags and tags[0] != "__placeholder__":
            path = Path(tags[0])
            if path != self.current_path:
                self.navigate(path)

    def choose_folder(self):
        chosen = filedialog.askdirectory(initialdir=self.current_path, title=f"Choose {self.title} folder")
        if chosen:
            self.navigate(Path(chosen))

    def go_up(self):
        self.navigate(self.current_path.parent)

    def go_back(self):
        if self.navigation_index <= 0:
            return
        previous_index = self.navigation_index
        self.navigation_index -= 1
        if not self.navigate(self.navigation_history[self.navigation_index], record_history=False):
            self.navigation_index = previous_index
            self.update_navigation_buttons()

    def go_forward(self):
        if self.navigation_index >= len(self.navigation_history) - 1:
            return
        previous_index = self.navigation_index
        self.navigation_index += 1
        if not self.navigate(self.navigation_history[self.navigation_index], record_history=False):
            self.navigation_index = previous_index
            self.update_navigation_buttons()

    def update_navigation_buttons(self):
        self.back_button.configure(state="normal" if self.navigation_index > 0 else "disabled")
        self.forward_button.configure(state="normal" if self.navigation_index < len(self.navigation_history) - 1 else "disabled")
        self.up_button.configure(state="normal" if self.current_path.parent != self.current_path else "disabled")

    def navigate(self, path: Path, record_history: bool = True) -> bool:
        path = path.expanduser().resolve()
        if not path.is_dir():
            messagebox.showerror("Folder not found", f"This folder does not exist:\n{path}")
            self.path_var.set(str(self.current_path))
            return False
        path_changed = path != self.current_path
        if path_changed:
            self.clear_checks()
        if record_history and path_changed:
            self.navigation_history = self.navigation_history[:self.navigation_index + 1]
            self.navigation_history.append(path)
            self.navigation_index = len(self.navigation_history) - 1
        self.current_path = path
        self.path_var.set(str(path))
        self.update_navigation_buttons()
        self.sync_folder_tree()
        self.restart_live_monitoring()
        self.scan()
        return True

    def restore_folder_width(self, width):
        if isinstance(width, int) and width > 50:
            try:
                self.content_panes.sashpos(0, width)
            except tk.TclError:
                pass

    def get_state(self) -> dict:
        try:
            folder_width = self.content_panes.sashpos(0)
        except tk.TclError:
            folder_width = 180
        return {
            "path": str(self.current_path),
            "recursive": self.recursive_var.get(),
            "live_updates": self.live_updates_var.get(),
            "inspector_enabled": self.inspector_enabled_var.get(),
            "show_videos": self.show_videos_var.get(),
            "show_images": self.show_images_var.get(),
            "resolution_filter": self.filter_var.get(),
            "outlier_sensitivity": self.outlier_sensitivity_var.get(),
            "search": self.search_var.get(),
            "advanced_filters": self.advanced_filters,
            "view_mode": self.view_mode_var.get(),
            "thumbnail_size": self.thumbnail_size_var.get(),
            "thumbnail_page_size": self.thumbnail_page_size,
            "thumbnail_page_size_mode": self.thumbnail_page_size_mode,
            "thumbnail_browse_mode": self.thumbnail_browse_mode,
            "sort_column": self.sort_column,
            "sort_reverse": self.sort_reverse,
            "column_order": list(self.tree["displaycolumns"]),
            "column_widths": {column: self.tree.column(column, "width") for column in self.tree["columns"]},
            "folder_width": folder_width,
        }

    def apply_state(self, state: dict):
        self.recursive_var.set(bool(state.get("recursive", False)))
        self.live_updates_var.set(bool(state.get("live_updates", False)))
        self.inspector_enabled_var.set(bool(state.get("inspector_enabled", False)))
        self.show_videos_var.set(bool(state.get("show_videos", True)))
        self.show_images_var.set(bool(state.get("show_images", True)))
        self.filter_var.set(state.get("resolution_filter", "All"))
        self.search_var.set(state.get("search", ""))
        self.advanced_filters = dict(state.get("advanced_filters", {}))
        self.sort_column = state.get("sort_column", "name")
        self.sort_reverse = bool(state.get("sort_reverse", False))
        self.update_sort_label()
        self.view_mode_var.set(state.get("view_mode", "Details"))
        self.thumbnail_size_var.set(state.get("thumbnail_size", "Medium"))
        self.thumbnail_page_size_mode = str(state.get("thumbnail_page_size_mode", "Auto"))
        if self.thumbnail_page_size_mode not in {"Auto", "200", "500", "1000"}: self.thumbnail_page_size_mode = "Auto"
        self.thumbnail_page_size_var.set(self.thumbnail_page_size_mode)
        self.thumbnail_browse_mode = str(state.get("thumbnail_browse_mode", "Continuous"))
        if self.thumbnail_browse_mode not in {"Continuous", "Paged"}: self.thumbnail_browse_mode = "Continuous"
        self.thumbnail_browse_mode_var.set(self.thumbnail_browse_mode)
        self.outlier_sensitivity_var.set(state.get("outlier_sensitivity", "Large (1.75×)"))
        columns = list(self.tree["columns"])
        order = [column for column in state.get("column_order", []) if column in columns]
        order.extend(column for column in columns if column not in order)
        self.tree.configure(displaycolumns=order)
        for column, width in state.get("column_widths", {}).items():
            if column in columns and isinstance(width, int): self.tree.column(column, width=width)
        path = Path(state.get("path", self.current_path))
        self.navigate(path if path.is_dir() else self.current_path)
        self.set_view_mode(self.view_mode_var.get())
        self.toggle_inspector()

    def recursive_changed(self):
        self.restart_live_monitoring()
        self.scan()

    def toggle_live_updates(self):
        if self.live_updates_var.get():
            self.start_live_monitoring(show_error=True)
        else:
            self.stop_live_monitoring()
            self.status_var.set("Live updates off")

    def restart_live_monitoring(self):
        self.stop_live_monitoring()
        if self.live_updates_var.get():
            self.start_live_monitoring(show_error=False)

    def start_live_monitoring(self, show_error: bool = False) -> bool:
        if not self.live_updates_var.get():
            return False
        if Observer is None:
            self.live_updates_var.set(False)
            if show_error:
                messagebox.showerror("Live updates unavailable", "The folder-monitoring component is not installed.")
            return False
        try:
            handler = PaneChangeHandler(lambda directory: self.app.post_ui(self.queue_live_refresh, directory))
            observer = Observer()
            observer.schedule(handler, str(self.current_path), recursive=self.recursive_var.get())
            observer.start()
            self.live_observer = observer
            self.status_var.set("Live updates on")
            return True
        except (OSError, RuntimeError) as exc:
            self.live_updates_var.set(False)
            self.live_observer = None
            if show_error:
                messagebox.showerror("Could not monitor folder", f"Live updates could not be enabled for:\n{self.current_path}\n\n{exc}")
            return False

    def stop_live_monitoring(self):
        if self.live_refresh_job:
            try: self.after_cancel(self.live_refresh_job)
            except tk.TclError: pass
            self.live_refresh_job = None
        observer, self.live_observer = self.live_observer, None
        if observer:
            observer.stop()
            observer.join(timeout=2)

    def queue_live_refresh(self, directory_changed: bool = False):
        if not self.live_updates_var.get() or not self.winfo_exists():
            return
        self.live_tree_changed = self.live_tree_changed or directory_changed
        if self.live_refresh_job:
            try: self.after_cancel(self.live_refresh_job)
            except tk.TclError: pass
        self.live_refresh_job = self.after(900, self.apply_live_refresh)

    def apply_live_refresh(self):
        self.live_refresh_job = None
        if not self.live_updates_var.get():
            return
        if self.scan_active:
            self.live_refresh_job = self.after(1000, self.apply_live_refresh)
            return
        if self.live_tree_changed:
            self.build_folder_roots()
            self.sync_folder_tree()
        self.live_tree_changed = False
        self.scan()

    def scan(self, preferred_path: Path | str | None = None):
        if preferred_path is None:
            selected = self.highlighted_items()
            preferred_path = selected[0].path if selected else None
        self.preferred_selection_path = str(preferred_path) if preferred_path is not None else None
        self.scan_cancel_event.set()
        self.scan_cancel_event = threading.Event()
        cancel_event = self.scan_cancel_event
        self.scan_generation += 1
        self.scan_active = True
        generation = self.scan_generation
        self.items.clear()
        self.visible_items = []
        self.thumbnail_page = 0
        self.tree.delete(*self.tree.get_children())
        if self.view_mode_var.get() == "Thumbnails": self.render_thumbnail_grid()
        self.status_var.set("Scanning media…")
        self.scan_progress.configure(value=0, maximum=1)
        self.cancel_button.configure(state="normal")
        self.filter_box["values"] = ("All",)

        scan_path = self.current_path
        recursive = self.recursive_var.get()

        def worker():
            try:
                candidates = scan_path.rglob("*") if recursive else scan_path.iterdir()
                paths = []
                for path in candidates:
                    if cancel_event.is_set():
                        self.results.put((generation, "cancelled", len(paths)))
                        return
                    try:
                        relative = str(path.relative_to(scan_path))
                        excluded = any(fnmatch.fnmatch(relative.lower(), pattern.lower()) or fnmatch.fnmatch(path.name.lower(), pattern.lower()) for pattern in self.app.excluded_patterns)
                        if not excluded and path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                            paths.append(path)
                    except OSError:
                        continue
                paths.sort(key=lambda p: str(p).lower())
                self.results.put((generation, "total", len(paths)))
                cached_count = 0
                def inspect_path(path):
                    try:
                        if not self.metadata_cache.is_current(path):
                            if not self.app.workload.wait_for_background(cancel_event):
                                return OSError("Scan cancelled")
                        return self.metadata_cache.inspect(path)
                    except OSError as exc: return exc
                with ThreadPoolExecutor(max_workers=self.app.scan_workers) as executor:
                    inspected = executor.map(inspect_path, paths)
                    for index, result in enumerate(inspected, 1):
                        path = paths[index - 1]
                        if cancel_event.is_set():
                            self.results.put((generation, "cancelled", index - 1))
                            return
                        if isinstance(result, OSError):
                            self.results.put((generation, "file_error", f"{path.name}: {result}"))
                            continue
                        item, was_cached = result
                        cached_count += int(was_cached)
                        self.results.put((generation, "item", (item, index, len(paths), cached_count)))
                self.results.put((generation, "done", len(paths)))
            except Exception as exc:
                self.results.put((generation, "error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def cancel_scan(self):
        self.scan_cancel_event.set()
        self.cancel_button.configure(state="disabled")
        self.status_var.set("Cancelling scan…")

    def poll_results(self):
        view_dirty = False
        force_refresh = False
        started = time.monotonic()
        processed = 0
        try:
            # A cached recursive scan can enqueue thousands of results almost
            # instantly. Keep each UI turn short so playback and controls run.
            while processed < 250 and time.monotonic() - started < 0.025:
                generation, kind, value = self.results.get_nowait()
                processed += 1
                if generation != self.scan_generation:
                    continue
                if kind == "item":
                    item, index, total, cached_count = value
                    self.items[str(item.path)] = item
                    self.scan_progress.configure(value=index)
                    self.status_var.set(f"Scanning {index} of {total}… · {cached_count} from cache")
                    view_dirty = True
                elif kind == "total":
                    self.scan_progress.configure(maximum=max(1, value), value=0)
                elif kind == "done":
                    self.scan_active = False
                    self.checked_paths.intersection_update(self.items)
                    self.update_checked_label()
                    failures = sum(bool(item.error) for item in self.items.values())
                    suffix = f" · {failures} unreadable" if failures else ""
                    if self.live_updates_var.get() and self.live_observer:
                        suffix += " · Live"
                    scope = "including subfolders" if self.recursive_var.get() else "in this folder"
                    self.status_var.set(f"{value} media file(s) {scope}{suffix}")
                    self.scan_progress.configure(value=value, maximum=max(1, value))
                    self.cancel_button.configure(state="disabled")
                    threading.Thread(target=self.metadata_cache.save, daemon=True).start()
                    view_dirty = True
                    force_refresh = True
                elif kind == "cancelled":
                    self.scan_active = False
                    self.status_var.set(f"Scan cancelled after {value} file(s)")
                    self.cancel_button.configure(state="disabled")
                    view_dirty = True
                    force_refresh = True
                elif kind == "file_error":
                    self.status_var.set(f"Skipped file: {value}")
                else:
                    self.scan_active = False
                    self.status_var.set(f"Could not scan: {value}")
                    self.cancel_button.configure(state="disabled")
                    force_refresh = True
        except queue.Empty:
            pass
        now = time.monotonic()
        # Rebuilding a growing Treeview is disproportionately expensive on a
        # large recursive scan. Keep collecting results and render once at the
        # end; progress and Cancel still update continuously.
        if view_dirty and (force_refresh or not self.scan_active):
            self.refresh_view(self.preferred_selection_path)
            self.last_view_refresh = now
        self.after(10 if not self.results.empty() else 100, self.poll_results)

    SORT_FIELDS = (
        ("Name", "name"), ("Date modified", "modified"), ("File size", "size"),
        ("Length", "duration"), ("Codec", "codec"), ("Resolution", "resolution"),
        ("Type", "type"), ("Bitrate", "bitrate"), ("Frame rate", "fps"),
        ("Rating", "rating"),
    )

    def build_sort_menu(self):
        """Build an explicit-direction sort menu for thumbnail browsing."""
        self.thumbnail_sort_menu.delete(0, "end")
        for label, column in self.SORT_FIELDS:
            submenu = tk.Menu(self.thumbnail_sort_menu, tearoff=False)
            if column == "name":
                ascending, descending = "A to Z", "Z to A"
            elif column == "modified":
                ascending, descending = "Oldest first", "Newest first"
            elif column in {"size", "resolution", "bitrate", "fps", "rating"}:
                ascending, descending = "Smallest first", "Largest first"
            elif column == "duration":
                ascending, descending = "Shortest first", "Longest first"
            else:
                ascending, descending = "Ascending", "Descending"
            submenu.add_command(label=ascending, command=lambda value=column: self.set_sort_direction(value, False))
            submenu.add_command(label=descending, command=lambda value=column: self.set_sort_direction(value, True))
            self.thumbnail_sort_menu.add_cascade(label=label, menu=submenu)

    def update_sort_label(self):
        labels = {column: label for label, column in self.SORT_FIELDS}
        field = labels.get(self.sort_column, self.sort_column.title())
        if self.sort_column == "name":
            direction = "Z–A" if self.sort_reverse else "A–Z"
        elif self.sort_column == "modified":
            direction = "Newest" if self.sort_reverse else "Oldest"
        elif self.sort_column == "duration":
            direction = "Longest" if self.sort_reverse else "Shortest"
        elif self.sort_column in {"size", "resolution", "bitrate", "fps", "rating"}:
            direction = "Largest" if self.sort_reverse else "Smallest"
        else:
            direction = "Descending" if self.sort_reverse else "Ascending"
        self.sort_label_var.set(f"Sort: {field} · {direction} ▾")

    def set_sort_direction(self, column: str, reverse: bool):
        if column not in dict(self.SORT_FIELDS).values():
            return
        self.sort_column, self.sort_reverse = column, bool(reverse)
        self.update_sort_label()
        self.refresh_view()

    def set_sort(self, column: str):
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column, self.sort_reverse = column, False
        self.update_sort_label()
        self.refresh_view()

    def refresh_view(self, preferred_path: Path | str | None = None):
        self.view_generation += 1
        view_generation = self.view_generation
        filter_signature = (
            self.show_videos_var.get(), self.show_images_var.get(), self.search_var.get().strip().lower(),
            self.filter_var.get(), json.dumps(self.advanced_filters, sort_keys=True), self.sort_column, self.sort_reverse,
        )
        if filter_signature != self.thumbnail_filter_signature:
            self.thumbnail_page = 0
            self.thumbnail_filter_signature = filter_signature
        selected_paths = {self.tree.item(iid, "tags")[0] for iid in self.tree.selection() if self.tree.item(iid, "tags")}
        if preferred_path is not None:
            selected_paths = {str(preferred_path)}
            self.preferred_selection_path = str(preferred_path)
        values = list(self.items.values())
        if not self.show_videos_var.get():
            values = [item for item in values if item.path.suffix.lower() not in VIDEO_EXTENSIONS]
        if not self.show_images_var.get():
            values = [item for item in values if item.path.suffix.lower() not in IMAGE_EXTENSIONS]
        query = self.search_var.get().strip().lower()
        if query:
            values = [item for item in values if query in str(item.path.relative_to(self.current_path)).lower()]
        values = [item for item in values if self.matches_advanced_filters(item)]
        resolution_filter = self.filter_var.get()
        resolutions = sorted({item.resolution for item in values}, key=lambda x: (x == "Unknown", x))
        self.filter_box["values"] = ("All", *resolutions)
        if resolution_filter != "All":
            values = [item for item in values if item.resolution == resolution_filter]
        key_map = {
            "name": lambda i: i.path.name.lower(), "type": lambda i: i.path.suffix.lower(), "codec": lambda i: i.codec.lower(),
            "rating": lambda i: i.rating, "color": lambda i: i.color_label.lower(), "tags": lambda i: tuple(tag.lower() for tag in i.tags),
            "resolution": lambda i: (i.pixels, i.width or 0, i.height or 0),
            "pixels": lambda i: i.pixels, "size": lambda i: i.size,
            "rate": lambda i: i.megabytes_per_minute if i.megabytes_per_minute is not None else -1,
            "bitrate": lambda i: i.bitrate or -1, "fps": lambda i: i.frame_rate or -1,
            "audio": lambda i: (i.audio_codec.lower(), i.audio_channels or 0), "hdr": lambda i: i.hdr,
            "modified": lambda i: i.modified, "duration": lambda i: i.duration if i.duration is not None else -1,
        }
        values.sort(key=key_map[self.sort_column], reverse=self.sort_reverse)
        self.visible_items = values
        if self.preferred_selection_path and not any(str(item.path) == self.preferred_selection_path for item in values):
            self.preferred_selection_path = None
        self.tree.delete(*self.tree.get_children())
        self.path_to_iid = {}
        self.after_idle(self.render_detail_batch, view_generation, values, 0, selected_paths)
        if self.view_mode_var.get() == "Thumbnails" and not self.scan_active: self.render_thumbnail_grid()

    def render_detail_batch(self, generation: int, values: list[MediaItem], start: int, selected_paths: set[str]):
        """Insert rows in short turns so Windows can keep painting/responding."""
        if generation != self.view_generation:
            return
        started = time.monotonic()
        index = start
        while index < len(values) and index < start + 300 and time.monotonic() - started < 0.02:
            item = values[index]
            iid = f"row-{index}"
            megapixels = f"{item.pixels / 1_000_000:.2f}" if item.pixels else "—"
            rate = f"{item.megabytes_per_minute:.1f}" if item.megabytes_per_minute is not None else "—"
            bitrate = f"{item.bitrate / 1_000_000:.2f} Mbps" if item.bitrate else "—"
            fps = f"{item.frame_rate:.2f}" if item.frame_rate else "—"
            audio = f"{item.audio_codec} · {item.audio_channels}ch" if item.audio_channels else item.audio_codec
            if self.recursive_var.get():
                character_width = max(24, int(self.tree.column("name", "width") / 7))
                display_name = compact_relative_path(item.path.relative_to(self.current_path), character_width)
            else:
                display_name = item.path.name
            modified = datetime.fromtimestamp(item.modified).strftime("%Y-%m-%d %H:%M")
            stars = "★" * item.rating if item.rating else "—"
            path_key = str(item.path)
            self.tree.insert("", "end", iid=iid, text="☑" if path_key in self.checked_paths else "☐", values=(display_name, item.codec, item.resolution, human_duration(item.duration), human_size(item.size), rate, fps, modified, item.path.suffix[1:].upper(), bitrate, audio, item.hdr, megapixels, item.color_label or "—", ", ".join(item.tags) or "—", stars), tags=(path_key,))
            self.path_to_iid[path_key] = iid
            if path_key in selected_paths:
                self.tree.selection_add(iid)
            index += 1
        if index < len(values):
            self.after(1, self.render_detail_batch, generation, values, index, selected_paths)
        elif self.preferred_selection_path:
            iid = self.path_to_iid.get(self.preferred_selection_path)
            if iid:
                self.tree.selection_set(iid); self.tree.focus(iid); self.tree.see(iid)
                item = self.items.get(self.preferred_selection_path)
                self.update_thumbnail_selection(); self.update_inspector(item)
                if item and self.preview_enabled_var.get(): self.preview_callback(item)
            self.preferred_selection_path = None

    def set_view_mode(self, mode: str):
        mode = mode if mode in {"Details", "Thumbnails"} else "Details"
        self.view_mode_var.set(mode)
        self.details_frame.pack_forget(); self.thumbnail_frame.pack_forget()
        if mode == "Thumbnails":
            self.thumbnail_frame.pack(fill="both", expand=True); self.render_thumbnail_grid()
        else:
            self.thumbnail_generation += 1; self.details_frame.pack(fill="both", expand=True)

    def render_thumbnail_grid(self):
        if self.view_mode_var.get() != "Thumbnails": return
        available = self.thumbnail_canvas.winfo_width()
        if available < 100:
            self.schedule_thumbnail_reflow(50)
            return
        self.thumbnail_generation += 1
        generation = self.thumbnail_generation
        self.clear_virtual_thumbnail_cards()
        for child in self.thumbnail_grid.winfo_children(): child.destroy()
        self.thumbnail_images.clear(); self.thumbnail_cells.clear()
        size_map = {"Small": (110, 75, 130), "Medium": (160, 110, 185), "Large": (230, 155, 255)}
        width, height, cell_width = size_map.get(self.thumbnail_size_var.get(), size_map["Medium"])
        columns = max(1, available // cell_width)
        self.thumbnail_columns = columns
        self.thumbnail_browse_mode = self.thumbnail_browse_mode_var.get() if self.thumbnail_browse_mode_var.get() in {"Continuous", "Paged"} else "Continuous"
        if self.thumbnail_browse_mode == "Continuous":
            self.render_virtual_thumbnail_grid(generation, width, height, cell_width, columns)
            return
        self.thumbnail_canvas.itemconfigure(self.thumbnail_window, state="normal", width=available)
        self.thumbnail_page_size_box.configure(state="readonly")
        self.thumbnail_page_size = self.effective_thumbnail_page_size()
        page_count = max(1, (len(self.visible_items) + self.thumbnail_page_size - 1) // self.thumbnail_page_size)
        preferred_index = next((index for index, item in enumerate(self.visible_items) if str(item.path) == self.preferred_selection_path), None)
        if preferred_index is not None:
            self.thumbnail_page = preferred_index // self.thumbnail_page_size
        self.thumbnail_page = max(0, min(self.thumbnail_page, page_count - 1))
        page_start = self.thumbnail_page * self.thumbnail_page_size
        page_items = self.visible_items[page_start:page_start + self.thumbnail_page_size]
        automatic = f" · Auto {self.thumbnail_page_size}/page" if self.thumbnail_page_size_mode == "Auto" else ""
        self.thumbnail_page_var.set(f"Page {self.thumbnail_page + 1} of {page_count} · {len(self.visible_items)} files{automatic}")
        self.thumbnail_previous_button.configure(state="normal" if self.thumbnail_page > 0 else "disabled")
        self.thumbnail_next_button.configure(state="normal" if self.thumbnail_page < page_count - 1 else "disabled")
        selected = {self.tree.item(iid, "tags")[0] for iid in self.tree.selection() if self.tree.item(iid, "tags")}
        if self.preferred_selection_path: selected.add(self.preferred_selection_path)
        pending = []
        for index, item in enumerate(page_items):
            path_key = str(item.path)
            card, image_label = self.create_thumbnail_card(self.thumbnail_grid, item, width, height, cell_width, path_key in selected)
            card.grid(row=index // columns, column=index % columns, padx=5, pady=5, sticky="n")
            self.thumbnail_cells[path_key] = card
            pending.append((image_label, item))
        self.thumbnail_canvas.yview_moveto(0)
        self.after(10, self.load_thumbnail_batch, generation, pending, 0, (width, height))

    def create_thumbnail_card(self, parent, item: MediaItem, width: int, height: int, cell_width: int, selected: bool):
        border = "#4a90e2" if selected else COLOR_LABEL_HEX.get(item.color_label, "#d0d0d0")
        card = tk.Frame(parent, bd=1, relief="solid", highlightthickness=2, highlightbackground=border, width=cell_width - 10, height=height + 78)
        card.pack_propagate(False)
        image_label = tk.Label(card, text="Loading…", anchor="center", bg="#202020", fg="#dddddd")
        image_label.pack(fill="both", expand=True, padx=3, pady=(3, 1))
        check_label = tk.Label(card, text="☑" if str(item.path) in self.checked_paths else "☐", font=("Segoe UI Symbol", 13, "bold"), bg="#202020", fg="#ffffff", cursor="hand2")
        check_label.place(x=7, y=6)
        check_label.bind("<Button-1>", lambda _event, value=item: self.toggle_check(str(value.path)))
        card.check_label = check_label
        display_name = compact_relative_path(item.path.relative_to(self.current_path), max(20, int(cell_width / 7))) if self.recursive_var.get() else item.path.name
        label_details = ""
        if item.rating: label_details += "\n" + "★" * item.rating
        if item.tags: label_details += (" · " if label_details else "\n") + ", ".join(item.tags[:3])
        name_label = tk.Label(card, text=display_name + label_details, anchor="center", justify="center", wraplength=cell_width - 12)
        name_label.pack(fill="x", padx=3, pady=(1, 3))
        for widget in (card, image_label, name_label):
            widget.bind("<MouseWheel>", self.scroll_thumbnail_grid)
            widget.bind("<Button-4>", self.scroll_thumbnail_grid)
            widget.bind("<Button-5>", self.scroll_thumbnail_grid)
            widget.bind("<Button-1>", lambda event, value=item: self.thumbnail_clicked(event, value))
            widget.bind("<Double-1>", lambda _event, value=item: self.thumbnail_opened(value))
            widget.bind("<Button-3>", lambda event, value=item: self.show_thumbnail_context(event, value))
            try:
                widget.drag_source_register(1, DND_FILES); widget.dnd_bind("<<DragInitCmd>>", self.start_thumbnail_drag)
            except tk.TclError: pass
        return card, image_label

    @staticmethod
    def virtual_thumbnail_range(total_items: int, columns: int, row_height: int, top: float, viewport_height: float, buffer_rows: int = 2) -> range:
        if not total_items or not columns or not row_height:
            return range(0)
        first_row = max(0, int(top // row_height) - buffer_rows)
        last_row = min((total_items - 1) // columns, int((top + viewport_height) // row_height) + buffer_rows)
        return range(first_row * columns, min(total_items, (last_row + 1) * columns))

    def render_virtual_thumbnail_grid(self, generation: int, width: int, height: int, cell_width: int, columns: int):
        self.thumbnail_canvas.itemconfigure(self.thumbnail_window, state="hidden")
        self.thumbnail_previous_button.configure(state="disabled")
        self.thumbnail_next_button.configure(state="disabled")
        self.thumbnail_page_size_box.configure(state="disabled")
        self.thumbnail_page_var.set(f"{len(self.visible_items)} files · Continuous · visible cards only")
        self.virtual_row_height = height + 88
        self.virtual_cell_width = cell_width
        self.virtual_dimensions = (width, height)
        rows = (len(self.visible_items) + columns - 1) // columns
        self.thumbnail_canvas.configure(scrollregion=(0, 0, max(1, self.thumbnail_canvas.winfo_width()), max(1, rows * self.virtual_row_height)))
        preferred_index = next((index for index, item in enumerate(self.visible_items) if str(item.path) == self.preferred_selection_path), None)
        if preferred_index is not None:
            target_row = preferred_index // columns
            self.thumbnail_canvas.yview_moveto(min(1.0, target_row / max(1, rows)))
        elif self.virtual_resize_anchor is not None and self.visible_items:
            target_row = self.virtual_resize_anchor // columns
            self.thumbnail_canvas.yview_moveto(min(1.0, target_row / max(1, rows)))
            self.virtual_resize_anchor = None
        else:
            self.thumbnail_canvas.yview_moveto(0)
        self.after_idle(self.update_virtual_thumbnail_cards, generation)

    def clear_virtual_thumbnail_cards(self):
        for _index, (window_id, card, _label, path_key) in list(self.virtual_thumbnail_cards.items()):
            self.thumbnail_canvas.delete(window_id)
            try: card.destroy()
            except tk.TclError: pass
            self.thumbnail_cells.pop(path_key, None)
        self.virtual_thumbnail_cards.clear()

    def update_virtual_thumbnail_cards(self, generation: int | None = None):
        if self.thumbnail_browse_mode != "Continuous" or self.view_mode_var.get() != "Thumbnails":
            return
        generation = self.thumbnail_generation if generation is None else generation
        if generation != self.thumbnail_generation:
            return
        top = self.thumbnail_canvas.canvasy(0)
        wanted = set(self.virtual_thumbnail_range(len(self.visible_items), self.thumbnail_columns, self.virtual_row_height, top, self.thumbnail_canvas.winfo_height()))
        for index in set(self.virtual_thumbnail_cards) - wanted:
            window_id, card, _label, path_key = self.virtual_thumbnail_cards.pop(index)
            self.thumbnail_canvas.delete(window_id); self.thumbnail_cells.pop(path_key, None)
            card.destroy()
        selected = {self.tree.item(iid, "tags")[0] for iid in self.tree.selection() if self.tree.item(iid, "tags")}
        width, height = self.virtual_dimensions
        for index in sorted(wanted - set(self.virtual_thumbnail_cards)):
            item = self.visible_items[index]; path_key = str(item.path)
            card, image_label = self.create_thumbnail_card(self.thumbnail_canvas, item, width, height, self.virtual_cell_width, path_key in selected)
            row, column = divmod(index, self.thumbnail_columns)
            x = column * self.virtual_cell_width + 5; y = row * self.virtual_row_height + 5
            window_id = self.thumbnail_canvas.create_window((x, y), window=card, anchor="nw", width=self.virtual_cell_width - 10, height=self.virtual_row_height - 10)
            self.virtual_thumbnail_cards[index] = (window_id, card, image_label, path_key)
            self.thumbnail_cells[path_key] = card
            image_label.thumbnail_generation = generation
            self.app.generate_thumbnail(self, image_label, item, index, (width, height))

    def thumbnail_yview(self, *args):
        self.thumbnail_canvas.yview(*args)
        if self.thumbnail_browse_mode == "Continuous": self.after_idle(self.update_virtual_thumbnail_cards)

    def scroll_thumbnail_grid(self, event):
        """Scroll this pane when the pointer is anywhere over its thumbnail grid."""
        if getattr(event, "num", None) == 4:
            steps = -1
        elif getattr(event, "num", None) == 5:
            steps = 1
        else:
            delta = getattr(event, "delta", 0)
            if not delta:
                return "break"
            steps = -max(1, abs(int(delta / 120))) if delta > 0 else max(1, abs(int(delta / 120)))
        self.thumbnail_canvas.yview_scroll(steps, "units")
        if self.thumbnail_browse_mode == "Continuous": self.after_idle(self.update_virtual_thumbnail_cards)
        return "break"

    def change_thumbnail_browse_mode(self, _event=None):
        self.thumbnail_browse_mode = self.thumbnail_browse_mode_var.get() if self.thumbnail_browse_mode_var.get() in {"Continuous", "Paged"} else "Continuous"
        self.thumbnail_page = 0
        self.render_thumbnail_grid()

    def change_thumbnail_page(self, delta: int):
        self.thumbnail_page += delta
        self.render_thumbnail_grid()

    def change_thumbnail_page_size(self, _event=None):
        requested = self.thumbnail_page_size_var.get()
        self.thumbnail_page_size_mode = requested if requested in {"Auto", "200", "500", "1000"} else "Auto"
        self.thumbnail_page = 0
        self.render_thumbnail_grid()

    def effective_thumbnail_page_size(self) -> int:
        if self.thumbnail_page_size_mode != "Auto":
            return int(self.thumbnail_page_size_mode)
        videos = sum(item.path.suffix.lower() in VIDEO_EXTENSIONS for item in self.visible_items)
        images = sum(item.path.suffix.lower() in IMAGE_EXTENSIONS for item in self.visible_items)
        return 200 if videos and videos >= images else 500

    def thumbnail_canvas_configured(self, event):
        if self.thumbnail_browse_mode == "Paged":
            self.thumbnail_canvas.itemconfigure(self.thumbnail_window, width=event.width)
        if self.view_mode_var.get() != "Thumbnails" or event.width < 100:
            return
        cell_width = {"Small": 130, "Medium": 185, "Large": 255}.get(self.thumbnail_size_var.get(), 185)
        if max(1, event.width // cell_width) != self.thumbnail_columns:
            if self.thumbnail_browse_mode == "Continuous" and self.virtual_row_height and self.thumbnail_columns:
                self.virtual_resize_anchor = int(self.thumbnail_canvas.canvasy(0) // self.virtual_row_height) * self.thumbnail_columns
            self.schedule_thumbnail_reflow(80)
        elif self.thumbnail_browse_mode == "Continuous":
            self.after_idle(self.update_virtual_thumbnail_cards)

    def thumbnail_grid_configured(self, _event=None):
        if self.thumbnail_browse_mode == "Paged":
            self.thumbnail_canvas.configure(scrollregion=self.thumbnail_canvas.bbox("all"))

    def schedule_thumbnail_reflow(self, delay: int = 50):
        if self.thumbnail_layout_job:
            try: self.after_cancel(self.thumbnail_layout_job)
            except tk.TclError: pass
        self.thumbnail_layout_job = self.after(delay, self.run_thumbnail_reflow)

    def run_thumbnail_reflow(self):
        self.thumbnail_layout_job = None
        self.render_thumbnail_grid()

    def load_thumbnail_batch(self, generation: int, pending: list, start: int, dimensions: tuple[int, int]):
        if generation != self.thumbnail_generation or self.view_mode_var.get() != "Thumbnails": return
        for label, item in pending[start:start + 12]:
            label.thumbnail_generation = generation
            self.app.generate_thumbnail(self, label, item, start, dimensions)
        next_index = start + 12
        if next_index < len(pending): self.after(60, self.load_thumbnail_batch, generation, pending, next_index, dimensions)

    def thumbnail_clicked(self, event, item: MediaItem):
        self.active_callback(self)
        iid = self.path_to_iid.get(str(item.path))
        if not iid: return
        if event.state & 0x0004:
            if iid in self.tree.selection(): self.tree.selection_remove(iid)
            else: self.tree.selection_add(iid)
        else: self.tree.selection_set(iid)
        self.tree.focus(iid); self.update_thumbnail_selection()
        self.update_inspector(item)
        if self.preview_enabled_var.get(): self.preview_callback(item)

    def toggle_preview(self):
        enabled = self.preview_enabled_var.get()
        self.preview_toggle_callback(self, enabled)
        if enabled:
            selected = self.highlighted_items()
            if selected: self.preview_callback(selected[0])

    def toggle_inspector(self):
        shown = any(str(pane) == str(self.inspector_frame) for pane in self.content_panes.panes())
        if self.inspector_enabled_var.get() and not shown:
            # Capture the selection before changing the paned-window layout.
            # On Windows that layout change can briefly disturb focus/events.
            selected = self.highlighted_items()
            item = selected[0] if selected else None
            self.content_panes.add(self.inspector_frame, weight=0)
            self.after_idle(lambda: self.content_panes.sashpos(1, max(300, self.content_panes.winfo_width() - 280)) if len(self.content_panes.panes()) > 2 else None)
            self.update_inspector(item)
            self.after_idle(lambda value=item: self.update_inspector(value))
        elif not self.inspector_enabled_var.get() and shown:
            self.content_panes.forget(self.inspector_frame)

    def update_inspector(self, item: MediaItem | None = None):
        if item is None:
            selected = self.highlighted_items()
            item = selected[0] if selected else None
        if not item:
            self.inspector_name_var.set("No file selected")
            self.inspector_path_var.set("")
            self.inspector_details_var.set("Select a media file to see its details.")
            return
        self.inspector_name_var.set(item.path.name)
        self.inspector_path_var.set(str(item.path))
        audio = f"{item.audio_codec} · {item.audio_channels} channel(s)" if item.audio_channels else item.audio_codec
        details = [
            f"Type: {item.path.suffix[1:].upper() or 'Unknown'}",
            f"Codec: {item.codec}",
            f"Resolution: {item.resolution}",
            f"File size: {human_size(item.size)}",
            f"Modified: {datetime.fromtimestamp(item.modified).strftime('%Y-%m-%d %H:%M:%S')}",
            f"Duration: {human_duration(item.duration)}",
            f"Frame rate: {item.frame_rate:.3f} fps" if item.frame_rate else "Frame rate: —",
            f"Bitrate: {item.bitrate / 1_000_000:.2f} Mbps" if item.bitrate else "Bitrate: —",
            f"Pixel format: {item.pixel_format}",
            f"Dynamic range: {item.hdr}",
            f"Audio: {audio}",
            "",
            f"Rating: {'★' * item.rating if item.rating else 'Unrated'}",
            f"Colour label: {item.color_label or 'None'}",
            f"Tags: {', '.join(item.tags) if item.tags else 'None'}",
        ]
        if item.error: details.extend(("", f"Unreadable: {item.error}"))
        self.inspector_details_var.set("\n".join(details))

    def copy_inspector_path(self):
        selected = self.highlighted_items()
        if not selected: return
        self.clipboard_clear(); self.clipboard_append(str(selected[0].path)); self.update()

    def update_thumbnail_selection(self):
        selected = {self.tree.item(iid, "tags")[0] for iid in self.tree.selection() if self.tree.item(iid, "tags")}
        for path, card in self.thumbnail_cells.items():
            item = self.items.get(path)
            card.configure(highlightbackground="#4a90e2" if path in selected else COLOR_LABEL_HEX.get(item.color_label if item else "", "#d0d0d0"))
            check_label = getattr(card, "check_label", None)
            if check_label and check_label.winfo_exists():
                check_label.configure(text="☑" if path in self.checked_paths else "☐")

    def thumbnail_opened(self, item: MediaItem):
        iid = self.path_to_iid.get(str(item.path))
        if iid: self.tree.selection_set(iid); self.tree.focus(iid)
        self.open_items([item])

    def show_thumbnail_context(self, event, item: MediaItem):
        iid = self.path_to_iid.get(str(item.path))
        if not iid: return
        if iid not in self.tree.selection(): self.tree.selection_set(iid); self.tree.focus(iid)
        self.update_thumbnail_selection()
        count = len(self.selected_items()); suffix = f" ({count} files)" if count > 1 else ""
        self.context_menu.entryconfigure(0, label=f"Copy to other pane{suffix}"); self.context_menu.entryconfigure(1, label=f"Move to other pane{suffix}")
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def refresh_selected_user_labels(self, paths: list[Path]):
        for path in paths:
            key = str(path)
            item = self.items.get(key)
            if item: self.items[key] = self.metadata_cache.with_user_labels(item)
        self.refresh_view()

    def assign_rating(self, rating: int):
        paths = [item.path for item in self.selected_items()]
        if not paths: return
        self.metadata_cache.set_rating(paths, rating)
        self.refresh_selected_user_labels(paths)

    def assign_color_label(self, color: str):
        paths = [item.path for item in self.selected_items()]
        if not paths: return
        self.metadata_cache.set_color_label(paths, color)
        self.refresh_selected_user_labels(paths)

    def edit_tags(self):
        items = self.selected_items()
        if not items: return
        common = set(items[0].tags)
        for item in items[1:]: common.intersection_update(item.tags)
        value = simpledialog.askstring("Edit tags", f"Comma-separated tags for {len(items)} selected file(s):\n\nThis replaces the tag list on every selected file.", initialvalue=", ".join(sorted(common, key=str.casefold)), parent=self)
        if value is None: return
        paths = [item.path for item in items]
        self.metadata_cache.set_tags(paths, value.split(","))
        self.refresh_selected_user_labels(paths)

    def start_thumbnail_drag(self, _event):
        files = tuple(str(item.path.resolve()) for item in self.selected_items() if item.path.exists())
        return (COPY, DND_FILES, files) if files else (REFUSE_DROP, DND_FILES, ())

    def start_selected_drag(self, _event):
        """Export the complete selection with a conventional left-button drag."""
        files = tuple(str(item.path.resolve()) for item in self.selected_items() if item.path.exists())
        if not files:
            self.status_var.set("Select one or more files before dragging")
            return (REFUSE_DROP, DND_FILES, ())
        self.status_var.set(f"Dragging {len(files)} selected file(s)…")
        return (COPY, DND_FILES, files)

    def contains_media_path(self, path: Path) -> bool:
        try:
            relative = path.resolve().relative_to(self.current_path.resolve())
        except (OSError, ValueError):
            return False
        return self.recursive_var.get() or len(relative.parts) == 1

    def remove_known_paths(self, paths) -> bool:
        changed = False
        for path in paths:
            path_key = str(Path(path))
            changed = self.items.pop(path_key, None) is not None or changed
            self.checked_paths.discard(path_key)
        self.update_checked_label()
        return changed

    def continuation_path_after_removal(self, paths) -> Path | None:
        """Return the item that should become current after visible rows disappear."""
        removed = {str(Path(path)) for path in paths}
        if not removed or not self.visible_items:
            return None
        removed_indexes = [index for index, item in enumerate(self.visible_items) if str(item.path) in removed]
        if not removed_indexes:
            return None
        remaining = [item for item in self.visible_items if str(item.path) not in removed]
        if not remaining:
            return None
        # The row that slides into the first removed row is the natural next
        # item; when deleting at the end, retain the new final row instead.
        return remaining[min(min(removed_indexes), len(remaining) - 1)].path

    def matches_advanced_filters(self, item: MediaItem) -> bool:
        filters = self.advanced_filters
        orientation = filters.get("orientation", "Any")
        if orientation == "Landscape" and not (item.width and item.height and item.width > item.height): return False
        if orientation == "Portrait" and not (item.width and item.height and item.height > item.width): return False
        if orientation == "Square" and not (item.width and item.height and item.width == item.height): return False
        if filters.get("codec") and filters["codec"].lower() not in item.codec.lower(): return False
        if filters.get("tag") and not any(filters["tag"].lower() in tag.lower() for tag in item.tags): return False
        color = filters.get("color", "Any")
        if color == "Unlabelled" and item.color_label: return False
        if color not in {"", "Any", "Unlabelled"} and item.color_label != color: return False
        try:
            if filters.get("min_rating") and item.rating < int(filters["min_rating"]): return False
        except (ValueError, TypeError): pass
        comparisons = (("min_width", item.width), ("max_width", item.width), ("min_height", item.height), ("max_height", item.height), ("min_size", item.size / (1024 * 1024)), ("max_size", item.size / (1024 * 1024)), ("min_duration", item.duration), ("max_duration", item.duration))
        for key, actual in comparisons:
            raw = filters.get(key, "")
            if raw in (None, ""): continue
            try: limit = float(raw)
            except (ValueError, TypeError): continue
            if actual is None or (key.startswith("min") and actual < limit) or (key.startswith("max") and actual > limit): return False
        date_from, date_to = filters.get("date_from", ""), filters.get("date_to", "")
        try:
            if date_from and item.modified < datetime.strptime(date_from, "%Y-%m-%d").timestamp(): return False
            if date_to and item.modified >= datetime.strptime(date_to, "%Y-%m-%d").timestamp() + 86400: return False
        except ValueError: pass
        return True

    def edit_advanced_filters(self):
        fields = (("orientation", "Orientation"), ("codec", "Codec contains"), ("tag", "Tag contains"), ("min_rating", "Minimum rating"), ("color", "Colour label"), ("min_width", "Minimum width (pixels)"), ("max_width", "Maximum width (pixels)"), ("min_height", "Minimum height (pixels)"), ("max_height", "Maximum height (pixels)"), ("min_size", "Minimum size (MB)"), ("max_size", "Maximum size (MB)"), ("min_duration", "Minimum duration (seconds)"), ("max_duration", "Maximum duration (seconds)"), ("date_from", "Modified from (YYYY-MM-DD)"), ("date_to", "Modified to (YYYY-MM-DD)"))
        dialog = tk.Toplevel(self)
        dialog.title("Advanced filters")
        dialog.transient(self.winfo_toplevel()); dialog.grab_set()
        variables = {}
        for row, (key, label) in enumerate(fields):
            ttk.Label(dialog, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=4)
            default = "Any" if key in {"orientation", "min_rating", "color"} else ""
            variable = tk.StringVar(value=self.advanced_filters.get(key, default)); variables[key] = variable
            if key == "orientation": widget = ttk.Combobox(dialog, textvariable=variable, state="readonly", values=("Any", "Landscape", "Portrait", "Square"))
            elif key == "min_rating": widget = ttk.Combobox(dialog, textvariable=variable, state="readonly", values=("Any", "1", "2", "3", "4", "5"))
            elif key == "color": widget = ttk.Combobox(dialog, textvariable=variable, state="readonly", values=("Any", "Unlabelled", "Red", "Yellow", "Green", "Blue", "Purple"))
            else: widget = ttk.Entry(dialog, textvariable=variable)
            widget.grid(row=row, column=1, sticky="ew", padx=8, pady=4)
        def apply():
            self.advanced_filters = {key: variable.get().strip() for key, variable in variables.items() if variable.get().strip() and variable.get() != "Any"}
            dialog.destroy(); self.refresh_view()
        ttk.Button(dialog, text="Clear", command=lambda: [variable.set("Any" if key in {"orientation", "min_rating", "color"} else "") for key, variable in variables.items()]).grid(row=len(fields), column=0, padx=8, pady=8)
        ttk.Button(dialog, text="Apply", command=apply).grid(row=len(fields), column=1, padx=8, pady=8, sticky="e")
        dialog.columnconfigure(1, weight=1)

    def select_matching(self):
        self.tree.selection_set(self.tree.get_children())
        self.tree.focus(self.tree.get_children()[0] if self.tree.get_children() else "")
        self.update_thumbnail_selection()

    def select_size_outliers(self):
        visible: list[tuple[str, MediaItem]] = []
        for iid in self.tree.get_children():
            tags = self.tree.item(iid, "tags")
            item = self.items.get(tags[0]) if tags else None
            if item and item.megabytes_per_minute is not None:
                visible.append((iid, item))
        if len(visible) < 2:
            messagebox.showinfo("Not enough videos", "At least two visible videos with readable durations are needed for comparison.")
            return
        multiplier = {"Moderate (1.4×)": 1.4, "Large (1.75×)": 1.75, "Extreme (2.5×)": 2.5}.get(self.outlier_sensitivity_var.get(), 1.75)
        average = sum(item.megabytes_per_minute or 0 for _iid, item in visible) / len(visible)
        threshold = average * multiplier
        outliers = [iid for iid, item in visible if (item.megabytes_per_minute or 0) >= threshold]
        self.tree.selection_set(outliers)
        if outliers:
            self.tree.focus(outliers[0])
            self.tree.see(outliers[0])
            self.status_var.set(f"Selected {len(outliers)} size outlier(s) · threshold {threshold:.1f} MB/min · average {average:.1f} MB/min")
        else:
            messagebox.showinfo("No size outliers", f"No visible video is at least {multiplier:g}× the average data rate of {average:.1f} MB/min.")

    def update_checked_label(self):
        if hasattr(self, "checked_label_var"):
            self.checked_label_var.set(f"{len(self.checked_paths)} ticked")

    def refresh_checks(self):
        for iid in self.tree.get_children():
            tags = self.tree.item(iid, "tags")
            path_key = tags[0] if tags else ""
            self.tree.item(iid, text="☑" if path_key in self.checked_paths else "☐")
        self.update_checked_label()
        self.update_thumbnail_selection()

    def clear_checks(self):
        self.checked_paths.clear()
        self.refresh_checks()

    def toggle_all_checks(self):
        visible = {str(item.path) for item in self.visible_items}
        if visible and visible.issubset(self.checked_paths):
            self.checked_paths.difference_update(visible)
        else:
            self.checked_paths.update(visible)
        self.refresh_checks()

    def toggle_focused_check(self, _event=None):
        iid = self.tree.focus()
        tags = self.tree.item(iid, "tags") if iid else ()
        if tags:
            self.toggle_check(tags[0])
        return "break"

    def toggle_check(self, path_key: str):
        if path_key in self.checked_paths:
            self.checked_paths.remove(path_key)
        elif path_key in self.items:
            self.checked_paths.add(path_key)
        iid = self.path_to_iid.get(path_key)
        if iid and self.tree.exists(iid):
            self.tree.item(iid, text="☑" if path_key in self.checked_paths else "☐")
        self.update_checked_label()
        self.update_thumbnail_selection()
        return "break"

    def highlighted_items(self) -> list[MediaItem]:
        result = []
        for iid in self.tree.selection():
            tags = self.tree.item(iid, "tags")
            if tags and tags[0] in self.items:
                result.append(self.items[tags[0]])
        return result

    def selected_items(self) -> list[MediaItem]:
        """Return the ticked action group, or highlighted rows when it is empty."""
        if not self.checked_paths:
            return self.highlighted_items()
        visible_order = [item for item in self.visible_items if str(item.path) in self.checked_paths]
        visible_keys = {str(item.path) for item in visible_order}
        hidden = [self.items[path] for path in sorted(self.checked_paths, key=str.casefold) if path in self.items and path not in visible_keys]
        return visible_order + hidden

    def start_file_drag(self, event):
        local_x = event.x_root - self.tree.winfo_rootx()
        local_y = event.y_root - self.tree.winfo_rooty()
        if self.tree.identify_region(local_x, local_y) != "cell":
            return (REFUSE_DROP, DND_FILES, ())
        row = self.tree.identify_row(local_y)
        if row and row not in self.tree.selection():
            self.tree.selection_set(row)
            self.tree.focus(row)
        files = tuple(str(item.path.resolve()) for item in self.selected_items() if item.path.exists())
        if not files:
            return (REFUSE_DROP, DND_FILES, ())
        self.status_var.set(f"Dragging {len(files)} file(s)…")
        if str(event.button) == "3":
            self.right_drag_completed = True
            return ((ASK, COPY, MOVE, LINK), DND_FILES, files)
        return (COPY, DND_FILES, files)

    def end_file_drag(self, _event):
        self.status_var.set(f"{len(self.items)} media file(s)")
        self.after(200, lambda: setattr(self, "right_drag_completed", False))

    def dropped_paths(self, event) -> list[Path]:
        try:
            return [Path(value) for value in self.tk.splitlist(event.data)]
        except (tk.TclError, TypeError):
            return []

    def drop_files_in_current_folder(self, event):
        return self.copy_dropped_files(self.dropped_paths(event), self.current_path)

    def drop_files_on_folder_tree(self, event):
        local_y = event.y_root - self.folder_tree.winfo_rooty()
        row = self.folder_tree.identify_row(local_y)
        tags = self.folder_tree.item(row, "tags") if row else ()
        target = Path(tags[0]) if tags and tags[0] != "__placeholder__" else self.current_path
        return self.copy_dropped_files(self.dropped_paths(event), target)

    def copy_dropped_files(self, paths: list[Path], destination: Path):
        files = [path for path in paths if path.is_file()]
        if not files or not destination.is_dir():
            return REFUSE_DROP
        pairs = [(path, destination / path.name) for path in files if path.resolve() != (destination / path.name).resolve()]
        self.app.enqueue_operation(pairs, False, f"Drop to {destination}")
        return COPY

    def drop_finished(self, copied: int, errors: list[str]):
        self.scan()
        if errors:
            messagebox.showerror("Some dropped files failed", "\n".join(errors[:10]))
        elif copied:
            self.status_var.set(f"Copied {copied} dropped file(s)")

    def open_selected(self):
        selected = self.selected_items()
        if not selected:
            return
        self.open_items(selected)

    def open_items(self, items: list[MediaItem]):
        for item in items[:10]:
            try:
                if sys.platform == "win32":
                    os.startfile(item.path)  # type: ignore[attr-defined]
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", str(item.path)])
                else:
                    subprocess.Popen(["xdg-open", str(item.path)])
            except OSError as exc:
                messagebox.showerror("Could not open file", str(exc))
                break

    def open_on_double_click(self, event):
        if self.tree.identify_region(event.x, event.y) == "cell":
            highlighted = self.highlighted_items()
            if highlighted: self.open_items([highlighted[0]])

    def reveal_selected(self):
        selected = self.selected_items()
        if not selected:
            return
        paths = [item.path for item in selected]
        if len(paths) > 5 and not messagebox.askyesno(
            "Reveal many files?",
            f"{len(paths)} files are selected. Revealing all of them may open a large number of file-manager windows.\n\n"
            "Choose Yes to reveal every selected file, or No to reveal only the first one.",
            parent=self.winfo_toplevel(),
        ):
            paths = paths[:1]
        errors = []
        for path in paths:
            try:
                if sys.platform == "win32":
                    subprocess.Popen(["explorer", "/select,", str(path)])
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", "-R", str(path)])
                else:
                    subprocess.Popen(["xdg-open", str(path.parent)])
            except OSError as exc:
                errors.append(f"{path.name}: {exc}")
        revealed = len(paths) - len(errors)
        if revealed:
            self.status_var.set(f"Revealed {revealed} selected file(s) in the system file manager")
        if errors:
            messagebox.showerror("Could not reveal some files", "\n".join(errors[:10]))

    def rename_selected(self):
        selected = self.selected_items()
        if len(selected) != 1:
            messagebox.showinfo("Select one file", "Select exactly one file to rename.")
            return
        item = selected[0]
        new_name = simpledialog.askstring("Rename file", "New filename:", initialvalue=item.path.name, parent=self)
        if not new_name or new_name == item.path.name:
            return
        if Path(new_name).name != new_name or new_name in {".", ".."}:
            messagebox.showerror("Invalid filename", "Enter a filename without folder separators.")
            return
        target = item.path.with_name(new_name)
        if target.exists():
            messagebox.showerror("File already exists", f"A file named {new_name} already exists.")
            return
        try:
            item.path.rename(target)
            self.metadata_cache.move_user_data(item.path, target)
            old_key, new_key = str(item.path), str(target)
            if old_key in self.checked_paths:
                self.checked_paths.discard(old_key); self.checked_paths.add(new_key)
            self.app.record_undo("rename", [(target, item.path)])
            self.scan(target)
        except OSError as exc:
            messagebox.showerror("Rename failed", str(exc))

    def media_button_pressed(self, event):
        self.active_callback(self)
        self.dragged_column = None
        self.column_drag_moved = False
        self.resizing_column = None
        region = self.tree.identify_region(event.x, event.y)
        if region == "tree" and self.tree.identify_column(event.x) == "#0":
            iid = self.tree.identify_row(event.y)
            tags = self.tree.item(iid, "tags") if iid else ()
            if tags:
                self.tree.focus_set(); self.tree.focus(iid); self.toggle_check(tags[0])
            return "break"
        if region == "separator":
            displayed_index = int(self.tree.identify_column(event.x)[1:]) - 1
            order = list(self.tree["displaycolumns"])
            if 0 <= displayed_index < len(order):
                self.resizing_column = order[displayed_index]
                self.resize_start_x = event.x
                self.resize_start_width = self.tree.column(self.resizing_column, "width")
                self.tree.configure(cursor="sb_h_double_arrow")
                return "break"
        elif region == "heading":
            displayed_index = int(self.tree.identify_column(event.x)[1:]) - 1
            order = list(self.tree["displaycolumns"])
            if 0 <= displayed_index < len(order):
                self.dragged_column = order[displayed_index]
                self.tree.configure(cursor="fleur")

    def media_button_dragged(self, event):
        if self.resizing_column:
            new_width = max(55, min(2000, self.resize_start_width + event.x - self.resize_start_x))
            self.tree.column(self.resizing_column, width=new_width, stretch=False)
            return "break"
        if not self.dragged_column or self.tree.identify_region(event.x, event.y) != "heading":
            return
        destination = int(self.tree.identify_column(event.x)[1:]) - 1
        order = list(self.tree["displaycolumns"])
        if self.dragged_column not in order or not 0 <= destination < len(order):
            return "break"
        current = order.index(self.dragged_column)
        if current != destination:
            order.pop(current)
            order.insert(destination, self.dragged_column)
            self.tree.configure(displaycolumns=order)
            self.column_drag_moved = True
        return "break"

    def media_button_released(self, _event):
        moved = self.column_drag_moved
        resized = self.resizing_column is not None
        self.dragged_column = None
        self.resizing_column = None
        self.column_drag_moved = False
        self.tree.configure(cursor="")
        if resized:
            self.refresh_view()
            return "break"
        if moved:
            return "break"

    def media_header_motion(self, event):
        if self.dragged_column or self.resizing_column: return
        region = self.tree.identify_region(event.x, event.y)
        self.tree.configure(cursor="sb_h_double_arrow" if region == "separator" else "")

    def reset_column_widths(self):
        defaults = {"name": 230, "rating": 75, "color": 75, "tags": 170, "type": 60, "codec": 105, "resolution": 110, "pixels": 85, "size": 85, "rate": 75, "bitrate": 90, "fps": 60, "audio": 110, "hdr": 55, "modified": 135, "duration": 90}
        for column, width in defaults.items(): self.tree.column(column, width=width, stretch=False)
        self.refresh_view()

    def configure_columns(self):
        window = tk.Toplevel(self); window.title(f"Columns — {self.title}"); window.geometry("470x470"); window.transient(self.winfo_toplevel()); window.grab_set()
        ttk.Label(window, text="Select a column, then move it or set its width.", font=("Segoe UI", 10, "bold")).pack(fill="x", padx=10, pady=(10, 5))
        list_frame = ttk.Frame(window); list_frame.pack(fill="both", expand=True, padx=10)
        listbox = tk.Listbox(list_frame, exportselection=False); listbox.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=listbox.yview); scroll.pack(side="right", fill="y"); listbox.configure(yscrollcommand=scroll.set)
        heading_labels = {column: self.tree.heading(column, "text") for column in self.tree["columns"]}
        order = list(self.tree["displaycolumns"])
        for column in order: listbox.insert("end", heading_labels[column])
        width_var = tk.IntVar(value=self.tree.column(order[0], "width") if order else 100)
        def selected_index():
            selection = listbox.curselection(); return selection[0] if selection else None
        def sync_width(_event=None):
            index = selected_index()
            if index is not None: width_var.set(self.tree.column(order[index], "width"))
        def move(delta: int):
            index = selected_index()
            if index is None or not 0 <= index + delta < len(order): return
            target = index + delta; order[index], order[target] = order[target], order[index]
            label = listbox.get(index); listbox.delete(index); listbox.insert(target, label); listbox.selection_set(target); listbox.see(target)
        def apply_width():
            index = selected_index()
            if index is not None: self.tree.column(order[index], width=max(55, min(2000, width_var.get())), stretch=False)
        listbox.bind("<<ListboxSelect>>", sync_width); listbox.selection_set(0); sync_width()
        controls = ttk.Frame(window); controls.pack(fill="x", padx=10, pady=8)
        ttk.Button(controls, text="Move left", command=lambda: move(-1)).pack(side="left")
        ttk.Button(controls, text="Move right", command=lambda: move(1)).pack(side="left", padx=5)
        ttk.Label(controls, text="Width:").pack(side="left", padx=(15, 3))
        ttk.Spinbox(controls, from_=55, to=2000, textvariable=width_var, width=7).pack(side="left")
        ttk.Button(controls, text="Set width", command=apply_width).pack(side="left", padx=5)
        def save():
            apply_width(); self.tree.configure(displaycolumns=order); window.destroy(); self.refresh_view()
        bottom = ttk.Frame(window); bottom.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(bottom, text="Reset widths", command=self.reset_column_widths).pack(side="left")
        ttk.Button(bottom, text="Cancel", command=window.destroy).pack(side="right")
        ttk.Button(bottom, text="Apply", command=save).pack(side="right", padx=5)

    def selection_changed(self, _event=None):
        self.active_callback(self)
        self.update_thumbnail_selection()
        selected = self.highlighted_items()
        self.update_inspector(selected[0] if selected else None)
        if selected and self.preview_enabled_var.get():
            focused = self.tree.focus()
            tags = self.tree.item(focused, "tags") if focused else ()
            focused_item = self.items.get(tags[0]) if tags else None
            self.preview_callback(focused_item or selected[0])

    def show_context_menu(self, event):
        if self.right_drag_completed:
            self.right_drag_completed = False
            return
        self.active_callback(self)
        if self.tree.identify_region(event.x, event.y) in {"heading", "separator"}:
            self.header_menu.tk_popup(event.x_root, event.y_root)
            return
        row = self.tree.identify_row(event.y)
        if not row:
            self.background_menu.tk_popup(event.x_root, event.y_root)
            return
        # Preserve a multi-file selection when right-clicking anywhere inside it.
        if row not in self.tree.selection():
            self.tree.selection_set(row)
            self.tree.focus(row)
        count = len(self.selected_items())
        suffix = f" ({count} files)" if count > 1 else ""
        self.context_menu.entryconfigure(0, label=f"Copy to other pane{suffix}")
        self.context_menu.entryconfigure(1, label=f"Move to other pane{suffix}")
        self.context_menu.tk_popup(event.x_root, event.y_root)


class PreviewPane(ttk.Frame):
    def __init__(self, master: tk.Misc, title: str = "Scratch preview", workload: WorkloadController | None = None):
        super().__init__(master, padding=(10, 5, 10, 10))
        self.workload = workload or WorkloadController()
        self.workload_source = f"preview-{id(self)}"
        self.item: MediaItem | None = None
        self.generation = 0
        self.photo: tk.PhotoImage | None = None
        self.process: subprocess.Popen | None = None
        self.audio_process: subprocess.Popen | None = None
        self.playing = False
        self.playback_speed = 4.0
        self.muted = True
        self.speed_buttons: dict[float, ttk.Button] = {}
        self.started_at = 0.0
        self.start_seconds = 0.0
        self.frame_queue: queue.Queue = queue.Queue(maxsize=1)
        self.still_queue: queue.Queue = queue.Queue()
        self.still_processes: dict[int, subprocess.Popen] = {}
        self.still_process_lock = threading.Lock()
        self.still_cache: dict[tuple, Path] = {}
        self.scrub_job: str | None = None
        self.preview_resize_job: str | None = None
        self.last_preview_dimensions = (0, 0)
        self.temp_dir = tempfile.TemporaryDirectory(prefix="resolution-preview-")

        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 4))
        ttk.Label(header, text=title, style="PaneTitle.TLabel").pack(side="left")
        self.info_var = tk.StringVar(value="Preview is off")
        ttk.Label(header, textvariable=self.info_var).pack(side="left", padx=12)

        self.preview_label = tk.Label(self, text="Preview off", bg="#171717", fg="#dddddd", height=12)
        self.preview_label.pack(fill="both", expand=True)
        self.preview_label.bind("<Configure>", self.preview_resized)

        controls = ttk.Frame(self)
        controls.pack(fill="x", pady=(5, 0))
        self.play_button = ttk.Button(controls, text="▶ Play", width=9, command=self.toggle_playback)
        self.play_button.pack(side="left")
        ttk.Label(controls, text="Skim:").pack(side="left")
        self.position_var = tk.DoubleVar(value=0)
        self.slider = ttk.Scale(controls, from_=0, to=100, variable=self.position_var)
        self.slider.pack(side="left", fill="x", expand=True, padx=8)
        self.slider.bind("<ButtonPress-1>", self.slider_pressed)
        self.slider.bind("<B1-Motion>", self.slider_dragged)
        self.slider.bind("<ButtonRelease-1>", self.slider_released)
        self.time_var = tk.StringVar(value="—")
        ttk.Label(controls, textvariable=self.time_var, width=18).pack(side="right")

        playback_options = ttk.Frame(self)
        playback_options.pack(fill="x", pady=(4, 0))
        ttk.Label(playback_options, text="Speed:").pack(side="left")
        for speed in (1, 2, 4, 6, 8, 16):
            button = ttk.Button(playback_options, text=f"{speed}×", width=4, command=lambda value=float(speed): self.set_playback_speed(value))
            button.pack(side="left", padx=(4, 0))
            self.speed_buttons[float(speed)] = button
        self.mute_button = ttk.Button(playback_options, text="🔇 Muted", width=10, command=self.toggle_mute)
        self.mute_button.pack(side="left", padx=(10, 0))
        self.previous_frame_button = ttk.Button(playback_options, text="|◀", width=4, command=lambda: self.step_frame(-1), state="disabled")
        self.previous_frame_button.pack(side="left", padx=(10, 0))
        self.next_frame_button = ttk.Button(playback_options, text="▶|", width=4, command=lambda: self.step_frame(1), state="disabled")
        self.next_frame_button.pack(side="left", padx=(4, 0))
        self.export_frame_button = ttk.Button(playback_options, text="⤓ PNG", width=7, command=self.export_current_frame, state="disabled")
        self.export_frame_button.pack(side="left", padx=(8, 0))
        self.update_speed_buttons()
        self.after(50, self.poll_playback)

    def disable(self):
        self.stop_playback()
        self.cancel_still_renders()
        self.item = None
        self.photo = None
        self.preview_label.configure(image="", text="Preview off")
        self.info_var.set("Preview is off")
        self.position_var.set(0)
        self.slider.state(["disabled"])
        self.play_button.configure(text="▶ Play", state="disabled")
        self.previous_frame_button.configure(state="disabled"); self.next_frame_button.configure(state="disabled"); self.export_frame_button.configure(state="disabled")
        self.time_var.set("—")

    def enable(self):
        if self.item is None:
            self.preview_label.configure(image="", text="Select a file to preview")
            self.info_var.set("Select an image or video on this side")

    def show_item(self, item: MediaItem):
        if self.item and self.item.path == item.path:
            return
        self.stop_playback()
        self.cancel_still_renders()
        self.item = item
        self.position_var.set(0)
        duration_text = human_duration(item.duration)
        details = f"{item.path.name}  ·  {item.resolution}  ·  {human_size(item.size)}"
        if item.duration is not None:
            details += f"  ·  {duration_text}"
        self.info_var.set(details)
        self.slider.state(["!disabled"] if item.duration else ["disabled"])
        self.time_var.set(f"0:00 / {duration_text}" if item.duration else "Still image")
        if item.path.suffix.lower() in VIDEO_EXTENSIONS and item.duration:
            self.previous_frame_button.configure(state="normal"); self.next_frame_button.configure(state="normal"); self.export_frame_button.configure(state="normal")
            self.start_video(0)
        else:
            self.play_button.configure(text="▶ Play", state="disabled")
            self.previous_frame_button.configure(state="disabled"); self.next_frame_button.configure(state="disabled"); self.export_frame_button.configure(state="disabled")
            self.render_still(0)

    def set_slider_from_pointer(self, event) -> None:
        try:
            value = float(self.slider.get(event.x, event.y))
        except (AttributeError, TypeError, ValueError, tk.TclError):
            return
        self.position_var.set(max(0.0, min(100.0, value)))

    def slider_pressed(self, event=None):
        if not self.item or not self.item.duration:
            return "break"
        if event is not None:
            self.set_slider_from_pointer(event)
        self.stop_playback()
        self.cancel_still_renders()
        seconds = self.item.duration * self.position_var.get() / 100
        self.update_time(seconds)
        return "break"

    def slider_dragged(self, event=None):
        if not self.item or not self.item.duration:
            return "break"
        if event is not None:
            self.set_slider_from_pointer(event)
        seconds = self.item.duration * self.position_var.get() / 100
        self.update_time(seconds)
        if self.scrub_job:
            self.after_cancel(self.scrub_job)
        self.scrub_job = self.after(80, lambda: self.render_still(seconds, loading_text=False))
        return "break"

    def slider_released(self, event=None):
        if not self.item or not self.item.duration:
            return "break"
        if event is not None:
            self.set_slider_from_pointer(event)
        if self.scrub_job:
            self.after_cancel(self.scrub_job)
            self.scrub_job = None
        self.cancel_still_renders()
        seconds = self.item.duration * self.position_var.get() / 100
        self.start_video(seconds)
        return "break"

    def toggle_playback(self):
        if not self.item or not self.item.duration:
            return
        if self.playing:
            seconds = min(self.item.duration, self.current_playback_seconds())
            self.stop_playback()
            self.position_var.set(seconds / self.item.duration * 100)
            self.update_time(seconds)
            self.render_still(seconds, loading_text=False)
        else:
            self.start_video(self.item.duration * self.position_var.get() / 100)

    def current_playback_seconds(self) -> float:
        return self.start_seconds + (time.monotonic() - self.started_at) * self.playback_speed

    def update_speed_buttons(self):
        for speed, button in self.speed_buttons.items():
            button.configure(state="disabled" if speed == self.playback_speed else "normal")

    def set_playback_speed(self, speed: float):
        if speed == self.playback_speed:
            return
        seconds = self.current_playback_seconds() if self.playing else (
            self.item.duration * self.position_var.get() / 100 if self.item and self.item.duration else 0
        )
        was_playing = self.playing
        self.playback_speed = speed
        self.update_speed_buttons()
        if was_playing:
            self.start_video(seconds)

    def toggle_mute(self):
        self.muted = not self.muted
        self.mute_button.configure(text="🔇 Muted" if self.muted else "🔊 Audio")
        self.stop_audio()
        if not self.muted and self.playing:
            self.start_audio(self.current_playback_seconds())

    def preview_position_seconds(self) -> float:
        if not self.item or not self.item.duration: return 0.0
        return min(self.item.duration, self.current_playback_seconds()) if self.playing else self.item.duration * self.position_var.get() / 100

    def step_frame(self, direction: int):
        if not self.item or not self.item.duration or self.item.path.suffix.lower() not in VIDEO_EXTENSIONS: return
        seconds = self.preview_position_seconds()
        self.stop_playback(); self.cancel_still_renders()
        frame_duration = 1.0 / (self.item.frame_rate or 25.0)
        seconds = max(0.0, min(max(0.0, self.item.duration - frame_duration), seconds + direction * frame_duration))
        self.position_var.set(seconds / self.item.duration * 100); self.update_time(seconds)
        self.render_still(seconds, loading_text=False, precise=True)

    def jump_percent(self, fraction: float) -> bool:
        """Move by a fraction of the clip while preserving play/pause state."""
        if not self.item or not self.item.duration or self.item.path.suffix.lower() not in VIDEO_EXTENSIONS:
            return False
        was_playing = self.playing
        seconds = self.preview_position_seconds() + self.item.duration * fraction
        frame_duration = 1.0 / (self.item.frame_rate or 25.0)
        seconds = max(0.0, min(max(0.0, self.item.duration - frame_duration), seconds))
        self.stop_playback(); self.cancel_still_renders()
        self.position_var.set(seconds / self.item.duration * 100); self.update_time(seconds)
        if was_playing: self.start_video(seconds)
        else: self.render_still(seconds, loading_text=False, precise=True)
        return True

    @staticmethod
    def save_video_frame(item: MediaItem, seconds: float, output: Path, cancel_event: threading.Event) -> tuple[str, str]:
        temporary = output.with_name(f"{output.stem}.{threading.get_ident()}.tmp.png")
        command = [bundled_command("ffmpeg"), "-v", "error", "-i", str(item.path), "-ss", f"{seconds:.6f}", "-frames:v", "1", "-y", str(temporary)]
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        process = None
        try:
            process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, creationflags=flags)
            while process.poll() is None:
                if cancel_event.wait(0.05):
                    process.terminate()
                    try: process.wait(timeout=2)
                    except subprocess.TimeoutExpired: process.kill(); process.wait()
                    try: temporary.unlink()
                    except OSError: pass
                    return "Cancelled", "Frame export cancelled"
            error = (process.stderr.read() if process.stderr else b"").decode("utf-8", errors="replace").strip()
            if process.returncode or not temporary.exists():
                try: temporary.unlink()
                except OSError: pass
                return "Failed", error[-2000:] or "FFmpeg did not produce a frame"
            output.parent.mkdir(parents=True, exist_ok=True); os.replace(temporary, output)
            return "Passed", f"Saved frame at {human_duration(seconds)} to {output}"
        except OSError as exc:
            try: temporary.unlink()
            except OSError: pass
            return "Failed", str(exc)

    def export_current_frame(self):
        if not self.item or not self.item.duration or self.item.path.suffix.lower() not in VIDEO_EXTENSIONS: return
        seconds = self.preview_position_seconds()
        if self.playing:
            self.stop_playback(); self.position_var.set(seconds / self.item.duration * 100); self.update_time(seconds); self.render_still(seconds, loading_text=False, precise=True)
        chosen = filedialog.asksaveasfilename(parent=self.winfo_toplevel(), title="Export current video frame", initialfile=f"{self.item.path.stem} - {seconds:.3f}s.png", defaultextension=".png", filetypes=(("PNG image", "*.png"),))
        if not chosen: return
        item = self.item; cancel_event = threading.Event(); self.export_frame_button.configure(state="disabled"); self.info_var.set(f"Exporting frame at {human_duration(seconds)}…")
        def worker():
            state, details = self.save_video_frame(item, seconds, Path(chosen), cancel_event)
            def finished():
                if not self.winfo_exists(): return
                self.export_frame_button.configure(state="normal" if self.item and self.item.path.suffix.lower() in VIDEO_EXTENSIONS else "disabled")
                self.info_var.set(details)
                if state == "Passed": messagebox.showinfo("Frame exported", details, parent=self.winfo_toplevel())
                elif state == "Failed": messagebox.showerror("Frame export failed", details, parent=self.winfo_toplevel())
            self.after(0, finished)
        threading.Thread(target=worker, daemon=True).start()

    def start_video(self, seconds: float):
        if not self.item or not self.item.duration:
            return
        self.stop_playback()
        self.cancel_still_renders()
        self.generation += 1
        generation = self.generation
        width, height = self.preview_dimensions(self.item)
        self.last_preview_dimensions = (width, height)
        output_fps = max(0.5, float(self.workload.settings["preview_fps"]) / self.playback_speed)
        command = [
            bundled_command("ffmpeg"), "-v", "error", "-ss", str(seconds), "-readrate", str(self.playback_speed), "-i", str(self.item.path),
            "-an", "-vf", f"fps={output_fps:g},scale={width}:{height}", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1",
        ]
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        try:
            self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, creationflags=flags)
        except Exception as exc:
            self.preview_label.configure(image="", text=f"Preview unavailable\n{exc}")
            return
        self.playing = True
        self.workload.set_interactive(self.workload_source, True)
        self.start_seconds = seconds
        self.started_at = time.monotonic()
        self.play_button.configure(text="Ⅱ Pause", state="normal")
        if not self.muted:
            self.start_audio(seconds)
        frame_size = width * height * 3
        playback_process = self.process

        def reader():
            assert playback_process.stdout
            stream = playback_process.stdout
            while generation == self.generation:
                frame = stream.read(frame_size)
                if len(frame) != frame_size:
                    break
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass
                try:
                    self.frame_queue.put_nowait((generation, width, height, frame))
                except queue.Full:
                    pass

        threading.Thread(target=reader, daemon=True).start()

    def start_audio(self, seconds: float):
        if not self.item or self.muted:
            return
        self.stop_audio()
        command = [
            bundled_command("ffplay"), "-v", "error", "-nodisp", "-autoexit", "-vn",
            "-ss", str(seconds), "-af", f"atempo={self.playback_speed:g}", str(self.item.path),
        ]
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        try:
            self.audio_process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)
        except OSError:
            self.audio_process = None
            self.muted = True
            self.mute_button.configure(text="🔇 Unavailable")

    def stop_audio(self):
        process, self.audio_process = self.audio_process, None
        if process and process.poll() is None:
            try: process.terminate()
            except OSError: pass

    def preview_dimensions(self, item: MediaItem) -> tuple[int, int]:
        source_width, source_height = item.width or 640, item.height or 360
        available_width = self.preview_label.winfo_width()
        available_height = self.preview_label.winfo_height()
        if available_width < 10: available_width = 640
        if available_height < 10: available_height = 250
        scale = min(available_width / source_width, available_height / source_height)
        return max(2, int(source_width * scale) // 2 * 2), max(2, int(source_height * scale) // 2 * 2)

    def preview_resized(self, _event=None):
        if not self.item:
            return
        dimensions = self.preview_dimensions(self.item)
        if dimensions == self.last_preview_dimensions:
            return
        if self.preview_resize_job:
            try: self.after_cancel(self.preview_resize_job)
            except tk.TclError: pass
        self.preview_resize_job = self.after(180, self.apply_preview_resize)

    def apply_preview_resize(self):
        self.preview_resize_job = None
        if not self.item:
            return
        dimensions = self.preview_dimensions(self.item)
        if dimensions == self.last_preview_dimensions:
            return
        seconds = self.current_playback_seconds() if self.playing else (
            self.item.duration * self.position_var.get() / 100 if self.item.duration else 0
        )
        if self.playing: self.start_video(seconds)
        else: self.render_still(seconds, loading_text=False)

    def stop_playback(self):
        self.playing = False
        self.workload.set_interactive(self.workload_source, False)
        self.generation += 1
        self.stop_audio()
        process, self.process = self.process, None
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=0.2)
            except subprocess.TimeoutExpired:
                process.kill()
        if process and process.stdout:
            try: process.stdout.close()
            except OSError: pass
        self.play_button.configure(text="▶ Play")

    def cancel_still_renders(self):
        """Stop obsolete scrub decoders so they cannot compete with playback."""
        with self.still_process_lock:
            processes = list(self.still_processes.values())
            self.still_processes.clear()
        for process in processes:
            if process.poll() is None:
                try: process.terminate()
                except OSError: pass

    def poll_playback(self):
        try:
            while True:
                generation, output, error, cache_key = self.still_queue.get_nowait()
                self.finish_render(generation, output, error, cache_key)
        except queue.Empty:
            pass
        try:
            while True:
                generation, width, height, frame = self.frame_queue.get_nowait()
                if generation == self.generation:
                    ppm = f"P6 {width} {height} 255\n".encode("ascii") + frame
                    self.photo = tk.PhotoImage(data=ppm, format="PPM")
                    self.preview_label.configure(image=self.photo, text="")
        except queue.Empty:
            pass
        if self.playing and self.item and self.item.duration:
            seconds = min(self.item.duration, self.current_playback_seconds())
            self.position_var.set(seconds / self.item.duration * 100)
            self.update_time(seconds)
            if seconds >= self.item.duration:
                self.start_video(0)
        self.after(50, self.poll_playback)

    def update_time(self, seconds: float):
        if self.item and self.item.duration:
            self.time_var.set(f"{human_duration(seconds)} / {human_duration(self.item.duration)}")

    def render_still(self, seconds: float, loading_text: bool = True, precise: bool = False):
        if not self.item:
            return
        self.generation += 1
        generation = self.generation
        item_path = self.item.path
        width, height = self.preview_dimensions(self.item)
        self.last_preview_dimensions = (width, height)
        output = Path(self.temp_dir.name) / f"preview-{generation}.png"
        cache_position = round(seconds, 6) if precise else round(seconds * 4) / 4
        cache_key = (str(item_path), self.item.size, self.item.modified, cache_position, width, height)
        cached = self.still_cache.get(cache_key)
        if cached and cached.exists():
            self.finish_render(generation, cached, "", cache_key)
            return
        self.cancel_still_renders()
        if loading_text:
            self.preview_label.configure(image="", text="Loading preview…")

        def worker():
            still_source = f"{self.workload_source}-still-{generation}"
            self.workload.set_interactive(still_source, True)
            command = [bundled_command("ffmpeg"), "-v", "error"]
            if item_path.suffix.lower() in VIDEO_EXTENSIONS and not precise:
                command += ["-ss", str(seconds)]
            command += ["-i", str(item_path)]
            if item_path.suffix.lower() in VIDEO_EXTENSIONS and precise:
                command += ["-ss", f"{seconds:.6f}"]
            command += ["-frames:v", "1", "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease", "-y", str(output)]
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            process = None
            try:
                process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, creationflags=flags)
                with self.still_process_lock:
                    if generation != self.generation:
                        process.terminate()
                    else:
                        self.still_processes[generation] = process
                _stdout, stderr = process.communicate(timeout=30)
                error = (stderr or "").strip() if process.returncode else ""
            except subprocess.TimeoutExpired:
                if process:
                    process.kill()
                    process.communicate()
                error = "Preview seek timed out"
            except Exception as exc:
                error = str(exc)
            finally:
                with self.still_process_lock:
                    self.still_processes.pop(generation, None)
                self.workload.set_interactive(still_source, False)
            self.still_queue.put((generation, output, error, cache_key))

        threading.Thread(target=worker, daemon=True).start()

    def finish_render(self, generation: int, output: Path, error: str, cache_key: tuple):
        if generation != self.generation:
            return
        if error or not output.exists():
            self.preview_label.configure(image="", text=f"Preview unavailable\n{error or 'Could not read frame'}")
            return
        try:
            self.photo = tk.PhotoImage(file=output)
            self.preview_label.configure(image=self.photo, text="")
            if self.item:
                self.still_cache[cache_key] = output
                while len(self.still_cache) > 120:
                    self.still_cache.pop(next(iter(self.still_cache)))
        except tk.TclError as exc:
            self.preview_label.configure(image="", text=f"Preview unavailable\n{exc}")


class MediaSorterApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.data_directory = application_data_directory()
        self.settings_path = self.data_directory / "settings.json"
        self.settings = load_json(self.settings_path, {})
        self.performance_profile = str(self.settings.get("performance_profile", "Balanced"))
        if self.performance_profile not in PERFORMANCE_PROFILES: self.performance_profile = "Balanced"
        self.workload = WorkloadController(self.performance_profile)
        profile_defaults = PERFORMANCE_PROFILES[self.performance_profile]
        try: self.scan_workers = max(1, min(16, int(self.settings.get("scan_workers", profile_defaults["scan_workers"]))))
        except (ValueError, TypeError): self.scan_workers = int(profile_defaults["scan_workers"])
        self.excluded_patterns = list(self.settings.get("excluded_patterns", []))
        self.metadata_cache = MetadataCache(
            self.data_directory / "metadata-cache.sqlite3",
            self.data_directory / "metadata-cache.json",
        )
        self.workspaces_path = self.data_directory / "workspaces.json"
        self.workspaces = load_json(self.workspaces_path, {})
        self.smart_collections_path = self.data_directory / "smart-collections.json"
        self.smart_collections = load_json(self.smart_collections_path, {})
        if not isinstance(self.smart_collections, dict): self.smart_collections = {}
        self.folder_rules_path = self.data_directory / "folder-rules.json"
        self.folder_rules = load_json(self.folder_rules_path, [])
        if not isinstance(self.folder_rules, list): self.folder_rules = []
        self.undo_directory = self.data_directory / "undo"
        self.undo_directory.mkdir(exist_ok=True)
        self.thumbnail_directory = self.data_directory / "thumbnails"
        self.thumbnail_directory.mkdir(exist_ok=True)
        try: self.thumbnail_cache_percent = max(0.1, min(10.0, float(self.settings.get("thumbnail_cache_percent", 1.0))))
        except (ValueError, TypeError): self.thumbnail_cache_percent = 1.0
        self.thumbnail_prune_lock = threading.Lock()
        self.thumbnail_write_count = 0
        self.thumbnail_cache_epoch = 0
        self.thumbnail_workers = int(profile_defaults["thumbnail_workers"])
        self.thumbnail_executor = ThreadPoolExecutor(max_workers=self.thumbnail_workers, thread_name_prefix="thumbnail")
        self.undo_stack: list[tuple[str, list]] = []
        self.file_clipboard: tuple[list[Path], bool] = ([], False)
        self.operation_queue: queue.Queue = queue.Queue()
        self.ui_events: queue.Queue = queue.Queue()
        self.operation_running = False
        self.operation_cancel = threading.Event()
        self.operation_paused = False
        self.operation_window: tk.Toplevel | None = None
        self.last_failed_operation: dict | None = None
        self.title(f"Resolution File Manager {APP_VERSION}")
        apply_application_icon(self)
        try: self.geometry(self.settings.get("geometry", "1300x900"))
        except tk.TclError: self.geometry("1300x900")
        self.minsize(950, 650)
        self.base_tk_scaling = float(self.tk.call("tk", "scaling"))
        self.base_named_font_sizes = {}
        for font_name in tkfont.names(self):
            try: self.base_named_font_sizes[font_name] = int(tkfont.nametofont(font_name, root=self).cget("size"))
            except (tk.TclError, ValueError, TypeError): pass
        self.appearance_theme = str(self.settings.get("appearance_theme", "System"))
        try: self.ui_scale = int(self.settings.get("ui_scale", 100))
        except (ValueError, TypeError): self.ui_scale = 100
        self.apply_appearance(self.appearance_theme, self.ui_scale)
        self.active_pane: FilePane | None = None
        self.create_menu_bar()

        toolbar = ttk.Frame(self, padding=(10, 8))
        toolbar.pack(fill="x")
        ttk.Label(toolbar, text="Choose files in either pane, then send them to the other pane.").pack(side="left")
        ttk.Button(toolbar, text="Undo", command=self.undo_last).pack(side="right", padx=4)
        ttk.Button(toolbar, text="Copy selected → other pane", command=lambda: self.transfer(False)).pack(side="right", padx=4)
        ttk.Button(toolbar, text="Move selected → other pane", command=lambda: self.transfer(True)).pack(side="right", padx=4)
        ttk.Button(toolbar, text="Refresh", command=self.refresh).pack(side="right", padx=4)

        workspace = tk.PanedWindow(
            self,
            orient=tk.VERTICAL,
            sashwidth=3,
            sashrelief=tk.FLAT,
            showhandle=False,
            opaqueresize=True,
            bg="#a0a0a0",
            bd=0,
        )
        self.workspace_panes = workspace
        workspace.pack(fill="both", expand=True)
        panes = tk.PanedWindow(
            workspace,
            orient=tk.HORIZONTAL,
            sashwidth=3,
            sashrelief=tk.FLAT,
            showhandle=False,
            opaqueresize=True,
            bg="#a0a0a0",
            bd=0,
        )
        self.browser_panes = panes
        self.preview_split_position = int(self.settings.get("preview_split", 600))
        left_state = self.settings.get("left", {})
        right_state = self.settings.get("right", {})
        left_path = Path(left_state.get("path", Path.home()))
        right_path = Path(right_state.get("path", Path.home()))
        if not left_path.is_dir():
            left_path = Path.home()
        if not right_path.is_dir():
            right_path = Path.home()
        self.preview_area = tk.PanedWindow(
            workspace, orient=tk.HORIZONTAL, sashwidth=3, sashrelief=tk.FLAT,
            showhandle=False, opaqueresize=True, bg="#a0a0a0", bd=0,
        )
        self.left_preview = PreviewPane(self.preview_area, "Left preview", self.workload)
        self.right_preview = PreviewPane(self.preview_area, "Right preview", self.workload)
        self.left_preview.disable()
        self.right_preview.disable()
        self.preview_area.add(self.left_preview, stretch="always", minsize=300)
        self.preview_area.add(self.right_preview, stretch="always", minsize=300)
        self.left = FilePane(panes, "Left pane", left_path, self.set_active, self.transfer_from, self.left_preview.show_item, self.set_pane_preview, self.metadata_cache, left_state)
        self.right = FilePane(panes, "Right pane", right_path, self.set_active, self.transfer_from, self.right_preview.show_item, self.set_pane_preview, self.metadata_cache, right_state)
        panes.add(self.left, stretch="always", minsize=350)
        panes.add(self.right, stretch="always", minsize=350)
        workspace.add(panes, stretch="always", minsize=400)
        self.set_active(self.left)
        self.protocol("WM_DELETE_WINDOW", self.close_app)
        self.after(300, self.restore_layout)
        self.after(50, self.poll_ui_events)
        self.after(1000, self.request_thumbnail_cache_prune)
        self.bind_all("<Control-a>", lambda _event: self.current_pane().select_matching())
        self.bind_all("<Control-c>", lambda _event: self.copy_to_clipboard(False))
        self.bind_all("<Control-x>", lambda _event: self.copy_to_clipboard(True))
        self.bind_all("<Control-v>", lambda _event: self.paste_clipboard())
        self.bind_all("<Control-z>", lambda _event: self.undo_last())
        self.bind_all("<F5>", lambda _event: self.refresh())
        self.bind_all("<BackSpace>", self.keyboard_go_up)
        self.bind_all("<Delete>", self.keyboard_delete)
        self.bind_all("<Key-comma>", lambda event: self.keyboard_preview_jump(event, -0.10))
        self.bind_all("<Key-period>", lambda event: self.keyboard_preview_jump(event, 0.10))

    def create_menu_bar(self):
        menu_bar = tk.Menu(self)
        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="Browse active pane…", command=lambda: self.current_pane().choose_folder())
        file_menu.add_command(label="Refresh", accelerator="F5", command=self.refresh)
        file_menu.add_separator(); file_menu.add_command(label="Exit", command=self.close_app)
        menu_bar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menu_bar, tearoff=False)
        edit_menu.add_command(label="Copy", accelerator="Ctrl+C", command=lambda: self.copy_to_clipboard(False))
        edit_menu.add_command(label="Cut", accelerator="Ctrl+X", command=lambda: self.copy_to_clipboard(True))
        edit_menu.add_command(label="Paste", accelerator="Ctrl+V", command=self.paste_clipboard)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self.undo_last)
        edit_menu.add_separator()
        edit_menu.add_command(label="Rename…", accelerator="F2", command=lambda: self.current_pane().rename_selected())
        edit_menu.add_command(label="Batch rename selected…", command=self.batch_rename_selected)
        edit_menu.add_command(label="Move to Recycle Bin / Trash", accelerator="Delete", command=self.delete_selected)
        edit_menu.add_command(label="Select all shown", accelerator="Ctrl+A", command=lambda: self.current_pane().select_matching())
        menu_bar.add_cascade(label="Edit", menu=edit_menu)

        view_menu = tk.Menu(menu_bar, tearoff=False)
        view_menu.add_command(label="Details in active pane", command=lambda: self.current_pane().set_view_mode("Details"))
        view_menu.add_command(label="Thumbnails in active pane", command=lambda: self.current_pane().set_view_mode("Thumbnails"))
        size_menu = tk.Menu(view_menu, tearoff=False)
        for size in ("Small", "Medium", "Large"):
            size_menu.add_command(label=size, command=lambda value=size: self.set_active_thumbnail_size(value))
        view_menu.add_cascade(label="Thumbnail size", menu=size_menu)
        view_menu.add_command(label="Configure columns…", command=lambda: self.current_pane().configure_columns())
        view_menu.add_command(label="Appearance and text size…", command=self.appearance_controls)
        view_menu.add_separator()
        view_menu.add_command(label="Refresh active pane", command=lambda: self.current_pane().refresh_browser())
        view_menu.add_command(label="Refresh both panes", accelerator="F5", command=self.refresh)
        view_menu.add_command(label="Go up", accelerator="Backspace", command=lambda: self.current_pane().go_up())
        menu_bar.add_cascade(label="View", menu=view_menu)

        tools_menu = tk.Menu(menu_bar, tearoff=False)
        tools_menu.add_command(label="Verify media integrity…", command=self.verify_media_integrity)
        tools_menu.add_command(label="Create video contact sheet…", command=self.create_video_contact_sheet)
        tools_menu.add_command(label="Export media report…", command=self.export_media_report)
        tools_menu.add_command(label="View embedded metadata…", command=self.view_embedded_metadata)
        tools_menu.add_command(label="Convert selected videos…", command=self.convert_selected_videos)
        tools_menu.add_separator()
        tools_menu.add_command(label="Find duplicates…", command=self.find_duplicates)
        tools_menu.add_command(label="Find visually similar images…", command=self.find_similar_images)
        tools_menu.add_command(label="Compare selected…", command=self.compare_selected)
        tools_menu.add_command(label="Compare / synchronize folders…", command=self.compare_folders)
        tools_menu.add_separator()
        tools_menu.add_command(label="Save workspace…", command=self.save_workspace)
        tools_menu.add_command(label="Load workspace…", command=self.load_workspace)
        tools_menu.add_command(label="Save active smart collection…", command=self.save_smart_collection)
        tools_menu.add_command(label="Manage smart collections…", command=self.manage_smart_collections)
        tools_menu.add_command(label="Folder organization rules…", command=self.manage_folder_rules)
        tools_menu.add_command(label="Cache and scanning…", command=self.cache_controls)
        tools_menu.add_command(label="Transfer queue…", command=self.show_operation_window)
        menu_bar.add_cascade(label="Tools", menu=tools_menu)

        help_menu = tk.Menu(menu_bar, tearoff=False)
        help_menu.add_command(label="How to use Resolution File Manager", command=self.show_help)
        help_menu.add_command(label="Keyboard shortcuts", command=self.show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="☕ If you like this, buy John a coffee…", command=self.open_support_page)
        help_menu.add_separator(); help_menu.add_command(label="About", command=self.show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        self.configure(menu=menu_bar)

    def open_support_page(self):
        try:
            if not webbrowser.open_new_tab(SUPPORT_URL):
                raise OSError("No web browser accepted the request")
        except (OSError, webbrowser.Error) as exc:
            messagebox.showerror("Could not open support page", f"Open this address in your web browser:\n\n{SUPPORT_URL}\n\n{exc}", parent=self)

    def show_about(self):
        window = tk.Toplevel(self); window.title("About Resolution File Manager"); window.geometry("480x285"); window.resizable(False, False); window.transient(self); window.grab_set()
        body = ttk.Frame(window, padding=18); body.pack(fill="both", expand=True)
        ttk.Label(body, text="Resolution File Manager", font=("Segoe UI", 16, "bold")).pack(anchor="center")
        ttk.Label(body, text=f"Version {APP_VERSION}", font=("Segoe UI", 10, "bold")).pack(anchor="center", pady=(3, 10))
        ttk.Label(body, text="A cross-platform dual-pane application for browsing, previewing, analysing and organising image and video collections.", wraplength=430, justify="center").pack(fill="x")
        support = ttk.LabelFrame(body, text="Support development", padding=10); support.pack(fill="x", pady=(16, 10))
        ttk.Label(support, text="If Resolution File Manager is useful to you, you can buy John a coffee. Support is entirely optional.", wraplength=390, justify="center").pack(fill="x")
        ttk.Button(support, text="☕ Buy John a coffee", command=self.open_support_page).pack(pady=(8, 0))
        ttk.Label(support, text=SUPPORT_URL).pack(pady=(4, 0))
        ttk.Button(body, text="Close", command=window.destroy).pack()
        window.bind("<Escape>", lambda _event: window.destroy())

    def set_active_thumbnail_size(self, size: str):
        pane = self.current_pane(); pane.thumbnail_size_var.set(size); pane.render_thumbnail_grid()

    def apply_appearance(self, theme: str, scale: int):
        theme = theme if theme in {"System", "Light", "Dark", "High contrast"} else "System"
        scale = scale if scale in {100, 125, 150, 175, 200} else 100
        self.appearance_theme, self.ui_scale = theme, scale
        self.tk.call("tk", "scaling", self.base_tk_scaling * scale / 100)
        # Reconfiguring named fonts forces existing widgets to recalculate their
        # metrics after tk scaling changes; leaving them untouched only affects
        # widgets created later on some Windows Tk builds.
        for font_name, base_size in self.base_named_font_sizes.items():
            try: tkfont.nametofont(font_name, root=self).configure(size=base_size)
            except tk.TclError: pass
        style = ttk.Style(self)
        if theme == "System":
            preferred = "vista" if sys.platform == "win32" and "vista" in style.theme_names() else ("aqua" if sys.platform == "darwin" and "aqua" in style.theme_names() else "clam")
            style.theme_use(preferred); self.option_clear()
            style.configure("PaneTitle.TLabel", font=("Segoe UI", 12, "bold"))
            style.configure("PaneToggle.Toolbutton", font=("Segoe UI", 10, "bold"), padding=(10, 6))
            try: self.configure(background=style.lookup("TFrame", "background") or "SystemButtonFace")
            except tk.TclError: pass
        else:
            style.theme_use("clam")
            palette = {
                "Light": {"bg": "#f5f5f5", "field": "#ffffff", "fg": "#202020", "muted": "#e6e6e6", "select": "#2864b4", "selectfg": "#ffffff"},
                "Dark": {"bg": "#252526", "field": "#1e1e1e", "fg": "#eeeeee", "muted": "#333333", "select": "#3f78b5", "selectfg": "#ffffff"},
                "High contrast": {"bg": "#000000", "field": "#000000", "fg": "#ffffff", "muted": "#111111", "select": "#ffff00", "selectfg": "#000000"},
            }[theme]
            bg, field, fg, muted, select, selectfg = (palette[key] for key in ("bg", "field", "fg", "muted", "select", "selectfg"))
            style.configure(".", background=bg, foreground=fg, fieldbackground=field)
            for name in ("TFrame", "TLabel", "TCheckbutton", "TRadiobutton", "TLabelframe", "TLabelframe.Label"): style.configure(name, background=bg, foreground=fg)
            style.configure("TButton", background=muted, foreground=fg, padding=4); style.map("TButton", background=[("active", select)], foreground=[("active", selectfg)])
            style.configure("TEntry", fieldbackground=field, foreground=fg, insertcolor=fg); style.configure("TCombobox", fieldbackground=field, foreground=fg)
            style.configure("Treeview", background=field, fieldbackground=field, foreground=fg); style.map("Treeview", background=[("selected", select)], foreground=[("selected", selectfg)])
            style.configure("Treeview.Heading", background=muted, foreground=fg); style.map("Treeview.Heading", background=[("active", select)], foreground=[("active", selectfg)])
            style.configure("PaneTitle.TLabel", background=bg, foreground=fg, font=("Segoe UI", 12, "bold"))
            style.configure("PaneToggle.Toolbutton", background=muted, foreground=fg, font=("Segoe UI", 10, "bold"), padding=(10, 6))
            style.map("PaneToggle.Toolbutton", background=[("selected", select), ("active", select)], foreground=[("selected", selectfg), ("active", selectfg)])
            self.option_add("*Menu.background", bg); self.option_add("*Menu.foreground", fg); self.option_add("*Menu.activeBackground", select); self.option_add("*Menu.activeForeground", selectfg)
            self.option_add("*Text.background", field); self.option_add("*Text.foreground", fg); self.option_add("*Listbox.background", field); self.option_add("*Listbox.foreground", fg)
            self.configure(background=bg)
        try: self.update_idletasks()
        except tk.TclError: pass

    def appearance_controls(self):
        original = (self.appearance_theme, self.ui_scale)
        window = tk.Toplevel(self); window.title("Appearance and text size"); window.geometry("500x300"); window.transient(self)
        body = ttk.Frame(window, padding=14); body.pack(fill="both", expand=True)
        ttk.Label(body, text="Appearance and accessibility", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(body, text="Changes are previewed immediately. Cancel restores the previous appearance.", wraplength=460).grid(row=1, column=0, columnspan=2, sticky="w", pady=(3, 14))
        theme_var = tk.StringVar(value=self.appearance_theme); scale_var = tk.StringVar(value=f"{self.ui_scale}%")
        ttk.Label(body, text="Theme:").grid(row=2, column=0, sticky="w", pady=6); ttk.Combobox(body, textvariable=theme_var, state="readonly", values=("System", "Light", "Dark", "High contrast"), width=18).grid(row=2, column=1, sticky="w")
        ttk.Label(body, text="Interface scale:").grid(row=3, column=0, sticky="w", pady=6); ttk.Combobox(body, textvariable=scale_var, state="readonly", values=("100%", "125%", "150%", "175%", "200%"), width=18).grid(row=3, column=1, sticky="w")
        sample = ttk.LabelFrame(body, text="Preview", padding=10); sample.grid(row=4, column=0, columnspan=2, sticky="ew", pady=12); ttk.Label(sample, text="Filename.jpg   1920 × 1080   H.265 / HEVC").pack(side="left"); ttk.Button(sample, text="Sample button").pack(side="right")
        def preview(*_args):
            try: scale = int(scale_var.get().rstrip("%"))
            except ValueError: scale = 100
            self.apply_appearance(theme_var.get(), scale)
        theme_var.trace_add("write", preview); scale_var.trace_add("write", preview)
        def save(): preview(); window.destroy()
        def cancel(): self.apply_appearance(*original); window.destroy()
        buttons = ttk.Frame(body); buttons.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(8, 0)); ttk.Button(buttons, text="Save", command=save).pack(side="left"); ttk.Button(buttons, text="Restore system default", command=lambda: (theme_var.set("System"), scale_var.set("100%"))).pack(side="left", padx=6); ttk.Button(buttons, text="Cancel", command=cancel).pack(side="right")
        window.protocol("WM_DELETE_WINDOW", cancel)

    def restore_layout(self):
        try:
            browser_split = int(self.settings.get("browser_split", self.winfo_width() // 2))
            self.browser_panes.sash_place(0, browser_split, 0)
        except (tk.TclError, ValueError, TypeError):
            pass
        self.preview_split_position = int(self.settings.get("preview_split", int(self.winfo_height() * 0.68)))

    def close_app(self):
        self.operation_cancel.set()
        try:
            settings = {
                "geometry": self.geometry(),
                "browser_split": self.browser_panes.sash_coord(0)[0],
                "preview_split": self.current_preview_split(),
                "scan_workers": self.scan_workers,
                "performance_profile": self.performance_profile,
                "excluded_patterns": self.excluded_patterns,
                "thumbnail_cache_percent": self.thumbnail_cache_percent,
                "appearance_theme": self.appearance_theme,
                "ui_scale": self.ui_scale,
                "left": self.left.get_state(),
                "right": self.right.get_state(),
            }
            save_json(self.settings_path, settings)
            self.metadata_cache.save()
        except (OSError, tk.TclError):
            pass
        self.left_preview.stop_playback()
        self.right_preview.stop_playback()
        self.left.stop_live_monitoring()
        self.right.stop_live_monitoring()
        self.thumbnail_executor.shutdown(wait=False, cancel_futures=True)
        self.left_preview.temp_dir.cleanup()
        self.right_preview.temp_dir.cleanup()
        self.destroy()

    def current_preview_split(self) -> int:
        try:
            if self.preview_area_shown():
                self.preview_split_position = self.workspace_panes.sash_coord(0)[1]
        except tk.TclError:
            pass
        return self.preview_split_position

    def preview_area_shown(self) -> bool:
        return any(str(pane) == str(self.preview_area) for pane in self.workspace_panes.panes())

    def set_pane_preview(self, pane: FilePane, enabled: bool):
        preview = self.left_preview if pane is self.left else self.right_preview
        if enabled: preview.enable()
        else: preview.disable()
        any_enabled = self.left.preview_enabled_var.get() or self.right.preview_enabled_var.get()
        shown = self.preview_area_shown()
        if any_enabled and not shown:
            self.workspace_panes.add(self.preview_area, stretch="always", minsize=190)
            self.after_idle(self.restore_preview_layout)
        elif not any_enabled and shown:
            self.current_preview_split()
            self.workspace_panes.forget(self.preview_area)

    def restore_preview_layout(self):
        try:
            split = min(max(300, self.preview_split_position), max(300, self.winfo_height() - 190))
            self.workspace_panes.sash_place(0, 0, split)
            self.preview_area.sash_place(0, self.browser_panes.sash_coord(0)[0], 0)
        except tk.TclError:
            pass

    def set_active(self, pane: FilePane):
        self.active_pane = pane

    def current_pane(self) -> FilePane:
        return self.active_pane or self.left

    def keyboard_preview_jump(self, event, fraction: float):
        # Punctuation typed into a path, search, filter, or dialog field must
        # remain ordinary text rather than controlling a background preview.
        if event.widget.winfo_class() in {"Entry", "TEntry", "Text", "TCombobox", "Spinbox", "TSpinbox"}:
            return None
        pane = self.current_pane()
        if not pane.preview_enabled_var.get():
            return None
        preview = self.left_preview if pane is self.left else self.right_preview
        return "break" if preview.jump_percent(fraction) else None

    def apply_performance_profile(self, profile: str, scan_workers: int | None = None):
        profile = profile if profile in PERFORMANCE_PROFILES else "Balanced"
        defaults = PERFORMANCE_PROFILES[profile]
        self.performance_profile = profile
        self.workload.set_profile(profile)
        selected_workers = scan_workers if scan_workers is not None else defaults["scan_workers"]
        self.scan_workers = max(1, min(16, int(selected_workers)))
        wanted_thumbnail_workers = int(defaults["thumbnail_workers"])
        if wanted_thumbnail_workers != self.thumbnail_workers:
            previous = self.thumbnail_executor
            self.thumbnail_workers = wanted_thumbnail_workers
            self.thumbnail_executor = ThreadPoolExecutor(max_workers=wanted_thumbnail_workers, thread_name_prefix="thumbnail")
            previous.shutdown(wait=False, cancel_futures=False)

    def post_ui(self, callback, *args):
        self.ui_events.put((callback, args))

    def system_drive_capacity(self) -> int:
        root = Path(os.environ.get("SystemDrive", "C:") + "\\") if sys.platform == "win32" else Path("/")
        try: return shutil.disk_usage(root).total
        except OSError: return shutil.disk_usage(self.thumbnail_directory).total

    def thumbnail_cache_limit(self) -> int:
        return int(self.system_drive_capacity() * self.thumbnail_cache_percent / 100)

    def request_thumbnail_cache_prune(self):
        if self.thumbnail_prune_lock.locked(): return
        def worker():
            with self.thumbnail_prune_lock:
                self.prune_thumbnail_cache()
        threading.Thread(target=worker, daemon=True).start()

    def prune_thumbnail_cache(self) -> tuple[int, int]:
        limit = self.thumbnail_cache_limit()
        files = []
        total = 0
        for path in self.thumbnail_directory.glob("*.png"):
            if ".tmp." in path.name: continue
            try:
                stat = path.stat(); total += stat.st_size; files.append((stat.st_mtime, stat.st_size, path))
            except OSError: pass
        removed = 0
        for _modified, size, path in sorted(files):
            if total <= limit: break
            try:
                path.unlink(); total -= size; removed += 1
            except OSError: pass
        return removed, total

    def clear_thumbnail_cache(self) -> tuple[int, int]:
        self.thumbnail_cache_epoch += 1
        removed = 0
        removed_bytes = 0
        for path in self.thumbnail_directory.glob("*.png"):
            try:
                size = path.stat().st_size
                path.unlink(); removed += 1; removed_bytes += size
            except OSError: pass
        self.left.thumbnail_generation += 1
        self.right.thumbnail_generation += 1
        return removed, removed_bytes

    def poll_ui_events(self):
        started = time.monotonic()
        processed = 0
        try:
            while processed < 20 and time.monotonic() - started < 0.02:
                callback, args = self.ui_events.get_nowait()
                callback(*args)
                processed += 1
        except queue.Empty: pass
        self.after(5 if not self.ui_events.empty() else 50, self.poll_ui_events)

    def keyboard_go_up(self, event):
        if isinstance(event.widget, (tk.Entry, ttk.Entry, ttk.Combobox)): return
        self.current_pane().go_up()

    def keyboard_delete(self, event):
        if isinstance(event.widget, (tk.Entry, ttk.Entry, ttk.Combobox)): return
        self.delete_selected()

    def refresh(self):
        self.left.refresh_browser()
        self.right.refresh_browser()

    def transfer(self, move: bool):
        source = self.active_pane or self.left
        self.transfer_from(source, move)

    def transfer_from(self, source: FilePane, move: bool):
        self.set_active(source)
        destination = self.right if source is self.left else self.left
        selected = source.selected_items()
        if not selected:
            messagebox.showinfo("Nothing selected", "Select one or more files in the active pane first.")
            return
        targets = [
            (item, destination.current_path / (item.path.relative_to(source.current_path) if source.recursive_var.get() else item.path.name))
            for item in selected
        ]
        verb = "move" if move else "copy"
        if not messagebox.askyesno(f"Confirm {verb}", f"{verb.title()} {len(selected)} file(s) to:\n{destination.current_path}?"):
            return
        self.enqueue_operation([(item.path, target) for item, target in targets], move, f"{verb.title()} to {destination.current_path}")

    def transfer_finished(self, source: FilePane, destination: FilePane, errors: list[str], count: int, verb: str):
        source.scan()
        destination.scan()
        if errors:
            messagebox.showerror("Some files failed", "\n".join(errors[:10]))
        else:
            completed_verb = "moved" if verb == "move" else "copied"
            messagebox.showinfo("Finished", f"Successfully {completed_verb} {count} file(s).")

    def conflict_policy(self, pairs: list[tuple[Path, Path]]) -> str | None:
        if not any(target.exists() and source.resolve() != target.resolve() for source, target in pairs):
            return "replace"
        choice = simpledialog.askstring("File conflicts", "Some files already exist. Enter: replace, skip, keep both, or newer", initialvalue="skip", parent=self)
        if choice is None: return None
        normalized = choice.strip().lower()
        aliases = {"keep": "keep both", "both": "keep both", "replace if newer": "newer"}
        normalized = aliases.get(normalized, normalized)
        if normalized not in {"replace", "skip", "keep both", "newer"}:
            messagebox.showerror("Unknown choice", "Use replace, skip, keep both, or newer.")
            return None
        return normalized

    @staticmethod
    def unique_target(path: Path) -> Path:
        counter = 2
        candidate = path
        while candidate.exists():
            candidate = path.with_name(f"{path.stem} ({counter}){path.suffix}")
            counter += 1
        return candidate

    @staticmethod
    def plan_batch_rename(items: list[MediaItem], template: str, find_text: str = "", replace_text: str = "", case_sensitive: bool = False, start_number: int = 1, padding: int = 3) -> list[dict]:
        ordered = sorted(items, key=lambda item: str(item.path).casefold())
        plans = []
        invalid_characters = set('<>:"/\\|?*')
        reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
        for offset, item in enumerate(ordered):
            name = item.path.stem
            if find_text:
                name = name.replace(find_text, replace_text) if case_sensitive else re.sub(re.escape(find_text), lambda _match: replace_text, name, flags=re.IGNORECASE)
            values = {"name": name, "n": str(start_number + offset).zfill(max(1, padding)), "ext": item.path.suffix[1:], "dotext": item.path.suffix}
            try: target_name = template.format_map(values)
            except (KeyError, ValueError) as exc:
                plans.append({"item": item, "target": item.path, "status": f"Invalid template: {exc}"}); continue
            status = "Ready"
            if not target_name or target_name in {".", ".."}: status = "Name cannot be empty"
            elif any(character in invalid_characters or ord(character) < 32 for character in target_name): status = "Name contains a forbidden character"
            elif target_name != target_name.rstrip(" ."): status = "Name cannot end with a space or dot"
            elif target_name.split(".", 1)[0].upper() in reserved: status = "Reserved Windows filename"
            target = item.path.with_name(target_name) if status == "Ready" else item.path
            if status == "Ready" and str(target) == str(item.path): status = "Unchanged"
            plans.append({"item": item, "target": target, "status": status})
        source_keys = {str(plan["item"].path.absolute()).casefold() for plan in plans}
        target_counts = {}
        for plan in plans:
            if plan["status"] not in {"Ready", "Unchanged"}: continue
            key = str(plan["target"].absolute()).casefold(); target_counts[key] = target_counts.get(key, 0) + 1
        for plan in plans:
            if plan["status"] != "Ready": continue
            target_key = str(plan["target"].absolute()).casefold()
            if target_counts[target_key] > 1: plan["status"] = "Duplicate output name"
            elif plan["target"].exists() and target_key not in source_keys: plan["status"] = "A file with this name already exists"
        return plans

    @staticmethod
    def perform_batch_rename(pairs: list[tuple[Path, Path]]) -> tuple[bool, str]:
        """Rename through unique temporary names so swaps and cycles are safe."""
        staged: list[tuple[Path, Path, Path]] = []
        completed: list[tuple[Path, Path, Path]] = []
        try:
            for index, (source, target) in enumerate(pairs):
                temporary = source.with_name(f".rfm-rename-{os.getpid()}-{time.time_ns()}-{index}.tmp")
                while temporary.exists(): temporary = temporary.with_name(temporary.stem + "x" + temporary.suffix)
                source.rename(temporary); staged.append((source, temporary, target))
            for source, temporary, target in staged:
                temporary.rename(target); completed.append((source, temporary, target))
            return True, ""
        except OSError as exc:
            for source, _temporary, target in reversed(completed):
                try:
                    if target.exists() and not source.exists(): target.rename(source)
                except OSError: pass
            completed_sources = {source for source, _temporary, _target in completed}
            for source, temporary, _target in reversed(staged):
                if source in completed_sources: continue
                try:
                    if temporary.exists() and not source.exists(): temporary.rename(source)
                except OSError: pass
            return False, str(exc)

    def batch_rename_selected(self):
        pane = self.current_pane(); items = pane.selected_items()
        if not items: messagebox.showinfo("Batch rename", "Select one or more files first."); return
        window = tk.Toplevel(self); window.title("Batch rename selected files"); window.geometry("980x650"); window.transient(self)
        settings = ttk.LabelFrame(window, text="Rename pattern", padding=10); settings.pack(fill="x", padx=10, pady=10)
        template_var = tk.StringVar(value="{name}{dotext}"); find_var = tk.StringVar(); replace_var = tk.StringVar(); case_var = tk.BooleanVar(value=False); start_var = tk.IntVar(value=1); padding_var = tk.IntVar(value=3)
        ttk.Label(settings, text="Template:").grid(row=0, column=0, sticky="w"); ttk.Entry(settings, textvariable=template_var, width=35).grid(row=0, column=1, sticky="ew", padx=(5, 12))
        ttk.Label(settings, text="Tokens: {name} original name, {n} number, {ext} extension, {dotext} extension including dot").grid(row=1, column=1, columnspan=5, sticky="w", pady=(2, 8))
        ttk.Label(settings, text="Find:").grid(row=2, column=0, sticky="w"); ttk.Entry(settings, textvariable=find_var, width=18).grid(row=2, column=1, sticky="ew", padx=(5, 12))
        ttk.Label(settings, text="Replace:").grid(row=2, column=2, sticky="w"); ttk.Entry(settings, textvariable=replace_var, width=18).grid(row=2, column=3, sticky="ew", padx=(5, 12)); ttk.Checkbutton(settings, text="Case sensitive", variable=case_var).grid(row=2, column=4, sticky="w")
        ttk.Label(settings, text="Start number:").grid(row=3, column=0, sticky="w", pady=(8, 0)); ttk.Spinbox(settings, from_=-999999, to=999999, textvariable=start_var, width=9).grid(row=3, column=1, sticky="w", padx=5, pady=(8, 0))
        ttk.Label(settings, text="Number padding:").grid(row=3, column=2, sticky="w", pady=(8, 0)); ttk.Spinbox(settings, from_=1, to=9, textvariable=padding_var, width=6).grid(row=3, column=3, sticky="w", padx=5, pady=(8, 0)); settings.columnconfigure(1, weight=1); settings.columnconfigure(3, weight=1)
        tree = ttk.Treeview(window, columns=("status", "current", "new"), show="headings")
        tree.heading("status", text="Status"); tree.heading("current", text="Current name"); tree.heading("new", text="New name"); tree.column("status", width=210); tree.column("current", width=330); tree.column("new", width=330)
        scroll = ttk.Scrollbar(window, orient="vertical", command=tree.yview); tree.configure(yscrollcommand=scroll.set); scroll.pack(side="right", fill="y", padx=(0, 10)); tree.pack(fill="both", expand=True, padx=(10, 0))
        status_var = tk.StringVar(); ttk.Label(window, textvariable=status_var, padding=(10, 5)).pack(fill="x")
        current_plans = {"value": []}
        def refresh_preview():
            try: start = start_var.get(); padding = max(1, min(9, padding_var.get()))
            except tk.TclError: status_var.set("Start and padding must be whole numbers."); apply_button.configure(state="disabled"); return
            plans = self.plan_batch_rename(items, template_var.get(), find_var.get(), replace_var.get(), case_var.get(), start, padding); current_plans["value"] = plans; tree.delete(*tree.get_children())
            for plan in plans: tree.insert("", "end", values=(plan["status"], plan["item"].path.name, plan["target"].name))
            errors = [plan for plan in plans if plan["status"] not in {"Ready", "Unchanged"}]; changed = [plan for plan in plans if plan["status"] == "Ready"]
            status_var.set(f"{len(changed)} file(s) ready · {len(plans)-len(changed)-len(errors)} unchanged · {len(errors)} problem(s)")
            apply_button.configure(state="normal" if changed and not errors else "disabled")
        def apply():
            refresh_preview(); plans = current_plans["value"]
            errors = [plan for plan in plans if plan["status"] not in {"Ready", "Unchanged"}]; changed = [plan for plan in plans if plan["status"] == "Ready"]
            if errors or not changed: return
            if not messagebox.askyesno("Confirm batch rename", f"Rename {len(changed)} file(s) exactly as previewed?\n\nThe complete batch can be undone with Ctrl+Z.", parent=window): return
            pairs = [(plan["item"].path, plan["target"]) for plan in changed]; success, error = self.perform_batch_rename(pairs)
            if not success: messagebox.showerror("Batch rename failed", f"No completed rename was kept where rollback was possible.\n\n{error}", parent=window); pane.scan(); return
            for old, new in pairs: self.metadata_cache.move_user_data(old, new)
            for old, new in pairs:
                old_key, new_key = str(old), str(new)
                if old_key in pane.checked_paths:
                    pane.checked_paths.discard(old_key); pane.checked_paths.add(new_key)
            self.record_undo("batch_rename", [(new, old) for old, new in pairs]); window.destroy(); pane.scan(pairs[0][1]); messagebox.showinfo("Batch rename complete", f"Renamed {len(pairs)} file(s). Use Ctrl+Z to undo the batch.")
        buttons = ttk.Frame(window, padding=10); buttons.pack(fill="x")
        ttk.Button(buttons, text="Refresh preview", command=refresh_preview).pack(side="left")
        apply_button = ttk.Button(buttons, text="Apply rename", command=apply); apply_button.pack(side="left", padx=6)
        ttk.Button(buttons, text="Cancel", command=window.destroy).pack(side="right")
        refresh_preview()

    def enqueue_operation(self, pairs: list[tuple[Path, Path]], move: bool, label: str):
        pairs = [(Path(source), Path(target)) for source, target in pairs if Path(source).is_file()]
        if not pairs: return
        policy = self.conflict_policy(pairs)
        if policy is None: return
        self.operation_queue.put({"pairs": pairs, "move": move, "label": label, "policy": policy})
        self.show_operation_window()
        if not self.operation_running: self.after(0, self.start_next_operation)

    def show_operation_window(self):
        if self.operation_window and self.operation_window.winfo_exists():
            self.operation_window.deiconify(); self.operation_window.lift(); return
        window = tk.Toplevel(self); window.title("Transfer queue"); window.geometry("520x170"); window.transient(self)
        self.operation_window = window
        self.operation_status = tk.StringVar(value="No active transfer")
        self.operation_detail = tk.StringVar(value=f"{self.operation_queue.qsize()} queued")
        ttk.Label(window, textvariable=self.operation_status, font=("Segoe UI", 11, "bold")).pack(fill="x", padx=12, pady=(12, 4))
        self.operation_progress = ttk.Progressbar(window, mode="determinate"); self.operation_progress.pack(fill="x", padx=12, pady=5)
        ttk.Label(window, textvariable=self.operation_detail).pack(fill="x", padx=12)
        buttons = ttk.Frame(window); buttons.pack(fill="x", padx=12, pady=10)
        self.pause_button = ttk.Button(buttons, text="Pause", command=self.toggle_operation_pause); self.pause_button.pack(side="left")
        ttk.Button(buttons, text="Cancel current", command=self.operation_cancel.set).pack(side="left", padx=6)
        ttk.Button(buttons, text="Retry failed", command=self.retry_failed_operation).pack(side="left", padx=6)
        ttk.Button(buttons, text="Close", command=window.withdraw).pack(side="right")

    def toggle_operation_pause(self):
        self.operation_paused = not self.operation_paused
        if hasattr(self, "pause_button"): self.pause_button.configure(text="Resume" if self.operation_paused else "Pause")

    def start_next_operation(self):
        if self.operation_running: return
        try: job = self.operation_queue.get_nowait()
        except queue.Empty:
            if hasattr(self, "operation_status"): self.operation_status.set("Queue complete")
            return
        self.operation_running = True; self.operation_cancel.clear(); self.operation_paused = False
        pairs, move, policy = job["pairs"], job["move"], job["policy"]
        total_bytes = sum(source.stat().st_size for source, _target in pairs if source.exists())
        if hasattr(self, "operation_progress"): self.operation_progress.configure(maximum=max(1, total_bytes), value=0)
        if hasattr(self, "operation_status"): self.operation_status.set(job["label"])

        def worker():
            completed_bytes = 0; errors = []; failed_pairs = []; undo_records = []; started = time.monotonic()
            for index, (source, original_target) in enumerate(pairs, 1):
                if self.operation_cancel.is_set(): break
                while self.operation_paused and not self.operation_cancel.is_set(): time.sleep(0.1)
                target = original_target
                backup = None
                try:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if target.exists():
                        if policy == "skip" or (policy == "newer" and source.stat().st_mtime <= target.stat().st_mtime):
                            continue
                        if policy == "keep both": target = self.unique_target(target)
                    if target.exists():
                        backup = self.undo_directory / f"{time.time_ns()}-{target.name}"
                        shutil.move(target, backup)
                    size = source.stat().st_size
                    if move:
                        shutil.move(source, target); completed_bytes += size
                        self.metadata_cache.move_user_data(source, target)
                        undo_records.append(("move", target, source, backup))
                    else:
                        with source.open("rb") as src, target.open("wb") as dst:
                            while True:
                                if self.operation_cancel.is_set(): raise InterruptedError("Cancelled")
                                while self.operation_paused and not self.operation_cancel.is_set(): time.sleep(0.1)
                                chunk = src.read(1024 * 1024)
                                if not chunk: break
                                dst.write(chunk); completed_bytes += len(chunk)
                                elapsed = max(0.01, time.monotonic() - started); speed = completed_bytes / elapsed
                                remaining = (total_bytes - completed_bytes) / speed if speed else 0
                                self.post_ui(self.update_operation_progress, completed_bytes, total_bytes, speed, remaining, index, len(pairs))
                        shutil.copystat(source, target)
                        self.metadata_cache.copy_user_data(source, target)
                        undo_records.append(("copy", target, source, backup))
                    self.post_ui(self.update_operation_progress, completed_bytes, total_bytes, completed_bytes / max(.01, time.monotonic()-started), 0, index, len(pairs))
                except InterruptedError:
                    try:
                        if target.exists() and not move: target.unlink()
                        if backup and backup.exists(): shutil.move(backup, target)
                    except OSError: pass
                    break
                except OSError as exc:
                    try:
                        if target.exists() and not move: target.unlink()
                        if backup and backup.exists() and not target.exists(): shutil.move(backup, target)
                    except OSError: pass
                    errors.append(f"{source.name}: {exc}"); failed_pairs.append((source, original_target))
            self.post_ui(self.finish_operation, undo_records, errors, self.operation_cancel.is_set(), failed_pairs, move, job["label"])
        threading.Thread(target=worker, daemon=True).start()

    def update_operation_progress(self, done: int, total: int, speed: float, remaining: float, index: int, count: int):
        if hasattr(self, "operation_progress"): self.operation_progress.configure(value=done)
        if hasattr(self, "operation_detail"): self.operation_detail.set(f"File {index} of {count} · {human_size(int(speed))}/s · about {human_duration(remaining)} remaining · {self.operation_queue.qsize()} job(s) queued")

    def apply_completed_file_changes(self, records: list, move: bool):
        """Update both browsers from completed transfers without rescanning folders."""
        panes = (self.left, self.right)
        known_items = {}
        for pane in panes:
            known_items.update(pane.items)
        changed = {pane: False for pane in panes}
        unknown_targets = {pane: [] for pane in panes}
        moved_sources = [Path(source) for _mode, _target, source, _backup in records] if move else []
        continuation = {pane: pane.continuation_path_after_removal(moved_sources) for pane in panes}

        for _mode, target, source, _backup in records:
            source, target = Path(source), Path(target)
            template = known_items.get(str(source))
            if move:
                for pane in panes:
                    changed[pane] = pane.remove_known_paths((source,)) or changed[pane]
            for pane in panes:
                if not pane.contains_media_path(target) or target.suffix.lower() not in SUPPORTED_EXTENSIONS or not target.exists():
                    continue
                if template is None:
                    unknown_targets[pane].append(target)
                    continue
                try:
                    stat = target.stat()
                    copied = replace(template, path=target, size=stat.st_size, modified=stat.st_mtime)
                except OSError:
                    continue
                pane.items[str(target)] = pane.metadata_cache.with_user_labels(copied)
                changed[pane] = True

        for pane in panes:
            if unknown_targets[pane]:
                # Uncommon external/drop sources have no in-memory metadata to
                # clone safely, so only that affected pane needs a real scan.
                pane.scan()
            elif changed[pane]:
                pane.refresh_view(continuation[pane])
                pane.status_var.set("File operation applied · no rescan needed")

    def finish_operation(self, records: list, errors: list[str], cancelled: bool, failed_pairs: list, move: bool, label: str):
        if records: self.record_undo("operation", records)
        self.operation_running = False
        if records: self.apply_completed_file_changes(records, move)
        if errors: messagebox.showerror("Some files failed", "\n".join(errors[:10]))
        self.last_failed_operation = {"pairs": failed_pairs, "move": move, "label": f"Retry: {label}"} if failed_pairs else None
        if hasattr(self, "operation_status"): self.operation_status.set("Cancelled" if cancelled else "Finished")
        self.after(100, self.start_next_operation)

    def retry_failed_operation(self):
        if not self.last_failed_operation:
            messagebox.showinfo("Nothing to retry", "The last transfer had no failed files."); return
        job = self.last_failed_operation; self.last_failed_operation = None
        self.enqueue_operation(job["pairs"], job["move"], job["label"])

    def record_undo(self, kind: str, records: list):
        self.undo_stack.append((kind, records))
        self.undo_stack = self.undo_stack[-20:]

    def undo_last(self):
        if self.operation_running:
            messagebox.showinfo("Transfer active", "Wait for the current transfer to finish before undoing."); return
        if not self.undo_stack:
            messagebox.showinfo("Nothing to undo", "There are no recent copy, move, replacement, or rename actions."); return
        kind, records = self.undo_stack.pop()
        errors = []
        if kind == "batch_rename":
            success, error = self.perform_batch_rename(records)
            if success:
                for current, old in records: self.metadata_cache.move_user_data(current, old)
            else: errors.append(error)
            records = []
        for record in reversed(records):
            try:
                if kind == "rename":
                    current, old = record
                    if current.exists():
                        current.rename(old); self.metadata_cache.move_user_data(current, old)
                    continue
                mode, target, source, backup = record
                if mode == "move" and target.exists():
                    source.parent.mkdir(parents=True, exist_ok=True); shutil.move(target, source); self.metadata_cache.move_user_data(target, source)
                elif mode == "copy" and target.exists():
                    target.unlink(); self.metadata_cache.delete_user_data(target)
                if backup and backup.exists():
                    target.parent.mkdir(parents=True, exist_ok=True); shutil.move(backup, target)
            except OSError as exc: errors.append(str(exc))
        self.refresh()
        if errors: messagebox.showerror("Undo incomplete", "\n".join(errors[:10]))
        else: messagebox.showinfo("Undo complete", "The most recent file operation was undone.")

    def copy_to_clipboard(self, move: bool):
        items = self.current_pane().selected_items()
        if not items: return
        self.file_clipboard = ([item.path for item in items], move)
        self.current_pane().status_var.set(f"{len(items)} file(s) ready to {'move' if move else 'copy'}")

    def paste_clipboard(self):
        paths, move = self.file_clipboard
        if not paths: return
        destination = self.current_pane().current_path
        self.enqueue_operation([(path, destination / path.name) for path in paths], move, f"Paste to {destination}")
        if move: self.file_clipboard = ([], False)

    def delete_selected(self, pane: FilePane | None = None):
        pane = pane or self.current_pane(); items = pane.selected_items()
        if not items: return
        if not messagebox.askyesno("Move to Recycle Bin", f"Move {len(items)} selected file(s) to the Recycle Bin / Trash?"): return
        errors = []; removed = []; continuation = pane.continuation_path_after_removal(item.path for item in items)
        for item in items:
            try: send2trash(str(item.path)); removed.append(item.path)
            except OSError as exc: errors.append(f"{item.path.name}: {exc}")
        if removed:
            pane.remove_known_paths(removed)
            pane.refresh_view(continuation)
            pane.status_var.set(f"Moved {len(removed)} file(s) to Trash · no rescan needed")
        if errors: messagebox.showerror("Some files could not be removed", "\n".join(errors[:10]))

    @staticmethod
    def verify_media_file(path: Path, cancel_event: threading.Event) -> tuple[str, str]:
        if cancel_event.is_set(): return "Cancelled", "Cancelled before verification"
        if path.suffix.lower() in IMAGE_EXTENSIONS:
            try:
                frames = 0
                with Image.open(path) as source:
                    for frame in ImageSequence.Iterator(source):
                        if cancel_event.is_set(): return "Cancelled", "Cancelled during image verification"
                        frame.load(); frames += 1
                return "Passed", f"Decoded {frames} image frame(s)"
            except Exception as exc:
                return "Failed", str(exc) or "Image decoder reported an error"
        command = [bundled_command("ffmpeg"), "-v", "error", "-i", str(path), "-map", "0:v?", "-map", "0:a?", "-f", "null", "-"]
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        try:
            with tempfile.TemporaryFile() as error_log:
                process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=error_log, creationflags=flags)
                while process.poll() is None:
                    if cancel_event.wait(0.1):
                        process.terminate()
                        try: process.wait(timeout=2)
                        except subprocess.TimeoutExpired: process.kill(); process.wait()
                        return "Cancelled", "Cancelled during full decode"
                error_log.seek(0)
                details = error_log.read().decode("utf-8", errors="replace").strip()
                if process.returncode == 0: return "Passed", "All selected audio/video streams decoded without errors"
                return "Failed", details[-4000:] or f"FFmpeg returned code {process.returncode}"
        except OSError as exc:
            return "Failed", str(exc)

    @staticmethod
    def write_integrity_report(path: Path, results: list[dict]):
        with path.open("w", newline="", encoding="utf-8-sig") as stream:
            writer = csv.writer(stream)
            writer.writerow(("Status", "Cached", "Checked", "File size", "Path", "Details"))
            for result in results:
                writer.writerow((result["status"], "Yes" if result.get("cached") else "No", datetime.fromtimestamp(result["checked"]).strftime("%Y-%m-%d %H:%M:%S"), result["size"], result["path"], result["details"]))

    @staticmethod
    def media_report_record(item: MediaItem, root: Path | None = None, full_paths: bool = True) -> dict:
        try: shown_path = str(item.path if full_paths or root is None else item.path.relative_to(root))
        except ValueError: shown_path = str(item.path)
        return {
            "Name": item.path.name, "Path": shown_path, "Folder": str(item.path.parent if full_paths else Path(shown_path).parent),
            "Kind": "Video" if item.path.suffix.lower() in VIDEO_EXTENSIONS else "Image", "Extension": item.path.suffix.lower(),
            "Width": item.width, "Height": item.height, "Resolution": item.resolution, "Size bytes": item.size,
            "Modified": datetime.fromtimestamp(item.modified).isoformat(sep=" ", timespec="seconds"), "Duration seconds": item.duration,
            "Codec": item.codec, "Bitrate": item.bitrate, "Frame rate": item.frame_rate, "Audio codec": item.audio_codec,
            "Audio channels": item.audio_channels, "Pixel format": item.pixel_format, "HDR": item.hdr,
            "Rating": item.rating, "Colour label": item.color_label, "Tags": ", ".join(item.tags), "Status": item.error or "Readable",
        }

    @staticmethod
    def media_report_summary(items: list[MediaItem]) -> dict:
        codecs: dict[str, int] = {}
        for item in items: codecs[item.codec] = codecs.get(item.codec, 0) + 1
        return {
            "Generated": datetime.now().isoformat(sep=" ", timespec="seconds"), "Files": len(items),
            "Images": sum(item.path.suffix.lower() in IMAGE_EXTENSIONS for item in items), "Videos": sum(item.path.suffix.lower() in VIDEO_EXTENSIONS for item in items),
            "Unreadable": sum(bool(item.error) for item in items), "Total size bytes": sum(item.size for item in items),
            "Total size": human_size(sum(item.size for item in items)), "Codecs": dict(sorted(codecs.items(), key=lambda pair: (-pair[1], pair[0].casefold()))),
        }

    @classmethod
    def write_media_report(cls, path: Path, items: list[MediaItem], report_format: str, root: Path | None, full_paths: bool, cancel_event: threading.Event, progress_callback=None) -> tuple[str, str]:
        report_format = report_format.upper()
        if report_format not in {"CSV", "JSON", "HTML"}: return "Failed", f"Unsupported report format: {report_format}"
        temporary = path.with_name(f"{path.stem}.{threading.get_ident()}.tmp{path.suffix}")
        fields = tuple(cls.media_report_record(items[0], root, full_paths)) if items else tuple()
        summary = cls.media_report_summary(items)
        try:
            encoding = "utf-8-sig" if report_format == "CSV" else "utf-8"
            with temporary.open("w", newline="" if report_format == "CSV" else None, encoding=encoding) as stream:
                if report_format == "CSV":
                    writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader()
                    for index, item in enumerate(items, 1):
                        if cancel_event.is_set(): raise InterruptedError
                        writer.writerow(cls.media_report_record(item, root, full_paths))
                        if progress_callback and (index % 100 == 0 or index == len(items)): progress_callback(index, len(items))
                elif report_format == "JSON":
                    stream.write('{\n  "summary": '); json.dump(summary, stream, ensure_ascii=False, indent=2); stream.write(',\n  "items": [\n')
                    for index, item in enumerate(items, 1):
                        if cancel_event.is_set(): raise InterruptedError
                        if index > 1: stream.write(",\n")
                        stream.write("    "); json.dump(cls.media_report_record(item, root, full_paths), stream, ensure_ascii=False)
                        if progress_callback and (index % 100 == 0 or index == len(items)): progress_callback(index, len(items))
                    stream.write("\n  ]\n}\n")
                elif report_format == "HTML":
                    stream.write("<!doctype html><html><head><meta charset='utf-8'><title>Media report</title><style>body{font:14px Segoe UI,Arial,sans-serif;margin:24px;color:#222}table{border-collapse:collapse;width:100%}th,td{border:1px solid #ccc;padding:6px;text-align:left;vertical-align:top}th{background:#eee;position:sticky;top:0}tr:nth-child(even){background:#fafafa}.summary{display:flex;gap:24px;flex-wrap:wrap;margin:14px 0 20px}</style></head><body><h1>Media report</h1><div class='summary'>")
                    for key in ("Generated", "Files", "Images", "Videos", "Unreadable", "Total size"): stream.write(f"<span><strong>{html.escape(str(key))}:</strong> {html.escape(str(summary[key]))}</span>")
                    stream.write("</div><table><thead><tr>"); stream.write("".join(f"<th>{html.escape(field)}</th>" for field in fields)); stream.write("</tr></thead><tbody>")
                    for index, item in enumerate(items, 1):
                        if cancel_event.is_set(): raise InterruptedError
                        record = cls.media_report_record(item, root, full_paths); stream.write("<tr>" + "".join(f"<td>{html.escape('' if record[field] is None else str(record[field]))}</td>" for field in fields) + "</tr>")
                        if progress_callback and (index % 100 == 0 or index == len(items)): progress_callback(index, len(items))
                    stream.write("</tbody></table></body></html>")
            if cancel_event.is_set(): raise InterruptedError
            path.parent.mkdir(parents=True, exist_ok=True); os.replace(temporary, path)
            return "Passed", f"Exported {len(items)} file(s) to {path}"
        except InterruptedError:
            try: temporary.unlink()
            except OSError: pass
            return "Cancelled", "Report export cancelled"
        except OSError as exc:
            try: temporary.unlink()
            except OSError: pass
            return "Failed", str(exc)

    def export_media_report(self):
        pane = self.current_pane(); window = tk.Toplevel(self); window.title("Export media report"); window.geometry("500x300"); window.transient(self)
        body = ttk.Frame(window, padding=12); body.pack(fill="both", expand=True)
        ttk.Label(body, text="Media inventory report", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(body, text="Exports technical details, annotations, file status, and a library summary without changing media.", wraplength=470).grid(row=1, column=0, columnspan=2, sticky="w", pady=(3, 12))
        scope_var = tk.StringVar(value="Selected" if pane.selected_items() else "Visible"); format_var = tk.StringVar(value="CSV"); full_paths_var = tk.BooleanVar(value=True)
        ttk.Label(body, text="Scope:").grid(row=2, column=0, sticky="w", pady=4); ttk.Combobox(body, textvariable=scope_var, state="readonly", values=("Selected", "Visible", "All scanned"), width=14).grid(row=2, column=1, sticky="w")
        ttk.Label(body, text="Format:").grid(row=3, column=0, sticky="w", pady=4); ttk.Combobox(body, textvariable=format_var, state="readonly", values=("CSV", "JSON", "HTML"), width=14).grid(row=3, column=1, sticky="w")
        ttk.Checkbutton(body, text="Include full file paths", variable=full_paths_var).grid(row=4, column=0, columnspan=2, sticky="w", pady=5)
        status_var = tk.StringVar(value="Ready"); ttk.Label(body, textvariable=status_var, wraplength=470).grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 3))
        progress = ttk.Progressbar(body, mode="determinate"); progress.grid(row=6, column=0, columnspan=2, sticky="ew"); body.columnconfigure(0, weight=1)
        cancel_event = threading.Event()
        def start():
            scope = scope_var.get(); items = pane.selected_items() if scope == "Selected" else list(pane.visible_items if scope == "Visible" else pane.items.values())
            if not items: messagebox.showinfo("Nothing to export", "The chosen scope contains no media files.", parent=window); return
            report_format = format_var.get(); extension = "." + report_format.lower()
            chosen = filedialog.asksaveasfilename(parent=window, title="Save media report", initialfile=f"media-report{extension}", defaultextension=extension, filetypes=((f"{report_format} report", f"*{extension}"),))
            if not chosen: return
            full_paths = full_paths_var.get(); cancel_event.clear(); start_button.configure(state="disabled"); cancel_button.configure(state="normal"); progress.configure(maximum=len(items), value=0); status_var.set(f"Exporting 0 of {len(items)}…")
            def update(done, total):
                if window.winfo_exists(): progress.configure(value=done); status_var.set(f"Exporting {done} of {total}…")
            def worker():
                state, details = self.write_media_report(Path(chosen), items, report_format, pane.current_path, full_paths, cancel_event, lambda done, total: self.post_ui(update, done, total))
                def finished():
                    if not window.winfo_exists(): return
                    start_button.configure(state="normal"); cancel_button.configure(state="disabled"); status_var.set(details)
                    if state == "Passed": messagebox.showinfo("Report exported", details, parent=window)
                    elif state == "Failed": messagebox.showerror("Report export failed", details, parent=window)
                self.post_ui(finished)
            threading.Thread(target=worker, daemon=True).start()
        buttons = ttk.Frame(body); buttons.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        start_button = ttk.Button(buttons, text="Export…", command=start); start_button.pack(side="left")
        cancel_button = ttk.Button(buttons, text="Cancel export", command=cancel_event.set, state="disabled"); cancel_button.pack(side="left", padx=6)
        ttk.Button(buttons, text="Close", command=lambda: (cancel_event.set(), window.destroy())).pack(side="right")

    @staticmethod
    def readable_metadata_value(value) -> str:
        if isinstance(value, bytes): return f"<{len(value)} bytes>"
        if isinstance(value, dict): return "; ".join(f"{key}={MediaSorterApp.readable_metadata_value(item)}" for key, item in value.items())
        if isinstance(value, (tuple, list)): return ", ".join(MediaSorterApp.readable_metadata_value(item) for item in value)
        text = str(value)
        return text if len(text) <= 4000 else text[:3997] + "…"

    @classmethod
    def extract_embedded_metadata(cls, path: Path, cancel_event: threading.Event) -> tuple[str, list[dict], str]:
        if cancel_event.is_set(): return "Cancelled", [], "Metadata reading cancelled"
        rows: list[dict] = []
        if path.suffix.lower() in IMAGE_EXTENSIONS:
            try:
                with Image.open(path) as source:
                    rows.extend((
                        {"section": "Image", "field": "Format", "value": source.format or "Unknown"},
                        {"section": "Image", "field": "Mode", "value": source.mode},
                        {"section": "Image", "field": "Size", "value": f"{source.width} × {source.height}"},
                        {"section": "Image", "field": "Frames", "value": str(getattr(source, "n_frames", 1))},
                    ))
                    for key, value in sorted(source.info.items(), key=lambda pair: str(pair[0]).casefold()):
                        if key.lower() == "exif": continue
                        rows.append({"section": "Image info", "field": str(key), "value": cls.readable_metadata_value(value)})
                    exif = source.getexif()
                    for tag_id, value in sorted(exif.items(), key=lambda pair: str(ExifTags.TAGS.get(pair[0], pair[0])).casefold()):
                        name = str(ExifTags.TAGS.get(tag_id, tag_id))
                        if name == "GPSInfo":
                            try:
                                gps = exif.get_ifd(ExifTags.IFD.GPSInfo)
                                for gps_id, gps_value in sorted(gps.items()):
                                    rows.append({"section": "EXIF GPS", "field": str(ExifTags.GPSTAGS.get(gps_id, gps_id)), "value": cls.readable_metadata_value(gps_value)})
                            except (AttributeError, KeyError, TypeError, ValueError):
                                rows.append({"section": "EXIF", "field": name, "value": cls.readable_metadata_value(value)})
                        else: rows.append({"section": "EXIF", "field": name, "value": cls.readable_metadata_value(value)})
                return "Passed", rows, f"Read {len(rows)} metadata field(s)"
            except Exception as exc:
                return "Failed", [], str(exc) or "Image metadata could not be read"
        command = [bundled_command("ffprobe"), "-v", "error", "-show_entries", "format=format_name,duration,size,bit_rate:format_tags:stream=index,codec_type,codec_name:stream_tags", "-of", "json", str(path)]
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        process = None
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=flags)
            while process.poll() is None:
                if cancel_event.wait(0.05):
                    process.terminate()
                    try: process.wait(timeout=2)
                    except subprocess.TimeoutExpired: process.kill(); process.wait()
                    return "Cancelled", [], "Metadata reading cancelled"
            stdout, stderr = process.communicate(); error = stderr.decode("utf-8", errors="replace").strip()
            if process.returncode: return "Failed", [], error[-2000:] or "FFprobe could not read metadata"
            payload = json.loads(stdout.decode("utf-8", errors="replace")); format_data = payload.get("format", {})
            for key in ("format_name", "duration", "size", "bit_rate"):
                if key in format_data: rows.append({"section": "Container", "field": key.replace("_", " ").title(), "value": cls.readable_metadata_value(format_data[key])})
            for key, value in sorted(format_data.get("tags", {}).items(), key=lambda pair: pair[0].casefold()): rows.append({"section": "Container tags", "field": str(key), "value": cls.readable_metadata_value(value)})
            for stream in payload.get("streams", []):
                section = f"Stream {stream.get('index', '?')} ({stream.get('codec_type', 'unknown')})"
                if stream.get("codec_name") is not None: rows.append({"section": section, "field": "Codec", "value": cls.readable_metadata_value(stream["codec_name"])})
                for key, value in sorted(stream.get("tags", {}).items(), key=lambda pair: pair[0].casefold()): rows.append({"section": section + " tags", "field": str(key), "value": cls.readable_metadata_value(value)})
            return "Passed", rows, f"Read {len(rows)} metadata field(s)"
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            if process and process.poll() is None: process.kill()
            return "Failed", [], str(exc)

    @staticmethod
    def write_embedded_metadata_json(path: Path, source: Path, rows: list[dict]):
        temporary = path.with_name(f"{path.stem}.{threading.get_ident()}.tmp{path.suffix}")
        try:
            temporary.write_text(json.dumps({"source": str(source), "exported": datetime.now().isoformat(sep=" ", timespec="seconds"), "metadata": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(temporary, path)
        except OSError:
            try: temporary.unlink()
            except OSError: pass
            raise

    def view_embedded_metadata(self):
        items = self.current_pane().selected_items()
        if len(items) != 1: messagebox.showinfo("Embedded metadata", "Select exactly one image or video first."); return
        item = items[0]; window = tk.Toplevel(self); window.title("Embedded metadata"); window.geometry("900x650"); window.transient(self)
        header = ttk.Frame(window, padding=10); header.pack(fill="x"); ttk.Label(header, text=item.path.name, font=("Segoe UI", 11, "bold"), wraplength=580).pack(side="left")
        search_var = tk.StringVar(); ttk.Label(header, text="Find:").pack(side="left", padx=(20, 4)); search_entry = ttk.Entry(header, textvariable=search_var, width=24); search_entry.pack(side="left")
        status_var = tk.StringVar(value="Reading embedded metadata…"); ttk.Label(window, textvariable=status_var, padding=(10, 0)).pack(fill="x")
        tree = ttk.Treeview(window, columns=("section", "field", "value"), show="headings", selectmode="extended")
        for key, label, width in (("section", "Section", 180), ("field", "Field", 230), ("value", "Value", 470)): tree.heading(key, text=label); tree.column(key, width=width, anchor="w")
        scroll = ttk.Scrollbar(window, orient="vertical", command=tree.yview); tree.configure(yscrollcommand=scroll.set); scroll.pack(side="right", fill="y", padx=(0, 10)); tree.pack(fill="both", expand=True, padx=(10, 0), pady=(6, 0))
        cancel_event = threading.Event(); all_rows: list[dict] = []
        def refresh(*_args):
            needle = search_var.get().strip().casefold(); tree.delete(*tree.get_children())
            for row in all_rows:
                if not needle or needle in f"{row['section']} {row['field']} {row['value']}".casefold(): tree.insert("", "end", values=(row["section"], row["field"], row["value"]))
        search_var.trace_add("write", refresh)
        def copy_rows():
            selection = tree.selection() or tree.get_children(); text = "\n".join("\t".join(str(value) for value in tree.item(iid, "values")) for iid in selection); self.clipboard_clear(); self.clipboard_append(text); status_var.set(f"Copied {len(selection)} row(s)")
        def export_json():
            chosen = filedialog.asksaveasfilename(parent=window, title="Export embedded metadata", initialfile=f"{item.path.stem} - metadata.json", defaultextension=".json", filetypes=(("JSON metadata", "*.json"),))
            if chosen:
                try: self.write_embedded_metadata_json(Path(chosen), item.path, all_rows); messagebox.showinfo("Metadata exported", f"Saved {len(all_rows)} field(s).", parent=window)
                except OSError as exc: messagebox.showerror("Could not export metadata", str(exc), parent=window)
        buttons = ttk.Frame(window, padding=10); buttons.pack(fill="x"); copy_button = ttk.Button(buttons, text="Copy selected/all", command=copy_rows, state="disabled"); copy_button.pack(side="left"); export_button = ttk.Button(buttons, text="Export JSON…", command=export_json, state="disabled"); export_button.pack(side="left", padx=6); ttk.Button(buttons, text="Close", command=lambda: (cancel_event.set(), window.destroy())).pack(side="right")
        def worker():
            state, rows, details = self.extract_embedded_metadata(item.path, cancel_event)
            def finished():
                if not window.winfo_exists(): return
                all_rows.extend(rows); refresh(); status_var.set(details); enabled = "normal" if rows else "disabled"; copy_button.configure(state=enabled); export_button.configure(state=enabled)
                if state == "Failed": messagebox.showerror("Metadata unavailable", details, parent=window)
            self.post_ui(finished)
        threading.Thread(target=worker, daemon=True).start()

    def verify_media_integrity(self):
        pane = self.current_pane()
        window = tk.Toplevel(self); window.title("Verify media integrity"); window.geometry("980x620"); window.transient(self)
        heading = ttk.Frame(window, padding=10); heading.pack(fill="x")
        ttk.Label(heading, text="Media integrity verification", font=("Segoe UI", 12, "bold")).pack(side="left")
        scope_var = tk.StringVar(value="Selected" if pane.selected_items() else "Visible")
        ttk.Label(heading, text="Scope:").pack(side="left", padx=(20, 4))
        scope_box = ttk.Combobox(heading, textvariable=scope_var, state="readonly", width=12, values=("Selected", "Visible", "All scanned")); scope_box.pack(side="left")
        force_var = tk.BooleanVar(value=False); ttk.Checkbutton(heading, text="Force recheck", variable=force_var).pack(side="left", padx=12)
        status_var = tk.StringVar(value="Choose a scope, then Start. Verification is read-only.")
        ttk.Label(window, textvariable=status_var, padding=(10, 0)).pack(fill="x")
        progress = ttk.Progressbar(window, mode="determinate"); progress.pack(fill="x", padx=10, pady=(6, 8))
        tree = ttk.Treeview(window, columns=("status", "cached", "path", "details"), show="headings", selectmode="extended")
        tree.heading("status", text="Status"); tree.heading("cached", text="Cached"); tree.heading("path", text="Path"); tree.heading("details", text="Details")
        tree.column("status", width=85); tree.column("cached", width=65); tree.column("path", width=500); tree.column("details", width=300)
        scroll = ttk.Scrollbar(window, orient="vertical", command=tree.yview); tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y", padx=(0, 10)); tree.pack(fill="both", expand=True, padx=(10, 0))
        cancel_event = threading.Event(); results: list[dict] = []; running = {"value": False}
        def scope_items():
            if scope_var.get() == "Selected": return pane.selected_items()
            if scope_var.get() == "All scanned": return list(pane.items.values())
            return list(pane.visible_items)
        def add_result(result: dict, index: int, total: int):
            if not window.winfo_exists(): return
            results.append(result)
            tree.insert("", "end", values=(result["status"], "Yes" if result["cached"] else "No", result["path"], result["details"]))
            progress.configure(value=index); status_var.set(f"Checked {index} of {total} · {sum(value['status']=='Failed' for value in results)} failed")
        def finished(cancelled: bool):
            if not window.winfo_exists(): return
            running["value"] = False; start_button.configure(state="normal"); cancel_button.configure(state="disabled")
            export_button.configure(state="normal" if results else "disabled"); select_button.configure(state="normal" if any(value["status"] == "Failed" for value in results) else "disabled")
            status_var.set(("Cancelled · " if cancelled else "Complete · ") + f"{len(results)} checked · {sum(value['status']=='Failed' for value in results)} failed · {sum(value['cached'] for value in results)} cached")
        def start():
            items = scope_items()
            if not items: messagebox.showinfo("Nothing to verify", "The chosen scope contains no media files.", parent=window); return
            force_recheck = force_var.get()
            tree.delete(*tree.get_children()); results.clear(); cancel_event.clear(); running["value"] = True
            progress.configure(maximum=len(items), value=0); start_button.configure(state="disabled"); cancel_button.configure(state="normal"); export_button.configure(state="disabled"); select_button.configure(state="disabled")
            def worker():
                for index, item in enumerate(items, 1):
                    if cancel_event.is_set(): break
                    cached = None if force_recheck else self.metadata_cache.cached_integrity(item)
                    if cached:
                        state, details, checked = cached; from_cache = True
                    else:
                        if not self.workload.wait_for_background(cancel_event): break
                        state, details = self.verify_media_file(item.path, cancel_event); checked = time.time(); from_cache = False
                        if state in {"Passed", "Failed"}: self.metadata_cache.store_integrity(item, state, details, checked)
                    if state == "Cancelled": break
                    result = {"status": state, "details": details, "checked": checked, "cached": from_cache, "path": str(item.path), "size": item.size}
                    self.post_ui(add_result, result, index, len(items))
                self.post_ui(finished, cancel_event.is_set())
            threading.Thread(target=worker, daemon=True).start()
        def export():
            chosen = filedialog.asksaveasfilename(parent=window, title="Export integrity report", defaultextension=".csv", filetypes=(("CSV report", "*.csv"),))
            if chosen:
                try: self.write_integrity_report(Path(chosen), results); messagebox.showinfo("Report exported", f"Saved {len(results)} result(s).", parent=window)
                except OSError as exc: messagebox.showerror("Could not export report", str(exc), parent=window)
        def select_failed():
            failed = {value["path"] for value in results if value["status"] == "Failed"}
            rows = [pane.path_to_iid[path] for path in failed if path in pane.path_to_iid]
            pane.tree.selection_set(rows); pane.update_thumbnail_selection(); window.destroy(); pane.status_var.set(f"Selected {len(rows)} failed file(s) from integrity report")
        def close():
            cancel_event.set(); window.destroy()
        buttons = ttk.Frame(window, padding=10); buttons.pack(fill="x")
        start_button = ttk.Button(buttons, text="Start", command=start); start_button.pack(side="left")
        cancel_button = ttk.Button(buttons, text="Cancel", command=cancel_event.set, state="disabled"); cancel_button.pack(side="left", padx=5)
        export_button = ttk.Button(buttons, text="Export CSV…", command=export, state="disabled"); export_button.pack(side="left", padx=(12, 5))
        select_button = ttk.Button(buttons, text="Select failed", command=select_failed, state="disabled"); select_button.pack(side="left")
        ttk.Button(buttons, text="Close", command=close).pack(side="right")
        window.protocol("WM_DELETE_WINDOW", close)

    @staticmethod
    def build_video_contact_sheet(item: MediaItem, output: Path, frame_count: int, columns: int, frame_width: int, captions: bool, cancel_event: threading.Event, progress_callback=None) -> tuple[str, str]:
        """Extract evenly spaced frames and atomically write one PNG contact sheet."""
        if not item.duration or item.duration <= 0:
            return "Failed", "The video duration is unavailable"
        rows = (frame_count + columns - 1) // columns
        caption_height = 26 if captions else 0
        header_height = 58
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        try:
            with tempfile.TemporaryDirectory(prefix="rfm-contact-sheet-") as folder:
                extracted: list[tuple[Path, float]] = []
                for index in range(frame_count):
                    if cancel_event.is_set(): return "Cancelled", "Cancelled before completion"
                    position = item.duration * (index + 1) / (frame_count + 1)
                    frame_path = Path(folder) / f"frame-{index:04d}.png"
                    command = [bundled_command("ffmpeg"), "-v", "error", "-ss", f"{position:.3f}", "-i", str(item.path), "-frames:v", "1", "-vf", f"scale={frame_width}:-2", "-y", str(frame_path)]
                    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, creationflags=flags)
                    while process.poll() is None:
                        if cancel_event.wait(0.05):
                            process.terminate()
                            try: process.wait(timeout=2)
                            except subprocess.TimeoutExpired: process.kill(); process.wait()
                            return "Cancelled", "Cancelled during frame extraction"
                    error = (process.stderr.read() if process.stderr else b"").decode("utf-8", errors="replace").strip()
                    if process.returncode or not frame_path.exists(): return "Failed", error[-2000:] or f"Could not extract frame {index + 1}"
                    extracted.append((frame_path, position))
                    if progress_callback: progress_callback(index + 1, frame_count)
                with Image.open(extracted[0][0]) as first:
                    ratio = first.height / max(1, first.width)
                frame_height = max(2, int(round(frame_width * ratio)))
                sheet = Image.new("RGB", (columns * frame_width, header_height + rows * (frame_height + caption_height)), "#171717")
                draw = ImageDraw.Draw(sheet)
                try: font = ImageFont.truetype("arial.ttf", 16); small_font = ImageFont.truetype("arial.ttf", 14)
                except OSError: font = small_font = ImageFont.load_default()
                draw.text((12, 8), item.path.name, fill="white", font=font)
                draw.text((12, 32), f"{frame_count} frames · {human_duration(item.duration)} · {item.resolution}", fill="#bdbdbd", font=small_font)
                for index, (frame_path, position) in enumerate(extracted):
                    with Image.open(frame_path) as source:
                        frame = source.convert("RGB"); frame.thumbnail((frame_width, frame_height), Image.Resampling.LANCZOS)
                        x = (index % columns) * frame_width + (frame_width - frame.width) // 2
                        y = header_height + (index // columns) * (frame_height + caption_height)
                        sheet.paste(frame, (x, y))
                    if captions:
                        label = f"{index + 1:02d}  {human_duration(position)}"
                        draw.text(((index % columns) * frame_width + 8, y + frame_height + 4), label, fill="#eeeeee", font=small_font)
                if cancel_event.is_set(): return "Cancelled", "Cancelled before saving"
                output.parent.mkdir(parents=True, exist_ok=True)
                temporary = output.with_name(f"{output.stem}.{threading.get_ident()}.tmp.png")
                sheet.save(temporary, format="PNG", optimize=True)
                os.replace(temporary, output)
            return "Passed", f"Saved {frame_count} frames to {output}"
        except (OSError, ValueError) as exc:
            return "Failed", str(exc)

    def create_video_contact_sheet(self):
        pane = self.current_pane(); videos = [item for item in pane.selected_items() if item.path.suffix.lower() in VIDEO_EXTENSIONS]
        if len(videos) != 1:
            messagebox.showinfo("Create video contact sheet", "Select exactly one video first."); return
        item = videos[0]
        window = tk.Toplevel(self); window.title("Create video contact sheet"); window.geometry("500x330"); window.transient(self)
        body = ttk.Frame(window, padding=12); body.pack(fill="both", expand=True)
        ttk.Label(body, text=item.path.name, font=("Segoe UI", 11, "bold"), wraplength=460).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        frame_var = tk.IntVar(value=12); column_var = tk.IntVar(value=4); width_var = tk.IntVar(value=320); caption_var = tk.BooleanVar(value=True)
        for row, (label, variable, low, high, step) in enumerate((("Number of frames:", frame_var, 4, 48, 1), ("Columns:", column_var, 2, 8, 1), ("Frame width (pixels):", width_var, 160, 640, 40)), 1):
            ttk.Label(body, text=label).grid(row=row, column=0, sticky="w", pady=4)
            ttk.Spinbox(body, from_=low, to=high, increment=step, textvariable=variable, width=9).grid(row=row, column=1, sticky="w", pady=4)
        ttk.Checkbutton(body, text="Show frame numbers and timestamps", variable=caption_var).grid(row=4, column=0, columnspan=2, sticky="w", pady=6)
        status_var = tk.StringVar(value="The original video will not be changed."); ttk.Label(body, textvariable=status_var, wraplength=460).grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 4))
        progress = ttk.Progressbar(body, mode="determinate"); progress.grid(row=6, column=0, columnspan=2, sticky="ew", pady=4)
        body.columnconfigure(0, weight=1)
        cancel_event = threading.Event(); running = {"value": False}
        def start():
            try: count = max(4, min(48, frame_var.get())); columns = max(2, min(8, column_var.get())); width = max(160, min(640, width_var.get()))
            except tk.TclError: messagebox.showerror("Invalid settings", "Use whole numbers for frames, columns, and width.", parent=window); return
            chosen = filedialog.asksaveasfilename(parent=window, title="Save contact sheet", initialfile=f"{item.path.stem} - contact sheet.png", defaultextension=".png", filetypes=(("PNG image", "*.png"),))
            if not chosen: return
            show_captions = caption_var.get()
            cancel_event.clear(); running["value"] = True; progress.configure(maximum=count, value=0); status_var.set("Extracting frames…"); start_button.configure(state="disabled"); cancel_button.configure(state="normal")
            def update_progress(done, total):
                if window.winfo_exists(): progress.configure(value=done); status_var.set(f"Extracting frame {done} of {total}…")
            def worker():
                state, details = self.build_video_contact_sheet(item, Path(chosen), count, columns, width, show_captions, cancel_event, lambda done, total: self.post_ui(update_progress, done, total))
                def finished():
                    if not window.winfo_exists(): return
                    running["value"] = False; start_button.configure(state="normal"); cancel_button.configure(state="disabled"); status_var.set(details)
                    if state == "Passed": messagebox.showinfo("Contact sheet complete", details, parent=window)
                    elif state == "Failed": messagebox.showerror("Contact sheet failed", details, parent=window)
                self.post_ui(finished)
            threading.Thread(target=worker, daemon=True).start()
        def close(): cancel_event.set(); window.destroy()
        buttons = ttk.Frame(body); buttons.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        start_button = ttk.Button(buttons, text="Create…", command=start); start_button.pack(side="left")
        cancel_button = ttk.Button(buttons, text="Cancel", command=cancel_event.set, state="disabled"); cancel_button.pack(side="left", padx=6)
        ttk.Button(buttons, text="Close", command=close).pack(side="right")
        window.protocol("WM_DELETE_WINDOW", close)

    @staticmethod
    def plan_video_conversions(items: list[MediaItem], preset_name: str, destination: Path, source_root: Path, preserve_relative: bool, existing_policy: str, resolution_name: str | None = None) -> list[dict]:
        preset = TRANSCODE_PRESETS.get(preset_name)
        if not preset: return [{"item": item, "target": item.path, "status": "Unknown preset"} for item in items]
        if resolution_name is not None and resolution_name not in TRANSCODE_RESOLUTIONS: return [{"item": item, "target": item.path, "status": "Unknown resolution"} for item in items]
        family = TRANSCODE_PRESET_CODEC_FAMILY.get(preset_name)
        resolution_suffix = f" {resolution_name}" if family is not None and resolution_name in TRANSCODE_RESOLUTIONS and resolution_name != TRANSCODE_SOURCE_RESOLUTION else ""
        plans = []; reserved = set()
        for item in sorted(items, key=lambda value: str(value.path).casefold()):
            try: relative_parent = item.path.relative_to(source_root).parent if preserve_relative else Path()
            except ValueError: relative_parent = Path()
            base = destination / relative_parent / f"{item.path.stem} - {preset['suffix']}{resolution_suffix}{preset['extension']}"
            target = base; key = str(target.absolute()).casefold()
            if existing_policy == "Keep both":
                counter = 2
                while target.exists() or key in reserved:
                    target = base.with_name(f"{base.stem} ({counter}){base.suffix}"); key = str(target.absolute()).casefold(); counter += 1
            status = "Skip existing" if target.exists() else ("Same as source" if str(target.absolute()).casefold() == str(item.path.absolute()).casefold() else "Ready")
            if key in reserved: status = "Duplicate output"
            reserved.add(key); plans.append({"item": item, "target": target, "status": status, "preset": preset_name})
        return plans

    @staticmethod
    @functools.lru_cache(maxsize=1)
    def ffmpeg_capabilities() -> tuple[frozenset[str], frozenset[str], str]:
        """Return encoders and hardware acceleration methods advertised by FFmpeg."""
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        try:
            encoders_result = subprocess.run([bundled_command("ffmpeg"), "-hide_banner", "-encoders"], capture_output=True, text=True, timeout=12, creationflags=flags)
            accelerators_result = subprocess.run([bundled_command("ffmpeg"), "-hide_banner", "-hwaccels"], capture_output=True, text=True, timeout=12, creationflags=flags)
            encoder_text = f"{encoders_result.stdout}\n{encoders_result.stderr}"
            encoders = frozenset(match.group(1) for line in encoder_text.splitlines() if (match := re.match(r"^\s*[A-Z\.]{6}\s+(\S+)", line)))
            accelerator_text = f"{accelerators_result.stdout}\n{accelerators_result.stderr}"
            accelerators = frozenset(line.strip() for line in accelerator_text.splitlines() if line.strip() and " " not in line.strip() and line.strip() != "Hardware acceleration methods:")
            error = "" if encoders else "FFmpeg did not report any encoders"
            return encoders, accelerators, error
        except (OSError, subprocess.SubprocessError) as exc:
            return frozenset(), frozenset(), str(exc)

    @classmethod
    def available_transcode_engines(cls, preset_name: str) -> tuple[str, ...]:
        family = TRANSCODE_PRESET_CODEC_FAMILY.get(preset_name)
        if family is None:
            return (TRANSCODE_SOFTWARE,)
        encoders, _accelerators, _error = cls.ffmpeg_capabilities()
        values = [TRANSCODE_AUTOMATIC, TRANSCODE_SOFTWARE]
        for engine, families in TRANSCODE_ENGINE_ENCODERS.items():
            if families.get(family) not in encoders:
                continue
            if engine == "VA-API (Linux)" and (sys.platform == "win32" or not Path("/dev/dri/renderD128").exists()):
                continue
            values.append(engine)
        return tuple(values)

    @staticmethod
    def transcode_arguments(preset_name: str, crf: int, engine: str, hardware_decode: bool, resolution_name: str | None = None) -> tuple[list[str], list[str], str]:
        preset = TRANSCODE_PRESETS[preset_name]
        family = TRANSCODE_PRESET_CODEC_FAMILY.get(preset_name)
        arguments = [str(value).replace("{crf}", str(max(0, min(63, int(crf))))) for value in preset["arguments"]]
        if resolution_name is not None and resolution_name not in TRANSCODE_RESOLUTIONS:
            raise ValueError(f"Unknown output resolution: {resolution_name}")
        if resolution_name is not None:
            while "-vf" in arguments:
                index = arguments.index("-vf"); del arguments[index:index + 2]
        target_height = TRANSCODE_RESOLUTIONS.get(resolution_name) if resolution_name is not None else None
        scale_filter = f"scale=-2:{target_height}" if target_height else None
        if family is None or engine == TRANSCODE_SOFTWARE:
            if family is not None and scale_filter:
                arguments.extend(("-vf", scale_filter))
            pre_input = ["-hwaccel", "auto"] if hardware_decode and family is not None else []
            return pre_input, arguments, "Stream copy" if family is None else TRANSCODE_SOFTWARE

        encoder = TRANSCODE_ENGINE_ENCODERS.get(engine, {}).get(family)
        if not encoder:
            raise ValueError(f"{engine} does not support the {family.upper()} preset")
        for option in ("-preset", "-crf"):
            while option in arguments:
                index = arguments.index(option); del arguments[index:index + 2]
        codec_index = arguments.index("-c:v") + 1
        arguments[codec_index] = encoder
        if "-pix_fmt" in arguments:
            pixel_index = arguments.index("-pix_fmt")
            arguments[pixel_index + 1] = "nv12"

        quality = str(max(0, min(51, int(crf))))
        if engine == "NVIDIA NVENC":
            arguments.extend(("-preset", "p5", "-rc", "vbr", "-cq", quality, "-b:v", "0"))
        elif engine == "Intel Quick Sync":
            arguments.extend(("-preset", "medium", "-global_quality", quality))
        elif engine == "AMD AMF":
            arguments.extend(("-quality", "quality", "-rc", "cqp", "-qp_i", quality, "-qp_p", quality, "-qp_b", quality))
        elif engine == "VA-API (Linux)":
            if "-pix_fmt" in arguments:
                index = arguments.index("-pix_fmt"); del arguments[index:index + 2]
            if "-vf" in arguments:
                index = arguments.index("-vf") + 1
                if hardware_decode:
                    arguments[index] = arguments[index].replace("scale=-2:", "scale_vaapi=w=-2:h=")
                else:
                    arguments[index] += ",format=nv12,hwupload"
            elif target_height:
                vaapi_filter = f"scale_vaapi=w=-2:h={target_height}" if hardware_decode else f"{scale_filter},format=nv12,hwupload"
                arguments.extend(("-vf", vaapi_filter))
            elif not hardware_decode:
                arguments.extend(("-vf", "format=nv12,hwupload"))
            arguments.extend(("-qp", quality))
        if engine != "VA-API (Linux)" and scale_filter:
            arguments.extend(("-vf", scale_filter))

        if engine == "VA-API (Linux)":
            pre_input = ["-vaapi_device", "/dev/dri/renderD128"]
            if hardware_decode: pre_input += ["-hwaccel", "vaapi", "-hwaccel_output_format", "vaapi"]
        else:
            pre_input = ["-hwaccel", "auto"] if hardware_decode else []
        return pre_input, arguments, f"{engine} ({encoder})"

    @classmethod
    def transcode_video_file(cls, item: MediaItem, target: Path, preset_name: str, crf: int, cancel_event: threading.Event, progress_callback=None, engine: str = TRANSCODE_AUTOMATIC, hardware_decode: bool = True, resolution_name: str | None = None) -> tuple[str, str]:
        preset = TRANSCODE_PRESETS.get(preset_name)
        if not preset: return "Failed", "Unknown conversion preset"
        if resolution_name is not None and resolution_name not in TRANSCODE_RESOLUTIONS: return "Failed", f"Unknown output resolution: {resolution_name}"
        if cancel_event.is_set(): return "Cancelled", "Conversion cancelled"
        if target.exists(): return "Skipped", "Output appeared before conversion started"
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f"{target.stem}.{threading.get_ident()}.partial{target.suffix}")
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        family = TRANSCODE_PRESET_CODEC_FAMILY.get(preset_name)
        encoders, _accelerators, capability_error = cls.ffmpeg_capabilities()
        if family is None:
            engine_candidates = [TRANSCODE_SOFTWARE]
        elif engine == TRANSCODE_AUTOMATIC:
            engine_candidates = [value for value in cls.available_transcode_engines(preset_name) if value not in {TRANSCODE_AUTOMATIC, TRANSCODE_SOFTWARE}] + [TRANSCODE_SOFTWARE]
        else:
            engine_candidates = [engine]
        if engine not in {TRANSCODE_AUTOMATIC, TRANSCODE_SOFTWARE}:
            wanted = TRANSCODE_ENGINE_ENCODERS.get(engine, {}).get(family or "")
            if not wanted or wanted not in encoders:
                return "Failed", f"{engine} is not available for this preset in the bundled FFmpeg"

        failures = []
        for candidate in engine_candidates:
            decode_attempts = (True, False) if hardware_decode and family is not None else (False,)
            for decode_attempt in decode_attempts:
                process = None
                try:
                    pre_input, arguments, engine_details = cls.transcode_arguments(preset_name, crf, candidate, decode_attempt, resolution_name)
                    if progress_callback: progress_callback(0.0)
                    command = [bundled_command("ffmpeg"), "-v", "error", "-y", *pre_input, "-i", str(item.path), *arguments, "-progress", "pipe:1", "-stats_period", "0.25", "-nostats", str(temporary)]
                    with tempfile.TemporaryFile() as error_log:
                        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=error_log, text=True, creationflags=flags)
                        lines: queue.Queue[str] = queue.Queue()
                        def reader(active_process=process):
                            if active_process.stdout:
                                for line in active_process.stdout: lines.put(line.rstrip())
                        threading.Thread(target=reader, daemon=True).start()
                        while process.poll() is None:
                            if cancel_event.wait(0.05):
                                process.terminate()
                                try: process.wait(timeout=3)
                                except subprocess.TimeoutExpired: process.kill(); process.wait()
                                try: temporary.unlink()
                                except OSError: pass
                                return "Cancelled", "Conversion cancelled"
                            try:
                                while True:
                                    line = lines.get_nowait()
                                    if line.startswith("out_time_us=") and item.duration and item.duration > 0 and progress_callback:
                                        progress_callback(min(1.0, int(line.split("=", 1)[1]) / 1_000_000 / item.duration))
                            except (queue.Empty, ValueError): pass
                        error_log.seek(0); error = error_log.read().decode("utf-8", errors="replace").strip()
                    if process.returncode or not temporary.exists():
                        try: temporary.unlink()
                        except OSError: pass
                        decode_label = "hardware decode" if decode_attempt else "software decode"
                        failures.append(f"{engine_details}, {decode_label}: {error[-1200:] or f'FFmpeg returned code {process.returncode}'}")
                        continue
                    if cancel_event.is_set():
                        try: temporary.unlink()
                        except OSError: pass
                        return "Cancelled", "Conversion cancelled"
                    os.replace(temporary, target)
                    if progress_callback: progress_callback(1.0)
                    decode_label = "hardware decode" if decode_attempt else "software decode"
                    resolution_details = resolution_name if family is not None and resolution_name else TRANSCODE_SOURCE_RESOLUTION
                    return "Passed", f"Saved {target} using {engine_details} with {decode_label} at {resolution_details}"
                except (OSError, ValueError) as exc:
                    if process and process.poll() is None: process.kill()
                    try: temporary.unlink()
                    except OSError: pass
                    failures.append(f"{candidate}: {exc}")
        suffix = f"\nCapability check: {capability_error}" if capability_error else ""
        return "Failed", ("\n\n".join(failures[-4:]) or "No suitable conversion engine was available") + suffix

    def convert_selected_videos(self):
        pane = self.current_pane(); items = [item for item in pane.selected_items() if item.path.suffix.lower() in VIDEO_EXTENSIONS]
        if not items: messagebox.showinfo("Convert videos", "Select one or more video files first."); return
        other = self.right if pane is self.left else self.left
        window = tk.Toplevel(self); window.title("Convert selected videos"); window.geometry("1060x690"); window.transient(self)
        settings = ttk.LabelFrame(window, text="Conversion settings", padding=10); settings.pack(fill="x", padx=10, pady=10)
        preset_var = tk.StringVar(value="H.264 MP4 (compatible)"); crf_var = tk.IntVar(value=23); resolution_var = tk.StringVar(value=TRANSCODE_SOURCE_RESOLUTION); destination_var = tk.StringVar(value=str(other.current_path)); preserve_var = tk.BooleanVar(value=pane.recursive_var.get()); existing_var = tk.StringVar(value="Skip existing")
        engine_var = tk.StringVar(value=TRANSCODE_AUTOMATIC); hardware_decode_var = tk.BooleanVar(value=True); engine_status_var = tk.StringVar()
        ttk.Label(settings, text="Preset:").grid(row=0, column=0, sticky="w", pady=4); preset_box = ttk.Combobox(settings, textvariable=preset_var, state="readonly", values=tuple(TRANSCODE_PRESETS), width=30); preset_box.grid(row=0, column=1, sticky="w", padx=5)
        ttk.Label(settings, text="Quality (CRF):").grid(row=0, column=2, sticky="w", padx=(15, 0)); ttk.Spinbox(settings, from_=18, to=35, textvariable=crf_var, width=6).grid(row=0, column=3, sticky="w", padx=5)
        ttk.Label(settings, text="Resolution:").grid(row=1, column=0, sticky="w", pady=4); resolution_box = ttk.Combobox(settings, textvariable=resolution_var, state="readonly", values=tuple(TRANSCODE_RESOLUTIONS), width=24); resolution_box.grid(row=1, column=1, sticky="w", padx=5)
        ttk.Label(settings, text="1080p and 720p set the output height while preserving the aspect ratio.").grid(row=1, column=2, columnspan=2, sticky="w", padx=(15, 0))
        ttk.Label(settings, text="Lower quality values request higher quality; hardware engines map this value to their own control. Remux ignores quality and resolution.").grid(row=2, column=1, columnspan=3, sticky="w")
        ttk.Label(settings, text="Encoding engine:").grid(row=3, column=0, sticky="w", pady=(10, 4)); engine_box = ttk.Combobox(settings, textvariable=engine_var, state="readonly", width=24); engine_box.grid(row=3, column=1, sticky="w", padx=5, pady=(10, 4))
        hardware_decode_check = ttk.Checkbutton(settings, text="Use hardware decoding when available", variable=hardware_decode_var)
        hardware_decode_check.grid(row=3, column=2, columnspan=2, sticky="w", padx=(15, 0), pady=(10, 4))
        ttk.Label(settings, textvariable=engine_status_var, wraplength=780).grid(row=4, column=1, columnspan=3, sticky="w")
        ttk.Label(settings, text="Output folder:").grid(row=5, column=0, sticky="w", pady=(10, 4)); ttk.Entry(settings, textvariable=destination_var).grid(row=5, column=1, columnspan=2, sticky="ew", padx=5, pady=(10, 4)); ttk.Button(settings, text="Browse…", command=lambda: destination_var.set(filedialog.askdirectory(parent=window, title="Choose conversion output folder") or destination_var.get())).grid(row=5, column=3, sticky="w", pady=(10, 4))
        ttk.Checkbutton(settings, text="Preserve folders relative to the active pane", variable=preserve_var).grid(row=6, column=1, columnspan=2, sticky="w", pady=4); ttk.Combobox(settings, textvariable=existing_var, state="readonly", values=("Skip existing", "Keep both"), width=16).grid(row=6, column=3, sticky="w"); settings.columnconfigure(1, weight=1)
        ttk.Label(window, text="Original videos are always retained. Review every output path before starting.", padding=(10, 0)).pack(fill="x")
        tree = ttk.Treeview(window, columns=("status", "source", "target", "result"), show="headings")
        for key, label, width in (("status", "Status", 110), ("source", "Source", 340), ("target", "Output", 430), ("result", "Result", 180)): tree.heading(key, text=label); tree.column(key, width=width)
        scroll = ttk.Scrollbar(window, orient="vertical", command=tree.yview); tree.configure(yscrollcommand=scroll.set); scroll.pack(side="right", fill="y", padx=(0, 10)); tree.pack(fill="both", expand=True, padx=(10, 0), pady=8)
        progress = ttk.Progressbar(window, mode="determinate", maximum=100); progress.pack(fill="x", padx=10); status_var = tk.StringVar(); ttk.Label(window, textvariable=status_var, padding=(10, 4)).pack(fill="x")
        current = {"plans": []}; cancel_event = threading.Event(); running = {"value": False}; previous_preset = {"value": preset_var.get()}
        def update_engine_choices(_event=None):
            selected_preset = preset_var.get()
            if selected_preset == "720p H.264 proxy" and previous_preset["value"] != selected_preset:
                resolution_var.set("720p")
            previous_preset["value"] = selected_preset
            values = self.available_transcode_engines(preset_var.get()); engine_box.configure(values=values)
            if engine_var.get() not in values: engine_var.set(values[0])
            encoders, accelerators, error = self.ffmpeg_capabilities()
            if TRANSCODE_PRESET_CODEC_FAMILY.get(preset_var.get()) is None:
                engine_box.configure(state="disabled"); resolution_box.configure(state="disabled"); hardware_decode_check.configure(state="disabled"); engine_status_var.set("Remux copies streams directly; encoding, resizing, and hardware decoding are not used.")
            else:
                engine_box.configure(state="readonly"); resolution_box.configure(state="readonly"); hardware_decode_check.configure(state="normal")
                hardware = [value for value in values if value not in {TRANSCODE_AUTOMATIC, TRANSCODE_SOFTWARE}]
                acceleration = ", ".join(sorted(accelerators)) if accelerators else "none reported"
                engine_status_var.set(("FFmpeg hardware encoder support: " + (", ".join(hardware) if hardware else "none; Automatic will use CPU") + f" · Decode methods: {acceleration}") if not error else f"Capability check failed: {error} · Software encoding remains available")
            refresh_preview()
        def refresh_preview():
            if running["value"]: return
            destination_text = destination_var.get().strip()
            if not destination_text: current["plans"] = []; status_var.set("Choose an output folder."); start_button.configure(state="disabled"); return
            plans = self.plan_video_conversions(items, preset_var.get(), Path(destination_text), pane.current_path, preserve_var.get(), existing_var.get(), resolution_var.get()); current["plans"] = plans; tree.delete(*tree.get_children())
            for index, plan in enumerate(plans): tree.insert("", "end", iid=str(index), values=(plan["status"], str(plan["item"].path), str(plan["target"]), ""))
            ready = sum(plan["status"] == "Ready" for plan in plans); skipped = len(plans) - ready; source_size = sum(plan["item"].size for plan in plans if plan["status"] == "Ready")
            status_var.set(f"{ready} ready · {skipped} skipped/problem · source size {human_size(source_size)}"); start_button.configure(state="normal" if ready else "disabled")
        def start():
            refresh_preview(); plans = [plan for plan in current["plans"] if plan["status"] == "Ready"]
            if not plans: return
            try: crf = max(18, min(35, crf_var.get()))
            except tk.TclError: messagebox.showerror("Invalid quality", "CRF must be a whole number from 18 to 35.", parent=window); return
            preset_name = preset_var.get(); engine_name = engine_var.get(); use_hardware_decode = hardware_decode_var.get(); resolution_name = resolution_var.get()
            available_engines = self.available_transcode_engines(preset_name)
            if engine_name not in available_engines:
                messagebox.showerror("Encoding engine unavailable", f"{engine_name} is not available for {preset_name}. Choose another engine.", parent=window); return
            resolution_summary = resolution_name if TRANSCODE_PRESET_CODEC_FAMILY.get(preset_name) is not None else "Unchanged (stream copy)"
            decode_summary = "not used (stream copy)" if TRANSCODE_PRESET_CODEC_FAMILY.get(preset_name) is None else ("requested with safe fallback" if use_hardware_decode else "off")
            if not messagebox.askyesno("Start video conversion", f"Create {len(plans)} new video file(s)?\n\nEncoding: {engine_name}\nResolution: {resolution_summary}\nHardware decoding: {decode_summary}\n\nOriginal files will be retained. Cancel removes the current partial output and stops the remaining queue.", parent=window): return
            cancel_event.clear(); running["value"] = True; start_button.configure(state="disabled"); refresh_button.configure(state="disabled"); cancel_button.configure(state="normal"); progress.configure(value=0)
            def update(index, fraction):
                if not window.winfo_exists(): return
                progress.configure(value=((index + fraction) / len(plans)) * 100); status_var.set(f"Converting file {index + 1} of {len(plans)} · {fraction*100:.0f}%")
            def worker():
                passed = failed = cancelled = 0
                for index, plan in enumerate(plans):
                    if cancel_event.is_set(): cancelled += len(plans) - index; break
                    self.post_ui(lambda iid=str(current["plans"].index(plan)): tree.set(iid, "status", "Converting"))
                    state, details = self.transcode_video_file(plan["item"], plan["target"], preset_name, crf, cancel_event, lambda fraction, i=index: self.post_ui(update, i, fraction), engine_name, use_hardware_decode, resolution_name)
                    if state == "Passed": passed += 1
                    elif state == "Cancelled": cancelled += len(plans) - index
                    else: failed += 1
                    def show_result(plan=plan, state=state, details=details):
                        if not window.winfo_exists(): return
                        iid = str(current["plans"].index(plan)); tree.set(iid, "status", state); tree.set(iid, "result", details.split(" using ", 1)[1][:120] if state == "Passed" and " using " in details else details[:120])
                    self.post_ui(show_result)
                    if state == "Cancelled": break
                def finished():
                    if not window.winfo_exists(): return
                    running["value"] = False; start_button.configure(state="normal"); refresh_button.configure(state="normal"); cancel_button.configure(state="disabled"); progress.configure(value=100 if not cancel_event.is_set() else progress["value"]); status_var.set(f"Complete · {passed} created · {failed} failed · {cancelled} cancelled"); other.refresh_browser()
                self.post_ui(finished)
            threading.Thread(target=worker, daemon=True).start()
        def close(): cancel_event.set(); window.destroy()
        buttons = ttk.Frame(window, padding=10); buttons.pack(fill="x"); refresh_button = ttk.Button(buttons, text="Refresh preview", command=refresh_preview); refresh_button.pack(side="left"); start_button = ttk.Button(buttons, text="Start conversion…", command=start); start_button.pack(side="left", padx=6); cancel_button = ttk.Button(buttons, text="Cancel conversion", command=cancel_event.set, state="disabled"); cancel_button.pack(side="left"); ttk.Button(buttons, text="Close", command=close).pack(side="right"); window.protocol("WM_DELETE_WINDOW", close)
        preset_box.bind("<<ComboboxSelected>>", update_engine_choices); resolution_box.bind("<<ComboboxSelected>>", lambda _event: refresh_preview()); update_engine_choices()

    @staticmethod
    def image_difference_hash(path: Path) -> int:
        with Image.open(path) as source:
            image = ImageOps.exif_transpose(source).convert("L").resize((9, 8), Image.Resampling.LANCZOS)
            pixels = list(image.getdata())
        value = 0
        for row in range(8):
            for column in range(8):
                value = (value << 1) | int(pixels[row * 9 + column] > pixels[row * 9 + column + 1])
        return value

    @staticmethod
    def group_similar_hashes(entries: list[tuple[MediaItem, int]], threshold: int) -> list[list[tuple[MediaItem, int]]]:
        """Cluster dHashes with a BK-tree, avoiding quadratic all-pairs comparison."""
        if len(entries) < 2: return []
        parents = list(range(len(entries)))
        def find(index):
            while parents[index] != index:
                parents[index] = parents[parents[index]]; index = parents[index]
            return index
        def union(left, right):
            left, right = find(left), find(right)
            if left != right: parents[right] = left
        root = None
        for index, (_item, value) in enumerate(entries):
            if root is None:
                root = [value, index, {}]; continue
            stack = [root]
            while stack:
                node = stack.pop(); distance = (value ^ node[0]).bit_count()
                if distance <= threshold: union(index, node[1])
                low, high = distance - threshold, distance + threshold
                stack.extend(child for edge, child in node[2].items() if low <= edge <= high)
            node = root
            while True:
                distance = (value ^ node[0]).bit_count()
                child = node[2].get(distance)
                if child is None: node[2][distance] = [value, index, {}]; break
                node = child
        groups: dict[int, list[tuple[MediaItem, int]]] = {}
        for index, entry in enumerate(entries): groups.setdefault(find(index), []).append(entry)
        return sorted((group for group in groups.values() if len(group) > 1), key=lambda group: (-len(group), str(group[0][0].path).casefold()))

    def find_similar_images(self):
        pane = self.current_pane(); window = tk.Toplevel(self); window.title("Find visually similar images"); window.geometry("540x270"); window.transient(self)
        body = ttk.Frame(window, padding=12); body.pack(fill="both", expand=True)
        ttk.Label(body, text="Perceptual image matching", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(body, text="Review-only: this tool never deletes or changes files.").grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 12))
        scope_var = tk.StringVar(value="Visible"); threshold_var = tk.IntVar(value=6)
        ttk.Label(body, text="Scope:").grid(row=2, column=0, sticky="w", pady=4); ttk.Combobox(body, textvariable=scope_var, state="readonly", values=("Visible", "All scanned"), width=14).grid(row=2, column=1, sticky="w")
        ttk.Label(body, text="Similarity tolerance (0–16):").grid(row=3, column=0, sticky="w", pady=4); ttk.Spinbox(body, from_=0, to=16, textvariable=threshold_var, width=8).grid(row=3, column=1, sticky="w")
        ttk.Label(body, text="Lower values are stricter. 6 is a useful starting point for resized or lightly recompressed copies.", wraplength=500).grid(row=4, column=0, columnspan=2, sticky="w", pady=(2, 8))
        status_var = tk.StringVar(value="Ready"); ttk.Label(body, textvariable=status_var).grid(row=5, column=0, columnspan=2, sticky="w")
        progress = ttk.Progressbar(body, mode="determinate"); progress.grid(row=6, column=0, columnspan=2, sticky="ew", pady=7); body.columnconfigure(0, weight=1)
        cancel_event = threading.Event()
        def start():
            try: threshold = max(0, min(16, threshold_var.get()))
            except tk.TclError: messagebox.showerror("Invalid tolerance", "Enter a whole number from 0 to 16.", parent=window); return
            source = list(pane.visible_items) if scope_var.get() == "Visible" else list(pane.items.values())
            items = [item for item in source if item.path.suffix.lower() in IMAGE_EXTENSIONS]
            if len(items) < 2: messagebox.showinfo("Not enough images", "The chosen scope contains fewer than two images.", parent=window); return
            cancel_event.clear(); start_button.configure(state="disabled"); cancel_button.configure(state="normal"); progress.configure(maximum=len(items), value=0); status_var.set(f"Hashing {len(items)} images…")
            def update(done, cached, failed):
                if window.winfo_exists(): progress.configure(value=done); status_var.set(f"Hashing {done} of {len(items)} · {cached} cached · {failed} unreadable")
            def worker():
                entries = []; cached_count = failed = 0
                for index, item in enumerate(items, 1):
                    if cancel_event.is_set(): break
                    value = self.metadata_cache.cached_image_hash(item)
                    if value is not None: cached_count += 1
                    else:
                        try: value = self.image_difference_hash(item.path); self.metadata_cache.store_image_hash(item, value)
                        except (OSError, ValueError): failed += 1; value = None
                    if value is not None: entries.append((item, value))
                    if index % 10 == 0 or index == len(items): self.post_ui(update, index, cached_count, failed)
                self.metadata_cache.save()
                groups = [] if cancel_event.is_set() else self.group_similar_hashes(entries, threshold)
                def finished():
                    if not window.winfo_exists(): return
                    if cancel_event.is_set(): status_var.set("Cancelled"); start_button.configure(state="normal"); cancel_button.configure(state="disabled")
                    else: window.destroy(); self.show_similar_image_results(pane, groups, threshold, cached_count, failed)
                self.post_ui(finished)
            threading.Thread(target=worker, daemon=True).start()
        buttons = ttk.Frame(body); buttons.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        start_button = ttk.Button(buttons, text="Start", command=start); start_button.pack(side="left")
        cancel_button = ttk.Button(buttons, text="Cancel", command=cancel_event.set, state="disabled"); cancel_button.pack(side="left", padx=6)
        ttk.Button(buttons, text="Close", command=lambda: (cancel_event.set(), window.destroy())).pack(side="right")

    def show_similar_image_results(self, pane: FilePane, groups: list[list[tuple[MediaItem, int]]], threshold: int, cached_count: int, failed: int):
        if not groups:
            messagebox.showinfo("Similar image search", f"No visually similar groups found at tolerance {threshold}.\n\n{cached_count} cached hash(es); {failed} unreadable image(s)."); return
        window = tk.Toplevel(self); window.title("Review visually similar images"); window.geometry("1120x720")
        ttk.Label(window, text=f"{len(groups)} visually similar group(s) · tolerance {threshold} · {cached_count} cached · {failed} unreadable", font=("Segoe UI", 11, "bold")).pack(fill="x", padx=10, pady=(10, 2))
        ttk.Label(window, text="Similarity is an estimate. Review files before taking any action; this window cannot delete them.").pack(fill="x", padx=10, pady=(0, 8))
        preview = ttk.Label(window, text="Select an image", anchor="center"); preview.pack(fill="x", padx=10, pady=4, ipady=90)
        columns = ("group", "distance", "name", "folder", "resolution", "size")
        tree = ttk.Treeview(window, columns=columns, show="headings", selectmode="browse")
        for key, label, width in (("group", "Group", 65), ("distance", "Difference", 85), ("name", "Name", 260), ("folder", "Folder", 430), ("resolution", "Resolution", 100), ("size", "Size", 90)):
            tree.heading(key, text=label); tree.column(key, width=width, anchor="center" if key in {"group", "distance", "resolution", "size"} else "w")
        scroll = ttk.Scrollbar(window, orient="vertical", command=tree.yview); tree.configure(yscrollcommand=scroll.set); scroll.pack(side="right", fill="y", padx=(0, 10)); tree.pack(fill="both", expand=True, padx=(10, 0))
        item_map = {}
        for group_number, group in enumerate(groups, 1):
            reference_hash = group[0][1]
            for item, value in group:
                iid = tree.insert("", "end", values=(group_number, (reference_hash ^ value).bit_count(), item.path.name, str(item.path.parent), item.resolution, human_size(item.size)))
                item_map[iid] = (group_number, item)
        def selected(_event=None):
            selection = tree.selection()
            if not selection: return
            _group, item = item_map[selection[0]]; self.generate_thumbnail(window, preview, item, 0, (640, 260))
        tree.bind("<<TreeviewSelect>>", selected)
        def select_group():
            selection = tree.selection()
            if not selection: return
            group_number = item_map[selection[0]][0]; paths = {str(item.path) for group, item in item_map.values() if group == group_number}
            rows = [pane.path_to_iid[path] for path in paths if path in pane.path_to_iid]; pane.tree.selection_set(rows); pane.update_thumbnail_selection(); pane.status_var.set(f"Selected {len(rows)} visible file(s) from similar-image group {group_number}"); window.destroy()
        actions = ttk.Frame(window, padding=10); actions.pack(fill="x"); ttk.Button(actions, text="Select this group in source pane", command=select_group).pack(side="left"); ttk.Button(actions, text="Close", command=window.destroy).pack(side="right")
        first = next(iter(item_map), None)
        if first: tree.selection_set(first); tree.focus(first); selected()

    @staticmethod
    def file_digest(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""): digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def quick_file_digest(path: Path, size: int) -> str:
        """Fingerprint three small regions before an expensive whole-file hash."""
        chunk_size = 256 * 1024
        digest = hashlib.blake2b(digest_size=16)
        digest.update(str(size).encode("ascii"))
        offsets = (0, max(0, size // 2 - chunk_size // 2), max(0, size - chunk_size))
        with path.open("rb") as stream:
            for offset in offsets:
                stream.seek(offset)
                digest.update(offset.to_bytes(8, "little"))
                digest.update(stream.read(chunk_size))
        return digest.hexdigest()

    def find_duplicates(self, pane: FilePane | None = None):
        pane = pane or self.current_pane(); items = list(pane.items.values())
        size_groups: dict[int, list[MediaItem]] = {}
        for item in items: size_groups.setdefault(item.size, []).append(item)
        candidates = [item for group in size_groups.values() if len(group) > 1 for item in group]
        if not candidates: messagebox.showinfo("Duplicates", "No same-size duplicate candidates were found."); return
        pane.status_var.set(f"Quick-checking {len(candidates)} duplicate candidate(s)…")
        def worker():
            quick_groups: dict[tuple[int, str], list[MediaItem]] = {}
            quick_cache_hits = 0
            for index, item in enumerate(candidates, 1):
                try:
                    fingerprint = self.metadata_cache.cached_file_hash(item.path, item.size, item.modified)
                    if fingerprint:
                        quick_cache_hits += 1
                    else:
                        fingerprint = self.quick_file_digest(item.path, item.size)
                        self.metadata_cache.store_file_hash(item.path, item.size, item.modified, fingerprint)
                    quick_groups.setdefault((item.size, fingerprint), []).append(item)
                except OSError:
                    continue
                if index % 25 == 0 or index == len(candidates):
                    self.post_ui(pane.status_var.set, f"Quick-checking duplicates {index} of {len(candidates)}…")
            full_candidates = [item for group in quick_groups.values() if len(group) > 1 for item in group]
            groups: dict[str, list[MediaItem]] = {}
            full_cache_hits = 0
            for index, item in enumerate(full_candidates, 1):
                try:
                    fingerprint = self.metadata_cache.cached_file_hash(item.path, item.size, item.modified, full=True)
                    if fingerprint:
                        full_cache_hits += 1
                    else:
                        fingerprint = self.file_digest(item.path)
                        self.metadata_cache.store_file_hash(item.path, item.size, item.modified, fingerprint, full=True)
                    groups.setdefault(fingerprint, []).append(item)
                except OSError:
                    continue
                if index % 10 == 0 or index == len(full_candidates):
                    self.post_ui(pane.status_var.set, f"Verifying exact matches {index} of {len(full_candidates)}…")
            self.metadata_cache.save()
            duplicates = [item for group in groups.values() if len(group) > 1 for item in group[1:]]
            self.post_ui(self.finish_duplicate_search, pane, groups, duplicates, quick_cache_hits + full_cache_hits)
        threading.Thread(target=worker, daemon=True).start()

    def finish_duplicate_search(self, pane: FilePane, groups: dict, duplicates: list[MediaItem], hash_cache_hits: int = 0):
        duplicate_groups = [group for group in groups.values() if len(group) > 1]
        if not duplicate_groups:
            pane.status_var.set(f"No exact duplicates found · {hash_cache_hits} cached fingerprint(s)")
            messagebox.showinfo("Duplicate search complete", "No exact duplicates were found.")
            return
        pane.status_var.set(f"{len(duplicate_groups)} exact duplicate group(s) · {hash_cache_hits} cached fingerprint(s)")
        self.show_duplicate_review(pane, duplicate_groups)

    @staticmethod
    def duplicate_labels(group: list[MediaItem], item: MediaItem) -> str:
        labels = []
        if item is group[0]: labels.append("First")
        if item.modified == max(value.modified for value in group): labels.append("Newest")
        if item.modified == min(value.modified for value in group): labels.append("Oldest")
        if item.size == min(value.size for value in group): labels.append("Smallest")
        if item.size == max(value.size for value in group): labels.append("Largest")
        return ", ".join(labels)

    def show_duplicate_review(self, pane: FilePane, groups: list[list[MediaItem]]):
        window = tk.Toplevel(self)
        window.title("Review exact duplicates")
        window.geometry("1120x760")
        window.thumbnail_images = []
        ttk.Label(window, text=f"Found {len(groups)} exact duplicate group(s). Select a row to preview it beside another copy from the same group.", font=("Segoe UI", 11, "bold")).pack(fill="x", padx=10, pady=(10, 4))
        ttk.Label(window, text="Exact duplicates have identical contents and file size, so Smallest and Largest will normally be tied. Dates and locations can still differ.").pack(fill="x", padx=10, pady=(0, 8))

        preview = ttk.Frame(window)
        preview.pack(fill="x", padx=10, pady=(0, 8))
        preview_labels = []
        preview_details = []
        for column in range(2):
            card = ttk.LabelFrame(preview, text=f"Preview {column + 1}", padding=8)
            card.grid(row=0, column=column, sticky="nsew", padx=(0, 5) if column == 0 else (5, 0))
            image_label = ttk.Label(card, text="Select a duplicate", anchor="center")
            image_label.pack(fill="both", expand=True)
            detail = tk.StringVar(value="—")
            ttk.Label(card, textvariable=detail, anchor="center", justify="center", wraplength=500).pack(fill="x", pady=(6, 0))
            preview_labels.append(image_label); preview_details.append(detail)
        preview.columnconfigure(0, weight=1); preview.columnconfigure(1, weight=1)

        columns = ("group", "name", "folder", "size", "modified", "labels")
        tree_frame = ttk.Frame(window); tree_frame.pack(fill="both", expand=True, padx=10)
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="extended")
        headings = {"group": "Group", "name": "Filename", "folder": "Folder", "size": "Size", "modified": "Modified", "labels": "Why it may be kept"}
        widths = {"group": 60, "name": 210, "folder": 390, "size": 90, "modified": 145, "labels": 200}
        for column in columns:
            tree.heading(column, text=headings[column]); tree.column(column, width=widths[column], anchor="center" if column in {"group", "size", "modified"} else "w")
        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview); tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y"); tree.pack(fill="both", expand=True)
        item_map = {}
        for group_index, group in enumerate(groups, 1):
            for item_index, item in enumerate(group):
                iid = f"{group_index}-{item_index}"
                item_map[iid] = (group_index - 1, item)
                tree.insert("", "end", iid=iid, values=(group_index, item.path.name, str(item.path.parent), human_size(item.size), datetime.fromtimestamp(item.modified).strftime("%Y-%m-%d %H:%M:%S"), self.duplicate_labels(group, item)))

        def show_pair(_event=None):
            selection = tree.selection()
            if not selection: return
            group_index, chosen = item_map[selection[0]]
            group = groups[group_index]
            second = next((item_map[iid][1] for iid in selection[1:] if item_map[iid][0] == group_index), None)
            second = second or next((item for item in group if item is not chosen), chosen)
            for index, item in enumerate((chosen, second)):
                preview_labels[index].configure(image="", text="Loading preview…")
                preview_details[index].set(f"{item.path}\n{human_size(item.size)} · {datetime.fromtimestamp(item.modified).strftime('%Y-%m-%d %H:%M:%S')}\n{self.duplicate_labels(group, item)}")
                self.generate_thumbnail(window, preview_labels[index], item, index)
        tree.bind("<<TreeviewSelect>>", show_pair)
        first_row = next(iter(item_map), None)
        if first_row: tree.selection_set(first_row); tree.focus(first_row); show_pair()

        controls = ttk.Frame(window); controls.pack(fill="x", padx=10, pady=10)
        ttk.Label(controls, text="Keep one per group:").pack(side="left")
        for strategy in ("First", "Newest", "Oldest", "Smallest", "Largest"):
            ttk.Button(controls, text=strategy, command=lambda value=strategy.lower(): self.apply_duplicate_strategy(pane, groups, value, window)).pack(side="left", padx=3)
        ttk.Button(controls, text="Clear proposal", command=lambda: pane.tree.selection_remove(pane.tree.selection())).pack(side="left", padx=(10, 3))
        ttk.Button(controls, text="Close without changes", command=window.destroy).pack(side="right")

    def apply_duplicate_strategy(self, pane: FilePane, groups: list[list[MediaItem]], strategy: str, window: tk.Toplevel):
        redundant = []
        for group in groups:
            if strategy == "newest": keeper = max(group, key=lambda item: item.modified)
            elif strategy == "oldest": keeper = min(group, key=lambda item: item.modified)
            elif strategy == "smallest": keeper = min(group, key=lambda item: (item.size, item.modified))
            elif strategy == "largest": keeper = max(group, key=lambda item: (item.size, item.modified))
            else: keeper = group[0]
            redundant.extend(item for item in group if item is not keeper)
        paths = {str(item.path) for item in redundant}
        rows = [iid for iid in pane.tree.get_children() if pane.tree.item(iid, "tags") and pane.tree.item(iid, "tags")[0] in paths]
        pane.tree.selection_set(rows)
        if rows: pane.tree.focus(rows[0]); pane.tree.see(rows[0])
        pane.status_var.set(f"Duplicate proposal: keep {strategy} · selected {len(rows)} redundant file(s) for review")
        window.destroy()
        messagebox.showinfo("Duplicate proposal applied", f"The {strategy} copy in each group was kept unselected.\n\n{len(rows)} redundant file(s) are selected in the main pane. Review them there before moving or deleting anything.")

    def compare_selected(self, pane: FilePane | None = None):
        pane = pane or self.current_pane(); items = pane.selected_items()
        if len(items) != 2: messagebox.showinfo("Select two files", "Select exactly two files to compare."); return
        window = tk.Toplevel(self); window.title("Compare files"); window.geometry("800x430")
        window.thumbnail_images = []
        previews = ttk.Frame(window); previews.pack(fill="x", padx=8, pady=(8, 0))
        left_preview = ttk.Label(previews, text="Loading preview…", anchor="center"); left_preview.pack(side="left", fill="x", expand=True)
        right_preview = ttk.Label(previews, text="Loading preview…", anchor="center"); right_preview.pack(side="left", fill="x", expand=True)
        self.generate_thumbnail(window, left_preview, items[0], 0); self.generate_thumbnail(window, right_preview, items[1], 1)
        fields = (("Path", lambda i: str(i.path)), ("Type", lambda i: i.path.suffix[1:].upper()), ("Codec", lambda i: i.codec), ("Resolution", lambda i: i.resolution), ("Size", lambda i: human_size(i.size)), ("Duration", lambda i: human_duration(i.duration)), ("Bitrate", lambda i: f"{i.bitrate/1_000_000:.2f} Mbps" if i.bitrate else "—"), ("Frame rate", lambda i: f"{i.frame_rate:.2f} fps" if i.frame_rate else "—"), ("Audio", lambda i: f"{i.audio_codec} {i.audio_channels or ''}ch"), ("Pixel format", lambda i: i.pixel_format), ("HDR", lambda i: i.hdr), ("Modified", lambda i: datetime.fromtimestamp(i.modified).strftime("%Y-%m-%d %H:%M:%S")))
        tree = ttk.Treeview(window, columns=("field", "left", "right"), show="headings")
        for column, label, width in (("field", "Property", 110), ("left", items[0].path.name, 320), ("right", items[1].path.name, 320)):
            tree.heading(column, text=label); tree.column(column, width=width)
        for field, getter in fields: tree.insert("", "end", values=(field, getter(items[0]), getter(items[1])))
        tree.pack(fill="both", expand=True, padx=8, pady=8)
        actions = ttk.Frame(window); actions.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(actions, text="Keep left (recycle right)", command=lambda: self.recycle_compare_file(items[1], window, pane)).pack(side="left")
        ttk.Button(actions, text="Keep right (recycle left)", command=lambda: self.recycle_compare_file(items[0], window, pane)).pack(side="right")

    def recycle_compare_file(self, item: MediaItem, window: tk.Toplevel, pane: FilePane):
        if messagebox.askyesno("Confirm", f"Move {item.path.name} to the Recycle Bin / Trash?", parent=window):
            continuation = pane.continuation_path_after_removal((item.path,))
            send2trash(str(item.path)); window.destroy()
            pane.remove_known_paths((item.path,)); pane.refresh_view(continuation)
            pane.status_var.set("Moved 1 file to Trash · no rescan needed")

    def show_thumbnails(self):
        self.current_pane().set_view_mode("Thumbnails")

    def generate_thumbnail(self, window, label, item: MediaItem, index: int, dimensions: tuple[int, int] = (150, 100)):
        width, height = dimensions
        cache_key = hashlib.sha256(f"thumbnail-v2|{item.path.resolve()}|{item.size}|{item.modified}|{width}x{height}".encode()).hexdigest()
        output = self.thumbnail_directory / f"{cache_key}.png"
        if output.exists() and self.valid_thumbnail_png(output):
            try: os.utime(output, None)
            except OSError: pass
            self.finish_thumbnail(window, label, output, 0); return
        if output.exists():
            try: output.unlink()
            except OSError: pass
        cache_epoch = self.thumbnail_cache_epoch
        def worker():
            if not self.workload.wait_for_background():
                return
            temporary = output.with_name(f"{output.stem}.{threading.get_ident()}.tmp.png")
            result_code = 1
            if item.path.suffix.lower() in IMAGE_EXTENSIONS:
                try:
                    with Image.open(item.path) as source:
                        image = ImageOps.exif_transpose(source)
                        image.thumbnail((width, height), Image.Resampling.LANCZOS)
                        if image.mode not in {"RGB", "RGBA"}:
                            image = image.convert("RGBA" if "transparency" in image.info else "RGB")
                        image.save(temporary, format="PNG")
                    result_code = 0 if self.valid_thumbnail_png(temporary) else 1
                except Exception:
                    # Pillow deliberately handles the common fast path. Keep
                    # FFmpeg as a compatibility fallback for unusual codecs.
                    result_code = 1
            command = [bundled_command("ffmpeg"), "-v", "error"]
            if item.path.suffix.lower() in VIDEO_EXTENSIONS:
                seek_seconds = item.duration * 0.15 if item.duration and item.duration > 0 else 1.0
                command += ["-ss", f"{seek_seconds:.3f}"]
            command += ["-i", str(item.path), "-frames:v", "1", "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease", "-y", str(temporary)]
            try:
                if result_code and item.path.suffix.lower() in IMAGE_EXTENSIONS:
                    try: temporary.unlink()
                    except OSError: pass
                if result_code:
                    result = subprocess.run(command, capture_output=True, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
                    result_code = result.returncode
                if result_code == 0 and self.valid_thumbnail_png(temporary) and cache_epoch == self.thumbnail_cache_epoch:
                    os.replace(temporary, output)
                    self.thumbnail_write_count += 1
                    if self.thumbnail_write_count % 50 == 0: self.request_thumbnail_cache_prune()
                else:
                    try: temporary.unlink()
                    except OSError: pass
            except (OSError, subprocess.TimeoutExpired):
                try: temporary.unlink()
                except OSError: pass
                result_code = 1
            self.post_ui(self.finish_thumbnail, window, label, output, result_code)
        self.thumbnail_executor.submit(worker)

    @staticmethod
    def valid_thumbnail_png(path: Path) -> bool:
        try:
            with path.open("rb") as stream:
                header = stream.read(24)
            return len(header) == 24 and header[:8] == b"\x89PNG\r\n\x1a\n" and header[12:16] == b"IHDR" and path.stat().st_size > 32
        except OSError:
            return False

    def finish_thumbnail(self, window: tk.Toplevel, label: ttk.Label, output: Path, returncode: int):
        try:
            if not window.winfo_exists() or not label.winfo_exists() or returncode or not self.valid_thumbnail_png(output): return
            label_generation = getattr(label, "thumbnail_generation", None)
            if label_generation is not None and getattr(window, "thumbnail_generation", label_generation) != label_generation: return
            photo = tk.PhotoImage(file=output)
            label.thumbnail_photo = photo
            label.configure(image=photo, text="")
        except (tk.TclError, RuntimeError): pass

    @staticmethod
    def folder_inventory(pane: FilePane) -> dict[str, Path]:
        iterator = pane.current_path.rglob("*") if pane.recursive_var.get() else pane.current_path.iterdir()
        result = {}
        for path in iterator:
            try:
                if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    result[str(path.relative_to(pane.current_path)).lower()] = path
            except OSError: continue
        return result

    def compare_folders(self):
        left, right = self.folder_inventory(self.left), self.folder_inventory(self.right)
        rows = []
        for key in sorted(set(left) | set(right)):
            left_path, right_path = left.get(key), right.get(key)
            if left_path and not right_path: status = "Left only"
            elif right_path and not left_path: status = "Right only"
            else:
                assert left_path and right_path
                left_stat, right_stat = left_path.stat(), right_path.stat()
                if left_stat.st_size == right_stat.st_size and abs(left_stat.st_mtime - right_stat.st_mtime) < 1: status = "Same"
                elif left_stat.st_mtime > right_stat.st_mtime: status = "Left newer"
                elif right_stat.st_mtime > left_stat.st_mtime: status = "Right newer"
                else: status = "Different"
            rows.append((key, status, left_path, right_path))
        window = tk.Toplevel(self); window.title("Folder comparison and synchronization"); window.geometry("900x600")
        ttk.Label(window, text=f"Left: {self.left.current_path}\nRight: {self.right.current_path}").pack(fill="x", padx=8, pady=8)
        tree = ttk.Treeview(window, columns=("path", "status"), show="headings", selectmode="extended")
        tree.heading("path", text="Relative path"); tree.heading("status", text="Status"); tree.column("path", width=650); tree.column("status", width=140)
        row_map = {}
        for index, row in enumerate(rows):
            iid = str(index); tree.insert("", "end", iid=iid, values=(row[0], row[1])); row_map[iid] = row
        tree.pack(fill="both", expand=True, padx=8)
        buttons = ttk.Frame(window); buttons.pack(fill="x", padx=8, pady=8)
        def selected_rows(): return [row_map[iid] for iid in tree.selection()] or rows
        ttk.Button(buttons, text="Copy missing/newer → right", command=lambda: self.sync_rows(selected_rows(), True)).pack(side="left")
        ttk.Button(buttons, text="Copy missing/newer → left", command=lambda: self.sync_rows(selected_rows(), False)).pack(side="left", padx=6)
        ttk.Button(buttons, text="Close", command=window.destroy).pack(side="right")

    def sync_rows(self, rows: list, to_right: bool):
        pairs = []
        for key, status, left_path, right_path in rows:
            if to_right and left_path and status in {"Left only", "Left newer", "Different"}:
                pairs.append((left_path, self.right.current_path / Path(key)))
            elif not to_right and right_path and status in {"Right only", "Right newer", "Different"}:
                pairs.append((right_path, self.left.current_path / Path(key)))
        if not pairs: messagebox.showinfo("Nothing to synchronize", "No selected files need copying in that direction."); return
        direction = "right" if to_right else "left"
        if messagebox.askyesno("Synchronize preview", f"Queue {len(pairs)} file(s) for copying to the {direction} pane?"):
            self.enqueue_operation(pairs, False, f"Synchronize to {direction} pane")

    def save_workspace(self):
        name = simpledialog.askstring("Save workspace", "Workspace name:", parent=self)
        if not name: return
        self.workspaces[name.strip()] = {
            "left": self.left.get_state(), "right": self.right.get_state(),
            "browser_split": self.browser_panes.sash_coord(0)[0], "preview_split": self.current_preview_split(),
        }
        try: save_json(self.workspaces_path, self.workspaces)
        except OSError as exc: messagebox.showerror("Could not save workspace", str(exc))

    def load_workspace(self):
        if not self.workspaces: messagebox.showinfo("No workspaces", "Save a workspace first."); return
        name = simpledialog.askstring("Load workspace", "Enter a workspace name:\n\n" + "\n".join(sorted(self.workspaces)), parent=self)
        if not name or name not in self.workspaces: return
        state = self.workspaces[name]
        self.left.apply_state(state.get("left", {})); self.right.apply_state(state.get("right", {}))
        try:
            self.browser_panes.sash_place(0, int(state.get("browser_split", self.winfo_width() // 2)), 0)
            self.preview_split_position = int(state.get("preview_split", self.winfo_height() * .68))
            if self.preview_area_shown(): self.restore_preview_layout()
        except (tk.TclError, ValueError, TypeError): pass

    @staticmethod
    def smart_collection_state(pane: FilePane) -> dict:
        return {
            "path": str(pane.current_path), "recursive": pane.recursive_var.get(),
            "show_videos": pane.show_videos_var.get(), "show_images": pane.show_images_var.get(),
            "search": pane.search_var.get(), "resolution_filter": pane.filter_var.get(),
            "advanced_filters": dict(pane.advanced_filters), "sort_column": pane.sort_column,
            "sort_reverse": pane.sort_reverse, "view_mode": pane.view_mode_var.get(),
            "thumbnail_size": pane.thumbnail_size_var.get(), "thumbnail_browse_mode": pane.thumbnail_browse_mode,
        }

    @staticmethod
    def smart_collection_summary(state: dict) -> str:
        parts = []
        if state.get("search"): parts.append(f"name: {state['search']}")
        if state.get("resolution_filter", "All") != "All": parts.append(str(state["resolution_filter"]))
        filters = state.get("advanced_filters", {})
        if filters.get("tag"): parts.append(f"tag: {filters['tag']}")
        if filters.get("min_rating"): parts.append(f"rating ≥ {filters['min_rating']}")
        if filters.get("color"): parts.append(f"label: {filters['color']}")
        if filters.get("codec"): parts.append(f"codec: {filters['codec']}")
        if state.get("recursive"): parts.append("subfolders")
        return " · ".join(parts) or "All visible media"

    def save_smart_collection(self, name: str | None = None):
        name = name or simpledialog.askstring("Save smart collection", "Collection name:", parent=self)
        if not name or not name.strip(): return False
        name = name.strip()
        if name in self.smart_collections and not messagebox.askyesno("Replace smart collection", f"Replace the existing collection named {name}?", parent=self): return False
        self.smart_collections[name] = self.smart_collection_state(self.current_pane())
        try: save_json(self.smart_collections_path, self.smart_collections)
        except OSError as exc: messagebox.showerror("Could not save collection", str(exc), parent=self); return False
        return True

    def apply_smart_collection(self, name: str, pane: FilePane | None = None) -> bool:
        state = self.smart_collections.get(name)
        if not isinstance(state, dict): return False
        pane = pane or self.current_pane()
        path = Path(state.get("path", pane.current_path))
        if not path.is_dir():
            messagebox.showerror("Collection folder unavailable", f"The saved folder does not currently exist:\n{path}", parent=self); return False
        pane.recursive_var.set(bool(state.get("recursive", False)))
        pane.show_videos_var.set(bool(state.get("show_videos", True)))
        pane.show_images_var.set(bool(state.get("show_images", True)))
        pane.search_var.set(str(state.get("search", "")))
        pane.filter_var.set(str(state.get("resolution_filter", "All")))
        pane.advanced_filters = dict(state.get("advanced_filters", {}))
        pane.sort_column = str(state.get("sort_column", "name"))
        if pane.sort_column not in pane.tree["columns"]: pane.sort_column = "name"
        pane.sort_reverse = bool(state.get("sort_reverse", False))
        pane.update_sort_label()
        pane.thumbnail_size_var.set(str(state.get("thumbnail_size", "Medium")))
        pane.thumbnail_browse_mode = str(state.get("thumbnail_browse_mode", "Continuous"))
        if pane.thumbnail_browse_mode not in {"Continuous", "Paged"}: pane.thumbnail_browse_mode = "Continuous"
        pane.thumbnail_browse_mode_var.set(pane.thumbnail_browse_mode)
        pane.set_view_mode(str(state.get("view_mode", "Details")))
        return pane.navigate(path)

    def rename_smart_collection(self, old: str, new: str) -> bool:
        new = new.strip()
        if old not in self.smart_collections or not new: return False
        state = self.smart_collections.pop(old); self.smart_collections[new] = state
        try: save_json(self.smart_collections_path, self.smart_collections)
        except OSError:
            self.smart_collections.pop(new, None); self.smart_collections[old] = state; return False
        return True

    def delete_smart_collection(self, name: str) -> dict | None:
        state = self.smart_collections.pop(name, None)
        if state is None: return None
        try: save_json(self.smart_collections_path, self.smart_collections)
        except OSError:
            self.smart_collections[name] = state; return None
        return state

    def restore_smart_collection(self, name: str, state: dict) -> bool:
        self.smart_collections[name] = state
        try: save_json(self.smart_collections_path, self.smart_collections)
        except OSError:
            self.smart_collections.pop(name, None); return False
        return True

    def manage_smart_collections(self):
        window = tk.Toplevel(self); window.title("Smart collections"); window.geometry("850x470"); window.transient(self)
        ttk.Label(window, text="Saved one-pane searches", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 4))
        ttk.Label(window, text="Applying a collection changes only the active pane's folder, filters, sorting, and view.").pack(anchor="w", padx=10, pady=(0, 8))
        tree = ttk.Treeview(window, columns=("name", "folder", "query"), show="headings", selectmode="browse")
        tree.heading("name", text="Name"); tree.heading("folder", text="Folder"); tree.heading("query", text="Query")
        tree.column("name", width=170); tree.column("folder", width=310); tree.column("query", width=330)
        tree.pack(fill="both", expand=True, padx=10)
        deleted_stack = []
        def refresh(preselect: str | None = None):
            tree.delete(*tree.get_children())
            for index, name in enumerate(sorted(self.smart_collections, key=str.casefold)):
                state = self.smart_collections[name]
                iid = str(index); tree.insert("", "end", iid=iid, values=(name, state.get("path", ""), self.smart_collection_summary(state)))
                if name == preselect: tree.selection_set(iid); tree.focus(iid); tree.see(iid)
        def selected_name():
            selected = tree.selection(); return str(tree.item(selected[0], "values")[0]) if selected else None
        def save_current():
            if self.save_smart_collection(): refresh()
        def apply_selected():
            name = selected_name()
            if name and self.apply_smart_collection(name): window.destroy()
        def rename_selected():
            old = selected_name()
            if not old: return
            new = simpledialog.askstring("Rename smart collection", "New name:", initialvalue=old, parent=window)
            if not new or not new.strip() or new.strip() == old: return
            new = new.strip()
            if new in self.smart_collections and not messagebox.askyesno("Replace collection", f"Replace {new}?", parent=window): return
            if self.rename_smart_collection(old, new): refresh(new)
        def delete_selected():
            name = selected_name()
            if not name or not messagebox.askyesno("Delete smart collection", f"Delete {name}?\n\nNo media files or annotations will be changed.", parent=window): return
            state = self.delete_smart_collection(name)
            if state is not None: deleted_stack.append((name, state)); refresh()
        def undo_delete():
            if not deleted_stack: return
            name, state = deleted_stack.pop()
            if self.restore_smart_collection(name, state): refresh(name)
        buttons = ttk.Frame(window); buttons.pack(fill="x", padx=10, pady=10)
        ttk.Button(buttons, text="Save current", command=save_current).pack(side="left")
        ttk.Button(buttons, text="Apply", command=apply_selected).pack(side="left", padx=5)
        ttk.Button(buttons, text="Rename", command=rename_selected).pack(side="left")
        ttk.Button(buttons, text="Delete", command=delete_selected).pack(side="left", padx=5)
        ttk.Button(buttons, text="Undo delete", command=undo_delete).pack(side="left")
        ttk.Button(buttons, text="Close", command=window.destroy).pack(side="right")
        tree.bind("<Double-1>", lambda _event: apply_selected())
        refresh()

    @staticmethod
    def folder_rule_matches(item: MediaItem, rule: dict) -> bool:
        if not bool(rule.get("enabled", True)): return False
        kind = str(rule.get("kind", "Any"))
        if kind == "Images" and item.path.suffix.lower() not in IMAGE_EXTENSIONS: return False
        if kind == "Videos" and item.path.suffix.lower() not in VIDEO_EXTENSIONS: return False
        raw_extensions = re.split(r"[,;\s]+", str(rule.get("extensions", "")).strip())
        extensions = {value.lower() if value.startswith(".") else "." + value.lower() for value in raw_extensions if value}
        if extensions and item.path.suffix.lower() not in extensions: return False
        if str(rule.get("filename", "")).strip().casefold() not in item.path.name.casefold(): return False
        if str(rule.get("codec", "")).strip().casefold() not in item.codec.casefold(): return False
        try: minimum_rating = max(0, min(5, int(rule.get("min_rating", 0))))
        except (ValueError, TypeError): minimum_rating = 0
        if item.rating < minimum_rating: return False
        wanted_tag = str(rule.get("tag", "")).strip().casefold()
        if wanted_tag and wanted_tag not in {tag.casefold() for tag in item.tags}: return False
        return True

    @classmethod
    def plan_folder_rules(cls, items: list[MediaItem], rules: list[dict], source_root: Path, preserve_relative: bool = True) -> list[dict]:
        plans = []
        for item in items:
            rule = next((candidate for candidate in rules if cls.folder_rule_matches(item, candidate)), None)
            if not rule: continue
            destination_text = str(rule.get("destination", "")).strip(); action = str(rule.get("action", "Copy")).title()
            if not destination_text:
                plans.append({"item": item, "rule": rule, "action": action, "target": item.path, "status": "Rule has no destination"}); continue
            destination = Path(destination_text)
            try: relative = item.path.relative_to(source_root) if preserve_relative else Path(item.path.name)
            except ValueError: relative = Path(item.path.name)
            target = destination / relative
            source_key, target_key = str(item.path.absolute()).casefold(), str(target.absolute()).casefold()
            status = "Already in destination" if source_key == target_key else ("Target exists" if target.exists() else "Ready")
            if action not in {"Copy", "Move"}: status = "Invalid action"
            plans.append({"item": item, "rule": rule, "action": action, "target": target, "status": status})
        counts = {}
        for plan in plans:
            if plan["status"] in {"Ready", "Target exists"}:
                key = str(plan["target"].absolute()).casefold(); counts[key] = counts.get(key, 0) + 1
        for plan in plans:
            if plan["status"] in {"Ready", "Target exists"} and counts[str(plan["target"].absolute()).casefold()] > 1: plan["status"] = "Duplicate target"
        return plans

    def save_folder_rules(self):
        save_json(self.folder_rules_path, self.folder_rules)

    def edit_folder_rule(self, parent: tk.Misc, existing: dict | None, callback):
        rule = dict(existing or {"name": "New rule", "enabled": True, "action": "Move", "destination": "", "kind": "Any", "extensions": "", "filename": "", "codec": "", "min_rating": 0, "tag": ""})
        window = tk.Toplevel(parent); window.title("Edit folder rule" if existing else "Add folder rule"); window.geometry("620x500"); window.transient(parent); window.grab_set()
        body = ttk.Frame(window, padding=12); body.pack(fill="both", expand=True)
        variables = {key: tk.StringVar(value=str(rule.get(key, ""))) for key in ("name", "action", "destination", "kind", "extensions", "filename", "codec", "min_rating", "tag")}; enabled_var = tk.BooleanVar(value=bool(rule.get("enabled", True)))
        rows = (("Rule name:", "name"), ("Action:", "action"), ("Destination folder:", "destination"), ("Media kind:", "kind"), ("Extensions (comma separated):", "extensions"), ("Filename contains:", "filename"), ("Codec contains:", "codec"), ("Minimum rating (0–5):", "min_rating"), ("Required exact tag:", "tag"))
        for row, (label, key) in enumerate(rows):
            ttk.Label(body, text=label).grid(row=row, column=0, sticky="w", pady=4)
            if key == "action": widget = ttk.Combobox(body, textvariable=variables[key], state="readonly", values=("Copy", "Move"), width=18)
            elif key == "kind": widget = ttk.Combobox(body, textvariable=variables[key], state="readonly", values=("Any", "Images", "Videos"), width=18)
            else: widget = ttk.Entry(body, textvariable=variables[key])
            widget.grid(row=row, column=1, sticky="ew", padx=(8, 4), pady=4)
            if key == "destination": ttk.Button(body, text="Browse…", command=lambda: variables["destination"].set(filedialog.askdirectory(parent=window, title="Choose rule destination") or variables["destination"].get())).grid(row=row, column=2, sticky="w")
        ttk.Checkbutton(body, text="Rule enabled", variable=enabled_var).grid(row=len(rows), column=1, sticky="w", pady=5); body.columnconfigure(1, weight=1)
        ttk.Label(body, text="All non-empty conditions must match. Rules are checked from top to bottom; the first match wins.", wraplength=580).grid(row=len(rows)+1, column=0, columnspan=3, sticky="w", pady=(8, 4))
        def save():
            name, destination = variables["name"].get().strip(), variables["destination"].get().strip()
            if not name: messagebox.showerror("Invalid rule", "Enter a rule name.", parent=window); return
            if not destination: messagebox.showerror("Invalid rule", "Choose a destination folder.", parent=window); return
            try: rating = max(0, min(5, int(variables["min_rating"].get())))
            except ValueError: messagebox.showerror("Invalid rating", "Minimum rating must be a whole number from 0 to 5.", parent=window); return
            result = {key: variables[key].get().strip() for key in variables}; result["enabled"] = enabled_var.get(); result["min_rating"] = rating; callback(result); window.destroy()
        buttons = ttk.Frame(body); buttons.grid(row=len(rows)+2, column=0, columnspan=3, sticky="ew", pady=(12, 0)); ttk.Button(buttons, text="Save rule", command=save).pack(side="left"); ttk.Button(buttons, text="Cancel", command=window.destroy).pack(side="right")

    def preview_folder_rules(self, parent: tk.Misc):
        pane = self.current_pane(); window = tk.Toplevel(parent); window.title("Preview folder organization rules"); window.geometry("1100x680"); window.transient(parent)
        controls = ttk.Frame(window, padding=10); controls.pack(fill="x"); scope_var = tk.StringVar(value="Visible"); preserve_var = tk.BooleanVar(value=True)
        ttk.Label(controls, text="Scope:").pack(side="left"); ttk.Combobox(controls, textvariable=scope_var, state="readonly", values=("Visible", "All scanned"), width=14).pack(side="left", padx=5); ttk.Checkbutton(controls, text="Preserve folders relative to the active pane", variable=preserve_var).pack(side="left", padx=12)
        ttk.Label(window, text="Preview only until Apply is confirmed. The first enabled matching rule wins.", padding=(10, 0)).pack(fill="x")
        tree = ttk.Treeview(window, columns=("status", "rule", "action", "source", "target"), show="headings")
        for key, label, width in (("status", "Status", 130), ("rule", "Rule", 150), ("action", "Action", 65), ("source", "Source", 350), ("target", "Destination", 390)): tree.heading(key, text=label); tree.column(key, width=width)
        scroll = ttk.Scrollbar(window, orient="vertical", command=tree.yview); tree.configure(yscrollcommand=scroll.set); scroll.pack(side="right", fill="y", padx=(0, 10)); tree.pack(fill="both", expand=True, padx=(10, 0), pady=8)
        status_var = tk.StringVar(); ttk.Label(window, textvariable=status_var, padding=(10, 0)).pack(fill="x"); current = {"plans": []}
        def refresh():
            items = list(pane.visible_items if scope_var.get() == "Visible" else pane.items.values()); plans = self.plan_folder_rules(items, self.folder_rules, pane.current_path, preserve_var.get()); current["plans"] = plans; tree.delete(*tree.get_children())
            for plan in plans: tree.insert("", "end", values=(plan["status"], plan["rule"].get("name", "Unnamed"), plan["action"], str(plan["item"].path), str(plan["target"])))
            actionable = sum(plan["status"] in {"Ready", "Target exists"} for plan in plans); problems = sum(plan["status"] not in {"Ready", "Target exists", "Already in destination"} for plan in plans); status_var.set(f"{actionable} planned action(s) · {len(items)-len(plans)} unmatched file(s) · {problems} problem(s)"); apply_button.configure(state="normal" if actionable and not problems else "disabled")
        def apply():
            refresh(); actionable = [plan for plan in current["plans"] if plan["status"] in {"Ready", "Target exists"}]
            if not actionable: return
            if not messagebox.askyesno("Apply folder rules", f"Queue {len(actionable)} planned copy/move action(s)?\n\nExisting targets will use the normal conflict choices. Moves and replacements remain undoable.", parent=window): return
            for move in (False, True):
                pairs = [(plan["item"].path, plan["target"]) for plan in actionable if (plan["action"] == "Move") == move]
                if pairs: self.enqueue_operation(pairs, move, f"Folder rules: {'Move' if move else 'Copy'} {len(pairs)} file(s)")
            window.destroy()
        buttons = ttk.Frame(window, padding=10); buttons.pack(fill="x"); ttk.Button(buttons, text="Refresh preview", command=refresh).pack(side="left"); apply_button = ttk.Button(buttons, text="Apply…", command=apply); apply_button.pack(side="left", padx=6); ttk.Button(buttons, text="Close", command=window.destroy).pack(side="right"); refresh()

    def manage_folder_rules(self):
        window = tk.Toplevel(self); window.title("Folder organization rules"); window.geometry("900x560"); window.transient(self)
        ttk.Label(window, text="Folder organization rules", font=("Segoe UI", 12, "bold"), padding=(10, 10, 10, 2)).pack(fill="x"); ttk.Label(window, text="Rules are evaluated from top to bottom. Files are never changed until a preview is reviewed and Apply is confirmed.", padding=(10, 0)).pack(fill="x")
        tree = ttk.Treeview(window, columns=("enabled", "name", "conditions", "action", "destination"), show="headings", selectmode="browse")
        for key, label, width in (("enabled", "On", 45), ("name", "Name", 160), ("conditions", "Conditions", 300), ("action", "Action", 65), ("destination", "Destination", 300)): tree.heading(key, text=label); tree.column(key, width=width)
        tree.pack(fill="both", expand=True, padx=10, pady=8); deleted = []
        def description(rule):
            parts = [str(rule.get("kind", "Any"))]
            for key, label in (("extensions", "ext"), ("filename", "name"), ("codec", "codec"), ("tag", "tag")):
                if str(rule.get(key, "")).strip(): parts.append(f"{label}: {rule[key]}")
            try: rating = int(rule.get("min_rating", 0) or 0)
            except (ValueError, TypeError): rating = 0
            if rating: parts.append(f"rating≥{rating}")
            return "; ".join(parts)
        def refresh(select_index=None):
            tree.delete(*tree.get_children())
            for index, rule in enumerate(self.folder_rules): tree.insert("", "end", iid=str(index), values=("✓" if rule.get("enabled", True) else "", rule.get("name", "Unnamed"), description(rule), rule.get("action", "Copy"), rule.get("destination", "")))
            if select_index is not None and str(select_index) in tree.get_children(): tree.selection_set(str(select_index))
            undo_button.configure(state="normal" if deleted else "disabled"); preview_button.configure(state="normal" if self.folder_rules else "disabled")
        def selected_index():
            selection = tree.selection(); return int(selection[0]) if selection else None
        def add(): self.edit_folder_rule(window, None, lambda rule: (self.folder_rules.append(rule), self.save_folder_rules(), refresh(len(self.folder_rules)-1)))
        def edit():
            index = selected_index()
            if index is not None: self.edit_folder_rule(window, self.folder_rules[index], lambda rule: (self.folder_rules.__setitem__(index, rule), self.save_folder_rules(), refresh(index)))
        def remove():
            index = selected_index()
            if index is not None and messagebox.askyesno("Delete rule", f"Delete rule '{self.folder_rules[index].get('name','Unnamed')}'?", parent=window): deleted.append((index, self.folder_rules.pop(index))); self.save_folder_rules(); refresh()
        def undo_delete():
            if deleted:
                index, rule = deleted.pop(); self.folder_rules.insert(min(index, len(self.folder_rules)), rule); self.save_folder_rules(); refresh(min(index, len(self.folder_rules)-1))
        def move(direction):
            index = selected_index(); target = index + direction if index is not None else -1
            if index is not None and 0 <= target < len(self.folder_rules): self.folder_rules[index], self.folder_rules[target] = self.folder_rules[target], self.folder_rules[index]; self.save_folder_rules(); refresh(target)
        buttons = ttk.Frame(window, padding=10); buttons.pack(fill="x"); ttk.Button(buttons, text="Add", command=add).pack(side="left"); ttk.Button(buttons, text="Edit", command=edit).pack(side="left", padx=4); ttk.Button(buttons, text="Delete", command=remove).pack(side="left"); undo_button = ttk.Button(buttons, text="Undo delete", command=undo_delete); undo_button.pack(side="left", padx=4); ttk.Button(buttons, text="↑", width=4, command=lambda: move(-1)).pack(side="left", padx=(12, 3)); ttk.Button(buttons, text="↓", width=4, command=lambda: move(1)).pack(side="left"); preview_button = ttk.Button(buttons, text="Preview active pane…", command=lambda: self.preview_folder_rules(window)); preview_button.pack(side="right", padx=(5, 0)); ttk.Button(buttons, text="Close", command=window.destroy).pack(side="right"); refresh()

    def cache_controls(self):
        window = tk.Toplevel(self); window.title("Cache and scanning"); window.geometry("540x520"); window.transient(self)
        status = tk.StringVar()
        workers_var = tk.IntVar(value=self.scan_workers)
        profile_var = tk.StringVar(value=self.performance_profile)
        profile_description = tk.StringVar()
        thumbnail_percent_var = tk.DoubleVar(value=self.thumbnail_cache_percent)
        thumbnail_limit_var = tk.StringVar()
        exclusions_var = tk.StringVar(value="; ".join(self.excluded_patterns))
        def profile_selected(_event=None):
            profile = profile_var.get() if profile_var.get() in PERFORMANCE_PROFILES else "Balanced"
            defaults = PERFORMANCE_PROFILES[profile]
            workers_var.set(defaults["scan_workers"])
            profile_description.set(
                f"{defaults['thumbnail_workers']} thumbnail worker(s) · {defaults['preview_fps']:g} preview fps"
                + (" · background work yields to previews" if defaults["interactive_delay"] else " · maximum background throughput")
            )
        profile_selected()
        def refresh_status():
            try: disk_size = self.metadata_cache.path.stat().st_size
            except OSError: disk_size = 0
            thumbnail_size = sum(path.stat().st_size for path in self.thumbnail_directory.glob("*.png"))
            status.set(f"{self.metadata_cache.count()} metadata entries · {human_size(disk_size)}\nThumbnail cache · {human_size(thumbnail_size)} of {human_size(self.thumbnail_cache_limit())}")
            try: proposed = max(0.1, min(10.0, float(thumbnail_percent_var.get())))
            except (ValueError, tk.TclError): proposed = 1.0
            thumbnail_limit_var.set(f"{proposed:g}% of the operating-system drive · {human_size(int(self.system_drive_capacity() * proposed / 100))}")
        def prune():
            count = self.metadata_cache.prune(); refresh_status(); messagebox.showinfo("Cache pruned", f"Removed {count} stale entry/entries.", parent=window)
        def clear():
            if messagebox.askyesno("Clear cache", "Clear all cached metadata? Files will be rescanned next time.", parent=window):
                count = self.metadata_cache.clear()
                thumbnails, removed_bytes = self.clear_thumbnail_cache()
                refresh_status(); messagebox.showinfo("Cache cleared", f"Removed {count} metadata entries and cached thumbnails.", parent=window)
        def clear_thumbnails():
            files = []
            total = 0
            for path in self.thumbnail_directory.glob("*.png"):
                try: total += path.stat().st_size; files.append(path)
                except OSError: pass
            if not files:
                messagebox.showinfo("Thumbnail cache", "The thumbnail cache is already empty.", parent=window); return
            if messagebox.askyesno("Clear thumbnail cache", f"Delete {len(files)} stored thumbnail(s) using {human_size(total)}?\n\nOriginal media files and metadata will not be changed.", parent=window):
                removed, removed_bytes = self.clear_thumbnail_cache()
                refresh_status(); messagebox.showinfo("Thumbnail cache cleared", f"Deleted {removed} thumbnail(s) and freed {human_size(removed_bytes)}.", parent=window)
        def apply_scanning():
            self.apply_performance_profile(profile_var.get(), workers_var.get())
            self.excluded_patterns = [value.strip() for value in exclusions_var.get().split(";") if value.strip()]
            try: self.thumbnail_cache_percent = max(0.1, min(10.0, float(thumbnail_percent_var.get())))
            except (ValueError, tk.TclError): self.thumbnail_cache_percent = 1.0
            thumbnail_percent_var.set(self.thumbnail_cache_percent)
            self.request_thumbnail_cache_prune(); refresh_status()
            messagebox.showinfo("Settings", f"{self.performance_profile} performance settings, scanning options, and the thumbnail-cache limit were saved. The cache limit is being enforced in the background.", parent=window)
        def enforce_thumbnail_limit():
            if self.thumbnail_prune_lock.locked(): return
            try: self.thumbnail_cache_percent = max(0.1, min(10.0, float(thumbnail_percent_var.get())))
            except (ValueError, tk.TclError): self.thumbnail_cache_percent = 1.0
            thumbnail_percent_var.set(self.thumbnail_cache_percent)
            def worker():
                with self.thumbnail_prune_lock:
                    removed, _remaining = self.prune_thumbnail_cache()
                self.post_ui(lambda: [refresh_status(), messagebox.showinfo("Thumbnail cache", f"Removed {removed} least-recently-used thumbnail(s).", parent=window)] if window.winfo_exists() else None)
            threading.Thread(target=worker, daemon=True).start()
        ttk.Label(window, text="Cache and scanning", font=("Segoe UI", 12, "bold")).pack(pady=(14, 6))
        ttk.Label(window, textvariable=status).pack(pady=6); refresh_status()
        buttons = ttk.Frame(window); buttons.pack(pady=14)
        ttk.Button(buttons, text="Remove stale entries", command=prune).pack(side="left", padx=5)
        ttk.Button(buttons, text="Clear thumbnails", command=clear_thumbnails).pack(side="left", padx=5)
        ttk.Button(buttons, text="Clear all cache", command=clear).pack(side="left", padx=5)
        thumbnail_frame = ttk.LabelFrame(window, text="Thumbnail storage", padding=8); thumbnail_frame.pack(fill="x", padx=12, pady=4)
        ttk.Label(thumbnail_frame, text="Maximum percentage of operating-system drive:").grid(row=0, column=0, sticky="w")
        percent_box = ttk.Spinbox(thumbnail_frame, from_=0.1, to=10.0, increment=0.1, textvariable=thumbnail_percent_var, width=7, command=refresh_status)
        percent_box.grid(row=0, column=1, sticky="w")
        percent_box.bind("<KeyRelease>", lambda _event: refresh_status())
        ttk.Label(thumbnail_frame, textvariable=thumbnail_limit_var).grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))
        ttk.Button(thumbnail_frame, text="Enforce limit now", command=enforce_thumbnail_limit).grid(row=2, column=1, sticky="e", pady=(6, 0))
        thumbnail_frame.columnconfigure(0, weight=1)
        settings_frame = ttk.LabelFrame(window, text="Scan settings", padding=8); settings_frame.pack(fill="x", padx=12, pady=4)
        ttk.Label(settings_frame, text="Performance profile:").grid(row=0, column=0, sticky="w")
        profile_box = ttk.Combobox(settings_frame, textvariable=profile_var, state="readonly", values=tuple(PERFORMANCE_PROFILES), width=12)
        profile_box.grid(row=0, column=1, sticky="w"); profile_box.bind("<<ComboboxSelected>>", profile_selected)
        ttk.Label(settings_frame, textvariable=profile_description).grid(row=1, column=0, columnspan=2, sticky="w", pady=(3, 5))
        ttk.Label(settings_frame, text="Parallel metadata workers (1–16):").grid(row=2, column=0, sticky="w")
        ttk.Spinbox(settings_frame, from_=1, to=16, textvariable=workers_var, width=6).grid(row=2, column=1, sticky="w")
        ttk.Label(settings_frame, text="Exclude patterns (semicolon separated):").grid(row=3, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(settings_frame, textvariable=exclusions_var).grid(row=4, column=0, columnspan=2, sticky="ew")
        ttk.Label(settings_frame, text="Examples: *.tmp; proxy/*; @eaDir/*").grid(row=5, column=0, columnspan=2, sticky="w")
        ttk.Button(settings_frame, text="Apply", command=apply_scanning).grid(row=6, column=1, sticky="e", pady=(8, 0))
        settings_frame.columnconfigure(0, weight=1)

    def show_shortcuts(self):
        messagebox.showinfo("Keyboard shortcuts", "Ctrl+A   Select all shown\nCtrl+C   Copy selected\nCtrl+X   Cut selected\nCtrl+V   Paste into active pane\nCtrl+Z   Undo last file operation\nDelete   Move selected files to Recycle Bin / Trash\nF2       Rename selected file\nF5       Refresh both panes\nBackspace   Go up one folder\n, (comma)   Active preview back 10%\n. (full stop)   Active preview forward 10%\nDouble-click   Open file")

    def show_help(self):
        window = tk.Toplevel(self); window.title(f"Resolution File Manager Help — {APP_VERSION}"); window.geometry("1100x740"); window.minsize(820, 540)
        window.transient(self)
        header = ttk.Frame(window, padding=(12, 10)); header.pack(fill="x")
        ttk.Label(header, text="Resolution File Manager Help", font=("Segoe UI", 15, "bold")).pack(side="left")
        search_var = tk.StringVar(); search_entry = ttk.Entry(header, textvariable=search_var, width=34)
        search_button = ttk.Button(header, text="Search")
        search_button.pack(side="right", padx=(5, 0)); search_entry.pack(side="right", padx=(6, 0)); ttk.Label(header, text="Search all chapters:").pack(side="right")
        body = ttk.Panedwindow(window, orient="horizontal"); body.pack(fill="both", expand=True, padx=12)
        contents_frame = ttk.Frame(body, padding=(0, 0, 8, 0)); reader_frame = ttk.Frame(body)
        body.add(contents_frame, weight=0); body.add(reader_frame, weight=1)
        ttk.Label(contents_frame, text="Contents", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 5))
        chapter_list = tk.Listbox(contents_frame, width=31, exportselection=False, activestyle="dotbox")
        chapter_scroll = ttk.Scrollbar(contents_frame, orient="vertical", command=chapter_list.yview); chapter_list.configure(yscrollcommand=chapter_scroll.set)
        chapter_scroll.pack(side="right", fill="y"); chapter_list.pack(side="left", fill="both", expand=True)
        text = tk.Text(reader_frame, wrap="word", padx=18, pady=14, font=("Segoe UI", 10), relief="flat", spacing1=2, spacing3=5)
        scroll = ttk.Scrollbar(reader_frame, orient="vertical", command=text.yview); text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y"); text.pack(fill="both", expand=True)
        guide = f"""RESOLUTION FILE MANAGER {APP_VERSION}

QUICK START
1. Choose a folder independently in each pane with Browse, the folder tree, or the path box.
2. Turn on Include subfolders only when you want the complete tree below that folder scanned.
3. Use Details for sortable technical information or Thumbnails for visual browsing.
4. Select files in one pane. Copy and Move use the folder displayed in the other pane as their destination.
5. Turn on Preview or Info only in the pane where you need them. Both default off to save processing power.
6. File-changing actions show confirmation or a preview where appropriate. Delete uses Recycle Bin/Trash, and Ctrl+Z reverses supported recent actions.

The chapters on the left explain every part of the program. Type any word or phrase in Search all chapters and press Enter. Matching chapters and the number of matches appear in the contents list; use Next match to step through each highlighted occurrence.

GETTING STARTED
Each side of the window is an independent folder browser. Use Browse, the folder tree, the path box, or Up to choose folders. Click inside a pane to make it active.

View > Appearance and text size offers System, Light, Dark, and High contrast themes plus 100%, 125%, 150%, 175%, and 200% interface scaling. Changes preview immediately throughout existing controls. Save keeps the choice for future launches, Cancel or closing the window restores the previous settings, and Restore system default returns to the operating-system theme at 100%. These settings change only presentation, never media or library data.

Each pane has its own compact Explorer-style navigation strip: ← goes Back, → goes Forward, ↑ opens the parent folder, and ↻ Refreshes the folder tree and current scan. Opening a different folder after going Back starts a new forward history from that point.

The folder tree always follows the pane's current location: it expands the parent folders, selects the exact scan starting folder, and scrolls that folder into view. The current folder remains closed until you expand it, preventing a temporary Loading placeholder from being displayed. This also happens after restoring a workspace or typing a path, so a drive root is not left highlighted while a deeper folder is being scanned. Include subfolders begins at the selected/current folder shown in that pane, not at the drive root above it.

DETAILS AND THUMBNAILS
Use the view selector at the top of either pane, or the View menu, to switch that pane between Details and Thumbnails. Both views show the same files and share their selection. Thumbnail mode respects Include subfolders, media switches, search, resolution, advanced filters, and sorting. Its Sort menu offers an exact direction for Name (A–Z/Z–A), Date modified (oldest/newest), File size, Length, Codec, Resolution, Type, Bitrate, Frame rate, and Rating. Each pane sorts independently, the button shows the active order, and saved workspaces and Smart Collections restore it. Details headings remain clickable for quick sorting. Relative paths appear beneath thumbnails during recursive scans. Choose Small, Medium, or Large beside the view selector. Continuous is the default thumbnail browser: one scrollbar covers the complete filtered collection, while the program creates only visible cards plus a small buffer and recycles them during scrolling. This keeps widget and image memory bounded for very large libraries. Choose Paged beside it at any time to restore the established page grid; choose Auto, 200, 500, or 1,000 cards per page and use the compact ← and → controls. Auto uses 200 when videos are at least half the filtered results and 500 when images are the majority. Each pane and saved workspace remembers its browser choice.

The thumbnail grid measures the actual browser width before its first render and reflows automatically when a pane or the folder/browser divider is resized. In Paged mode, page 1 therefore uses the same column count as later pages for a given pane width and thumbnail size. In Continuous mode, resizing recalculates the virtual rows without constructing the whole collection. Roll the mouse wheel anywhere over a thumbnail pane—including over a card, image, or filename—to scroll that pane up and down; the two panes scroll independently.

In Details mode, the default order is Name, Codec, Resolution, Video length, File size, MB/min, FPS, Date modified, Type, Bitrate, Audio, HDR, Megapixels, Label, Tags, and Rating. Drag the divider between headers to resize a column by any amount; the horizontal-resize cursor shows when the divider is ready. Drag a header itself to reorder it—no keyboard modifier is required. A simple header click still sorts. Columns keep their chosen widths and the horizontal scrollbar reaches fields outside the pane. For precise control, choose View > Configure columns or right-click a header; the Columns window can move fields, set exact widths, and restore defaults. Existing personally arranged and saved column orders are preserved. Long recursive paths are shortened in the middle so the filename remains visible.

Video thumbnails are sampled 15% into the clip to avoid unrepresentative opening frames. If duration metadata is unavailable, the application uses a one-second fallback. Generated thumbnails are cached for faster repeat browsing.

Ordinary image thumbnails are decoded efficiently in-process with Pillow; FFmpeg is used for video frames and as a fallback for unusual image formats. Thumbnail decoding uses a small worker pool so a large folder cannot launch an excessive number of decoders. Cache images are written atomically and checked before display; incomplete or corrupt cached thumbnails are ignored and regenerated, while results belonging to an older grid are discarded safely.

Generated thumbnails remain available after the program closes, so revisiting an unchanged file normally uses its cached image immediately. Tools > Cache and scanning controls the maximum thumbnail-cache size as a percentage of the operating-system drive; the default is 1%. Reused thumbnails are marked as recent, and when the limit is exceeded the least recently used entries are removed first. The limit can be set from 0.1% to 10% and enforced immediately. Clear thumbnails reports the current count and size before confirmation, then removes only generated thumbnails—not original media or cached technical metadata. Clear all cache removes both thumbnails and metadata.

SELECTING AND PREVIEWING
Each pane has an independent tick-box action group. Click the ☐/☑ box beside a Details row or on a thumbnail card, or focus a Details row and press Space. Ticks remain collected while you highlight and preview other files, sort the pane, or change filters. The counter below the browser shows the total, including ticked files currently hidden by a filter. Click the ✓ Details heading or ✓ All shown in Thumbnails to tick every currently displayed file; repeat it to untick that displayed group. Clear ticks removes the complete group. Copy, move, drag, delete, rename, rating, tag, comparison, integrity and conversion actions use all ticked files when any exist; with no ticks they use the ordinary highlighted rows. Changing that pane to a different folder or drive clears its ticks, and ticks are not saved after closing the application.

Each browser pane has its own large ▶ Preview toggle, which defaults off to avoid unnecessary decoding. Enable Preview on the left, right, or both sides to open separate aligned preview panels below the browsers. The button has a distinct selected state so enabled previews are easy to spot. When both toggles are off, the preview area collapses completely and the browsers use the full window height. Click a file to preview it on its own side. Highlighting is independent from ticks, so you can inspect or preview another file without losing the action group. Hold Ctrl while clicking thumbnails or detail rows to highlight several files. Select matching highlights every currently displayed result. Double-click opens the highlighted file in its normal application.

Each pane also has a large independent ⓘ Info toggle. It defaults off and adds a collapsible inspector on that pane's right edge. If a file is already selected, enabling Info displays it immediately—there is no need to select it again. The inspector follows later selection in Details, Continuous thumbnails, and Paged thumbnails and shows the full path, dimensions, size, dates, duration, codec, frame rate, bitrate, pixel format, HDR, audio, unreadable reason, rating, colour, and tags. Copy path places the full path on the clipboard; Open and Reveal use the normal file actions. Turning Info off removes the inspector completely, and saved workspaces remember its state.

Show in File Explorer/Reveal works with the complete selection. With up to five selected files it sends a separate reveal request for every path. Above five, a warning shows the exact count because the operation may open many file-manager windows. Choose Yes to reveal every selected file or No to reveal only the first. Windows and macOS select each exact file; Linux opens each file's containing folder through the system file manager.

Select one file and choose Tools > View embedded metadata for a searchable, read-only view of information stored inside that file. Images show format details, EXIF camera/date fields, GPS fields when present, and safe summaries for binary blocks. Videos show container and per-stream tags through FFprobe. This work happens only on request, so ordinary scans are not slowed down. Copy selected/all sends tab-separated rows to the clipboard, and Export JSON writes a structured atomic copy; neither action alters embedded metadata.

Images and video frames automatically use the largest size that fits their own preview panel while keeping the original width-to-height ratio. Resizing the main window or either preview divider updates the image after a short delay, avoiding repeated decoder restarts while the divider is being dragged.

SCANNING AND FILTERING
Enable Include subfolders to scan recursively. Use Find for filenames, Resolution for an exact resolution, and More filters for dimensions, file size, duration, codec, orientation, and date. Cancel stops a long scan. Cache and scanning settings under Tools control parallel workers and excluded patterns.

Tools > Export media report creates a portable inventory from Selected, Visible, or All scanned files. CSV is convenient for spreadsheets, JSON preserves a structured summary and item list, and HTML produces a self-contained readable table with a sticky header. Reports include paths, media type, dimensions, size/date, duration, codecs, bitrate, frame rate, audio, pixel format, HDR, ratings, colour labels, tags, and unreadable status. Full paths can be replaced by paths relative to the active folder. Large exports show progress and can be cancelled; temporary output is removed unless the complete report is ready.

Large recursive scans collect results without repeatedly rebuilding the growing browser. When scanning finishes, Details rows are added in short batches so Play/Pause, navigation, painting, and window controls remain responsive. Thumbnail grids likewise update at scan completion. Successful copy, move, and delete commands now update only affected in-memory entries instead of rescanning both folders; unfamiliar files dropped from outside the application still trigger a safety scan only in the affected pane. Metadata cache saving runs in the background, and stopped FFmpeg preview processes are cleaned up promptly. Tools > Cache and scanning provides Quiet, Balanced, and Fast performance profiles. Balanced retains the established behaviour. Quiet reduces scan and thumbnail concurrency and targets 8 preview frames per second; Fast increases concurrency and targets 15 frames per second. Quiet and Balanced pace new uncached probes and thumbnail decodes while a preview is playing or seeking, giving interactive work priority. Cached results are never deliberately delayed. The metadata-worker field remains adjustable after selecting a profile.

Each side has independent playback, timeline, speed, audio/mute, frame cache, and decoder processes. Scratch video playback is deliberately paced to real time at 12 frames per second. This keeps previews smooth while avoiding the heavy CPU use caused by decoding the rest of a clip faster than the preview can display it, especially while a large folder scan is running.

Click anywhere on either preview timeline to move its marker directly to that position and resume playback there. You can also press and drag the marker for continuous scrubbing. Scrubbing cancels an older frame request as soon as a newer position is requested, preventing several FFmpeg decoders from competing in the background. Recently visited positions are cached in quarter-second steps, so moving back to them is immediate. Release the slider to resume playback from the chosen position.

Video preview defaults to 4× speed for faster reviewing. Use the 1×, 2×, 4×, 6×, 8×, and 16× buttons beneath the timeline to change playback speed. The active speed button is disabled to make the current setting clear. Audio is muted by default; select 🔇 Muted to enable synchronized sound, and select 🔊 Audio to mute it again. Changing speed while playing restarts video and audio together at the current timeline position.

Use |◀ and ▶| beside the audio button to move backward or forward by one frame. The application uses the video's reported frame rate, with a 25 fps fallback when that metadata is unavailable, and performs a precise seek for the resulting still. Choose ⤓ PNG to export the current video position as a full-source-resolution PNG; playback pauses at that exact position, output is written through a temporary file, and the video is never altered.

With focus outside a typing field, press comma (,) to jump the active pane's video preview backward by 10% of its total duration, or full stop/period (.) to jump forward by 10%. The active pane is the side most recently clicked. A playing preview continues playing from the new position; a paused preview remains paused and displays the exact destination frame. The keys type normally in path, search, filter, and dialog fields.

Refresh active pane or Refresh both panes under View after folders or files are changed in File Explorer or another application. Refresh rebuilds the folder tree as well as rescanning media. It is also available through F5, the toolbar, and right-click menus in the browser and folder tree. Alternatively, enable Live independently in either pane to watch its current folder automatically. Live follows navigation and uses the same scope as Include subfolders. Bursts of creates, modifications, renames, and deletions are combined before refreshing; folder changes also update the tree. A Live marker appears in the completed scan status. Live defaults off, and clearing its checkbox immediately restores manual-refresh behaviour.

COPYING AND MOVING
Select files in one pane and use the toolbar, Edit menu, right-click menu, keyboard shortcuts, or drag-and-drop. To send several selected files to another application such as Shutter, drag the large ↗ Drag selected handle beside that pane's navigation controls with the left mouse button. It exports the complete selection using the normal operating-system file-list format and works in both Details and Thumbnails without interfering with column resizing. The other pane is the destination for in-app transfers. Transfers enter a queue with progress, speed, remaining time, pause, cancel, retry, and conflict choices. Recursive transfers preserve relative folders.

Edit > Batch rename selected opens a complete preview before changing any names. Build names with {{name}} for the original stem, {{n}} for a padded sequence number, {{ext}} for the extension without a dot, and {{dotext}} for the extension including its dot. Optional find/replace can be case-sensitive or insensitive, and numbering has adjustable start and padding. Invalid Windows names, duplicate outputs, and conflicts with unselected files disable Apply. A confirmed batch uses temporary names internally so swaps and cycles cannot overwrite one another; an interrupted batch is rolled back where possible. The successful batch is one Ctrl+Z undo action, including ratings and tags.

Tools > Folder organization rules manages reusable Copy or Move rules. Each enabled rule can require a media kind, one or more extensions, filename text, codec text, a minimum rating, and an exact tag. Rules are evaluated from top to bottom and the first match wins; use the arrow buttons to change precedence. Preview active pane shows every proposed source, destination, rule, action, existing target, and problem for Visible or All scanned files, with optional recursive relative-folder preservation. Nothing happens until Apply is confirmed. Applied work uses the normal transfer queue, conflict choices, progress, cancellation, retry, and undo. Rule deletion is confirmed and can be undone while the manager remains open.

Right-click one or several selected files to assign a zero-to-five-star rating, a Red/Yellow/Green/Blue/Purple colour label, or comma-separated tags. Clear rating, None, and an empty tag list reverse those changes. These annotations are stored only in the application database; original media and embedded metadata are never altered. Details mode provides sortable Rating, Label, and Tags columns. Thumbnail captions show ratings/tags and use the colour label as their unselected outline. More filters can require a minimum rating, colour (including Unlabelled), or tag text. Internal rename, copy, move, and undo operations carry annotations to the resulting path. Clear all cache removes technical cache data but deliberately retains user annotations.

In Details mode, individual rows retain right-button file dragging; a normal right-click still opens the context menu. This preserves unrestricted left-button header resizing and reordering. For conventional left-button dragging—especially multi-file drops into another program—use ↗ Drag selected. Thumbnail cards also support ordinary left-button file dragging.

DUPLICATES AND COMPARISON
Tools > Find duplicates finds exact matches in stages. Same-size files receive a quick fingerprint sampled from the beginning, middle, and end; only matching candidates are then read completely and verified with SHA-256. Both fingerprints are retained in the SQLite cache while path, size, and modification time remain unchanged, making later searches much faster. Progress appears in the active pane status line. The review window shows two copies side by side with paths, dates, and retention labels. A strategy only selects proposed redundant files—it never deletes them automatically. Compare selected shows two chosen files and their technical metadata.

Tools > Find visually similar images detects resized, lightly recompressed, and otherwise visually close images even when their files are not byte-for-byte identical. Choose Visible or All scanned and a tolerance from 0–16; lower values are stricter and 6 is the default. The 64-bit difference hashes are cached against path, size, and modification date, and a BK-tree keeps matching practical on large collections. Results are estimates and open in a review-only window with previews and a Select this group action. The tool never deletes or changes files; review every proposed group before using normal file actions.

Tools > Verify media integrity performs a read-only full decode to find damaged or incomplete media. Choose Selected, Visible, or All scanned files, then Start. Images are decoded frame by frame in-process and video/audio streams are decoded completely with FFmpeg; original files are never changed. The check can be cancelled, and unchanged results are cached using the file path, size, and modification date. Enable Force recheck to ignore a cached result. The results can select failed files back in the source pane or be exported as a CSV report. Clear all cache removes cached integrity results but does not remove media or user ratings, colours, and tags.

Select exactly one video and choose Tools > Create video contact sheet to save a PNG overview of the clip. Choose 4–48 evenly spaced frames, 2–8 columns, a frame width from 160–640 pixels, and optional frame numbers/timestamps. Sampling avoids the very start and end of the video. Extraction runs in the background with progress and cancellation, the finished image is written atomically, and the source video is never changed.

Select one or more videos and choose Tools > Convert selected videos for a preview-first conversion queue. Presets create compatible H.264 MP4, smaller H.265 MP4, AV1 MKV, 720p H.264 proxy, or a fast stream-copy MKV remux. Resolution independently offers the source size, 1080p, or 720p for every encoded preset and every software or hardware engine. Resizing sets the selected output height, preserves the aspect ratio, and adds 1080p or 720p to the output filename. The 720p proxy preset selects 720p automatically, but you can change it before starting. Remux always retains the source resolution because it copies streams without re-encoding. Encoding engine offers Automatic, Software/CPU, NVIDIA NVENC, Intel Quick Sync, AMD AMF, and Linux VA-API according to the encoders advertised by the bundled FFmpeg and the chosen preset. Automatic tries detected hardware engines and safely falls through to alternatives and finally CPU if the matching hardware cannot actually start. An explicit hardware choice reports failure rather than silently changing the encoder. Use hardware decoding when available is independently selectable; an unsupported hardware decoder is retried with software decoding while retaining the selected encoder. The displayed detection summary lists available engines and decode methods. Quality 18–35 controls software CRF and maps to the comparable constant-quality control for hardware engines (lower is higher quality/larger output); remux ignores quality and acceleration. Output defaults to the opposite pane, can preserve folders relative to a recursive source, and either skips existing names or creates numbered Keep both names. Original videos are always retained and outputs use a partial filename until FFmpeg completes. The queue is sequential to limit CPU/memory pressure, reports the engine used plus overall/per-file progress, and Cancel terminates the current encoder, removes its partial output, and skips the remaining queue.

FOLDER SYNCHRONIZATION
Open the folders to compare in the left and right panes, then choose Tools > Compare / synchronize folders. Review Left only, Right only, Newer, and Different entries before queuing a one-way synchronization.

SAFE FILE ACTIONS
Delete sends files to the operating-system Recycle Bin or Trash. After a delete or move, the file that follows the removed selection in the active sort order is automatically selected and revealed; if the removed files were at the end, the new final file is selected. Rename and refresh also retain a useful current file, and this behaviour is shared by Details and Thumbnails. Undo reverses recent copies, moves, replacements, single renames, and complete batch renames. Replacement conflicts offer Replace, Skip, Keep both, or Replace when newer.

WORKSPACES AND CACHE
Saved workspaces remember folders, filters, view modes, columns, inspectors, and layout. Smart Collections under Tools are smaller one-pane presets: they save the folder, Include subfolders and media switches, filename and advanced filters, resolution, sorting, Details/Thumbnails view, thumbnail size, and Continuous/Paged choice. Applying one affects only the active pane. The manager can rename or delete presets; deletion requires confirmation and Undo delete restores it while the manager remains open. Smart Collections never move, delete, or annotate media. Cached metadata and thumbnails speed up future visits; Tools > Cache and scanning can inspect, prune, or clear them. Metadata is stored in an indexed SQLite database and committed incrementally during large scans. When upgrading from version 9, existing JSON metadata is imported automatically on the first launch; the old JSON file is retained as a backup but is not imported again after the database cache is cleared.

SUPPORT THE PROJECT
Resolution File Manager is provided as a standalone application without requiring a subscription. If you find it useful and would like to support continued development, choose Help > If you like this, buy John a coffee. The same optional support button appears in Help > About and opens the public JohnPerky page in your normal web browser:

https://buymeacoffee.com/johnperky

Supporting the project is completely optional. The application does not open the page automatically, collect payment information, track whether you visit it, or change any feature based on support.

BUILD AND ROLLBACK
Each release is also copied to the Desktop with its version in the filename, so installing or trying a newer build does not overwrite earlier rollback executables. The Windows project build script verifies dependency installation, PyInstaller's exit code, output existence, and a fresh output timestamp; it stops with an error instead of reporting success if packaging fails.

Windows releases use the blue dual-folder media icon for the executable, taskbar, title bar, shortcuts, and File Explorer instead of PyInstaller's generic application icon. The folders, video frame, image frame, and transfer arrows represent the application's two-pane media workflow.

Official public Windows releases are portable ZIP packages. Extract the complete ZIP and open the versioned executable; a separate FFmpeg installation is not required. The release also contains installation guidance, SHA-256 verification information, privacy information, the GNU GPL version 3 licence, source code, and third-party notices. While builds remain unsigned, Windows may display a SmartScreen warning, so obtain releases only from the official project page and compare their published SHA-256 checksum.

LICENSING AND PRIVACY
Resolution File Manager is free software distributed under GNU GPL version 3 or later. You may use, study, modify, and redistribute it under that licence. Public packages include the corresponding application source and notices for FFmpeg, Python components, and other redistributed software.

Media scanning, thumbnails, metadata, ratings, labels, tags, file operations, previews, and conversion all remain local to the computer. The application has no account, advertising, analytics, or media-library upload. It accesses an external website only after you deliberately choose a link such as Buy John a coffee; payment details are handled by that website and never by Resolution File Manager.

The Linux build must be created on Linux Mint, not Windows. build_linux.sh now packages FFmpeg, FFprobe, and FFplay into the single versioned file it places in dist, so a separate FFmpeg installation is not needed on the destination computer. Copy that file to another compatible Linux Mint PC, run chmod +x on it once, and open it. Linux builds remain processor-specific (normally x86_64), and building on the oldest Mint release you intend to support gives the widest compatibility with that release and newer ones.

TROUBLESHOOTING
The folder tree says Loading: Expand that folder once. Folders are loaded only when needed so large drives do not freeze the interface. The pane's path box always shows the actual scan location.

A deleted or externally moved folder is still shown: Choose ↻ in that pane, right-click and choose Refresh this pane, or press F5 for both panes. Live can perform this refresh automatically.

Scanning is slow or the fan becomes loud: Turn off unused Preview panes, choose the Quiet profile under Tools > Cache and scanning, narrow the starting folder, or temporarily turn off Include subfolders. A completed first scan makes later scans much faster through cached metadata.

Thumbnails are slow: Use Continuous mode, Small or Medium thumbnails, and Auto sizing. Video thumbnails need FFmpeg decoding and are naturally more expensive than images. Cached thumbnails are reused after the first successful generation.

A video preview fails or becomes slow: Pause preview during an intensive first scan, try a different file to identify a format-specific problem, and use Tools > Verify media integrity on the file. The original media is never modified by previewing.

Hardware conversion is unavailable: The engine must be included in FFmpeg and supported by installed graphics hardware and drivers. Automatic is recommended because it tries supported hardware paths and then safely falls back to CPU encoding. Explicit hardware selection reports a failure rather than silently changing engines.

A file is marked unreadable: Open Info for the recorded reason, then use Verify media integrity for a complete decode test. Permission errors, disconnected drives, corrupt files, and unsupported formats are common causes.

Columns or layout look wrong: Right-click a Details heading and choose Configure columns or Reset column widths. View > Appearance and text size can restore System appearance and 100% scaling.

Something changed unexpectedly: Stop before making more changes. Ctrl+Z reverses the most recent supported copy, move, replacement, or rename. Deleted files normally remain in the operating-system Recycle Bin/Trash. Conversion always retains the source.

GLOSSARY
Active pane: The left or right browser that most recently received a click. Menu and keyboard actions normally apply there.

Codec: The method used to encode video or audio, such as H.264, H.265/HEVC, AV1, AAC, or Opus. A container such as MP4 or MKV can hold one or more encoded streams.

Remux: Copying existing video/audio streams into another container without re-encoding. It is fast and lossless but does not change the codec.

CRF/quality: A constant-quality target for re-encoding. Lower numbers request higher quality and larger files. Hardware encoders translate it to their closest quality control.

Metadata cache: Stored technical results that avoid repeatedly probing unchanged files. It is separate from ratings, labels, and tags.

Thumbnail cache: Generated preview pictures retained on disk for faster future visits and limited through Tools > Cache and scanning.

Recursive/Include subfolders: Scan the selected folder and every folder below it. It never means the entire drive unless the drive root itself is selected.

Smart Collection: A saved view definition containing a location, filters, sorting, and presentation settings. It does not copy or move files.
"""
        chapter_pattern = re.compile(r"(?m)^([A-Z][A-Z /&-]{2,})$")
        matches = list(chapter_pattern.finditer(guide))
        chapters: list[tuple[str, str]] = []
        for index, match in enumerate(matches):
            title = match.group(1).strip().title()
            if title.startswith("Resolution File Manager"):
                continue
            end = matches[index + 1].start() if index + 1 < len(matches) else len(guide)
            chapters.append((title, guide[match.end():end].strip()))
        visible_chapters = list(range(len(chapters))); current = {"chapter": 0, "match": 0}
        status_var = tk.StringVar(value=f"{len(chapters)} chapters · Resolution File Manager {APP_VERSION}")

        text.tag_configure("chapter", font=("Segoe UI", 17, "bold"), spacing3=14)
        text.tag_configure("search_hit", background="#ffe08a", foreground="#202020")
        text.tag_configure("search_current", background="#ffad42", foreground="#101010")

        def fill_contents(labels=None):
            chapter_list.delete(0, "end")
            for label in ([chapters[index][0] for index in visible_chapters] if labels is None else labels): chapter_list.insert("end", label)

        def highlight_query(query: str):
            text.tag_remove("search_hit", "1.0", "end"); text.tag_remove("search_current", "1.0", "end")
            if not query: return 0
            count = 0; position = "1.0"
            while True:
                position = text.search(query, position, stopindex="end", nocase=True)
                if not position: break
                end = f"{position}+{len(query)}c"; text.tag_add("search_hit", position, end); position = end; count += 1
            return count

        def show_chapter(chapter_index: int, select_contents: bool = True):
            if not 0 <= chapter_index < len(chapters): return
            current["chapter"] = chapter_index; current["match"] = 0
            title, content = chapters[chapter_index]
            text.configure(state="normal"); text.delete("1.0", "end"); text.insert("end", title + "\n", "chapter"); text.insert("end", content); text.configure(state="disabled")
            count = highlight_query(search_var.get().strip())
            if select_contents and chapter_index in visible_chapters:
                position = visible_chapters.index(chapter_index); chapter_list.selection_clear(0, "end"); chapter_list.selection_set(position); chapter_list.activate(position); chapter_list.see(position)
            status_var.set(f"Chapter {chapter_index + 1} of {len(chapters)} · {title}" + (f" · {count} match(es)" if search_var.get().strip() else ""))
            text.yview_moveto(0)

        def chapter_selected(_event=None):
            selection = chapter_list.curselection()
            if selection: show_chapter(visible_chapters[selection[0]], select_contents=False)

        def search_help(_event=None):
            query = search_var.get().strip(); visible_chapters.clear()
            labels = []
            for index, (title, content) in enumerate(chapters):
                count = (title + "\n" + content).casefold().count(query.casefold()) if query else 1
                if count: visible_chapters.append(index); labels.append(f"{title}  ({count})" if query else title)
            fill_contents(labels)
            if visible_chapters:
                show_chapter(visible_chapters[0]); status_var.set(f"{len(visible_chapters)} chapter(s) match “{query}”" if query else f"{len(chapters)} chapters")
            else:
                text.configure(state="normal"); text.delete("1.0", "end"); text.insert("end", "No results\n", "chapter"); text.insert("end", f"No help chapter contains “{query}”.\n\nTry a shorter term such as thumbnails, codec, delete, scan, preview, Linux, or shortcut."); text.configure(state="disabled"); status_var.set(f"No matches for “{query}”")

        def clear_search(): search_var.set(""); search_help(); search_entry.focus_set()
        def step_chapter(delta: int):
            if not visible_chapters: return
            try: position = visible_chapters.index(current["chapter"])
            except ValueError: position = 0
            show_chapter(visible_chapters[(position + delta) % len(visible_chapters)])
        def next_match():
            ranges = text.tag_ranges("search_hit")
            if not ranges: return
            pair_count = len(ranges) // 2; pair = current["match"] % pair_count; current["match"] = pair + 1
            text.configure(state="normal"); text.tag_remove("search_current", "1.0", "end"); text.tag_add("search_current", ranges[pair * 2], ranges[pair * 2 + 1]); text.configure(state="disabled"); text.see(ranges[pair * 2])
            status_var.set(f"Match {pair + 1} of {pair_count} in {chapters[current['chapter']][0]}")

        search_button.configure(command=search_help)
        chapter_list.bind("<<ListboxSelect>>", chapter_selected); search_entry.bind("<Return>", search_help); window.bind("<F3>", lambda _event: next_match()); window.bind("<Escape>", lambda _event: window.destroy())
        controls = ttk.Frame(window, padding=(12, 8)); controls.pack(fill="x")
        ttk.Label(controls, textvariable=status_var).pack(side="left", fill="x", expand=True)
        ttk.Button(controls, text="Previous chapter", command=lambda: step_chapter(-1)).pack(side="left", padx=3)
        ttk.Button(controls, text="Next chapter", command=lambda: step_chapter(1)).pack(side="left", padx=3)
        ttk.Button(controls, text="Next match (F3)", command=next_match).pack(side="left", padx=3)
        ttk.Button(controls, text="Clear search", command=clear_search).pack(side="left", padx=3)
        ttk.Button(controls, text="Close", command=window.destroy).pack(side="left", padx=(8, 0))
        fill_contents(); show_chapter(0); search_entry.focus_set()


if __name__ == "__main__":
    MediaSorterApp().mainloop()
