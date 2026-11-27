import sys,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import patch
class ProgressTests(unittest.TestCase):
 def test_child_stderr_completion_reaches_callback_before_exit(self):
  from ai_pipeline import _run
  with tempfile.TemporaryDirectory() as d:
   marker=Path(d)/'seen'
   code="import sys,time;from pathlib import Path;p=Path(sys.argv[1]);print('saved frame done',file=sys.stderr,flush=True);end=time.monotonic()+2\nwhile not p.exists() and time.monotonic()<end:time.sleep(.01)\nsys.exit(0 if p.exists() else 7)"
   _run([sys.executable,'-u','-c',code,str(marker)],threading.Event(),on_line=lambda line:marker.write_text(line))
   self.assertEqual(marker.read_text(),'saved frame done')
 def test_preparation_reports_activity_before_frame_probe(self):
  import ai_pipeline as p
  with tempfile.TemporaryDirectory() as d:
   events=[]
   def probe(*args):
    self.assertTrue(events,'Setup must visibly start before the potentially slow frame probe')
    self.assertIsNone(events[-1].fraction);raise InterruptedError('test cancellation')
   with patch.object(p,'media_probe',side_effect=probe),self.assertRaises(InterruptedError):
    p.prepare_ai_video('unused',Path(d)/'work','video_2x','cpu','unused',threading.Event(),events.append)
 def test_gpu_saved_frames_report_before_batch_returns_without_regressing(self):
  import ai_pipeline as p
  events=[];info={'hdr':False,'width':16,'height':12,'fps':4,'duration':.5,'sar':(1,1),'frames':[{'best_effort_timestamp_time':'0'},{'best_effort_timestamp_time':'.25'}]}
  def run(command,cancel,check,on_line=None):
   self.assertIn('-v',command);self.assertIsNotNone(on_line)
   on_line('source/000000001.png -> output/000000001.png done')
   self.assertEqual(events[-1].completed,1)
   on_line('source/000000002.png -> output/000000002.png done')
  def stream(source,work,info,stamps,durations,mode,cancel,enhance,progress,check):
   enhance(Path(work)/'source',Path(work)/'upscaled')
   progress(1);progress(2)
   output=Path(work)/'frames.mkv';output.touch();return output
  with tempfile.TemporaryDirectory() as d,patch.object(p,'media_probe',return_value=info),patch.object(p,'_run',side_effect=run),patch('ai_video_stream.stream_gpu',side_effect=stream):
   p.prepare_ai_video('unused',Path(d),'video_2x','gpu:0','assets/ai',threading.Event(),events.append)
  fractions=[e.fraction for e in events if e.fraction is not None]
  self.assertEqual(fractions,[.5,1,1,1])

 def test_activity_switches_to_measured_progress_and_stops(self):
  from conversion_ui import set_conversion_activity
  class Bar:
   def __init__(self):self.values={'mode':'determinate','value':0};self.running=False
   def cget(self,key):return self.values[key]
   def configure(self,**kw):self.values.update(kw)
   def start(self,*args):self.running=True
   def stop(self):self.running=False
  bar=Bar();set_conversion_activity(bar,None);self.assertTrue(bar.running);self.assertEqual(bar.values['mode'],'indeterminate')
  set_conversion_activity(bar,.25);self.assertFalse(bar.running);self.assertEqual(bar.values['mode'],'determinate');self.assertEqual(bar.values['value'],25)
  set_conversion_activity(bar,0);self.assertFalse(bar.running);self.assertEqual(bar.values['value'],0)
if __name__=='__main__':unittest.main()
