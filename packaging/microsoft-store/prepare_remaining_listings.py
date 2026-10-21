"""Prepare local, reviewable Store copy. Never accesses Partner Center."""
from pathlib import Path
import hashlib
import html
from html.parser import HTMLParser
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'packaging/microsoft-store/prepared-12.6.1'
LANGUAGES = {
 'it':('Italian','it-it'), 'ar':('Arabic','ar-sa'), 'vi':('Vietnamese','vi-vn'),
 'uk':('Ukrainian','uk-ua'), 'no':('Norwegian','nb-no'), 'fi':('Finnish','fi-fi'),
 'da':('Danish','da-dk'), 'hu':('Hungarian','hu-hu'), 'ro':('Romanian','ro-ro'),
 'cs':('Czech','cs-cz'), 'pt-PT':('Portuguese (Portugal)','pt-pt'),
 'pt-BR':('Portuguese (Brazil)','pt-br'), 'tr':('Turkish','tr-tr'),
 'zh-TW':('Chinese (Traditional)','zh-hant'), 'ms':('Malay','ms-my'),
 'he':('Hebrew','he-il'), 'bn':('Bengali','bn-in'), 'ur':('Urdu','ur-pk'),
 'fa':('Persian','fa-ir'), 'sk':('Slovak','sk-sk'), 'hr':('Croatian','hr-hr'),
 'sr':('Serbian','sr-cyrl-rs'), 'ca':('Catalan','ca-es'),
 'et':('Estonian','et-ee'), 'lv':('Latvian','lv-lv'), 'lt':('Lithuanian','lt-lt')}

MASTER = {
 'shortDescription':'Rapidly scan, preview, sort, organise and convert large video and image collections.',
 'description': 'Resolution File Manager is a dual-pane media manager for large collections of videos and images.\n\nScan folders and subfolders, then sort and filter files by codec, resolution, file size, duration, frame rate, bitrate, date or file type. Select matching files across subfolders to copy, move or organise them together.\n\nQuickly browse multiple video files using independent previews, a seek slider, playback speeds up to 16× and side-by-side comparison. Switch between detailed file lists and cached thumbnails. Review duplicates before choosing which files to keep.\n\nConvert selected videos to H.264, H.265 or AV1, change resolution, create proxies or remux compatible files. Choose supported hardware encoding and decoding options. Originals are retained during conversion.\n\nUse Smart Collections, ratings, labels and tags to organise your library. Export media reports, check media integrity or create video contact sheets.\n\nMedia processing runs locally. No account is required. The app contains no advertising or analytics and does not upload your media or file metadata to the developer.',
 'releaseNotes':'Additional interface languages and expanded translated help documentation.',
 'features':[
  'Dual-pane browsing with independent video and image previews',
  'Scan and select media across folders and subfolders',
  'Sort and filter by codec, resolution, size, duration, FPS and more',
  'Rapid video seeking, adjustable playback speed and frame export',
  'Detailed media information and cached thumbnails',
  'Copy, move, rename and send selected files to the Recycle Bin',
  'Review duplicates and compare files side by side',
  'Smart Collections, ratings, labels and tags',
  'Batch video conversion with selectable hardware acceleration',
  'Media reports, integrity checks and video contact sheets',
  'Local media processing without an account, advertising or analytics'],
 'keywords':['media manager','video organiser','file manager','codec','resolution','thumbnails','duplicate finder']}

class Paragraphs(HTMLParser):
 def __init__(self): super().__init__(); self.values={}; self.current=None
 def handle_starttag(self,tag,attrs):
  if tag=='p':
   self.current=dict(attrs).get('id'); self.values[self.current]=''
 def handle_data(self,data):
  if self.current is not None: self.values[self.current]+=data
 def handle_endtag(self,tag):
  if tag=='p': self.current=None

