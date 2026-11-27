"""Supervise only subprocess trees launched for a conversion."""
import os,signal,subprocess
from pathlib import Path


def start_owned_process(*args, **kwargs):
    process = subprocess.Popen(*args, **kwargs, **owned_process_options())
    if os.name == 'nt':
        # A job retains ownership even when a launcher exits before its child.
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel.CreateJobObjectW.restype = wintypes.HANDLE
        kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.CreateJobObjectW(None, None)
        if not handle or not kernel.AssignProcessToJobObject(handle, int(process._handle)):
            error = ctypes.get_last_error()
            if handle: kernel.CloseHandle(handle)
            process.kill(); process.wait()
            raise ctypes.WinError(error)
        process._rfm_job = handle
    return process

def owned_process_options():
    return {'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {'start_new_session':True}

def stop_owned_process(process):
    if process is None:return
    if os.name=='nt':
        handle = getattr(process, '_rfm_job', None)
        if handle:
            import ctypes
            from ctypes import wintypes
            kernel = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
            kernel.CloseHandle.argtypes = [wintypes.HANDLE]
            kernel.TerminateJobObject(handle, 1)
            kernel.CloseHandle(handle)
            process._rfm_job = None
        if process.poll() is not None:return
        # Frozen/venv launchers can have a worker child. Terminating just the
        # launcher leaves that child running and holding temporary files open.
        taskkill=Path(os.environ.get('SystemRoot','C:/Windows'))/'System32/taskkill.exe'
        try:subprocess.run([str(taskkill),'/PID',str(process.pid),'/T','/F'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW)
        except (OSError,subprocess.TimeoutExpired):pass
    else:
        try:os.killpg(process.pid,signal.SIGTERM)
        except ProcessLookupError:pass
    try:process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if os.name!='nt':
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
        process.kill();process.wait(timeout=5)
    finally:
        if os.name!='nt':
            # Parent exit alone does not prove every member stopped.
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
