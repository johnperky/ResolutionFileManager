"""Catch English-only labels in dynamically populated file information."""
import unittest
from pathlib import Path
from types import SimpleNamespace
import tkinter as tk
from localization import Translator, SUPPORTED_LANGUAGES
from media_sorter import FilePane, MediaItem


class InspectorLocalizationTests(unittest.TestCase):
    def test_populated_inspector_uses_current_language_and_preserves_metadata(self):
        root=tk.Tcl()
        item=MediaItem(path=Path('E:/sample.mp4'),size=1048576,modified=0,
                       width=1920,height=1080,duration=10,codec='H.264')
        for code in SUPPORTED_LANGUAGES:
            translator=Translator(Path(__file__).parent/'locales',code)
            pane=SimpleNamespace(tr=translator.text,
                inspector_name_var=tk.StringVar(master=root),
                inspector_path_var=tk.StringVar(master=root),
                inspector_details_var=tk.StringVar(master=root))
            FilePane.update_inspector(pane,item)
            text=pane.inspector_details_var.get()
            with self.subTest(language=code):
                self.assertIn(translator.text('column.type')+': MP4',text)
                self.assertIn(translator.text('column.resolution')+': 1920 × 1080',text)
                self.assertIn(translator.text('inspector.unrated'),text)
                self.assertIn('H.264',text)
                if code=='ar':
                    self.assertNotIn('Type:',text)
                    self.assertNotIn('Frame rate:',text)
                    self.assertNotIn('Colour label:',text)

if __name__=='__main__':unittest.main()
