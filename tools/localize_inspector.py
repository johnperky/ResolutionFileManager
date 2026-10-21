"""Add only the six missing dynamic inspector terms; retain all existing UI/help."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import string
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import translate_help as t
from localization import SUPPORTED_LANGUAGES
t.PROVIDER='google'
TERMS={'inspector.channels':'{count} channel(s)',
       'inspector.pixel_format':'Pixel format','inspector.dynamic_range':'Dynamic range',
       'inspector.unknown':'Unknown','inspector.unrated':'Unrated',
       'inspector.unreadable':'Unreadable'}

def update(code):
    target=ROOT/'locales'/f'{code}.json'
    pack=json.loads(target.read_text(encoding='utf-8'))
    cache_path=ROOT/'.ui-translation-cache'/'12.7.5'/f'{code}.json'
    cache_path.parent.mkdir(parents=True,exist_ok=True)
    cache=json.loads(cache_path.read_text(encoding='utf-8')) if cache_path.exists() else {}
    pending=[(k,v) for k,v in TERMS.items() if k not in pack['strings']]
    results={}
    if code=='en':results=dict(pending)
    elif pending:
        missing=[(k,v) for k,v in pending if v not in cache]
        if missing:
            combined='\n\n'.join(f'ZXQSEG{i:05d}QXZ\n{v}' for i,(_,v) in enumerate(missing))
            translated=t.translate_text(combined,code,{'{count}':'{count}'})
            markers=re.findall(r'ZXQSEG(\d{5})QXZ',translated,re.I)
            if markers==[f'{i:05d}' for i in range(len(missing))]:
                values=[v.strip() for v in re.split(r'ZXQSEG\d{5}QXZ',translated,flags=re.I)[1:]]
            else:values=[t.translate_text(v,code,{'{count}':'{count}'}).strip() for _,v in missing]
            for (_,source),value in zip(missing,values):cache[source]=value
        results={k:cache[v] for k,v in pending}
    for key,value in results.items():
        assert value.strip(),(code,key)
        assert sorted(f for _,f,_,_ in string.Formatter().parse(value) if f)==sorted(f for _,f,_,_ in string.Formatter().parse(TERMS[key]) if f),(code,key,value)
        pack['strings'][key]=value
    cache_path.write_text(json.dumps(cache,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    target.write_text(json.dumps(pack,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return code

if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=6) as pool:
        for code in pool.map(update,SUPPORTED_LANGUAGES):print('Inspector terms ready: '+code,flush=True)
