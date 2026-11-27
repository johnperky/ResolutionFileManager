import unittest
import tempfile
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import conversion_profiles as profiles


class CompressionTests(unittest.TestCase):
    def test_shutter_calculation_uses_actual_output_and_frame_rate(self):
        info = {'width':1920,'height':1080,'fps':25,'sar':(1,1)}
        self.assertEqual(profiles.automatic_video_bitrate('Keep source H.265 MKV (smaller)', info),2500)
        self.assertEqual(profiles.automatic_video_bitrate('Keep source H.264 MP4 (compatible)', info),5000)
        self.assertEqual(profiles.automatic_video_bitrate('Keep source AV1 MKV (smallest)', info),2000)
        self.assertEqual(profiles.automatic_video_bitrate('Keep source H.265 MKV (smaller)', dict(info,fps=50)),5000)
        self.assertEqual(profiles.automatic_video_bitrate('720p H.265 MKV (smaller)', info),1111)
        self.assertEqual(profiles.automatic_video_bitrate('1080p H.265 MKV (smaller)',dict(info,width=960,height=540)),2500)
        self.assertEqual(profiles.automatic_video_bitrate('1080p H.265 MKV (smaller)',dict(info,width=960,height=540,sar=(2,1))),5000)
        self.assertEqual(profiles.automatic_video_bitrate('Keep source H.265 MKV (smaller)',dict(info,fps=30000/1001)),2997)
        with self.assertRaises(ValueError):profiles.automatic_video_bitrate('Keep source H.265 MKV (smaller)',dict(info,fps=0))

    def test_auto_nvenc_uses_target_and_quality_mode_stays_available(self):
        args=['-c:v','hevc_nvenc','-preset','p5','-rc','vbr','-cq','25','-b:v','0','-c:a','aac','-b:a','192k']
        result=profiles.video_compression_arguments(args,'hevc','NVIDIA NVENC','automatic',2500,True,192,'Original channels')
        self.assertNotIn('-cq',result)
        self.assertEqual(result[result.index('-b:v')+1],'2500k')
        self.assertIn('p7',result);self.assertIn('-rc-lookahead',result)
        self.assertEqual(result[result.index('-b:a')+1],'192k')
        result=profiles.video_compression_arguments(args,'hevc','NVIDIA NVENC','quality',None,False,128,'Stereo')
        self.assertIn('-cq',result);self.assertIn('p5',result)
        self.assertEqual(result[result.index('-b:a')+1],'128k')
        self.assertEqual(result[result.index('-ac')+1],'2')
        self.assertNotIn('-pass',result)

    def test_remux_is_unchanged_and_cpu_abr_drops_crf(self):
        remux=['-map','0','-c','copy']
        self.assertEqual(profiles.video_compression_arguments(remux,None,'Software / CPU','automatic',None,True,128,'Stereo'),remux)
        result=profiles.video_compression_arguments(['-c:v','libx265','-crf','25','-preset','medium','-b:a','192k'],'hevc','Software / CPU','automatic',2500,True,128,'Original channels')
        self.assertNotIn('-crf',result);self.assertIn('veryslow',result);self.assertIn('2500k',result)

    def test_nvenc_compatibility_keeps_engine_and_p7(self):
        result=profiles.video_compression_arguments(['-c:v','hevc_nvenc','-preset','p5','-b:a','192k'],'hevc','NVIDIA NVENC','automatic',2500,True,192,'Original channels',compatibility=True)
        self.assertIn('hevc_nvenc',result);self.assertIn('p7',result)
        self.assertNotIn('-rc-lookahead',result);self.assertNotIn('-spatial-aq',result)

    def test_startup_compatibility_retry_keeps_explicit_nvidia_and_can_cancel(self):
        import media_sorter as m
        for cancel_after_failure in (False, True):
            with self.subTest(cancel=cancel_after_failure), tempfile.TemporaryDirectory() as folder:
                root=Path(folder);target=root/'out.mkv';cancel=threading.Event();commands=[];events=[]
                item=SimpleNamespace(path=root/'source.mp4',duration=1)
                def launch(command,**_kwargs):
                    commands.append(command)
                    if '-rc-lookahead' in command:
                        if cancel_after_failure:cancel.set()
                        raise OSError('Simulated optional quality setting rejection')
                    Path(command[-1]).write_bytes(b'unit-test-output')
                    return SimpleNamespace(stdout=None,returncode=0,poll=lambda:0)
                info={'width':1920,'height':1080,'fps':25,'sar':(1,1)}
                with patch.object(m.MediaSorterApp,'ffmpeg_capabilities',return_value=({'hevc_nvenc'},set(),'')),patch.object(m,'start_owned_process',side_effect=launch),patch.object(m,'stop_owned_process'):
                    state,details=m.MediaSorterApp.transcode_video_file(item,target,'Keep source H.265 MKV (smaller)',25,cancel,engine='NVIDIA NVENC',hardware_decode=False,source_info=info,stage_callback=events.append)
                if cancel_after_failure:
                    self.assertEqual(state,'Cancelled');self.assertEqual(len(commands),1);self.assertFalse(target.exists())
                else:
                    self.assertEqual(state,'Passed',details);self.assertEqual(len(commands),2)
                    self.assertTrue(all('hevc_nvenc' in command for command in commands))
                    self.assertIn('p7',commands[-1]);self.assertIn('2500k',commands[-1])
                    self.assertNotIn('-rc-lookahead',commands[-1]);self.assertNotIn('-pass',commands[-1])
                    self.assertTrue(any('compatibility mode' in event.stage for event in events))


if __name__=='__main__':unittest.main()
