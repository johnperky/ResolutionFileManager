"""Prepare reviewable release-note-only batches. Never contacts Partner Center."""
import argparse,csv,hashlib,html,json,re,shutil,sys
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools import translate_help as t
from localization import SUPPORTED_LANGUAGES,RTL_LANGUAGES

VERSION='12.7.4'
MASTER=[
    'New in version 12.7.4',
    'Create folders and choose whether copies and moves preserve subfolders or transfer files only.',
    'Preview transfers and handle filename conflicts with Keep both, Replace or Skip.',
    'Preview filename changes live and gather files in a temporary selection basket.',
    'Highlight groups separately from ticked files, with clearer selection controls, remembered Info panel widths and adjustable thumbnail sizes.',
    'Drag between panes using clearly labelled Copy, Move and Cancel buttons.',
    'Improved Undo reliability during scans and previews, with updated help in all 43 languages.'
]

def render(values):return values[0]+'\n\n'+'\n'.join('• '+value for value in values[1:])

def code_for(locale):
    if locale in ('zh-cn','zh-hans-cn'):return 'zh-CN'
    if locale=='zh-tw':return 'zh-TW'
    if locale=='pt-br':return 'pt-BR'
    if locale=='pt-pt':return 'pt-PT'
    if locale=='nb-no':return 'no'
    return locale.split('-')[0]

