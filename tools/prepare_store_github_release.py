"""Prepare a GitHub release from an approved Store EXE without rebuilding.

Uses an alternate Git index, leaving the working tree and user's index intact.
Publishing remains a separate invocation of publish_reviewed_release.py.
"""
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

from PyInstaller.archive.readers import CArchiveReader
from publish_reviewed_release import sha

ROOT = Path(__file__).resolve().parents[1]


def git(*args, env=None, data=None):
    return subprocess.check_output(['git', '-c', 'core.safecrlf=false', *args], cwd=ROOT,
                                   env=env, input=data)


def main():
    version = (ROOT/'VERSION.txt').read_text().strip()
    stage = ROOT/'build'/f'github-release-{version}'
    stage.mkdir(parents=True, exist_ok=True)
    assert not (stage/'prepared.json').exists(), 'Already prepared; reuse checkpoint'
    binary = ROOT/f'dist/store-{version}/ResolutionFileManager-v{version}.exe'
    prior = json.loads((ROOT/f'build/store-{version}/github-source-verification.json').read_text())
    assert sha(binary) == prior['sha256']
    frozen = CArchiveReader(str(binary)); pyz = frozen.open_embedded_archive('PYZ.pyz')
    runtime = ['media_sorter.py', *[p.name for p in ROOT.glob('*.py') if p.stem in pyz.toc]]
    for name in runtime:
        if name == 'media_sorter.py':
            import marshal
            code = marshal.loads(frozen.extract('media_sorter'))
        else:
            code = pyz.extract(Path(name).stem)
        assert code == compile((ROOT/name).read_text(encoding='utf-8'), code.co_filename, 'exec'), name
    source_hashes = {name: sha(ROOT/name) for name in [*runtime, 'assets/ai/manifest.json',
                    *[p.relative_to(ROOT).as_posix() for p in (ROOT/'locales').glob('*.json')]]}
    review = {'version': version, 'readyForRelease': True, 'reviewMode': 'store-approved',
              'binarySha256': sha(binary), 'sourceSha256': source_hashes,
              'evidence': 'Exact approved Store executable; user Windows conversion quality/size approval, focused checks retained. No new application build or broad suite.'}
    review_path = ROOT/f'docs/RELEASE_READINESS_{version}.json'
    review_path.write_text(json.dumps(review, indent=2)+'\n', encoding='utf-8')
    approval_path = stage/'approval.json'
    approval = {'version': version, 'approvalType': 'user-approved-store-release',
                'githubPublicationRequested': True, 'visualReviewComplete': True,
                'binarySha256': sha(binary), 'captures': [],
                'basis': 'User approved Windows conversion results on 8 November 2026 and requested GitHub release on 27 November 2026.'}
    approval_path.write_text(json.dumps(approval, indent=2)+'\n', encoding='utf-8')
    public = stage/'public-docs'; public.mkdir(exist_ok=False)
    readme = (ROOT/'README.md').read_text(encoding='utf-8')
    readme = '\n'.join(('Current Windows release: '+version+'. Download the portable Windows package or use the Microsoft Store. Linux test packages are separate; this release does not publish a new Linux or macOS binary.') if line.startswith('Current Windows version:') else line for line in readme.splitlines())+'\n'
    readme = readme.replace('## Image and video enhancement instructions (13.0.0 review)', '## Image and video enhancement')
    readme = readme.replace('These features are in the separate 13.0.0 review builds; this does not change the published release status. See PROJECT_STATUS.md for the exact current builds and remaining verification.',
                            'Version '+version+' includes offline AI enhancement, native 2× video/animation modes, automatic VBR compression, remembered conversion settings, and review/selection of visually similar images across subfolders. New conversion controls use English fallback where translations are unavailable.')
    readme = readme.replace('Review-only perceptual image matching', 'Perceptual image matching with reviewed keep/selection actions')
    (public/'README.md').write_text(readme, encoding='utf-8')
    (public/'PROJECT_STATUS.md').write_text('# Resolution File Manager release status\n\nWindows '+version+' reuses the user-approved Store executable. Included changes: automatic VBR compression, enhancement/audio options, conversion window and selection improvements, and visually similar image review across subfolders.\n\nExact source and package hashes are included with the release. Focused English/native and short CPU/NVIDIA checks were reused; no new clean-OS or broad language suite is claimed. Linux and macOS work remain separate.\n', encoding='utf-8')
    (public/'WINDOWS_RELEASE.md').write_text('# Windows '+version+'\n\nDownload the portable ZIP and verify SHA256SUMS.txt. Extract the full folder and open ResolutionFileManager-'+version+'.exe. Settings stay in local application data. The standalone EXE contains the same application; the ZIP also includes licences and instructions.\n\nThe application EXE is unsigned. Only use the official project downloads and verify hashes. Existing media is retained by conversion. Review output quality before deleting originals.\n', encoding='utf-8')
    old_changelog = git('show', 'FETCH_HEAD:CHANGELOG.md').decode('utf-8')
    (public/'CHANGELOG.md').write_text((ROOT/f'RELEASE_NOTES_{version}.md').read_text(encoding='utf-8')+'\n\n'+old_changelog, encoding='utf-8')
    index = stage/'release.index'
    env = dict(os.environ, GIT_INDEX_FILE=str(index))
    base = git('rev-parse', 'FETCH_HEAD').decode().strip()
    git('read-tree', base, env=env)
    names = set(runtime) | {'VERSION.txt', 'LICENSE', 'PRIVACY.md', 'THIRD_PARTY_NOTICES.md',
              'requirements.txt', 'requirements-ai.txt', 'app_icon.png', 'app_icon.ico',
              'build_windows.ps1', 'build_windows_release.ps1', 'build_linux.sh', 'run_linux.sh',
              f'RELEASE_NOTES_{version}.md', f'docs/RELEASE_READINESS_{version}.json',
              'docs/ENHANCEMENT_GUIDE.md', 'assets/ai/manifest.json'}
    for pattern in ('locales/*.json', 'docs/help/*.json', 'docs/help/*.md', 'assets/ai/LICENSES/*', 'tests/test_conversion*.py', 'tests/test_automatic_video*.py', 'test_*.py'):
        names.update(p.relative_to(ROOT).as_posix() for p in ROOT.glob(pattern) if p.is_file())
    for name in ('prepare_ai_assets', 'convert_ai_models', 'collect_ai_notices', 'export_compact_onnx', 'export_compact_ncnn', 'verify_english_review', 'project_snapshot', 'verify_windows_package', 'publish_reviewed_release', 'prepare_store_github_release'):
        names.add('tools/'+name+'.py')
    for name in sorted(names):
        assert (ROOT/name).is_file(), name
    git('add', '--', *sorted(names), env=env)
    for path in public.iterdir():
        blob = git('hash-object', '-w', '--stdin', data=path.read_bytes()).decode().strip()
        git('update-index', '--add', '--cacheinfo', '100644', blob, path.name, env=env)
    tree = git('write-tree', env=env).decode().strip()
    commit = git('commit-tree', tree, '-p', base, data=f'Release {version}: approved VBR conversion and usability improvements\n'.encode()).decode().strip()
    source = stage/'source'; source.mkdir(exist_ok=False)
    with zipfile.ZipFile(io.BytesIO(git('archive', '--format=zip', commit))) as archive:
        for item in archive.infolist():
            target = source/item.filename
            assert target.resolve().is_relative_to(source.resolve())
            if item.is_dir(): target.mkdir(parents=True, exist_ok=True)
            else:
                assert Path(item.filename).name not in ('settings.json', '.env')
                target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(archive.read(item))
    manifest = {'version': version, 'git_head': commit,
                'files': {p.relative_to(source).as_posix(): sha(p) for p in source.rglob('*') if p.is_file()}}
    (source/'SOURCE_MANIFEST.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    licenses = stage/'licenses'
    old = ROOT/'release-output/12.7.10/ResolutionFileManager-12.7.10-Windows-x64'
    old_binary = CArchiveReader(str(old/'ResolutionFileManager-12.7.10.exe'))
    for name in ('ffmpeg.exe', 'ffprobe.exe', 'ffplay.exe'):
        assert hashlib.sha256(frozen.extract(name)).digest() == hashlib.sha256(old_binary.extract(name)).digest(), 'Refresh FFmpeg notices: '+name
    shutil.copytree(old/'licenses', licenses)
    shutil.copytree(ROOT/'assets/ai/LICENSES', licenses/'ai-components')
    shutil.copy2(ROOT/'assets/ai/manifest.json', licenses/'AI-ASSET-MANIFEST.json')
    for distribution in importlib.metadata.distributions():
        for file in distribution.files or ():
            if any(word in str(file).lower() for word in ('license', 'licence', 'copying', 'copyright')):
                path = Path(distribution.locate_file(file))
                if path.is_file():
                    target = licenses/'python-distributions'/distribution.metadata['Name']/(path.name if '..' in file.parts else str(file))
                    target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(path, target)
    checkpoint = {'version':version, 'baseCommit':base, 'sourceCommit':commit,
                  'source':str(source), 'licenses':str(licenses), 'review':str(review_path),
                  'approval':str(approval_path), 'sourceFiles':len(manifest['files'])}
    (stage/'prepared.json').write_text(json.dumps(checkpoint, indent=2)+'\n')
    print(json.dumps(checkpoint), flush=True)


if __name__ == '__main__':main()
