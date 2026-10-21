"""One native pilot: Tools toggle affects both panes, persists, leaves geometry."""
import json
from pathlib import Path
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import Image
import media_sorter as m


with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
    root=Path(directory);media=root/'media';media.mkdir();data=root/'settings';data.mkdir()
    (media/'.private').mkdir()
    for name in ('normal.png','.hidden.png','.private/inside.png'):
        Image.new('RGB',(80,60),'green').save(media/name)
    (data/'settings.json').write_text(json.dumps({'language':'en','geometry':'1500x900','left':{'path':str(media),'recursive':True},'right':{'path':str(media),'recursive':True},'reminders':{'rating_disabled':True,'support_disabled':True}}),encoding='utf-8')
    m.application_data_directory=lambda:data
    app=m.MediaSorterApp()
    errors=[];app.report_callback_exception=lambda *exc:errors.append(str(exc[1]))
    def wait(count):
        until=time.monotonic()+15
        while time.monotonic()<until:
            app.update();time.sleep(.02)
            if all(not p.scan_active and len(p.items)==count for p in (app.left,app.right)):return
        raise AssertionError(f'Expected {count} files in both panes')
    try:
        wait(1)
        # The application restores its saved sash positions after 300ms.
        # Fast Linux fixture scans can finish before that startup callback.
        settled=time.monotonic()+.6
        while time.monotonic()<settled:app.update();time.sleep(.02)
        geometry=app.geometry();split=app.browser_panes.sash_coord(0)
        menu=app.nametowidget(app.cget('menu'))
        tool_index=next(index for index in range(menu.index('end')+1) if menu.type(index)=='cascade' and menu.entrycget(index,'label')==app.tr('menu.tools'))
        tools=app.nametowidget(menu.entrycget(tool_index,'menu'))
        assert tools.type(0)=='checkbutton' and tools.entrycget(0,'label')=='Show hidden files'
        tools.invoke(0);wait(3)
        assert json.loads((data/'settings.json').read_text(encoding='utf-8'))['show_hidden_files'] is True
        assert app.geometry()==geometry and app.browser_panes.sash_coord(0)==split,'Toggle changed window layout'
        app.left.set_view_mode('Thumbnails');app.update()
        tools.invoke(0);wait(1)
        assert not app.show_hidden_files_var.get()
        assert app.geometry()==geometry and app.browser_panes.sash_coord(0)==split
        assert not errors,errors
        print('PASS: native Tools checkbutton, both panes, recursion, persistence, Details/Thumbnails, unchanged geometry')
    finally:app.close_app()
