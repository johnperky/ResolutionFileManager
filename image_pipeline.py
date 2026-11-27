"""Still-image conversion using the existing standalone CPU/Vulkan AI engines."""
import json,os,shutil,sys,tempfile,uuid
from pathlib import Path
from PIL import Image,ImageOps,ImageFilter,ImageEnhance,PngImagePlugin,JpegImagePlugin,WebPImagePlugin
from conversion_conflicts import publish_conversion_output,validate_approval
from ai_backends import asset_directory,validate_assets,probe_hardware,hardware_choice,infer_image,mode_spec
from ai_pipeline import _run,estimate_ai_disk_bytes,publish_output_without_replace
from process_utils import start_owned_process,stop_owned_process


class ImageEnhancementBatch:
    """One lazy, cancellable CPU process per batch, never a global worker."""
    def __init__(self):
        self.process=None;self._directory=None;self._log=None;self._assets=None;self._request=0
        self.failed_gpus=set()

    def __enter__(self):return self

    def __exit__(self,*exc):self.close()

    def close(self):
        try:stop_owned_process(self.process)
        finally:
            self.process=None
            if self._log is not None:self._log.close();self._log=None
            if self._directory is not None:self._directory.cleanup();self._directory=None

    def infer(self,source,target,mode,assets,cancel_event,working_folder,check):
        try:
            if cancel_event.is_set():raise InterruptedError('AI cancelled')
            if self.process is not None and self._assets!=Path(assets).resolve():self.close()
            if self.process is None:
                self._assets=Path(assets).resolve()
                self._request=0
                self._directory=tempfile.TemporaryDirectory(prefix='rfm-image-worker-',dir=working_folder)
                directory=Path(self._directory.name);job=directory/'job.json'
                job.write_text(json.dumps({'session':True,'assets':str(self._assets),'directory':str(directory)}),encoding='utf-8')
                self._log=tempfile.TemporaryFile(dir=directory)
                command=[sys.executable,'--rfm-ai-worker',str(job)] if getattr(sys,'frozen',False) else [sys.executable,str(Path(__file__).with_name('ai_worker.py')),str(job)]
                self.process=start_owned_process(command,stdout=self._log,stderr=self._log)
            directory=Path(self._directory.name);self._request+=1
            request=directory/f'request-{self._request}.json';temporary=request.with_suffix('.tmp')
            temporary.write_text(json.dumps({'id':self._request,'input':str(source),'output':str(target),'mode':mode}),encoding='utf-8')
            temporary.replace(request)
            response=directory/f'response-{self._request}.json'
            while True:
                if cancel_event.is_set():raise InterruptedError('AI cancelled')
                check()
                if self.process.poll() is not None:
                    self._log.seek(0)
                    raise RuntimeError('CPU AI worker stopped: '+self._log.read().decode(errors='replace')[-1500:])
                if response.exists():
                    value=json.loads(response.read_text(encoding='utf-8'))
                    if value['id']==self._request:
                        if 'error' in value:raise RuntimeError(value['error'])
                        if not Path(target).is_file():raise RuntimeError('CPU AI returned no image')
                        return
                cancel_event.wait(.025)
        except BaseException:
            # Terminate before the caller cleans files the worker could be using.
            self.close();raise

IMAGE_MODES={'Ordinary resizing':'ordinary','AI Photo fast 2×':'photo_fast_2x','AI Photo fast 4×':'photo_fast_4x','AI Photo restore/detail 2×':'video_2x','AI Photo restore/detail 4×':'video_4x','AI Illustration 2×':'animation_2x','AI Illustration 4×':'animation_4x'}
RESIZE_CHOICES=('Original size','50%','200%','400%','Long edge 1280 px','Long edge 1920 px','Long edge 2560 px','Long edge 3840 px','Custom long edge')
FORMATS={'JPEG':'.jpg','PNG':'.png','WebP':'.webp'}
MAX_PIXELS=320_000_000
EFFECTS=('Denoise','Sharpen','Smooth','Auto contrast','Colour boost')

