"""CPU inference subprocess: a frozen app dispatches here before opening Tk."""
import json
from pathlib import Path
import sys
import threading
import time
import os
import traceback
from ai_backends import infer_image,validate_assets


def serve(job):
    """Keep CPU sessions warm for one owned still-image batch."""
    root=Path(job['assets']);validate_assets(root)
    directory=Path(job['directory']);sequence=1
    while True:
        # Publish each message once. Windows readers need not share deletion.
        request=directory/f'request-{sequence}.json';response=directory/f'response-{sequence}.json'
        if not request.exists():time.sleep(.025);continue
        value=json.loads(request.read_text(encoding='utf-8'))
        result={'id':value['id']}
        try:
            validate_assets(root)
            infer_image(value['input'],value['output'],value['mode'],'cpu',root,threading.Event())
        except Exception as exc:
            result['error']=str(exc)
        temporary=response.with_suffix('.tmp')
        temporary.write_text(json.dumps(result),encoding='utf-8');temporary.replace(response)
        sequence+=1


def main(job_path):
    job=json.loads(Path(job_path).read_text())
    if job.get('session'):return serve(job)
    try:
        root=Path(job['assets']);validate_assets(root)
        if job.get('video_stream'):
            from ai_video_stream import stream_cpu
            def progress(done):
                with Path(job['progress']).open('a',encoding='utf-8') as stream:
                    stream.write(json.dumps({'done':done})+'\n')
            return stream_cpu(job['source'],job['work'],job['info'],job['timestamps'],job['durations'],job['mode'],root,progress,preview_directory=job.get('preview_directory'))
        source=Path(job['source']);dest=Path(job['dest']);dest.mkdir(exist_ok=True)
        frames=sorted(source.glob('*.png'));started=time.monotonic()
        for index,frame in enumerate(frames):
            infer_image(frame,dest/frame.name,job['mode'],'cpu',root,threading.Event())
            progress={'done':index+1,'total':len(frames),'fps':(index+1)/max(.001,time.monotonic()-started)}
            # Append framed records: Windows readers may hold a file open
            # without delete sharing, so replacing a progress file can fail.
            with Path(job['progress']).open('a',encoding='utf-8') as stream:
                stream.write(json.dumps(progress)+'\n')
    except Exception:
        Path(job['error']).write_text(traceback.format_exc(),encoding='utf-8');raise

if __name__=='__main__':main(sys.argv[1])
