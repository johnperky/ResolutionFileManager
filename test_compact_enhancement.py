import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

from PIL import Image


class CompactPhotoTests(unittest.TestCase):
    def test_cpu_batch_switches_between_all_three_model_families(self):
        from image_pipeline import convert_image_file, ImageEnhancementBatch
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source.png'
            image=Image.new('RGB',(12,10));image.putdata([((i*31)%256,(i*17)%256,(i*43)%256) for i in range(120)]);image.save(source)
            with ImageEnhancementBatch() as batch:
                first=None;pixels=[]
                for index,mode in enumerate(('photo_fast_2x','video_2x','animation_4x','photo_fast_2x')):
                    target=root/f'out-{index}.png'
                    state,details=convert_image_file(source,target,'PNG','Original size',threading.Event(),ai_mode=mode,ai_hardware='cpu',working_folder=root,enhancement_batch=batch)
                    self.assertEqual(state,'Passed',details)
                    if first is None:first=batch.process
                    self.assertIs(first,batch.process)
                    with Image.open(target) as im:pixels.append(im.tobytes())
                self.assertEqual(pixels[0],pixels[-1])
            self.assertFalse(list(root.glob('rfm-*')))
    def test_compact_modes_use_photo_model_and_native_four(self):
        from ai_backends import mode_spec, gpu_model_spec
        from image_pipeline import IMAGE_MODES
        for factor in (2, 4):
            mode=f'photo_fast_{factor}x'
            self.assertEqual(mode_spec(mode),('photo_fast',factor))
            self.assertEqual(gpu_model_spec(mode),('realesr-general-x4v3-medium',4))
            self.assertIn(mode,IMAGE_MODES.values())
        self.assertEqual(gpu_model_spec('video_2x'),('realesrgan-x4plus',4))
        self.assertEqual(gpu_model_spec('animation_2x'),('realesr-animevideov3',2))

    def test_compact_cpu_restoration_retains_alpha_and_original(self):
        from image_pipeline import convert_image_file, ImageEnhancementBatch
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source.png';target=root/'out.png'
            Image.new('RGBA',(12,10),(90,120,160,100)).save(source);before=source.read_bytes()
            with ImageEnhancementBatch() as batch:
                state,details=convert_image_file(source,target,'PNG','Original size',threading.Event(),ai_mode='photo_fast_2x',ai_hardware='cpu',working_folder=root,enhancement_batch=batch)
            self.assertEqual(state,'Passed',details)
            with Image.open(target) as result:
                self.assertEqual(result.size,(12,10));self.assertEqual(result.getextrema()[3],(100,100))
            self.assertEqual(source.read_bytes(),before)
            self.assertFalse(list(root.glob('rfm-*')))


