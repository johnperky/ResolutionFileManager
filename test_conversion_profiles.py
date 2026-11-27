import unittest

class ProfileTests(unittest.TestCase):
    def test_exact_order_and_container_matrix(self):
        from conversion_profiles import visible_profiles
        values=visible_profiles()
        self.assertEqual(len(values),38)
        for index,height in enumerate((360,540,720,1080,2160)):
            group=values[index*6:index*6+6]
            self.assertEqual([v.height for v in group],[height]*6)
            self.assertEqual([(v.family,v.extension) for v in group],[(f,e) for f in ('h264','hevc','av1') for e in ('.mp4','.mkv')])
        self.assertTrue(all(v.family is None for v in values[-2:]))

    def test_dimensions_rotation_and_sar(self):
        from conversion_profiles import output_dimensions
        self.assertEqual(output_dimensions(1920,1080,720),(1280,720))
        self.assertEqual(output_dimensions(1920,1080,720,90),(406,720))
        self.assertEqual(output_dimensions(720,576,540,sar=(16,15)),(720,540))
        for h in (360,540,720,1080,2160):
            w,height=output_dimensions(641,359,h)
            self.assertEqual(height,h);self.assertEqual(w%2,0)

if __name__=='__main__':unittest.main()
