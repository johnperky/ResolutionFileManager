"""Platform-specific choices must also reject stale saved scales."""
import unittest
import media_sorter as m


class InterfaceScaleTests(unittest.TestCase):
    def test_linux_has_no_200_percent_choice(self):
        self.assertEqual(m.interface_scales("linux"), (100, 125, 150, 175))

    def test_windows_retains_existing_choices(self):
        self.assertEqual(m.interface_scales("win32"), (100, 125, 150, 175, 200))


if __name__ == "__main__":
    unittest.main()
