"""Prepare small Import listings folders from a fresh export; never uploads."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import hashlib
import html
import importlib.util
import io
import json
from pathlib import Path
import re
import shutil
import sys
import zipfile
import xml.etree.ElementTree as ET

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from localization import SUPPORTED_LANGUAGES, RTL_LANGUAGES

spec = importlib.util.spec_from_file_location("notes_helper", Path(__file__).with_name("prepare_1274_release_notes.py"))
notes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notes)
notes.VERSION = "12.7.10"
notes.MASTER = [
    "New in version 12.7.10",
    "Show or hide hidden files and folders from the Tools menu.",
    "Expanded Help for folder organisation rules, including filename, codec, rating and tag examples.",
    "More reliable undo, clearer transfer previews, filename conflict choices and file selection controls.",
    "Better layouts for file information, video conversion settings, themes and enlarged text.",
    "43 interface languages, each with a full user guide. All media processing stays on your computer.",
    "Details and file information", "Independent media previews", "Thumbnail browsing", "Video conversion preview",
]
VIEWS = ("01-details-info", "02-dual-previews", "03-thumbnails", "04-video-conversion")
EXPECTED_BINARY = "ecc2b624c556aa923bcb132e937b3600abb11bdcc8b6a94a5d2e8f997f004419"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_preserving(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    content = content.encode("utf-8-sig") if path.suffix == ".csv" else content.encode("utf-8")
    if path.exists():
        assert path.read_bytes() == content, f"Preserving different existing file: {path}"
    else:
        path.write_bytes(content)


def translate_notes(code, cache):
    """Translate prose naturally; short UI glossary words can corrupt longer words."""
    fingerprint = notes.t.digest(json.dumps(notes.MASTER, ensure_ascii=False))
    path = cache / f"plain-{code}.json"
    if path.exists():
        saved = json.loads(path.read_text(encoding="utf-8"))
        if saved["sourceSha256"] == fingerprint:
            return code, saved["paragraphs"]
    if code == "en":
        values = notes.MASTER
    else:
        text = "\n\n".join(f"ZXQSEG{i:05d}QXZ\n{value}" for i, value in enumerate(notes.MASTER))
        translated = notes.t.translate_text(text, code, {"12.7.10": "12.7.10", "43": "43"})
        markers = re.findall(r"ZXQSEG(\d{5})QXZ", translated, re.I)
        if markers == [f"{i:05d}" for i in range(len(notes.MASTER))]:
            values = [value.strip() for value in re.split(r"ZXQSEG\d{5}QXZ", translated, flags=re.I)[1:]]
        else:
            values = [notes.t.translate_text(value, code, {"12.7.10": "12.7.10", "43": "43"}).strip() for value in notes.MASTER]
    assert len(values) == len(notes.MASTER) and all(values)
    assert "12.7.10" in values[0] and "43" in values[5]
    assert len(notes.render(values[:6])) <= 1500, code
    if code in RTL_LANGUAGES:
        assert re.search(r"[\u0590-\u08ff]", " ".join(values)), code
    path.write_text(json.dumps({"sourceSha256": fingerprint, "paragraphs": values}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {code}", flush=True)
    return code, values


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", type=Path)
    parser.add_argument("--translations-only", action="store_true")
    parser.add_argument("--languages", nargs="*")
    parser.add_argument("--batch-size", type=int, choices=range(1, 13), default=12)
    parser.add_argument("--output", type=Path, default=ROOT.parent / "Store Preparation 12.7.10/Submission Folders Preserved")
    args = parser.parse_args()
    cache = ROOT / "packaging/microsoft-store/prepared-12.7.10/translation-cache"
    cache.mkdir(parents=True, exist_ok=True)
    notes.t.PROVIDER = "google"
    codes = args.languages or list(SUPPORTED_LANGUAGES)
    translations = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        jobs = [pool.submit(translate_notes, code, cache) for code in codes]
        for job in as_completed(jobs):
            code, values = job.result()
            translations[code] = values
    if args.translations_only:
        print(json.dumps({"translatedLanguages": sorted(translations), "sourceSha256": notes.t.digest(json.dumps(notes.MASTER, ensure_ascii=False))}))
        return
    assert args.export and args.export.is_file(), "A fresh Partner Center export is required"
    assert set(translations) == set(SUPPORTED_LANGUAGES)
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    baseline = out / "Baseline/current-draft-export.csv"
    baseline.parent.mkdir(exist_ok=True)
    if baseline.exists():
        assert baseline.read_bytes() == args.export.read_bytes(), "Different baseline: use a new output folder"
    else:
        shutil.copy2(args.export, baseline)
    with baseline.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        columns, rows = reader.fieldnames, list(reader)
    assert columns[:4] == ["Field", "ID", "Type (Type)", "default"]
    locales, metadata = columns[4:], columns[:4]
    assert "en-in" in locales and "sr-cyrl-rs" in locales
    assert len(set(locales)) == len(locales)
    assert {notes.code_for(locale) for locale in locales} == set(SUPPORTED_LANGUAGES)
    fields = {row["Field"]: row for row in rows}
    changed = ["ReleaseNotes"] + [f"DesktopScreenshot{i}" for i in range(1, 5)] + [f"DesktopScreenshotCaption{i}" for i in range(1, 5)]
    assert all(field in fields for field in changed)
    captures = ROOT.parent / "Store Preparation 12.7.10/Batch Candidates v3"
    review = json.loads((captures / "visual-review.json").read_text(encoding="utf-8"))
    assert review["visualReviewComplete"] and review["version"] == "12.7.10"
    approved = {entry["file"]: entry["sha256"] for entry in review["captures"]}
    assert len(approved) == 172
    images = {}
    for code in SUPPORTED_LANGUAGES:
        for view in VIEWS:
            relative = f"{code}/{view}.png"
            path = captures / relative
            assert sha(path) == approved[relative], path
            assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
            with Image.open(path) as image:
                image.load()
                assert image.format == "PNG" and min(image.size) >= 720
                assert path.stat().st_size < 50 * 1024**2
                images[relative] = {"sha256": sha(path), "dimensions": list(image.size)}
    # Validate packaged identity and the exact reviewed Help executable before copying.
    package = ROOT / "packaging/microsoft-store/output/ResolutionFileManager-12.7.10.0-x64.msix"
    with zipfile.ZipFile(package) as archive:
        assert archive.testzip() is None
        manifest = ET.fromstring(archive.read("AppxManifest.xml"))
        ns = {"m": "http://schemas.microsoft.com/appx/manifest/foundation/windows10"}
        identity = manifest.find("m:Identity", ns).attrib
        assert identity["Version"] == "12.7.10.0"
        assert identity["Name"] == "JohnPerky1.ResolutionFileManager"
        assert identity["Publisher"] == "CN=F8A8AD4B-0BE8-4500-B4F9-27B3B0FB48ED"
        languages = [entry.attrib["Language"] for entry in manifest.findall("m:Resources/m:Resource", ns)]
        assert len(languages) == 43 and "sr-cyrl-rs" in languages
        assert hashlib.sha256(archive.read("ResolutionFileManager.exe")).hexdigest() == EXPECTED_BINARY
        assert any(name.startswith("licenses/") for name in archive.namelist())
    target_package = out / "Package" / package.name
    target_package.parent.mkdir(exist_ok=True)
    if not target_package.exists():
        shutil.copy2(package, target_package)
    assert sha(target_package) == sha(package)
    batches = []
    for start in range(0, len(locales), args.batch_size):
        group = locales[start:start + args.batch_size]
        folder = out / f"RFM-12.7.10-Import-Part-{start // args.batch_size + 1}"
        folder.mkdir(exist_ok=True)
        # Partner Center clears omitted list fields (features/search terms), even
        # when omitted scalar fields survive. Always send the complete export.
        data = [{key: original[key] for key in metadata} for original in rows]
        for locale in group:
            code = notes.code_for(locale)
            values = translations[code]
            note = notes.render(values[:6])
            write_preserving(out / "Release Notes" / f"{locale}.txt", note + "\n")
            for row in data:
                field = row["Field"]
                if field not in changed:
                    row[locale] = fields[field][locale]
                elif field == "ReleaseNotes":
                    row[locale] = note
                elif field.startswith("DesktopScreenshotCaption"):
                    row[locale] = values[5 + int(field.removeprefix("DesktopScreenshotCaption"))]
                else:
                    view = VIEWS[int(field.removeprefix("DesktopScreenshot")) - 1]
                    relative = f"{code}/{view}.png"
                    dest = folder / "images" / locale / f"{view}.png"
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if not dest.exists():
                        shutil.copy2(captures / relative, dest)
                    assert sha(dest) == images[relative]["sha256"]
                    row[locale] = f"{folder.name}/images/{locale}/{view}.png"
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=metadata + group)
        writer.writeheader()
        writer.writerows(data)
        write_preserving(folder / "listings.csv", stream.getvalue())
        assert len(list(folder.glob("*.csv"))) == 1
        assert len(list(folder.rglob("*.png"))) == len(group) * 4
        with (folder / "listings.csv").open(encoding="utf-8-sig", newline="") as stream:
            saved = list(csv.DictReader(stream))
        assert saved == data
        for row in saved:
            for locale in group:
                if row["Field"] in changed and row["Field"].startswith("DesktopScreenshot") and "Caption" not in row["Field"]:
                    assert (folder.parent / row[locale]).is_file()
                assert all(row[key] == fields[row["Field"]][key] for key in metadata)
        batches.append({"folder": folder.name, "storeLocales": group, "listingCount": len(group), "pngCount": len(group) * 4, "csvSha256": sha(folder / "listings.csv")})
    report = {"version": "12.7.10", "packageVersion": "12.7.10.0", "productId": "9NZL6GF5JSJK",
        "draftSubmissionId": "1152921505702194214", "baselineSha256": sha(baseline),
        "packageSha256": sha(package), "embeddedExeSha256": EXPECTED_BINARY,
        "applicationLanguages": len(translations), "storeListings": len(locales), "uniqueApprovedPngs": 172,
        "uploadPngs": len(locales) * 4, "batches": batches, "changedFields": changed,
        "otherFieldsCopiedFromBaseline": True, "freshDraftExportVerified": True,
        "pngFilesVerified": True, "localPreparationComplete": True, "uploaded": False, "submitted": False,
        "translationReview": "Machine translation; technical version/count preserved; native-speaker proofreading not claimed."}
    write_preserving(out / "preparation.json", json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    cards = "".join(f'<section dir="{"rtl" if c in RTL_LANGUAGES else "ltr"}"><h2>{html.escape(c)}</h2><pre>{html.escape(notes.render(translations[c][:6]))}</pre></section>' for c in SUPPORTED_LANGUAGES)
    write_preserving(out / "Release Notes Review.html", '<!doctype html><meta charset="utf-8"><title>12.7.10 Store release notes</title><style>body{font:16px system-ui;max-width:1000px;margin:30px auto}pre{white-space:pre-wrap;font:inherit}section{border-top:1px solid #ccc;padding:12px}</style><h1>Resolution File Manager 12.7.10</h1>' + cards)
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
