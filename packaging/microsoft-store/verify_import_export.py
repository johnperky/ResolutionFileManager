"""Verify saved Import listings batches against a new Partner Center export."""
import argparse
import csv
from collections import Counter
import hashlib
import json
from pathlib import Path


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = [row for row in reader if row["Field"]]
        assert len({row["Field"] for row in rows}) == len(rows)
        return reader.fieldnames, {row["Field"]: row for row in rows}


def normal(value):
    return value.replace("\r\n", "\n").strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--export", type=Path, required=True)
    parser.add_argument("--parts", nargs="+", type=int, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--selected-only", action="store_true")
    parser.add_argument("--image-reference", type=Path,
                        help="Earlier saved export: preserve URL/caption pairs during restoration")
    parser.add_argument("--image-reference-parts", nargs="+", type=int,
                        help="Limit saved-pair checks to restored batches")
    args = parser.parse_args()
    preparation = json.loads((args.prepared / "preparation.json").read_text(encoding="utf-8"))
    columns, baseline = read(args.prepared / "Baseline/current-draft-export.csv")
    actual_columns, actual = read(args.export)
    assert actual_columns == columns, "Store locale/metadata columns changed"
    assert set(actual) == set(baseline), "Export fields changed"
    expected, locales = {}, []
    for part in args.parts:
        batch = preparation["batches"][part - 1]
        _, patch = read(args.prepared / batch["folder"] / "listings.csv")
        locales.extend(batch["storeLocales"])
        for field, row in patch.items():
            if field not in preparation["changedFields"]:
                continue
            for locale in batch["storeLocales"]:
                expected[field, locale] = row[locale]
    assert len(set(locales)) == len(locales)
    errors, verified = [], 0
    verified_pairs = 0
    if args.image_reference:
        _, reference = read(args.image_reference)
        pair_locales = [locale for part in (args.image_reference_parts or args.parts)
                        for locale in preparation["batches"][part - 1]["storeLocales"]]
        for column in pair_locales:
            pairs = lambda data: Counter((data[f"DesktopScreenshot{i}"][column], normal(data[f"DesktopScreenshotCaption{i}"][column])) for i in range(1, 5))
            if pairs(reference) != pairs(actual):
                errors.append(f"Saved screenshot/caption pairing changed: {column}")
            else:
                verified_pairs += 4
    for field, original in baseline.items():
        for column in columns:
            if args.selected_only and column in columns[4:] and column not in locales:
                continue
            key = field, column
            value = actual[field][column]
            if key not in expected:
                if normal(value) != normal(original[column]):
                    errors.append(f"Unexpected change: {field}/{column}")
            elif field.startswith("DesktopScreenshotCaption"):
                # Partner Center may reorder uploaded screenshot/caption pairs.
                # Compare the complete caption set instead of asserting slots.
                wanted = Counter(normal(expected[f"DesktopScreenshotCaption{i}", column]) for i in range(1, 5))
                saved = Counter(normal(actual[f"DesktopScreenshotCaption{i}"][column]) for i in range(1, 5))
                if saved != wanted:
                    errors.append(f"Saved caption set differs: {column}")
                else:
                    verified += 1
            elif field.startswith("DesktopScreenshot") and "Caption" not in field:
                if not value.startswith("https://") or value == original[column]:
                    errors.append(f"New screenshot not confirmed: {field}/{column}")
                else:
                    verified += 1
            elif normal(value) != normal(expected[key]):
                errors.append(f"Saved text differs: {field}/{column}")
            else:
                verified += 1
    result = {"submissionId": preparation["draftSubmissionId"], "completedParts": args.parts,
        "verifiedStoreListings": len(locales), "verifiedChangedCells": verified,
        "selectedLocalesOnly": args.selected_only,
        "verifiedSavedScreenshotCaptionPairs": verified_pairs,
        "exportSha256": hashlib.sha256(args.export.read_bytes()).hexdigest(),
        "otherFieldsUnchanged": not any(e.startswith("Unexpected") for e in errors),
        "errors": errors, "passed": not errors}
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
