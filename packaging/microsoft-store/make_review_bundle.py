"""Validate local listing fields and index real captures without modifying images."""
from pathlib import Path
import hashlib
import html
import json
import shutil
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from prepare_remaining_listings import LANGUAGES, OUT
from PIL import Image

VERSION=(HERE.parents[1]/'VERSION.txt').read_text(encoding='utf-8').strip()
CAPTURES=HERE.parents[2]/f'Store Preparation {VERSION}'

def main():
 CAPTURES.mkdir(exist_ok=True)
 records=[]; cards=[]
 for code,(name,locale) in LANGUAGES.items():
  original=OUT/code/'listing.json'
  folder=CAPTURES/name; folder.mkdir(exist_ok=True)
  problems=[]; images=[]
  entry=json.loads(original.read_text(encoding='utf-8')) if original.exists() else {}
  if entry:
   assert entry['appLanguage']==code
   for field in ('description','shortDescription','releaseNotes'):
    if not entry.get(field,'').strip(): problems.append(f'empty {field}')
   if len(entry['shortDescription'])>270: problems.append('shortDescription exceeds 270 characters')
   if not 1<=len(entry['features'])<=20 or any(not v.strip() or len(v)>200 for v in entry['features']): problems.append('invalid features')
   keys=entry['keywords']
   if not 1<=len(keys)<=7 or len(set(keys))!=len(keys) or any(not v.strip() or len(v)>40 for v in keys) or len(' '.join(keys).split())>21: problems.append('invalid keywords')
   problems+=entry.get('validationFlags',[])
   shutil.copy2(original,folder/'listing.json')
  else: problems.append('listing not prepared')
  candidates=sorted(folder.glob('*.png'))
  excluded=[]
  if code=='ar': excluded.append('02-thumbnails.png')
  if code=='pt-PT' and (folder/'02-thumbnails-wide.png').exists(): excluded.append('02-thumbnails-codec-sorting.png')
  for image in candidates:
   if image.name in excluded: continue
   with Image.open(image) as picture:
    assert picture.format=='PNG',f'Not a PNG: {image}'
    picture.verify()
   with Image.open(image) as picture: width,height=picture.size
   images.append({'path':str(image),'width':width,'height':height,'sha256':hashlib.sha256(image.read_bytes()).hexdigest()})
  if len(images)<3: problems.append(f'{3-len(images)} or more screenshots still required')
  problems.append('linguistic and visual approval pending')
  if code in ('fi','no','uk','ro','ms','bn','sk','sr'):
   problems.append('Some closed option selectors truncate long localized values; review original captures before approval')
  records.append({'appLanguage':code,'languageName':name,'suggestedStoreLocale':locale,'listingPath':str(original),'reviewListingPath':str(folder/'listing.json'),'screenshots':images,'excludedPreservedCaptures':excluded,'screenshotsComplete':len(images)>=3,'outstanding':problems,'uploadReady':False})
  esc=html.escape; direction=entry.get('direction','ltr')
  shots=''.join(f'<a href="{esc(name)}/{esc(Path(i["path"]).name)}"><img src="{esc(name)}/{esc(Path(i["path"]).name)}" alt="{esc(Path(i["path"]).stem)}"></a>' for i in images)
  copy=f'<h3>{esc(entry.get("shortDescription","Pending"))}</h3><p>{esc(entry.get("description","")).replace(chr(10),"<br>")}</p><ul>'+''.join(f'<li>{esc(v)}</li>' for v in entry.get('features',[]))+'</ul><p>'+esc('; '.join(entry.get('keywords',[])))+'</p><p>'+esc(entry.get('releaseNotes',''))+'</p>'
  cards.append(f'<section><h2>{esc(name)} ({esc(code)}) — {len(images)} captures</h2><p class="pending">Review draft — not upload-ready</p>{shots}<details><summary>Localized listing copy</summary><div lang="{esc(code)}" dir="{direction}">{copy}</div></details><ul>'+''.join(f'<li>{esc(v)}</li>' for v in problems)+'</ul></section>')
 report={'productId':'9NZL6GF5JSJK','applicationVersion':VERSION,'scope':'26 remaining application languages; preserve 17 existing listings and English India','storeChangesMade':False,'screenshotsComplete':all(r['screenshotsComplete'] for r in records),'uploadReady':False,'reviewNotes':['Original native-window PNGs, no taskbar, no image edits or resizing.','Details, thumbnail/codec sorting and selected-video conversion views in every language; extra dual-preview views in Italian and Arabic.','Visual inspection is not native-speaker linguistic approval.','Two superseded captures preserved but excluded from selected upload candidates.'],'packageBlocker':'Existing MSIX 12.5.2.0 differs from current EXE; new package and language validation required before upload','entries':records}
 (CAPTURES/'submission-preparation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 page='<!doctype html><meta charset="utf-8"><title>RFM Store preparation review</title><style>body{font:16px system-ui;max-width:1500px;margin:30px auto;padding:20px;background:#f3f5f8;color:#17202b}section{background:white;padding:22px;margin:22px 0;border:1px solid #ccd5df;border-radius:12px}img{width:31%;height:auto;margin:1%;border:1px solid #aaa}.pending{color:#984900;font-weight:600}details{margin-top:15px}summary{cursor:pointer}p{line-height:1.6}</style><h1>Resolution File Manager — Store preparation review</h1><p>26 remaining languages. Nothing uploaded or submitted. Capture files are genuine unmodified native screenshots; click to open the original PNG at its original resolution. Every language has details, thumbnails/sorting and conversion views. Listings and screenshots await your approval. Minor selector text-fit concerns are noted per language. A new validated Store package is still required.</p>'+''.join(cards)
 (CAPTURES/'REVIEW.html').write_text(page,encoding='utf-8')
 print(json.dumps({'languages':len(records),'listingDrafts':sum(bool((OUT/code/'listing.json').exists()) for code in LANGUAGES),'captures':sum(len(r['screenshots']) for r in records),'uploadReady':False},indent=2))

if __name__=='__main__':main()
