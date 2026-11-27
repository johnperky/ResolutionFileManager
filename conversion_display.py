"""Optional full-resolution conversion snapshots; preview errors never fail a job."""
import os
from pathlib import Path
import tempfile
import shutil
import time
import threading
import tkinter as tk
from tkinter import ttk
from PIL import Image,ImageTk


def display_geometry(parent,screen):
    """Prefer unused side space; otherwise avoid the bottom progress area."""
    px,py,pw,ph=parent;sx,sy,sw,sh=screen
    left=max(0,px-sx-16);right=max(0,sx+sw-(px+pw)-16)
    side=max(left,right)
    if side>=360:
        width=min(680,side);height=min(540,sh-32)
        x=px+pw+8 if right>=left else px-width-8
        y=max(sy+8,min(py,sy+sh-height-8))
    else:
        width=min(640,sw-32)
        # Progress indicators sit at the bottom of both conversion dialogs.
        bottom=min(sy+sh-16,py+ph-140)
        height=min(480,max(120,bottom-(sy+16)))
        x=sx+sw-width-16;y=sy+16
    return int(x),int(y),int(width),int(height)


def monitor_area(parent):
    # Windows work area respects the monitor containing the conversion dialog.
    if os.name=='nt':
        try:
            import ctypes
            from ctypes import wintypes
            class MonitorInfo(ctypes.Structure):
                _fields_=[('size',wintypes.DWORD),('monitor',wintypes.RECT),('work',wintypes.RECT),('flags',wintypes.DWORD)]
            user=ctypes.windll.user32
            user.MonitorFromWindow.argtypes=[wintypes.HWND,wintypes.DWORD]
            user.MonitorFromWindow.restype=wintypes.HANDLE
            user.GetMonitorInfoW.argtypes=[wintypes.HANDLE,ctypes.POINTER(MonitorInfo)]
            info=MonitorInfo();info.size=ctypes.sizeof(info)
            if user.GetMonitorInfoW(user.MonitorFromWindow(parent.winfo_id(),2),ctypes.byref(info)):
                r=info.work;return r.left,r.top,r.right-r.left,r.bottom-r.top
        except (OSError,AttributeError):pass
    return parent.winfo_vrootx(),parent.winfo_vrooty(),parent.winfo_vrootwidth(),parent.winfo_vrootheight()


class PreviewPublisher:
    def __init__(self,directory):
        self.directory=Path(directory) if directory else None
        self.last=0
        self.lock=threading.Lock()

    def wanted(self):
        try:return self.directory is not None and time.monotonic()-self.last>=1 and (self.directory/'enabled').exists()
        except OSError:return False

    def _publish(self,write):
        # Both still-image reopening and a conversion may request a snapshot.
        with self.lock:
            if not self.wanted():return
            self.last=time.monotonic();temporary=self.directory/'latest.tmp'
            try:
                write(temporary)
                if (self.directory/'enabled').exists():os.replace(temporary,self.directory/'latest.frame')
            except (OSError,ValueError,RuntimeError):pass
            finally:
                try:temporary.unlink(missing_ok=True)
                except OSError:pass

    def publish(self,image):
        self._publish(lambda path:image.save(path,format='PNG',compress_level=1))

    def publish_image(self,image):
        self.last=0;self.publish(image)

    def publish_path(self,path):
        # Preserve the actual completed file, including its full encoded quality.
        self._publish(lambda temporary:shutil.copyfile(path,temporary))


