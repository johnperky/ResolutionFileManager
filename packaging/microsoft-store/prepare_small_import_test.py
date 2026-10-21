"""Create a one-language text import using only its already-uploaded assets."""
import csv
from pathlib import Path

root = Path(r'F:\Resolution File Manager project\Store Preparation 12.6.2')
with (root/'Store-export-before-bulk.csv').open(encoding='utf-8-sig', newline='') as f:
    baseline = {r['Field']:r for r in csv.DictReader(f) if r['Field']}
with (root/'RFM-Bulk-Import-12.6.2/listings.csv').open(encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    columns = reader.fieldnames[:4]+['uk-ua']
    rows = [{k:r[k] for k in columns} for r in reader if r['Field']]
for row in rows:
    if row['Type (Type)'] != 'Text':
        row['uk-ua'] = baseline[row['Field']]['uk-ua']
    assert not row['uk-ua'].startswith('RFM-Bulk-Import')
with (root/'Ukrainian-text-import-test.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)
print('One-language CSV ready; existing asset references preserved, no local images uploaded.')
