"""Encode native captures as PNG with identical decoded pixels; index completeness.

No resizing, cropping, overlays or translated screenshot text. Originals remain.
"""
import argparse
import hashlib
import html
import json
from pathlib import Path
from PIL import Image

parser=argparse.ArgumentParser()
parser.add_argument('root',type=Path)
args=parser.parse_args()
root=args.root.resolve()
project=Path(__file__).resolve().parents[1]
version=(project/'VERSION.txt').read_text(encoding='utf-8').strip()
languages=sorted(p.stem for p in (project/'locales').glob('*.json'))
layouts=['01-details-info','02-dual-previews','03-thumbnails','04-video-conversion']
records=json.loads((root/'capture-progress.json').read_text(encoding='utf-8'))
results=[]
for record in records:
    source=Path(record['path'])
    assert source.is_relative_to(root),source
    target=source.with_suffix('.png')
    with Image.open(source) as native:
        native.load()
        assert native.size==(1920,1032),(source,native.size)
        pixels=native.tobytes()
        mode=native.mode
        if target!=source:
            if target.exists():
                with Image.open(target) as existing:
                    existing.load()
                    assert existing.mode==mode and existing.tobytes()==pixels,target
            else:
                native.save(target,format='PNG')
    with Image.open(target) as encoded:
        encoded.load()
        assert encoded.format=='PNG' and encoded.size==(1920,1032)
        assert encoded.mode==mode and encoded.tobytes()==pixels,target
    results.append({**record,'png':str(target),'decodedPixelsIdentical':True,
                    'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
missing={code:[layout for layout in layouts if not any(r['language']==code and r['name']==layout for r in results)] for code in languages}
missing={code:value for code,value in missing.items() if value}
report={'captures':results,'completeLanguages':len(languages)-len(missing),
        'expectedLanguages':len(languages),'missing':missing,'uploaded':False,
        'visualReviewRequired':'Check every original at full size; completeness is not linguistic approval.'}
(root/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sections=[]
for code in languages:
    shots=[r for r in results if r['language']==code]
    if not shots:continue
    images=''.join(f'<a href="{html.escape(Path(r["png"]).relative_to(root).as_posix())}"><img src="{html.escape(Path(r["png"]).relative_to(root).as_posix())}" alt="{html.escape(r["name"])}"></a>' for r in shots)
    sections.append(f'<section><h2>{html.escape(code)}</h2>{images}</section>')
(root/'REVIEW.html').write_text('<!doctype html><meta charset="utf-8"><title>RFM '+html.escape(version)+' screenshots</title><style>body{font:16px system-ui;margin:30px}img{width:46%;margin:1%;border:1px solid #aaa}section{margin:30px 0}</style><h1>RFM '+html.escape(version)+' — genuine E: sample captures</h1><p>Maximized app, original 1920 × 1032 resolution, no taskbar. Nothing uploaded.</p>'+''.join(sections),encoding='utf-8')
print(json.dumps({'captures':len(results),'completeLanguages':report['completeLanguages'],'expectedLanguages':len(languages),'pixelChecksPassed':len(results),'uploaded':False}))
