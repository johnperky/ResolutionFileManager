import json
from pathlib import Path
import tempfile
import unittest


class BackendTests(unittest.TestCase):
    def test_modes_and_native_scale(self):
        from ai_backends import mode_spec
        for name, family, scale in [('video_2x','video',2),('video_4x','video',4),('animation_2x','animation',2),('animation_4x','animation',4)]:
            self.assertEqual(mode_spec(name),(family,scale))
        with self.assertRaises(ValueError):mode_spec('ordinary')

    def test_video_2x_uses_native_2x_without_changing_still_photo_model(self):
        from ai_backends import video_gpu_model_spec,gpu_model_spec
        self.assertEqual(video_gpu_model_spec('video_2x'),('realesrgan-x2plus',2))
        self.assertEqual(video_gpu_model_spec('video_4x'),gpu_model_spec('video_4x'))
        self.assertEqual(gpu_model_spec('video_2x'),('realesrgan-x4plus',4))

    def test_optional_high_quality_2x_retains_previous_4x_model(self):
        from ai_backends import mode_spec,video_gpu_model_spec,VIDEO_MODES
        self.assertEqual(mode_spec('video_hq_2x'),('video',2))
        self.assertEqual(video_gpu_model_spec('video_hq_2x'),('realesrgan-x4plus',4))
        self.assertIn('video_hq_2x',VIDEO_MODES)
        from image_pipeline import IMAGE_MODES
        self.assertNotIn('video_hq_2x',IMAGE_MODES.values())

    def test_native_2x_cpu_tiles_do_not_create_4x_pixels(self):
        import numpy as np,threading
        from PIL import Image
        from unittest.mock import patch
        import ai_backends as backend
        pixels=np.random.default_rng(5).integers(0,256,(137,149,3),dtype=np.uint8)
        class Native2xSession:
            def run(self,names,inputs):
                block=inputs['input'];self_test.assertEqual(block.shape[2]%2,0);self_test.assertEqual(block.shape[3]%2,0)
                return [np.repeat(np.repeat(block,2,axis=2),2,axis=3)]
        self_test=self
        with patch.object(backend,'_session',return_value=Native2xSession()) as session:
            result=backend._cpu_image(Image.fromarray(pixels),'video_native',backend.asset_directory(),threading.Event(),native_scale=2)
        self.assertTrue(session.call_args.args[0].endswith('video_native-x2.onnx'))
        self.assertEqual(result.size,(298,274))
        np.testing.assert_array_equal(np.asarray(result),np.repeat(np.repeat(pixels,2,axis=0),2,axis=1))

    def test_animation_has_native_and_legacy_quality_video_paths(self):
        from ai_backends import video_gpu_model_spec,video_cpu_model_spec,gpu_model_spec,mode_spec
        self.assertEqual(video_gpu_model_spec('animation_2x'),('realesr-animation-native-x2',2))
        self.assertEqual(video_gpu_model_spec('animation_hq_2x'),('realesr-animevideov3',2))
        self.assertEqual(video_cpu_model_spec('animation_2x'),('animation_native',2))
        self.assertEqual(video_cpu_model_spec('animation_hq_2x'),('animation',4))
        self.assertEqual(mode_spec('animation_hq_2x'),('animation',2))
        self.assertEqual(gpu_model_spec('animation_2x'),('realesr-animevideov3',2))
        from image_pipeline import IMAGE_MODES
        self.assertNotIn('animation_hq_2x',IMAGE_MODES.values())

    def test_native_animation_cpu_keeps_odd_shape_without_video_unshuffle_padding(self):
        import numpy as np,threading
        from PIL import Image
        from unittest.mock import patch
        import ai_backends as backend
        pixels=np.random.default_rng(6).integers(0,256,(7,9,3),dtype=np.uint8)
        class Session:
            def run(self,names,inputs):
                block=inputs['input'];self_test.assertEqual(block.shape,(1,3,7,9))
                return [np.repeat(np.repeat(block,2,axis=2),2,axis=3)]
        self_test=self
        with patch.object(backend,'_session',return_value=Session()):
            result=backend._cpu_image(Image.fromarray(pixels),'animation_native',backend.asset_directory(),threading.Event(),native_scale=2)
        np.testing.assert_array_equal(np.asarray(result),np.repeat(np.repeat(pixels,2,axis=0),2,axis=1))

    def test_native_animation_clip_scalar_uses_float_param_encoding(self):
        from ai_backends import asset_directory
        graph=(asset_directory()/'models/realesr-animation-native-x2.param').read_text()
        high=next(line for line in graph.splitlines() if 'clip_high' in line)
        self.assertRegex(high,r'2=1\.0+e\+00')

    def test_missing_or_changed_assets_rejected(self):
        from ai_backends import validate_assets
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'manifest.json').write_text(json.dumps({'files':{'missing.bin':{'sha256':'0'*64}}}))
            with self.assertRaises((ValueError,FileNotFoundError)):validate_assets(root)
            (root/'missing.bin').write_bytes(b'changed')
            with self.assertRaises(ValueError):validate_assets(root)

    def test_bad_gpu_selection_does_not_disguise_cpu(self):
        from ai_backends import hardware_choice,AIHardware
        devices=[AIHardware('cpu','CPU','onnx',True,'')]
        self.assertEqual(hardware_choice('auto',devices).id,'cpu')
        with self.assertRaises(ValueError):hardware_choice('gpu:0',devices)


if __name__=='__main__':unittest.main()
