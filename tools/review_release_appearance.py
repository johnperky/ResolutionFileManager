"""Read-only real-Tk appearance/resizing/conversion checks, isolated settings."""
import argparse
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import sys
import tempfile
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import media_sorter as m
from tools.smoke_test_gui import descendants


def check(language, output):
    from PIL import ImageGrab
    output.mkdir(parents=True,exist_ok=True)
    results=[]
    with tempfile.TemporaryDirectory(prefix='rfm-release-layout-',ignore_cleanup_errors=True) as tmp:
        data=Path(tmp)
        sample=Path('E:/free to use videos')
        (data/'settings.json').write_text(json.dumps({'language':language,'geometry':'1900x960+0+0',
            'left':{'path':str(sample),'recursive':True},'right':{'path':str(sample),'recursive':True,'inspector_enabled':True},
            'reminders':{'rating_disabled':True,'support_disabled':True}}),encoding='utf-8')
        m.application_data_directory=lambda:data
        app=m.MediaSorterApp()
        errors=[]
        app.report_callback_exception=lambda *exc: errors.append(str(exc[1]))
        def pump(seconds=.2):
            deadline=time.monotonic()+seconds
            while time.monotonic()<deadline:
                app.update();time.sleep(.01)
        def capture(window,name):
            user=ctypes.windll.user32
            user.GetAncestor.restype=wintypes.HWND
            hwnd=user.GetAncestor(wintypes.HWND(window.winfo_id()),2)
            path=output/f'{language}-{name}.png'
            ImageGrab.grab(window=hwnd).save(path)
            return str(path)
        try:
            pump(1)
            # Actual sample path with deterministic geometry-test metadata.
            # These diagnostics are not Store assets; no conversion is executed.
            path=next(sample.rglob('*.mp4'))
            stat=path.stat()
            item=m.MediaItem(path,1920,1080,stat.st_size,stat.st_mtime,10)
            app.left.selected_items=lambda:[item]
            for theme in ('System','Light','Dark','High contrast'):
                for scale in (100,125,150,175,200):
                    for width,height in ((1900,960),(1400,850)):
                        app.geometry(f'{width}x{height}+0+0')
                        app.apply_appearance(theme,scale)
                        pump()
                        failures=[]
                        for widget in app.toolbar.winfo_children():
                            if isinstance(widget,m.ttk.Button) and (not widget.winfo_ismapped() or widget.winfo_width()<widget.winfo_reqwidth()-2):
                                failures.append(f'top action clipped: {widget.cget("text")}')
                        style=m.ttk.Style(app)
                        lines=m.tkfont.nametofont('TkDefaultFont',root=app).metrics('linespace')
                        if int(style.lookup('Treeview','rowheight') or 20)<lines+2:
                            failures.append('file rows shorter than scaled font')
                        if theme in ('Dark','High contrast'):
                            expected='#1e1e1e' if theme=='Dark' else '#000000'
                            if style.lookup('TCombobox','fieldbackground',('readonly',))!=expected:
                                failures.append('readonly selector does not use readable theme background')
                        for side,pane in (('left',app.left),('right',app.right)):
                            if not pane.cancel_button.winfo_ismapped() or pane.cancel_button.winfo_width()<pane.cancel_button.winfo_reqwidth()-2:
                                failures.append(f'{side} scan Cancel hidden/clipped')
                            heading_font=m.tkfont.nametofont('TkHeadingFont',root=app)
                            for column in pane.tree['columns']:
                                if pane.tree.column(column,'width')<heading_font.measure(pane.tree.heading(column,'text'))+24:
                                    failures.append(f'{side} scaled column heading clipped: {column}')
                            for button in pane.selection_toolbar_groups:
                                if button.winfo_width()<button.winfo_reqwidth()-2:
                                    failures.append(f'{side} tick control clipped: {button.cget("text")}')
                                if button.winfo_x()+button.winfo_width()>pane.selection_toolbar.winfo_width()+2:
                                    failures.append(f'{side} tick control outside toolbar')
                        app.set_active(app.left)
                        app.convert_selected_videos()
                        pump()
                        dialog=next(w for w in app.winfo_children() if isinstance(w,m.tk.Toplevel))
                        for widget in descendants(dialog):
                            if isinstance(widget,m.ttk.Button):
                                if not widget.winfo_ismapped():
                                    failures.append(f'conversion button hidden: {widget.cget("text")}')
                                if widget.winfo_width()<widget.winfo_reqwidth()-2:
                                    failures.append(f'conversion button clipped: {widget.cget("text")}')
                                if widget.winfo_rooty()+widget.winfo_height()>dialog.winfo_rooty()+dialog.winfo_height()+2:
                                    failures.append(f'conversion button below dialog: {widget.cget("text")}')
                            if isinstance(widget,m.ttk.Combobox) and widget.winfo_ismapped():
                                font=m.tkfont.Font(root=app,font=widget.cget('font'))
                                required=max((font.measure(str(v)) for v in widget['values']),default=0)+28
                                if widget.winfo_width()<required:
                                    failures.append('conversion selector text clipped')
                                if widget.winfo_rootx()+widget.winfo_width()>dialog.winfo_rootx()+dialog.winfo_width()+2:
                                    parent=widget.master
                                    while parent is not dialog and not isinstance(parent,m.tk.Canvas):
                                        parent=parent.master
                                    if not isinstance(parent,m.tk.Canvas):
                                        failures.append('conversion selector outside dialog without scrolling')
                        row={'language':language,'theme':theme,'scale':scale,'size':[width,height],
                             'passed':not failures and not errors,'failures':failures,'errors':list(errors)}
                        if failures or (width==1900 and scale in (100,200)):
                            name=f'{theme.replace(" ","-")}-{scale}-{width}'
                            row['mainCapture']=capture(app,name+'-main')
                            row['dialogCapture']=capture(dialog,name+'-conversion')
                        dialog.destroy()
                        if width==1900 and scale in (100,200):
                            app.appearance_controls();pump()
                            appearance=next(w for w in app.winfo_children() if isinstance(w,m.tk.Toplevel))
                            for button in descendants(appearance):
                                if isinstance(button,m.ttk.Button) and (not button.winfo_ismapped() or button.winfo_rooty()+button.winfo_height()>appearance.winfo_rooty()+appearance.winfo_height()+2):
                                    failures.append('appearance action hidden')
                            row['appearanceCapture']=capture(appearance,f'{theme.replace(" ","-")}-{scale}-appearance')
                            appearance.destroy()
                            row['passed']=not failures and not errors
                        results.append(row)
                        if failures or errors:
                            return results
            return results
        finally:
            app.close_app()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--language',default='en')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    results=check(args.language,args.output)
    report=args.output/f'{args.language}-results.json'
    report.write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'states':len(results),'passed':all(r['passed'] for r in results),'report':str(report)}))
    raise SystemExit(0 if all(r['passed'] for r in results) else 1)
