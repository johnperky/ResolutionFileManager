import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from conversion_display import PreviewPublisher

class PreviewTests(unittest.TestCase):
 def test_closed_does_not_touch_pixels(self):
  with tempfile.TemporaryDirectory() as d:
   p=PreviewPublisher(d)
   self.assertFalse(p.wanted())
   p.publish(object())
   self.assertFalse((Path(d)/'latest.frame').exists())
 def test_full_quality_latest_throttled_and_optional(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'enabled').touch();p=PreviewPublisher(root)
   with Image.new('RGB',(1600,900),'red') as image:p.publish(image)
   with Image.open(root/'latest.frame') as image:self.assertEqual(image.size,(1600,900))
   original=(root/'latest.frame').read_bytes()
   with Image.new('RGB',(10,20),'blue') as image:p.publish(image)
   self.assertEqual((root/'latest.frame').read_bytes(),original)
   p.last=0
   with Image.new('RGB',(10,20),'blue') as image:p.publish(image)
   with Image.open(root/'latest.frame') as image:self.assertEqual(image.size,(10,20))
   self.assertEqual({f.name for f in root.iterdir()},{'enabled','latest.frame'})
 def test_preview_failure_cannot_fail_conversion(self):
  with tempfile.TemporaryDirectory() as d:
   (Path(d)/'enabled').touch();p=PreviewPublisher(d)
   with patch('conversion_display.os.replace',side_effect=PermissionError):
    with Image.new('RGB',(10,10),'red') as image:p.publish(image)
   self.assertFalse((Path(d)/'latest.tmp').exists())

class PlacementTests(unittest.TestCase):
 def test_beside_or_above_progress(self):
  from conversion_display import display_geometry
  for parent in [(300,100,1000,800),(0,0,1920,1040),(1000,100,900,800)]:
   x,y,w,h=display_geometry(parent,(0,0,1920,1040))
   self.assertGreaterEqual(x,0);self.assertGreaterEqual(y,0)
   self.assertLessEqual(x+w,1920);self.assertLessEqual(y+h,1040)
   px,py,pw,ph=parent
   self.assertTrue(x+w<=px or x>=px+pw or y+h<=py+ph-120)

if __name__=='__main__':unittest.main()
