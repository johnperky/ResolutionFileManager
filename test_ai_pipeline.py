from pathlib import Path
import tempfile
import unittest
import json
import shutil
import subprocess
import threading
import importlib.util

class PipelineTests(unittest.TestCase):
    def test_no_clobber_publication(self):
        from ai_pipeline import publish_output_without_replace
        with tempfile.TemporaryDirectory() as d:
            temp=Path(d)/'partial';target=Path(d)/'result';temp.write_bytes(b'new');target.write_bytes(b'original')
            with self.assertRaises(FileExistsError):publish_output_without_replace(temp,target)
            self.assertEqual(target.read_bytes(),b'original');self.assertEqual(temp.read_bytes(),b'new')
            target.unlink();publish_output_without_replace(temp,target)
            self.assertEqual(target.read_bytes(),b'new');self.assertFalse(temp.exists())

    @unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg required')
    def test_successful_encoding_releases_owned_process(self):
        import media_sorter as m
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'source.mp4';target=Path(d)/'result.mp4'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=s=32x24:r=5:d=0.2','-c:v','libx264',str(source)],check=True,timeout=20)
            owned=[];stopped=[];start=m.start_owned_process;stop=m.stop_owned_process
            def launch(*args,**kwargs):
                process=start(*args,**kwargs);owned.append(process);return process
            def release(process):
                stopped.append(process);return stop(process)
            try:
                with patch.object(m,'start_owned_process',side_effect=launch),patch.object(m,'stop_owned_process',side_effect=release):
                    state,details=m.MediaSorterApp.transcode_video_file(m.inspect_media(source),target,'360p H.264 MP4 (compatible)',28,threading.Event(),engine=m.TRANSCODE_SOFTWARE,hardware_decode=False)
                self.assertEqual(state,'Passed',details)
                self.assertTrue(owned)
                self.assertTrue(all(process in stopped for process in owned),'Successful encoder must release its ownership handle')
            finally:
                for process in owned:stop(process)

    def test_frame_durations_normalise_nonzero_timeline(self):
        from ai_pipeline import frame_durations
        self.assertEqual(frame_durations([10.0,10.04,10.12],.2),[.04,.08,.08])
        with self.assertRaises(ValueError):frame_durations([0,.1,.05],.2)

    def test_disk_estimate_includes_source_and_ai_frames(self):
        from ai_pipeline import estimate_ai_disk_bytes
        self.assertGreater(estimate_ai_disk_bytes(100,100,10,'video_4x'),100*100*10*3*(1+16))

    @unittest.skipUnless(importlib.util.find_spec('onnxruntime') and shutil.which('ffmpeg'),'AI runtime required')
    def test_real_cpu_ai_video_preserves_frames_audio_and_size(self):
        from media_sorter import MediaSorterApp,inspect_media,TRANSCODE_SOFTWARE
        from ai_pipeline import media_probe
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'source.mp4'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=s=32x24:r=8:d=0.5','-f','lavfi','-i','sine=frequency=440:duration=0.5','-c:v','libx264','-c:a','aac','-shortest',str(source)],check=True,timeout=20)
            for mode in ('video_2x','video_4x','animation_2x','animation_4x'):
                target=root/f'{mode}.mp4';events=[]
                state,details=MediaSorterApp.transcode_video_file(inspect_media(source),target,'360p H.264 MP4 (compatible)',28,threading.Event(),engine=TRANSCODE_SOFTWARE,hardware_decode=False,ai_mode=mode,ai_hardware='cpu',stage_callback=events.append)
                self.assertEqual(state,'Passed',details)
                result=media_probe(target,frames=True)
                self.assertEqual(result['height'],360);self.assertEqual(len(result['frames']),4)
                self.assertAlmostEqual(result['duration'],.5,delta=.03)
                streams=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(target)]))['streams']
                self.assertTrue(any(s['codec_type']=='audio' for s in streams))
                self.assertTrue(any('AI upscaling' in e.stage for e in events))

    @unittest.skipUnless(importlib.util.find_spec('onnxruntime') and shutil.which('ffmpeg'),'AI runtime required')
    def test_vfr_nonzero_start_survives_real_ai(self):
        from media_sorter import MediaSorterApp,inspect_media,TRANSCODE_SOFTWARE
        from ai_pipeline import media_probe
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'vfr.mkv';target=root/'out.mp4'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=s=32x24:r=10:d=0.3','-f','lavfi','-i','sine=duration=0.4','-vf',r'settb=1/1000,setpts=if(eq(N\,0)\,2000\,if(eq(N\,1)\,2100\,2300))','-af','asetpts=PTS+2/TB','-copyts','-fps_mode','vfr','-enc_time_base','1:1000','-c:v','libx264','-c:a','aac',str(source)],check=True,timeout=20)
            state,details=MediaSorterApp.transcode_video_file(inspect_media(source),target,'360p H.264 MP4 (compatible)',28,threading.Event(),engine=TRANSCODE_SOFTWARE,hardware_decode=False,ai_mode='animation_2x',ai_hardware='cpu')
            self.assertEqual(state,'Passed',details)
            before=media_probe(source,frames=True);after=media_probe(target,frames=True)
            initial=float(before['frames'][0]['best_effort_timestamp_time'])
            self.assertEqual(len(after['frames']),len(before['frames']))
            for a,b in zip(before['frames'],after['frames']):
                self.assertAlmostEqual(float(a['best_effort_timestamp_time'])-initial,float(b['best_effort_timestamp_time']),delta=.002)
            self.assertAlmostEqual(after['duration'],.4,delta=.03)

    @unittest.skipUnless(importlib.util.find_spec('onnxruntime') and shutil.which('ffmpeg'),'AI runtime required')
    def test_cancel_ai_and_disk_full_leave_no_unfinished_output(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        import hashlib
        from media_sorter import MediaSorterApp,inspect_media,TRANSCODE_SOFTWARE
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'source.mp4';target=root/'out.mp4'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=s=32x24:r=8:d=1','-c:v','libx264',str(source)],check=True,timeout=20)
            original=hashlib.sha256(source.read_bytes()).hexdigest();event=threading.Event()
            def stage(value):
                if value.stage.startswith('AI upscaling'):event.set()
            state,details=MediaSorterApp.transcode_video_file(inspect_media(source),target,'360p H.264 MP4 (compatible)',28,event,engine=TRANSCODE_SOFTWARE,hardware_decode=False,ai_mode='animation_2x',ai_hardware='cpu',stage_callback=stage)
            self.assertEqual(state,'Cancelled',details);self.assertFalse(target.exists())
            self.assertFalse(list(root.glob('rfm-ai-*')));self.assertFalse(list(root.glob('*.partial*')))
            with patch('ai_pipeline.shutil.disk_usage',return_value=SimpleNamespace(free=0)):
                state,details=MediaSorterApp.transcode_video_file(inspect_media(source),target,'360p H.264 MP4 (compatible)',28,threading.Event(),engine=TRANSCODE_SOFTWARE,hardware_decode=False,ai_mode='animation_2x',ai_hardware='cpu')
            self.assertEqual(state,'Failed');self.assertIn('space',details)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original)
            self.assertFalse(target.exists());self.assertFalse(list(root.glob('rfm-ai-*')))

    @unittest.skipUnless(importlib.util.find_spec('onnxruntime') and shutil.which('ffmpeg'),'AI runtime required')
    def test_cancel_during_final_validation_never_publishes(self):
        from unittest.mock import patch
        import media_sorter as m
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'source.mp4';target=root/'out.mp4';event=threading.Event()
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=s=32x24:r=8:d=0.25','-c:v','libx264',str(source)],check=True,timeout=20)
            probe=m.media_probe
            def cancel_on_validation(path,*args,**kwargs):
                value=probe(path,*args,**kwargs)
                if '.partial' in str(path):event.set()
                return value
            with patch.object(m,'media_probe',cancel_on_validation):
                state,details=m.MediaSorterApp.transcode_video_file(m.inspect_media(source),target,'360p H.264 MP4 (compatible)',28,event,engine=m.TRANSCODE_SOFTWARE,hardware_decode=False,ai_mode='animation_2x',ai_hardware='cpu')
            self.assertEqual(state,'Cancelled',details);self.assertFalse(target.exists())
            self.assertFalse(list(root.glob('*.partial*')))

    @unittest.skipUnless(importlib.util.find_spec('onnxruntime') and shutil.which('ffmpeg'),'AI runtime required')
    def test_selected_working_folder_success_cancel_and_full_disk_cleanup(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        import media_sorter as m
        import hashlib
        output_base = Path('F:/') if __import__('os').name=='nt' and Path('F:/').is_dir() else None
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory(prefix='rfm-test-output-',dir=output_base) as out:
            root=Path(d);working=root/'fast-working';working.mkdir();sentinel=working/'keep.txt';sentinel.write_text('unrelated')
            source=root/'source.mp4';target=Path(out)/'result.mp4'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=s=32x24:r=8:d=0.25','-c:v','libx264',str(source)],check=True,timeout=20)
            original=hashlib.sha256(source.read_bytes()).hexdigest();prepare=m.prepare_ai_video;used=[]
            def inspect_work(source_path,work,*args,**kwargs):
                self.assertEqual(Path(work).parent,working);self.assertNotEqual(Path(work).parent,target.parent)
                used.append(Path(work));return prepare(source_path,work,*args,**kwargs)
            with patch.object(m,'prepare_ai_video',inspect_work):
                state,details=m.MediaSorterApp.transcode_video_file(m.inspect_media(source),target,'360p H.264 MP4 (compatible)',28,threading.Event(),engine=m.TRANSCODE_SOFTWARE,hardware_decode=False,ai_mode='animation_2x',ai_hardware='cpu',ai_working_folder=working)
            self.assertEqual(state,'Passed',details);self.assertTrue(target.exists());self.assertTrue(used)
            self.assertEqual(set(working.iterdir()),{sentinel});target.unlink()
            event=threading.Event()
            def cancel(stage):
                if stage.stage.startswith('AI upscaling'):event.set()
            state,details=m.MediaSorterApp.transcode_video_file(m.inspect_media(source),target,'360p H.264 MP4 (compatible)',28,event,engine=m.TRANSCODE_SOFTWARE,hardware_decode=False,ai_mode='animation_2x',ai_hardware='cpu',ai_working_folder=working,stage_callback=cancel)
            self.assertEqual(state,'Cancelled',details);self.assertFalse(target.exists());self.assertEqual(set(working.iterdir()),{sentinel})
            checked=[]
            def full(path):checked.append(Path(path));return SimpleNamespace(free=0)
            with patch('ai_pipeline.shutil.disk_usage',side_effect=full):
                state,details=m.MediaSorterApp.transcode_video_file(m.inspect_media(source),target,'360p H.264 MP4 (compatible)',28,threading.Event(),engine=m.TRANSCODE_SOFTWARE,hardware_decode=False,ai_mode='animation_2x',ai_hardware='cpu',ai_working_folder=working)
            self.assertEqual(state,'Failed');self.assertIn('space',details);self.assertTrue(all(working in p.parents for p in checked))
            self.assertEqual(set(working.iterdir()),{sentinel});self.assertFalse(target.exists());self.assertFalse(list(target.parent.glob('*.partial*')))
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original)
            self.assertEqual(sentinel.read_text(),'unrelated')

if __name__=='__main__':unittest.main()
