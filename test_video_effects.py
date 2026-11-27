import unittest
from video_enhancement import video_effect_arguments,fast_video_arguments

class VideoEffectTests(unittest.TestCase):
 def test_no_effects_preserves_existing_arguments(self):
  args=['-map','0:v:0','-vf','scale=640:360','-c:v','libx264']
  self.assertEqual(video_effect_arguments(args,(),2),args)
 def test_fast_sharpen_is_replaced_not_doubled(self):
  args=fast_video_arguments(['-vf','scale=640:360'],'Software / CPU')
  result=video_effect_arguments(args,('Sharpen','Denoise','Smooth','Contrast boost','Colour boost'),3)
  chain=result[result.index('-vf')+1]
  self.assertEqual(chain.count('unsharp='),1)
  self.assertIn('hqdn3d=',chain);self.assertIn('gblur=',chain)
  self.assertIn('contrast=',chain);self.assertIn('saturation=',chain)
  self.assertEqual(result.count('-vf'),1)
 def test_filters_before_upload_and_reject_unknown_values(self):
  result=video_effect_arguments(['-vf','scale=640:360,format=nv12,hwupload'],('Sharpen',),1)
  chain=result[result.index('-vf')+1]
  self.assertLess(chain.index('unsharp='),chain.index('format='))
  for effects,strength in [(('Magic',),2),(('Sharpen',),0)]:
   with self.assertRaises(ValueError):video_effect_arguments([],effects,strength)

if __name__=='__main__':unittest.main()
