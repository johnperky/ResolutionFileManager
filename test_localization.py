import json
import tempfile
import unittest
from pathlib import Path


class LocalizationSelectionTests(unittest.TestCase):
    def test_right_to_left_languages_are_identified(self):
        from localization import is_rtl_language

        for language in ("ar", "he", "ur", "fa"):
            self.assertTrue(is_rtl_language(language), language)
        for language in ("en", "pt-PT", "pt-BR", "zh-TW"):
            self.assertFalse(is_rtl_language(language), language)

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
            "German_Germany.1252": "de",
            "Spanish_Spain.1252": "es",
            "Chinese (Simplified)_China.936": "zh-CN",
            "sv-SE": "sv",
            "Swedish_Sweden.1252": "sv",
            "bg-BG": "bg",
            "Bulgarian_Bulgaria.1251": "bg",
            "th-TH": "th",
            "Thai_Thailand.874": "th",
            "id-ID": "id",
            "Indonesian_Indonesia.1252": "id",
            "el-GR": "el",
            "Greek_Greece.1253": "el",
            "fil-PH": "fil",
            "Filipino_Philippines.1252": "fil",
            "hi-IN": "hi",
            "Hindi_India.65001": "hi",
            "pl-PL": "pl",
            "Polish_Poland.1250": "pl",
            "it-IT": "it",
            "Italian_Italy.1252": "it",
            "ar-SA": "ar",
            "vi-VN": "vi",
            "uk-UA": "uk",
            "nb-NO": "no",
            "Norwegian_Norway.1252": "no",
            "fi-FI": "fi",
            "da-DK": "da",
            "hu-HU": "hu",
            "ro-RO": "ro",
            "cs-CZ": "cs",
            "pt-BR": "pt-BR",
            "pt-PT": "pt-PT",
            "Portuguese_Portugal.1252": "pt-PT",
            "Portuguese_Brazil.1252": "pt-BR",
            "tr-TR": "tr",
            "zh-TW": "zh-TW",
            "zh-Hant-HK": "zh-TW",
            "ms-MY": "ms",
            "he-IL": "he",
            "bn-BD": "bn",
            "ur-PK": "ur",
            "fa-IR": "fa",
            "sk-SK": "sk",
            "hr-HR": "hr",
            "sr-Latn-RS": "sr",
            "ca-ES": "ca",
            "et-EE": "et",
            "lv-LV": "lv",
            "lt-LT": "lt",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(normalise_locale(raw), expected)

    def test_unknown_or_empty_locale_falls_back_to_english(self):
        from localization import normalise_locale

        self.assertEqual(normalise_locale("zz-ZZ"), "en")
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
            "literals": {"Error": "Error", "Could not open {name}: {error}": "Could not open {name}: {error}"},
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

    def test_localized_choices_display_translations_but_preserve_internal_values(self):
        from localization import LocalizedChoices, Translator

        self.english["strings"].update({
            "view.details": "Details",
            "view.thumbnails": "Thumbnails",
            "size.medium": "Medium",
        })
        (self.root / "en.json").write_text(json.dumps(self.english), encoding="utf-8")
        self.write_pack("de", {
            "meta": {"language": "Deutsch"},
            "strings": {
                "view.details": "Details",
                "view.thumbnails": "Miniaturen",
                "size.medium": "Mittel",
            },
            "help": {"chapters": []},
        })
        translator = Translator(self.root, "de")
        choices = LocalizedChoices(translator, {
            "Details": "view.details",
            "Thumbnails": "view.thumbnails",
            "Medium": "size.medium",
        })

        self.assertEqual(choices.labels, ("Details", "Miniaturen", "Mittel"))
        self.assertEqual(choices.label("Thumbnails"), "Miniaturen")
        self.assertEqual(choices.internal("Miniaturen"), "Thumbnails")
        self.assertEqual(choices.internal("unknown"), "unknown")

    def test_ui_text_translates_exact_and_dynamic_dialog_messages(self):
        from localization import Translator

        self.write_pack("de", {
            "meta": {"language": "Deutsch"},
            "strings": {},
            "literals": {"Error": "Fehler", "Could not open {name}: {error}": "{name} konnte nicht geöffnet werden: {error}"},
            "help": {"chapters": []},
        })
        translator = Translator(self.root, "de")
        self.assertEqual(translator.ui_text("Error"), "Fehler")
        self.assertEqual(translator.ui_text("Could not open film.avi: access denied"), "film.avi konnte nicht geöffnet werden: access denied")
        self.assertEqual(translator.ui_text("Uncatalogued text"), "Uncatalogued text")


if __name__ == "__main__":
    unittest.main()
