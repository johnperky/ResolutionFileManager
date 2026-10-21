import tempfile
import unittest
from pathlib import Path


class PackagingAssetTests(unittest.TestCase):
    def test_validator_accepts_complete_locale_directory(self):
        from verify_release_assets import REQUIRED_LOCALES, validate_release_assets

        self.assertEqual(REQUIRED_LOCALES, (
            "en", "zh-CN", "nl", "fr", "de", "ja", "ko", "ru", "es",
            "sv", "bg", "th", "id", "el", "fil", "hi", "pl",
            "it",
            "ar", "vi", "uk", "no", "fi", "da", "hu", "ro", "cs", "pt-PT", "pt-BR", "tr",
            "zh-TW", "ms", "he", "bn", "ur", "fa", "sk", "hr", "sr", "ca", "et", "lv", "lt",
        ))

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            locale_dir = root / "locales"
            locale_dir.mkdir()
            for code in (
                "en", "zh-CN", "nl", "fr", "de", "ja", "ko", "ru", "es",
                "sv", "bg", "th", "id", "el", "fil", "hi", "pl",
                "it",
                "ar", "vi", "uk", "no", "fi", "da", "hu", "ro", "cs", "pt-PT", "pt-BR", "tr",
                "zh-TW", "ms", "he", "bn", "ur", "fa", "sk", "hr", "sr", "ca", "et", "lv", "lt",
            ):
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
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        self.assertEqual(media_sorter.APP_VERSION, version)
        self.assertTrue((root / f"RELEASE_NOTES_{version}.md").is_file())

    def test_store_manifest_declares_italian(self):
        manifest = (Path(__file__).parent / "packaging" / "microsoft-store" / "AppxManifest.template.xml").read_text(
            encoding="utf-8"
        )
        self.assertIn('<Resource Language="it-it" />', manifest)

    def test_store_manifest_declares_12_6_language_expansion(self):
        manifest = (Path(__file__).parent / "packaging" / "microsoft-store" / "AppxManifest.template.xml").read_text(
            encoding="utf-8"
        )
        for language in (
            "ar-sa", "vi-vn", "uk-ua", "nb-no", "fi-fi", "da-dk", "hu-hu", "ro-ro",
            "cs-cz", "pt-pt", "pt-br", "tr-tr", "zh-tw", "ms-my", "he-il", "bn-bd", "ur-pk",
            "fa-ir", "sk-sk", "hr-hr", "sr-cyrl-rs", "ca-es", "et-ee", "lv-lv", "lt-lt",
        ):
            with self.subTest(language=language):
                self.assertIn(f'<Resource Language="{language}" />', manifest)

    def test_store_builder_rejects_an_executable_older_than_release_sources(self):
        from verify_release_assets import validate_store_executable

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            executable = root / "ResolutionFileManager.exe"
            source = root / "media_sorter.py"
            executable.write_bytes(b"old executable")
            source.write_text('APP_VERSION = "12.4.0"', encoding="utf-8")
            executable.touch()
            source.touch()
            executable_time = executable.stat().st_mtime
            source_time = executable_time + 10
            import os

            os.utime(source, (source_time, source_time))

            with self.assertRaisesRegex(ValueError, "older than release source"):
                validate_store_executable(root, executable)

    def test_store_builder_uses_the_project_release_version(self):
        script = (Path(__file__).parent / "packaging" / "microsoft-store" / "Build-StorePackage.ps1").read_text(
            encoding="utf-8"
        )
        self.assertIn("VERSION.txt", script)
        self.assertNotIn('[string] $Version = "12.3.0.0"', script)


if __name__ == "__main__":
    unittest.main()
