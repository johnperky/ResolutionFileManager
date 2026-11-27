"""Regression coverage for unchanged model pixels, worker reuse and ownership."""
import hashlib
import io
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from contextlib import ExitStack

from PIL import Image


class EfficiencyTests(unittest.TestCase):
    def test_cpu_tiles_keep_exact_pixels_with_bounded_numpy_allocations(self):
        import numpy as np
        import tracemalloc
        import ai_backends as backend
        class NearestSession:
            def run(self,names,inputs):
                block=inputs['input']
                self_test.assertEqual(block.dtype,np.float32)
                self_test.assertTrue(block.flags.c_contiguous)
                return [np.repeat(np.repeat(block,4,axis=2),4,axis=3)]
        self_test=self
        pixels=np.random.default_rng(42).integers(0,256,(379,501,3),dtype=np.uint8)
        image=Image.fromarray(pixels)
        with patch.object(backend,'_session',return_value=NearestSession()):
            tracemalloc.start()
            try:
                result=backend._cpu_image(image,'video',backend.asset_directory(),threading.Event())
                _,peak=tracemalloc.get_traced_memory()
            finally:tracemalloc.stop()
        # Budget for Python/NumPy tile buffers, not ONNX native arena/Pillow.
        # Covers edge and interior tiles in both axes without a real AI load.
        self.assertLess(peak,18*1024*1024,'Avoid full float image and padded-output quantisation copies')
        np.testing.assert_array_equal(np.asarray(result),np.repeat(np.repeat(pixels,4,axis=0),4,axis=1))

    def test_asset_verification_reuses_hash_but_rejects_changed_bytes(self):
        import ai_backends as backend
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);asset=root/'weight.bin';asset.write_bytes(b'original')
            (root/'manifest.json').write_text(json.dumps({'files':{'weight.bin':{
                'sha256':hashlib.sha256(b'original').hexdigest()}}}))
            time.sleep(1.05)  # Permit settled-asset caching on coarse Linux timestamps.
            with patch.object(backend.hashlib,'sha256',wraps=hashlib.sha256) as digest:
                backend.validate_assets(root);backend.validate_assets(root)
                self.assertEqual(digest.call_count,1)
                asset.write_bytes(b'corrupt!')
                with self.assertRaises(ValueError):backend.validate_assets(root)

    def test_immediate_same_size_asset_rewrite_is_rejected(self):
        import ai_backends as backend
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);asset=root/'weight.bin';asset.write_bytes(b'original')
            (root/'manifest.json').write_text(json.dumps({'files':{'weight.bin':{
                'sha256':hashlib.sha256(b'original').hexdigest()}}}))
            backend.validate_assets(root);asset.write_bytes(b'corrupt!')
            with self.assertRaises(ValueError):backend.validate_assets(root)

    def test_native_gpu_output_is_not_decoded_or_reencoded(self):
        import ai_backends as backend
        buffer=io.BytesIO();Image.new('RGB',(32,24),(32,71,135)).save(buffer,format='PNG')
        payload=buffer.getvalue()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'in.png';target=root/'out.png'
            Image.new('RGB',(8,6)).save(source)
            engine=backend.gpu_executable(root);engine.parent.mkdir();engine.touch()
            def launch(command,**kwargs):
                Path(command[command.index('-o')+1]).write_bytes(payload)
                process=MagicMock();process.poll.return_value=0;process.returncode=0
                return process
            with patch.object(backend,'start_owned_process',side_effect=launch),patch.object(backend,'stop_owned_process'),patch.object(Image.Image,'convert',side_effect=AssertionError('Unnecessary decode')):
                backend.infer_image(source,target,'video_4x','gpu:0',root,threading.Event(),working_dir=root)
            self.assertEqual(target.read_bytes(),payload)

    def test_batch_reuses_real_cpu_worker_and_preserves_standalone_pixels(self):
        from image_pipeline import ImageEnhancementBatch,convert_image_file
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'sample.png';work=root/'working';work.mkdir()
            sentinel=work/'keep.txt';sentinel.write_text('keep')
            image=Image.new('RGBA',(12,9),(40,90,160,128));image.putpixel((5,4),(200,25,50,200));image.save(source)
            status,details=convert_image_file(source,root/'reference.png','PNG','200%',threading.Event(),ai_mode='animation_2x',ai_hardware='cpu',working_folder=work)
            self.assertEqual(status,'Passed',details)
            with ImageEnhancementBatch() as batch,ExitStack() as readers:
                pids=[]
                for index in range(2):
                    target=root/f'batch{index}.png'
                    status,details=convert_image_file(source,target,'PNG','200%',threading.Event(),ai_mode='animation_2x',ai_hardware='cpu',working_folder=work,enhancement_batch=batch)
                    self.assertEqual(status,'Passed',details)
                    pids.append(batch.process.pid)
                    if index==0:
                        # Keep old IPC messages open: later requests must not
                        # replace them (Windows denies delete sharing).
                        directory=Path(batch._directory.name)
                        readers.enter_context((directory/'request-1.json').open())
                        readers.enter_context((directory/'response-1.json').open())
                    with Image.open(target) as actual,Image.open(root/'reference.png') as expected:
                        self.assertEqual(actual.tobytes(),expected.tobytes())
                self.assertEqual(pids[0],pids[1]);process=batch.process
            self.assertIsNotNone(process.poll());self.assertEqual(set(work.iterdir()),{sentinel})

    def test_cancelling_active_batch_stops_owned_worker_and_removes_scratch(self):
        from image_pipeline import ImageEnhancementBatch,convert_image_file
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'sample.png';work=root/'work';work.mkdir()
            Image.new('RGB',(16,12),'blue').save(source)
            with ImageEnhancementBatch() as batch:
                status,details=convert_image_file(source,root/'first.png','PNG','200%',threading.Event(),ai_mode='animation_2x',ai_hardware='cpu',working_folder=work,enhancement_batch=batch)
                self.assertEqual(status,'Passed',details);process=batch.process
                cancel=threading.Event()
                def stage(text):
                    if text=='AI enhancing (CPU)':cancel.set()
                status,details=convert_image_file(source,root/'cancelled.png','PNG','200%',cancel,ai_mode='video_4x',ai_hardware='cpu',working_folder=work,enhancement_batch=batch,on_stage=stage)
                self.assertEqual(status,'Cancelled',details)
            self.assertIsNotNone(process.poll());self.assertFalse((root/'cancelled.png').exists())
            self.assertTrue((root/'first.png').exists());self.assertEqual(list(work.iterdir()),[])

    def test_cancel_during_worker_request_stops_before_caller_cleanup(self):
        from image_pipeline import ImageEnhancementBatch
        from ai_backends import asset_directory
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'input.png';Image.new('RGB',(128,96),'blue').save(source)
            cancel=threading.Event();processes=[]
            with ImageEnhancementBatch() as batch:
                def check():
                    processes.append(batch.process)
                    cancel.set()
                with self.assertRaises(InterruptedError):
                    batch.infer(source,root/'out.png','video_4x',asset_directory(),cancel,root,check)
                self.assertTrue(processes);self.assertIsNotNone(processes[0].poll())
                self.assertIsNone(batch.process)
            self.assertEqual(set(root.iterdir()),{source})

    def test_worker_failure_is_reported_and_next_request_can_restart(self):
        from image_pipeline import ImageEnhancementBatch
        from ai_backends import asset_directory
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'input.png';Image.new('RGB',(8,6),'blue').save(source)
            with ImageEnhancementBatch() as batch:
                with self.assertRaises(RuntimeError):
                    batch.infer(source,root/'bad.png','bad_mode',asset_directory(),threading.Event(),root,lambda:None)
                self.assertIsNone(batch.process)
                batch.infer(source,root/'good.png','animation_2x',asset_directory(),threading.Event(),root,lambda:None)
                with Image.open(root/'good.png') as image:self.assertEqual(image.size,(16,12))

    def test_automatic_gpu_failure_uses_warm_cpu_fallback(self):
        import image_pipeline as pipeline
        from ai_backends import AIHardware
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'input.png';Image.new('RGBA',(8,6),(30,70,150,128)).save(source)
            devices=[AIHardware('gpu:0','GPU','ncnn',True),AIHardware('cpu','CPU','onnx',True)]
            with pipeline.ImageEnhancementBatch() as batch,patch.object(pipeline,'probe_hardware',return_value=devices),patch.object(pipeline,'infer_image',side_effect=RuntimeError('GPU unavailable')) as gpu:
                for index in range(2):
                    status,details=pipeline.convert_image_file(source,root/f'fallback-{index}.png','PNG','200%',threading.Event(),ai_mode='animation_2x',working_folder=root,enhancement_batch=batch)
                    self.assertEqual(status,'Passed',details);self.assertIn('cpu',details)
                    if index==0:process=batch.process
                    else:self.assertIs(batch.process,process)
                self.assertEqual(gpu.call_count,1,'Do not retry a failed automatic GPU for every image')
            self.assertIsNotNone(process.poll())

    def test_automatic_selection_does_not_mistake_software_vulkan_for_gpu(self):
        from ai_backends import AIHardware,hardware_choice
        devices=[AIHardware('gpu:0','llvmpipe (LLVM)','ncnn',True),AIHardware('cpu','CPU','onnx',True)]
        self.assertEqual(hardware_choice('auto',devices).id,'cpu')
        self.assertEqual(hardware_choice('gpu:0',devices).id,'gpu:0')

    def test_probe_uses_reported_gpu_indexes_even_if_first_gpu_fails(self):
        import ai_backends as backend
        diagnostics='[0 Unsupported GPU] queueC=0\n[5 NVIDIA Workstation] queueC=1\n[5 NVIDIA Workstation] fp16-p/s/a=1/1/1\n'
        calls=[]
        def infer(source,target,mode,hardware,*args,on_diagnostics=None,**kwargs):
            calls.append(hardware)
            if on_diagnostics:on_diagnostics(diagnostics)
            if hardware=='gpu:0':raise RuntimeError('First GPU does not support this model')
            Image.new('RGB',(16,16),'steelblue').save(target)
            return diagnostics if hardware!='cpu' else 'CPU'
        backend.probe_hardware.cache_clear()
        try:
            with tempfile.TemporaryDirectory() as directory,patch.object(backend,'validate_assets'),patch.object(backend,'infer_image',side_effect=infer):
                devices=backend.probe_hardware(Path(directory))
            self.assertEqual(calls,['cpu','gpu:0','gpu:5'])
            self.assertEqual([device.id for device in devices],['cpu','gpu:5'])
            self.assertEqual(devices[1].label,'NVIDIA Workstation')
        finally:backend.probe_hardware.cache_clear()

    def test_failed_gpu_inference_still_supplies_enumeration_diagnostics(self):
        import ai_backends as backend
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'in.png';target=root/'out.png'
            Image.new('RGB',(8,6)).save(source)
            engine=backend.gpu_executable(root);engine.parent.mkdir();engine.touch()
            def launch(command,**kwargs):
                kwargs['stderr'].write(b'[5 NVIDIA Workstation] queueC=1\nGPU inference failed\n')
                process=MagicMock();process.poll.return_value=1;process.returncode=1
                return process
            diagnostics=[]
            with patch.object(backend,'start_owned_process',side_effect=launch),patch.object(backend,'stop_owned_process'):
                with self.assertRaises(RuntimeError):
                    backend.infer_image(source,target,'animation_2x','gpu:0',root,threading.Event(),working_dir=root,on_diagnostics=diagnostics.append)
            self.assertEqual(len(diagnostics),1)
            self.assertIn('[5 NVIDIA Workstation]',diagnostics[0])

    def test_timed_out_gpu_still_supplies_enumeration_diagnostics(self):
        import ai_backends as backend
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'in.png';target=root/'out.png'
            Image.new('RGB',(8,6)).save(source)
            engine=backend.gpu_executable(root);engine.parent.mkdir();engine.touch()
            def launch(command,**kwargs):
                kwargs['stderr'].write(b'[5 NVIDIA Workstation] queueC=1\n')
                process=MagicMock();process.poll.return_value=None
                return process
            diagnostics=[]
            with patch.object(backend,'start_owned_process',side_effect=launch),patch.object(backend,'stop_owned_process'):
                with self.assertRaisesRegex(RuntimeError,'timed out'):
                    backend.infer_image(source,target,'animation_2x','gpu:0',root,threading.Event(),working_dir=root,timeout=0,on_diagnostics=diagnostics.append)
            self.assertEqual(len(diagnostics),1)
            self.assertIn('[5 NVIDIA Workstation]',diagnostics[0])


if __name__=='__main__':unittest.main()
