from __future__ import annotations

import sys
from pathlib import Path


REQUIRED_LOCALES = ("en", "zh-CN", "nl", "fr", "de", "ja", "ko", "ru", "es")


def validate_release_assets(project_root: Path) -> Path:
    locale_dir = Path(project_root) / "locales"
    missing = [f"{code}.json" for code in REQUIRED_LOCALES if not (locale_dir / f"{code}.json").is_file()]
    if missing:
        raise FileNotFoundError("Missing required language packs: " + ", ".join(missing))
    return locale_dir


if __name__ == "__main__":
    try:
        validated = validate_release_assets(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent)
    except (OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)
    print(validated)
