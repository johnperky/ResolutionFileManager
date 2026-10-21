"""Explain safe asynchronous Undo beside the existing safety instructions."""
import json
from pathlib import Path
from sync_help_master import main as sync
root=Path(__file__).resolve().parents[1]
path=root/'docs/help/en.json'
master=json.loads(path.read_text(encoding='utf-8'))
chapter=next(c for c in master['chapters'] if c['id']=='safe_file_actions')
chapter['paragraphs']=[p for p in chapter['paragraphs'] if p['id']!='safe_file_actions.undo_busy_1273']
chapter['paragraphs'].append({'id':'safe_file_actions.undo_busy_1273','text':'Undo runs in the background so the window remains responsive. It temporarily stops the previews and pauses new metadata and thumbnail file reads while existing reads finish, then restores the files. You do not need to wait for a folder scan to finish first. Brief Windows file-sharing locks are retried automatically. If another program still holds a file, or a restored source would replace a newly created file, Undo stops and reports the problem rather than overwriting it. Completed recovery steps are retained; unfinished steps and original replacement backups remain available. Close the application using the affected file or resolve the reported conflict, then press Undo again to resume. Queued transfers wait while recovery is incomplete. Do not delete recovery backups or edit the affected files while recovery is incomplete. Preview toggles remain as chosen; select a file again after recovery to resume previewing.'})
path.write_text(json.dumps(master,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sync()
english=root/'locales/en.json'
pack=json.loads(english.read_text(encoding='utf-8'))
for text in ('Undo in progress…','\nUnfinished recovery steps and backups were retained. Close applications using these files, then press Undo again.',
             'Undo would overwrite an existing file: {target}. Both files were retained.',
             'Undo target is missing; recovery retained: {target}', 'Undo backup is missing: {backup}'):
    pack.setdefault('literals',{})[text]=text
english.write_text(json.dumps(pack,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
