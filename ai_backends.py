"""Standalone AI image inference; GPU compute and CPU fallback are explicit."""
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import time
from process_utils import start_owned_process,stop_owned_process
from PIL import Image, PngImagePlugin

MODES={'ordinary':'Ordinary resizing','video_2x':'AI Video 2×','video_hq_2x':'AI Video 2× High quality (slower)','video_4x':'AI Video 4×','animation_2x':'AI Animation 2×','animation_hq_2x':'AI Animation 2× High quality (slower)','animation_4x':'AI Animation 4×','photo_fast_2x':'AI Photo fast 2×','photo_fast_4x':'AI Photo fast 4×'}
VIDEO_MODES={'ordinary':MODES['ordinary'],'fast_video':'Fast enhancement (no AI)',**{k:v for k,v in MODES.items() if k!='ordinary'}}

@dataclass(frozen=True)
class AIHardware:
    id:str
    label:str
    backend:str
    usable:bool
    reason:str=''

def asset_directory():
    return Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent))/'assets/ai'

def mode_spec(mode):
    if mode not in MODES or mode=='ordinary':raise ValueError('Choose a genuine AI mode')
    if mode=='video_hq_2x':return 'video',2
    if mode=='animation_hq_2x':return 'animation',2
    family,factor=mode.rsplit('_',1)
    return family,int(factor[0])


def gpu_model_spec(mode):
    family,factor=mode_spec(mode)
    names={'video':'realesrgan-x4plus','animation':'realesr-animevideov3','photo_fast':'realesr-general-x4v3-medium'}
    return names[family],factor if family=='animation' else 4

def video_gpu_model_spec(mode):
    # Still-photo restoration retains its established model; video2x has its
    # own trained native2x network, never a native4x image followed by shrinking.
    if mode=='video_2x':return 'realesrgan-x2plus',2
    if mode=='animation_2x':return 'realesr-animation-native-x2',2
    return gpu_model_spec(mode)


def video_cpu_model_spec(mode):
    if mode=='video_2x':return 'video_native',2
    if mode=='animation_2x':return 'animation_native',2
    return mode_spec(mode)[0],4


@lru_cache(maxsize=256)
def _verify_asset(path,signature,expected):
    # Fingerprints invalidate cached hashes after replacement or modification.
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    if digest.hexdigest()!=expected:raise ValueError(f'AI resource checksum mismatch: {Path(path).name}')


def validate_assets(root):
    root=Path(root);manifest=json.loads((root/'manifest.json').read_text())
    for name,entry in manifest['files'].items():
        path=(root/name).resolve()
        if not path.is_relative_to(root.resolve()):raise ValueError('Unsafe AI asset path')
        stat=path.stat()
        signature=(stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns,stat.st_ino)
        # Some Linux filesystems keep the same timestamps for quick rewrites.
        # Recently touched files must settle before their hashes are reusable.
        verify=_verify_asset.__wrapped__ if time.time_ns()-max(stat.st_mtime_ns,stat.st_ctime_ns)<1_000_000_000 else _verify_asset
        verify(str(path),signature,entry['sha256'])
    return manifest

def hardware_choice(requested,devices):
    usable=[d for d in devices if d.usable]
    if requested=='auto':
        software=('llvmpipe','lavapipe','swiftshader','software rasterizer','microsoft basic render')
        gpus=[d for d in usable if d.id.startswith('gpu:') and not any(name in d.label.lower() for name in software)]
        gpu=next((d for d in gpus if 'nvidia' in d.label.lower() or 'radeon' in d.label.lower()),gpus[0] if gpus else None)
        if gpu:return gpu
        requested='cpu'
    found=next((d for d in usable if d.id==requested),None)
    if not found:raise ValueError('Requested AI hardware is unavailable; choose Automatic or CPU')
    return found

@lru_cache(maxsize=2)
def _session(model_path,mtime):
    import onnxruntime as ort
    options=ort.SessionOptions();options.intra_op_num_threads=max(1,min(4,os.cpu_count() or 1));options.inter_op_num_threads=1
    return ort.InferenceSession(model_path,sess_options=options,providers=['CPUExecutionProvider'])

def _cpu_image(image,model,root,cancel_event,*,native_scale=4):
    import numpy as np
    path=Path(root)/'cpu'/f'{model}-x{native_scale}.onnx';session=_session(str(path),path.stat().st_mtime_ns)
    # Retain byte pixels for the full image; only the active tile needs floats.
    pixels=np.asarray(image if image.mode=='RGB' else image.convert('RGB'))
    height,width=pixels.shape[:2];result=Image.new('RGB',(width*native_scale,height*native_scale));core=128;pad=32
    for y in range(0,height,core):
        for x in range(0,width,core):
            if cancel_event.is_set():raise InterruptedError('AI cancelled')
            x0=max(0,x-pad);y0=max(0,y-pad);x1=min(width,x+core+pad);y1=min(height,y+core+pad)
            tile=pixels[y0:y1,x0:x1]
            if model=='video_native' and native_scale==2 and (tile.shape[0]%2 or tile.shape[1]%2):
                tile=np.pad(tile,((0,tile.shape[0]%2),(0,tile.shape[1]%2),(0,0)),mode='edge')
            block=np.ascontiguousarray(tile.transpose(2,0,1)[None],dtype=np.float32)
            block/=255.0
            output=session.run(None,{'input':block})[0][0].transpose(1,2,0)
            crop=output[(y-y0)*native_scale:(min(y+core,height)-y0)*native_scale,(x-x0)*native_scale:(min(x+core,width)-x0)*native_scale]
            # Padding supplies model context but is never part of the result.
            # Quantise the retained pixels in place, avoiding full float copies.
            np.multiply(crop,255,out=crop);np.rint(crop,out=crop);np.clip(crop,0,255,out=crop)
            result.paste(Image.fromarray(crop.astype('uint8')),(x*native_scale,y*native_scale))
            del output,crop,block  # Release this tile before allocating the next.
    return result

