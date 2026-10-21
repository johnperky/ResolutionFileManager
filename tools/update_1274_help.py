"""Keep the existing transfer instructions accurate after explicit action buttons."""
import json
from pathlib import Path
from sync_help_master import main as sync
root=Path(__file__).resolve().parents[1];path=root/'docs/help/en.json'
master=json.loads(path.read_text(encoding='utf-8'))
paragraph=next(p for c in master['chapters'] for p in c['paragraphs'] if p['id']=='copying_and_moving.p005')
paragraph['text']=paragraph['text'].replace('A drop asks whether to Copy (Yes), Move (No), or Cancel, then opens the transfer preview.','A drop offers clearly labelled Copy, Move and Cancel buttons. Copy or Move opens the transfer preview; Cancel or closing the prompt leaves the files unchanged.')
path.write_text(json.dumps(master,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sync()
