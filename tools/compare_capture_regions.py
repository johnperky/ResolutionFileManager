"""Reuse an earlier visual review only for proven identical decoded pixels."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image,ImageDraw

REGIONS={
    '01-details-info':{'headers':(0,24,1920,310),'info':(1615,310,1910,990)},
    '02-dual-previews':{'previews':(0,640,1920,1032)},
    '03-thumbnails':{'thumbnails':(0,310,960,990)},
    '04-video-conversion':{'conversionSettings':(437,140,1498,497)},
}


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main(previous,current):
    approved=json.loads((previous/'visual-review.json').read_text(encoding='utf-8'))
    assert approved['visualReviewComplete']
    old={(r['language'],r['view']):r for r in approved['captures']}
    rows=json.loads((current/'candidate-progress.json').read_text(encoding='utf-8'))
    results=[]
    for row in rows:
        key=(row['language'],row['view']);before=old[key]
        a=previous/row['file'];b=current/row['file']
        assert digest(a)==before['sha256'] and digest(b)==row['sha256']
        with Image.open(a) as aa,Image.open(b) as bb:
            aa=aa.convert('RGB');bb=bb.convert('RGB');assert aa.size==bb.size==(1920,1032)
            regions={name:{'identical':aa.crop(box).tobytes()==bb.crop(box).tobytes(),
                           'currentPixelSha256':hashlib.sha256(bb.crop(box).tobytes()).hexdigest(),'box':box}
                     for name,box in REGIONS[row['view']].items()}
        results.append({'language':key[0],'view':key[1],'previousSha256':before['sha256'],'currentSha256':row['sha256'],'regions':regions})
    output=current/'review-evidence';output.mkdir(exist_ok=True)
    report={'previousRoot':str(previous),'previousApprovalSha256':digest(previous/'visual-review.json'),'currentRoot':str(current),'comparisons':results,
            'identicalRegionCount':sum(r['identical'] for row in results for r in row['regions'].values()),'regionCount':sum(len(r['regions']) for r in results)}
    (output/'region-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    languages=sorted({r['language'] for r in rows});sheets=[]
    for start in range(0,len(languages),10):
        group=languages[start:start+10]
        sheet=Image.new('RGB',(1061,len(group)*110),'white');draw=ImageDraw.Draw(sheet)
        for index,code in enumerate(group):
            draw.text((4,index*110+2),code+' / CONVERSION STATUS AND ACTIONS - DIAGNOSTIC ONLY',fill='black')
            with Image.open(current/code/'04-video-conversion.png') as shot:sheet.paste(shot.crop((437,772,1498,862)),(0,index*110+20))
        path=output/f'conversion-actions-{start//10+1:02d}.png';sheet.save(path);sheets.append(str(path))
    print(json.dumps({'identicalRegions':report['identicalRegionCount'],'totalRegions':report['regionCount'],'actionSheets':sheets}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('previous',type=Path);parser.add_argument('current',type=Path)
    args=parser.parse_args();main(args.previous.resolve(),args.current.resolve())
