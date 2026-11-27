"""Conversion naming, formats and startup tree regressions."""
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
import threading
import subprocess
import hashlib
import shutil

from media_sorter import FilePane, MediaSorterApp, TRANSCODE_PRESETS, inspect_media, TRANSCODE_SOFTWARE, CODEC_LABELS


class ConversionUpgradeTests(unittest.TestCase):
    def test_both_tree_widths_recover_collapsed_or_missing_settings(self):
        class Panes:
            position = 0
            def winfo_width(self): return 900
            def sashpos(self, index, value): self.position = value
        for saved in (None, 0, 1, 30, 180, 9999):
            pane = SimpleNamespace(content_panes=Panes())
            FilePane.restore_folder_width(pane, saved)
            self.assertGreaterEqual(pane.content_panes.position, 120)
            self.assertLessEqual(pane.content_panes.position, 300)

    def test_custom_names_preview_and_collisions(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            item = SimpleNamespace(path=root/'clip.mkv')
            plans = MediaSorterApp.plan_video_conversions([item], 'H.264 MP4 (compatible)', root, root, False, 'Keep both', prefix='done_', suffix='_small')
            self.assertEqual(plans[0]['target'].name, 'done_clip_small.mp4')
            plans[0]['target'].touch()
            plans = MediaSorterApp.plan_video_conversions([item], 'H.264 MP4 (compatible)', root, root, False, 'Keep both', prefix='done_', suffix='_small')
            self.assertEqual(plans[0]['target'].name, 'done_clip_small (2).mp4')
            for bad in ('../', 'a/b', 'a\\b', ':', '\x00'):
                with self.assertRaises(ValueError):
                    MediaSorterApp.plan_video_conversions([item], 'H.264 MP4 (compatible)', root, root, False, 'Keep both', prefix=bad)

    def test_new_presets_keep_codec_and_container_separate(self):
        for name, codec in (('H.264 MKV', 'libx264'), ('H.265 MKV', 'libx265')):
            self.assertIn(name, TRANSCODE_PRESETS)
            preset = TRANSCODE_PRESETS[name]
            self.assertEqual(preset['extension'], '.mkv')
            self.assertIn(codec, preset['arguments'])
            self.assertNotIn('-movflags', preset['arguments'])
        self.assertIn('Remux to MP4 (no re-encoding)', TRANSCODE_PRESETS)

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg required')
    def test_real_formats_remux_and_fps_keep_original(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); source = root / 'source.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=s=160x120:r=24:d=1', '-c:v', 'libx264', str(source)], check=True, timeout=20)
            original = hashlib.sha256(source.read_bytes()).hexdigest()
            item = inspect_media(source)
            for name, codec, extension in (('H.264 MP4 (compatible)', 'h264', '.mp4'), ('H.265 MP4 (smaller)', 'hevc', '.mp4'), ('H.264 MKV', 'h264', '.mkv'), ('H.265 MKV', 'hevc', '.mkv')):
                with self.subTest(preset=name):
                    target = root / (name.split()[0] + '_' + codec + extension)
                    fractions = []; rates = []
                    state, details = MediaSorterApp.transcode_video_file(item, target, name, 28, threading.Event(), fractions.append, TRANSCODE_SOFTWARE, False, stats_callback=rates.append)
                    self.assertEqual(state, 'Passed', details)
                    self.assertEqual(inspect_media(target).codec, CODEC_LABELS[codec])
                    self.assertEqual(fractions[-1], 1.0)
                    self.assertTrue(rates and rates[-1] > 0, rates)
                    if extension == '.mkv':
                        remux = target.with_name(target.stem + '_remux.mp4')
                        state, details = MediaSorterApp.transcode_video_file(inspect_media(target), remux, 'Remux to MP4 (no re-encoding)', 23, threading.Event())
                        self.assertEqual(state, 'Passed', details)
                        self.assertEqual(inspect_media(remux).codec, CODEC_LABELS[codec])
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), original)

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg required')
    def test_mid_conversion_cancel_cleans_partial_and_keeps_original(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); source = root / 'source.mp4'; target = root / 'output.mkv'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=s=160x120:d=1','-c:v','libx264',str(source)],check=True,timeout=20)
            event = threading.Event()
            state, _ = MediaSorterApp.transcode_video_file(inspect_media(source), target, 'H.264 MKV',23,event,lambda _fraction:event.set(), TRANSCODE_SOFTWARE,False)
            self.assertEqual(state, 'Cancelled')
            self.assertFalse(target.exists())
            self.assertEqual(list(root.glob('*.partial*')), [])
            self.assertTrue(source.exists())

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg required')
    def test_incompatible_mp4_remux_fails_without_dropping_subtitles(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); source = root/'subtitled.mkv'; target = root/'out.mp4'
            captions = root/'caption.srt'
            captions.write_text('1\n00:00:00,000 --> 00:00:00,500\nTest\n')
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=s=160x120:d=1','-i',str(captions),'-map','0:v','-map','1:s','-c:v','libx264','-c:s','ass',str(source)],check=True,timeout=20)
            original = hashlib.sha256(source.read_bytes()).hexdigest()
            state, details = MediaSorterApp.transcode_video_file(inspect_media(source), target, 'Remux to MP4 (no re-encoding)',23,threading.Event())
            self.assertEqual(state,'Failed',details)
            self.assertTrue('codec' in details.lower() or 'support' in details.lower(),details)
            self.assertFalse(target.exists())
            self.assertFalse(list(root.glob('*.partial*')))
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original)


if __name__ == '__main__': unittest.main()
