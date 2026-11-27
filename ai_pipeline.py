"""Owned, cancellable frame preparation and safe conversion publication."""
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from fractions import Fraction
from process_utils import start_owned_process,stop_owned_process
from PIL import Image
from ai_backends import infer_image,mode_spec,gpu_executable,gpu_model_spec,video_gpu_model_spec

@dataclass(frozen=True)
class AIProgress:
    stage:str
    completed:int
    total:int|None
    fraction:float|None
    average_fps:float|None

def publish_output_without_replace(temporary,target):
    temporary=Path(temporary);target=Path(target)
    if os.name=='nt':os.rename(temporary,target)
    else:
        os.link(temporary,target)
        temporary.unlink()

def frame_durations(timestamps,duration):
    if not timestamps:raise ValueError('No video frames found')
    values=[round(b-a,9) for a,b in zip(timestamps,timestamps[1:])]
    if any(v<=0 for v in values):raise ValueError('Unsupported non-increasing frame timestamps')
    last=round(duration-(timestamps[-1]-timestamps[0]),9)
    if last<=0:last=values[-1] if values else max(duration,1/25)
    return values+[last]

def estimate_ai_disk_bytes(width,height,frame_count,mode):
    _,factor=mode_spec(mode)
    # Real-life 2x temporarily uses its native 4x model too.
    native=gpu_model_spec(mode)[1]
    return int(width*height*max(1,frame_count)*4*(1+2*native*native)*1.2+64*1024*1024)

def estimate_ai_video_disk_bytes(width,height,frame_count,mode):
    from ai_video_stream import chunk_size,timed_video_path
    factor=mode_spec(mode)[1];native=video_gpu_model_spec(mode)[1]
    # Huffman's encoder bounds packets at12 bytes/output pixel; keep space
    # conservative even though representative compressed output is far smaller.
    pixel_bytes=12 if timed_video_path('.',{'width':width,'height':height},mode).suffix=='.nut' else 4
    intermediate=width*height*max(1,frame_count)*pixel_bytes*factor*factor
    scratch=width*height*chunk_size(width,height,mode)*4*(1+native*native)
    return int((intermediate+scratch)*1.2+64*1024*1024)


def media_probe(source,ffprobe='ffprobe',frames=False,cancel_event=None):
    entries='stream=index,codec_type,width,height,pix_fmt,color_transfer,bits_per_raw_sample,sample_aspect_ratio,avg_frame_rate,start_time,duration,nb_frames:stream_tags=rotate:stream_side_data=rotation:format=duration'
    if frames:entries+=':frame=best_effort_timestamp_time,pkt_duration_time,duration_time'
    command=[str(ffprobe),'-v','error','-select_streams','v:0','-show_entries',entries]
    if frames:command+=['-show_frames']
    with tempfile.TemporaryFile() as out,tempfile.TemporaryFile() as error:
        process=start_owned_process([*command,'-of','json',str(source)],stdout=out,stderr=error)
        deadline=time.monotonic()+120
        try:
            while process.poll() is None:
                if cancel_event and cancel_event.wait(.05):raise InterruptedError('Conversion cancelled')
                if time.monotonic()>deadline:raise TimeoutError('Video inspection timed out')
                if not cancel_event:time.sleep(.05)
            out.seek(0);error.seek(0)
            if process.returncode:raise ValueError('Cannot inspect video: '+error.read().decode(errors='replace')[-500:])
            data=json.loads(out.read())
        finally:
            stop_owned_process(process)
    streams=data.get('streams',[])
    if not streams:raise ValueError('No video stream')
    v=streams[0]
    rotation=int(next((s.get('rotation',0) for s in v.get('side_data_list',[]) if 'rotation' in s),v.get('tags',{}).get('rotate',0)))
    width,height=int(v.get('width',0)),int(v.get('height',0))
    sar=v.get('sample_aspect_ratio','1:1');sar=tuple(map(int,sar.split(':'))) if ':' in sar and sar!='0:1' else (1,1)
    if rotation%180:width,height=height,width;sar=(sar[1],sar[0])
    rate=v.get('avg_frame_rate','0/1');n,d=map(float,rate.split('/'));fps=n/d if d else 0
    duration=float(v.get('duration',data.get('format',{}).get('duration',0)))
    count=int(v['nb_frames']) if str(v.get('nb_frames','')).isdigit() else math.ceil(duration*fps)
    bits=int(v.get('bits_per_raw_sample') or 0)
    hdr=v.get('color_transfer') in ('smpte2084','arib-std-b67') or bits>8 or any(x in v.get('pix_fmt','') for x in ('p10','p12','p16','p9','rgb48','gbrp10'))
    return {'width':width,'height':height,'sar':sar,'rotation':rotation,'duration':duration,'fps':fps,'count':count,'hdr':hdr,'stream':v,'frames':data.get('frames',[])}

def _run(command,cancel_event,check=None,on_line=None):
    flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
    with tempfile.TemporaryFile() as log:
        p=start_owned_process(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT if on_line else log,text=True,errors='replace')
        lines=queue.Queue()
        def reader():
            for line in p.stdout:lines.put(line.strip())
        thread=threading.Thread(target=reader,daemon=True);thread.start()
        try:
            while p.poll() is None:
                if cancel_event.wait(.1):raise InterruptedError('Conversion cancelled')
                if check:check()
                while not lines.empty():
                    line=lines.get_nowait()
                    if on_line:
                        log.write((line+'\n').encode('utf-8'));on_line(line)
            thread.join(timeout=2)
            while not lines.empty():
                line=lines.get_nowait()
                if on_line:
                    log.write((line+'\n').encode('utf-8'));on_line(line)
            log.seek(0);details=log.read().decode(errors='replace')
            if p.returncode:raise RuntimeError(details[-1800:] or f'Processing failed ({p.returncode})')
        finally:
            stop_owned_process(p)
            thread.join(timeout=2)
            if p.stdout:p.stdout.close()

