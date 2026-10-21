"""Hidden-file enumeration must prune hidden folders without changing media."""
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
import media_sorter as m


class HiddenFilesTests(unittest.TestCase):
    def test_recursive_hidden_files_and_folders(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for name in ('visible.jpg','.hidden.jpg','visible/nested.jpg','.private/nested.jpg'):
                path=root/name;path.parent.mkdir(exist_ok=True);path.write_bytes(b'unchanged')
            names=lambda shown:{p.relative_to(root).as_posix() for p in m.iter_browser_files(root,True,shown)}
            self.assertEqual(names(False),{'visible.jpg','visible/nested.jpg'})
            self.assertEqual(names(True),{'visible.jpg','.hidden.jpg','visible/nested.jpg','.private/nested.jpg'})
            self.assertTrue(all(p.read_bytes()==b'unchanged' for p in root.rglob('*.jpg')))

    def test_non_recursive_and_explicit_hidden_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'.explicit';root.mkdir()
            (root/'visible.jpg').write_bytes(b'x');(root/'.hidden.jpg').write_bytes(b'x')
            self.assertEqual({p.name for p in m.iter_browser_files(root,False,False)},{'visible.jpg'})

    def test_windows_hidden_attribute(self):
        path=Mock(name='normal_name');path.name='normal.jpg'
        path.stat.return_value=SimpleNamespace(st_file_attributes=2)
        self.assertTrue(m.is_hidden_path(path))
        path.stat.return_value=SimpleNamespace(st_file_attributes=32)
        self.assertFalse(m.is_hidden_path(path))


if __name__=='__main__':unittest.main()
