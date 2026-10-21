"""Freeze committed source/docs into preserved, verified release archives.

Run after committing the review evidence, before tagging and publication.
The external readiness gate binds exact asset hashes without putting a
self-referential source-ZIP hash inside that same source ZIP.
"""
import json
from pathlib import Path
import shutil
import subprocess
import zipfile
from project_snapshot import sha, snapshot
from verify_windows_package import main as verify

ROOT=Path(__file__).resolve().parents[1]


def main():
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip(), 'Commit intended source/evidence first'
    version=(ROOT/'VERSION.txt').read_text().strip()
    review_path=ROOT/f'docs/RELEASE_READINESS_{version}.json'
    review=json.loads(review_path.read_text())
    assert review['readyForRelease'] is True
    folder=ROOT/f'release-output/{version}'
    saved=folder/'preserved-before-final-source'
    assert not saved.exists(), 'Previous finalization exists; inspect and preserve it explicitly'
    saved.mkdir()
    portable=folder/f'ResolutionFileManager-{version}-Windows-x64'
    for name in ('README.md','WINDOWS_RELEASE.md',f'RELEASE_NOTES_{version}.md','LICENSE','THIRD_PARTY_NOTICES.md','PRIVACY.md','CHANGELOG.md'):
        shutil.copy2(ROOT/name,portable/name)
    source=folder/'committed-source-export'
    manifest=snapshot(source)
    for name,directory,prefix in ((f'ResolutionFileManager-{version}-Windows-x64.zip',portable,portable.name),
                                 (f'ResolutionFileManager-{version}-Source.zip',source,f'ResolutionFileManager-{version}-Source')):
        target=folder/name
        temporary=folder/(name+'.finalizing')
        with zipfile.ZipFile(temporary,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
            for path in sorted(directory.rglob('*')):
                if path.is_file():archive.write(path,prefix+'/'+path.relative_to(directory).as_posix())
        shutil.move(target,saved/name)
        temporary.replace(target)
    shutil.move(folder/'SHA256SUMS.txt',saved/'SHA256SUMS.txt')
    targets=sorted(folder.glob('*.zip'))+[folder/f'ResolutionFileManager-{version}.exe']
    (folder/'SHA256SUMS.txt').write_text(''.join(f'{sha(path)}  {path.name}\n' for path in sorted(targets)),encoding='ascii')
    report=verify()
    assert report['binarySha256']==review['binarySha256']
    assert report['sourceCommit']==manifest['git_head']
    gate={**review,'sourceCommit':manifest['git_head'],'assetsSha256':report['assetsSha256'],'reviewEvidenceSha256':sha(review_path)}
    (folder/'RELEASE_READINESS.json').write_text(json.dumps(gate,indent=2)+'\n')
    print('Exact reviewed archives frozen; publication gate written.',flush=True)


if __name__=='__main__':main()
