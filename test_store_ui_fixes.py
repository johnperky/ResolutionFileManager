"""Regressions for visible issues found during genuine Store captures."""
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from types import SimpleNamespace

from localization import LocalizedChoices, Translator
from media_sorter import FilePane, MediaItem, MediaSorterApp, TRANSCODE_STATUS_LABEL_KEYS

ROOT=Path(__file__).parent

class StoreUiFixTests(unittest.TestCase):
    def test_tick_counter_uses_existing_language_and_updates_count(self):
        master=tk.Tcl()
        pane=SimpleNamespace(tr=Translator(ROOT/'locales','it').text,
            checked_paths=set(),checked_label_var=tk.StringVar(master=master))
        FilePane.update_checked_label(pane)
        self.assertEqual(pane.checked_label_var.get(),'0 selezionati')
        pane.checked_paths.update(('first','second','hidden'))
        FilePane.update_checked_label(pane)
        self.assertEqual(pane.checked_label_var.get(),'3 selezionati')

    def test_actual_conversion_collision_is_localized_without_changing_plan(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            items=[MediaItem(root/f'clip.{ext}',1920,1080,100,1.0) for ext in ('mp4','webm')]
            plans=MediaSorterApp.plan_video_conversions(items,'H.264 MP4 (compatible)',root/'out',root,True,'Skip existing','Keep source resolution')
            self.assertEqual([p['status'] for p in plans],['Ready','Duplicate output'])
            labels=LocalizedChoices(Translator(ROOT/'locales','it'),TRANSCODE_STATUS_LABEL_KEYS)
            self.assertEqual(labels.label(plans[1]['status']),'Nome di output duplicato')
            self.assertEqual(labels.internal('Nome di output duplicato'),'Duplicate output')

    def test_preview_existing_and_same_source_statuses_are_localized(self):
        labels=LocalizedChoices(Translator(ROOT/'locales','it'),TRANSCODE_STATUS_LABEL_KEYS)
        self.assertEqual(labels.label('Skip existing'),'Salta esistenti')
        self.assertEqual(labels.label('Same as source'),'Uguale al file sorgente')

    def test_heading_width_adapts_once_but_keeps_same_language_custom_resize(self):
        from media_sorter import localized_column_width
        self.assertEqual(localized_column_width(85,None,140,False),164)
        self.assertEqual(localized_column_width(85,90,140,False),164)
        self.assertEqual(localized_column_width(85,60,140,True),60)
        self.assertEqual(localized_column_width(85,300,140,False),300)
        self.assertEqual(localized_column_width(85,'bad',140,True),164)

if __name__=='__main__':unittest.main()
