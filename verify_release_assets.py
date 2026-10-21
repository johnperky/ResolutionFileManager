from __future__ import annotations

import sys
from pathlib import Path


REQUIRED_LOCALES = (
    "en", "zh-CN", "nl", "fr", "de", "ja", "ko", "ru", "es",
    "sv", "bg", "th", "id", "el", "fil", "hi", "pl", "it",
    "ar", "vi", "uk", "no", "fi", "da", "hu", "ro", "cs", "pt-PT", "pt-BR", "tr",
    "zh-TW", "ms", "he", "bn", "ur", "fa", "sk", "hr", "sr", "ca", "et", "lv", "lt",
)


def validate_release_assets(project_root: Path) -> Path:
    locale_dir = Path(project_root) / "locales"
    missing = [f"{code}.json" for code in REQUIRED_LOCALES if not (locale_dir / f"{code}.json").is_file()]
    if missing:
        raise FileNotFoundError("Missing required language packs: " + ", ".join(missing))
    return locale_dir


def validate_store_executable(project_root: Path, executable: Path) -> Path:
    project_root = Path(project_root)
    executable = Path(executable)
    if not executable.is_file():
        raise FileNotFoundError(f"Missing executable: {executable}")

    release_sources = [
        project_root / "media_sorter.py",
        project_root / "localization.py",
        project_root / "rtl_display.py",
        project_root / "reminder_policy.py",
        project_root / "VERSION.txt",
    ]
    release_sources.extend((project_root / "locales").glob("*.json"))
    newer_sources = [path for path in release_sources if path.is_file() and path.stat().st_mtime > executable.stat().st_mtime]
    if newer_sources:
        names = ", ".join(path.name for path in newer_sources)
        raise ValueError(
            f"Store executable is older than release source files ({names}). "
            "Run build_windows.ps1 before building the Store package."
        )
    return executable


if __name__ == "__main__":
    try:
        root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
        validated = validate_release_assets(root)
        if len(sys.argv) > 2:
            validate_store_executable(root, Path(sys.argv[2]))
    except (OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)
    print(validated)
