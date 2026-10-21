import re
import unittest
from pathlib import Path


class LocalizedOptionControlTests(unittest.TestCase):
    def test_user_facing_combobox_choices_are_not_embedded_english_tuples(self):
        source = (Path(__file__).parent / "media_sorter.py").read_text(encoding="utf-8")
        forbidden = (
            '("System", "Light", "Dark", "High contrast")',
            '("Selected", "Visible", "All scanned")',
            '("Visible", "All scanned")',
            '("Copy", "Move")',
            '("Any", "Images", "Videos")',
            'tuple(PERFORMANCE_PROFILES)',
        )
        for value in forbidden:
            with self.subTest(value=value):
                self.assertNotIn(value, source)

    def test_conversion_choice_maps_cover_internal_values(self):
        from media_sorter import (
            TRANSCODE_AUTOMATIC,
            TRANSCODE_ENGINE_LABEL_KEYS,
            TRANSCODE_PRESETS,
            TRANSCODE_PRESET_LABEL_KEYS,
            TRANSCODE_RESOLUTIONS,
            TRANSCODE_RESOLUTION_LABEL_KEYS,
            TRANSCODE_SOFTWARE,
        )

        self.assertEqual(set(TRANSCODE_PRESET_LABEL_KEYS), set(TRANSCODE_PRESETS))
        self.assertEqual(set(TRANSCODE_RESOLUTION_LABEL_KEYS), set(TRANSCODE_RESOLUTIONS))
        self.assertTrue({TRANSCODE_AUTOMATIC, TRANSCODE_SOFTWARE}.issubset(TRANSCODE_ENGINE_LABEL_KEYS))


if __name__ == "__main__":
    unittest.main()
