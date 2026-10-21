"""Split the verified import into four disjoint locale batches without deleting originals."""
import csv
import json
import shutil
from pathlib import Path

root=Path(r'F:\Resolution File Manager project\Store Preparation 12.6.2')
source=root/'RFM-Bulk-Import-12.6.2'
with (source/'listings.csv').open(encoding='utf-8-sig',newline='') as f:
    reader=csv.DictReader(f);columns=reader.fieldnames;rows=list(reader)
# Keep all existing locale cells in exactly one batch. Spread image-bearing languages evenly.
locales=columns[4:]
image_locales=[c for c in locales if any(r[c].startswith(source.name+'/') for r in rows)]
groups=[image_locales[i::4] for i in range(4)]
for i,c in enumerate(c for c in locales if c not in image_locales):groups[i%4].append(c)
report=[]
for i,group in enumerate(groups,1):
    dest=root/f'RFM-Import-Part-{i}'
    dest.mkdir(exist_ok=True)
    selected=columns[:4]+group
    out=[];count=0
    for row in rows:
        item={c:row[c] for c in selected}
        for c in group:
            value=item[c]
            if not value.startswith(source.name+'/'):continue
            relative=Path(value).relative_to(source.name)
            target=dest/relative;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source/relative,target)
            assert target.read_bytes()==(source/relative).read_bytes()
            item[c]=f'{dest.name}/{relative.as_posix()}'
            count+=1
        out.append(item)
    with (dest/'listings.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=selected);writer.writeheader();writer.writerows(out)
    assert len(list(dest.glob('*.csv')))==1
    report.append({'part':i,'folder':str(dest),'locales':group,'images':count})
assert sorted(c for g in groups for c in g)==sorted(locales)
assert sum(r['images'] for r in report)==67
(root/'four-part-import.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps([{'part':r['part'],'languages':len(r['locales']),'images':r['images']} for r in report]))
