"""Isolated real-Tk checks for the English review controls (no user media)."""
import json
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import media_sorter as m
from PIL import Image


def children(widget):
    for child in widget.winfo_children():
        yield child
        yield from children(child)


def main():
    results=[]; errors=[]
    with tempfile.TemporaryDirectory(prefix='rfm-upgrade-',ignore_cleanup_errors=True) as directory:
        root=Path(directory); source=root/'source'; source.mkdir(); dest=root/'destination'; dest.mkdir(); data=root/'settings'; data.mkdir()
        for n in range(6): Image.new('RGB',(320+n*20,200),'blue').save(source/f'image{n}.png')
        (data/'settings.json').write_text(json.dumps({'language':'en','geometry':'1500x900','left':{'path':str(source),'show_images':True},'right':{'path':str(dest),'show_images':True},'reminders':{'rating_disabled':True,'support_disabled':True}}))
        m.application_data_directory=lambda:data
        app=m.MediaSorterApp(); app.report_callback_exception=lambda *args:errors.append(str(args[1]))
        def pump(seconds=.3):
            until=time.monotonic()+seconds
            while time.monotonic()<until: app.update(); time.sleep(.01)
        def check(condition,name):
            print(name,condition,flush=True)
            assert condition,name
            results.append(name)
        try:
            pump(2); pane=app.left; app.set_active(pane)
            check(len(pane.items)==6,'Image scan')
            pane.inspector_enabled_var.set(True); pane.toggle_inspector(); pump()
            check(abs(pane.inspector_frame.winfo_width()-180)<12 and pane.media_frame.winfo_width()>=160,'Info opens at compact default without hiding files')
            pane.inspector_panes.sashpos(0,pane.inspector_panes.winfo_width()-240); pump()
            pane.inspector_enabled_var.set(False); pane.toggle_inspector(); pump()
            pane.inspector_enabled_var.set(True); pane.toggle_inspector(); pump()
            check(abs(pane.inspector_frame.winfo_width()-240)<12,'Info remembers adjusted width after toggle')
            check(abs(pane.get_state()['inspector_width']-240)<12,'Info width saved in workspace state')
            pane.inspector_enabled_var.set(False); pane.toggle_inspector(); pump()
            pane.thumbnail_pixels.set(290); pane.thumbnail_slider_changed(); check(pane.thumbnail_dimensions()[0]==290,'Thumbnail slider dimensions')
            pane.tree.selection_set(pane.tree.get_children()[:2]); app.add_to_selection_basket(pane); pump()
            check(len(app.selection_basket)==2,'Basket contains selected references')
            check(len(list(source.glob('*.png')))==6,'Basket leaves originals unchanged')
            app.hide_selection_basket()
            pane.tree.selection_set(pane.tree.get_children()[:1]); pane.rename_selected(); pump()
            rename=next(w for w in children(app) if isinstance(w,m.tk.Toplevel) and 'Rename file' in w.title())
            entry=next(w for w in children(rename) if isinstance(w,m.ttk.Entry)); entry.delete(0,'end'); entry.insert(0,'renamed.png'); pump()
            check(any('renamed.png' in str(w.cget('text')) for w in children(rename) if isinstance(w,m.ttk.Label)),'Single rename live preview')
            rename.destroy(); app.batch_rename_selected(); pump()
            batch=next(w for w in app.winfo_children() if isinstance(w,m.tk.Toplevel) and 'Batch rename' in w.title())
            entry=next(w for w in children(batch) if isinstance(w,m.ttk.Entry)); entry.delete(0,'end'); entry.insert(0,'new-{n}{dotext}'); pump()
            tree=next(w for w in children(batch) if isinstance(w,m.ttk.Treeview))
            check('new-' in str(tree.item(tree.get_children()[0],'values')),'Batch rename automatically updates preview')
            batch.destroy()
            pane.tree.selection_set(()); pane.clear_checks(); pump()
            first=pane.tree.get_children()[0]; box=pane.tree.bbox(first)
            x=pane.tree.winfo_rootx()+box[0]+100; top=pane.tree.winfo_rooty()+box[1]
            start=SimpleNamespace(widget=pane.tree,state=0,x_root=x,y_root=top+150)
            end=SimpleNamespace(widget=pane.tree,state=0,x_root=x+100,y_root=top+2)
            pane.rubber_start(start); pane.rubber_motion(end); pane.rubber_end(end); pump()
            check(len(pane.highlighted_items())>=3 and not pane.checked_paths,'Details rubber-band highlights without ticking')
            pane.clear_checks(); rows=pane.tree.get_children(); pane.tree.selection_set(rows[:2]); box=pane.tree.bbox(rows[0])
            click=SimpleNamespace(widget=pane.tree,state=0,x=box[0]+70,y=box[1]+5,x_root=pane.tree.winfo_rootx()+box[0]+70,y_root=pane.tree.winfo_rooty()+box[1]+5)
            pane.media_button_pressed(click); pane.media_button_released(click)
            check(pane.tree.selection()==(rows[0],),'Ordinary click collapses highlighted group')
            pane.tree.selection_set(rows[:2]); captured=[]
            with patch.object(app.right,'ask_drop_action',return_value=True),patch.object(app,'preview_transfer',lambda *a,**k:captured.append((a,k))):
                pane.media_button_pressed(click)
                drop=SimpleNamespace(x_root=app.right.winfo_rootx()+100,y_root=app.right.winfo_rooty()+180)
                pane.media_button_released(drop)
            check(bool(captured) and len(captured[0][0][0])==2,'Internal drag retains selected group and opens preview')
            for choice,expected in ((True,False),(False,True),(None,None)):
                captured=[]
                with patch.object(app.right,'ask_drop_action',return_value=choice),patch.object(app,'preview_transfer',lambda *a,**k:captured.append((a,k))):
                    result=app.right.copy_dropped_files([source/'image0.png'],dest)
                if choice is None: check(not captured and result==m.REFUSE_DROP,'Cancel drop leaves transfer preview closed')
                else: check(len(captured)==1 and captured[0][1]['move'] is expected,'Drop action preserves Copy/Move meaning')
            with patch('transfer_ui.simpledialog.askstring',return_value='Test new folder'): pane.new_folder()
            pump()
            check((source/'Test new folder').is_dir(),'Pane New Folder creates destination')
            pane.view_mode_var.set('Thumbnails'); pane.details_frame.pack_forget(); pane.thumbnail_frame.pack(fill='both',expand=True); pane.render_thumbnail_grid(); pump(.8)
            pane.clear_checks(); card=next(iter(pane.thumbnail_cells.values()))
            origin=SimpleNamespace(widget=pane.thumbnail_canvas,state=0,x_root=pane.thumbnail_canvas.winfo_rootx()+2,y_root=pane.thumbnail_canvas.winfo_rooty()+2)
            final=SimpleNamespace(widget=pane.thumbnail_canvas,state=0,x_root=card.winfo_rootx()+card.winfo_width()-2,y_root=card.winfo_rooty()+card.winfo_height()-2)
            pane.rubber_start(origin); pane.rubber_motion(final); pane.rubber_end(final); pump()
            check(bool(pane.highlighted_items()) and not pane.checked_paths,'Thumbnail rubber-band highlights without ticking')
            pane.view_mode_var.set('Details'); pane.thumbnail_frame.pack_forget(); pane.details_frame.pack(fill='both',expand=True); pump()
            pane.clear_checks(); pane.tree.selection_set(first)
            def cancel_preview():
                dialog=next(w for w in children(app) if isinstance(w,m.tk.Toplevel) and w.title()=='Copy files')
                check(any(isinstance(w,m.ttk.Radiobutton) and 'Files only' in w.cget('text') for w in children(dialog)),'Transfer preview folder choices')
                dialog.destroy()
            app.after(250,cancel_preview); app.preview_transfer([source/'image0.png'],source,dest)
            app.enqueue_operation([(source/'image0.png',dest/'image0.png')],False,'Test',policies=['skip'])
            deadline=time.monotonic()+30
            while time.monotonic()<deadline and (not (dest/'image0.png').exists() or app.operation_running): pump(.05)
            check((dest/'image0.png').is_file() and not app.operation_running,'Queue copied file and completed')
            with patch.object(m.messagebox,'showinfo',lambda *a,**k:None),patch.object(m.messagebox,'showerror',lambda *a,**k:errors.append(str(a))):
                app.undo_last()
                deadline=time.monotonic()+35
                while app.operation_running and time.monotonic()<deadline: pump(.05)
            check(not app.operation_running,'Undo completes without blocking the event loop')
            pump()
            check(not (dest/'image0.png').exists() and (source/'image0.png').exists(),'Queue copy undo')
            import subprocess, threading
            clip=source/'undo-preview.mp4'; copied=dest/clip.name
            subprocess.run([m.bundled_command('ffmpeg'),'-v','error','-f','lavfi','-i','color=c=blue:s=320x180:r=15','-t','3','-c:v','mpeg4','-y',str(clip)],check=True,capture_output=True)
            app.enqueue_operation([(clip,copied)],False,'Preview Undo test',policies=['skip'])
            deadline=time.monotonic()+30
            while time.monotonic()<deadline and (app.operation_running or not app.operation_queue.empty()): pump(.05)
            app.right_preview.show_item(m.inspect_media(copied)); pump(.3)
            check(app.right_preview.process is not None and app.right_preview.process.poll() is None,'Real video preview active before Undo')
            from transfer_engine import MEDIA_ACCESS
            reading=threading.Event(); release=threading.Event(); responsive=[]
            def held_reader():
                with MEDIA_ACCESS.read(): reading.set(); release.wait(3)
            reader=threading.Thread(target=held_reader); reader.start(); assert reading.wait(1)
            app.after(50,lambda:responsive.append(True)); threading.Timer(.3,release.set).start()
            with patch.object(m.messagebox,'showinfo',lambda *a,**k:None),patch.object(m.messagebox,'showerror',lambda *a,**k:errors.append(str(a))):
                app.undo_last(); pump(.15)
                check(app.operation_running and responsive and copied.exists(),'Undo waits for reader while UI remains responsive')
                deadline=time.monotonic()+30
                while app.operation_running and time.monotonic()<deadline: pump(.05)
            reader.join(3)
            check(not copied.exists() and clip.exists(),'Undo releases real preview and restores safely after reader finishes')
            (source/'a').mkdir(); (source/'b').mkdir()
            s1=source/'a'/'same.png'; s2=source/'b'/'same.png'; target=dest/'same.png'
            s1.write_bytes(b'first'); s2.write_bytes(b'second'); target.write_bytes(b'original')
            app.enqueue_operation([(s1,target),(s2,target)],True,'Repeated replacement test',policies=['replace','replace'])
            pump(.1); deadline=time.monotonic()+30
            while time.monotonic()<deadline and (app.operation_running or not app.operation_queue.empty()): pump(.05)
            check(target.read_bytes()==b'second' and not s1.exists() and not s2.exists(),'Flattened duplicate replace move')
            app.left.scan(); app.right.scan()
            check(app.left.scan_active and app.right.scan_active,'Metadata scans active at replacement Undo')
            with patch.object(m.messagebox,'showinfo',lambda *a,**k:None),patch.object(m.messagebox,'showerror',lambda *a,**k:errors.append(str(a))): app.undo_last()
            deadline=time.monotonic()+35
            with patch.object(m.messagebox,'showinfo',lambda *a,**k:None),patch.object(m.messagebox,'showerror',lambda *a,**k:errors.append(str(a))):
                while app.operation_running and time.monotonic()<deadline: pump(.05)
            pump()
            if not (s1.exists() and s2.exists() and target.exists() and s1.read_bytes()==b'first' and s2.read_bytes()==b'second' and target.read_bytes()==b'original'):
                print('Replacement undo diagnostic:',{'sources':[p.read_bytes() if p.exists() else None for p in (s1,s2)],'target':target.read_bytes() if target.exists() else None,'errors':errors},flush=True)
            check(s1.read_bytes()==b'first' and s2.read_bytes()==b'second' and target.read_bytes()==b'original','Repeated replacement move undo restores every original')
            print('Callback errors:',errors,flush=True)
            check(not errors,'No Tk callback exceptions')
        finally: app.close_app()
    report={'version':m.APP_VERSION,'checks':results,'callback_errors':errors}
    Path(f'docs/GUI_UPGRADE_{m.APP_VERSION}_ENGLISH.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__': main()
