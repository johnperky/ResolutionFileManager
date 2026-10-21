import os
import tempfile
import threading
import time
import unittest
from pathlib import Path


class BusyUndoTests(unittest.TestCase):
    def test_application_keeps_failed_record_and_retry_restores_original(self):
        from types import SimpleNamespace
        from media_sorter import MediaSorterApp
        from transfer_engine import file_stamp
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); target=root/'target'; source=root/'source'; backup=root/'backup'
            target.write_bytes(b'new'); source.write_bytes(b'recreated'); backup.write_bytes(b'old')
            record=('move',target,source,backup); records=[record]
            app=SimpleNamespace(undo_stamps={(id(records),id(record)):file_stamp(target)},
                metadata_cache=SimpleNamespace(move_user_data=lambda *a:None,delete_user_data=lambda *a:None))
            errors=MediaSorterApp.restore_undo_records(app,'operation',records)
            self.assertTrue(errors); self.assertEqual(len(records),1)
            self.assertEqual(source.read_bytes(),b'recreated'); self.assertEqual(backup.read_bytes(),b'old')
            source.unlink()
            self.assertEqual(MediaSorterApp.restore_undo_records(app,'operation',records),[])
            self.assertEqual(records,[]); self.assertEqual(source.read_bytes(),b'new'); self.assertEqual(target.read_bytes(),b'old')

    def test_background_readers_finish_before_exclusive_restore(self):
        from transfer_engine import MediaAccess
        gate=MediaAccess(); reading=threading.Event(); release=threading.Event(); restored=threading.Event()
        def reader():
            with gate.read(): reading.set(); release.wait(3)
        def writer():
            with gate.exclusive(): restored.set()
        a=threading.Thread(target=reader); b=threading.Thread(target=writer)
        a.start(); self.assertTrue(reading.wait(1)); b.start()
        self.assertFalse(restored.wait(.1)); release.set(); a.join(2); b.join(2)
        self.assertTrue(restored.is_set())

    def test_failed_backup_restore_retains_resumable_state(self):
        from transfer_engine import undo_transfer, file_stamp
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); target=root/'target'; source=root/'source'; backup=root/'backup'
            target.write_bytes(b'new'); backup.write_bytes(b'old')
            states=[]; record=('move',target,source,backup)
            # Existing destination directory prevents backup restoration without
            # touching either the restored source or the original backup.
            def checkpoint(state):
                states.append(state); target.mkdir()
            with self.assertRaises(OSError): undo_transfer(record,file_stamp(target),checkpoint)
            self.assertEqual(source.read_bytes(),b'new'); self.assertEqual(backup.read_bytes(),b'old')
            self.assertEqual(states[-1][0],'restore')
            target.rmdir(); undo_transfer(states[-1],None,lambda state:None)
            self.assertEqual(target.read_bytes(),b'old'); self.assertEqual(source.read_bytes(),b'new')

    @unittest.skipUnless(os.name=='nt','Windows sharing lock')
    def test_real_windows_busy_destination_retries_then_restores(self):
        import ctypes
        from ctypes import wintypes
        from transfer_engine import undo_transfer,file_stamp
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
        kernel.CreateFileW.restype=wintypes.HANDLE
        kernel.CloseHandle.argtypes=[wintypes.HANDLE]
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); target=root/'target'; source=root/'source'; backup=root/'backup'
            target.write_bytes(b'new'); backup.write_bytes(b'old'); stamp=file_stamp(target)
            handle=kernel.CreateFileW(str(target),0x80000000,1,None,3,0,None)
            self.assertNotEqual(handle,ctypes.c_void_p(-1).value)
            timer=threading.Timer(.2,lambda:kernel.CloseHandle(handle)); timer.start()
            try: undo_transfer(('move',target,source,backup),stamp,lambda state:None)
            finally: timer.join()
            self.assertEqual(source.read_bytes(),b'new'); self.assertEqual(target.read_bytes(),b'old')

if __name__=='__main__': unittest.main()
