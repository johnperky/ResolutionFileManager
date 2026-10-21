"""Preview planning and cancellable, no-silent-overwrite file transfers."""
import os
from pathlib import Path
import shutil
import tempfile
import time
import threading
from contextlib import contextmanager
from functools import wraps


class MediaAccess:
    """Concurrent readers; a pending restore blocks new readers until drained."""
    def __init__(self):
        self.condition=threading.Condition(); self.readers=0; self.writers=0; self.writing=False

    @contextmanager
    def read(self):
        with self.condition:
            self.condition.wait_for(lambda:not self.writing and not self.writers)
            self.readers+=1
        try: yield
        finally:
            with self.condition:
                self.readers-=1; self.condition.notify_all()

    @contextmanager
    def exclusive(self):
        with self.condition:
            self.writers+=1
            self.condition.wait_for(lambda:not self.writing and self.readers==0)
            self.writers-=1; self.writing=True
        try: yield
        finally:
            with self.condition:
                self.writing=False; self.condition.notify_all()

    def read_call(self, function, *args, **kwargs):
        with self.read(): return function(*args,**kwargs)

    def reading(self,function):
        @wraps(function)
        def wrapped(*args,**kwargs): return self.read_call(function,*args,**kwargs)
        return wrapped


MEDIA_ACCESS=MediaAccess()


def retry_busy(action,timeout=2.0):
    deadline=time.monotonic()+timeout
    while True:
        try: return action()
        except OSError as exc:
            if getattr(exc,'winerror',None) not in (32,33) or time.monotonic()>=deadline: raise
            time.sleep(.05)


def move_without_replace(source,target):
    if target.exists(): raise FileExistsError(f'Undo would overwrite an existing file: {target}. Both files were retained.')
    target.parent.mkdir(parents=True,exist_ok=True)
    if os.name=='nt':
        try: os.rename(source,target); return
        except OSError as exc:
            if getattr(exc,'winerror',None)!=17: raise
    result=transfer_file(source,target,True,'skip',target.parent,threading.Event())
    if result is None: raise FileExistsError(str(target))


def undo_transfer(record,expected,checkpoint):
    """Checkpoint the restore phase so a failed backup restore is retryable."""
    mode,target,source,backup=record
    if mode!='restore':
        if not target.exists(): raise FileNotFoundError(f'Undo target is missing; recovery retained: {target}')
        validate_undo_target(target,expected)
        if mode=='move': retry_busy(lambda:move_without_replace(target,source))
        elif mode=='copy': retry_busy(target.unlink)
        else: raise ValueError(mode)
        checkpoint(('restore',target,source,backup))
    if backup:
        if not backup.exists(): raise FileNotFoundError(f'Undo backup is missing: {backup}')
        retry_busy(lambda:move_without_replace(backup,target))


def path_key(path):
    return os.path.normcase(str(Path(path).resolve()))


def file_stamp(path):
    stat=Path(path).stat()
    return stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns


def validate_undo_target(path, expected):
    if expected is not None and file_stamp(path)!=expected:
        raise OSError(f'Undo stopped because this file changed after transfer: {path}. The file was retained.')


def validate_folder_name(name):
    reserved = {'CON','PRN','AUX','NUL', *(f'COM{i}' for i in range(1,10)), *(f'LPT{i}' for i in range(1,10))}
    if (not name or name in {'.','..'} or name != name.rstrip(' .')
        or any(c in '<>:"/\\|?*' or ord(c)<32 for c in name)
        or name.split('.')[0].upper() in reserved):
        raise ValueError('Enter a valid folder name without slashes, reserved names or trailing spaces/dots.')
    return name


def plan_targets(paths, source_root, destination, preserve):
    pairs=[]
    for path in paths:
        path=Path(path)
        try: relative=path.relative_to(source_root) if preserve else Path(path.name)
        except ValueError: relative=Path(path.name)
        pairs.append((path,Path(destination)/relative))
    return pairs


def available_target(path, reserved=()):
    path=Path(path); keys=set(reserved); candidate=path; index=2
    while candidate.exists() or path_key(candidate) in keys:
        candidate=path.with_name(f'{path.stem} ({index}){path.suffix}'); index+=1
    return candidate


def transfer_file(source, target, move, policy, undo_directory, cancel, paused=lambda:False, progress=lambda count:None):
    source,target=Path(source),Path(target)
    if path_key(source)==path_key(target) or (target.exists() and os.path.samefile(source,target)):
        raise ValueError('Source and destination are the same file; nothing was changed.')
    if cancel.is_set(): raise InterruptedError('Cancelled')
    original_stamp=file_stamp(source)
    if target.exists():
        if target.is_dir(): raise IsADirectoryError(str(target))
        if policy=='skip' or (policy=='newer' and source.stat().st_mtime<=target.stat().st_mtime): return None
        if policy=='keep both': target=available_target(target)
        elif policy not in {'replace','newer'}: raise FileExistsError(str(target))
    target.parent.mkdir(parents=True,exist_ok=True)
    temporary=None; backup=None; published=False
    try:
        fd,name=tempfile.mkstemp(prefix='.rfm-transfer-',suffix='.partial',dir=target.parent)
        temporary=Path(name)
        with os.fdopen(fd,'wb') as dst, source.open('rb') as src:
            while True:
                while paused() and not cancel.is_set(): time.sleep(.05)
                if cancel.is_set(): raise InterruptedError('Cancelled')
                block=src.read(1024*1024)
                if not block: break
                dst.write(block); progress(len(block))
            dst.flush(); os.fsync(dst.fileno())
        shutil.copystat(source,temporary)
        if file_stamp(source)!=original_stamp: raise OSError('Source changed during transfer; retained original. Retry after writing finishes.')
        if cancel.is_set(): raise InterruptedError('Cancelled')
        if target.exists():
            if policy not in {'replace','newer'}: raise FileExistsError(f'Destination changed; retry: {target}')
            undo_directory=Path(undo_directory); undo_directory.mkdir(parents=True,exist_ok=True)
            backup=undo_directory/f'{time.time_ns()}-{target.name}'
            shutil.move(target,backup)
        # Exclusive create prevents a newly arriving file being overwritten.
        # Copy from completed staging works on FAT/exFAT as well as NTFS.
        if os.name=='nt':
            # Windows rename refuses an existing target, including FAT/exFAT;
            # publish the completed staging file without copying it twice.
            os.rename(temporary,target); published=True
        else:
            try: os.link(temporary,target); published=True
            except FileExistsError: raise
            except OSError:
                # Filesystems without hard links still get exclusive creation.
                with target.open('xb') as dst:
                    published=True
                    with temporary.open('rb') as src:
                        while True:
                            while paused() and not cancel.is_set(): time.sleep(.05)
                            if cancel.is_set(): raise InterruptedError('Cancelled')
                            block=src.read(1024*1024)
                            if not block: break
                            dst.write(block)
                    dst.flush(); os.fsync(dst.fileno())
        if temporary.exists(): shutil.copystat(temporary,target)
        if move:
            if file_stamp(source)!=original_stamp: raise OSError('Source changed during transfer; retained original. Retry after writing finishes.')
            source.unlink()
        return ('move' if move else 'copy',target,source,backup)
    except BaseException:
        if published: target.unlink(missing_ok=True)
        if backup and backup.exists() and not target.exists(): shutil.move(backup,target)
        raise
    finally:
        if temporary: temporary.unlink(missing_ok=True)
