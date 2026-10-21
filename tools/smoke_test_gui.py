"""Isolated real-Tk tests of scanning, Smart Collections and Help navigation."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)

def smoke(language):
    import media_sorter as m
    from rtl_display import needs_visual_order, ordered
    from PIL import Image
    with tempfile.TemporaryDirectory(prefix="rfm-gui-test-",ignore_cleanup_errors=True) as folder:
        root=Path(folder); media=root/"media"; media.mkdir(); (media/"nested").mkdir()
        Image.new("RGB",(640,480),"blue").save(media/"small.jpg")
        Image.new("RGB",(1920,1080),"green").save(media/"nested"/"large.png")
        subprocess.run([shutil.which("ffmpeg"),"-v","error","-f","lavfi","-i","color=c=red:s=320x240:d=1","-c:v","mpeg4",str(media/"test.mp4")],check=True,timeout=20)
        subprocess.run([shutil.which("ffmpeg"),"-v","error","-f","lavfi","-i","color=c=blue:s=1280x720:d=1","-c:v","mpeg4",str(media/"nested"/"larger.mp4")],check=True,timeout=20)
        settings=root/"settings"; settings.mkdir()
        (settings/"settings.json").write_text(json.dumps({"language":language,"geometry":"1500x950+0+0",
            "performance_profile":"Quiet","scan_workers":1,
            "left":{"path":str(media),"recursive":True},"right":{"path":str(media),"recursive":True},
            "reminders":{"rating_disabled":True,"support_disabled":True}}),encoding="utf-8")
        m.application_data_directory=lambda:settings
        app=m.MediaSorterApp()
        failures=[]
        app.report_callback_exception=lambda *args:failures.append(str(args[1]))
        try:
            deadline=time.monotonic()+30
            while time.monotonic()<deadline:
                app.update()
                if len(app.left.items)==4 and not app.left.scan_active and not app.right.scan_active: break
                time.sleep(.03)
            assert len(app.left.items)==4,"recursive media scan did not finish"
            p=app.left; app.set_active(p)
            # Regression coverage for the real controls used in Store captures.
            for pane in (app.left,app.right):
                assert pane.checked_label_var.get()==app.tr("pane.checked",count=0),"initial tick counter is not localized"
                font=m.tkfont.Font(root=app,font=m.ttk.Style(app).lookup("Treeview.Heading","font") or "TkHeadingFont")
                for column in pane.tree['columns']:
                    assert pane.tree.column(column,'width')>=font.measure(pane.tree.heading(column,'text'))+24, f"clipped default heading: {column}"
            p.checked_paths.update(list(p.items)[:2]); p.refresh_checks()
            assert p.checked_label_var.get()==app.tr("pane.checked",count=2),"updated tick counter is not localized"
            p.clear_checks()
            p.tree.column('size',width=60)
            saved=p.get_state(); assert saved['column_width_language']==language
            p.apply_state(saved); app.update()
            assert p.tree.column('size','width')==60,"same-language manual resizing was lost"
            saved['column_width_language']='previous-language'
            p.apply_state(saved); app.update()
            assert p.tree.column('size','width')>=font.measure(p.tree.heading('size','text'))+24,"language change did not fit heading"
            p.reset_column_widths(); app.update()
            # Restoring a saved pane legitimately schedules a new asynchronous
            # scan. Do not test sorting against its partially populated results.
            deadline=time.monotonic()+20
            while time.monotonic()<deadline and (p.scan_active or len(p.items)!=4):
                app.update(); time.sleep(.03)
            assert not p.scan_active and len(p.items)==4,"workspace-restore scan did not finish"
            p.show_videos_var.set(False); p.show_images_var.set(True)
            p.sort_column="resolution"; p.sort_reverse=False; p.refresh_view(); app.update()
            assert [i.width for i in p.visible_items]==[640,1920],"image resolution sorting"
            assert app.save_smart_collection("Test images")
            p.show_images_var.set(False); p.show_videos_var.set(True)
            p.refresh_view(); app.update()
            assert [i.width for i in p.visible_items]==[320,1280],"video resolution sorting"
            assert app.apply_smart_collection("Test images",p)
            deadline=time.monotonic()+20
            while time.monotonic()<deadline:
                app.update()
                if len(p.visible_items)==2 and not p.scan_active: break
                time.sleep(.03)
            assert len(p.visible_items)==2,"saved image filter not restored"
            app.show_help(); app.update()
            help_window=[w for w in app.winfo_children() if isinstance(w,m.tk.Toplevel)][-1]
            widgets=list(descendants(help_window))
            listing=next(w for w in widgets if isinstance(w,m.tk.Listbox))
            reader=next(w for w in widgets if isinstance(w,m.tk.Text))
            expected=app.translator.help_chapters()
            visual=needs_visual_order(language)
            assert listing.size()==len(expected)
            for index,(_title,body) in enumerate(expected):
                listing.selection_clear(0,"end"); listing.selection_set(index)
                listing.event_generate("<<ListboxSelect>>"); app.update()
                rendered=reader.get("1.0","end")
                assert (ordered(_title)[0] if visual else _title) in rendered, f"chapter navigation {index}"
                if not visual and "[chapter:" not in body: assert body.replace("{version}",m.APP_VERSION) in rendered
            # Index link bindings exist for every chapter; invoke one callback
            # through its real Tcl binding and confirm navigation.
            chapter_ids=[entry[0] for entry in app.translator._chapter_map(app.translator._english)]
            listing.selection_clear(0,"end"); listing.selection_set(chapter_ids.index("topic_index"))
            listing.event_generate("<<ListboxSelect>>"); app.update()
            links=[tag for tag in reader.tag_names() if tag.startswith("link_")]
            assert links,"topic index has no clickable links"
            target="link_smart_collections"
            script=reader.tk.call(reader._w,"tag","bind",target,"<Button-1>")
            assert script,"Smart Collections index link has no callback"
            ranges=reader.tag_ranges(target)
            assert ranges,"Smart Collections index link not rendered"
            reader.see(ranges[0]); app.update()
            box=reader.bbox(ranges[0]); assert box,"index link not visible after scrolling"
            reader.event_generate("<Motion>",x=box[0]+2,y=box[1]+2)
            reader.event_generate("<Button-1>",x=box[0]+2,y=box[1]+2); app.update()
            smart_title=next(title for ident,(title,_body) in zip(app.translator._chapter_map(app.translator._english),expected) if ident[0]=="smart_collections")
            assert (ordered(smart_title)[0] if visual else smart_title) in reader.get("1.0","2.0"),"clicking index link did not navigate"
            search_entry=next(w for w in widgets if isinstance(w,m.ttk.Entry))
            search_entry.delete(0,"end"); search_entry.insert(0,"smart_collections.json")
            search_button=next(w for w in widgets if isinstance(w,m.ttk.Button) and str(w.cget("text"))==app.tr("pane.find").rstrip(":"))
            search_button.invoke(); app.update()
            assert 0<listing.size()<len(expected),"full-text search did not filter chapters"
            assert reader.tag_ranges("search_hit"),"search results not highlighted"
            next_match=next(w for w in widgets if isinstance(w,m.ttk.Button) and str(w.cget("text"))==app.tr("help.next_match"))
            next_match.invoke(); app.update()
            assert reader.tag_ranges("search_current"),"next match did not select a result"
            clear=next(w for w in widgets if isinstance(w,m.ttk.Button) and str(w.cget("text"))==app.tr("help.clear"))
            clear.invoke(); app.update()
            assert listing.size()==len(expected),"clear search did not restore chapters"
            assert reader.tag_cget("body","justify")==("right" if app.is_rtl else "left")
            help_window.destroy()
            p.edit_advanced_filters(); app.update()
            dialog=[w for w in descendants(app) if isinstance(w,m.tk.Toplevel)][-1]
            assert dialog.title()==app.tr("filters.title"); dialog.destroy()
            assert not app.translator.diagnostics,app.translator.diagnostics
            assert not failures,failures
            return {"language":language,"version":m.APP_VERSION,"scan_files":4,"help_chapters":len(expected),
                "rtl":app.is_rtl,"passed":True,"visual_review":"not performed; geometry/text/navigation tested programmatically"}
        finally:
            app.close_app()

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("languages",nargs="*")
    parser.add_argument("--single"); parser.add_argument("--report"); args=parser.parse_args()
    if args.single:
        print(json.dumps(smoke(args.single),ensure_ascii=True)); return
    from localization import SUPPORTED_LANGUAGES
    results=[]
    for code in args.languages or SUPPORTED_LANGUAGES:
        child=subprocess.run([sys.executable,str(Path(__file__)),"--single",code],capture_output=True,text=True,encoding="utf-8",timeout=90)
        if child.returncode:
            results.append({"language":code,"passed":False,"error":child.stderr[-3000:]})
        else:
            results.append(json.loads(child.stdout.strip().splitlines()[-1]))
        print(f"{code}: {'PASS' if results[-1]['passed'] else 'FAIL'}",flush=True)
    if args.report: Path(args.report).write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if not all(r["passed"] for r in results): raise SystemExit(1)

if __name__=="__main__": main()
