"""Validate batch candidates and make diagnostic review sheets, never Store assets."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageStat


def review(root):
    rows = json.loads((root/'candidate-progress.json').read_text(encoding='utf-8'))
    proof = json.loads((root/'provenance.json').read_text(encoding='utf-8'))
    output = root/'review-evidence'
    output.mkdir(exist_ok=True)
    checked = []
    seen = set()
    for row in rows:
        path = (root/row['file']).resolve()
        assert path.is_relative_to(root.resolve()), path
        assert row['binarySha256'] == proof['binarySha256']
        assert row['sourceSha256'] == proof['sourceSha256']
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        assert digest == row['sha256'], path
        with Image.open(path) as image:
            assert image.format == 'PNG' and image.size == (1920, 1032), path
            image.load()
            regions = []
            if row['view']=='02-dual-previews':
                regions = [(390,640,540,900),(1100,650,1750,900)]
            elif row['view']=='03-thumbnails':
                regions = [(30,370,740,880)]
            for region in regions:
                assert max(ImageStat.Stat(image.crop(region).convert('RGB')).stddev)>15, f'Empty/flat media: {path}'
            pixels = hashlib.sha256(image.convert('RGB').tobytes()).hexdigest()
            assert pixels not in seen, f'Duplicate capture: {path}'
            seen.add(pixels)
        checked.append({'language': row['language'], 'view': row['view'], 'sha256': digest, 'pixelSha256': pixels})
    languages = sorted({row['language'] for row in rows})
    pages = []
    for start in range(0, len(languages), 3):
        codes = languages[start:start+3]
        sheet = Image.new('RGB', (2560, len(codes)*370), 'white')
        draw = ImageDraw.Draw(sheet)
        for y, code in enumerate(codes):
            for x, row in enumerate(sorted((r for r in rows if r['language']==code), key=lambda r:r['view'])):
                draw.text((x*640+5, y*370+5), f'{code} / {row["view"]} - DIAGNOSTIC ONLY', fill='black')
                with Image.open(root/row['file']) as image:
                    sheet.paste(image.resize((640,344), Image.Resampling.LANCZOS), (x*640,y*370+25))
        page = output/f'overview-{start//3+1:02d}.jpg'
        sheet.save(page, quality=94)
        pages.append(str(page))
    # Native-size control strips keep small labels readable while reviewing
    # many locales. Originals remain untouched; these are diagnostic sheets.
    control_pages = []
    for start in range(0,len(languages),4):
        codes = languages[start:start+4]
        sheet = Image.new('RGB',(1920,len(codes)*335),'white')
        draw = ImageDraw.Draw(sheet)
        for y,code in enumerate(codes):
            draw.text((5,y*335+3),code+' / MAIN CONTROLS AT ORIGINAL PIXEL SIZE',fill='black')
            with Image.open(root/code/'01-details-info.png') as image:
                sheet.paste(image.crop((0,0,1920,310)),(0,y*335+25))
        path = output/f'controls-{start//4+1:02d}.png'
        sheet.save(path)
        control_pages.append(str(path))
    preview_rows = [row for row in rows if row['view']=='02-dual-previews']
    preview_pages = []
    for start in range(0,len(preview_rows),4):
        group = preview_rows[start:start+4]
        sheet = Image.new('RGB',(1920,602),'white')
        draw = ImageDraw.Draw(sheet)
        for index,row in enumerate(group):
            x,y = (index%2)*960,(index//2)*301
            draw.text((x+5,y+3),row['language']+' / FINAL PREVIEWS - DIAGNOSTIC ONLY',fill='black')
            with Image.open(root/row['file']) as image:
                sheet.paste(image.crop((0,480,1920,1032)).resize((960,276),Image.Resampling.LANCZOS),(x,y+25))
        path = output/f'previews-{start//4+1:02d}.png'
        sheet.save(path)
        preview_pages.append(str(path))
    visual_path = root/'visual-review.json'
    visual = json.loads(visual_path.read_text(encoding='utf-8')) if visual_path.exists() else {}
    reviewed = (visual.get('visualReviewComplete',False) and
                {(r['language'],r['view'],r['sha256']) for r in checked} ==
                {(r['language'],r['view'],r['sha256']) for r in visual.get('captures',[])})
    report = {'count':len(checked), 'expected':43*4, 'completeLanguages':sum(sum(r['language']==c for r in rows)==4 for c in languages),
              'binarySha256':proof['binarySha256'], 'checks':checked, 'overviewPages':pages, 'controlPages':control_pages, 'previewPages':preview_pages,
              'visualReviewComplete':reviewed, 'readyForRelease':False}
    (output/'integrity.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path)
    review(parser.parse_args().root.resolve())
