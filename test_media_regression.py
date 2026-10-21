"""Small real-media regressions shared by Windows and Linux."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest

from PIL import Image
from media_sorter import MediaSorterApp, TRANSCODE_SOFTWARE, inspect_media

@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),"FFmpeg tools required")
class MediaRegressionTests(unittest.TestCase):
    def test_probe_verify_convert_remux_and_cancellation_preserve_originals(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); video=root/"source.mp4"; image=root/"photo.png"
            subprocess.run(["ffmpeg","-v","error","-f","lavfi","-i","color=c=blue:s=320x240:d=0.3","-c:v","mpeg4",str(video)],check=True,timeout=20)
            Image.new("RGB",(120,80),"red").save(image)
            original=hashlib.sha256(video.read_bytes()).hexdigest()
            item=inspect_media(video)
            self.assertEqual((item.width,item.height),(320,240))
            self.assertGreater(item.duration,0)
            self.assertEqual(MediaSorterApp.verify_media_file(image,threading.Event())[0],"Passed")
            self.assertEqual(MediaSorterApp.verify_media_file(video,threading.Event())[0],"Passed")
            converted=root/"720p.mp4"
            state,details=MediaSorterApp.transcode_video_file(item,converted,"H.264 MP4 (compatible)",23,threading.Event(),engine=TRANSCODE_SOFTWARE,hardware_decode=False,resolution_name="720p")
            self.assertEqual(state,"Passed",details)
            result=inspect_media(converted)
            self.assertEqual(result.height,720)
            self.assertEqual(result.width,960)
            remux=root/"copy.mkv"
            state,details=MediaSorterApp.transcode_video_file(item,remux,"Remux to MKV (no re-encoding)",23,threading.Event(),engine=TRANSCODE_SOFTWARE,hardware_decode=False)
            self.assertEqual(state,"Passed",details)
            self.assertEqual(inspect_media(remux).codec,item.codec)
            cancel=threading.Event(); cancel.set()
            target=root/"cancelled.mp4"
            self.assertEqual(MediaSorterApp.transcode_video_file(item,target,"H.264 MP4 (compatible)",23,cancel)[0],"Cancelled")
            self.assertFalse(target.exists())
            self.assertEqual(hashlib.sha256(video.read_bytes()).hexdigest(),original)

if __name__=="__main__":unittest.main()
