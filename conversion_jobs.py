"""Track conversion lifetime until owned process/file cleanup is complete."""
from dataclasses import dataclass,field
import threading

@dataclass
class ConversionJob:
    cancel:threading.Event
    label:str
    done:threading.Event=field(default_factory=threading.Event)
    thread:threading.Thread|None=None

class ConversionJobs:
    def __init__(self):
        self._jobs=[];self._lock=threading.Lock();self.closing=False

    def active(self):
        with self._lock:
            self._jobs=[job for job in self._jobs if not job.done.is_set()]
            return list(self._jobs)

    def start(self,target,cancel,label):
        job=ConversionJob(cancel,label)
        def run():
            try:target()
            finally:job.done.set()
        with self._lock:
            if self.closing:raise RuntimeError('The application is closing; no new conversion can start')
            self._jobs.append(job)
            job.thread=threading.Thread(target=run,daemon=True)
            try:job.thread.start()
            except BaseException:self._jobs.remove(job);raise
        return job

    def request_close(self,confirm,schedule,finish,on_wait=None):
        if self.closing:return False
        active=self.active()
        if active and not confirm():return False
        with self._lock:
            self.closing=True
            for job in self._jobs:job.cancel.set()
        if active and on_wait:on_wait()
        def poll():
            if self.active():schedule(100,poll)
            else:finish()
        poll();return True


def close_conversion_window(window,job,cancel,confirm):
    if getattr(window,'_conversion_close_pending',False):return
    if job is None or job.done.is_set():
        cancel.set();window.destroy();return
    if not confirm():return
    window._conversion_close_pending=True;cancel.set();window.title('Cancelling conversion and cleaning temporary files…');window.configure(cursor='watch')
    def wait():
        if not window.winfo_exists():return
        if job.done.is_set():window.destroy()
        else:window.after(100,wait)
    wait()
