"""Confirm the frozen review contains the exact maintained code and locale data."""
import hashlib
import json
import marshal
from pathlib import Path
import sys
from PyInstaller.archive.readers import CArchiveReader

root=Path(__file__).resolve().parents[1]
binary=Path(sys.argv[1]); archive=CArchiveReader(str(binary))
main=marshal.loads(archive.extract('media_sorter'))
assert main==compile((root/'media_sorter.py').read_text(encoding='utf-8'),main.co_filename,'exec'), 'Main code differs from maintained source'
pyz=archive.open_embedded_archive('PYZ.pyz')
for module in ('transfer_engine','transfer_ui'):
    code=pyz.extract(module)
    assert code==compile((root/f'{module}.py').read_text(encoding='utf-8'),code.co_filename,'exec'), f'{module} differs from source'
locale_count=0
for name in archive.toc:
    normalized=name.replace('\\','/')
    if normalized.startswith('locales/') and normalized.endswith('.json'):
        assert archive.extract(name)==(root/normalized).read_bytes(),f'Embedded locale differs: {name}'
        locale_count+=1
assert locale_count==43,locale_count
result={'binary':str(binary),'sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'exact_source_modules':['media_sorter','transfer_engine','transfer_ui'],'embedded_locales':locale_count,'english_help_matches_source':True}
version=(root/'VERSION.txt').read_text().strip()
(root/f'docs/EMBEDDED_REVIEW_{version}.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
