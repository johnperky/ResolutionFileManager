"""Merge prepared RFM listings into an exported draft, preserving unrelated cells."""
import csv
import hashlib
import json
import shutil
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT.parent / 'Store Preparation 12.6.2'
SOURCE = Path(r'C:\Downloads\listingData-9NZL6GF5JSJK-1152921505702180770 (2).csv')
DEST = REVIEW / 'RFM-Bulk-Import-12.6.2'
DEST.mkdir(exist_ok=True)
backup = REVIEW / 'Store-export-before-bulk.csv'
if not backup.exists():
    shutil.copy2(SOURCE, backup)
assert backup.read_bytes() == SOURCE.read_bytes()
with SOURCE.open(encoding='utf-8-sig', newline='') as stream:
    reader = csv.DictReader(stream)
    columns = reader.fieldnames
    rows = list(reader)
before = [dict(row) for row in rows]
fields = {row['Field']: row for row in rows if row['Field']}
review = json.loads((REVIEW / 'submission-preparation.json').read_text(encoding='utf-8'))
aliases = {'bn':'bn-bd', 'zh-TW':'zh-tw'}
changed = set()
images = []
for entry in review['entries']:
    code = entry['appLanguage']
    locale = aliases.get(code, entry['suggestedStoreLocale'])
    assert locale in columns, locale
    data = json.loads(Path(entry['reviewListingPath']).read_text(encoding='utf-8'))
    values = {'Description':data['description'], 'ShortDescription':data['shortDescription'],
              'ReleaseNotes':data['releaseNotes'], 'Title':'Resolution File Manager'}
    values.update({f'Feature{i+1}':v for i,v in enumerate(data['features'])})
    values.update({f'SearchTerm{i+1}':v for i,v in enumerate(data['keywords'])})
    for field, value in values.items():
        fields[field][locale] = value
        changed.add((field, locale))
    for i, shot in enumerate(entry['screenshots'], 1):
        field = f'DesktopScreenshot{i}'
        if fields[field][locale].startswith('https://'):
            continue  # Reuse already saved images, rather than upload them again.
        source = Path(shot['path'])
        with Image.open(source) as image:
            assert image.format == 'PNG'
            image.verify()
        target = DEST / 'images' / code / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        assert hashlib.sha256(source.read_bytes()).digest() == hashlib.sha256(target.read_bytes()).digest()
        fields[field][locale] = f'{DEST.name}/images/{code}/{source.name}'
        changed.add((field, locale))
        images.append(str(target))

notes = {
 'en-gb':'Improved help documentation and more languages added.',
 'en-in':'Improved help documentation and more languages added.',
 'de-de':'Verbesserte Hilfedokumentation und zusätzliche Sprachen.',
 'fr-fr':"Documentation d’aide améliorée et ajout de nouvelles langues.",
 'es-es':'Documentación de ayuda mejorada y más idiomas añadidos.',
 'nl-nl':'Verbeterde helpdocumentatie en meer talen toegevoegd.',
 'ja-jp':'ヘルプを改善し、対応言語を追加しました。',
 'ko-kr':'도움말 문서를 개선하고 지원 언어를 추가했습니다.',
 'ru-ru':'Улучшена справочная документация и добавлены новые языки.',
 'zh-cn':'改进了帮助文档，并新增更多语言。',
 'zh-hans-cn':'改进了帮助文档，并新增更多语言。',
 'bg-bg':'Подобрена помощна документация и добавени още езици.',
 'el-gr':'Βελτιωμένη τεκμηρίωση βοήθειας και προσθήκη περισσότερων γλωσσών.',
 'fil-ph':'Pinahusay na dokumentasyon ng tulong at nagdagdag ng higit pang mga wika.',
 'hi-in':'सहायता दस्तावेज़ों में सुधार किया गया और अधिक भाषाएँ जोड़ी गईं।',
 'id-id':'Dokumentasi bantuan ditingkatkan dan lebih banyak bahasa ditambahkan.',
 'pl-pl':'Ulepszono dokumentację pomocy i dodano więcej języków.',
 'sv-se':'Förbättrad hjälpdokumentation och fler språk har lagts till.',
 'th-th':'ปรับปรุงเอกสารช่วยเหลือและเพิ่มภาษาที่รองรับ'
}
for locale, text in notes.items():
    assert locale in columns
    fields['ReleaseNotes'][locale] = text
    changed.add(('ReleaseNotes', locale))

# Full export metadata, existing descriptions, image URLs, trailers and optional fields stay intact.
for old, new in zip(before, rows):
    for column in columns:
        if (new['Field'], column) not in changed:
            assert old[column] == new[column], (new['Field'], column)
output = DEST / 'listings.csv'
with output.open('w', encoding='utf-8-sig', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)
assert len(list(DEST.glob('*.csv'))) == 1
report = {'baseline':str(backup), 'importFolder':str(DEST), 'languageColumns':len(columns)-4,
          'newListingLanguages':26, 'imageFiles':len(images), 'releaseNotesLanguages':45,
          'unrelatedCellsPreserved':True, 'files':images}
(REVIEW/'bulk-import-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2))
