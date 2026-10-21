"""Translation-service whitespace loss must not merge labels or numbered steps."""
import unittest
from tools.align_help_terminology import restore_instruction_format
from tools.translate_help import unprotect


class HelpTranslationFormatTests(unittest.TestCase):
    def test_multi_modifier_shortcut_is_preserved_as_one_reference(self):
        from tools.translate_help import protect
        prepared,replacements=protect('Press Ctrl+Shift+N to create a folder.',{})
        self.assertIn('Ctrl+Shift+N',replacements.values())
        self.assertEqual(unprotect(prepared,replacements),'Press Ctrl+Shift+N to create a folder.')

    def test_glossary_replacement_does_not_join_neighbouring_words(self):
        self.assertEqual(unprotect("CliquerZXQKEEP00000QXZmaintenant",{"ZXQKEEP00000QXZ":"Démarrer…"}),"Cliquer Démarrer… maintenant")

    def test_latin_ui_boundaries_keep_natural_short_inflection_suffixes(self):
        text="WähleBilderoderVideos undDurchsuchen…jetzt. Ausgewählte Dateien."
        terms={"Images":"Bilder","Videos":"Videos","Browse":"Durchsuchen…","Selected":"Ausgewählt"}
        source="Choose Images, Videos, Browse and Selected."
        self.assertEqual(restore_instruction_format(text,source,terms),"Wähle Bilder oder Videos und Durchsuchen… jetzt. Ausgewählte Dateien.")

    def test_natural_latin_compounds_are_not_split(self):
        text="Mindestbewertungsbeschränkung und Vorschaumodus"
        self.assertEqual(restore_instruction_format(text,"Minimum rating and Preview",{"Minimum rating":"Mindestbewertung","Preview":"Vorschau"}),text)

    def test_restores_numbered_lines_without_changing_decimals_or_codecs(self):
        source="1. Choose a file.\n2. Set H.264 and 0.1%.\n3. Start."
        actual="1. Choisir.2. H.264 et 0.1%. 3. Démarrer."
        self.assertEqual(restore_instruction_format(actual,source,{}),
                         "1. Choisir.\n2. H.264 et 0.1%.\n3. Démarrer.")

    def test_separates_joined_rtl_ui_labels(self):
        source="Choose Tools and Clear unwanted ticks. Images are ignored."
        terms={"Tools":"أدوات", "Clear":"مسح", "Images":"صور"}
        text="اخترأدوات ثم مسحالعلامات. صورفي المجموعة."
        self.assertEqual(restore_instruction_format(text,source,terms),
                         "اختر أدوات ثم مسح العلامات. صور في المجموعة.")

    def test_does_not_add_missing_step_or_modify_unrelated_words(self):
        self.assertEqual(restore_instruction_format("1. Un seul.","1. One.\n2. Two.",{}),"1. Un seul.")
        self.assertEqual(restore_instruction_format("صورفي", "An unrelated sentence.", {"Images":"صور"}),"صورفي")

    def test_does_not_split_normal_arabic_words_or_generic_menu_nouns(self):
        text="افتح المجلد ثم الملفات في المجموعة."
        terms={"Open":"فتح", "File":"ملف", "Folder":"مجلد", "Group":"مجموعة"}
        self.assertEqual(restore_instruction_format(text,"Open the folder and files in the group.",terms),text)

    def test_step_detection_ignores_extension_digits_and_rating_ranges(self):
        source="1. Start.\n2. Choose .mp4.\n3. Set rating (0–3).\n4. Finish."
        value="1. A2. .mp4.3. (0–3).4. D"
        self.assertEqual(restore_instruction_format(value,source,{}),"1. A\n2. .mp4.\n3. (0–3).\n4. D")

    def test_preserves_localised_digits_while_restoring_lines(self):
        self.assertEqual(restore_instruction_format("১. A২. B", "1. A\n2. B",{}),"১. A\n২. B")

    def test_urdu_markers_and_missing_space_after_number(self):
        self.assertEqual(restore_instruction_format("1۔A2.B", "1. A\n2. B",{}),"1۔ A\n2. B")


if __name__=="__main__": unittest.main()
