import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from conversion_conflicts import overwrite_approval,publish_conversion_output

class ConflictTests(unittest.TestCase):
 def test_default_never_overwrites_and_source_cannot_be_approved(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);old=r/'old';new=r/'new';old.write_bytes(b'old');new.write_bytes(b'new')
   with self.assertRaises(FileExistsError):publish_conversion_output(new,old)
   with self.assertRaises(ValueError):overwrite_approval(old,[old])
   self.assertEqual(old.read_bytes(),b'old')
 def test_approved_replace_and_changed_target_is_retained(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);target=r/'out';temp=r/'partial';target.write_bytes(b'old');temp.write_bytes(b'new');approval=overwrite_approval(target)
   publish_conversion_output(temp,target,approval);self.assertEqual(target.read_bytes(),b'new');self.assertEqual(list(r.iterdir()),[target])
   approval=overwrite_approval(target);target.write_bytes(b'changed');temp.write_bytes(b'next')
   with self.assertRaises(ValueError):publish_conversion_output(temp,target,approval)
   self.assertEqual(target.read_bytes(),b'changed')
 def test_new_arrival_after_backup_never_replaced(self):
  import ai_pipeline
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);target=r/'out';temp=r/'partial';target.write_bytes(b'old');temp.write_bytes(b'new');approval=overwrite_approval(target);publish=ai_pipeline.publish_output_without_replace
   def concurrent(source,dest):
    if source==temp:target.write_bytes(b'arrival')
    return publish(source,dest)
   with patch.object(ai_pipeline,'publish_output_without_replace',side_effect=concurrent):
    with self.assertRaises(OSError):publish_conversion_output(temp,target,approval)
   self.assertEqual(target.read_bytes(),b'arrival')
   self.assertTrue(any(p.read_bytes()==b'old' for p in r.iterdir() if p!=temp and p!=target))

if __name__=='__main__':unittest.main()
