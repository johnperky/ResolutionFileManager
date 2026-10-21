"""Local native-Tk screenshot candidates; no remote clicks or media operations.

Uses source verified against the frozen review build, NOT the EXE process.
Candidates always require visual approval before promotion to Store assets.
"""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import html
import json
import marshal
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
VIEWS = ('01-details-info', '02-dual-previews', '03-thumbnails', '04-video-conversion')
MODULES = ('media_sorter', 'transfer_engine', 'transfer_ui', 'localization', 'rtl_display', 'reminder_policy')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def atomic_json(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    temp.replace(path)


def ensure_capture_focus(owned, activate, settle, attempts=60):
    for _ in range(attempts):
        if owned():
            return
        activate()
        settle()
    if not owned():
        raise RuntimeError('Cannot regain capture window focus; no image saved')


def title_decoration(name, rect, top):
    left, y, right, bottom = rect
    return name.startswith('NviewButton') and top <= y <= bottom <= top+24 and 0 < right-left <= 64


def preflight():
    from PyInstaller.archive.readers import CArchiveReader
    version = (ROOT/'VERSION.txt').read_text().strip()
    binary = ROOT/f'dist/multilingual-review-{version}/ResolutionFileManager-v{version}-Multilingual-Review.exe'
    archive = CArchiveReader(str(binary))
    main = marshal.loads(archive.extract('media_sorter'))
    assert main == compile((ROOT/'media_sorter.py').read_text(encoding='utf-8'), main.co_filename, 'exec'), 'Source differs from EXE'
    pyz = archive.open_embedded_archive('PYZ.pyz')
    for module in MODULES[1:]:
        code = pyz.extract(module)
        assert code == compile((ROOT/f'{module}.py').read_text(encoding='utf-8'), code.co_filename, 'exec'), module
    locales = {}
    for name in archive.toc:
        normal = name.replace('\\', '/')
        if normal.startswith('locales/') and normal.endswith('.json'):
            path = ROOT/normal
            assert archive.extract(name) == path.read_bytes(), normal
            locales[path.stem] = sha(path)
    assert len(locales) == 43
    binary_hash = sha(binary)
    checkpoint = (ROOT/'docs/LAYOUT_REVIEW_CHECKPOINT.md').read_text(encoding='utf-8')
    assert 'readyForScreenshots: true' in checkpoint and binary_hash in checkpoint, 'Layout gate or binary mismatch'
    return {'version': version, 'binarySha256': binary_hash,
            'sourceSha256': {f'{name}.py': sha(ROOT/f'{name}.py') for name in MODULES},
            'captureScriptSha256': sha(Path(__file__)),
            'locales': locales, 'provenance': 'verified-source-native-ui',
            'python': sys.version, 'readyForRelease': False, 'readyForStoreImport': False}


def reusable(row, folder, proof):
    path = (folder/row['file']).resolve()
    if not path.is_relative_to(folder.resolve()):
        return False
    return (row.get('binarySha256') == proof['binarySha256'] and
            row.get('sourceSha256') == proof['sourceSha256'] and
            path.is_file() and sha(path) == row.get('sha256'))


def gallery(folder):
    rows = []
    for path in sorted(folder.glob('*/captures.json')):
        rows.extend(json.loads(path.read_text(encoding='utf-8')))
    atomic_json(folder/'candidate-progress.json', rows)
    approval_path = folder/'visual-review.json'
    approval = json.loads(approval_path.read_text(encoding='utf-8')) if approval_path.exists() else {}
    reviewed = (approval.get('visualReviewComplete',False) and
                {(r['language'],r['view'],r['sha256']) for r in rows} ==
                {(r['language'],r['view'],r['sha256']) for r in approval.get('captures',[])})
    heading = 'Visually reviewed screenshot candidates' if reviewed else 'Unapproved screenshot candidates'
    cards = ''.join(f'<section><h2>{html.escape(r["language"])} / {r["view"]}</h2><a href="{r["file"]}"><img loading="lazy" src="{r["file"]}" width="768"></a></section>' for r in rows)
    note = ('Visual review recorded for these exact images; see visual-review.json for scope and binary checks. Store import and full release approval remain separate.' if reviewed else 'Native source UI verified against the review EXE; not EXE-process captures. Visual review and binary spot checks remain required.')
    (folder/'REVIEW.html').write_text('<!doctype html><meta charset="utf-8"><title>RFM batch candidates</title><h1>'+heading+'</h1><p>'+note+'</p>'+cards, encoding='utf-8')
    return len(rows)


def worker(args, proof, folder):
    # A process per locale avoids language/global Tk state leaking between runs.
    from PIL import ImageGrab
    sys.path.insert(0, str(ROOT))
    import media_sorter as m
    locale = args.worker
    dest = folder/locale
    dest.mkdir(exist_ok=True)
    manifest = dest/'captures.json'
    rows = json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else []
    assert all(reusable(row, folder, proof) for row in rows), 'Existing candidate changed; choose a new output folder'
    done = {row['view'] for row in rows}
    if done == set(VIEWS):
        return
    data = dest/'settings'
    data.mkdir(exist_ok=True)
    template = folder.parent/'Review Settings/ResolutionFileManager'
    settings = json.loads((template/'settings.json').read_text(encoding='utf-8-sig'))
    settings.update(language=locale, geometry='1900x900+0+0', browser_split=960, preview_split=480)
    settings['reminders'].update(rating_disabled=True, support_disabled=True)
    sample = Path('E:/free to use videos')
    assert sample.is_dir()
    for side in ('left', 'right'):
        settings[side].update(path=str(sample), recursive=True, view_mode='Details', search='',
                              show_images=False, show_videos=True, preview_enabled=False,
                              inspector_enabled=side == 'right', inspector_width=290,
                              sort_column='resolution', sort_reverse=True)
    atomic_json(data/'settings.json', settings)
    cache = template/'metadata-cache.sqlite3'
    if cache.exists() and not (data/cache.name).exists():
        with sqlite3.connect(cache.as_uri()+'?mode=ro', uri=True) as src, sqlite3.connect(data/cache.name) as target:
            src.backup(target)
    m.application_data_directory = lambda: data
    app = m.MediaSorterApp()
    errors = []
    app.report_callback_exception = lambda *exc: errors.append(str(exc))

    def pump(seconds=.3, until=None, timeout=90):
        deadline = time.monotonic()+(timeout if until else seconds)
        while time.monotonic() < deadline:
            app.update()
            if errors:
                raise RuntimeError(errors[0])
            if until and until():
                return
            time.sleep(.025)
        if until:
            raise TimeoutError('Native UI did not become ready')

    def select(pane, name):
        item = next(item for item in pane.visible_items if item.path.name == name)
        iid = pane.path_to_iid[str(item.path)]
        pane.tree.selection_set(iid)
        pane.tree.focus(iid)
        pane.tree.see(iid)
        pane.update_inspector(item)
        return item

    user = ctypes.windll.user32
    user.GetForegroundWindow.restype = wintypes.HWND
    user.GetAncestor.restype = wintypes.HWND
    user.GetLastActivePopup.restype = wintypes.HWND
    user.GetTopWindow.restype = wintypes.HWND
    user.GetWindow.restype = wintypes.HWND
    hwnd = None

    def activate(handle):
        # Windows may deny a background child's first activation. Temporarily
        # join input queues to activate our own window without synthetic clicks.
        foreground = user.GetForegroundWindow()
        foreground_thread = user.GetWindowThreadProcessId(wintypes.HWND(foreground), None)
        current_thread = ctypes.windll.kernel32.GetCurrentThreadId()
        attached = foreground_thread != current_thread and user.AttachThreadInput(current_thread, foreground_thread, True)
        try:
            user.BringWindowToTop(wintypes.HWND(handle))
            user.SetForegroundWindow(wintypes.HWND(handle))
        finally:
            if attached:
                user.AttachThreadInput(current_thread, foreground_thread, False)

    def capture(view):
        if view in done:
            return
        pump(1)
        def owned():
            foreground = user.GetForegroundWindow()
            pid = wintypes.DWORD()
            user.GetWindowThreadProcessId(wintypes.HWND(foreground), ctypes.byref(pid))
            if pid.value != os.getpid():
                return False
            # Foreground ownership alone misses topmost notification toasts.
            # Walk only windows above our root and reject visible overlaps.
            bounds = wintypes.RECT()
            ctypes.windll.dwmapi.DwmGetWindowAttribute(wintypes.HWND(hwnd), 9, ctypes.byref(bounds), ctypes.sizeof(bounds))
            above = user.GetTopWindow(None)
            while above and above != hwnd:
                other_pid = wintypes.DWORD()
                user.GetWindowThreadProcessId(wintypes.HWND(above), ctypes.byref(other_pid))
                if other_pid.value != os.getpid() and user.IsWindowVisible(wintypes.HWND(above)):
                    cloaked = wintypes.DWORD()
                    ctypes.windll.dwmapi.DwmGetWindowAttribute(wintypes.HWND(above), 14, ctypes.byref(cloaked), 4)
                    other = wintypes.RECT()
                    user.GetWindowRect(wintypes.HWND(above), ctypes.byref(other))
                    name = ctypes.create_unicode_buffer(256)
                    user.GetClassNameW(wintypes.HWND(above), name, 256)
                    # NVIDIA nView adds a tiny title-bar decoration, not an
                    # obstructing notification. Do not treat it as app content.
                    decoration = title_decoration(name.value, (other.left,other.top,other.right,other.bottom), bounds.top)
                    if not decoration and not cloaked.value and max(bounds.left,other.left)<min(bounds.right,other.right) and max(bounds.top,other.top)<min(bounds.bottom,other.bottom):
                        print(f'Capture delayed: overlapping window class={name.value}, bounds={(other.left,other.top,other.right,other.bottom)}', flush=True)
                        return False
                above = user.GetWindow(wintypes.HWND(above), 2)
            return True
        ensure_capture_focus(owned, lambda: activate(user.GetLastActivePopup(wintypes.HWND(hwnd))), lambda: pump(.3))
        rect = wintypes.RECT()
        ctypes.windll.dwmapi.DwmGetWindowAttribute(wintypes.HWND(hwnd), 9, ctypes.byref(rect), ctypes.sizeof(rect))
        bounds = (rect.left, rect.top, rect.right, rect.bottom)
        assert bounds[2]-bounds[0] >= 1600 and bounds[3]-bounds[1] >= 850, bounds
        output = dest/f'{view}.png'
        assert not output.exists(), 'Orphan file preserved; use a new output folder'
        image = ImageGrab.grab(bbox=bounds, all_screens=True)
        assert owned(), 'Focus changed during capture; image discarded'
        image.save(output, format='PNG')
        rows.append({'language': locale, 'view': view, 'file': output.relative_to(folder).as_posix(),
                     'width': image.width, 'height': image.height, 'sha256': sha(output),
                     'reviewed': False, 'provenance': proof['provenance'],
                     'binarySha256': proof['binarySha256'], 'sourceSha256': proof['sourceSha256']})
        rows[-1]['captureScriptSha256'] = proof['captureScriptSha256']
        atomic_json(manifest, rows)
        print(f'{locale}: {view}', flush=True)

    try:
        app.state('zoomed')
        app.lift()
        pump(.8)
        hwnd = user.GetAncestor(wintypes.HWND(app.winfo_id()), 2)
        activate(hwnd)
        pump(until=lambda: not app.left.scan_active and not app.right.scan_active and len(app.left.visible_items)>3)
        left = select(app.left, '19784079-hd_1080_1918_60fps.mp4')
        right = select(app.right, '9894607-uhd_4096_2160_25fps.mp4')
        capture(VIEWS[0])
        for pane, preview, item in ((app.left, app.left_preview, left), (app.right, app.right_preview, right)):
            pane.preview_enabled_var.set(True)
            pane.toggle_preview()
            preview.show_item(item)
            preview.stop_playback()
            preview.position_var.set(300/item.duration if item.duration else 0)
            preview.update_time(3)
            preview.render_still(3)
        pump(until=lambda: app.left_preview.photo is not None and app.right_preview.photo is not None)
        app.preview_area.sash_place(0, app.browser_panes.sash_coord(0)[0], 0)
        capture(VIEWS[1])
        if set(VIEWS)-done == {VIEWS[1]}:
            return  # Resume just the preview; no thumbnail/dialog staging.
        for pane in (app.left, app.right):
            pane.preview_enabled_var.set(False)
            pane.toggle_preview()
        app.left.show_images_var.set(True)
        app.left.show_videos_var.set(False)
        app.left.navigate(Path('E:/Resolution File Manager Demo Media'))
        pump(until=lambda: not app.left.scan_active and bool(app.left.visible_items))
        app.left.set_view_mode('Thumbnails')
        pump(5)
        capture(VIEWS[2])
        app.left.set_view_mode('Details')
        app.left.show_images_var.set(False)
        app.left.show_videos_var.set(True)
        app.left.navigate(sample)
        pump(until=lambda: not app.left.scan_active and len(app.left.visible_items)>3)
        app.set_active(app.right)
        names = {'6332697-uhd_4096_2160_25fps.mp4', '10264814-uhd_4096_2160_25fps.mp4', '10637339-uhd_4096_2160_25fps.mp4'}
        app.right.checked_paths = {str(item.path) for item in app.right.visible_items if item.path.name in names}
        assert len(app.right.checked_paths) == 3
        app.right.refresh_checks()
        app.convert_selected_videos()  # Opens the plan only. Never invokes Start.
        pump(.5)
        dialogs = [w for w in app.winfo_children() if isinstance(w, m.tk.Toplevel)]
        assert len(dialogs) == 1
        dialogs[0].geometry('1060x690+430+140')
        dialogs[0].lift()
        dialogs[0].focus_force()
        capture(VIEWS[3])
        dialogs[0].destroy()
    finally:
        app.close_app()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--languages', default='all', help='all or comma-separated locale codes')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--worker', help=argparse.SUPPRESS)
    args = parser.parse_args()
    proof = preflight()
    folder = args.output or ROOT.parent/f'Store Preparation {proof["version"]}/Batch Candidates v2'
    folder = folder.resolve()
    folder.mkdir(parents=True, exist_ok=True)
    if (folder/'provenance.json').exists():
        previous = json.loads((folder/'provenance.json').read_text(encoding='utf-8'))
        # A capture-only repair may resume unchanged application code/resources.
        stable = lambda p: {k: v for k, v in p.items() if k != 'captureScriptSha256'}
        assert stable(previous) == stable(proof) or not any(folder.glob('*/*.png')), 'App provenance changed; use a new output folder'
        if previous != proof:
            history = folder/f'provenance-{previous["captureScriptSha256"]}.json'
            if not history.exists():
                atomic_json(history, previous)
        atomic_json(folder/'provenance.json', proof)
    else:
        atomic_json(folder/'provenance.json', proof)
    if args.worker:
        worker(args, proof, folder)
        return
    languages = sorted(proof['locales']) if args.languages == 'all' else args.languages.split(',')
    assert all(code in proof['locales'] for code in languages), 'Unknown language'
    import msvcrt
    with (folder/'.batch.lock').open('a+b') as lock:
        lock.seek(0)
        lock.write(b'0')
        lock.flush()
        lock.seek(0)
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        for code in languages:
            result = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--worker', code, '--output', str(folder)], cwd=ROOT, timeout=240)
            count = gallery(folder)
            atomic_json(folder/'run-status.json', {'lastLanguage': code, 'candidateCount': count,
                        'requestedLanguages': languages, 'failed': result.returncode != 0,
                        'visualReviewComplete': False, 'readyForRelease': False})
            if result.returncode:
                raise SystemExit(f'Stopped at {code}; earlier candidates preserved. See batch log.')
    print(f'Finished: {gallery(folder)} candidates. Review {folder / "REVIEW.html"}', flush=True)


if __name__ == '__main__':
    main()
