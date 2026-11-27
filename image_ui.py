"""Localized still-image conversion dialog; processing choices retain stable IDs."""
import os,tempfile,threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk,messagebox
from ai_backends import asset_directory,probe_hardware
from ai_pipeline import estimate_ai_disk_bytes
from conversion_conflicts import ConversionConflicts
from conversion_display import ConversionDisplay
from conversion_ui import choose_conversion_folder,bind_conversion_scrolling,grow_conversion_options_once,source_folder_choice,conversion_items,ConversionPaths,remember_conversion_choice
from conversion_jobs import close_conversion_window
from image_pipeline import IMAGE_MODES,RESIZE_CHOICES,FORMATS,EFFECTS,inspect_image,target_dimensions,convert_image_file,ImageEnhancementBatch

INPUTS={'.jpg','.jpeg','.png','.webp','.bmp','.tif','.tiff','.gif'}

class ImageChoices:
    """Translate display labels while keeping processing choices stable."""
    def __init__(self, translate, values):
        self.mapping = {value: translate(value) for value in values}
        self.reverse = {label: value for value, label in self.mapping.items()}
    @property
    def labels(self): return tuple(self.mapping.values())
    def label(self, value): return self.mapping.get(value, value)
    def internal(self, value): return self.reverse.get(value, value)

class ImageChoiceVar(tk.StringVar):
    def __init__(self, translate, values, value, master=None):
        self.translate = translate
        self.choices = ImageChoices(translate, values)
        super().__init__(master=master, value=self.choices.label(value))
    def get(self): return self.choices.internal(super().get())
    def set(self, value): super().set(self.choices.label(value))
    def update_choices(self, values):
        selected = self.get()
        self.choices = ImageChoices(self.translate, values)
        self.set(selected)

