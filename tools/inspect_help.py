"""Open an isolated interactive Help window for visual language/RTL review."""
import argparse
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def main():
    import media_sorter as m
    parser=argparse.ArgumentParser(); parser.add_argument("language"); parser.add_argument("--chapter",default="smart_collections"); args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="rfm-help-review-",ignore_cleanup_errors=True) as folder:
        root=Path(folder); (root/"media").mkdir(); settings=root/"settings"; settings.mkdir()
        (settings/"settings.json").write_text(json.dumps({"language":args.language,"geometry":"1400x900+40+30",
            "left":{"path":str(root/"media")},"right":{"path":str(root/"media")},
            "reminders":{"rating_disabled":True,"support_disabled":True}}),encoding="utf-8")
        m.application_data_directory=lambda:settings
        app=m.MediaSorterApp(); app.show_help(); app.update()
        from tools.smoke_test_gui import descendants
        help_window=next(w for w in app.winfo_children() if isinstance(w,m.tk.Toplevel))
        listing=next(w for w in descendants(help_window) if isinstance(w,m.tk.Listbox))
        ids=[c[0] for c in app.translator._chapter_map(app.translator._english)]
        if args.chapter in ids:
            listing.selection_clear(0,"end"); listing.selection_set(ids.index(args.chapter)); listing.event_generate("<<ListboxSelect>>")
        help_window.lift(); app.mainloop()

if __name__=="__main__":main()
