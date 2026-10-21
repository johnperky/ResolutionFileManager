"""Validate complete Help; structural errors fail, linguistic flags require review."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from localization import RTL_LANGUAGES, SUPPORTED_LANGUAGES

def validate(root=ROOT, languages=None):
    raw=(root/"docs/help/en.json").read_text(encoding="utf-8")
    master=json.loads(raw)
    expected_hash=hashlib.sha256(raw.encode()).hexdigest()
    source=master["chapters"]
    ids=[c["id"] for c in source]
    selected_languages=languages or SUPPORTED_LANGUAGES
    errors=[]; warnings=[]; languages=[]
    for code in selected_languages:
        path=root/"locales"/f"{code}.json"
        try: help_data=json.loads(path.read_text(encoding="utf-8"))["help"]
        except (OSError,ValueError,KeyError) as error:
            errors.append(f"{code}: unreadable Help: {error}"); continue
        chapters=help_data.get("chapters",[])
        if [c.get("id") for c in chapters]!=ids:
            errors.append(f"{code}: missing/reordered chapters"); continue
        if help_data.get("master_sha256")!=expected_hash: errors.append(f"{code}: stale master hash")
        direction="rtl" if code in RTL_LANGUAGES else "ltr"
        if help_data.get("direction")!=direction: errors.append(f"{code}: wrong text direction")
        count=0
        for original,chapter in zip(source,chapters):
            label=f"{code}/{original['id']}"
            paragraphs=chapter.get("paragraphs",[])
            if not str(chapter.get("title","")).strip(): errors.append(f"{label}: empty title")
            if code=="en" and chapter.get("title")!=original["title"]: errors.append(f"{label}: English title differs from master")
            if [p.get("id") for p in paragraphs]!=[p["id"] for p in original["paragraphs"]]:
                errors.append(f"{label}: missing/reordered paragraphs"); continue
            if chapter.get("body")!="\n\n".join(p.get("text","") for p in paragraphs): errors.append(f"{label}: body/paragraph mismatch")
            for op,p in zip(original["paragraphs"],paragraphs):
                value=p.get("text",""); baseline=op["text"]
                name=f"{code}/{p['id']}"
                if not value.strip(): errors.append(f"{name}: empty paragraph"); continue
                if code=="en" and value!=baseline: errors.append(f"{name}: English paragraph differs from master")
                if code!="en" and p.get("source_sha256")!=hashlib.sha256(baseline.encode()).hexdigest(): errors.append(f"{name}: stale paragraph source")
                if code!="en" and value==baseline and len(baseline)>90 and not baseline.startswith("http"):
                    errors.append(f"{name}: untranslated English paragraph")
                source_steps=[int(n) for n in re.findall(r"(?m)^\s*(\d+)[.)]\s",baseline)]
                translated_steps=[int(n) for n in re.findall(r"(?m)^\s*(\d+)[.۔)]\s",value)]
                if len(source_steps)>1 and translated_steps!=source_steps:
                    errors.append(f"{name}: missing/reordered numbered instructions")
                minimum=.18 if code in {"zh-CN","zh-TW","ja","ko","th"} else .32
                if len(baseline)>160 and len(value)<len(baseline)*minimum: errors.append(f"{name}: suspiciously short paragraph")
                links=re.findall(r"\[chapter:([^]]+)\]",value)
                if links!=re.findall(r"\[chapter:([^]]+)\]",baseline): errors.append(f"{name}: changed links")
                if any(link not in ids for link in links): errors.append(f"{name}: broken chapter link")
                references=re.findall(r"Ctrl(?:\+(?:Shift|Alt))*\+[A-Za-z]|\bF[235]\b|\{[A-Za-z_][A-Za-z_0-9]*\}|https?://[^\s]+|[A-Za-z_][A-Za-z_0-9.-]*\.(?:py|json|ps1|sh|txt|md|exe)",baseline)
                missing_refs=[reference for reference in references if reference not in value]
                if missing_refs: errors.append(f"{name}: missing technical references: {missing_refs}")
                for marker in ("ZXQKEEP","RFMSEP"):
                    if marker in value.upper(): errors.append(f"{name}: unresolved translation marker")
                if re.search(r"</?(?:span|div|br|p)\b",value,re.I) or value.lstrip().startswith(('{"Translation"','```')):
                    errors.append(f"{name}: unexpected translation markup/wrapper")
                if value.count("\u2066")+value.count("\u2067")+value.count("\u2068")!=value.count("\u2069"): errors.append(f"{name}: unbalanced bidi isolation")
                if value.count("\u202a")+value.count("\u202b")!=value.count("\u202c"): errors.append(f"{name}: unbalanced bidi embedding")
                if any(c in value for c in ("\u202d","\u202e")): errors.append(f"{name}: bidi override")
                if code in RTL_LANGUAGES and len(value)>90 and not re.search(r"[\u0590-\u08ff]",value): errors.append(f"{name}: no RTL-script content")
                # Long English residue is a review flag; protected file paths,
                # shortcuts, product names and translated UI terms are legitimate.
                if code!="en" and len(baseline)>200:
                    words=re.findall(r"[A-Za-z]{3,}",baseline)
                    for start in range(max(0,len(words)-11)):
                        phrase=" ".join(words[start:start+12])
                        if phrase.casefold() in " ".join(re.findall(r"[A-Za-z]{3,}",value)).casefold():
                            warnings.append(f"{name}: review English residue: {phrase}"); break
                count+=1
        languages.append({"language":code,"chapters":len(chapters),"paragraphs":count,"direction":direction})
    return {"master_sha256":expected_hash,"languages":languages,"errors":errors,"review_warnings":warnings}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--report"); args=parser.parse_args()
    result=validate()
    if args.report: Path(args.report).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Help: {len(result['languages'])} languages; {len(result['errors'])} errors; {len(result['review_warnings'])} review flags")
    for entry in result["errors"]: print(entry)
    if result["errors"]: raise SystemExit(1)

if __name__=="__main__": main()
