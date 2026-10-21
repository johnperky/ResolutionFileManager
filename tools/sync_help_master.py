"""Render the English master and sync only English Help, never UI translations."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    path=ROOT/"docs/help/en.json"
    master=json.loads(path.read_text(encoding="utf-8"))
    for chapter in master["chapters"]:
        chapter["body"]="\n\n".join(p["text"] for p in chapter["paragraphs"])
    raw=json.dumps(master,ensure_ascii=False,indent=2)+"\n"
    path.write_text(raw,encoding="utf-8")
    english_path=ROOT/"locales/en.json"
    english=json.loads(english_path.read_text(encoding="utf-8"))
    english["help"]={**master,"master_sha256":hashlib.sha256(raw.encode()).hexdigest(),"direction":"ltr"}
    english_path.write_text(json.dumps(english,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (ROOT/"docs/help/ENGLISH_MANUAL.md").write_text("# Resolution File Manager — authoritative English manual\n\n"+"\n\n".join(f"## {c['title']}\n\n{c['body']}" for c in master["chapters"])+"\n",encoding="utf-8")
    print(f"English master synchronised: {len(master['chapters'])} chapters")

if __name__=="__main__":main()
