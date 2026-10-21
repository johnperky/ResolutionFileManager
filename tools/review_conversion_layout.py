"""Measure real conversion controls without executing any media operation."""
import argparse
import json
import sys
import subprocess
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import media_sorter as m
from tools.smoke_test_gui import descendants


def check(code, interactive=False):
    sample_root = Path('E:/free to use videos')
    sample = next(sample_root.rglob('*.mp4'))
    stat = sample.stat()
    with tempfile.TemporaryDirectory(prefix='rfm-conversion-layout-', ignore_cleanup_errors=True) as folder:
        data = Path(folder)
        (data / 'settings.json').write_text(json.dumps({
            'language': code, 'geometry': '1800x950+0+0',
            'performance_profile': 'Quiet',
            'left': {'path': str(sample_root)}, 'right': {'path': str(sample_root)},
            'reminders': {'rating_disabled': True, 'support_disabled': True},
        }), encoding='utf-8')
        m.application_data_directory = lambda: data
        app = m.MediaSorterApp()
        errors = []
        app.report_callback_exception = lambda *args: errors.append(str(args[1]))
        # Real sample path, read-only preview planning; no conversion is started.
        app.left.selected_items = lambda: [m.MediaItem(sample, 1920, 1080, stat.st_size, stat.st_mtime, 10)]
        app.set_active(app.left)
        try:
            app.convert_selected_videos()
            deadline = time.monotonic() + .3
            while time.monotonic() < deadline:
                app.update()
                time.sleep(.01)
            window = next(w for w in app.winfo_children() if isinstance(w, m.tk.Toplevel))
            combos = [w for w in descendants(window) if isinstance(w, m.ttk.Combobox)]
            failures = []
            measurements = []
            for combo in combos:
                font = m.tkfont.Font(root=app, font=combo.cget('font'))
                required = max(font.measure(value) for value in combo['values']) + 28
                actual = combo.winfo_width()
                measurements.append({'values': list(combo['values']), 'required': required, 'actual': actual})
                if actual < required:
                    failures.append(f'choice clipped: {combo.get()!r}: {actual} < {required}')
                if combo.winfo_rootx() + actual > window.winfo_rootx() + window.winfo_width() - 8:
                    failures.append('combobox exceeds dialog right edge')
            for control in descendants(window):
                if isinstance(control, (m.ttk.Button, m.ttk.Checkbutton)) and control.winfo_ismapped():
                    if control.winfo_rootx() + control.winfo_width() > window.winfo_rootx() + window.winfo_width() - 6:
                        failures.append(f'control exceeds dialog: {control.cget("text")}')
            if interactive:
                app.title(f'RFM layout review {code}')
                app.mainloop()
            return {'language': code, 'passed': not failures and not errors,
                    'failures': failures, 'errors': errors, 'comboboxes': measurements}
        finally:
            try:
                app.close_app()
            except m.tk.TclError:
                pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('languages', nargs='*')
    parser.add_argument('--report')
    parser.add_argument('--interactive', action='store_true')
    parser.add_argument('--single')
    args = parser.parse_args()
    if args.single:
        result = check(args.single, args.interactive)
        print(json.dumps(result, ensure_ascii=True))
        raise SystemExit(0 if result['passed'] else 1)
    from localization import SUPPORTED_LANGUAGES
    results = []
    for code in args.languages or SUPPORTED_LANGUAGES:
        child = subprocess.run([sys.executable, __file__, '--single', code] +
                               (['--interactive'] if args.interactive else []),
                               capture_output=True, text=True, encoding='utf-8', timeout=120)
        try:
            result = json.loads(child.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            result = {'language': code, 'passed': False, 'error': child.stderr[-2000:]}
        results.append(result)
        print(json.dumps(result, ensure_ascii=True), flush=True)
    if args.report:
        Path(args.report).write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    raise SystemExit(0 if all(r['passed'] for r in results) else 1)