def prepare_ai_video(source,work_dir,mode,hardware_id,asset_root,cancel_event,on_progress,ffmpeg='ffmpeg',ffprobe='ffprobe',fallback_cpu=False,preview_directory=None):
    work=Path(work_dir);source=Path(source);work.mkdir(exist_ok=True)
    on_progress(AIProgress('Preparing video frames',0,None,None,None))
    info=media_probe(source,ffprobe,True,cancel_event)
    if info['hdr']:raise ValueError('AI currently supports SDR 8-bit input only. Choose ordinary resizing for HDR/high-bit-depth video.')
    if min(info['width'],info['height'],info['fps'],info['duration'])<=0:raise ValueError('AI requires known dimensions, timing and duration')
    timestamps=[float(f['best_effort_timestamp_time']) for f in info['frames'] if 'best_effort_timestamp_time' in f]
    if not timestamps or len(timestamps)!=len(info['frames']):raise ValueError('AI requires presentation timestamps for every frame')
    last=info['frames'][-1] if info['frames'] else {}
    tail=float(last.get('duration_time',last.get('pkt_duration_time',0)) or 0) or 1/info['fps']
    durations=frame_durations(timestamps,timestamps[-1]-timestamps[0]+tail);count=len(durations)
    required=estimate_ai_video_disk_bytes(info['width'],info['height'],count,mode)
    if shutil.disk_usage(work).free<required:raise OSError(f'Not enough temporary disk space; approximately {required//1048576} MB required')
    from ai_video_stream import stream_gpu,timed_video_path
    def disk_check():
        if shutil.disk_usage(work).free<32*1024*1024:raise OSError('Temporary disk space exhausted')
    from conversion_display import PreviewPublisher
    preview=PreviewPublisher(preview_directory)
    started=time.monotonic();completed=[0]
    def progress(done,backend):
        completed[0]=max(completed[0],done)
        done=completed[0]
        on_progress(AIProgress(f'AI upscaling ({backend})',done,count,done/count,done/max(.001,time.monotonic()-started)))
    def run_cpu():
        on_progress(AIProgress('Loading AI model',completed[0],count,None,None))
        progress_path=work/'worker-progress.json';error_path=work/'worker-error.txt'
        progress_path.unlink(missing_ok=True);error_path.unlink(missing_ok=True)
        job=work/'job.json';job.write_text(json.dumps({'preview_directory':str(preview_directory) if preview_directory else None,'video_stream':True,'source':str(source),'work':str(work),'assets':str(asset_root),'mode':mode,'info':info,'timestamps':timestamps,'durations':durations,'progress':str(progress_path),'error':str(error_path)}),encoding='utf-8')
        command=[sys.executable,'--rfm-ai-worker',str(job)] if getattr(sys,'frozen',False) else [sys.executable,str(Path(__file__).with_name('ai_worker.py')),str(job)]
        position=[0];pending=['']
        def cpu_check():
            disk_check()
            if progress_path.exists():
                with progress_path.open(encoding='utf-8') as stream:
                    stream.seek(position[0]);pending[0]+=stream.read();position[0]=stream.tell()
                while '\n' in pending[0]:
                    line,pending[0]=pending[0].split('\n',1)
                    value=json.loads(line);progress(value['done'],'CPU')
        try:_run(command,cancel_event,cpu_check)
        except RuntimeError:
            if error_path.exists():raise RuntimeError(error_path.read_text(encoding='utf-8')) from None
            raise
        cpu_check()
        if cancel_event.is_set():raise InterruptedError('Conversion cancelled')
        return timed_video_path(work,info,mode)
    if hardware_id=='cpu':timed=run_cpu()
    else:
        model_name,native=video_gpu_model_spec(mode);engine=gpu_executable(asset_root)
        if os.name!='nt':engine.chmod(engine.stat().st_mode|0o111)
        def enhance(raw,dest):
            on_progress(AIProgress('Loading AI model',completed[0],count,None,None))
            def saved(line):
                match=re.search(r'(\d{9,})\.png\s*->.*\.png done$',line)
                if match:
                    done=int(match[1])
                    if 0<done<=count:
                        preview.publish_path(dest/f'{done:09d}.png')
                        progress(done,hardware_id)
            command=[str(engine),'-i',str(raw),'-o',str(dest),'-m',str(Path(asset_root)/'models'),'-n',model_name,'-s',str(native),'-g',hardware_id.split(':',1)[1],'-j','1:1:1','-t','128','-f','png','-v']
            _run(command,cancel_event,disk_check,on_line=saved)
        try:
            timed=stream_gpu(source,work,info,timestamps,durations,mode,cancel_event,enhance,lambda done:progress(done,hardware_id),disk_check)
        except RuntimeError:
            if not fallback_cpu:raise
            (work/'frames.mkv').unlink(missing_ok=True)
            (work/'frames.nut').unlink(missing_ok=True)
            on_progress(AIProgress('GPU unavailable; falling back to CPU',0,count,0,None))
            # Restart the source; mixing CPU/GPU precision between chunks can flicker.
            completed[0]=0;hardware_id='cpu';timed=run_cpu()
    if cancel_event.is_set():raise InterruptedError('Conversion cancelled')
    (work/'timing.json').write_text(json.dumps({'count':count,'duration':sum(durations),'last_duration':durations[-1],'source_start':timestamps[0],'hardware':hardware_id,'info':info},indent=2))
    return timed
