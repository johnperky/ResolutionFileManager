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
modules=('transfer_engine','transfer_ui','localization','rtl_display','reminder_policy','conversion_ui','conversion_profiles','ai_backends','ai_pipeline','ai_worker','ai_video_stream','image_pipeline','image_ui','conversion_jobs','process_utils','video_enhancement','conversion_display','conversion_conflicts')
for module in modules:
    code=pyz.extract(module)
    assert code==compile((root/f'{module}.py').read_text(encoding='utf-8'),code.co_filename,'exec'), f'{module} differs from source'
locale_count=0
for name in archive.toc:
    normalized=name.replace('\\','/')
    if normalized.startswith('locales/') and normalized.endswith('.json'):
        assert archive.extract(name)==(root/normalized).read_bytes(),f'Embedded locale differs: {name}'
        locale_count+=1
assert locale_count==43,locale_count
manifest=json.loads((root/'assets/ai/manifest.json').read_text())
manifest_entry=next(key for key in archive.toc if key.replace('\\','/')=='assets/ai/manifest.json')
assert archive.extract(manifest_entry)==(root/'assets/ai/manifest.json').read_bytes(),'Embedded model manifest/provenance differs from source'
for name,entry in manifest['files'].items():
    embedded='assets/ai/'+name
    archive_name=next((key for key in archive.toc if key.replace('\\','/')==embedded),None)
    assert archive_name,f'Missing AI asset {name}'
    assert hashlib.sha256(archive.extract(archive_name)).hexdigest()==entry['sha256'],f'Changed AI asset {name}'
result={'binary':str(binary),'sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'exact_source_modules':['media_sorter',*modules],'embedded_locales':locale_count,'english_help_matches_source':True,'verified_ai_assets':len(manifest['files'])}
version=(root/'VERSION.txt').read_text().strip()
report=Path(sys.argv[2]) if len(sys.argv)>2 else root/f'docs/EMBEDDED_REVIEW_{version}.json'
report.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
