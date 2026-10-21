"""Create a complete, non-overwriting source snapshot and verify every file."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {"media_sorter.py", "localization.py", "rtl_display.py", "reminder_policy.py", "verify_release_assets.py",
            "VERSION.txt", "requirements.txt", "build_windows.ps1", "build_linux.sh", "run_linux.sh",
            "app_icon.png", "app_icon.ico", "docs/help/en.json", "docs/help/ENGLISH_MANUAL.md"}

def sha(path):
    result=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024), b""): result.update(block)
    return result.hexdigest()

def source_files():
    result=subprocess.check_output(["git","ls-files","--cached","--others","--exclude-standard","-z"],cwd=ROOT).decode("utf-8")
    names=set(result.rstrip("\0").split("\0")) | REQUIRED
    files=sorted(p for p in names if p and (ROOT/p).is_file())
    missing=sorted(REQUIRED-set(files))
    if missing: raise ValueError("Missing essential source files: "+", ".join(missing))
    return files

def verify(destination):
    destination=Path(destination)
    manifest=json.loads((destination/"SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    errors=[]
    for name, expected in manifest["files"].items():
        path=destination/name
        if not path.is_file() or sha(path)!=expected: errors.append(name)
    if errors: raise ValueError("Snapshot verification failed: "+", ".join(errors))
    return manifest

def snapshot(destination, archive=False):
    destination=Path(destination).resolve()
    if destination.exists(): raise FileExistsError(f"Preserving existing snapshot: {destination}")
    names=source_files()
    hashes={name:sha(ROOT/name) for name in names}
    destination.mkdir(parents=True)
    for name in names:
        target=destination/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/name,target)
    manifest={"version":(ROOT/"VERSION.txt").read_text().strip(),"source":str(ROOT),
              "git_head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
              "files":hashes}
    (destination/"SOURCE_MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    verify(destination)
    # Detect edits during the copy rather than calling a mixed snapshot complete.
    changed=[name for name in names if sha(ROOT/name)!=hashes[name]]
    if changed: raise ValueError("Source changed during snapshot; use a fresh destination: "+", ".join(changed))
    if archive:
        zip_path=Path(str(destination)+".zip")
        if zip_path.exists(): raise FileExistsError(zip_path)
        with zipfile.ZipFile(zip_path,"x",zipfile.ZIP_DEFLATED) as output:
            for name in [*names,"SOURCE_MANIFEST.json"]: output.write(destination/name,name)
    return manifest

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=("create","verify","candidates"))
    parser.add_argument("destination",nargs="?")
    parser.add_argument("--zip",action="store_true")
    args=parser.parse_args()
    if args.action=="candidates":
        print("\n".join(source_files())); return
    if not args.destination: parser.error("destination required")
    result=verify(args.destination) if args.action=="verify" else snapshot(args.destination,args.zip)
    print(f"Verified {len(result['files'])} files for {result['version']}: {args.destination}")

if __name__=="__main__": main()
