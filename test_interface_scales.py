"""Platform-specific choices must also reject stale saved scales."""
import unittest
import media_sorter as m


class InterfaceScaleTests(unittest.TestCase):
    def test_linux_choices_stop_at_150(self):
        self.assertEqual(m.interface_scales("linux"), (100, 125, 150))

    def test_windows_choices_stop_at_150(self):
        self.assertEqual(m.interface_scales("win32"), (100, 125, 150))


if __name__ == "__main__":
    unittest.main()
