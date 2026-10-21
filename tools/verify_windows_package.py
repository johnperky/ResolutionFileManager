"""Check release checksums, exact portable bytes, source and licence contents."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile
from PyInstaller.archive.readers import CArchiveReader

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    version=(ROOT/'VERSION.txt').read_text().strip()
    release=ROOT/f'release-output/{version}'
    binary=ROOT/f'dist/multilingual-review-{version}/ResolutionFileManager-v{version}-Multilingual-Review.exe'
    digest=sha(binary)
    for line in (release/'SHA256SUMS.txt').read_text().splitlines():
        expected,name=line.split('  ',1)
        assert sha(release/name)==expected,name
    assert sha(release/f'ResolutionFileManager-{version}.exe')==digest
    prefix=f'ResolutionFileManager-{version}-Windows-x64/'
    with zipfile.ZipFile(release/f'ResolutionFileManager-{version}-Windows-x64.zip') as archive:
        assert archive.testzip() is None
        with archive.open(prefix+f'ResolutionFileManager-{version}.exe') as stream:
            assert hashlib.file_digest(stream,'sha256').hexdigest()==digest
        required=['LICENSE','THIRD_PARTY_NOTICES.md','PRIVACY.md',f'RELEASE_NOTES_{version}.md','licenses/ffmpeg/LICENSE','licenses/ffmpeg/README.txt',
                  *['licenses/python-components/'+name+'.txt' for name in ('Python','Tcl-Tk','Pillow','Send2Trash','watchdog','tkinterdnd2','PyInstaller','arabic-reshaper','python-bidi','python-bidi-GPL','six')]]
        for name in required:assert len(archive.read(prefix+name))>100,name
        portable_files=len(archive.namelist())
    prefix=f'ResolutionFileManager-{version}-Source/'
    with zipfile.ZipFile(release/f'ResolutionFileManager-{version}-Source.zip') as archive:
        assert archive.testzip() is None
        names=archive.namelist()
        manifest=json.loads(archive.read(prefix+'SOURCE_MANIFEST.json'))
        head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        assert manifest['git_head']==head, 'Source export is from a different commit'
        for name,expected in manifest['files'].items():
            assert hashlib.sha256(archive.read(prefix+name)).hexdigest()==expected,name
        for name in names:
            normal=name.replace('\\','/')
            assert not any(part in normal.split('/') for part in ('.git','__pycache__','.venv','release-output','dist'))
            assert not normal.endswith(('settings.json','.sqlite3','.env'))
            if normal.endswith('.py'):compile(archive.read(name),normal,'exec')
        for name in ('VERSION.txt','media_sorter.py','transfer_engine.py','transfer_ui.py','localization.py','rtl_display.py','reminder_policy.py',*[f'locales/{p.name}' for p in (ROOT/'locales').glob('*.json')]):
            assert archive.read(prefix+name)==(ROOT/name).read_bytes(),name
        source_files=sum(not n.endswith('/') for n in names)
    frozen=CArchiveReader(str(binary))
    tool_hashes={}
    for name in ('ffmpeg','ffprobe','ffplay'):
        installed=Path(subprocess.check_output(['where.exe',name],text=True).splitlines()[0])
        bundled=hashlib.sha256(frozen.extract(name+'.exe')).hexdigest()
        assert bundled==sha(installed),name+' differs from verified installed tool'
        tool_hashes[name]=bundled
    targets=[f'ResolutionFileManager-{version}.exe',f'ResolutionFileManager-{version}-Windows-x64.zip',f'ResolutionFileManager-{version}-Source.zip','SHA256SUMS.txt']
    report={'version':version,'binarySha256':digest,'sourceCommit':head,'assetsSha256':{name:sha(release/name) for name in targets},'portableExactBinary':True,'checksumsValid':True,'zipIntegrity':True,'sourceModulesAnd43LocalesMatch':True,'sourcePythonCompiles':True,'privateSettingsExcluded':True,'portableFiles':portable_files,'sourceFiles':source_files,'licenceFilesVerified':len(required),'bundledMediaToolsMatchInstalled':tool_hashes,'passed':True}
    (release/'PACKAGE_VERIFIED.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)
    return report


if __name__=='__main__':main()
