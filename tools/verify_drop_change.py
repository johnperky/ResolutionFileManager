"""Verify that this small dialog change touched only the relevant Help paragraph."""
import json,sys,copy
from pathlib import Path
root=Path(__file__).resolve().parents[1]
before=Path('F:/Resolution File Manager project/Recovery Backups/2026-10-21-before-drop-button-fix/source')
results=[]
for path in (root/'locales').glob('*.json'):
    new=json.loads(path.read_text(encoding='utf-8'));old=json.loads((before/'locales'/path.name).read_text(encoding='utf-8'))
    if '--restore-unrelated' in sys.argv:
        previous={p['id']:p for c in old['help']['chapters'] for p in c['paragraphs']}
        for chapter in new['help']['chapters']:
            chapter['paragraphs']=[p if p['id']=='copying_and_moving.p005' else copy.deepcopy(previous[p['id']]) for p in chapter['paragraphs']]
            chapter['body']='\n\n'.join(p['text'] for p in chapter['paragraphs'])
        path.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert new['strings']==old['strings'] and new['literals']==old['literals'],path.stem
    assert [c['id'] for c in new['help']['chapters']]==[c['id'] for c in old['help']['chapters']],path.stem
    changes=[]
    for nc,oc in zip(new['help']['chapters'],old['help']['chapters']):
        assert nc['title']==oc['title'],path.stem
        assert [p['id'] for p in nc['paragraphs']]==[p['id'] for p in oc['paragraphs']],path.stem
        changes.extend(p['id'] for p,o in zip(nc['paragraphs'],oc['paragraphs']) if p['text']!=o['text'])
    assert set(changes)=={'copying_and_moving.p005'},(path.stem,changes)
    results.append({'language':path.stem,'existing_ui_unchanged':True,'changed_help':changes})
(root/'docs/DROP_CHANGE_PRESERVATION_12.7.4.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'{len(results)} languages: existing UI and all other Help paragraphs preserved')
