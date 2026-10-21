import unittest


class ResponsiveLayoutTests(unittest.TestCase):
    def test_combobox_width_fits_longest_translated_choice(self):
        from media_sorter import translated_combobox_width

        self.assertEqual(translated_combobox_width(("A", "Medium"), minimum=4), 8)
        self.assertEqual(translated_combobox_width(("short", "a much longer label"), minimum=4, maximum=12), 12)

    def test_filter_toolbar_uses_two_rows_to_protect_long_translations(self):
        from media_sorter import filter_toolbar_groups

        self.assertEqual(
            filter_toolbar_groups(),
            (("resolution", "matching", "advanced"), ("outliers", "sensitivity")),
        )


if __name__ == "__main__":
    unittest.main()
