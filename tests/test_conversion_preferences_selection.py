import tkinter as tk
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import conversion_ui as ui


class ConversionPreferencesTests(unittest.TestCase):
    def test_defaults_and_valid_quality_survive_reopening(self):
        app = tk.Tcl()
        app.settings = {}
        app.save_local_preferences = lambda: None
        quality = ui.video_quality_choice(app)
        self.assertEqual(quality.get(), 25)
        quality.set(29)
        quality.set('')  # A partially edited spinbox must not erase the preference.
        self.assertEqual(ui.video_quality_choice(app).get(), 29)
        folder = ui.source_folder_choice(app, 'video')
        self.assertTrue(folder.get())
        folder.set(False)
        self.assertFalse(ui.source_folder_choice(app, 'video').get())

    def test_conflicting_groups_choose_either_or_cancel(self):
        old = SimpleNamespace(path=Path('old.mp4'))
        new = SimpleNamespace(path=Path('new.mp4'))
        pane = SimpleNamespace(selected_items=lambda: [old], highlighted_items=lambda: [new])
        for answer, expected in ((True, [old]), (False, [new]), (None, None)):
            with patch.object(ui.messagebox, 'askyesnocancel', return_value=answer) as prompt:
                self.assertEqual(ui.conversion_items(None, pane, {'.mp4'}), expected)
                prompt.assert_called_once()
        pane.highlighted_items = lambda: [old]
        with patch.object(ui.messagebox, 'askyesnocancel') as prompt:
            self.assertEqual(ui.conversion_items(None, pane, {'.mp4'}), [old])
            prompt.assert_not_called()

    def test_preset_default_and_remembered_choice(self):
        app = tk.Tcl()
        app.settings = {}
        app.save_local_preferences = lambda: None
        choices = SimpleNamespace(mapping={'Keep source H.265 MKV (smaller)': 'Source H265 MKV', '720p H.264 MP4 (compatible)': '720 MP4'})
        choices.label = choices.mapping.get
        choices.internal = lambda label: {v:k for k,v in choices.mapping.items()}.get(label)
        choices.labels = tuple(choices.mapping.values())
        preset = ui.video_preset_choice(app, choices)
        self.assertEqual(preset.get(), 'Source H265 MKV')
        preset.set('720 MP4')
        self.assertEqual(ui.video_preset_choice(app, choices).get(), '720 MP4')


if __name__ == '__main__':
    unittest.main()
