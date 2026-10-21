"""Recoverable source exports must preserve versions and reject corruption."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools import project_snapshot as snapshots


class ProjectSnapshotTests(unittest.TestCase):
    def test_versioned_archive_manifest_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            source = base / "source"
            source.mkdir()
            (source / "VERSION.txt").write_text("12.6.1\n")
            (source / "module.py").write_text("VALUE = 43\n")
            destination = base / "source-12.6.1"
            with patch.object(snapshots, "ROOT", source), patch.object(snapshots, "source_files", return_value=["VERSION.txt", "module.py"]), patch.object(snapshots.subprocess, "check_output", return_value="test-head"):
                result = snapshots.snapshot(destination, archive=True)
                self.assertEqual(result["version"], "12.6.1")
                self.assertTrue((base / "source-12.6.1.zip").is_file())
                self.assertFalse((base / "source-12.6.zip").exists())
                self.assertEqual(snapshots.verify(destination), result)
                with self.assertRaises(FileExistsError):
                    snapshots.snapshot(destination)
                (destination / "module.py").write_text("corrupt")
                with self.assertRaisesRegex(ValueError, "module.py"):
                    snapshots.verify(destination)


if __name__ == "__main__":
    unittest.main()
