"""Regression checks through Tk bindings, not direct selection-handler calls."""
import json, sys, tempfile, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import Image
import media_sorter as m

def main():
    results=[]; errors=[]
    with tempfile.TemporaryDirectory(prefix='rfm-layout-',ignore_cleanup_errors=True) as directory:
        root=Path(directory); media=root/'media'; media.mkdir(); settings=root/'settings'; settings.mkdir()
        for i in range(8): Image.new('RGB',(400,300),'green').save(media/f'picture{i}.png')
        state={'path':str(media),'show_images':True,'inspector_enabled':True,'inspector_width':9000,'folder_width':9000}
        if '--interactive-thumbnails' in sys.argv: state.update(view_mode='Thumbnails',inspector_enabled=False)
        (settings/'settings.json').write_text(json.dumps({'language':'en','geometry':'1500x900','left':state,'right':state,'reminders':{'rating_disabled':True,'support_disabled':True}}))
        m.application_data_directory=lambda:settings
        app=m.MediaSorterApp(); app.report_callback_exception=lambda *a:errors.append(str(a[1]))
        if '--interactive' in sys.argv or '--interactive-thumbnails' in sys.argv:
            app.title(f'Resolution File Manager {m.APP_VERSION} — isolated mouse review')
            app.mainloop()
            return
        def pump(seconds=.3):
            end=time.monotonic()+seconds
            while time.monotonic()<end: app.update(); time.sleep(.01)
        def check(value,name):
            print(name,value,flush=True); assert value,name; results.append(name)
        def event(widget,kind,x,y,state=0):
            widget.event_generate(kind,x=x,y=y,rootx=widget.winfo_rootx()+x,rooty=widget.winfo_rooty()+y,state=state); pump(.04)
        try:
            pump(2)
            for pane in (app.left,app.right):
                toolbar_width=pane.selection_toolbar.winfo_width()
                check(abs(pane.inspector_frame.winfo_width()-180)<12,'Inspector uses compact 180px default')
                for button in pane.inspector_buttons.winfo_children():
                    check(button.winfo_x()+button.winfo_width()<=pane.inspector_buttons.winfo_width()+1,'Compact Info action buttons remain visible')
                check(pane.media_frame.winfo_width()>=160,'Files remain visible with oversized saved inspector/folder widths')
                pane.inspector_panes.sashpos(0,0); pump(.05); pane.remember_inspector_width(); pump(.05)
                check(pane.media_frame.winfo_width()>=160,'Dragging Info to edge cannot hide files after release')
                pane.inspector_panes.sashpos(0,pane.inspector_panes.winfo_width()-240); pane.remember_inspector_width()
                pane.inspector_enabled_var.set(False); pane.toggle_inspector(); pump()
                check(pane.media_frame.winfo_width()>250,'Files fill pane after hiding inspector')
                check(pane.selection_toolbar.winfo_width()==toolbar_width,'Info toggle does not squeeze top tick controls')
                pane.inspector_enabled_var.set(True); pane.toggle_inspector(); pump()
                check(abs(pane.inspector_frame.winfo_width()-240)<15,'Inspector width survives toggle')
                check(pane.selection_toolbar.winfo_width()==toolbar_width,'Info restore leaves selection toolbar width unchanged')
                pane.inspector_enabled_var.set(False); pane.toggle_inspector()
            pump(); pane=app.left; tree=pane.tree; rows=tree.get_children(); check(len(rows)==8,'Rows available')
            check(not pane.thumbnail_slider.winfo_ismapped(),'Thumbnail slider is hidden in Details')
            remembered_size=pane.thumbnail_pixels.get()
            pane.set_view_mode('Thumbnails'); pump()
            check(pane.thumbnail_slider.winfo_ismapped(),'Thumbnail slider is visible in Thumbnails')
            pane.set_view_mode('Details'); pump()
            check(not pane.thumbnail_slider.winfo_ismapped() and pane.thumbnail_pixels.get()==remembered_size,'View switching preserves thumbnail size without showing slider in Details')
            old_focus=pane.folder_tree.focus(); synthetic=pane.folder_tree.insert('','end',text='Alignment test',open=True)
            parent=synthetic
            for depth in range(35): parent=pane.folder_tree.insert(parent,'end',text=f'Level {depth}',open=True)
            pane.folder_tree.see(parent); pump()
            check(pane.folder_tree.xview()[0]>0,'Visible deep branches shift left without wasted indentation')
            pane.folder_tree.yview_moveto(0); pump()
            check(pane.folder_tree.xview()[0]==0,'Scrolling back to ancestors resets horizontal alignment without clicking')
            pane.folder_tree.delete(synthetic); pane.folder_tree.see(old_focus); pump()
            for control in pane.selection_toolbar_groups:
                check(control.winfo_x()+control.winfo_width()<=pane.selection_toolbar.winfo_width()+1,'Top selection controls fit the pane width')
            box=tree.bbox(rows[0]); x=100
            event(tree,'<ButtonPress-1>',x,tree.winfo_height()-30)
            event(tree,'<B1-Motion>',x+70,box[1]+3,256)
            event(tree,'<ButtonRelease-1>',x+70,box[1]+3)
            check(len(pane.highlighted_items())>=4 and not pane.checked_paths,'Rectangle highlights files without ticking')
            old_tick=tree.item(rows[-1],'tags')[0]; pane.checked_paths.add(old_tick); pane.refresh_checks()
            event(tree,'<ButtonPress-1>',x,tree.winfo_height()-30)
            event(tree,'<B1-Motion>',x+70,box[1]+3,256)
            event(tree,'<ButtonRelease-1>',x+70,box[1]+3)
            check(pane.checked_paths=={old_tick},'Existing ticks survive a new rectangle selection')
            pane.clear_checks(); check_row=rows[0]; row_box=tree.bbox(check_row,'#0'); cy=row_box[1]+row_box[3]//2
            event(tree,'<ButtonPress-1>',row_box[0]+2,cy)
            event(tree,'<ButtonRelease-1>',row_box[0]+2,cy)
            check(not pane.checked_paths,'Click beside checkbox does not tick the row')
            from types import SimpleNamespace
            hit_x=next(px for px in range(row_box[0],row_box[0]+row_box[2]) if pane.checkbox_hit(SimpleNamespace(widget=tree,x=px,y=cy)))
            event(tree,'<ButtonPress-1>',hit_x,cy)
            check(not pane.checked_paths,'Checkbox does not toggle on mouse-down')
            event(tree,'<ButtonRelease-1>',hit_x,cy)
            check(len(pane.checked_paths)==1,'Precise checkbox click toggles on release')
            retained=set(pane.checked_paths)
            event(tree,'<ButtonPress-1>',hit_x,cy)
            event(tree,'<B1-Motion>',hit_x+20,cy+75,256)
            event(tree,'<ButtonRelease-1>',hit_x+20,cy+75)
            check(pane.checked_paths==retained and not pane.rubber_active,'Dragging from checkbox selects without toggling it')
            pane.checked_paths={old_tick}; pane.refresh_checks()
            event(tree,'<ButtonPress-1>',x,tree.winfo_height()-30)
            event(app.right.tree,'<B1-Motion>',100,80,256)
            event(app.right.tree,'<ButtonRelease-1>',100,80)
            check(not pane.rubber_active and pane.checked_paths=={old_tick},'Release across other pane reliably ends rectangle without changing ticks')
            pane.clear_checks(); tree.selection_set(())
            event(tree,'<ButtonPress-1>',x,box[1]+5)
            event(tree,'<B1-Motion>',x+3,box[1]+85,256)
            event(tree,'<ButtonRelease-1>',x+3,box[1]+85)
            check(len(pane.highlighted_items())>=3 and not pane.checked_paths,'Row drag highlights without ticking')
            pane.tick_highlighted(); ticked=set(pane.checked_paths)
            tree.selection_set(rows[-1]); pane.tick_highlighted()
            check(pane.checked_paths==ticked|{tree.item(rows[-1],'tags')[0]},'Tick selection adds to existing ticks')
            pane.untick_highlighted(); check(pane.checked_paths==ticked,'Untick selection removes only highlighted group')
            app.add_to_selection_basket(pane); pump()
            check(not isinstance(app.basket_panel,m.tk.Toplevel) and app.basket_panel.winfo_ismapped(),'Basket is docked in main window')
            check(app.basket_panel.winfo_rooty()<app.workspace_panes.winfo_rooty(),'Basket sits above browsers')
            check(len(app.basket_tree.get_children())>=3,'Docked basket shows selected references')
            app.hide_selection_basket(); pump(); check(not app.basket_panel.winfo_ismapped(),'Basket can collapse')
            pane.view_mode_var.set('Thumbnails'); pane.details_frame.pack_forget(); pane.thumbnail_frame.pack(fill='both',expand=True); pane.render_thumbnail_grid(); pump(.7)
            pane.clear_checks(); card=next(iter(pane.thumbnail_cells.values())); label=next(w for w in card.winfo_children() if isinstance(w,m.tk.Label))
            canvas=pane.thumbnail_canvas
            event(canvas,'<ButtonPress-1>',canvas.winfo_width()-30,canvas.winfo_height()-30)
            event(label,'<B1-Motion>',label.winfo_width()//2,5,256)
            event(label,'<ButtonRelease-1>',label.winfo_width()//2,5)
            check(len(pane.highlighted_items())>=1 and not pane.checked_paths and not pane.rubber_active,'Thumbnail drag highlights without changing ticks')
            checkbox=card.check_label
            event(checkbox,'<ButtonPress-1>',0,0)
            event(checkbox,'<ButtonRelease-1>',0,0)
            check(not pane.checked_paths,'Thumbnail checkbox padding does not toggle')
            event(checkbox,'<ButtonPress-1>',checkbox.winfo_width()//2,checkbox.winfo_height()//2)
            check(not pane.checked_paths,'Thumbnail checkbox waits for release')
            event(checkbox,'<ButtonRelease-1>',checkbox.winfo_width()//2,checkbox.winfo_height()//2)
            check(len(pane.checked_paths)==1,'Thumbnail checkbox centre toggles once')
            check(not errors,'No callback exceptions')
        finally: app.close_app()
    Path(f'docs/GUI_LAYOUT_{m.APP_VERSION}.json').write_text(json.dumps({'checks':results,'errors':errors},indent=2)+'\n')

if __name__=='__main__': main()