def translate(code,cache_dir,en):
    source_hash=t.digest(json.dumps(MASTER,ensure_ascii=False))
    cache=cache_dir/f'{code}.json'
    if cache.exists():
        saved=json.loads(cache.read_text(encoding='utf-8'))
        if saved.get('sourceSha256')==source_hash:return code,saved['paragraphs']
    if code=='en': values=MASTER
    else:
        pack=json.loads((ROOT/'locales'/f'{code}.json').read_text(encoding='utf-8'))
        terms={value:pack['strings'][key] for key,value in en['strings'].items() if key in pack['strings'] and len(value)>=3 and '{' not in value}
        terms.update({key:value for key,value in pack['literals'].items() if 3<=len(key)<90 and '{' not in key})
        terms[VERSION]=VERSION;terms['43']='43'
        combined='\n\n'.join(f'ZXQSEG{i:05d}QXZ\n{value}' for i,value in enumerate(MASTER))
        result=t.translate_text(combined,code,terms)
        if re.findall(r'ZXQSEG(\d{5})QXZ',result,re.I)==[f'{i:05d}' for i in range(len(MASTER))]:
            values=[s.strip() for s in re.split(r'ZXQSEG\d{5}QXZ',result,flags=re.I)[1:]]
        else:values=[t.translate_text(value,code,terms).strip() for value in MASTER]
    assert len(values)==len(MASTER) and all(v.strip() for v in values),code
    assert VERSION in values[0],code
    assert len(render(values))<=1500,(code,'release notes exceed conservative 1500-character cap')
    if code in RTL_LANGUAGES: assert re.search(r'[\u0590-\u08ff]',render(values)),code
    cache.write_text(json.dumps({'sourceSha256':source_hash,'paragraphs':values},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Prepared {code}',flush=True)
    return code,values

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--export',type=Path);parser.add_argument('--provider',choices=('bing','google'),default='google');args=parser.parse_args()
    t.PROVIDER=args.provider
    saved_export=args.export or ROOT.parent/'Store Preparation 12.6.2/RFM-Bulk-Import-12.6.2/listings.csv'
    maintained=ROOT/'packaging/microsoft-store/prepared-12.7.4';maintained.mkdir(exist_ok=True)
    out=ROOT.parent/'Store Preparation 12.7.4';out.mkdir(exist_ok=True)
    cache=maintained/'translation-cache';cache.mkdir(exist_ok=True)
    (maintained/'release-notes-master.json').write_text(json.dumps({'version':VERSION,'paragraphs':MASTER},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    en=json.loads((ROOT/'locales/en.json').read_text(encoding='utf-8'))
    translations={}
    with ThreadPoolExecutor(max_workers=6) as executor:
        jobs={executor.submit(translate,code,cache,en):code for code in SUPPORTED_LANGUAGES}
        for job in as_completed(jobs):
            code,values=job.result();translations[code]=values
    with saved_export.open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream);columns=reader.fieldnames;rows=list(reader)
    metadata=columns[:4];locales=columns[4:]
    original=next(row for row in rows if row['Field']=='ReleaseNotes')
    export_backup=out/'baseline-export-preserved.csv'
    if export_backup.exists():assert export_backup.read_bytes()==saved_export.read_bytes(),'Use a new preparation folder for a different export'
    else:shutil.copy2(saved_export,export_backup)
    results=[]
    for code in SUPPORTED_LANGUAGES:
        target=out/'Languages'/code;target.mkdir(parents=True,exist_ok=True)
        note=render(translations[code]);(target/'ReleaseNotes.txt').write_text(note+'\n',encoding='utf-8')
        patch={'version':VERSION,'appLanguage':code,'releaseNotes':note,'fieldsChanged':['ReleaseNotes']}
        (target/'release-notes.json').write_text(json.dumps(patch,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for start in range(0,len(locales),11):
        group=locales[start:start+11];target=out/f'RFM-12.7.4-ReleaseNotes-Part-{start//11+1}';target.mkdir(exist_ok=True)
        fields=metadata+group;row={key:original[key] for key in metadata}
        for locale in group:
            code=code_for(locale);assert code in translations,locale
            row[locale]=render(translations[code])
        with (target/'listings.csv').open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerow(row)
        assert len(list(target.glob('*.csv')))==1
        with (target/'listings.csv').open(encoding='utf-8-sig',newline='') as stream:
            checked=list(csv.DictReader(stream));assert len(checked)==1 and checked[0]['Field']=='ReleaseNotes'
        results.append({'folder':str(target),'storeLocales':group,'count':len(group),'newImages':0})
    data={'version':VERSION,'productId':'9NZL6GF5JSJK','applicationLanguages':len(translations),'storeLocaleColumns':len(locales),
          'batches':results,'changedFields':['ReleaseNotes'],'existingDescriptionsFeaturesKeywordsScreenshotsUntouched':True,
          'baselineExport':str(saved_export),'baselineSha256':hashlib.sha256(saved_export.read_bytes()).hexdigest(),
          'freshDraftExportVerified':args.export is not None,'uploadReady':False,'uploaded':False,
          'packageStatus':'Newest existing MSIX is 12.6.2.0; a verified 12.7.4.0 package is still required before submission.',
          'translationReview':'Machine translated using existing application terminology; native-speaker review not claimed.'}
    (out/'release-preparation.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (maintained/'localized-release-notes.json').write_text(json.dumps({code:render(values) for code,values in translations.items()},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'English release notes.txt').write_text(render(MASTER)+'\n',encoding='utf-8')
    instructions=f'''Resolution File Manager {VERSION} — LOCAL REVIEW ONLY

Release notes only: {len(translations)} application languages / {len(locales)} existing Store locale columns.
Five sequential batches: at most11 listings each; final smaller remainder allowed.
No new screenshots, image conversions, description/keyword edits or uploads.
Descriptions and existing asset URLs are preserved by NOT including those fields.

Before any import: export the current Partner Center draft, preserve that export,
and regenerate/reconcile these release-note-only CSVs against its actual locale
columns and Field/ID/Type metadata. The current baseline is the last saved12.6.2
export, NOT a verified fresh12.7.4 draft export. These CSVs are review templates.
Import one folder at a time and verify its save before starting the next folder.
Never fall back to repetitive individual language/image uploads by default.

The latest existing MSIX is12.6.2.0, NOT12.7.4.0. Do not upload the old package as
this release. No current package has been created or submitted in this task.
'''
    (out/'READ ME - review before upload.txt').write_text(instructions,encoding='utf-8')
    cards=''.join(f'<section dir="{"rtl" if code in RTL_LANGUAGES else "ltr"}"><h2>{html.escape(code)}</h2><pre>{html.escape(render(translations[code]))}</pre></section>' for code in SUPPORTED_LANGUAGES)
    page='<!doctype html><meta charset="utf-8"><title>RFM 12.7.4 Store release notes</title><style>body{font:16px system-ui;max-width:1000px;margin:30px auto;padding:0 20px}section{border-top:1px solid #ccc;padding:12px 0}pre{white-space:pre-wrap;font:inherit;line-height:1.6}</style><h1>Resolution File Manager12.7.4 — Store release notes</h1><p>Local review only. Release-note-only batches; no uploads or submissions.</p>'+cards
    (out/'REVIEW.html').write_text(page,encoding='utf-8')
    print(json.dumps({'folder':str(out),'languages':len(translations),'storeListings':len(locales),'batches':[r['count'] for r in results],'uploadReady':False}))

if __name__=='__main__':main()