class VideoPreviewSampler:
    """Sample the current processed position only while Display is open.

    Separate one-frame reads avoid depending on an unfinished MP4's index.
    These are full-size filtered frames before final encoder compression.
    """
    def __init__(self,source,arguments,directory,ffmpeg,cancel_event):
        self.source=source;self.directory=Path(directory) if directory else None
        self.publisher=PreviewPublisher(directory);self.ffmpeg=ffmpeg;self.cancel=cancel_event
        self.position=0.;self.stop=threading.Event();self.thread=None
        chain=arguments[arguments.index('-vf')+1] if '-vf' in arguments else ''
        chain=chain.replace('scale_vaapi=w=','scale=').replace(':h=',':')
        self.filters=','.join(f for f in chain.split(',') if f!='hwupload')

    def __enter__(self):
        if self.directory:
            try:(self.directory/'preview-kind').write_text('Processed frame before encoding',encoding='utf-8')
            except OSError:pass
            self.thread=threading.Thread(target=self._work,daemon=True);self.thread.start()
        return self

    def __exit__(self,*args):
        self.stop.set()
        if self.thread:self.thread.join()

    def _work(self):
        import subprocess,io
        from process_utils import start_owned_process,stop_owned_process
        while not self.stop.is_set() and not self.cancel.is_set():
            if not self.publisher.wanted():self.stop.wait(.2);continue
            process=None
            try:
                command=[self.ffmpeg,'-v','error','-ss',str(max(0,self.position)),
                         '-i',str(self.source),'-map','0:v:0','-frames:v','1','-an','-sn']
                if self.filters:command+=['-vf',self.filters]
                command+=['-threads','1','-c:v','png','-f','image2pipe','pipe:1']
                process=start_owned_process(command,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
                deadline=time.monotonic()+15
                while True:
                    if self.stop.is_set() or self.cancel.is_set() or not (self.directory/'enabled').exists() or time.monotonic()>deadline:
                        stop_owned_process(process);break
                    try:
                        data,_=process.communicate(timeout=.15)
                        if process.returncode==0 and data:
                            with Image.open(io.BytesIO(data)) as frame:self.publisher.publish(frame)
                        break
                    except subprocess.TimeoutExpired:continue
            except (OSError,ValueError,RuntimeError):pass
            finally:
                if process:stop_owned_process(process)
            self.stop.wait(3)


class ConversionDisplay:
    def __init__(self,parent,translate):
        self.parent=parent;self.tr=translate
        self.storage=tempfile.TemporaryDirectory(prefix='rfm-display-')
        self.directory=Path(self.storage.name);self.publisher=PreviewPublisher(self.directory)
        self.window=None;self.timer=None;self.redraw=None;self.stamp=None;self.picture=None;self.photo=None;self.latest_path=None
        self.fit=True;self.fullscreen=False
        parent.bind('<Destroy>',self._destroy,add='+')

    def show(self):
        if self.window is not None and self.window.winfo_exists():self.close();return
        self.window=tk.Toplevel(self.parent);self.window.title(self.tr('Display'));self.window.transient(self.parent)
        x,y,w,h=display_geometry((self.parent.winfo_rootx(),self.parent.winfo_rooty(),self.parent.winfo_width(),self.parent.winfo_height()),monitor_area(self.parent))
        self.window.geometry(f'{w}x{h}{x:+d}{y:+d}');self.fullscreen=False
        toolbar=ttk.Frame(self.window);toolbar.pack(side='bottom',fill='x')
        sizing=ttk.Frame(toolbar);sizing.pack(fill='x')
        actions=ttk.Frame(toolbar);actions.pack(fill='x')
        ttk.Button(sizing,text=self.tr('Fit to window'),command=lambda:self.set_fit(True)).pack(side='left')
        ttk.Button(sizing,text='100%',command=lambda:self.set_fit(False)).pack(side='left',padx=4)
        self.detail=ttk.Label(sizing);self.detail.pack(side='left',padx=5)
        ttk.Button(actions,text=self.tr('Full screen')+' (F11)',command=self.toggle_fullscreen).pack(side='left')
        ttk.Button(actions,text=self.tr('Close'),command=self.close).pack(side='right')
        host=ttk.Frame(self.window);host.pack(fill='both',expand=True)
        self.canvas=tk.Canvas(host,background='#202020',highlightthickness=0)
        sy=ttk.Scrollbar(host,orient='vertical',command=self.canvas.yview);sx=ttk.Scrollbar(host,orient='horizontal',command=self.canvas.xview)
        sy.pack(side='right',fill='y');sx.pack(side='bottom',fill='x');self.canvas.pack(fill='both',expand=True)
        self.canvas.configure(yscrollcommand=sy.set,xscrollcommand=sx.set)
        self.canvas.bind('<Configure>',self._schedule_draw)
        self.canvas.bind('<Double-1>',lambda event:self.toggle_fullscreen())
        self.window.bind('<F11>',lambda event:self.toggle_fullscreen())
        self.window.bind('<Escape>',lambda event:self.toggle_fullscreen(False))
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        (self.directory/'enabled').touch()
        if self.latest_path is not None:
            self.publisher.last=0
            threading.Thread(target=self.publisher.publish_path,args=(self.latest_path,),daemon=True).start()
        self.stamp=None;self._tick();self._schedule_draw()

    def set_fit(self,value):
        self.fit=value
        self.canvas.xview_moveto(0);self.canvas.yview_moveto(0);self._draw()

    def toggle_fullscreen(self,value=None):
        self.fullscreen=not self.fullscreen if value is None else value
        self.window.attributes('-fullscreen',self.fullscreen);self._schedule_draw()

    def _schedule_draw(self,event=None):
        if self.redraw is not None:self.parent.after_cancel(self.redraw)
        self.redraw=self.parent.after(60,self._draw)

    def _draw(self):
        if self.redraw is not None:self.parent.after_cancel(self.redraw)
        self.redraw=None
        if self.window is None:return
        self.canvas.delete('all');w=max(1,self.canvas.winfo_width());h=max(1,self.canvas.winfo_height())
        if self.picture is None:
            self.canvas.create_text(w/2,h/2,text=self.tr('Loading preview…'),fill='white');return
        if self.fit:
            ratio=min(w/self.picture.width,h/self.picture.height)
            size=max(1,round(self.picture.width*ratio)),max(1,round(self.picture.height*ratio))
            with self.picture.resize(size,Image.Resampling.BILINEAR) as scaled:self.photo=ImageTk.PhotoImage(scaled,master=self.window)
            self.canvas.create_image(w/2,h/2,image=self.photo,anchor='center');self.canvas.configure(scrollregion=(0,0,w,h))
        else:
            self.photo=ImageTk.PhotoImage(self.picture,master=self.window)
            self.canvas.create_image(0,0,image=self.photo,anchor='nw');self.canvas.configure(scrollregion=(0,0,self.picture.width,self.picture.height))
        description=''
        try:description=' · '+(self.directory/'preview-kind').read_text(encoding='utf-8')
        except OSError:pass
        self.detail.configure(text=f'{self.picture.width} × {self.picture.height}'+description)

    def _tick(self):
        if self.window is None:return
        try:
            path=self.directory/'latest.frame';stamp=path.stat().st_mtime_ns
            if stamp!=self.stamp:
                with Image.open(path) as image:new=image.copy()
                if self.picture is not None:self.picture.close()
                self.picture=new;self.stamp=stamp;self._draw()
        except (OSError,ValueError):pass
        self.timer=self.parent.after(500,self._tick)

    def reset(self):
        try:
            (self.directory/'latest.frame').unlink(missing_ok=True)
            (self.directory/'preview-kind').unlink(missing_ok=True)
        except OSError:pass
        self.stamp=None
        if self.picture is not None:self.picture.close();self.picture=None
        self.photo=None
        if self.window is not None:self.canvas.delete('all');self._schedule_draw()

    def close(self):
        try:(self.directory/'enabled').unlink(missing_ok=True)
        except OSError:pass
        for name in ('timer','redraw'):
            token=getattr(self,name)
            if token is not None:self.parent.after_cancel(token);setattr(self,name,None)
        if self.window is not None:
            if self.window.winfo_exists():self.window.destroy()
            self.window=None
        self.photo=None

    def _destroy(self,event):
        if event.widget is not self.parent:return
        self.close()
        if self.picture is not None:self.picture.close();self.picture=None
        try:self.storage.cleanup()
        except OSError:pass