def gpu_executable(root):
    platform='windows' if sys.platform=='win32' else 'linux'
    return Path(root)/platform/('realesrgan-ncnn-vulkan.exe' if platform=='windows' else 'realesrgan-ncnn-vulkan')

def infer_image(input_path,output_path,mode,hardware_id,asset_root,cancel_event,on_progress=None,*,working_dir=None,timeout=30,resource_check=None,on_diagnostics=None):
    family,factor=mode_spec(mode);input_path=Path(input_path);output_path=Path(output_path);root=Path(asset_root)
    with Image.open(input_path) as source:
        size=source.size
        image=source.convert('RGB') if hardware_id=='cpu' else None
    if hardware_id=='cpu':
        result=_cpu_image(image,family,root,cancel_event)
        if factor==2:result=result.resize((size[0]*2,size[1]*2),Image.Resampling.LANCZOS)
        result.save(output_path,compress_level=1)
    elif hardware_id.startswith('gpu:'):
        engine=gpu_executable(root)
        if sys.platform!='win32':engine.chmod(engine.stat().st_mode|0o111)
        model_name,native=gpu_model_spec(mode)
        with tempfile.TemporaryDirectory(prefix='rfm-ai-image-',dir=working_dir) as directory:
            native_output=output_path if factor==native else Path(directory)/'result.png'
            command=[str(engine),'-i',str(input_path),'-o',str(native_output),'-m',str(root/'models'),'-n',model_name,'-s',str(native),'-g',hardware_id.split(':',1)[1],'-j','1:1:1','-t','128']
            with tempfile.TemporaryFile() as log:
                process=start_owned_process(command,stdout=log,stderr=log)
                deadline=time.monotonic()+timeout if timeout is not None else None
                try:
                    while process.poll() is None:
                        if cancel_event.wait(.05):raise InterruptedError('AI cancelled')
                        if deadline is not None and time.monotonic()>deadline:raise RuntimeError('GPU image inference timed out')
                        if resource_check:resource_check()
                    log.seek(0);details=log.read().decode(errors='replace')
                    if process.returncode or not native_output.is_file():raise RuntimeError('GPU AI failed: '+details[-1500:])
                finally:
                    stop_owned_process(process)
                    if on_diagnostics:
                        # A timeout may still have listed other usable devices.
                        log.seek(0);on_diagnostics(log.read().decode(errors='replace'))
            with PngImagePlugin.PngImageFile(native_output) as raw:
                if raw.size!=(size[0]*native,size[1]*native):raise RuntimeError('AI model returned incorrect dimensions')
                if factor!=native:
                    result=raw.convert('RGB').resize((size[0]*factor,size[1]*factor),Image.Resampling.LANCZOS)
                    result.save(output_path,compress_level=1)
    else:raise ValueError('Unknown AI hardware')
    if cancel_event.is_set():
        output_path.unlink(missing_ok=True);raise InterruptedError('AI cancelled')
    with PngImagePlugin.PngImageFile(output_path) as result:
        if result.size!=(size[0]*factor,size[1]*factor):raise RuntimeError('AI output dimensions mismatch')
    if on_progress:on_progress(1.0)
    return details if hardware_id.startswith('gpu:') else 'CPU'

@lru_cache(maxsize=2)
def probe_hardware(asset_root):
    root=Path(asset_root);validate_assets(root);devices=[]
    with tempfile.TemporaryDirectory(prefix='rfm-ai-probe-') as directory:
        base=Path(directory);source=base/'probe.png'
        image=Image.new('RGB',(8,8));image.putdata([((x*29)%256,(x*41)%256,150) for x in range(64)]);image.save(source)
        try:
            infer_image(source,base/'cpu.png','animation_2x','cpu',root,threading.Event())
            devices.append(AIHardware('cpu','CPU (slower)','onnx',True))
        except Exception as exc:devices.append(AIHardware('cpu','CPU','onnx',False,str(exc)))
        # The bundled engine reports all adapters, even when inference fails.
        # Discover those actual indexes instead of guessing a fixed range.
        pending=[0];probed=set();names={}
        def collect(details):
            for number,label in re.findall(r'^\[(\d+)\s+([^\]]+)\]',details,re.MULTILINE):
                number=int(number);names[number]=label
                if number not in probed and number not in pending:pending.append(number)
        # Every returned device still has to pass a real inference check.
        while pending:
            index=pending.pop(0);probed.add(index)
            try:
                details=infer_image(source,base/f'gpu{index}.png','animation_2x',f'gpu:{index}',root,threading.Event(),on_diagnostics=collect)
                collect(details)
                with Image.open(base/f'gpu{index}.png') as result:
                    if not result.getbbox():raise RuntimeError('GPU returned black image')
                devices.append(AIHardware(f'gpu:{index}',names.get(index,f'Compatible GPU {index}'),'ncnn',True))
            except Exception:pass
    return devices
