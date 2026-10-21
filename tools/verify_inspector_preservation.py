"""Verify the small inspector addition did not replace UI or Help content."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BACKUP=ROOT.parent/'Recovery Backups/2026-10-21-before-inspector-localization/source'
KEYS={'inspector.channels','inspector.pixel_format','inspector.dynamic_range',
      'inspector.unknown','inspector.unrated','inspector.unreadable'}
count=0
for path in (ROOT/'locales').glob('*.json'):
    old=json.loads((BACKUP/'locales'/path.name).read_text(encoding='utf-8'))
    new=json.loads(path.read_text(encoding='utf-8'))
    assert all(old[key]==new[key] for key in ('meta','help','literals')),path
    assert all(new['strings'][key]==value for key,value in old['strings'].items()),path
    assert set(new['strings'])-set(old['strings'])==KEYS,path
    count+=1
print(f'Preserved existing UI/help in {count} locales; only six inspector keys added.')
