import subprocess,sys,tempfile,threading,time,unittest
from pathlib import Path

class ConversionShutdownTests(unittest.TestCase):
    def test_refusing_quit_does_not_cancel_work(self):
        from conversion_jobs import ConversionJobs
        registry=ConversionJobs();cancel=threading.Event();job=registry.start(lambda:cancel.wait(5),cancel,'video');scheduled=[];finished=[]
        try:
            registry.request_close(lambda:False,lambda delay,callback:scheduled.append(callback),lambda:finished.append(True))
            self.assertFalse(cancel.is_set());self.assertFalse(finished);self.assertFalse(scheduled);self.assertTrue(registry.active())
        finally:cancel.set();self.assertTrue(job.done.wait(2))

    def test_confirmed_quit_waits_for_all_owned_cleanup(self):
        from conversion_jobs import ConversionJobs
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);sentinel=root/'completed.mp4';sentinel.write_bytes(b'keep');registry=ConversionJobs();releases=[threading.Event(),threading.Event()];started=[threading.Event(),threading.Event()];cancel=[threading.Event(),threading.Event()]
            def worker(index):
                with tempfile.TemporaryDirectory(prefix='owned-',dir=root) as folder:
                    (Path(folder)/'partial.png').write_bytes(b'working');started[index].set();cancel[index].wait(5);releases[index].wait(5)
            jobs=[registry.start(lambda index=i:worker(index),cancel[i],'conversion') for i in range(2)]
            try:
                self.assertTrue(all(event.wait(2) for event in started));callbacks=[];finished=[]
                registry.request_close(lambda:True,lambda delay,callback:callbacks.append(callback),lambda:finished.append(set(p.name for p in root.iterdir())))
                self.assertTrue(all(event.is_set() for event in cancel));self.assertFalse(finished)
                releases[0].set();self.assertTrue(jobs[0].done.wait(2));callbacks.pop(0)();self.assertFalse(finished)
                releases[1].set();self.assertTrue(jobs[1].done.wait(2));callbacks.pop(0)();self.assertEqual(finished,[{'completed.mp4'}]);self.assertEqual(sentinel.read_bytes(),b'keep')
            finally:
                for event in cancel+releases:event.set()
                for job in jobs:job.done.wait(2)

    def test_shutdown_rejects_new_work_and_no_idle_prompt(self):
        from conversion_jobs import ConversionJobs
        registry=ConversionJobs();prompts=[];finished=[]
        registry.request_close(lambda:prompts.append(True),lambda delay,callback:None,lambda:finished.append(True))
        self.assertEqual(prompts,[]);self.assertEqual(finished,[True])
        with self.assertRaises(RuntimeError):registry.start(lambda:None,threading.Event(),'late job')

    def test_conversion_window_refusal_and_cleanup_wait(self):
        from conversion_jobs import close_conversion_window,ConversionJob
        class Window:
            def __init__(self):self.destroyed=False;self.callbacks=[]
            def destroy(self):self.destroyed=True
            def title(self,text):pass
            def configure(self,**kwargs):pass
            def winfo_exists(self):return not self.destroyed
            def after(self,delay,callback):self.callbacks.append(callback)
        window=Window();cancel=threading.Event();job=ConversionJob(cancel,'image')
        close_conversion_window(window,job,cancel,lambda:False)
        self.assertFalse(cancel.is_set());self.assertFalse(window.destroyed)
        close_conversion_window(window,job,cancel,lambda:True)
        self.assertTrue(cancel.is_set());self.assertFalse(window.destroyed)
        job.done.set();window.callbacks.pop()();self.assertTrue(window.destroyed)

    def test_exited_launcher_does_not_abandon_worker(self):
        from process_utils import start_owned_process,stop_owned_process
        with tempfile.TemporaryDirectory() as d:
            beat=Path(d)/'heartbeat.txt'
            child="import sys,time,signal;from pathlib import Path;signal.signal(signal.SIGTERM,signal.SIG_IGN);p=Path(sys.argv[1]);\nwhile True:p.write_text(str(time.monotonic()));time.sleep(.05)"
            parent="import subprocess,sys,time;subprocess.Popen([sys.executable,'-c',"+repr(child)+",sys.argv[1]]);time.sleep(.4)"
            process=start_owned_process([sys.executable,'-c',parent,str(beat)])
            try:
                process.wait(timeout=5);self.assertTrue(beat.exists())
                stop_owned_process(process);time.sleep(.15)
                before=beat.read_bytes();time.sleep(.2);self.assertEqual(beat.read_bytes(),before)
            finally:stop_owned_process(process)

    def test_cancel_stops_owned_child_and_grandchild(self):
        from process_utils import start_owned_process,stop_owned_process
        with tempfile.TemporaryDirectory() as d:
            beat=Path(d)/'heartbeat.txt'
            child="import sys,time;from pathlib import Path;p=Path(sys.argv[1]);\nwhile True:p.write_text(str(time.monotonic()));time.sleep(.05)"
            parent="import subprocess,sys,time;subprocess.Popen([sys.executable,'-c',"+repr(child)+",sys.argv[1]]);time.sleep(60)"
            process=start_owned_process([sys.executable,'-c',parent,str(beat)])
            try:
                until=time.monotonic()+5
                while not beat.exists() and time.monotonic()<until:time.sleep(.02)
                self.assertTrue(beat.exists());stop_owned_process(process);self.assertIsNotNone(process.poll());before=beat.read_bytes();time.sleep(.2);self.assertEqual(beat.read_bytes(),before)
            finally:stop_owned_process(process)

if __name__=='__main__':unittest.main()