def apply_effects(image,effects,strength=2):
    effects=set(effects);strength=max(1,min(3,int(strength)))
    if effects-set(EFFECTS):raise ValueError('Unknown image effect')
    if 'Denoise' in effects:image=image.filter(ImageFilter.MedianFilter(5 if strength==3 else 3))
    if 'Smooth' in effects:image=image.filter(ImageFilter.GaussianBlur(.3*strength))
    if 'Auto contrast' in effects:image=ImageOps.autocontrast(image,cutoff=.25*strength)
    if 'Colour boost' in effects:image=ImageEnhance.Color(image).enhance(1+.1*strength)
    if 'Sharpen' in effects:image=image.filter(ImageFilter.UnsharpMask(radius=.6*strength,percent=60*strength,threshold=3))
    return image

def target_dimensions(width,height,choice,custom_edge=1920):
    if choice=='Original size':scale=1
    elif choice in ('50%','200%','400%'):scale=int(choice[:-1])/100
    elif choice.startswith('Long edge '):scale=int(choice.split()[2])/max(width,height)
    elif choice=='Custom long edge':
        if not 1<=int(custom_edge)<=32768:raise ValueError('Custom long edge must be between 1 and 32768 pixels')
        scale=int(custom_edge)/max(width,height)
    else:raise ValueError('Unknown image size')
    result=max(1,round(width*scale)),max(1,round(height*scale))
    if result[0]*result[1]>MAX_PIXELS:raise ValueError('Requested image is too large; select a smaller output size')
    return result

def inspect_image(path):
    with Image.open(path) as image:
        if getattr(image,'n_frames',1)!=1:raise ValueError('Animated or multi-page images are not supported; originals are retained')
        width,height=image.size
        if image.getexif().get(274) in (5,6,7,8):width,height=height,width
        return {'width':width,'height':height,'mode':image.mode}

