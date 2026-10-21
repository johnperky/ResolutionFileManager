"""Regression: a short browser must retain Info actions and scrollable metadata."""
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import media_sorter as m

def check(code):
    sample_root = Path('E:/free to use videos')
    sample = next(sample_root.rglob('*.mp4'))
    with tempfile.TemporaryDirectory(prefix='rfm-info-layout-', ignore_cleanup_errors=True) as folder:
        data = Path(folder)
        (data/'settings.json').write_text(json.dumps({'language': code, 'geometry': '1700x750',
            'left': {'path': str(sample_root)},
            'right': {'path': str(sample_root), 'inspector_enabled': True, 'inspector_width': 290},
            'reminders': {'rating_disabled': True, 'support_disabled': True}}), encoding='utf-8')
        m.application_data_directory = lambda: data
        app = m.MediaSorterApp()
        try:
            pane = app.right
            stat = sample.stat()
            pane.update_inspector(m.MediaItem(sample, 1920, 1080, stat.st_size, stat.st_mtime,
                10, codec='H.264', bitrate=8000000, frame_rate=30, tags=('last-metadata-marker',)))
            app.left.preview_enabled_var.set(True)
            app.left.toggle_preview()
            deadline = time.monotonic()+1
            while time.monotonic()<deadline:
                app.update(); time.sleep(.01)
            app.update_idletasks()
            for button in pane.inspector_buttons.winfo_children():
                assert button.winfo_ismapped(), 'Info action disappears when previews reduce browser height'
                bounds = (button.winfo_rooty()+button.winfo_height(), pane.inspector_frame.winfo_rooty()+pane.inspector_frame.winfo_height())
                assert bounds[0]<=bounds[1], f'Info action exceeds browser bottom: {bounds}'
            assert 'last-metadata-marker' in pane.inspector_details_text.get('1.0', 'end'), 'Last metadata field lost'
            pane.inspector_details_text.yview_moveto(1)
            app.update()
            assert pane.inspector_details_text.yview()[1]>=.99, 'Final metadata cannot be reached by scrolling'
            return {'language': code, 'passed': True}
        finally:
            app.close_app()

if __name__ == '__main__':
    print(json.dumps(check(sys.argv[1] if len(sys.argv)>1 else 'ar')))