def main():
 OUT.mkdir(exist_ok=True)
 (OUT/'english-copy-master.json').write_text(json.dumps(MASTER,ensure_ascii=False,indent=2),encoding='utf-8')
 fields=['shortDescription','description','releaseNotes']
 values=[MASTER[k] for k in fields]+MASTER['features']+MASTER['keywords']
 # Paragraphs split independently so structure survives translation exactly.
 pieces=[]; mapping=[]
 for value in values:
  indexes=[]
  for paragraph in value.split('\n\n'):
   indexes.append(len(pieces)); pieces.append(paragraph)
  mapping.append(indexes)
 source=''.join(f'<p id="f{i}">{html.escape(p)}</p>' for i,p in enumerate(pieces))
 digest=hashlib.sha256(source.encode()).hexdigest()
 for code in sys.argv[1:] or LANGUAGES:
  name,locale=LANGUAGES[code]; dest=OUT/code; dest.mkdir(exist_ok=True)
  cache=dest/'translated-copy-cache.json'
  if cache.exists() and (cached:=json.loads(cache.read_text(encoding='utf-8'))).get('sourceSha256')==digest:
   parsed=cached['paragraphs']
  else:
   chunks=[]; chunk=''
   for i,piece in enumerate(pieces):
    paragraph=f'<p id="f{i}">{html.escape(piece)}</p>'
    if len(chunk)+len(paragraph)>700:
     chunks.append(chunk); chunk=''
    chunk+=paragraph
   if chunk: chunks.append(chunk)
   child=subprocess.run(['pwsh','-NoProfile','-File',str(ROOT/'tools/help_translation_bridge.ps1'),'-Language',code],input=''.join(json.dumps({'text':chunk})+'\n' for chunk in chunks),text=True,encoding='utf-8',capture_output=True,timeout=150)
   responses=[json.loads(line) for line in child.stdout.splitlines() if line.startswith('{')]
   if len(responses)!=len(chunks) or any(not r.get('text') for r in responses): raise RuntimeError(f'{code}: translation unavailable; cached languages preserved')
   parser=Paragraphs()
   for result in responses: parser.feed(result['text'])
   parsed=parser.values
   if any(not parsed.get(f'f{i}','').strip() for i in range(len(pieces))): raise RuntimeError(f'{code}: missing translated paragraph')
   cache.write_text(json.dumps({'sourceSha256':digest,'paragraphs':parsed},ensure_ascii=False,indent=2),encoding='utf-8')
  translated=['\n\n'.join(parsed[f'f{i}'].strip() for i in indexes) for indexes in mapping]
  entry=dict(zip(fields,translated[:3])); entry['features']=translated[3:3+len(MASTER['features'])]; entry['keywords']=translated[3+len(MASTER['features']):]
  overrides=json.loads((OUT/'reviewed-copy-overrides.json').read_text(encoding='utf-8'))
  entry['keywords']=overrides['keywords'][code]
  def refine(value):
   if isinstance(value,list): return [refine(v) for v in value]
   for before,after in overrides.get('replacements',{}).get(code,{}).items(): value=value.replace(before,after)
   return value
  entry={key:refine(value) for key,value in entry.items()}
  flags=[]
  if len(entry['shortDescription'])>270: flags.append('shortDescription exceeds 270 characters')
  if any(len(v)>200 for v in entry['features']): flags.append('feature exceeds 200 characters')
  if any(len(v)>40 for v in entry['keywords']): flags.append('keyword exceeds 40 characters')
  if len(set(entry['keywords']))!=len(entry['keywords']): flags.append('duplicate keywords')
  if len(' '.join(entry['keywords']).split())>21: flags.append('keywords exceed 21 words')
  if any(translated[i]==values[i] for i in range(len(values)) if values[i] not in {'codec','resolution'}): flags.append('unchanged English text needs review')
  entry.update({'appLanguage':code,'languageName':name,'suggestedStoreLocale':locale,'productName':'Resolution File Manager','direction':'rtl' if code in {'ar','he','ur','fa'} else 'ltr','website':'https://johnperky.github.io/ResolutionFileManager/','support':'https://github.com/johnperky/ResolutionFileManager/issues','privacy':'https://johnperky.github.io/ResolutionFileManager/privacy.html','reviewStatus':'draft: linguistic and screenshot review required','validationFlags':flags})
  (dest/'listing.json').write_text(json.dumps(entry,ensure_ascii=False,indent=2),encoding='utf-8')
  print(code, 'prepared',flags,flush=True)

if __name__=='__main__':main()