def convert_image_file(source,target,format,resize,cancel_event,*,quality=92,custom_edge=1920,ai_mode='ordinary',ai_hardware='auto',working_folder=None,on_stage=None,effects=(),effect_strength=2,enhancement_batch=None,on_preview=None,overwrite=None):
    source,target=Path(source),Path(target);temporary=None;retained_backup=None
    stage=on_stage or (lambda text:None)
    def cancelled():
        if cancel_event.is_set():raise InterruptedError('Image conversion cancelled')
    try:
        cancelled()
        if format not in FORMATS:raise ValueError('Choose JPEG, PNG or WebP output')
        if overwrite is not None:validate_approval(target,overwrite,(source,))
        elif target.exists():return 'Skipped','Existing output retained'
        info=inspect_image(source);size=target_dimensions(info['width'],info['height'],resize,custom_edge)
        if ai_mode!='ordinary':
            mode_spec(ai_mode)
            if info['width']*info['height']*16>MAX_PIXELS:raise ValueError('Image is too large for AI; first make a smaller copy using ordinary resizing')
            if info['mode'] not in ('RGB','RGBA','L','LA','P'):raise ValueError('AI supports 8-bit RGB, transparency and greyscale images; use ordinary conversion for this image')
        stage('Reading image');cancelled()
        with Image.open(source) as original:
            oriented=ImageOps.exif_transpose(original);oriented.load()
            rgba=oriented.convert('RGBA');icc=original.info.get('icc_profile') if original.mode in ('RGB','RGBA') else None
        target.parent.mkdir(parents=True,exist_ok=True)
        temporary=target.with_name(target.stem+'.'+uuid.uuid4().hex+'.partial'+target.suffix)
        hardware='ordinary'
        def finish(picture):
            nonlocal retained_backup
            cancelled();stage('Resizing and saving image')
            picture=picture.convert('RGB').resize(size,Image.Resampling.LANCZOS)
            picture=apply_effects(picture,effects,effect_strength)
            alpha=rgba.getchannel('A').resize(size,Image.Resampling.LANCZOS)
            if format=='JPEG':
                white=Image.new('RGB',size,'white');white.paste(picture,mask=alpha);picture=white
            else:picture.putalpha(alpha)
            options={'icc_profile':icc}  # Explicit None prevents inheriting a CMYK profile into RGB PNG.
            if format in ('JPEG','WebP'):options['quality']=max(1,min(100,int(quality)))
            picture.save(temporary,format=format,**options)
            cancelled()
            # Inspect only our own generated output, whose requested dimensions
            # were bounded above; this does not change Pillow's global guard.
            with {'PNG':PngImagePlugin.PngImageFile,'JPEG':JpegImagePlugin.JpegImageFile,'WebP':WebPImagePlugin.WebPImageFile}[format](temporary) as checked:
                if checked.size!=size:raise ValueError('Saved image dimensions did not match preview')
                checked.verify()
            cancelled();retained_backup=publish_conversion_output(temporary,target,overwrite)
            if on_preview:on_preview(target)
        if ai_mode=='ordinary':finish(rgba)
        else:
            work_root=Path(working_folder or tempfile.gettempdir()).expanduser().resolve()
            if not work_root.is_dir():raise ValueError('AI working folder must exist')
            required=estimate_ai_disk_bytes(info['width'],info['height'],1,ai_mode)
            if shutil.disk_usage(work_root).free<required:raise OSError('Not enough AI working drive space')
            assets=asset_directory();validate_assets(assets)
            hardware=hardware_choice(ai_hardware,probe_hardware(assets)).id if ai_hardware=='auto' else ai_hardware
            if ai_hardware=='auto' and enhancement_batch is not None and hardware in enhancement_batch.failed_gpus:hardware='cpu'
            with tempfile.TemporaryDirectory(prefix='rfm-image-ai-',dir=work_root) as directory:
                work=Path(directory);raw=work/'source';raw.mkdir();dest=work/'upscaled';dest.mkdir();input=raw/'image.png';output=dest/'image.png'
                rgba.convert('RGB').save(input,compress_level=1)
                def disk_check():
                    cancelled()
                    if shutil.disk_usage(work).free<32*1024*1024:raise OSError('AI working drive space exhausted')
                def cpu():
                    stage('AI enhancing (CPU)');disk_check()
                    if enhancement_batch is not None:
                        enhancement_batch.infer(input,output,ai_mode,assets,cancel_event,work_root,disk_check)
                        return
                    error=work/'worker-error.txt';job=work/'job.json'
                    job.write_text(json.dumps({'source':str(raw),'dest':str(dest),'assets':str(assets),'mode':ai_mode,'progress':str(work/'progress.json'),'error':str(error)}))
                    command=[sys.executable,'--rfm-ai-worker',str(job)] if getattr(sys,'frozen',False) else [sys.executable,str(Path(__file__).with_name('ai_worker.py')),str(job)]
                    try:_run(command,cancel_event,disk_check)
                    except RuntimeError:
                        if error.exists():raise RuntimeError(error.read_text(encoding='utf-8')) from None
                        raise
                if hardware=='cpu':cpu()
                else:
                    stage('AI enhancing ('+hardware+')');disk_check()
                    try:infer_image(input,output,ai_mode,hardware,assets,cancel_event,working_dir=work,timeout=None,resource_check=disk_check)
                    except RuntimeError:
                        if ai_hardware!='auto':raise
                        if enhancement_batch is not None:enhancement_batch.failed_gpus.add(hardware)
                        stage('GPU unavailable; falling back to CPU');output.unlink(missing_ok=True);hardware='cpu';cpu()
                cancelled()
                with PngImagePlugin.PngImageFile(output) as enhanced:
                    factor=mode_spec(ai_mode)[1]
                    if enhanced.size!=(info['width']*factor,info['height']*factor):raise ValueError('AI image dimensions mismatch')
                    finish(enhanced)
        return 'Passed',f'Saved {size[0]}×{size[1]} {format}; '+('ordinary resizing' if hardware=='ordinary' else 'AI on '+hardware)+(f'; previous output retained at {retained_backup}' if retained_backup else '')
    except InterruptedError:return 'Cancelled','Image conversion cancelled; unfinished files removed'
    except FileExistsError:return 'Skipped','An output appeared during conversion; existing file retained'
    except (OSError,ValueError,RuntimeError,MemoryError,Image.DecompressionBombError) as exc:return 'Failed',str(exc)
    finally:
        if temporary is not None:
            try:temporary.unlink(missing_ok=True)
            except OSError:pass
