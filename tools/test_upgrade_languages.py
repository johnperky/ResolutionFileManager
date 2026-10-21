"""Check new dialogs in real Tk, including displayed policies and internal IDs."""
import argparse,json,sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import media_sorter as m
from tools.smoke_test_gui import descendants

def check(code):
    with tempfile.TemporaryDirectory(prefix='rfm-language-upgrade-',ignore_cleanup_errors=True) as folder:
        root=Path(folder); source=root/'source'; dest=root/'dest'; data=root/'settings'
        source.mkdir(); dest.mkdir(); data.mkdir()
        from PIL import Image
        Image.new('RGB',(100,100),'blue').save(source/'test.png')
        (dest/'test.png').write_bytes(b'old')
        (data/'settings.json').write_text(json.dumps({'language':code,'geometry':'1700x950','left':{'path':str(source),'show_images':True},'right':{'path':str(dest)},'reminders':{'rating_disabled':True,'support_disabled':True}}),encoding='utf-8')
        m.application_data_directory=lambda:data
        app=m.MediaSorterApp(); errors=[]; checks=[]; app.report_callback_exception=lambda *a:errors.append(str(a[1]))
        def pump():
            until=time.monotonic()+.6
            while time.monotonic()<until: app.update(); time.sleep(.01)
        def inspect():
            try:
                window=next(w for w in app.winfo_children() if isinstance(w,m.tk.Toplevel))
                combo=next(w for w in descendants(window) if isinstance(w,m.ttk.Combobox))
                expected=tuple(app.translator.ui_text(v) for v in ('Ask for each conflict','Keep both','Replace','Skip'))
                assert tuple(combo['values'])==expected,('policy labels',combo['values'],expected)
                assert combo.get()==expected[0],('default',combo.get())
                combo.set(expected[3]); checks.append('translated conflict choices preserve selection')
                labels=[str(w.cget('text')) for w in descendants(window) if isinstance(w,m.ttk.Label)]
                assert app.translator.ui_text('Destination folder:') in labels
                tree=next(w for w in descendants(window) if isinstance(w,m.ttk.Treeview))
                assert tree.item(tree.get_children()[0],'values')[2]==app.translator.ui_text('Existing destination')
                checks.append('translated preview status and labels')
                start=next(w for w in descendants(window) if isinstance(w,m.ttk.Button) and w.cget('text')==app.translator.ui_text('Queue copy'))
                start.invoke()
                assert (dest/'test.png').read_bytes()==b'old' and (source/'test.png').is_file(),'translated Skip changed a file'
                assert app.operation_queue.empty(),'translated Skip queued an overwrite'
                checks.append('translated Skip retains originals and queues no transfer')
            except Exception as exc: errors.append(str(exc))
            finally:
                for w in app.winfo_children():
                    if isinstance(w,m.tk.Toplevel): w.destroy()
        try:
            pump(); app.after(250,inspect); app.preview_transfer([source/'test.png'],source,dest)
            assert not errors,errors
            for pane in (app.left,app.right):
                for button in pane.selection_toolbar_groups:
                    assert button.winfo_x()+button.winfo_width()<=pane.selection_toolbar.winfo_width()+2, 'selection toolbar overflow'
                    assert button.winfo_width()>=button.winfo_reqwidth()-2, 'selection button clipping'
                pane.inspector_enabled_var.set(True);pane.toggle_inspector();pump()
                assert pane.media_frame.winfo_width()>=160,'Info hides files'
                for button in pane.selection_toolbar_groups:
                    assert button.winfo_x()+button.winfo_width()<=pane.selection_toolbar.winfo_width()+2, 'Info causes toolbar overflow'
            checks.append('selection toolbar and Info geometry')
            app.show_selection_basket(); pump()
            assert app.basket_panel.cget('text')==app.translator.ui_text('Selection basket — temporary references')
            checks.append('translated docked basket')
            buttons=[w for w in descendants(app.basket_panel) if isinstance(w,m.ttk.Button)]
            assert all(w.winfo_width()>=w.winfo_reqwidth()-2 for w in buttons), 'basket button clipping'
            assert all(w.winfo_x()+w.winfo_width()<=w.master.winfo_width()+2 for w in buttons),'basket buttons overflow'
            app.left.tree.selection_set(app.left.tree.get_children()[0]); app.left.rename_with_preview(); pump()
            window=next(w for w in descendants(app) if isinstance(w,m.tk.Toplevel))
            status=next(w for w in descendants(window) if isinstance(w,m.ttk.Label) and w.cget('textvariable'))
            text=app.getvar(status.cget('textvariable'))
            expected=app.translator.ui_text('New filename: {name}\n{status}').format(name='test.png',status=app.translator.ui_text('Unchanged'))
            assert text==expected,('rename preview',text,expected)
            checks.append('translated live rename status'); window.destroy()
            app.set_active(app.left); app.batch_rename_selected();pump()
            window=next(w for w in descendants(app) if isinstance(w,m.tk.Toplevel))
            table=next(w for w in descendants(window) if isinstance(w,m.ttk.Treeview))
            assert table.item(table.get_children()[0],'values')[0]==app.translator.ui_text('Unchanged'),'batch status is not translated'
            checks.append('translated batch rename status');window.destroy()
            import transfer_ui
            assert transfer_ui.simpledialog is m.simpledialog and transfer_ui.messagebox is m.messagebox
            checks.append('localized new-folder and error dialog routing')
            assert not errors,errors
            return {'language':code,'passed':True,'checks':checks,'errors':errors}
        finally: app.close_app()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('languages',nargs='*'); parser.add_argument('--single');parser.add_argument('--report');args=parser.parse_args()
    if args.single:
        print(json.dumps(check(args.single),ensure_ascii=True)); raise SystemExit(0)
    from localization import SUPPORTED_LANGUAGES
    results=[]
    for code in args.languages or SUPPORTED_LANGUAGES:
        try:
            import subprocess
            child=subprocess.run([sys.executable,__file__,'--single',code],capture_output=True,text=True,encoding='utf-8',timeout=60)
            if child.returncode: raise RuntimeError(child.stderr[-3000:])
            results.append(json.loads(child.stdout.strip().splitlines()[-1]))
        except Exception as exc:
            import traceback
            results.append({'language':code,'passed':False,'error':str(exc),'traceback':traceback.format_exc()})
        print(f'{code}: {results[-1]}',flush=True)
    if args.report: Path(args.report).write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if any(not r['passed'] for r in results): raise SystemExit(1)
