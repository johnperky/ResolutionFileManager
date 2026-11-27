"""Incremental pixels; presentation times remain supplied by the checked probe."""
from fractions import Fraction
from pathlib import Path
import shutil
import threading

from PIL import Image
from ai_backends import _cpu_image, mode_spec, video_gpu_model_spec, video_cpu_model_spec


def chunk_size(width,height,mode):
    # Bound file count and estimated raw scratch on disk, not an in-RAM batch.
    native=video_gpu_model_spec(mode)[1]
    return max(1,min(64,int(512*1024*1024/(width*height*4*(1+native*native)*1.2))))


def timed_video_path(work,info,mode):
    factor=mode_spec(mode)[1]
    # FFV1's RGB worst-case packet pool is about63 bytes/output pixel.
    # Avoid retaining hundreds of MB while the next NCNN process is active.
    large=info['width']*info['height']*factor*factor*63>128*1024*1024
    return Path(work)/('frames.nut' if large else 'frames.mkv')


def decoded_images(source,info,cancel_event):
    import av
    with av.open(str(source)) as container:
        for frame in container.decode(video=0):
            if cancel_event.is_set():raise InterruptedError('Conversion cancelled')
            image=frame.to_image().convert('RGB')
            if info['rotation']%360:
                rotated=image.rotate(info['rotation'],expand=True);image.close();image=rotated
            if image.size!=(info['width'],info['height']):
                image.close();raise ValueError('Decoded frame dimensions changed')
            try:yield image
            finally:image.close()


class TimedWriter:
    def __init__(self,path,info,timestamps,durations,factor):
        import av
        self.av=av;self.stamps=timestamps;self.durations=durations;self.index=0
        self.lengths={};self.clock=Fraction(1,1000000)
        self.output=av.open(str(path),'w')
        huffman=Path(path).suffix=='.nut'
        self.stream=self.output.add_stream('ffvhuff' if huffman else 'ffv1',rate=Fraction(str(info['fps'])).limit_denominator(100000))
        self.stream.width=info['width']*factor;self.stream.height=info['height']*factor
        self.stream.pix_fmt='rgb24' if huffman else 'bgr0';self.stream.time_base=self.clock
        if huffman:self.stream.codec_context.thread_count=1
        self.stream.codec_context.time_base=self.clock
        self.stream.codec_context.sample_aspect_ratio=Fraction(*info['sar'])

    def mux(self,packets):
        for packet in packets:
            packet.duration=self.lengths.pop(packet.pts,round(self.durations[-1]*1000000))
            self.output.mux(packet)

    def write(self,picture):
        if self.index>=len(self.stamps):raise ValueError('Decoded frame count exceeds presentation timing')
        if picture.size!=(self.stream.width,self.stream.height):raise ValueError('AI frame dimensions mismatch')
        frame=self.av.VideoFrame.from_image(picture.convert('RGB'))
        frame.pts=round((self.stamps[self.index]-self.stamps[0])*1000000);frame.time_base=self.clock
        self.lengths[frame.pts]=round(self.durations[self.index]*1000000)
        self.mux(self.stream.encode(frame));self.index+=1

    def finish(self):
        if self.index!=len(self.stamps):raise ValueError('Decoded frame count does not match presentation timing')
        self.mux(self.stream.encode())

    def close(self):self.output.close()


def stream_cpu(source,work,info,timestamps,durations,mode,assets,progress,cancel_event=None,preview_directory=None):
    cancel_event=cancel_event or threading.Event()
    from conversion_display import PreviewPublisher
    preview=PreviewPublisher(preview_directory)
    family,factor=mode_spec(mode);target=timed_video_path(work,info,mode)
    writer=TimedWriter(target,info,timestamps,durations,factor)
    try:
        for image in decoded_images(source,info,cancel_event):
            if shutil.disk_usage(work).free<32*1024*1024:raise OSError('Temporary disk space exhausted')
            model,native=video_cpu_model_spec(mode)
            result=_cpu_image(image,model,assets,cancel_event,native_scale=native)
            try:
                if factor!=native:
                    resized=result.resize((image.width*2,image.height*2),Image.Resampling.LANCZOS)
                    result.close();result=resized
                writer.write(result)
                preview.publish(result)
            finally:result.close()
            progress(writer.index)
        writer.finish()
    finally:writer.close()
    return target


def stream_gpu(source,work,info,timestamps,durations,mode,cancel_event,enhance,progress,disk_check):
    work=Path(work);raw=work/'source';dest=work/'upscaled'
    raw.mkdir(exist_ok=True);dest.mkdir(exist_ok=True)
    factor=mode_spec(mode)[1];native=video_gpu_model_spec(mode)[1]
    limit=chunk_size(info['width'],info['height'],mode);target=timed_video_path(work,info,mode)
    writer=TimedWriter(target,info,timestamps,durations,factor)
    files=[]
    def flush():
        enhance(raw,dest)
        if {p.name for p in dest.glob('*.png')}!={p.name for p in files}:raise RuntimeError('AI returned incomplete frames')
        for path in files:
            if cancel_event.is_set():raise InterruptedError('Conversion cancelled')
            disk_check()
            with Image.open(dest/path.name) as picture:
                padded_w=info['width']+(info['width']%2 if mode=='video_2x' else 0)
                padded_h=info['height']+(info['height']%2 if mode=='video_2x' else 0)
                if picture.size!=(padded_w*native,padded_h*native):raise RuntimeError('AI frame dimensions mismatch')
                if mode=='video_2x' and (padded_w!=info['width'] or padded_h!=info['height']):
                    with picture.crop((0,0,info['width']*factor,info['height']*factor)) as cropped:writer.write(cropped)
                elif native!=factor:
                    with picture.resize((info['width']*factor,info['height']*factor),Image.Resampling.LANCZOS) as resized:writer.write(resized)
                else:writer.write(picture)
            path.unlink();(dest/path.name).unlink();progress(writer.index)
        files.clear()
    try:
        for index,image in enumerate(decoded_images(source,info,cancel_event)):
            disk_check();path=raw/f'{index+1:09d}.png'
            if mode=='video_2x' and (image.width%2 or image.height%2):
                # The trained2x network unshuffles pairs; replicate only the
                # missing last row/column, then crop these pixels after inference.
                with Image.new('RGB',(image.width+image.width%2,image.height+image.height%2)) as padded:
                    padded.paste(image)
                    if image.width%2:
                        with image.crop((image.width-1,0,image.width,image.height)) as edge:padded.paste(edge,(image.width,0))
                    if image.height%2:
                        with padded.crop((0,image.height-1,padded.width,image.height)) as edge:padded.paste(edge,(0,image.height))
                    padded.save(path,compress_level=1)
            else:image.save(path,compress_level=1)
            files.append(path)
            if len(files)>=limit:flush()
        if files:flush()
        writer.finish()
    finally:
        writer.close()
        # Only these job-owned directories are touched; the caller owns their lifetime.
        for directory in (raw,dest):
            for path in directory.glob('*.png'):path.unlink()
    return target
