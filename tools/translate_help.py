"""Resumable Help-only translation. Existing UI dictionaries are never changed."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import html
import json
import re
import sys
import threading
import subprocess
import time
import urllib.parse
import urllib.request
import http.cookiejar
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from localization import RTL_LANGUAGES, SUPPORTED_LANGUAGES

LOCK = threading.Lock()
LOCAL = threading.local()
PROVIDER = "bing"
REFRESH = set()
STOP = threading.Event()
SERVICE = {"zh-CN":"zh-CN", "zh-TW":"zh-TW", "no":"no", "pt-PT":"pt-PT", "pt-BR":"pt-BR", "he":"iw", "fil":"tl"}

def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def request_translation(text, code):
    if STOP.is_set(): raise RuntimeError("translation service rate limit; retry later")
    if PROVIDER=="bing": return request_bing(text,code)
    query = urllib.parse.urlencode({"client":"gtx","sl":"en","tl":SERVICE.get(code,code),"dt":"t","q":text})
    for attempt in range(5):
        try:
            req = urllib.request.Request("https://translate.googleapis.com/translate_a/single?"+query, headers={"User-Agent":"Mozilla/5.0"})
            data = json.load(urllib.request.urlopen(req, timeout=45))
            value = "".join(part[0] for part in data[0] if part[0])
            if not value.strip(): raise ValueError("empty translation")
            return value
        except urllib.error.HTTPError as error:
            if error.code==429:
                STOP.set()
                raise
            if attempt==4: raise
            time.sleep(2+attempt)
        except Exception:
            if attempt == 4: raise
            time.sleep(min(8, 1+attempt*2))

def request_bing(text,code):
    if sys.platform=="win32":
        if not hasattr(LOCAL,"bridge") or LOCAL.bridge_code!=code:
            if hasattr(LOCAL,"bridge"): LOCAL.bridge.stdin.close(); LOCAL.bridge.wait(timeout=5)
            LOCAL.bridge=subprocess.Popen(["pwsh","-NoProfile","-File",str(ROOT/"tools/help_translation_bridge.ps1"),"-Language",code],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding="utf-8")
            LOCAL.bridge_code=code
        LOCAL.bridge.stdin.write(json.dumps({"text":text},ensure_ascii=False)+"\n"); LOCAL.bridge.stdin.flush()
        line=LOCAL.bridge.stdout.readline()
        if not line: raise ValueError("Help translation bridge stopped")
        response=json.loads(line)
        if "error" in response: raise ValueError(response["error"])
        return response["text"]
    if not hasattr(LOCAL,"bing"):
        opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        page=opener.open("https://www.bing.com/translator",timeout=40).read().decode()
        key,token=re.search(r'params_AbusePreventionHelper = \[(\d+),"([^"]+)"',page).groups()
        ig=re.search(r'IG:"([A-F0-9]+)"',page).group(1)
        iid=re.search(r'data-iid="([^"]+)"',page).group(1)
        LOCAL.bing=(opener,key,token,ig,iid)
    opener,key,token,ig,iid=LOCAL.bing
    target={"no":"nb","pt-BR":"pt","zh-CN":"zh-Hans","zh-TW":"zh-Hant","sr":"sr-Cyrl"}.get(code,code)
    body=urllib.parse.urlencode({"fromLang":"en","to":target,"text":html.escape(text),"token":token,"key":key,"textType":"html"}).encode()
    req=urllib.request.Request(f"https://www.bing.com/ttranslatev3?isVertical=1&IG={ig}&IID={urllib.parse.quote(iid)}",data=body)
    try:
        result=json.load(opener.open(req,timeout=45))
    except urllib.error.HTTPError as error:
        if error.code==429: STOP.set()
        raise
    if isinstance(result,dict):
        if result.get("statusCode")==429: STOP.set()
        raise ValueError(f"Bing translation failed: {result}")
    time.sleep(.2)
    return html.unescape(result[0]["translations"][0]["text"])

def protect(text, terms):
    replacements = {}
    # Exact UI terminology comes from the existing locale, not a new UI translation.
    patterns = sorted(terms, key=len, reverse=True)
    technical = r"\[chapter:[a-z_]+\]|\{[A-Za-z_][A-Za-z_0-9]*\}|https?://[^\s]+|F:\\Resolution File Manager project\\ResolutionFileManager-Project-v6|Ctrl(?:\+(?:Shift|Alt))*\+[A-Za-z]|F[235]|FFmpeg|FFprobe|FFplay|SQLite|[A-Za-z_][A-Za-z_0-9.-]*\.(?:py|json|ps1|sh|txt|md|exe)"
    pattern = re.compile(technical + ("|"+"|".join(re.escape(p) for p in patterns) if patterns else ""))
    def replace(match):
        token = f"ZXQKEEP{len(replacements):05d}QXZ"
        value = match.group(0)
        replacements[token] = terms.get(value,value)
        return token
    return pattern.sub(replace,text), replacements

def unprotect(text, replacements):
    for token,value in replacements.items():
        pattern = re.escape(token)
        if len(re.findall(pattern,text,flags=re.I)) != 1:
            raise ValueError(f"translation damaged protected token {token}")
        def restore(match):
            left=bool(value) and value[0].isalnum() and match.start()>0 and text[match.start()-1].isalnum()
            right=bool(value) and (value[-1].isalnum() or value[-1]=="…") and match.end()<len(text) and text[match.end()].isalnum()
            return (" " if left else "")+value+(" " if right else "")
        text = re.sub(pattern,restore,text,flags=re.I)
    if "ZXQKEEP" in text.upper(): raise ValueError("unresolved protected marker")
    return text

def translate_text(text, code, terms):
    prepared,replacements=protect(text,terms)
    try:
        return unprotect(request_translation(prepared,code),replacements)
    except ValueError:
        # Never guess a corrupted protected token. Translate surrounding prose
        # separately and insert the verified UI/reference text locally.
        parts=re.split(r"(ZXQKEEP\d{5}QXZ)",prepared)
        output=[]
        for part in parts:
            if part in replacements: output.append(replacements[part])
            elif not any(c.isalpha() for c in part): output.append(part)
            else: output.append(request_translation(part,code))
        return "".join(output)

def translate_language(code, master, master_hash, english):
    path = ROOT / "locales" / f"{code}.json"
    pack = json.loads(path.read_text(encoding="utf-8"))
    ui_hash = digest(json.dumps([pack["strings"],pack.get("literals",{})],ensure_ascii=False,sort_keys=True))
    terms = {}
    for key, value in english["strings"].items():
        translated = pack["strings"].get(key)
        if translated and len(value)>=5 and "{" not in value:
            terms.setdefault(value,translated)
    for key, value in pack.get("literals",{}).items():
        if len(key)>=5 and len(key)<110 and "{" not in key: terms.setdefault(key,value)
    cache_dir = ROOT / ".help-translation-cache" / master_hash
    cache_dir.mkdir(parents=True,exist_ok=True)
    cache_path = cache_dir / (f"{code}-regional.json" if code in {"pt-PT","pt-BR"} else f"{code}.json")
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    # Reuse matching paragraphs across master revisions, never a previous short
    # chapter merely because its chapter count happens to match.
    for previous in (ROOT/".help-translation-cache").glob("*/"+cache_path.name):
        prior=json.loads(previous.read_text(encoding="utf-8"))
        for key,value in prior.items(): cache.setdefault(key,value)
    records=[]
    for chapter in master["chapters"]:
        records.append((chapter["id"]+".title",chapter["title"]))
        records.extend((p["id"],p["text"]) for p in chapter["paragraphs"])
    # Prefer already reviewed locale paragraphs over older machine caches.
    # Hash matching also reuses unchanged prose moved to a different chapter.
    existing = {p.get("source_sha256"): p["text"]
                for c in pack.get("help",{}).get("chapters",[])
                for p in c.get("paragraphs",[]) if p.get("source_sha256") and p.get("text")}
    for key,text in records:
        source_hash=digest(text)
        if source_hash in existing and key not in REFRESH:
            cache[key]={"source_sha256":source_hash,"text":existing[source_hash]}
    pending=[(key,text) for key,text in records if key not in cache or cache[key].get("source_sha256")!=digest(text) or key in REFRESH]
    # Translate each paragraph independently: separators cannot merge or omit content.
    groups=[]; group=[]; size=0
    for record in pending:
        estimated=len(protect(record[1],terms)[0])+30
        if group and size+estimated>2800:
            groups.append(group); group=[]; size=0
        group.append(record); size+=estimated
    if group: groups.append(group)
    completed=0
    for group in groups:
        combined="\n\n".join(f"ZXQSEG{i:05d}QXZ\n{text}" for i,(_key,text) in enumerate(group))
        # Markers enforce one-to-one paragraph correspondence; any service
        # merge, omission or reordering falls back to individual paragraphs.
        prepared,replacements=protect(combined,terms)
        try:
            translated=unprotect(request_translation(prepared,code),replacements)
            markers=re.findall(r"ZXQSEG(\d{5})QXZ",translated,flags=re.I)
            if markers!=[f"{i:05d}" for i in range(len(group))]: raise ValueError("paragraph separator changed")
            chunks=re.split(r"ZXQSEG\d{5}QXZ",translated,flags=re.I)[1:]
            values=[c.strip() for c in chunks]
            if any(not v for v in values): raise ValueError("empty translated paragraph")
        except ValueError:
            values=[translate_text(text,code,terms) for _key,text in group]
        for (key,text),translated in zip(group,values):
            cache[key]={"source_sha256":digest(text),"text":translated}
        temp_cache=cache_path.with_suffix(".tmp")
        temp_cache.write_text(json.dumps(cache,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        temp_cache.replace(cache_path)
        completed+=len(group)
        with LOCK: print(f"{code}: {completed}/{len(pending)} paragraphs/titles",flush=True)
    chapters=[]
    for source in master["chapters"]:
        paragraphs=[{"id":p["id"],**cache[p["id"]]} for p in source["paragraphs"]]
        chapters.append({"id":source["id"],"title":cache[source["id"]+".title"]["text"],"paragraphs":paragraphs,"body":"\n\n".join(p["text"] for p in paragraphs)})
    pack["help"]={"schema":2,"master_sha256":master_hash,"direction":"rtl" if code in RTL_LANGUAGES else "ltr","translation_method":"machine translation with existing UI glossary; human linguistic review pending","chapters":chapters}
    assert digest(json.dumps([pack["strings"],pack.get("literals",{})],ensure_ascii=False,sort_keys=True))==ui_hash
    temporary=path.with_suffix(".help.tmp")
    temporary.write_text(json.dumps(pack,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    temporary.replace(path)
    with LOCK: print(f"COMPLETE {code}: {len(chapters)} chapters, UI unchanged",flush=True)
    return code

def main():
    global PROVIDER, REFRESH
    parser=argparse.ArgumentParser()
    parser.add_argument("languages",nargs="*")
    parser.add_argument("--workers",type=int,default=8)
    parser.add_argument("--provider",choices=("bing","google"),default="bing")
    parser.add_argument("--refresh-paragraph",action="append",default=[])
    args=parser.parse_args()
    PROVIDER=args.provider
    REFRESH=set(args.refresh_paragraph)
    raw=(ROOT/"docs/help/en.json").read_text(encoding="utf-8")
    master=json.loads(raw)
    english=json.loads((ROOT/"locales/en.json").read_text(encoding="utf-8"))
    codes=args.languages or [c for c in SUPPORTED_LANGUAGES if c!="en"]
    failures=[]
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        jobs={executor.submit(translate_language,c,master,digest(raw),english):c for c in codes}
        for job in as_completed(jobs):
            try: job.result()
            except Exception as error:
                failures.append(jobs[job]); print(f"FAILED {jobs[job]}: {error}",flush=True)
    if failures: raise SystemExit("Retry: python tools/translate_help.py "+" ".join(failures))

if __name__=="__main__": main()