def show_image_conversion(app):
    tr=app.translator.ui_text
    pane=app.current_pane();items=conversion_items(app,pane,INPUTS)
    if items is None:return
    if not items:messagebox.showinfo('Convert / enhance images','Select one or more still images first.',parent=app);return
    window=tk.Toplevel(app);window.title(tr('Convert / enhance images'))
    width=min(app.winfo_screenwidth()-40,int(1100*app.ui_scale/100));height=min(app.winfo_screenheight()-80,int((900 if os.name!='nt' else 800)*app.ui_scale/100));window.geometry(f'{width}x{height}')
    display=ConversionDisplay(window,tr)
    output=tk.StringVar(value=str(items[0].path.parent));working=tk.StringVar(value=tempfile.gettempdir())
    format=tk.StringVar(value='JPEG');resize=ImageChoiceVar(tr,RESIZE_CHOICES,'Original size');custom=tk.IntVar(value=1920);quality=tk.IntVar(value=92)
    method=ImageChoiceVar(tr,tuple(IMAGE_MODES),'Ordinary resizing');hardware=ImageChoiceVar(tr,('Automatic',),'Automatic');prefix=tk.StringVar();suffix=tk.StringVar(value=' - converted')
    same_source=source_folder_choice(app,'image');preserve=tk.BooleanVar(value=False);collision=ImageChoiceVar(tr,('Skip existing','Keep both'),'Skip existing');strength=ImageChoiceVar(tr,('Light','Medium','Strong'),'Medium')
    effects={name:tk.BooleanVar(value=False) for name in EFFECTS};notice=tk.StringVar();hardware_status=tk.StringVar(value=tr('AI Photo can restore/enhance details at Original size or resize to a larger image.'))
    remember_conversion_choice(app, 'image_enhancement', method, tuple(IMAGE_MODES))
    remember_conversion_choice(app, 'image_effect_strength', strength, ('Light','Medium','Strong'))
    for name, variable in effects.items():
        remember_conversion_choice(app, 'image_effect_' + name, variable, (True, False))
    state={'running':False,'loaded':False,'info':{},'plans':[],'devices':[],'hardware_busy':False,'hardware_checked':False,'job':None};cancel=threading.Event()
    host=ttk.Frame(window);host.pack(fill='x',padx=10,pady=8)
    canvas=tk.Canvas(host,highlightthickness=0,height=400);sy=ttk.Scrollbar(host,orient='vertical',command=canvas.yview);sx=ttk.Scrollbar(host,orient='horizontal',command=canvas.xview)
    sy.pack(side='right',fill='y');sx.pack(side='bottom',fill='x');canvas.pack(fill='both',expand=True);canvas.configure(yscrollcommand=sy.set,xscrollcommand=sx.set)
    form=ttk.LabelFrame(canvas,text=tr('Image conversion settings'),padding=10);form_id=canvas.create_window(0,0,window=form,anchor='nw');form.columnconfigure(1,weight=1)
    def combo(label,var,values,row,column=0,width=27):
        ttk.Label(form,text=tr(label)).grid(row=row,column=column,sticky='w',padx=4,pady=5)
        box=ttk.Combobox(form,textvariable=var,values=var.choices.labels if isinstance(var,ImageChoiceVar) else values,state='readonly',width=width);box.grid(row=row,column=column+1,sticky='ew',padx=4,pady=5);return box
    combo('Output format',format,tuple(FORMATS),0);combo('Output size',resize,RESIZE_CHOICES,0,2,25)
    ttk.Label(form,text=tr('JPEG / WebP quality')).grid(row=1,column=0,sticky='w',padx=4)
    ttk.Spinbox(form,from_=1,to=100,textvariable=quality,width=7).grid(row=1,column=1,sticky='w',padx=4)
    ttk.Label(form,text=tr('Custom long edge (pixels)')).grid(row=1,column=2,sticky='w',padx=4)
    custom_box=ttk.Spinbox(form,from_=1,to=32768,textvariable=custom,width=9);custom_box.grid(row=1,column=3,sticky='w',padx=4)
    combo('Enhancement method',method,tuple(IMAGE_MODES),2,width=32);hardware_box=combo('AI processing hardware',hardware,('Automatic',),2,2,25)
    ttk.Label(form,textvariable=hardware_status,wraplength=max(600,width-60)).grid(row=3,column=0,columnspan=4,sticky='w',padx=4,pady=4)
    effect_frame=ttk.Frame(form);effect_frame.grid(row=4,column=0,columnspan=4,sticky='ew',pady=5)
    ttk.Label(effect_frame,text=tr('Standard effects:')).pack(side='left')
    for name,var in effects.items():ttk.Checkbutton(effect_frame,text=tr(name),variable=var).pack(side='left',padx=3)
    combo('Effect strength',strength,('Light','Medium','Strong'),5)
    ttk.Label(form,text=tr('Aspect ratio is preserved. JPEG uses a white background for transparency.')).grid(row=5,column=2,columnspan=2,sticky='w',padx=4)
    def path_row(text,var,row,browse_label):
        ttk.Label(form,text=tr(text)).grid(row=row,column=0,sticky='w',padx=4,pady=5)
        entry=ttk.Entry(form,textvariable=var);entry.grid(row=row,column=1,columnspan=2,sticky='ew',padx=4,pady=5)
        browse=ttk.Button(form,text=tr(browse_label),command=lambda:var.set(choose_conversion_folder(window,var.get() or tempfile.gettempdir()) or var.get()));browse.grid(row=row,column=3,sticky='w',padx=4);return entry,browse
    output_entry,output_button=path_row('Output folder',output,6,'Browse output…')
    for label in form.grid_slaves(row=6,column=0):label.destroy()
    output_label=ttk.Frame(form);output_label.grid(row=6,column=0,sticky='w',padx=4)
    ttk.Label(output_label,text=tr('Output folder')).pack(anchor='w')
    ttk.Checkbutton(output_label,text=tr('Same as source'),variable=same_source).pack(anchor='w')
    work_entry,work_button=path_row('AI working folder',working,7,'Browse working folder…')
    ttk.Label(form,text=tr('Filename prefix')).grid(row=8,column=0,sticky='w',padx=4);ttk.Entry(form,textvariable=prefix).grid(row=8,column=1,sticky='ew',padx=4)
    ttk.Label(form,text=tr('Filename suffix')).grid(row=8,column=2,sticky='w',padx=4);ttk.Entry(form,textvariable=suffix,width=25).grid(row=8,column=3,sticky='ew',padx=4)
    preserve_button=ttk.Checkbutton(form,text=tr('Preserve folders relative to active pane'),variable=preserve);preserve_button.grid(row=9,column=0,columnspan=3,sticky='w',padx=4,pady=5)
    ttk.Combobox(form,textvariable=collision,values=collision.choices.labels,state='readonly',width=20).grid(row=9,column=3,sticky='w',padx=4)
    note=ttk.Label(window,textvariable=notice,wraplength=width-25,padding=(10,2));note.pack(fill='x')
    footer=ttk.Frame(window,padding=10);footer.pack(side='bottom',fill='x');current=tk.StringVar(value=tr('Original images are retained. Review output names before starting.'))
    ttk.Label(footer,textvariable=current).pack(fill='x');file_bar=ttk.Progressbar(footer,mode='indeterminate');file_bar.pack(fill='x',pady=3)
    total_bar=ttk.Progressbar(footer,maximum=100);total_bar.pack(fill='x',pady=3);buttons=ttk.Frame(footer);buttons.pack(fill='x',pady=(5,0))
    table=ttk.Frame(window);table.pack(fill='both',expand=True,padx=10,pady=5)
    tree=ttk.Treeview(table,columns=('status','source','output','details'),show='headings',height=3)
    for key,label,w in (('status','Status',95),('source','Source',290),('output','Output',330),('details','Size / result',330)):
        tree.heading(key,text=tr(label));tree.column(key,width=w,stretch=False)
    path_labels=ConversionPaths(tree,footer,'output',tr)
    output_summary=tk.StringVar(master=window)
    ttk.Label(footer,textvariable=output_summary,wraplength=width-30).pack(fill='x')
    sy_table=ttk.Scrollbar(table,command=tree.yview);sx_table=ttk.Scrollbar(table,orient='horizontal',command=tree.xview);tree.configure(yscrollcommand=sy_table.set,xscrollcommand=sx_table.set)
    sy_table.pack(side='right',fill='y');sx_table.pack(side='bottom',fill='x');tree.pack(fill='both',expand=True)
    def fit(event=None):
        canvas.itemconfigure(form_id,width=max(canvas.winfo_width(),form.winfo_reqwidth()));canvas.configure(scrollregion=canvas.bbox('all'))
        reserved=footer.winfo_reqheight()+note.winfo_reqheight()+tree.winfo_reqheight()+60
        grow_conversion_options_once(window,form,reserved)
        available=max(140,window.winfo_height()-reserved)
        desired=min(form.winfo_reqheight(),available)
        if int(canvas.cget('height'))!=desired:canvas.configure(height=desired)
        note.configure(wraplength=max(200,window.winfo_width()-25))
    form.bind('<Configure>',fit);canvas.bind('<Configure>',fit);window.bind('<Configure>',lambda event:fit() if event.widget is window else None)
    def update_controls():
        for control in (output_entry,output_button,preserve_button):control.configure(state='disabled' if same_source.get() or state['running'] else 'normal')
        ai=IMAGE_MODES[method.get()]!='ordinary'
        for widget in (work_entry,work_button):widget.configure(state='normal' if ai and not state['running'] else 'disabled')
        hardware_box.configure(state='readonly' if ai and state['devices'] and not state['running'] else 'disabled')
        custom_box.configure(state='normal' if resize.get()=='Custom long edge' else 'disabled')
        notice.set(tr('WARNING: AI restoration can change fine details, takes time and uses significant drive space. Review a sample before a batch. Temporary job folders use the AI working drive; finished files use the output folder.' if ai else 'Standard effects do not use AI. Originals are retained. Animated and multi-page files are excluded.'))
        if ai and not state['hardware_checked'] and not state['hardware_busy']:
            state['hardware_busy']=True;hardware_status.set(tr('Checking actual AI CPU / GPU support…'))
            def discover():
                try:devices=[d for d in probe_hardware(asset_directory()) if d.usable];error=''
                except Exception as exc:devices=[];error=str(exc)
                def complete():
                    if not window.winfo_exists():return
                    state.update(devices=devices,hardware_busy=False,hardware_checked=True)
                    hardware.update_choices(('Automatic',*(d.label for d in devices)))
                    hardware_box.configure(values=hardware.choices.labels)
                    hardware_status.set(tr('AI: {hardware}').format(hardware=', '.join(tr(d.label) if d.label=='CPU (slower)' else d.label for d in devices)) if devices else tr('AI unavailable: {error}').format(error=tr(error)));refresh()
                app.post_ui(complete)
            threading.Thread(target=discover,daemon=True).start()
    def refresh(*args):
        if state['running']:return
        update_controls();tree.delete(*tree.get_children());plans=[];used=set()
        for index,item in enumerate(items):
            target=(item.path.parent if same_source.get() else Path(output.get()).expanduser())/(prefix.get()+item.path.stem+suffix.get()+FORMATS[format.get()]);status='Ready';details='Checking image…';info=state['info'].get(item.path)
            try:
                if not state['loaded']:status='Checking'
                elif isinstance(info,str):raise ValueError(info)
                else:
                    size=target_dimensions(info['width'],info['height'],resize.get(),custom.get() if resize.get()=='Custom long edge' else 1920);details=f"{info['width']}×{info['height']} → {size[0]}×{size[1]}"
                if any(c in '<>:"/\\|?*' or ord(c)<32 for c in prefix.get()+suffix.get()):raise ValueError('Invalid filename prefix or suffix')
                if preserve.get() and not same_source.get():
                    relative=item.path.parent.relative_to(pane.current_path);target=target.parent/relative/target.name
                if target.resolve()==item.path.resolve():raise ValueError('Output is the original; add a suffix or choose another folder')
                if target in used or target.exists():
                    if collision.get()=='Skip existing':status='Skipped';details='Existing output retained'
                    else:
                        original=target;number=2
                        while target in used or target.exists():target=original.with_name(f'{original.stem} ({number}){original.suffix}');number+=1
                used.add(target)
            except (OSError,ValueError,tk.TclError) as exc:status='Problem';details=str(exc)
            plan={'source':item.path,'target':target,'status':status,'details':details,'info':info};plans.append(plan)
        plans=conflicts.apply(plans)
        for index,plan in enumerate(plans):
            tree.insert('', 'end',iid=str(index),values=(tr(plan['status']),str(plan['source']),str(plan['target']),tr(plan['details'])),tags=conflicts.tags(plan))
            path_labels.set(str(index),plan['source'],plan['target'])
        state['plans']=plans
        destination=tr('Beside each original') if same_source.get() else output.get()
        try: quality_text=quality.get()
        except tk.TclError: quality_text='?'
        output_summary.set(tr('{count} images → {format} · {resize} · quality {quality} · {destination}').format(count=sum(p['status']=='Ready' for p in plans),format=format.get(),resize=tr(resize.get()),quality=quality_text if format.get()!='PNG' else tr('Not used'),destination=destination)
                           +' · '+tr(method.get())+(' · '+', '.join(tr(name) for name,var in effects.items() if var.get())+' ('+tr(strength.get())+')' if any(var.get() for var in effects.values()) else ''))
        ready=any(p['status']=='Ready' for p in plans) or bool(conflicts.conflicts);ai=IMAGE_MODES[method.get()]!='ordinary'
        start_button.configure(state='normal' if ready and (not ai or state['devices']) and not state['hardware_busy'] else 'disabled')
    def start():
        if getattr(window, "_conversion_close_pending", False):return
        refresh()
        if conflicts.conflicts:
            conflicts.resolve();return
        plans=[p for p in state['plans'] if p['status']=='Ready']
        if not plans:return
        ai_mode=IMAGE_MODES[method.get()];work=None
        try:
            edge=custom.get() if resize.get()=='Custom long edge' else 1920;q=quality.get() if format.get()!='PNG' else 92;weight=('Light','Medium','Strong').index(strength.get())+1
            if not 1<=q<=100:raise ValueError('Quality must be between 1 and 100')
            warning=tr('Originals will be retained. JPEG flattens transparency onto white. Existing outputs will not be replaced.')
            if ai_mode!='ordinary':
                work=Path(working.get().strip() or tempfile.gettempdir()).expanduser().resolve()
                if not work.is_dir():raise ValueError('Choose an existing AI working folder')
                required=max(estimate_ai_disk_bytes(p['info']['width'],p['info']['height'],1,ai_mode) for p in plans)
                import shutil
                if shutil.disk_usage(work).free<required:raise ValueError('Not enough AI working drive space')
                with tempfile.TemporaryFile(dir=work):pass
                warning+=tr('\n\nAI restoration/enlargement may change fine details and can be slow. Approximate temporary space: {space} MB, one image at a time. Working folder: {working}. Finished files: {output}. Temporary job folders are cleaned after success, cancellation or failure.').format(space=f'{required/1048576:,.0f}',working=work,output=tr('Same as source') if same_source.get() else output.get())
        except (OSError,ValueError,tk.TclError) as exc:messagebox.showerror('Cannot start image conversion',str(exc),parent=window);return
        if not messagebox.askyesno('Start image conversion?',tr('Convert {count} image(s)?').format(count=len(plans))+'\n\n'+output_summary.get()+'\n\n'+warning,parent=window):return
        options={'format':format.get(),'resize':resize.get(),'quality':q,'custom_edge':edge,'ai_mode':ai_mode,'ai_hardware':'auto' if hardware.get()=='Automatic' else next((d.id for d in state['devices'] if d.label==hardware.get()),'cpu'),'working_folder':work,'effects':tuple(name for name,var in effects.items() if var.get()),'effect_strength':weight}
        conflicts.button.configure(state='disabled')
        state['running']=True;cancel.clear();start_button.configure(state='disabled');cancel_button.configure(state='normal');file_bar.start();total_bar.configure(value=0)
        control_states=[]
        def lock(widget):
            for child in widget.winfo_children():
                if isinstance(child,(ttk.Entry,ttk.Combobox,ttk.Spinbox,ttk.Button,ttk.Checkbutton)):
                    control_states.append((child,child.cget('state')));child.configure(state='disabled')
                lock(child)
        lock(form)
        def update_stage(index,text):
            if not window.winfo_exists():return
            iid=str(state['plans'].index(plans[index]));tree.set(iid,'status',tr(text));current.set(plans[index]['source'].name+' · '+tr(text))
        def worker():
            results=[]
            with ImageEnhancementBatch() as batch:
                for index,plan in enumerate(plans):
                    if cancel.is_set():break
                    result,details=convert_image_file(plan['source'],plan['target'],cancel_event=cancel,on_stage=lambda text,i=index:app.post_ui(update_stage,i,text),enhancement_batch=batch,on_preview=display.publisher.publish_path,overwrite=plan.get('overwrite_approval'),**options);results.append(result)
                    def show_result(index=index,plan=plan,result=result,details=details):
                        if not window.winfo_exists():return
                        if result=='Passed':display.latest_path=plan['target']
                        iid=str(state['plans'].index(plan));tree.set(iid,'status',tr(result));tree.set(iid,'details',tr(details));plan['details']=details;total_bar.configure(value=100*(index+1)/len(plans))
                    app.post_ui(show_result)
                    if result=='Cancelled':break
            def finished():
                if not window.winfo_exists():return
                conflicts.button.configure(state='normal')
                state['running']=False;file_bar.stop();file_bar.configure(value=0);cancel_button.configure(state='disabled');start_button.configure(state='normal')
                for control,previous in control_states:control.configure(state=previous)
                current.set(tr('Completed: {passed} · Failed: {failed} · {status}').format(passed=results.count('Passed'),failed=results.count('Failed'),status=tr('Cancelled' if cancel.is_set() else 'Ready')))
                pane.refresh_browser()
            app.post_ui(finished)
        state['job']=app.conversion_jobs.start(worker,cancel,'image conversion')
    bind_conversion_scrolling(canvas,form,sx,sy)
    conflicts=ConversionConflicts(window,footer,tr,refresh,tree)
    display_button=ttk.Button(buttons,text=tr('Display'),command=display.show);display_button.pack(side='left')
    start_button=ttk.Button(buttons,text=tr('Start image conversion…'),command=start);start_button.pack(side='left',padx=5)
    cancel_button=ttk.Button(buttons,text=tr('Cancel conversion'),command=cancel.set,state='disabled');cancel_button.pack(side='left')
    def close():
        close_conversion_window(window,state['job'],cancel,lambda:messagebox.askyesno('Cancel conversion?', 'A conversion is running. Cancel it and close this window after temporary files have been cleaned?',parent=window,default=messagebox.NO))
    ttk.Button(buttons,text=tr('Minimise'),command=window.iconify).pack(side='right')
    ttk.Button(buttons,text=tr('Close'),command=close).pack(side='right');window.protocol('WM_DELETE_WINDOW',close)
    def details(event=None):
        selected=tree.selection()
        if selected:messagebox.showinfo('Image conversion details',state['plans'][int(selected[0])]['details'],parent=window)
    tree.bind('<Double-1>',details)
    for var in (output,same_source,working,format,resize,custom,quality,method,hardware,prefix,suffix,preserve,collision,strength,*effects.values()):var.trace_add('write',refresh)
    refresh()
    def inspect():
        info={}
        for item in items:
            try:info[item.path]=inspect_image(item.path)
            except Exception as exc:info[item.path]=str(exc)
        def complete():
            if window.winfo_exists():state.update(loaded=True,info=info);refresh()
        app.post_ui(complete)
    threading.Thread(target=inspect,daemon=True).start();window.after_idle(fit)
