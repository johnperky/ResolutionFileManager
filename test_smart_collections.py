import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from media_sorter import MediaSorterApp, FilePane, MediaItem

class Variable:
    def __init__(self,value): self.value=value
    def get(self): return self.value
    def set(self,value): self.value=value

def pane(path):
    p=SimpleNamespace(current_path=path,recursive_var=Variable(True),show_videos_var=Variable(False),
        show_images_var=Variable(True),search_var=Variable("holiday"),filter_var=Variable("All"),
        advanced_filters={"min_width":"1000"},sort_column="resolution",sort_reverse=True,
        view_mode_var=Variable("Thumbnails"),thumbnail_size_var=Variable("Large"),thumbnail_browse_mode="Continuous",
        thumbnail_browse_mode_var=Variable("Continuous"),tree={"columns":("name","resolution")},
        update_sort_label=lambda:None)
    p.set_view_mode=lambda value:p.view_mode_var.set(value)
    def navigate(path): p.current_path=path; p.navigated=True; return True
    p.navigate=navigate
    return p

class SmartCollectionTests(unittest.TestCase):
    def test_save_apply_edit_rename_delete_restore_without_touching_media(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); media=root/"holiday.jpg"; media.write_bytes(b"original media")
            active=pane(root)
            app=SimpleNamespace(smart_collections={},smart_collections_path=root/"smart_collections.json",
                current_pane=lambda:active,smart_collection_state=MediaSorterApp.smart_collection_state)
            self.assertTrue(MediaSorterApp.save_smart_collection(app,"Images by resolution"))
            saved=json.loads(app.smart_collections_path.read_text())
            self.assertEqual(saved["Images by resolution"]["sort_column"],"resolution")
            self.assertTrue(saved["Images by resolution"]["recursive"])
            self.assertNotIn("checked_paths",saved["Images by resolution"])
            target=pane(root); target.search_var.set("wrong")
            self.assertTrue(MediaSorterApp.apply_smart_collection(app,"Images by resolution",target))
            self.assertEqual(target.search_var.get(),"holiday")
            self.assertEqual(target.advanced_filters,{"min_width":"1000"})
            self.assertEqual(target.sort_column,"resolution")
            self.assertTrue(target.sort_reverse)
            active.search_var.set("updated")
            with patch("media_sorter.messagebox.askyesno",return_value=True):
                self.assertTrue(MediaSorterApp.save_smart_collection(app,"Images by resolution"))
            self.assertTrue(MediaSorterApp.rename_smart_collection(app,"Images by resolution","Renamed"))
            state=MediaSorterApp.delete_smart_collection(app,"Renamed")
            self.assertNotIn("Renamed",app.smart_collections)
            self.assertTrue(MediaSorterApp.restore_smart_collection(app,"Renamed",state))
            self.assertEqual(app.smart_collections["Renamed"]["search"],"updated")
            self.assertEqual(media.read_bytes(),b"original media")

    def test_missing_root_does_not_navigate_or_apply_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            target=pane(Path(folder))
            app=SimpleNamespace(smart_collections={"gone":{"path":str(Path(folder)/"missing")}},current_pane=lambda:target)
            with patch("media_sorter.messagebox.showerror"):
                self.assertFalse(MediaSorterApp.apply_smart_collection(app,"gone"))
            self.assertFalse(hasattr(target,"navigated"))

if __name__=="__main__": unittest.main()
