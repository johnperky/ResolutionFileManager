"""Bounded pixel staging with the existing timing authority and model paths."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

from PIL import Image


class VideoStorageTests(unittest.TestCase):
    def test_native_2x_gpu_staging_pads_odd_edges_and_never_stages_4x(self):
        from ai_video_stream import stream_gpu
        import av
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);image=Image.frombytes('RGB',(17,13),bytes((i*31)%256 for i in range(17*13*3)))
            def enhance(raw,dest):
                for file in raw.glob('*.png'):
                    with Image.open(file) as source:
                        self.assertEqual(source.size,(18,14))
                        source.resize((36,28),Image.Resampling.NEAREST).save(dest/file.name)
            with patch('ai_video_stream.decoded_images',return_value=iter([image])):
                output=stream_gpu('ignored',root,{'width':17,'height':13,'fps':5,'sar':(1,1)},[0],[.2],'video_2x',threading.Event(),enhance,lambda done:None,lambda:None)
            with av.open(str(output)) as container:frames=list(container.decode(video=0))
            self.assertEqual(len(frames),1)
            self.assertEqual(frames[0].to_image().tobytes(),image.resize((34,26),Image.Resampling.NEAREST).tobytes())
            self.assertFalse(list(root.rglob('*.png')))

    def test_large_intermediate_avoids_ffv1_worst_packet_allocation(self):
        from ai_video_stream import timed_video_path
        self.assertEqual(timed_video_path(Path('work'),{'width':1280,'height':720},'photo_fast_2x').suffix,'.nut')
        self.assertEqual(timed_video_path(Path('work'),{'width':640,'height':360},'photo_fast_2x').suffix,'.mkv')

    def test_rgb_huffman_intermediate_is_lossless_for_odd_sized_pixels_and_vfr(self):
        from ai_video_stream import TimedWriter
        import av
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/'frames.nut';stamps=[2,.0+2.041,2.173];durations=[.041,.132,.027]
            writer=TimedWriter(target,{'width':7,'height':5,'fps':15,'sar':(1,1)},stamps,durations,2)
            originals=[]
            try:
                for index in range(3):
                    image=Image.frombytes('RGB',(14,10),bytes((i*37+index*19)%256 for i in range(14*10*3)))
                    originals.append(image.tobytes());writer.write(image);image.close()
                writer.finish()
            finally:writer.close()
            with av.open(str(target)) as container:
                frames=list(container.decode(video=0))
                self.assertEqual(container.streams.video[0].codec_context.name,'ffvhuff')
                self.assertEqual([f.to_image().tobytes() for f in frames],originals)
                self.assertEqual([round(float(f.pts*f.time_base),6) for f in frames],[0,.041,.173])

    @unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg required')
    def test_nut_final_encoding_preserves_vfr_sar_audio_and_tail(self):
        from media_sorter import MediaSorterApp,inspect_media,TRANSCODE_SOFTWARE
        from ai_pipeline import media_probe
        from ai_worker import main as cpu_worker
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'input.mkv';target=root/'output.mkv'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=s=32x24:r=10:d=0.3','-f','lavfi','-i','sine=duration=0.3','-vf',r'settb=1/1000,setpts=if(eq(N\,0)\,2000\,if(eq(N\,1)\,2041\,2173)),setsar=4/3','-af','asetpts=PTS+2/TB','-copyts','-fps_mode','vfr','-enc_time_base','1:1000','-c:v','libx264','-c:a','aac',str(source)],check=True)
            def worker_in_process(command,cancel,check):
                # Exercise actual CPU model and NUT plumbing at tiny dimensions;
                # real owned subprocess cancellation is covered separately.
                cpu_worker(command[-1]);check()
            with patch('ai_video_stream.timed_video_path',side_effect=lambda work,*args:Path(work)/'frames.nut'),patch('ai_pipeline._run',side_effect=worker_in_process):
                state,details=MediaSorterApp.transcode_video_file(inspect_media(source),target,'360p H.264 MKV (compatible)',28,threading.Event(),engine=TRANSCODE_SOFTWARE,hardware_decode=False,ai_mode='photo_fast_2x',ai_hardware='cpu')
            self.assertEqual(state,'Passed',details)
            before=media_probe(source,frames=True);after=media_probe(target,frames=True)
            initial=float(before['frames'][0]['best_effort_timestamp_time'])
            self.assertEqual(len(after['frames']),3)
            self.assertEqual((after['width'],after['height'],after['sar']),(640,360,(1,1)))
            offset=float(after['frames'][0]['best_effort_timestamp_time'])
            for a,b in zip(before['frames'],after['frames']):
                self.assertAlmostEqual(float(a['best_effort_timestamp_time'])-initial,float(b['best_effort_timestamp_time'])-offset,delta=.002)
            streams=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(target)]))['streams']
            self.assertTrue(any(s['codec_type']=='audio' for s in streams))
            self.assertAlmostEqual(after['duration'],.273,delta=.05)

    def test_missing_presentation_timestamps_fail_clearly(self):
        from ai_pipeline import prepare_ai_video
        info={'hdr':False,'width':16,'height':12,'fps':4,'duration':.5,'frames':[]}
        with tempfile.TemporaryDirectory() as d,patch('ai_pipeline.media_probe',return_value=info):
            with self.assertRaisesRegex(ValueError,'timestamp'):
                prepare_ai_video('unused',Path(d),'photo_fast_2x','cpu',Path(d),threading.Event(),lambda e:None)

    def test_video_estimate_accounts_for_one_intermediate_and_bounded_scratch(self):
        from ai_pipeline import estimate_ai_video_disk_bytes, estimate_ai_disk_bytes
        small=estimate_ai_video_disk_bytes(1920,1080,100,'video_2x')
        large=estimate_ai_video_disk_bytes(1920,1080,200,'video_2x')
        self.assertGreater(small,1920*1080*100*4*4)
        self.assertGreaterEqual(large-small,1920*1080*100*4*12)
        self.assertLess(large-small,1920*1080*100*4*12*1.3)
        self.assertLess(small,estimate_ai_disk_bytes(1920,1080,100,'video_2x')/2.5)

    @unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg required')
    def test_gpu_staging_is_bounded_and_pixels_timing_sar_survive(self):
        from ai_video_stream import stream_gpu, chunk_size
        from ai_pipeline import media_probe, frame_durations
        import av
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'input.mkv';work=root/'work';work.mkdir()
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=s=32x24:r=10:d=6.5','-vf','setsar=4/3','-c:v','ffv1',str(source)],check=True)
            info=media_probe(source,frames=True);stamps=[float(f['best_effort_timestamp_time']) for f in info['frames']]
            durations=frame_durations(stamps,6.5);seen=[]
            def enhance(raw,dest):
                files=sorted(raw.glob('*.png'));seen.append(len(files))
                self.assertLessEqual(len(files),chunk_size(32,24,'animation_2x'))
                self.assertEqual(list(dest.glob('*.png')),[])
                for path in files:
                    with Image.open(path) as picture:picture.resize((64,48),Image.Resampling.NEAREST).save(dest/path.name)
            target=stream_gpu(source,work,info,stamps,durations,'animation_2x',threading.Event(),enhance,lambda done:None,lambda:None)
            self.assertEqual(sum(seen),65);self.assertGreater(len(seen),1)
            self.assertFalse(list(work.rglob('*.png')))
            output=media_probe(target,frames=True)
            # Final conversion uses original SAR for display sizing; PyAV's
            # FFV1 intermediate does not reliably persist container SAR.
            self.assertEqual(info['sar'],(4,3));self.assertEqual(len(output['frames']),65)
            self.assertEqual([f['best_effort_timestamp_time'] for f in output['frames']],[f['best_effort_timestamp_time'] for f in info['frames']])
            with av.open(str(target)) as container:
                decoded=list(container.decode(video=0))
            with av.open(str(source)) as container:
                originals=list(container.decode(video=0))
            for old,new in zip(originals,decoded):
                self.assertEqual(old.to_image().resize((64,48),Image.Resampling.NEAREST).tobytes(),new.to_image().tobytes())

    @unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg required')
    def test_cpu_video_worker_never_materialises_png_frames(self):
        from ai_pipeline import prepare_ai_video
        from ai_backends import asset_directory
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'input.mkv';work=root/'work'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=s=16x12:r=4:d=0.5','-c:v','ffv1',str(source)],check=True)
            peak=[]
            def progress(event):peak.append(len(list(work.rglob('*.png'))))
            result=prepare_ai_video(source,work,'photo_fast_2x','cpu',asset_directory(),threading.Event(),progress)
            self.assertTrue(result.exists());self.assertTrue(peak)
            self.assertEqual(max(peak),0)
            self.assertEqual(json.loads((work/'timing.json').read_text())['count'],2)

    @unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg required')
    def test_final_ai_video_keeps_anamorphic_display_aspect(self):
        from media_sorter import MediaSorterApp,inspect_media,TRANSCODE_SOFTWARE
        from ai_pipeline import media_probe
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'input.mkv';target=root/'output.mp4'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=s=32x24:r=4:d=0.5','-vf','setsar=4/3','-c:v','ffv1',str(source)],check=True)
            state,details=MediaSorterApp.transcode_video_file(inspect_media(source),target,'360p H.264 MP4 (compatible)',28,threading.Event(),engine=TRANSCODE_SOFTWARE,hardware_decode=False,ai_mode='photo_fast_2x',ai_hardware='cpu')
            self.assertEqual(state,'Passed',details)
            info=media_probe(target);self.assertEqual((info['width'],info['height'],info['sar']),(640,360,(1,1)))

    @unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg required')
    def test_decoder_rotation_matches_ffmpeg_autorotation(self):
        from ai_video_stream import decoded_images
        from ai_pipeline import media_probe
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);base=root/'base.mp4'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=s=32x24:r=4:d=0.25','-c:v','libx264',str(base)],check=True)
            for rotation in (90,-90,180):
                source=root/f'rot{rotation}.mp4';reference=root/f'ref{rotation}.png'
                subprocess.run(['ffmpeg','-v','error','-i',str(base),'-c','copy','-metadata:s:v:0',f'rotate={rotation}',str(source)],check=True)
                subprocess.run(['ffmpeg','-v','error','-i',str(source),'-frames:v','1',str(reference)],check=True)
                for image in decoded_images(source,media_probe(source),threading.Event()):
                    with Image.open(reference) as expected:
                        self.assertEqual(image.size,expected.size)
                        self.assertEqual(image.tobytes(),expected.tobytes())

    @unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg required')
    def test_gpu_failure_restarts_whole_source_on_cpu(self):
        from ai_pipeline import prepare_ai_video
        from ai_backends import asset_directory
        import av
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'input.mkv';cpu=root/'cpu';gpu=root/'gpu'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=s=16x12:r=4:d=0.5','-c:v','ffv1',str(source)],check=True)
            expected=prepare_ai_video(source,cpu,'photo_fast_2x','cpu',asset_directory(),threading.Event(),lambda event:None)
            def failure(source,work,*args):
                (Path(work)/'frames.mkv').write_bytes(b'incomplete GPU output')
                raise RuntimeError('GPU lost')
            with patch('ai_video_stream.stream_gpu',side_effect=failure):
                result=prepare_ai_video(source,gpu,'photo_fast_2x','gpu:0',asset_directory(),threading.Event(),lambda event:None,fallback_cpu=True)
            with av.open(str(expected)) as a,av.open(str(result)) as b:
                self.assertEqual([f.to_image().tobytes() for f in a.decode(video=0)],[f.to_image().tobytes() for f in b.decode(video=0)])
            self.assertEqual(json.loads((gpu/'timing.json').read_text())['hardware'],'cpu')

    def test_gpu_disk_error_never_retries_cpu(self):
        from ai_pipeline import prepare_ai_video
        from ai_backends import asset_directory
        info={'hdr':False,'width':16,'height':12,'fps':4,'duration':.5,
              'frames':[{'best_effort_timestamp_time':'0'},{'best_effort_timestamp_time':'.25'}]}
        with tempfile.TemporaryDirectory() as d,patch('ai_pipeline.media_probe',return_value=info),patch('ai_video_stream.stream_gpu',side_effect=OSError('drive full')),patch('ai_pipeline._run') as run:
            with self.assertRaisesRegex(OSError,'drive full'):
                prepare_ai_video('unused',Path(d),'photo_fast_2x','gpu:0',asset_directory(),threading.Event(),lambda e:None,fallback_cpu=True)
            run.assert_not_called()


if __name__=='__main__':unittest.main()
