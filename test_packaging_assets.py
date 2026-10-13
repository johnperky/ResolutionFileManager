import tempfile
import unittest
from pathlib import Path


class PackagingAssetTests(unittest.TestCase):
    def test_validator_accepts_complete_locale_directory(self):
        from verify_release_assets import validate_release_assets

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            locale_dir = root / "locales"
            locale_dir.mkdir()
            for code in ("en", "zh-CN", "nl", "fr", "de", "ja", "ko", "ru", "es"):
                (locale_dir / f"{code}.json").write_text("{}", encoding="utf-8")
            self.assertEqual(validate_release_assets(root), locale_dir)

    def test_validator_reports_every_missing_pack(self):
        from verify_release_assets import validate_release_assets

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "locales").mkdir()
            (root / "locales" / "en.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(FileNotFoundError, "zh-CN.json.*de.json"):
                validate_release_assets(root)

    def test_release_version_is_consistent(self):
        import media_sorter

        root = Path(__file__).parent
        version = (root / "VERSION.txt").read_text(encoding="utf-8").strip()
        self.assertEqual(version, "12.4.0")
        self.assertEqual(media_sorter.APP_VERSION, version)
        self.assertTrue((root / "RELEASE_NOTES_12.4.0.md").is_file())


if __name__ == "__main__":
    unittest.main()
