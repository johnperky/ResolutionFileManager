"""Check candidate integrity/resume and unapproved gallery handling without UI."""
import json
from pathlib import Path
import tempfile
import unittest
import batch_store_screenshots as batch


class CandidateTests(unittest.TestCase):
    def test_nvidia_title_decoration_does_not_hide_notifications(self):
        for name in ('NviewButtonCurtain','NviewButtonImage'):
            self.assertTrue(batch.title_decoration(name, (1723,1,1771,23), 0))
        self.assertFalse(batch.title_decoration('NviewButtonImage', (1540,800,1900,1020), 0))
        self.assertFalse(batch.title_decoration('Windows.UI.Core.CoreWindow', (1723,1,1771,23), 0))

    def test_focus_loss_reactivates_and_retries(self):
        checks = iter([False, False, True])
        attempts = []
        batch.ensure_capture_focus(lambda: next(checks), lambda: attempts.append(True), lambda: None)
        self.assertEqual(len(attempts), 2)

    def test_focus_cannot_be_regained_fails_without_capture(self):
        with self.assertRaises(RuntimeError):
            batch.ensure_capture_focus(lambda: False, lambda: None, lambda: None, attempts=3)

    def test_resume_rejects_changed_image_binary_and_path_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root/'sample.png'
            image.write_bytes(b'original')
            proof = {'binarySha256': 'binary', 'sourceSha256': {'module': 'hash'}}
            row = dict(proof, file='sample.png', sha256=batch.sha(image))
            self.assertTrue(batch.reusable(row, root, proof))
            self.assertFalse(batch.reusable(row, root, dict(proof, binarySha256='changed')))
            self.assertFalse(batch.reusable(dict(row, file='../sample.png'), root, proof))
            image.write_bytes(b'changed')
            self.assertFalse(batch.reusable(row, root, proof))

    def test_gallery_never_promotes_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'en').mkdir()
            batch.atomic_json(root/'en/captures.json', [{'language': 'en', 'view': batch.VIEWS[0],
                              'file': 'en/example.png', 'reviewed': False}])
            self.assertEqual(batch.gallery(root), 1)
            self.assertFalse(json.loads((root/'candidate-progress.json').read_text())[0]['reviewed'])
            self.assertFalse((root/'capture-progress.json').exists())

    def test_gallery_review_only_applies_to_exact_images(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'en').mkdir()
            row={'language':'en','view':batch.VIEWS[0],'file':'en/example.png','sha256':'original','reviewed':False}
            batch.atomic_json(root/'en/captures.json',[row])
            batch.atomic_json(root/'visual-review.json',{'visualReviewComplete':True,'captures':[row]})
            batch.gallery(root)
            self.assertIn('Visually reviewed screenshot candidates',(root/'REVIEW.html').read_text())
            batch.atomic_json(root/'en/captures.json',[dict(row,sha256='changed')])
            batch.gallery(root)
            self.assertIn('Unapproved screenshot candidates',(root/'REVIEW.html').read_text())


if __name__ == '__main__':
    unittest.main()
