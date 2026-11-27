import tkinter as tk
import unittest
from pathlib import Path
from types import SimpleNamespace

import conversion_ui as ui


class UsabilityTests(unittest.TestCase):
    def test_remembered_choices_are_separate_and_validated(self):
        app = tk.Tcl()
        app.settings = {}
        app.save_local_preferences = lambda: None
        effect = tk.BooleanVar(master=app, value=False)
        ui.remember_conversion_choice(app, 'video_denoise', effect, (True, False))
        effect.set(True)
        reopened = tk.BooleanVar(master=app, value=False)
        ui.remember_conversion_choice(app, 'video_denoise', reopened, (True, False))
        self.assertTrue(reopened.get())
        image = tk.BooleanVar(master=app, value=False)
        ui.remember_conversion_choice(app, 'image_denoise', image, (True, False))
        self.assertFalse(image.get())
        app.settings['bad'] = 'not valid'
        mode = tk.StringVar(master=app, value='ordinary')
        ui.remember_conversion_choice(app, 'bad', mode, ('ordinary', 'fast'))
        self.assertEqual(mode.get(), 'ordinary')

    def test_counts_include_hidden_files_and_folders(self):
        paths = {str(Path('a/one.mp4')), str(Path('b/two.mp4'))}
        counts = ui.checked_counts(paths, [SimpleNamespace(path=Path('a/one.mp4'))])
        self.assertEqual(counts, (2, 2, 1))

    def test_eta_needs_real_progress(self):
        self.assertIsNone(ui.remaining_seconds(0, 10))
        self.assertIsNone(ui.remaining_seconds(.25, .5))
        self.assertAlmostEqual(ui.remaining_seconds(.25, 10), 30)
        self.assertEqual(ui.remaining_seconds(1, 10), 0)


if __name__ == '__main__':
    unittest.main()
