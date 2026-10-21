"""Restore complete listing fields while reusing newly saved screenshot URLs."""
import argparse
import csv
import io
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--saved-export", type=Path, required=True)
    args = parser.parse_args()
    with args.saved_export.open(encoding="utf-8-sig", newline="") as stream:
        current = {row["Field"]: row for row in csv.DictReader(stream) if row["Field"]}
    report = json.loads((args.prepared / "preparation.json").read_text(encoding="utf-8"))
    for part, batch in enumerate(report["batches"][:3], 1):
        source = args.prepared / batch["folder"] / "listings.csv"
        with source.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            columns, rows = reader.fieldnames, list(reader)
        for row in rows:
            if row["Field"] in report["changedFields"] and row["Field"] != "ReleaseNotes":
                for locale in batch["storeLocales"]:
                    assert current[row["Field"]][locale]
                    row[locale] = current[row["Field"]][locale]
        # Full export rows include every existing feature, keyword and logo flag.
        assert len(rows) > 400
        dest = args.prepared / f"RFM-12.7.10-Restore-Part-{part}"
        dest.mkdir(exist_ok=True)
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
        content = stream.getvalue().encode("utf-8-sig")
        target = dest / "listings.csv"
        if target.exists():
            assert target.read_bytes() == content
        else:
            target.write_bytes(content)
        print(f"Prepared full-field restore folder {part}: {len(batch['storeLocales'])} locales; existing screenshot URLs reused; no images reuploaded")


if __name__ == "__main__":
    main()
