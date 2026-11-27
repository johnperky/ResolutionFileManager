"""Image output safety and real standalone AI regression samples."""
import hashlib,json,shutil,subprocess,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

class ImageConversionTests(unittest.TestCase):
    def test_aspect_ratio_sizes(self):
        from image_pipeline import target_dimensions
        self.assertEqual(target_dimensions(400,200,'Original size'),(400,200))
        self.assertEqual(target_dimensions(400,200,'50%'),(200,100))
        self.assertEqual(target_dimensions(400,200,'200%'),(800,400))
        self.assertEqual(target_dimensions(400,200,'Long edge 1920 px'),(1920,960))
        self.assertEqual(target_dimensions(200,400,'Custom long edge',600),(300,600))

    def test_real_formats_alpha_orientation_and_no_overwrite(self):
        from image_pipeline import convert_image_file
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'source.png';Image.new('RGBA',(32,24),(25,100,200,100)).save(source);original=source.read_bytes()
            for format,ext in [('PNG','.png'),('JPEG','.jpg'),('WebP','.webp')]:
                target=root/('out'+ext)
                state,details=convert_image_file(source,target,format,'200%',threading.Event())
                self.assertEqual(state,'Passed',details)
                with Image.open(target) as image:
                    self.assertEqual(image.size,(64,48))
                    if format!='JPEG':self.assertEqual(image.getpixel((1,1))[3],100)
                before=target.read_bytes();state,_=convert_image_file(source,target,format,'50%',threading.Event())
                self.assertEqual(state,'Skipped');self.assertEqual(target.read_bytes(),before)
            self.assertEqual(source.read_bytes(),original)
            rotated=root/'rotated.jpg';image=Image.new('RGB',(32,24),'red');exif=Image.Exif();exif[274]=6;image.save(rotated,exif=exif)
            state,details=convert_image_file(rotated,root/'oriented.png','PNG','Original size',threading.Event())
            self.assertEqual(state,'Passed',details)
            with Image.open(root/'oriented.png') as image:self.assertEqual(image.size,(24,32))

    def test_cmyk_profile_is_not_attached_to_converted_rgb_pixels(self):
        from image_pipeline import convert_image_file
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'scan.jpg';target=root/'scan.png'
            Image.new('CMYK',(8,8),(0,100,50,0)).save(source,icc_profile=b'CMYK-only-profile')
            state,details=convert_image_file(source,target,'PNG','Original size',threading.Event())
            self.assertEqual(state,'Passed',details)
            with Image.open(target) as image:self.assertNotIn('icc_profile',image.info)

    def test_effects_remove_impulse_noise_and_smooth_or_expand_contrast(self):
        from image_pipeline import apply_effects
        image=Image.new('RGB',(9,9),(30,30,30));image.putpixel((4,4),(200,200,200))
        self.assertEqual(apply_effects(image,['Denoise'],2).getpixel((4,4)),(30,30,30))
        self.assertLess(apply_effects(image,['Smooth'],2).getpixel((4,4))[0],200)
        expanded=apply_effects(image,['Auto contrast'],2)
        self.assertEqual(expanded.getpixel((0,0)),(0,0,0));self.assertEqual(expanded.getpixel((4,4)),(255,255,255))
        self.assertNotEqual(apply_effects(image,['Sharpen'],2).tobytes(),image.tobytes())
        colour=Image.new('RGB',(4,4),(70,100,150))
        self.assertNotEqual(apply_effects(colour,['Colour boost'],2).tobytes(),colour.tobytes())

    def test_animated_input_is_rejected(self):
        from image_pipeline import convert_image_file
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'animation.gif';Image.new('RGB',(8,8),'red').save(source,save_all=True,append_images=[Image.new('RGB',(8,8),'blue')],duration=100)
            state,details=convert_image_file(source,root/'out.png','PNG','Original size',threading.Event())
            self.assertEqual(state,'Failed');self.assertIn('animated',details.lower());self.assertFalse((root/'out.png').exists())

    def test_real_cpu_photo_ai_and_owned_cleanup(self):
        from image_pipeline import convert_image_file
        import image_pipeline as pipeline
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);working=root/'working';working.mkdir();sentinel=working/'keep.txt';sentinel.write_text('untouched')
            source=root/'photo.png';Image.new('RGBA',(16,12),(60,90,120,128)).save(source);original=source.read_bytes()
            for mode,size in [('video_2x','Original size'),('animation_4x','200%')]:
                target=root/(mode+'.png');events=[]
                state,details=convert_image_file(source,target,'PNG',size,threading.Event(),ai_mode=mode,ai_hardware='cpu',working_folder=working,on_stage=events.append)
                self.assertEqual(state,'Passed',details);self.assertTrue(events)
                with Image.open(target) as image:
                    self.assertEqual(image.size,(16,12) if size=='Original size' else (32,24));self.assertEqual(image.getpixel((0,0))[3],128)
                self.assertEqual(set(working.iterdir()),{sentinel})
            event=threading.Event();target=root/'cancelled.png'
            def cancel(stage):
                if 'AI' in stage:event.set()
            state,details=convert_image_file(source,target,'PNG','200%',event,ai_mode='video_2x',ai_hardware='cpu',working_folder=working,on_stage=cancel)
            self.assertEqual(state,'Cancelled',details);self.assertFalse(target.exists());self.assertEqual(set(working.iterdir()),{sentinel})
            self.assertEqual(source.read_bytes(),original);self.assertEqual(sentinel.read_text(),'untouched')
            from types import SimpleNamespace
            with patch.object(pipeline.shutil,'disk_usage',return_value=SimpleNamespace(free=0)):
                state,details=convert_image_file(source,target,'PNG','200%',threading.Event(),ai_mode='video_2x',ai_hardware='cpu',working_folder=working)
            self.assertEqual(state,'Failed');self.assertIn('space',details);self.assertFalse(target.exists());self.assertEqual(set(working.iterdir()),{sentinel})

if __name__=='__main__':unittest.main()
