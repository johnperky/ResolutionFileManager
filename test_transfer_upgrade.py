import tempfile
import threading
import unittest
from pathlib import Path


class TransferUpgradeTests(unittest.TestCase):
    def test_inspector_release_clamps_actual_sash_not_only_saved_width(self):
        from transfer_ui import UpgradePaneMixin
        class Panes:
            position=0
            def panes(self): return (1,2)
            def winfo_width(self): return 600
            def sashpos(self,index,value=None):
                if value is not None: self.position=value
                return self.position
        class Pane(UpgradePaneMixin): inspector_panes=Panes()
        pane=Pane(); pane.remember_inspector_width()
        self.assertGreaterEqual(pane.inspector_panes.position,180)
    def test_folder_modes_and_collision_reservations(self):
        from transfer_engine import plan_targets
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'source'; dest = root/'dest'
            files = [source/'a'/'one.mp4', source/'b'/'one.mp4']
            for path in files:
                path.parent.mkdir(parents=True); path.write_bytes(b'video')
            self.assertEqual(plan_targets(files, source, dest, True)[1][1], dest/'b'/'one.mp4')
            self.assertEqual(plan_targets(files, source, dest, False)[1][1], dest/'one.mp4')

    def test_same_path_never_destroys_source(self):
        from transfer_engine import transfer_file
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'one.mp4'; path.write_bytes(b'original')
            with self.assertRaises(ValueError):
                transfer_file(path,path,True,'replace',Path(directory)/'undo',threading.Event())
            self.assertEqual(path.read_bytes(),b'original')

    def test_keep_both_skip_and_replace_backup(self):
        from transfer_engine import transfer_file
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); source=root/'s.mp4'; target=root/'t.mp4'
            source.write_bytes(b'new'); target.write_bytes(b'old')
            cancel=threading.Event()
            self.assertIsNone(transfer_file(source,target,False,'skip',root/'undo',cancel))
            record=transfer_file(source,target,False,'keep both',root/'undo',cancel)
            self.assertEqual(record[1].name,'t (2).mp4')
            self.assertEqual(target.read_bytes(),b'old')
            record=transfer_file(source,target,True,'replace',root/'undo',cancel)
            self.assertEqual(record[3].read_bytes(),b'old')
            self.assertEqual(target.read_bytes(),b'new'); self.assertFalse(source.exists())

    def test_cancel_does_not_replace_or_remove_source(self):
        from transfer_engine import transfer_file
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); source=root/'s'; target=root/'t'
            source.write_bytes(b'new'); target.write_bytes(b'old')
            cancel=threading.Event(); cancel.set()
            with self.assertRaises(InterruptedError):
                transfer_file(source,target,True,'replace',root/'undo',cancel)
            self.assertEqual(source.read_bytes(),b'new'); self.assertEqual(target.read_bytes(),b'old')

    def test_invalid_folder_names(self):
        from transfer_engine import validate_folder_name
        for name in ('', '..', 'a/b', 'CON', 'bad.', 'bad '):
            with self.assertRaises(ValueError): validate_folder_name(name)
        self.assertEqual(validate_folder_name('New folder'),'New folder')

    def test_mid_copy_cancel_restores_destination_and_move_source(self):
        from transfer_engine import transfer_file
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); source=root/'s'; target=root/'t'; source.write_bytes(b'x'*(3*1024*1024)); target.write_bytes(b'old')
            cancel=threading.Event()
            with self.assertRaises(InterruptedError):
                transfer_file(source,target,True,'replace',root/'undo',cancel,progress=lambda count:cancel.set())
            self.assertEqual(source.stat().st_size,3*1024*1024); self.assertEqual(target.read_bytes(),b'old')
            self.assertEqual(list(root.glob('*.partial')),[])

    def test_failure_publishing_restores_replacement(self):
        from transfer_engine import transfer_file
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); source=root/'s'; target=root/'t'; source.write_bytes(b'new'); target.write_bytes(b'old')
            import os
            original=os.rename
            def fail(src,dst,*args,**kwargs):
                if Path(dst)==target and Path(src).name.startswith('.rfm-transfer-'): raise PermissionError('test')
                return original(src,dst,*args,**kwargs)
            with patch('transfer_engine.os.rename',fail),self.assertRaises(PermissionError):
                transfer_file(source,target,True,'replace',root/'undo',threading.Event())
            self.assertEqual(source.read_bytes(),b'new'); self.assertEqual(target.read_bytes(),b'old')

    def test_batch_keep_both_reserves_names_before_execution(self):
        from transfer_ui import UpgradeAppMixin
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); target=root/'out'/'one.mp4'
            pairs=[(root/'a'/'one.mp4',target),(root/'b'/'one.mp4',target),(root/'c'/'one.mp4',target)]
            planned=UpgradeAppMixin.resolve_transfer_conflicts(object(),pairs,'keep both')
            self.assertEqual([t.name for s,t,p in planned],['one.mp4','one (2).mp4','one (3).mp4'])

    def test_apply_all_only_prompts_once(self):
        from transfer_ui import UpgradeAppMixin
        class App(UpgradeAppMixin):
            calls=0
            def ask_transfer_conflict(self,*args): self.calls+=1; return 'skip',True
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); target=root/'t'; target.write_bytes(b'old'); app=App()
            self.assertEqual(app.resolve_transfer_conflicts([(root/'a',target),(root/'b',target)]),[])
            self.assertEqual(app.calls,1)

    def test_move_does_not_remove_source_changed_during_transfer(self):
        from transfer_engine import transfer_file
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); source=root/'s'; target=root/'t'; source.write_bytes(b'new'); target.write_bytes(b'old')
            changed=[False]
            def progress(count):
                if not changed[0]:
                    source.write_bytes(b'changed while copying'); changed[0]=True
            with self.assertRaises(OSError):
                transfer_file(source,target,True,'replace',root/'undo',threading.Event(),progress=progress)
            self.assertEqual(source.read_bytes(),b'changed while copying'); self.assertEqual(target.read_bytes(),b'old')

    def test_undo_guard_rejects_modified_target(self):
        from transfer_engine import file_stamp, validate_undo_target
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'copy'; path.write_bytes(b'copy'); stamp=file_stamp(path)
            path.write_bytes(b'modified after transfer')
            with self.assertRaises(OSError): validate_undo_target(path,stamp)

    @unittest.skipUnless(__import__('os').name=='nt','Windows exclusive-rename publication')
    def test_windows_publishes_staged_data_without_second_copy(self):
        from transfer_engine import transfer_file
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); source=root/'s'; target=root/'t'; source.write_bytes(b'new')
            original=Path.open
            def no_second_copy(path,*args,**kwargs):
                if path==target and args and args[0]=='xb': raise AssertionError('Second full copy')
                return original(path,*args,**kwargs)
            with patch.object(Path,'open',no_second_copy): transfer_file(source,target,False,'skip',root/'undo',threading.Event())
            self.assertEqual(target.read_bytes(),b'new')
