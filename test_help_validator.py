import copy
import json
import re
from pathlib import Path
import tempfile
import unittest

from tools.validate_help import validate

ROOT=Path(__file__).parent

class HelpValidatorRegressionTests(unittest.TestCase):
    def test_language_subset_checks_only_requested_language(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); (root/"docs/help").mkdir(parents=True); (root/"locales").mkdir()
            (root/"docs/help/en.json").write_bytes((ROOT/"docs/help/en.json").read_bytes())
            (root/"locales/en.json").write_bytes((ROOT/"locales/en.json").read_bytes())
            report=validate(root,("en",))
            self.assertEqual(report["errors"],[])
            self.assertEqual([row["language"] for row in report["languages"]],["en"])

    def test_missing_empty_summary_english_links_and_rtl_fail_validation(self):
        english=json.loads((ROOT/"locales/en.json").read_text(encoding="utf-8"))
        french=json.loads((ROOT/"locales/fr.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); (root/"docs/help").mkdir(parents=True); (root/"locales").mkdir()
            (root/"docs/help/en.json").write_bytes((ROOT/"docs/help/en.json").read_bytes())
            (root/"locales/en.json").write_text(json.dumps(english),encoding="utf-8")
            mutations=("chapter","paragraph","empty","summary","english","links","rtl","steps")
            for mutation in mutations:
                with self.subTest(mutation=mutation):
                    pack=copy.deepcopy(french); chapter=pack["help"]["chapters"][0]
                    if mutation=="chapter": pack["help"]["chapters"].pop()
                    elif mutation=="paragraph": chapter["paragraphs"].pop()
                    elif mutation=="empty": chapter["paragraphs"][0]["text"]=""
                    elif mutation=="summary": chapter["paragraphs"][0]["text"]="Bref."
                    elif mutation=="english": chapter["paragraphs"][0]["text"]=english["help"]["chapters"][0]["paragraphs"][0]["text"]
                    elif mutation=="links": chapter["paragraphs"][0]["text"]+=" [chapter:does_not_exist]"
                    elif mutation=="rtl": chapter["paragraphs"][0]["text"]+="\u2067"
                    elif mutation=="steps": chapter["paragraphs"][0]["text"]=re.sub(r"(?m)^2\..*(?:\n|$)","",chapter["paragraphs"][0]["text"])
                    chapter["body"]="\n\n".join(p["text"] for p in chapter["paragraphs"])
                    (root/"locales/fr.json").write_text(json.dumps(pack),encoding="utf-8")
                    errors=validate(root,("en","fr"))["errors"]
                    expected={"chapter":"chapters","paragraph":"paragraphs","empty":"empty paragraph","summary":"short paragraph","english":"untranslated English","links":"broken chapter link","rtl":"unbalanced bidi","steps":"numbered instructions"}[mutation]
                    self.assertTrue(any(expected in error for error in errors),errors)

if __name__=="__main__":unittest.main()