class StreamingVideoTests(unittest.TestCase):
    def test_fast_vfr_keeps_timestamps_between_nominal_frame_ticks(self):
        from ai_pipeline import media_probe
        from media_sorter import MediaSorterApp,inspect_media,TRANSCODE_SOFTWARE
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'vfr.mkv';target=root/'out.mkv'
            pts=r'settb=1/1000,setpts=if(eq(N\,0)\,0\,if(eq(N\,1)\,41\,if(eq(N\,2)\,105\,if(eq(N\,3)\,148\,if(eq(N\,4)\,205\,247)))))'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=s=64x48:r=30:d=0.2','-vf',pts,'-fps_mode','vfr','-enc_time_base','1:1000','-c:v','ffv1',str(source)],check=True,timeout=20)
            state,details=MediaSorterApp.transcode_video_file(inspect_media(source),target,'360p H.264 MKV (compatible)',28,threading.Event(),engine=TRANSCODE_SOFTWARE,hardware_decode=False,ai_mode='fast_video')
            self.assertEqual(state,'Passed',details)
            before=media_probe(source,frames=True)['frames'];after=media_probe(target,frames=True)['frames']
            self.assertEqual(len(before),6);self.assertEqual(len(after),6)
            for a,b in zip(before,after):self.assertAlmostEqual(float(a['best_effort_timestamp_time']),float(b['best_effort_timestamp_time']),delta=.002)
    def test_preview_routes_fast_enhancement_even_when_downscaling(self):
        from video_enhancement import effective_video_mode
        self.assertEqual(effective_video_mode('fast_video',2160,360),'fast_video')
        self.assertEqual(effective_video_mode('photo_fast_2x',360,720),'photo_fast_2x')
        self.assertEqual(effective_video_mode('photo_fast_2x',1080,720),'ordinary')
        self.assertEqual(effective_video_mode('fast_video',360,None),'ordinary')
    def test_fast_vfr_preserves_audio_tracks_subtitles_chapters_and_timestamps(self):
        from media_sorter import MediaSorterApp,inspect_media,TRANSCODE_SOFTWARE
        def probe(path):
            return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_chapters','-show_format','-of','json',str(path)]))
        def stamps(path):
            value=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_frames','-show_entries','frame=best_effort_timestamp_time','-of','json',str(path)]))
            return [float(f['best_effort_timestamp_time']) for f in value['frames']]
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source.mkv';target=root/'out.mkv';subs=root/'sub.srt';metadata=root/'meta.txt'
            subs.write_text('1\n00:00:02,100 --> 00:00:02,400\nRetained caption\n')
            metadata.write_text(';FFMETADATA1\ntitle=Timing fixture\n[CHAPTER]\nTIMEBASE=1/1000\nSTART=2000\nEND=2500\ntitle=Chapter test\n')
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=s=64x48:r=10:d=0.4','-f','lavfi','-i','sine=frequency=440:duration=0.5','-f','lavfi','-i','sine=frequency=880:duration=0.5','-i',str(subs),'-f','ffmetadata','-i',str(metadata),'-map','0:v','-map','1:a','-map','2:a','-map','3:s','-map_metadata','4','-map_chapters','4','-vf',r'settb=1/1000,setpts=if(eq(N\,0)\,2000\,if(eq(N\,1)\,2100\,if(eq(N\,2)\,2300\,2400)))','-filter:a','asetpts=PTS+2/TB','-copyts','-fps_mode','vfr','-enc_time_base','1:1000','-c:v','ffv1','-c:a','aac','-c:s','srt',str(source)],check=True,timeout=20)
            state,details=MediaSorterApp.transcode_video_file(inspect_media(source),target,'360p H.264 MKV (compatible)',28,threading.Event(),engine=TRANSCODE_SOFTWARE,hardware_decode=False,ai_mode='fast_video')
            self.assertEqual(state,'Passed',details)
            before=probe(source);after=probe(target)
            self.assertEqual(sum(s['codec_type']=='audio' for s in after['streams']),2)
            self.assertEqual(sum(s['codec_type']=='subtitle' for s in after['streams']),1)
            self.assertEqual(after['format']['tags']['title'],'Timing fixture')
            self.assertEqual(after['chapters'][0]['tags']['title'],'Chapter test')
            a=stamps(source);b=stamps(target);self.assertEqual(len(a),len(b))
            for x,y in zip(a,b):self.assertAlmostEqual(x-a[0],y-b[0],delta=.002)
            # Audio/video/subtitle relative offsets must survive timeline shifts.
            for kind in ('audio','subtitle'):
                x=next(s for s in before['streams'] if s['codec_type']==kind)
                y=next(s for s in after['streams'] if s['codec_type']==kind)
                self.assertAlmostEqual(float(x['start_time'])-a[0],float(y['start_time'])-b[0],delta=.03)
    def test_fast_video_has_no_ai_model_or_working_drive_requirement(self):
        from ai_backends import VIDEO_MODES, mode_spec
        self.assertIn('fast_video',VIDEO_MODES)
        with self.assertRaises(ValueError):mode_spec('fast_video')
        from media_sorter import MediaSorterApp, inspect_media, TRANSCODE_SOFTWARE
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source.mkv';target=root/'out.mkv'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=s=64x48:r=8:d=0.5','-c:v','ffv1',str(source)],check=True,timeout=15)
            with patch('media_sorter.prepare_ai_video',side_effect=AssertionError('Fast must stream')),patch('media_sorter.probe_hardware',side_effect=AssertionError('Fast must not probe AI')):
                state,details=MediaSorterApp.transcode_video_file(inspect_media(source),target,'360p H.264 MKV (compatible)',28,threading.Event(),engine=TRANSCODE_SOFTWARE,hardware_decode=False,ai_mode='fast_video',ai_working_folder=root/'missing')
            self.assertEqual(state,'Passed',details);self.assertFalse(list(root.glob('rfm-ai-*')))
            frames=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=height,nb_read_frames','-of','json',str(target)]))['streams'][0]
            self.assertEqual(frames['height'],360);self.assertEqual(int(frames['nb_read_frames']),4)

    def test_filter_keeps_sharpening_before_vaapi_upload(self):
        from video_enhancement import fast_video_arguments
        result=fast_video_arguments(['-vf','scale=640:360,format=nv12,hwupload'],'VA-API (Linux)')
        chain=result[result.index('-vf')+1]
        self.assertIn('flags=lanczos',chain)
        self.assertLess(chain.index('unsharp='),chain.index('hwupload'))
        self.assertEqual(result[result.index('-fps_mode')+1],'passthrough')


if __name__=='__main__':unittest.main()
