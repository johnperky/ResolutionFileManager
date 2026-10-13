import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class AppIntegrationHelperTests(unittest.TestCase):
    def test_resource_directory_uses_source_and_pyinstaller_roots(self):
        import media_sorter

        source = media_sorter.bundled_resource("locales")
        self.assertEqual(source, Path(media_sorter.__file__).parent / "locales")
        with tempfile.TemporaryDirectory() as folder, patch.object(media_sorter.sys, "_MEIPASS", folder, create=True):
            self.assertEqual(media_sorter.bundled_resource("locales"), Path(folder) / "locales")

    def test_merge_settings_preserves_unrelated_existing_values(self):
        from media_sorter import merge_application_settings

        original = {"geometry": "1000x700", "left": {"path": "A"}, "custom": 42}
        merged = merge_application_settings(original, {"geometry": "1200x800", "language": "de"}, {"launch_count": 7})
        self.assertEqual(merged["geometry"], "1200x800")
        self.assertEqual(merged["left"], {"path": "A"})
        self.assertEqual(merged["custom"], 42)
        self.assertEqual(merged["language"], "de")
        self.assertEqual(merged["reminders"], {"launch_count": 7})
        self.assertEqual(original["geometry"], "1000x700")

    def test_store_destinations_use_official_product_id(self):
        from media_sorter import microsoft_store_destinations

        self.assertEqual(microsoft_store_destinations(), (
            "ms-windows-store://pdp/?productid=9NZL6GF5JSJK",
            "https://apps.microsoft.com/detail/9NZL6GF5JSJK",
        ))


if __name__ == "__main__":
    unittest.main()
