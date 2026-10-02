import unittest
from pathlib import Path
from types import SimpleNamespace

from media_sorter import FilePane, MediaItem


def item(name: str) -> MediaItem:
    return MediaItem(Path(name), 1920, 1080, 100, 1.0)


class FakeTree:
    def __init__(self, rows=(), selected=()):
        self.rows = dict(rows)
        self.selected = tuple(selected)
        self.text = {}

    def selection(self):
        return self.selected

    def item(self, iid, option=None, **kwargs):
        if "text" in kwargs:
            self.text[iid] = kwargs["text"]
        if option == "tags":
            return (self.rows[iid],)
        return {"tags": (self.rows[iid],), "text": self.text.get(iid, "")}

    def get_children(self):
        return tuple(self.rows)

    def exists(self, iid):
        return iid in self.rows


class TickSelectionTests(unittest.TestCase):
    def make_pane(self):
        first, second, hidden = item("first.mp4"), item("second.mp4"), item("hidden.mp4")
        pane = SimpleNamespace(
            items={str(value.path): value for value in (first, second, hidden)},
            visible_items=[first, second],
            checked_paths=set(),
            tree=FakeTree((("row-0", str(first.path)), ("row-1", str(second.path))), ("row-1",)),
            path_to_iid={str(first.path): "row-0", str(second.path): "row-1"},
            update_checked_label=lambda: None,
            update_thumbnail_selection=lambda: None,
        )
        pane.highlighted_items = lambda: FilePane.highlighted_items(pane)
        pane.refresh_checks = lambda: FilePane.refresh_checks(pane)
        return pane, first, second, hidden

    def test_highlight_is_used_when_no_files_are_ticked(self):
        pane, _first, second, _hidden = self.make_pane()
        self.assertEqual(FilePane.selected_items(pane), [second])

    def test_ticks_override_highlight_and_include_hidden_filtered_files(self):
        pane, first, _second, hidden = self.make_pane()
        pane.checked_paths.update((str(first.path), str(hidden.path)))
        self.assertEqual(FilePane.selected_items(pane), [first, hidden])

    def test_toggle_all_affects_only_visible_files(self):
        pane, first, second, hidden = self.make_pane()
        pane.checked_paths.add(str(hidden.path))
        FilePane.toggle_all_checks(pane)
        self.assertEqual(pane.checked_paths, {str(first.path), str(second.path), str(hidden.path)})
        FilePane.toggle_all_checks(pane)
        self.assertEqual(pane.checked_paths, {str(hidden.path)})

    def test_removed_files_are_also_removed_from_ticks(self):
        pane, first, _second, hidden = self.make_pane()
        pane.checked_paths.update((str(first.path), str(hidden.path)))
        self.assertTrue(FilePane.remove_known_paths(pane, [first.path]))
        self.assertEqual(pane.checked_paths, {str(hidden.path)})


if __name__ == "__main__":
    unittest.main()
