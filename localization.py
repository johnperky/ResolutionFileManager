from __future__ import annotations

import json
import re
import string
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
    aliases = {
        "english": "en", "chinese": "zh-CN", "dutch": "nl",
        "french": "fr", "german": "de", "japanese": "ja",
        "korean": "ko", "russian": "ru", "spanish": "es",
    }
    if lowered.startswith("zh") or lowered.startswith("chinese"):
        return "zh-CN"
    base = lowered.split("-", 1)[0]
    if base in SUPPORTED_LANGUAGES:
        return base
    return next((code for name, code in aliases.items() if base.startswith(name)), "en")


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

    def ui_text(self, value: str) -> str:
        """Translate a completed dialog string, including catalogued templates."""
        if not isinstance(value, str) or self.language == "en":
            return value
        selected = self._selected.get("literals", {})
        if not isinstance(selected, dict):
            return value
        exact = selected.get(value)
        if isinstance(exact, str) and exact:
            return exact
        for template, translated in selected.items():
            if not isinstance(template, str) or not isinstance(translated, str) or "{" not in template:
                continue
            pattern_parts = []
            field_names = []
            for literal, field_name, _format_spec, _conversion in string.Formatter().parse(template):
                pattern_parts.append(re.escape(literal))
                if field_name:
                    safe_name = f"field_{len(field_names)}"
                    pattern_parts.append(f"(?P<{safe_name}>.+?)")
                    field_names.append((field_name, safe_name))
            match = re.fullmatch("".join(pattern_parts), value, flags=re.DOTALL)
            if match:
                values = {name: match.group(safe_name) for name, safe_name in field_names}
                try:
                    return translated.format(**values)
                except (KeyError, ValueError, IndexError):
                    return value
        return value

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


class LocalizedChoices:
    """Translate displayed choices without changing their saved internal IDs."""

    def __init__(self, translator: Translator, choices: dict[str, str]):
        self._internal_to_label = {
            internal: translator.text(key) for internal, key in choices.items()
        }
        self._label_to_internal = {
            label: internal for internal, label in self._internal_to_label.items()
        }

    @property
    def labels(self) -> tuple[str, ...]:
        return tuple(self._internal_to_label.values())

    def label(self, internal: str) -> str:
        return self._internal_to_label.get(internal, internal)

    def internal(self, label: str) -> str:
        return self._label_to_internal.get(label, label)
