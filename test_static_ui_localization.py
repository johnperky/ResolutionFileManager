import json
import unittest
from pathlib import Path

from localization import Translator
from media_sorter import LocalizedFileDialog, LocalizedSimpleDialog
from tools.sync_static_ui_literals import static_ui_literals


class DummyDialogs:
    def askstring(self, title, prompt, *args, **kwargs):
        return title, prompt, args, kwargs

    def askopenfilename(self, *args, **kwargs):
        return args, kwargs


class StaticUiLocalizationTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parent
        self.translator = Translator(self.root / "locales", "de")

    def test_every_static_widget_label_is_catalogued(self):
        english = json.loads((self.root / "locales" / "en.json").read_text(encoding="utf-8"))
        discovered = static_ui_literals((self.root / "media_sorter.py").read_text(encoding="utf-8"))
        self.assertTrue(discovered.issubset(english["literals"]))

    def test_standard_input_dialog_translates_title_and_prompt(self):
        dialogs = LocalizedSimpleDialog(DummyDialogs(), self.translator)
        title, prompt, _args, _kwargs = dialogs.askstring("Rename file", "New filename:")
        self.assertNotEqual(title, "Rename file")
        self.assertNotEqual(prompt, "New filename:")

    def test_file_dialog_translates_title_keyword(self):
        dialogs = LocalizedFileDialog(DummyDialogs(), self.translator)
        _args, kwargs = dialogs.askopenfilename(title="Export integrity report")
        self.assertNotEqual(kwargs["title"], "Export integrity report")


if __name__ == "__main__":
    unittest.main()
