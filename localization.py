from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


SUPPORTED_LANGUAGES = {
    "en": "English",
    "zh-CN": "简体中文",
    "nl": "Nederlands",
    "fr": "Français",
    "de": "Deutsch",
    "ja": "日本語",
    "ko": "한국어",
    "ru": "Русский",
    "es": "Español",
}


def normalise_locale(value: str | None) -> str:
    if not value:
        return "en"
    cleaned = str(value).split(".", 1)[0].replace("_", "-").strip()
    lowered = cleaned.casefold()
    if lowered.startswith("zh"):
        return "zh-CN"
    base = lowered.split("-", 1)[0]
    return base if base in SUPPORTED_LANGUAGES else "en"


def select_language(saved: str | None, system_locale: str | None) -> str:
    if saved and str(saved).casefold() != "system" and saved in SUPPORTED_LANGUAGES:
        return saved
    return normalise_locale(system_locale)


class Translator:
    def __init__(self, locale_dir: Path, language: str):
        self.locale_dir = Path(locale_dir)
        self.diagnostics: list[str] = []
        self._english = self._load("en", required=True)
        requested = language if language in SUPPORTED_LANGUAGES else "en"
        if requested == "en":
            self.language = "en"
            self._selected = self._english
        else:
            selected = self._load(requested, required=False)
            if selected is None:
                self.language = "en"
                self._selected = self._english
            else:
                self.language = requested
                self._selected = selected

    def _load(self, language: str, required: bool) -> dict[str, Any] | None:
        path = self.locale_dir / f"{language}.json"
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict) or not isinstance(value.get("strings"), dict):
                raise ValueError("language pack must contain a strings object")
            return value
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError, TypeError) as exc:
            self.diagnostics.append(f"Could not load {path.name}: {exc}")
            if required:
                return {"meta": {"language": "English"}, "strings": {}, "help": {"chapters": []}}
            return None

    def text(self, key: str, **values: object) -> str:
        selected_strings = self._selected.get("strings", {})
        english_strings = self._english.get("strings", {})
        value = selected_strings.get(key)
        if not isinstance(value, str) or not value.strip():
            value = english_strings.get(key)
        if not isinstance(value, str) or not value:
            self.diagnostics.append(f"Missing English translation: {key}")
            return key
        try:
            return value.format(**values)
        except (KeyError, ValueError, IndexError) as exc:
            self.diagnostics.append(f"Could not format {key}: {exc}")
            fallback = english_strings.get(key, value)
            try:
                return fallback.format(**values)
            except (KeyError, ValueError, IndexError):
                return fallback

    def help_chapters(self) -> list[tuple[str, str]]:
        english = self._chapter_map(self._english)
        selected = self._chapter_map(self._selected)
        chapters: list[tuple[str, str]] = []
        for chapter_id, title, body in english:
            translated = next((entry for entry in selected if entry[0] == chapter_id), None)
            if translated and translated[1].strip() and translated[2].strip():
                chapters.append((translated[1], translated[2]))
            else:
                chapters.append((title, body))
        return chapters

    @staticmethod
    def _chapter_map(pack: dict[str, Any]) -> list[tuple[str, str, str]]:
        result: list[tuple[str, str, str]] = []
        chapters = pack.get("help", {}).get("chapters", []) if isinstance(pack.get("help"), dict) else []
        if not isinstance(chapters, list):
            return result
        for value in chapters:
            if not isinstance(value, dict):
                continue
            chapter_id = value.get("id")
            title = value.get("title")
            body = value.get("body")
            if all(isinstance(part, str) for part in (chapter_id, title, body)):
                result.append((chapter_id, title, body))
        return result
