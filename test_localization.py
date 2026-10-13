import json
import tempfile
import unittest
from pathlib import Path


class LocalizationSelectionTests(unittest.TestCase):
    def test_regional_locales_map_to_supported_language(self):
        from localization import normalise_locale

        cases = {
            "de-AT": "de",
            "de_AT.UTF-8": "de",
            "es-MX": "es",
            "zh-Hans-CN": "zh-CN",
            "zh_CN": "zh-CN",
            "en-IN": "en",
            "ja_JP": "ja",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(normalise_locale(raw), expected)

    def test_unknown_or_empty_locale_falls_back_to_english(self):
        from localization import normalise_locale

        self.assertEqual(normalise_locale("pt-BR"), "en")
        self.assertEqual(normalise_locale(""), "en")
        self.assertEqual(normalise_locale(None), "en")

    def test_saved_override_wins_and_system_restores_detection(self):
        from localization import select_language

        self.assertEqual(select_language("fr", "de-DE"), "fr")
        self.assertEqual(select_language("system", "de-DE"), "de")
        self.assertEqual(select_language(None, "ko-KR"), "ko")
        self.assertEqual(select_language("not-a-language", "nl-NL"), "nl")


class TranslatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.english = {
            "meta": {"language": "English"},
            "strings": {
                "hello": "Hello",
                "greeting": "Hello, {name}",
                "english_only": "English only",
            },
            "help": {
                "chapters": [
                    {"id": "quick_start", "title": "Quick Start", "body": "Start here."},
                    {"id": "privacy", "title": "Privacy", "body": "Local only."},
                ]
            },
        }
        (self.root / "en.json").write_text(json.dumps(self.english), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def write_pack(self, code, value):
        (self.root / f"{code}.json").write_text(json.dumps(value), encoding="utf-8")

    def test_selected_pack_overlays_english_and_missing_values_fall_back(self):
        from localization import Translator

        self.write_pack("de", {
            "meta": {"language": "Deutsch"},
            "strings": {"hello": "Hallo", "greeting": "Hallo, {name}", "english_only": ""},
            "help": {"chapters": []},
        })
        translator = Translator(self.root, "de")
        self.assertEqual(translator.text("hello"), "Hallo")
        self.assertEqual(translator.text("english_only"), "English only")
        self.assertEqual(translator.text("greeting", name="John"), "Hallo, John")

    def test_absent_or_malformed_selected_pack_uses_english(self):
        from localization import Translator

        missing = Translator(self.root, "fr")
        self.assertEqual(missing.language, "en")
        self.assertEqual(missing.text("hello"), "Hello")
        self.assertTrue(missing.diagnostics)

        (self.root / "de.json").write_text("{not json", encoding="utf-8")
        malformed = Translator(self.root, "de")
        self.assertEqual(malformed.language, "en")
        self.assertEqual(malformed.text("hello"), "Hello")
        self.assertTrue(malformed.diagnostics)

    def test_missing_key_and_bad_interpolation_are_safe_and_diagnostic(self):
        from localization import Translator

        translator = Translator(self.root, "en")
        self.assertEqual(translator.text("missing.key"), "missing.key")
        self.assertEqual(translator.text("greeting"), "Hello, {name}")
        self.assertEqual(translator.text("hello", unused="value"), "Hello")
        self.assertGreaterEqual(len(translator.diagnostics), 2)

    def test_help_chapters_preserve_pack_order_with_english_fallback(self):
        from localization import Translator

        self.write_pack("de", {
            "meta": {"language": "Deutsch"},
            "strings": {},
            "help": {"chapters": [
                {"id": "quick_start", "title": "Schnellstart", "body": "Hier beginnen."}
            ]},
        })
        translator = Translator(self.root, "de")
        self.assertEqual(translator.help_chapters(), [
            ("Schnellstart", "Hier beginnen."),
            ("Privacy", "Local only."),
        ])


if __name__ == "__main__":
    unittest.main()
