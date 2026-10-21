"""Ensure a translation-only update retained approved English and existing UI."""
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('baseline');parser.add_argument('--report');args=parser.parse_args()
baseline=Path(args.baseline)
for name in ('docs/help/en.json','docs/help/ENGLISH_MANUAL.md'):
    assert (ROOT/name).read_bytes()==(baseline/name).read_bytes(),f'Approved English changed: {name}'
results=[];flags=[]
for path in (ROOT/'locales').glob('*.json'):
    new=json.loads(path.read_text(encoding='utf-8'));old=json.loads((baseline/'locales'/path.name).read_text(encoding='utf-8'))
    additions=0
    for section in ('strings','literals'):
        for key,value in old[section].items(): assert new[section][key]==value,(path.stem,section,key)
        additions+=len(set(new[section])-set(old[section]))
        if path.stem!='en':
            for key in set(new[section])-set(old[section]):
                value=new[section][key]
                if value==key and len(key)>25 and len(key.split())>4: flags.append({'language':path.stem,'key':key})
    if path.stem=='en': assert new['help']==old['help'],'English runtime Help changed'
    results.append({'language':path.stem,'original_ui_preserved':True,'added_entries':additions})
report={'baseline':str(baseline),'approved_english_master_manual_and_runtime_help_preserved':True,'languages':results,'new_ui_english_review_flags':flags}
if args.report: Path(args.report).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'preserved_languages':len(results),'added_entries':sum(r['added_entries'] for r in results),'new_ui_english_review_flags':flags}))
