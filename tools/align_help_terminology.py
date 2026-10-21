"""Align residual English UI labels with each existing interface dictionary."""
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]

def restore_instruction_format(value,source,terms):
    for symbol,damaged in (("↑","Ôåæ"),("↓","Ôåô")):
        if symbol in source: value=value.replace(damaged,symbol)
    expected=[int(n) for n in re.findall(r"(?m)^\s*([1-9]\d*)[.)]\s",source)]
    if len(expected)>1:
        protected=[m.span() for m in re.finditer(r"\b(?:mp4|mkv|webm|avi|mov|jpe?g|png|json|py|ps1|txt|md|exe)\b|(?<!\w)\d+(?:\.\d+)+",value,re.I)]
        steps=[m for m in re.finditer(r"(?<!\d)(\d+)[.۔](?!\d)",value)
               if int(m.group(1)) in expected and not any(a<=m.start()<b for a,b in protected)]
        if [int(m.group(1)) for m in steps]==expected:
            for match in reversed(steps):
                prefix=value[:match.start()].rstrip(" \t")
                suffix=value[match.end():]
                value=prefix+("\n" if prefix and not prefix.endswith("\n") else "")+value[match.start():match.end()]+(" " if suffix and not suffix[0].isspace() else "")+suffix
    # Translation services sometimes consume whitespace next to glossary
    # placeholders. Restore boundaries only for expected script-specific UI
    # labels, not arbitrary translated words or CJK prose.
    labels=sorted({target for label,target in terms.items()
                   if len(target)>=3 and label in source and label not in {"Open","File","Folder","Group"}
                   and not re.search(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]",target)
                   and re.search(r"(?<!\w)"+re.escape(label)+r"(?!\w)",source)},key=len,reverse=True)
    if labels:
        pattern=re.compile("|".join(re.escape(label) for label in labels))
        def separate(match):
            left=match.start()>0 and value[match.start()-1].isalpha() and match.group()[0].isalpha()
            right=match.end()<len(value) and value[match.end()].isalpha()
            suffix=re.match(r"[^\W\d_]+",value[match.end():])
            if right and not re.search(r"[\u0590-\u0dff]",match.group()) and match.group()[-1].isalnum():
                # Keep native short inflections (e.g. Ausgewählt + e), but
                # separate a following word or another capitalised UI label.
                connectors={"and","or","und","oder","mit","zur","zum","falls","wenn","et","ou","avec","pour","dans","si","y","o","con","para","de","en","e","com","se","di","per","ed","och","eller","med","til","og","i","om","hvis","of","met","voor","als","a","nebo","pak","gdy","oraz","czy","és","vagy","ha","dacă","și","sau","cu","in","to","for","the","then","is","are"}
                verbs={"Add","Edit","Delete","Apply","Start","Save","Rename","Copy","Move","Cancel","Pause","Resume","Retry failed","Clear","Close","Save rule"}
                # A long lowercase suffix may be a genuine compound, not a
                # lost space (Mindestbewertung + sbeschränkung, for example).
                labels_here={label for label,target in terms.items() if target==match.group()}
                right=bool(suffix and (not suffix.group().islower() or (len(suffix.group())>2 and (suffix.group() in connectors or labels_here & verbs))))
            return (" " if left else "")+match.group()+(" " if right else "")
        value=pattern.sub(separate,value)
    return value

def main():
    english=json.loads((ROOT/"locales/en.json").read_text(encoding="utf-8"))
    source={p["id"]:p["text"] for c in english["help"]["chapters"] for p in c["paragraphs"]}
    total=0
    for path in (ROOT/"locales").glob("*.json"):
        if path.stem=="en":continue
        pack=json.loads(path.read_text(encoding="utf-8"))
        before_help=json.dumps(pack["help"],ensure_ascii=False,sort_keys=True)
        assert pack["help"].get("schema")==2,f"Translate full Help first: {path.stem}"
        terms={}
        format_terms={value.rstrip(":…"):pack["strings"][key].rstrip(":…")
                      for key,value in english["strings"].items() if key in pack["strings"]
                      and len(value.rstrip(":…"))>=3 and "{" not in value}
        for label,target in pack.get("literals",{}).items():
            if len(label.rstrip(":…"))>=3 and "{" not in label:
                format_terms.setdefault(label.rstrip(":…"),target.rstrip(":…"))
        for key,value in english["strings"].items():
            if not key.startswith(("pane.","sort.","view.","menu.","filters.","common.","choice.","convert.")):continue
            if "{" in value:continue
            label=value.rstrip(":…")
            translated=pack["strings"][key].rstrip(":…")
            if len(label)>=3 and label!=translated:terms.setdefault(label,translated)
        changed=0
        for chapter in pack["help"]["chapters"]:
            for paragraph in chapter["paragraphs"]:
                value=paragraph["text"]
                original=source[paragraph["id"]]
                for label,target in sorted(terms.items(),key=lambda pair:len(pair[0]),reverse=True):
                    if label not in original:continue
                    # Protect code, paths and filenames; match standalone UI
                    # words or phrases rather than substrings of other words.
                    pattern=r"(?<![\w./\\:-])"+re.escape(label)+r"(?![\w./\\:-])"
                    value,count=re.subn(pattern,lambda _m:target,value)
                    changed+=count
                paragraph["text"]=restore_instruction_format(value,original,format_terms)
            chapter["body"]="\n\n".join(p["text"] for p in chapter["paragraphs"])
        if changed or json.dumps(pack["help"],ensure_ascii=False,sort_keys=True)!=before_help:
            path.write_text(json.dumps(pack,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        total+=changed
    print(f"Aligned {total} Help UI-label occurrences; interface dictionaries unchanged.")

if __name__=="__main__":main()
