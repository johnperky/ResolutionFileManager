"""Native packaged UI checks through owned Windows menus, no remote clicks."""
import argparse
import ctypes
from ctypes import wintypes as w
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sqlite3
import time
from PIL import ImageGrab


def main(binary, output, theme, scale):
    output.mkdir(parents=True,exist_ok=False)
    data=output/'ResolutionFileManager';data.mkdir()
    settings={'language':'en','geometry':'1850x940+0+0','appearance_theme':theme,'ui_scale':scale,
              'show_hidden_files':False,'left':{'path':'E:/free to use videos','recursive':True},
              'right':{'path':'E:/free to use videos','recursive':True,'inspector_enabled':True},
              'reminders':{'rating_disabled':True,'support_disabled':True}}
    (data/'settings.json').write_text(json.dumps(settings),encoding='utf-8')
    template=Path(__file__).resolve().parents[1].parent/'Store Preparation 12.7.8/Review Settings/ResolutionFileManager/metadata-cache.sqlite3'
    if template.exists():
        with sqlite3.connect(template.as_uri()+'?mode=ro',uri=True) as source, sqlite3.connect(data/template.name) as target:
            source.backup(target)
    env=dict(os.environ,LOCALAPPDATA=str(output.resolve()),XDG_CONFIG_HOME=str(output.resolve()),
             PATH=str(Path(os.environ['SystemRoot'])/'System32'))
    env.pop('PYTHONPATH',None);env.pop('PYTHONHOME',None)
    user=ctypes.windll.user32
    user.GetMenu.restype=w.HMENU;user.GetSubMenu.restype=w.HMENU
    callback_type=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
    process=subprocess.Popen([str(binary.resolve())],env=env)
    def owned_pids():
        class Entry(ctypes.Structure):
            _fields_=[('size',w.DWORD),('usage',w.DWORD),('pid',w.DWORD),('heap',ctypes.c_size_t),
                      ('module',w.DWORD),('threads',w.DWORD),('parent',w.DWORD),('priority',w.LONG),
                      ('flags',w.DWORD),('exe',w.WCHAR*260)]
        kernel=ctypes.windll.kernel32
        kernel.CreateToolhelp32Snapshot.restype=w.HANDLE
        handle=kernel.CreateToolhelp32Snapshot(2,0)
        assert handle != w.HANDLE(-1).value
        entry=Entry();entry.size=ctypes.sizeof(entry);rows=[]
        try:
            exists=kernel.Process32FirstW(w.HANDLE(handle),ctypes.byref(entry))
            while exists:
                rows.append((entry.pid,entry.parent))
                exists=kernel.Process32NextW(w.HANDLE(handle),ctypes.byref(entry))
        finally:kernel.CloseHandle(w.HANDLE(handle))
        ids={process.pid}
        for _ in range(4):ids.update(pid for pid,parent in rows if parent in ids)
        return ids
    def windows():
        ids=owned_pids()
        found=[]
        @callback_type
        def callback(hwnd,_):
            pid=w.DWORD();user.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
            if pid.value in ids and user.IsWindowVisible(hwnd):
                title=ctypes.create_unicode_buffer(512);user.GetWindowTextW(hwnd,title,512)
                if title.value:found.append((hwnd,title.value))
            return True
        user.EnumWindows(callback,0)
        return found
    def menu_command(hwnd,group,substring):
        menu=user.GetMenu(w.HWND(hwnd))
        def text(menu,index):
            name=ctypes.create_unicode_buffer(512)
            user.GetMenuStringW(w.HMENU(menu),index,name,512,0x400)
            return name.value.replace('&','')
        groups=[(i,text(menu,i)) for i in range(user.GetMenuItemCount(w.HMENU(menu)))]
        index=next(i for i,name in groups if group in name)
        sub=user.GetSubMenu(w.HMENU(menu),index)
        user.SendMessageW(w.HWND(hwnd),0x117,w.WPARAM(sub),w.LPARAM(index))
        entries=[(i,text(sub,i)) for i in range(user.GetMenuItemCount(w.HMENU(sub)))]
        matches=[i for i,name in entries if substring in name]
        # Tk draws submenu labels itself on Windows. Positions are verified
        # against create_menu_bar in the exact embedded source before this probe.
        positions={('Tools','Show hidden files'):0,('View','Appearance'):4}
        index=matches[0] if matches else positions[(group,substring)]
        identifier=user.GetMenuItemID(w.HMENU(sub),index)
        assert identifier not in (0,-1,0xffffffff)
        assert user.PostMessageW(w.HWND(hwnd),0x111,identifier,0)
    try:
        deadline=time.monotonic()+40;main_window=None
        while time.monotonic()<deadline:
            main_window=next((h for h,title in windows() if title.startswith('Resolution File Manager')),None)
            if main_window:break
            if process.poll() is not None:raise RuntimeError('Packaged process exited during startup')
            time.sleep(.2)
        assert main_window,'Packaged native window missing'
        time.sleep(10)
        ImageGrab.grab(window=main_window).save(output/'main.png')
        menu_command(main_window,'Tools','Show hidden files')
        deadline=time.monotonic()+10
        while time.monotonic()<deadline:
            saved=json.loads((data/'settings.json').read_text(encoding='utf-8-sig'))
            if saved.get('show_hidden_files') is True:break
            time.sleep(.1)
        assert saved.get('show_hidden_files') is True,'Native menu did not persist hidden-files toggle'
        menu_command(main_window,'Tools','Show hidden files');time.sleep(.5)
        assert json.loads((data/'settings.json').read_text(encoding='utf-8-sig'))['show_hidden_files'] is False
        menu_command(main_window,'View','Appearance')
        deadline=time.monotonic()+10;dialog=None
        while time.monotonic()<deadline:
            dialog=next((h for h,title in windows() if 'Appearance' in title),None)
            if dialog:break
            time.sleep(.1)
        assert dialog,'Native appearance dialog missing'
        time.sleep(.6)
        ImageGrab.grab(window=dialog).save(output/'appearance.png')
        user.PostMessageW(w.HWND(dialog),0x10,0,0);time.sleep(.3)
        report={'executable':str(binary),'sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),
                'theme':theme,'scale':scale,'native_menu_toggle_persisted':True,'native_appearance_opened':True,
                'isolated_settings':True,'PATH_system_only':True,'passed':True,
                'scope':'Current Windows host, isolated application environment; not a separate clean OS/Windows 10 machine.'}
        (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        user.PostMessageW(w.HWND(main_window),0x10,0,0)
        process.wait(timeout=20)
        print(json.dumps(report),flush=True)
    finally:
        if process.poll() is None:
            subprocess.run(['C:/Windows/System32/taskkill.exe','/PID',str(process.pid),'/T','/F'],capture_output=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary',type=Path);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--theme',default='System');parser.add_argument('--scale',type=int,default=100)
    args=parser.parse_args();main(args.binary,args.output,args.theme,args.scale)
