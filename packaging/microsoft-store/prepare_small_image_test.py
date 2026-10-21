"""Isolate bulk image import using one missing Ukrainian screenshot."""
import csv
import shutil
from pathlib import Path

root=Path(r'F:\Resolution File Manager project\Store Preparation 12.6.2')
dest=root/'RFM-One-Image-Test'
dest.mkdir(exist_ok=True)
with (root/'Ukrainian-text-import-test.csv').open(encoding='utf-8-sig',newline='') as f:
    reader=csv.DictReader(f);columns=reader.fieldnames;rows=list(reader)
source=root/'Ukrainian/03-video-conversion.png'
shutil.copy2(source,dest/source.name)
for row in rows:
    if row['Field']=='DesktopScreenshot3':
        row['uk-ua']=f'{dest.name}/{source.name}'
with (dest/'listings.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader();writer.writerows(rows)
print(f'One-image import ready: {(dest/source.name).stat().st_size/1048576:.2f} MB')
