"""Explicit conversion conflict choices and guarded output replacement."""
from pathlib import Path
import os,stat,uuid
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog


def identity(path):
    value=Path(path).lstat()
    if not stat.S_ISREG(value.st_mode):raise ValueError('Destination is not a regular file')
    return [value.st_dev,value.st_ino,value.st_size,value.st_mtime_ns]


def protected_target(target,sources):
    target=Path(target)
    for source in sources:
        source=Path(source)
        if target.resolve()==source.resolve():return True
        if target.exists() and source.exists() and os.path.samefile(target,source):return True
    return False


def overwrite_approval(target,sources=()):
    target=Path(target)
    if protected_target(target,sources):raise ValueError('Output is the original; add a suffix or choose another folder')
    return {'path':str(target.resolve()),'identity':identity(target)}


def validate_approval(target,approval,sources=()):
    target=Path(target)
    if protected_target(target,sources):raise ValueError('Output is the original; add a suffix or choose another folder')
    if str(target.resolve())!=approval['path']:raise ValueError('Overwrite approval does not match the output path')
    if target.exists() and identity(target)!=approval['identity']:raise ValueError('Destination changed after overwrite approval; existing file retained')


def publish_conversion_output(temporary,target,approval=None):
    from ai_pipeline import publish_output_without_replace
    temporary,target=Path(temporary),Path(target)
    if approval is None:return publish_output_without_replace(temporary,target)
    validate_approval(target,approval)
    if not target.exists():return publish_output_without_replace(temporary,target)
    backup=target.with_name('.'+target.name+'.rfm-backup-'+uuid.uuid4().hex)
    os.rename(target,backup)
    try:
        if identity(backup)!=approval['identity']:raise ValueError('Destination changed after overwrite approval')
        publish_output_without_replace(temporary,target)
    except Exception as exc:
        try:publish_output_without_replace(backup,target)
        except OSError:
            raise OSError(f'Output could not be replaced. Previous file retained at {backup}') from exc
        raise
    # Never discard a file modified through an open handle after approval.
    try:
        if identity(backup)==approval['identity']:backup.unlink();return None
    except OSError:pass
    return backup


def source_of(plan):return Path(plan['source']) if 'source' in plan else plan['item'].path


class ConversionConflicts:
    def __init__(self,parent,host,translate,refresh,tree):
        self.parent=parent;self.tr=translate;self.refresh=refresh;self.tree=tree
        self.overrides={};self.plans=[];self.conflicts=[]
        self.banner=ttk.Frame(host)
        self.label=ttk.Label(self.banner,foreground='#c26900');self.label.pack(side='left',fill='x',expand=True)
        self.button=ttk.Button(self.banner,text=self.tr('Rename')+' / '+self.tr('Replace')+' / '+self.tr('Folder'),command=self.resolve)
        self.button.pack(side='right')
        self.tree.tag_configure('filename_conflict',foreground='#c26900')

    def apply(self,plans):
        self.plans=plans;self.conflicts=[];sources=[source_of(p) for p in plans];used=set()
        eligible={'Ready','Skipped','Skip existing','Duplicate output'}
        for p in plans:
            original=Path(p['target']);key=str(source_of(p).resolve());override=self.overrides.get(key)
            if override and override['base']!=str(original):self.overrides.pop(key);override=None
            if override:p['target']=Path(override['target'])
            if override and override.get('skip'):
                p['status']='Skipped';p['conflict']=False;p['details']='Existing output retained';continue
            target=Path(p['target']);p['conflict']=False;p.pop('overwrite_approval',None)
            original_problem=p['status']=='Problem' and 'Output is the original' in p.get('details','')
            if p['status'] not in eligible and not original_problem:continue
            normalized=os.path.normcase(str(target.resolve()))
            if protected_target(target,sources):
                p['status']='Same as source';p['conflict']=True;self.conflicts.append(p);continue
            approval=override.get('approval') if override else None
            if approval:
                try:validate_approval(target,approval,sources);p['overwrite_approval']=approval
                except (OSError,ValueError):approval=None
            conflict=normalized in used or (target.exists() and approval is None)
            p['status']='Skipped' if conflict else 'Ready';p['conflict']=conflict
            if original_problem and not conflict:p['details']='Ready'
            if conflict:self.conflicts.append(p)
            used.add(normalized)
        if self.conflicts:
            first=self.conflicts[0]['target'].name
            self.label.configure(text=self.tr('File already exists')+f': {first}'+(f' (+{len(self.conflicts)-1})' if len(self.conflicts)>1 else ''))
            if not self.banner.winfo_manager():self.banner.pack(fill='x',pady=4)
        else:self.banner.pack_forget()
        return plans

    def tags(self,plan):return ('filename_conflict',) if plan.get('conflict') else ()

    def resolve(self):
        if not self.conflicts:return
        tr=self.tr;window=tk.Toplevel(self.parent);window.title(tr('File already exists'));window.transient(self.parent)
        listing=tk.Listbox(window,width=95,height=min(8,max(2,len(self.conflicts))));listing.pack(fill='both',expand=True,padx=10,pady=10)
        for p in self.conflicts:listing.insert('end',str(p['target']))
        listing.selection_set(0)
        def choose(action):
            index=listing.curselection()
            if not index:return
            plan=self.conflicts[index[0]];target=Path(plan['target']);approval=None
            try:
                if action=='rename':
                    name=simpledialog.askstring(tr('Rename'),tr('Rename file'),initialvalue=target.name,parent=window)
                    if name is None:return
                    if not name or Path(name).name!=name or any(c in '<>:"/\\|?*' or ord(c)<32 for c in name):raise ValueError('Enter a filename without folder separators.')
                    if not Path(name).suffix:name+=target.suffix
                    if Path(name).suffix.lower()!=target.suffix.lower():raise ValueError('Keep the output filename extension')
                    target=target.with_name(name)
                elif action=='folder':
                    from conversion_ui import choose_conversion_folder
                    folder=choose_conversion_folder(window,str(target.parent))
                    if not folder:return
                    target=Path(folder)/target.name
                elif action=='skip':
                    pass
                else:
                    if not target.exists():raise ValueError('Destination now exists. Choose another name.')
                    if not messagebox.askyesno(tr('Replace'),tr('Replace {field0}?').format(field0=str(target)),parent=window,default=messagebox.NO):return
                    approval=overwrite_approval(target,[source_of(p) for p in self.plans])
                if action!='skip' and protected_target(target,[source_of(p) for p in self.plans]):raise ValueError('Output is the original; add a suffix or choose another folder')
                if action not in ('overwrite','skip') and target.exists():raise ValueError('File already exists')
                key=str(source_of(plan).resolve());previous=self.overrides.get(key)
                base=previous['base'] if previous else str(plan['target'])
                self.overrides[key]={'base':base,'target':str(target),'approval':approval,'skip':action=='skip'}
                window.destroy();self.refresh()
                if self.conflicts:self.parent.after_idle(self.resolve)
            except (OSError,ValueError) as exc:messagebox.showerror(tr('File already exists'),tr(str(exc)),parent=window)
        buttons=ttk.Frame(window);buttons.pack(fill='x',padx=10,pady=8)
        for label,action in [('Rename','rename'),('Replace','overwrite'),('Folder','folder'),('Skip','skip')]:ttk.Button(buttons,text=tr(label),command=lambda a=action:choose(a)).pack(side='left',padx=4)
        ttk.Button(buttons,text=tr('Close'),command=window.destroy).pack(side='right')
        window.grab_set()
