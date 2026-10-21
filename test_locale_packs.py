import json
import string
import unittest
from pathlib import Path


PACKS = (
    "en", "zh-CN", "nl", "fr", "de", "ja", "ko", "ru", "es",
    "sv", "bg", "th", "id", "el", "fil", "hi", "pl", "it",
    "ar", "vi", "uk", "no", "fi", "da", "hu", "ro", "cs", "pt-PT", "pt-BR", "tr",
    "zh-TW", "ms", "he", "bn", "ur", "fa", "sk", "hr", "sr", "ca", "et", "lv", "lt",
)
REQUIRED_TRANSLATED_KEYS = {
    "pane.checked", "convert.status_same_source", "convert.status_duplicate_output",
    "app.title", "menu.file", "menu.edit", "menu.view", "menu.tools", "menu.help",
    "menu.language", "menu.reminders", "menu.how_to", "menu.about",
    "toolbar.guide", "toolbar.refresh", "toolbar.move", "toolbar.copy", "toolbar.undo",
    "pane.left", "pane.right", "pane.preview", "pane.info", "pane.browse", "pane.drag", "pane.show",
    "pane.videos", "pane.images", "pane.find", "pane.subfolders", "pane.scanning", "pane.cancel",
    "common.system_default", "common.restart_required", "common.close", "common.save",
    "language.title", "language.message", "reminders.title", "reminders.rating", "reminders.support",
    "rating.title", "rating.body", "rating.rate", "rating.later", "rating.never",
    "support.title", "support.body", "support.open", "support.later", "support.never",
    "link.error_title", "link.error_body", "help.title", "help.search", "help.previous", "help.next"
    , "view.details", "view.thumbnails", "size.small", "size.medium", "size.large",
    "browse.continuous", "browse.paged", "browse.auto", "browse.per_page",
    "column.name", "column.codec", "column.resolution", "column.duration", "column.size",
    "column.rate", "column.fps", "column.modified", "column.type", "column.bitrate",
    "column.audio", "column.hdr", "column.pixels", "column.color", "column.tags", "column.rating",
    "status.ready", "status.scanning_progress", "status.scan_complete_folder",
    "status.scan_complete_subfolders", "status.unreadable", "status.from_cache",
    "status.scan_cancelled", "status.skipped_file", "status.scan_failed"
    , "filters.title", "filters.orientation", "filters.codec", "filters.tag",
    "filters.min_rating", "filters.color", "filters.min_width", "filters.max_width",
    "filters.min_height", "filters.max_height", "filters.min_size", "filters.max_size",
    "filters.min_duration", "filters.max_duration", "filters.date_from", "filters.date_to",
    "filters.any", "filters.landscape", "filters.portrait", "filters.square",
    "filters.unlabelled", "filters.clear", "filters.apply",
    "filters.rating_1", "filters.rating_2", "filters.rating_3", "filters.rating_4", "filters.rating_5"
    , "convert.preset_h264", "convert.preset_h265", "convert.preset_av1",
    "convert.preset_proxy", "convert.preset_remux", "convert.resolution_source",
    "convert.resolution_1080p", "convert.resolution_720p", "convert.engine_automatic",
    "convert.engine_software", "convert.status_ready", "convert.status_skipped",
    "convert.status_unknown_resolution", "convert.status_converting", "convert.status_passed",
    "convert.status_cancelled", "convert.status_failed",
    "choice.system", "choice.light", "choice.dark", "choice.high_contrast",
    "choice.selected", "choice.visible", "choice.all_scanned",
    "choice.copy", "choice.move", "choice.any", "choice.images", "choice.videos",
    "choice.quiet", "choice.balanced", "choice.fast"
}


def placeholders(value):
    return {name for _, name, _, _ in string.Formatter().parse(value) if name}


class LocalePackParityTests(unittest.TestCase):
    def test_all_supported_packs_have_required_keys_and_help_chapters(self):
        root = Path(__file__).parent / "locales"
        packs = {code: json.loads((root / f"{code}.json").read_text(encoding="utf-8")) for code in PACKS}
        english = packs["en"]
        english_strings = english["strings"]
        self.assertGreaterEqual(len(english_strings), 70)
        english_chapters = english["help"]["chapters"]
        self.assertGreaterEqual(len(english_chapters), 6)
        english_literals = english.get("literals", {})
        self.assertGreaterEqual(len(english_literals), 60)
        chapter_ids = [chapter["id"] for chapter in english_chapters]
        visible_menu_keys = {key for key in english_strings if key.startswith((
            "menu.", "context.", "sort.", "view.", "size.", "browse.", "column.",
            "status.", "outlier.", "inspector.", "preview.", "convert.", "duplicates.",
        ))}

        for code, pack in packs.items():
            with self.subTest(code=code):
                self.assertTrue(pack["meta"]["language"].strip())
                self.assertTrue(REQUIRED_TRANSLATED_KEYS.issubset(pack["strings"]))
                self.assertTrue(visible_menu_keys.issubset(pack["strings"]))
                self.assertEqual(set(pack["strings"]), set(english_strings))
                self.assertTrue(all(isinstance(value, str) and value.strip() for value in pack["strings"].values()))
                for key, translated_value in pack["strings"].items():
                    english_value = english_strings[key]
                    self.assertEqual(placeholders(translated_value), placeholders(english_value), key)
                chapters = pack["help"]["chapters"]
                self.assertEqual([chapter["id"] for chapter in chapters], chapter_ids)
                self.assertTrue(all(chapter["title"].strip() and chapter["body"].strip() for chapter in chapters))
                literals = pack.get("literals", {})
                self.assertEqual(set(literals), set(english_literals))
                for template, translated in literals.items():
                    self.assertTrue(translated.strip())
                    self.assertEqual(placeholders(translated), placeholders(template), template)


if __name__ == "__main__":
    unittest.main()
