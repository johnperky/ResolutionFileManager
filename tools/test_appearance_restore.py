"""Native regression: theme preview/Cancel must preserve custom column widths."""
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import media_sorter as m
from tools.smoke_test_gui import descendants


class AppearanceRestoreTests(unittest.TestCase):
    def test_cancel_restores_custom_width_after_scaling_preview(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            data=Path(directory)
            (data/'settings.json').write_text(json.dumps({'language':'en','left':{'path':directory},'right':{'path':directory},'reminders':{'rating_disabled':True,'support_disabled':True}}),encoding='utf-8')
            m.application_data_directory=lambda:data
            app=m.MediaSorterApp()
            def pump():
                until=time.monotonic()+.2
                while time.monotonic()<until: app.update();time.sleep(.01)
            try:
                if sys.platform.startswith('linux'):
                    app.apply_appearance('System',200);pump()
                    self.assertEqual(app.ui_scale,100,'Removed saved scale was not reset safely')
                pump();app.left.tree.column('size',width=60)
                app.appearance_controls();pump()
                dialog=next(w for w in app.winfo_children() if isinstance(w,m.tk.Toplevel))
                app.apply_appearance('Dark',100);pump()
                self.assertEqual(app.left.tree.column('size','width'),60,'theme-only preview changed custom width')
                app.apply_appearance('Dark',max(m.interface_scales()));pump()
                for widget in app.toolbar.winfo_children():
                    if isinstance(widget,m.ttk.Button):
                        self.assertGreaterEqual(widget.winfo_width(),widget.winfo_reqwidth()-2,f'Top action clipped: {widget.cget("text")}')
                for pane in (app.left,app.right):
                    self.assertTrue(pane.cancel_button.winfo_ismapped(),'Scan Cancel hidden at enlarged text size')
                    self.assertGreaterEqual(pane.cancel_button.winfo_width(),pane.cancel_button.winfo_reqwidth()-2,'Scan Cancel clipped at enlarged text size')
                cancel=next(w for w in descendants(dialog) if isinstance(w,m.ttk.Button) and w.cget('text')=='Cancel')
                cancel.invoke();pump()
                self.assertEqual(app.left.tree.column('size','width'),60,'Cancel changed custom width')
                self.assertEqual((app.appearance_theme,app.ui_scale),('System',100))
                self.assertFalse(getattr(app,'toolbar_wrapped',False),'Toolbar stayed wrapped after restoring normal text size')
            finally:
                app.close_app()


if __name__=='__main__':unittest.main()
