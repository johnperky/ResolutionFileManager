"""Retranslate a selected numbered paragraph one instruction at a time.

Preserve the original step labels outside the translation service so they
cannot be dropped. Only specified Help paragraphs change, never UI or English.
"""
import argparse
import json
import re
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import translate_help as t

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("paragraphs",nargs="+"); args=parser.parse_args()
    en=json.loads((ROOT/"locales/en.json").read_text(encoding="utf-8"))
    source={p["id"]:p["text"] for c in en["help"]["chapters"] for p in c["paragraphs"]}
    for specification in args.paragraphs:
        code,ident=specification.split(":",1)
        if code=="en": raise ValueError("English is protected")
        path=ROOT/"locales"/(code+".json"); pack=json.loads(path.read_text(encoding="utf-8"))
        terms={value:pack["strings"][key] for key,value in en["strings"].items() if key in pack["strings"] and len(value)>=5 and "{" not in value}
        for key,value in pack.get("literals",{}).items():
            if 5<=len(key)<110 and "{" not in key: terms.setdefault(key,value)
        result=[]
        for line in source[ident].splitlines():
            match=re.match(r"^(\d+[.)]\s+)(.*)$",line)
            if match: result.append(match[1]+t.translate_text(match[2],code,terms))
            elif line.strip(): result.append(t.translate_text(line,code,terms))
            else: result.append("")
        value="\n".join(result)
        for chapter in pack["help"]["chapters"]:
            for paragraph in chapter["paragraphs"]:
                if paragraph["id"]==ident: paragraph["text"]=value
            chapter["body"]="\n\n".join(p["text"] for p in chapter["paragraphs"])
        temporary=path.with_suffix(".help.tmp"); temporary.write_text(json.dumps(pack,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); temporary.replace(path)
        print("Repaired "+specification,flush=True)

if __name__=="__main__": main()
