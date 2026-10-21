"""Resumable additive UI translation using existing locale terminology."""
import ast
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import json
from pathlib import Path
import re
import string
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import translate_help as t

ROOT=t.ROOT
TEMPLATES=[
    '{ready} file(s) ready · {unchanged} unchanged · {problems} problem(s)',
    'Start and padding must be whole numbers.',
    'Undo stopped because this file changed after transfer: {path}. The file was retained.',
    'Destination changed; retry: {target}',
    'Source','Destination','Status','[missing]',
    'Unchanged','Name cannot be empty','Name contains a forbidden character',
    'Name cannot end with a space or dot','Reserved Windows filename',
    'Duplicate output name','A file with this name already exists','Invalid template: {error}',
    '{count} files. Conflicts are reviewed before queuing. Replace keeps an undo backup for this session.',
    'Source: {source}\n\nDestination: {target}\n\nKeep both creates a numbered filename. Replace backs up the destination for session Undo.',
    'Current filename: {name}', 'New filename: {name}\n{status}',
    'Undo would overwrite an existing file: {target}. Both files were retained.',
    'Undo target is missing; recovery retained: {target}', 'Undo backup is missing: {backup}',
]

def prepare():
    path=ROOT/'locales/en.json'; en=json.loads(path.read_text(encoding='utf-8'))
    for filename in ('transfer_ui.py','transfer_engine.py'):
        tree=ast.parse((ROOT/filename).read_text(encoding='utf-8'))
        docs={id(n.value) for n in ast.walk(tree) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant)}
        for n in ast.walk(tree):
            if isinstance(n,ast.Constant) and isinstance(n.value,str) and id(n) not in docs:
                value=n.value
                if re.search('[A-Za-z]',value) and ((' ' in value and len(value)>3) or re.fullmatch('[A-Z][a-z]+',value)):
                    if '\\' not in value and not value.startswith(('.', '<', '__')) and len(value)<800:
                        en['literals'].setdefault(value,value)
    for value in TEMPLATES: en['literals'].setdefault(value,value)
    path.write_text(json.dumps(en,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return en

def fields(value):
    return sorted(f for _,f,_,_ in string.Formatter().parse(value) if f is not None)

def language(code,en,cache_only=False):
    path=ROOT/'locales'/f'{code}.json'; pack=json.loads(path.read_text(encoding='utf-8'))
    cache_path=ROOT/'.ui-translation-cache'/'12.7.3'/f'{code}.json'; cache_path.parent.mkdir(parents=True,exist_ok=True)
    cache=json.loads(cache_path.read_text(encoding='utf-8')) if cache_path.exists() else {}
    terms={value:pack['strings'][key] for key,value in en['strings'].items() if key in pack['strings'] and '{' not in value and len(value)>=4}
    terms.update({key:value for key,value in pack['literals'].items() if 4<=len(key)<110 and '{' not in key})
    pending=[]
    for section in ('strings','literals'):
        for key,value in en[section].items():
            if key not in pack[section]:
                if value in cache: pack[section][key]=cache[value]
                elif value in terms: pack[section][key]=terms[value]
                else: pending.append((section,key,value))
    groups=[]; group=[]; size=0
    for record in pending:
        if group and size+len(record[2])>2200: groups.append(group); group=[]; size=0
        group.append(record); size+=len(record[2])+30
    if group: groups.append(group)
    for group in groups:
        values=[r[2] for r in group]
        # Protect ALL Formatter fields, including attribute/format specifiers.
        protected_terms=dict(terms)
        for value in values:
            for field in re.findall(r'\{[^{}]+\}',value): protected_terms[field]=field
        combined='\n\n'.join(f'ZXQSEG{i:05d}QXZ\n{v}' for i,v in enumerate(values))
        try:
            translated=t.translate_text(combined,code,protected_terms)
            if re.findall(r'ZXQSEG(\d{5})QXZ',translated,re.I)!=[f'{i:05d}' for i in range(len(values))]: raise ValueError('segments')
            results=[v.strip() for v in re.split(r'ZXQSEG\d{5}QXZ',translated,flags=re.I)[1:]]
            if any(not v or fields(v)!=fields(s) for s,v in zip(values,results)): raise ValueError('fields')
        except ValueError:
            results=[t.translate_text(v,code,protected_terms).strip() for v in values]
        for (section,key,original),value in zip(group,results):
            if not value or fields(value)!=fields(original): raise ValueError(f'{code}: placeholder loss: {key}')
            if original.startswith('\n'): value='\n'+value.lstrip('\n')
            pack[section][key]=value; cache[original]=value
        cache_path.write_text(json.dumps(cache,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if not cache_only: path.write_text(json.dumps(pack,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'UI COMPLETE {code}: {len(pending)} new entries; existing translations retained',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--cache-only',action='store_true');args=parser.parse_args()
    en=prepare(); failures=[]
    with ThreadPoolExecutor(max_workers=6) as executor:
        jobs={executor.submit(language,c,en,args.cache_only):c for c in t.SUPPORTED_LANGUAGES if c!='en'}
        for future in as_completed(jobs):
            try: future.result()
            except Exception as exc: failures.append(jobs[future]); print(f'UI FAILED {jobs[future]}: {exc}',flush=True)
    if failures: raise SystemExit('Unfinished: '+','.join(failures))
