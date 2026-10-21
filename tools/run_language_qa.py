"""Run isolated Help and new-control checks with bounded two-process concurrency."""
from concurrent.futures import ThreadPoolExecutor,as_completed
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from localization import SUPPORTED_LANGUAGES

def language(code):
    result={'language':code}
    for name,script in (('help_and_browsing','smoke_test_gui.py'),('upgrade_controls','test_upgrade_languages.py')):
        child=subprocess.run([sys.executable,str(ROOT/'tools'/script),'--single',code],capture_output=True,text=True,encoding='utf-8',timeout=120)
        if child.returncode: result[name]={'passed':False,'error':child.stderr[-3500:]}
        else: result[name]=json.loads(child.stdout.strip().splitlines()[-1])
    result['passed']=all(result[key]['passed'] for key in ('help_and_browsing','upgrade_controls'))
    return result

if __name__=='__main__':
    results=[]
    with ThreadPoolExecutor(max_workers=2) as executor:
        jobs={executor.submit(language,code):code for code in SUPPORTED_LANGUAGES}
        for job in as_completed(jobs):
            try: result=job.result()
            except Exception as exc: result={'language':jobs[job],'passed':False,'error':str(exc)}
            results.append(result);print(json.dumps(result,ensure_ascii=True),flush=True)
            (ROOT/'docs/LANGUAGE_QA_12.7.3.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if not all(result['passed'] for result in results): raise SystemExit(1)
