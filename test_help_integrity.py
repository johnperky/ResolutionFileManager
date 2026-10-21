import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest

from tools.validate_help import validate

ROOT=Path(__file__).parent

class FullHelpTests(unittest.TestCase):
    def test_short_summary_cannot_override_full_english(self):
        from localization import Translator
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            en={"strings":{},"help":{"schema":2,"master_sha256":"verified","chapters":[{
                "id":"manual","title":"Manual","body":"Full paragraph one.\n\nFull paragraph two.",
                "paragraphs":[{"id":"p1","text":"Full paragraph one."},{"id":"p2","text":"Full paragraph two."}]}]}}
            de={"strings":{},"help":{"chapters":[{"id":"manual","title":"Kurz","body":"Short summary."}]}}
            (root/"en.json").write_text(json.dumps(en),encoding="utf-8")
            (root/"de.json").write_text(json.dumps(de),encoding="utf-8")
            translator=Translator(root,"de")
            self.assertEqual(translator.help_chapters(),[("Manual","Full paragraph one.\n\nFull paragraph two.")])
            self.assertTrue(translator.diagnostics)

    def test_full_historical_guide_archive_is_preserved(self):
        raw=(ROOT/"docs/help/en.json").read_text(encoding="utf-8")
        master=json.loads(raw)
        original=(ROOT/"docs/help/recovered-12.3.0-en.txt").read_text(encoding="utf-8")
        self.assertEqual(hashlib.sha256(original.encode()).hexdigest(),master["source_guide_sha256"])
        titles=list(re.finditer(r"(?m)^([A-Z][A-Z /&-]{2,})$",original))
        self.assertEqual(len(titles),15)
        # The archive is immutable provenance. The user-approved live manual
        # deliberately removes developer/legal chapters and reorders others.
        # Its completeness is checked against the current master, not 12.3.0.

    def test_master_and_every_language_pass_completeness_validation(self):
        self.assertEqual(validate()["errors"],[])

    def test_smart_collections_explains_limits_and_exact_functions(self):
        master=json.loads((ROOT/"docs/help/en.json").read_text(encoding="utf-8"))
        body=next(c["body"] for c in master["chapters"] if c["id"]=="smart_collections")
        for text in ("Save active smart collection", "Manage smart collections", "Save current", "Undo delete", "one starting folder", "pixel area", "original media", "Minimum width (pixels)"):
            self.assertIn(text,body)
        self.assertGreater(len(body),6500)

if __name__=="__main__":unittest.main()
