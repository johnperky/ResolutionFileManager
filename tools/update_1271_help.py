"""Mechanical corrections to English-only review instructions."""
import json
from pathlib import Path
from sync_help_master import main as sync
root=Path(__file__).resolve().parents[1]
path=root/'docs/help/en.json'; master=json.loads(path.read_text(encoding='utf-8'))
changes={
    'Choose Small, Medium, or Large beside the view selector.':'Use the thumbnail-size slider beside the view selector. Named size presets remain under View > Thumbnail size.',
    'The small slider beside the Small/Medium/Large selector':'The small slider beside the Details/Thumbnails selector',
    'The three named sizes remain available as quick presets.':'Named size presets remain available in the View menu; there is no duplicate size dropdown in the pane heading.',
    'Selection basket: choose File > Selection basket… or right-click selected files and choose Add to selection basket.':'Selection basket: use the Selection basket toolbar button, File > Selection basket…, or right-click selected files and choose Add to selection basket. The basket is a collapsible panel above both browsers, not a separate window. Hide basket or the toolbar button hides it without clearing its references.',
    'Start on empty space, not a thumbnail image or filename, because dragging a file starts a transfer instead.':'Start on empty thumbnail space, not an image or filename, because dragging a thumbnail file starts a transfer instead. In Details you can also drag vertically across rows to build a group; drag towards the other pane for a transfer.'
}
for before,after in changes.items():
    matches=0
    for chapter in master['chapters']:
        for paragraph in chapter['paragraphs']:
            if before in paragraph['text']:
                paragraph['text']=paragraph['text'].replace(before,after); matches+=1
    assert matches==1,(before,matches)
path.write_text(json.dumps(master,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); sync()
