"""Mechanical English review correction: highlighting is not ticking."""
import json
from pathlib import Path
from sync_help_master import main as sync
root=Path(__file__).resolve().parents[1]; path=root/'docs/help/en.json'
master=json.loads(path.read_text(encoding='utf-8'))
for chapter in master['chapters']:
    for paragraph in chapter['paragraphs']:
        if paragraph['id']=='selecting_and_previewing.p007':
            paragraph['text']='Drag from empty browser space across rows or thumbnail cards to highlight a group with an outlined selection rectangle. This does not tick or untick any files. A plain drag starts a new highlighted group; hold Ctrl while starting the drag to add to existing highlights. Start on empty thumbnail space, not an image or filename, because dragging a thumbnail file starts a transfer instead. In Details you can also drag vertically across rows to highlight a group; drag towards the other pane for a transfer. Headers retain their normal resizing and reordering gestures. Use Tick selection to add the highlighted files to the existing ticked action group. Use Untick selection to remove only those highlighted files from that group. Both buttons are at the top of each browser beside Sort, Select all shown and Clear ticks; controls wrap on narrower panes. Both commands are also available in the right-click menus. Other ticks, including files hidden by filters, are retained. File actions continue to prefer all ticks when any exist, so use these explicit controls before copying or moving if you want to change the action group.'
        if paragraph['id']=='selecting_and_previewing.p008':
            paragraph['text']=paragraph['text'].replace('Info opens to a useful width rather than a narrow strip.','Info opens at a compact starting width of about 180 pixels. The top Sort and selection controls are independent of the Info divider, so opening Info does not squeeze those buttons.')
            paragraph['text']=paragraph['text'].replace('The small slider beside the Details/Thumbnails selector adjusts thumbnail size continuously.','The thumbnail-size slider appears only in Thumbnails; Details hides it. Moving it adjusts thumbnail size continuously, and switching views retains its setting.')
        if paragraph['id']=='getting_started.tree_alignment_1272':
            paragraph['text']='The folder tree automatically aligns the currently visible branches to avoid wasted indentation. When you scroll down into deeper branches it shifts horizontally; scrolling back up to ancestors returns it left without requiring a click. The full hierarchy remains available, and the horizontal scrollbar beneath the tree permits manual horizontal viewing.'
    if chapter['id']=='getting_started' and not any(p['id']=='getting_started.tree_alignment_1272' for p in chapter['paragraphs']):
        chapter['paragraphs'].append({'id':'getting_started.tree_alignment_1272','text':'For deeply nested folders, the folder tree automatically shifts horizontally so the selected folder and its expand arrow remain near the left edge instead of leaving a wide empty indentation. The full hierarchy remains available: use the horizontal scrollbar beneath the tree to look back across ancestors. Navigation or resizing realigns the current folder.'})
    if chapter['id']=='selecting_and_previewing' and not any(p['id']=='selecting_and_previewing.checkbox_accuracy_1272' for p in chapter['paragraphs']):
        chapter['paragraphs'].append({'id':'selecting_and_previewing.checkbox_accuracy_1272','text':'Checkboxes change only when you click and release on the box without dragging. Empty space beside a box is not part of its clickable area. Moving more than a few pixels starts a highlight selection instead and leaves the ticks unchanged, even when the drag began on a checkbox. Use the explicit Tick selection and Untick selection controls to change an entire highlighted group.'})
# Keep instructions beside their subject instead of accumulating an update appendix.
selection=next(c for c in master['chapters'] if c['id']=='selecting_and_previewing')
by_id={p['id']:p for p in selection['paragraphs']}
combined=by_id.pop('selecting_and_previewing.p008',None)
if combined:
    info_text, slider_text=combined['text'].split(' The thumbnail-size slider',1)
    info=by_id['selecting_and_previewing.p003']
    if info_text not in info['text']:
        info['text']+=' '+info_text
    details=next(c for c in master['chapters'] if c['id']=='details_and_thumbnails')
    if not any(p['id']=='details_and_thumbnails.size_slider_1272' for p in details['paragraphs']):
        details['paragraphs'].append({'id':'details_and_thumbnails.size_slider_1272','text':'The thumbnail-size slider'+slider_text})
order=['selecting_and_previewing.p001','selecting_and_previewing.checkbox_accuracy_1272',
       'selecting_and_previewing.p007','selecting_and_previewing.p002',
       'selecting_and_previewing.p006','selecting_and_previewing.p003',
       'selecting_and_previewing.p004','selecting_and_previewing.p005']
selection['paragraphs']=[by_id.pop(key) for key in order if key in by_id]+list(by_id.values())
path.write_text(json.dumps(master,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); sync()
