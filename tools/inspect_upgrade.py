"""Isolated real desktop review of localised upgrade controls; no user settings."""
import json,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import media_sorter as m
from PIL import Image
code=sys.argv[1]; scene=sys.argv[2] if len(sys.argv)>2 else 'transfer'
with tempfile.TemporaryDirectory(prefix='rfm-visual-',ignore_cleanup_errors=True) as directory:
    root=Path(directory); source=root/'source'; dest=root/'destination'; data=root/'settings'
    source.mkdir(); dest.mkdir(); data.mkdir()
    for i in range(6): Image.new('RGB',(640+i*100,360),'blue').save(source/f'Example {i}.png')
    (data/'settings.json').write_text(json.dumps({'language':code,'geometry':'1700x950+30+20','left':{'path':str(source),'show_images':True},'right':{'path':str(dest)},'reminders':{'rating_disabled':True,'support_disabled':True}}),encoding='utf-8')
    m.application_data_directory=lambda:data
    app=m.MediaSorterApp();app.title(f'RFM 12.7.3 QA {code} {scene}')
    def show():
        rows=app.left.tree.get_children();app.left.tree.selection_set(rows[:3])
        if scene=='transfer': app.preview_transfer([p for p in source.glob('*.png')],source,dest)
        elif scene=='basket': app.add_to_selection_basket(app.left);app.show_selection_basket()
        elif scene=='help': app.show_help()
    app.after(1200,show);app.after(180000,app.close_app);app.mainloop()
