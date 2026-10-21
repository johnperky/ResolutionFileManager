"""Add three requested sorting searches to local multilingual batch templates."""
import csv,json,re,sys
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools import translate_help as t
from localization import SUPPORTED_LANGUAGES
OUT=ROOT.parent/'Store Preparation 12.7.4'
MAINTAINED=ROOT/'packaging/microsoft-store/prepared-12.7.4'
SOURCE=['sort by video length','sort by resolution','sort across folders']
COMPACT=['video duration sorting','resolution sorting','cross-folder sorting']
t.PROVIDER='google'

def language(code):
    cache=MAINTAINED/'keyword-cache';cache.mkdir(exist_ok=True);path=cache/f'{code}.json'
    if path.exists(): return code,json.loads(path.read_text(encoding='utf-8'))
    if code=='en':values=SOURCE
    else:
        combined='\n'.join(f'ZXQSEG{i:05d}QXZ\n{text}' for i,text in enumerate(SOURCE))
        translated=t.translate_text(combined,code,{})
        if re.findall(r'ZXQSEG(\d{5})QXZ',translated,re.I)==['00000','00001','00002']:
            values=[s.strip() for s in re.split(r'ZXQSEG\d{5}QXZ',translated,flags=re.I)[1:]]
        else:values=[t.translate_text(value,code,{}).strip() for value in SOURCE]
        for i,value in enumerate(values):
            if len(value)>40: values[i]=t.translate_text(COMPACT[i],code,{}).strip()
    assert len(values)==3 and all(v and len(v)<=40 for v in values),(code,values)
    path.write_text(json.dumps(values,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return code,values

def code_for(locale):
    return {'zh-hans-cn':'zh-CN','zh-cn':'zh-CN','zh-tw':'zh-TW','pt-br':'pt-BR','pt-pt':'pt-PT','nb-no':'no'}.get(locale,locale.split('-')[0])

def main():
    with (OUT/'baseline-export-preserved.csv').open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f);columns=reader.fieldnames;rows={row['Field']:row for row in reader}
    translations={}
    with ThreadPoolExecutor(max_workers=6) as executor:
        for code,values in executor.map(language,SUPPORTED_LANGUAGES):translations[code]=values
    reports=[]
    for folder in sorted(OUT.glob('RFM-12.7.4-ReleaseNotes-Part-*')):
        with (folder/'listings.csv').open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f);fields=reader.fieldnames;existing=list(reader)
        output=[row for row in existing if not row['Field'].startswith('SearchTerm')]
        for i in range(3):
            original=rows[f'SearchTerm{i+1}'];entry={c:original[c] for c in fields[:4]}
            for locale in fields[4:]:entry[locale]=translations[code_for(locale)][i]
            output.append(entry)
        with (folder/'listings.csv').open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(output)
        for locale in fields[4:]:
            code=code_for(locale);keywords=translations[code]+[rows[f'SearchTerm{i}'][locale] for i in range(4,8)]
            words=len({word.casefold().strip('.,;:!?') for value in keywords for word in value.split()})
            assert len(keywords)==7 and max(map(len,keywords))<=40 and words<=21,(locale,keywords,words)
            reports.append({'locale':locale,'appLanguage':code,'keywords':keywords,'uniqueWordCount':words,'passed':True})
    for code in SUPPORTED_LANGUAGES:
        target=OUT/'Languages'/code
        locales=[r for r in reports if r['appLanguage']==code];keywords=locales[0]['keywords']
        (target/'Search terms.txt').write_text('\n'.join(keywords)+'\n',encoding='utf-8')
        path=target/'release-notes.json';data=json.loads(path.read_text(encoding='utf-8'))
        data['keywords']=keywords;data['fieldsChanged']=['ReleaseNotes','SearchTerm1','SearchTerm2','SearchTerm3']
        path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report={'source':'https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/add-additional-information',
        'limits':{'keywords':7,'charactersPerKeyword':40,'uniqueWordsAcrossAllKeywords':21},
        'changes':'Replace three broad manager/organiser keywords with requested sorting phrases; preserve SearchTerm4–7.',
        'storeListings':reports,'uploadReady':False,'uploaded':False}
    (OUT/'keyword-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (MAINTAINED/'localized-keywords.json').write_text(json.dumps(translations,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    path=OUT/'release-preparation.json';data=json.loads(path.read_text(encoding='utf-8'))
    data.pop('existingDescriptionsFeaturesKeywordsScreenshotsUntouched',None)
    data['existingDescriptionsFeaturesScreenshotsUntouched']=True
    data['changedFields']=['ReleaseNotes','SearchTerm1','SearchTerm2','SearchTerm3'];data['keywordsValidated']=True
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    readme=OUT/'READ ME - review before upload.txt'
    text=readme.read_text(encoding='utf-8').replace('Release notes only:','Release notes and sorting search terms:').replace('description/keyword edits','description edits')
    text+='\nSearchTerm1–3 now contain the requested sorting searches in every language. SearchTerm4–7 are preserved from the saved export. Screenshots are being refreshed separately; English proposals require review before all-language capture.\n'
    readme.write_text(text,encoding='utf-8')
    print(f'Validated sorting keywords in {len(translations)} languages / {len(reports)} Store columns; descriptions and screenshots untouched.')

if __name__=='__main__':main()
