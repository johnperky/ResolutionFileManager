"""Inventory the pre-recovery backups, including Git and historical binaries."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BACKUPS=ROOT.parent/"Recovery Backups"/"2026-10-19-before-help-recovery"

def entry(path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):h.update(block)
    return path.relative_to(BACKUPS).as_posix(),h.hexdigest()

def main():
    files=[p for p in BACKUPS.rglob("*") if p.is_file() and p.name!="BACKUP_VERIFICATION.json"]
    with ThreadPoolExecutor(max_workers=4) as pool: hashes=dict(pool.map(entry,files))
    labels=["Latest-Windows-Source-12.6.0","Existing-F-Project-12.6.0","Existing-Linux-Source-12.3.0","Help-and-Translations-12.6.0"]
    for label in labels:
        assert any(p.startswith(label+"/") for p in hashes),f"Missing backup {label}"
    initial="C5177E0A72F66CA2BB38B742228ADE60E09AD9927D21CD6522D557B93AAFE487".lower()
    for label in labels[:2]:
        assert hashes[label+"/media_sorter.py"]==initial
        assert len(list((BACKUPS/label/"locales").glob("*.json")))==43
        assert (BACKUPS/label/".git"/"HEAD").is_file()
    first=labels[0]+"/"; second=labels[1]+"/"
    differences=[p[len(first):] for p,h in hashes.items() if p.startswith(first) and not p.startswith(first+".git/") and hashes.get(second+p[len(first):])!=h]
    assert not differences,differences
    report={"backup_root":str(BACKUPS),"verified_files":len(hashes),"windows_source_sha256":initial,
            "separate_labels":labels,"windows_and_f_source_differences":differences,"files":hashes}
    (BACKUPS/"BACKUP_VERIFICATION.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    (ROOT/"docs"/"BACKUP_VERIFICATION.json").write_text(json.dumps({k:v for k,v in report.items() if k!="files"},indent=2)+"\n",encoding="utf-8")
    print(f"Verified {len(hashes)} backup files; Windows/F sources identical; 43 locale packs protected in both.")

if __name__=="__main__":main()
