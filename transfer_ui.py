"""English-review controls for file transfers and temporary selections."""
import os
from pathlib import Path
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from transfer_engine import plan_targets, path_key, available_target, validate_folder_name


def open_folder(path):
    if sys.platform=='win32': os.startfile(str(path))
    else: subprocess.Popen(['open' if sys.platform=='darwin' else 'xdg-open',str(path)])


def create_folder(parent, destination):
    name=simpledialog.askstring('New folder','Folder name:',parent=parent)
    if name is None: return None
    try:
        target=Path(destination)/validate_folder_name(name)
        target.mkdir()
        return target
    except (OSError,ValueError) as error:
        messagebox.showerror('Could not create folder',str(error),parent=parent)
        return None


class UpgradeAppMixin:
    def preview_transfer(self, paths, source_root, destination, move=False):
        paths=list(dict.fromkeys(Path(p) for p in paths))
        if not paths:
            messagebox.showinfo('Nothing selected','Select or tick files first.',parent=self); return
        window=tk.Toplevel(self); window.title('Move files' if move else 'Copy files'); window.geometry('1000x620'); window.transient(self)
        preserve=tk.BooleanVar(value=bool(self.settings.get('transfer_preserve_folders',True)))
        open_after=tk.BooleanVar(value=bool(self.settings.get('transfer_open_destination',False)))
        policy_labels={value:self.translator.ui_text(value) for value in ('Ask for each conflict','Keep both','Replace','Skip')}
        destination_var=tk.StringVar(value=str(destination)); conflict=tk.StringVar(value=policy_labels['Ask for each conflict'])
        settings=ttk.Frame(window,padding=10); settings.pack(fill='x')
        ttk.Label(settings,text='Destination folder:').grid(row=0,column=0,sticky='w')
        ttk.Entry(settings,textvariable=destination_var).grid(row=0,column=1,sticky='ew',padx=6)
        def browse():
            value=filedialog.askdirectory(parent=window,initialdir=destination_var.get())
            if value: destination_var.set(value)
        ttk.Button(settings,text='Browse…',command=browse).grid(row=0,column=2)
        def new_folder():
            target=create_folder(window,destination_var.get())
            if target: destination_var.set(str(target))
        ttk.Button(settings,text='New folder…',command=new_folder).grid(row=0,column=3,padx=6)
        ttk.Radiobutton(settings,text='Preserve folder structure',variable=preserve,value=True).grid(row=1,column=1,sticky='w',pady=6)
        ttk.Radiobutton(settings,text='Files only (no subfolders)',variable=preserve,value=False).grid(row=2,column=1,sticky='w')
        ttk.Label(settings,text='If a destination filename already exists:').grid(row=3,column=0,sticky='w',pady=6)
        ttk.Combobox(settings,textvariable=conflict,state='readonly',values=tuple(policy_labels.values()),width=max(26,min(50,max(map(len,policy_labels.values()))+2))).grid(row=3,column=1,sticky='w')
        ttk.Checkbutton(settings,text='Open destination when complete',variable=open_after).grid(row=4,column=1,sticky='w')
        settings.columnconfigure(1,weight=1)
        frame=ttk.Frame(window); frame.pack(fill='both',expand=True,padx=10)
        tree=ttk.Treeview(frame,columns=('source','destination','status'),show='headings')
        for key,width in (('source',390),('destination',390),('status',180)):
            tree.heading(key,text=key.title()); tree.column(key,width=width,stretch=True)
        scroll=ttk.Scrollbar(frame,command=tree.yview); scroll.pack(side='right',fill='y'); tree.configure(yscrollcommand=scroll.set); tree.pack(fill='both',expand=True)
        horizontal=ttk.Scrollbar(window,orient='horizontal',command=tree.xview); horizontal.pack(fill='x',padx=10); tree.configure(xscrollcommand=horizontal.set)
        note=tk.StringVar(); note_label=ttk.Label(window,textvariable=note,padding=10,wraplength=960)
        note_label.pack(fill='x')
        window.bind('<Configure>',lambda event:note_label.configure(wraplength=max(200,window.winfo_width()-40)) if event.widget is window else None,add='+')
        state={'pairs':[],'errors':False}; refresh_job=[None]
        def refresh():
            refresh_job[0]=None; pairs=plan_targets(paths,source_root,Path(destination_var.get()),preserve.get())
            tree.delete(*tree.get_children()); seen=set(); sources={path_key(p) for p in paths}; errors=False
            for source,target in pairs:
                key=path_key(target); status='Ready'
                if not source.is_file(): status='Source missing'; errors=True
                elif key in sources: status='Destination is a selected source'; errors=True
                elif target.is_dir(): status='Destination is a folder'; errors=True
                elif key in seen: status='Duplicate destination name'
                elif target.exists(): status='Existing destination'
                seen.add(key); tree.insert('', 'end', values=(str(source),str(target),self.translator.ui_text(status)))
            state.update(pairs=pairs,errors=errors)
            note.set(self.translator.ui_text(f'{len(pairs)} files. Conflicts are reviewed before queuing. Replace keeps an undo backup for this session.'))
            start.configure(state='disabled' if errors or not Path(destination_var.get()).is_dir() else 'normal')
        def schedule(*_):
            if refresh_job[0]: window.after_cancel(refresh_job[0])
            refresh_job[0]=window.after(120,refresh)
        def submit():
            refresh()
            if state['errors'] or not Path(destination_var.get()).is_dir(): return
            selected=next((value for value,label in policy_labels.items() if label==conflict.get()),'Ask for each conflict')
            policy={'Keep both':'keep both','Replace':'replace','Skip':'skip'}.get(selected,'ask')
            planned=self.resolve_transfer_conflicts(state['pairs'],policy,window)
            if planned is None: return
            self.settings['transfer_preserve_folders']=preserve.get(); self.settings['transfer_open_destination']=open_after.get()
            self.save_local_preferences()
            destination=Path(destination_var.get()); window.destroy()
            if planned:
                label=('Move' if move else 'Copy')+f' to {destination}'
                if self.language!='en': label=self.tr('choice.move' if move else 'choice.copy')+' → '+str(destination)
                self.enqueue_operation([(s,t) for s,t,p in planned],move,label,policies=[p for s,t,p in planned],open_destination=destination if open_after.get() else None)
        buttons=ttk.Frame(window,padding=10); buttons.pack(fill='x')
        start=ttk.Button(buttons,text='Queue move' if move else 'Queue copy',command=submit); start.pack(side='left')
        ttk.Button(buttons,text='Cancel',command=window.destroy).pack(side='right')
        preserve.trace_add('write',schedule); destination_var.trace_add('write',schedule)
        refresh(); window.grab_set(); self.wait_window(window)

    def resolve_transfer_conflicts(self,pairs,policy='ask',parent=None):
        reserved=set(); result=[]; sources={path_key(s) for s,t in pairs}; apply_policy=None
        for source,target in pairs:
            key=path_key(target)
            if key in sources:
                messagebox.showerror('Unsafe destination','A destination is one of the selected source files. Choose another folder.',parent=parent or self); return None
            collision=target.exists() or key in reserved
            choice=apply_policy or policy
            if collision and choice=='ask':
                choice,all_conflicts=self.ask_transfer_conflict(source,target,parent or self)
                if choice is None: return None
                if all_conflicts: apply_policy=choice
            if collision:
                if choice=='skip': continue
                if choice=='keep both': target=available_target(target,reserved)
            reserved.add(path_key(target)); result.append((source,target,choice if collision else 'skip'))
        return result

    def ask_transfer_conflict(self,source,target,parent):
        window=tk.Toplevel(parent); window.title('Filename conflict'); window.transient(parent)
        ttk.Label(window,text=f'Source: {source}\n\nDestination: {target}\n\nKeep both creates a numbered filename. Replace backs up the destination for session Undo.',wraplength=650,padding=15).pack(fill='x')
        apply_all=tk.BooleanVar(value=False); ttk.Checkbutton(window,text='Apply to all remaining conflicts',variable=apply_all).pack(anchor='w',padx=15)
        result=[None,False]
        def choose(value): result[:]=[value,apply_all.get()]; window.destroy()
        buttons=ttk.Frame(window,padding=15); buttons.pack(fill='x')
        for label,value in (('Keep both','keep both'),('Replace','replace'),('Skip','skip'),('Cancel',None)):
            ttk.Button(buttons,text=label,command=lambda v=value:choose(v)).pack(side='left',padx=4)
        window.grab_set(); self.wait_window(window)
        return result

    def show_selection_basket(self):
        if not hasattr(self,'selection_basket'): self.selection_basket={}
        if getattr(self,'basket_panel',None) and self.basket_panel.winfo_exists():
            self.basket_panel.pack(before=self.workspace_panes,fill='x',padx=10,pady=(0,5)); self.refresh_selection_basket(); return
        window=ttk.LabelFrame(self,text='Selection basket — temporary references',padding=5); self.basket_panel=window
        window.pack(before=self.workspace_panes,fill='x',padx=10,pady=(0,5))
        table=ttk.Frame(window); table.pack(fill='x')
        self.basket_tree=ttk.Treeview(table,columns=('name','path'),show='headings',selectmode='extended',height=4)
        self.basket_tree.heading('name',text='Filename'); self.basket_tree.heading('path',text='Original location'); self.basket_tree.column('path',width=570)
        scroll=ttk.Scrollbar(table,command=self.basket_tree.yview); scroll.pack(side='right',fill='y'); self.basket_tree.configure(yscrollcommand=scroll.set)
        self.basket_tree.pack(fill='both',expand=True)
        buttons=ttk.Frame(window,padding=10); buttons.pack(fill='x')
        def remove():
            for iid in self.basket_tree.selection(): self.selection_basket.pop(iid,None)
            self.refresh_selection_basket()
        def transfer(move):
            selected=self.basket_tree.selection() or self.basket_tree.get_children()
            paths=[self.selection_basket[key] for key in selected if key in self.selection_basket]
            self.preview_transfer(paths,Path('__basket_no_common_root__'),self.current_pane().current_path,move)
            self.refresh_selection_basket()
        for label,command in (('Add pane selection',lambda:self.add_to_selection_basket(self.current_pane())),('Remove references',remove),('Clear basket',lambda:(self.selection_basket.clear(),self.refresh_selection_basket())),('Copy to active pane',lambda:transfer(False)),('Move to active pane',lambda:transfer(True))):
            ttk.Button(buttons,text=label,command=command).pack(side='left',padx=3)
        ttk.Button(buttons,text='Hide basket',command=self.hide_selection_basket).pack(side='right')
        self.refresh_selection_basket()

    def hide_selection_basket(self):
        if getattr(self,'basket_panel',None): self.basket_panel.pack_forget()

    def toggle_selection_basket(self):
        if getattr(self,'basket_panel',None) and self.basket_panel.winfo_ismapped(): self.hide_selection_basket()
        else: self.show_selection_basket()

    def add_to_selection_basket(self,pane):
        if not hasattr(self,'selection_basket'): self.selection_basket={}
        for item in pane.selected_items(): self.selection_basket[path_key(item.path)]=item.path
        self.show_selection_basket()

    def refresh_selection_basket(self):
        if not getattr(self,'basket_panel',None) or not self.basket_panel.winfo_exists(): return
        self.basket_tree.delete(*self.basket_tree.get_children())
        for key,path in self.selection_basket.items():
            self.basket_tree.insert('', 'end',iid=key,values=(path.name,str(path)+(' '+self.translator.ui_text('[missing]') if not path.is_file() else '')))


class UpgradePaneMixin:
    def ask_drop_action(self):
        """Use actual action labels, with the old True/False/None contract."""
        copy=self.app.tr('choice.copy'); move=self.app.tr('choice.move')
        window=tk.Toplevel(self);window.title(copy+' / '+move)
        window.transient(self.winfo_toplevel());window.resizable(False,False)
        ttk.Label(window,text=copy+' / '+move,padding=16,anchor='center').pack(fill='x')
        buttons=ttk.Frame(window,padding=(16,0,16,16));buttons.pack(fill='x')
        result=[None]
        def choose(value):result[0]=value;window.destroy()
        side='right' if self.app.is_rtl else 'left'
        for label,value in ((copy,True),(move,False),(self.app.tr('common.cancel'),None)):
            button=ttk.Button(buttons,text=label,command=lambda v=value:choose(v))
            button.pack(side=side,padx=4)
            if value is None: cancel=button
        window.protocol('WM_DELETE_WINDOW',lambda:choose(None))
        window.bind('<Escape>',lambda _event:choose(None))
        window.bind('<Return>',lambda _event:window.focus_get().invoke() if isinstance(window.focus_get(),ttk.Button) else choose(None))
        window.grab_set();cancel.focus_set();self.wait_window(window)
        return result[0]

    def checkbox_hit(self,event):
        widget=event.widget
        if widget is self.tree:
            row=widget.identify_row(event.y)
            if not row or widget.identify_column(event.x)!='#0': return False
            box=widget.bbox(row,'#0')
            if not box: return False
            x,y,width,height=box; cy=y+height//2
            text_pixels=[px for px in range(max(0,x),min(widget.winfo_width(),x+width)) if widget.identify_element(px,cy).endswith('text')]
            if not text_pixels: return False
            import tkinter.font as tkfont
            font=tkfont.Font(root=widget,font=ttk.Style(widget).lookup('Treeview','font') or 'TkDefaultFont')
            glyph_width=min(len(text_pixels),max(8,font.measure(widget.item(row,'text') or '☐')))
            anchor=str(widget.column('#0','anchor'))
            left=text_pixels[0]+(max(0,(len(text_pixels)-glyph_width)//2) if anchor=='center' else max(0,len(text_pixels)-glyph_width) if anchor in {'e','ne','se'} else 0)
            side=min(glyph_width,max(8,height-4))
            return left<=event.x<left+glyph_width and abs(event.y-cy)<=side/2
        side=max(4,min(widget.winfo_width()-2,widget.winfo_height()-6))
        return abs(event.x-widget.winfo_width()/2)<=side/2 and abs(event.y-widget.winfo_height()/2)<=side/2

    def checkbox_pressed(self,event,key):
        self.active_callback(self)
        self.checkbox_pending=None
        if not self.checkbox_hit(event): return self.rubber_start(event)
        self.checkbox_pending=(key,event.widget,event.x_root,event.y_root,event.state)
        self.route_pointer_gesture(f'RFMCheck{self.winfo_id()}',self.checkbox_motion,self.checkbox_released)
        return 'break'

    def checkbox_motion(self,event):
        pending=getattr(self,'checkbox_pending',None)
        if not pending: return
        key,widget,x,y,state=pending
        if max(abs(event.x_root-x),abs(event.y_root-y))>4:
            self.checkbox_pending=None
            from types import SimpleNamespace
            self.rubber_start(SimpleNamespace(widget=widget,x_root=x,y_root=y,state=state))
            self.rubber_motion(event)
        return 'break'

    def checkbox_released(self,event):
        pending=getattr(self,'checkbox_pending',None)
        if not pending: return
        self.checkbox_pending=None
        key,widget,x,y,_state=pending
        if event.widget is widget and max(abs(event.x_root-x),abs(event.y_root-y))<=4 and self.checkbox_hit(event): self.toggle_check(key)
        return 'break'

    def route_pointer_gesture(self,tag,motion,release):
        self.bind_class(tag,'<B1-Motion>',motion)
        self.bind_class(tag,'<ButtonRelease-1>',release)
        def attach(parent):
            tags=parent.bindtags()
            if tag not in tags: parent.bindtags((tag,*tags))
            for child in parent.winfo_children(): attach(child)
        attach(self.winfo_toplevel())

    @staticmethod
    def preferred_inspector_width(state):
        if state.get('inspector_layout_version')!=2: return 180
        try: return max(120,min(1000,int(state.get('inspector_width',180))))
        except (ValueError,TypeError): return 180

    def reflow_selection_toolbar(self,_event=None):
        available=self.selection_toolbar.winfo_width()
        if available<20: return
        x=y=row_height=0
        for group in self.selection_toolbar_groups:
            width=group.winfo_reqwidth(); height=group.winfo_reqheight()
            if x and x+width>available: y+=row_height+4; x=row_height=0
            group.place(x=x,y=y,width=width,height=height)
            x+=width+6; row_height=max(row_height,height)
        self.selection_toolbar.configure(height=y+row_height+4)

    def align_folder_tree(self,_event=None):
        self.folder_alignment_job=None
        tree=self.folder_tree
        if tree.winfo_width()<30: return
        visible={tree.identify_row(y) for y in range(1,tree.winfo_height(),8)}-{''}
        if not visible: return
        def depth(node):
            result=0; ancestor=tree.parent(node)
            while ancestor: result+=1; ancestor=tree.parent(ancestor)
            return result
        try: indent=int(ttk.Style(tree).lookup('Treeview','indent') or 20)
        except (ValueError,tk.TclError): indent=20
        import tkinter.font as tkfont
        font=tkfont.nametofont('TkDefaultFont',root=tree)
        offset=max(0,min(depth(node) for node in visible)*indent-4)
        width=max(tree.winfo_width()+offset,max(depth(node)*indent+font.measure(tree.item(node,'text'))+40 for node in visible))
        tree.column('#0',width=width,stretch=False)
        tree.xview_moveto(offset/max(1,width))

    def folder_scroll_changed(self,scrollbar,first,last):
        scrollbar.set(first,last)
        position=(first,last)
        if position!=getattr(self,'folder_scroll_position',None):
            self.folder_scroll_position=position
            if getattr(self,'folder_alignment_job',None) is None:
                self.folder_alignment_job=self.after_idle(self.align_folder_tree)

    def tick_highlighted(self):
        self.checked_paths.update(str(item.path) for item in self.highlighted_items())
        self.refresh_checks()

    def untick_highlighted(self):
        self.checked_paths.difference_update(str(item.path) for item in self.highlighted_items())
        self.refresh_checks()

    def rename_with_preview(self):
        items=self.selected_items()
        if len(items)!=1:
            self.app.batch_rename_selected(); return
        item=items[0]; window=tk.Toplevel(self); window.title('Rename file — live preview'); window.geometry('680x240'); window.transient(self.winfo_toplevel())
        value=tk.StringVar(value=item.path.name); status=tk.StringVar()
        ttk.Label(window,text=f'Current filename: {item.path.name}',padding=12).pack(fill='x')
        entry=ttk.Entry(window,textvariable=value); entry.pack(fill='x',padx=12)
        ttk.Label(window,textvariable=status,wraplength=650,padding=12).pack(fill='x')
        def preview(*_):
            template=value.get().replace('{','{{').replace('}','}}')
            plan=self.app.plan_batch_rename([item],template)[0]
            status.set(self.app.translator.ui_text('New filename: {name}\n{status}').format(name=value.get(),status=self.app.translator.ui_text(plan['status'])))
            apply_button.configure(state='normal' if plan['status']=='Ready' else 'disabled')
            return plan
        def apply():
            plan=preview()
            if plan['status']!='Ready': return
            target=plan['target']
            if target.exists():
                messagebox.showerror('Rename failed','Destination now exists. Choose another name.',parent=window); return
            try:
                item.path.rename(target); self.metadata_cache.move_user_data(item.path,target)
                if str(item.path) in self.checked_paths:
                    self.checked_paths.discard(str(item.path)); self.checked_paths.add(str(target))
                self.app.record_undo('rename',[(target,item.path)])
                window.destroy(); self.scan(target)
            except OSError as error: messagebox.showerror('Rename failed',str(error),parent=window)
        buttons=ttk.Frame(window,padding=12); buttons.pack(fill='x')
        apply_button=ttk.Button(buttons,text='Rename',command=apply); apply_button.pack(side='left')
        ttk.Button(buttons,text='Cancel',command=window.destroy).pack(side='right')
        value.trace_add('write',preview); preview(); entry.focus_set(); entry.selection_range(0,len(item.path.stem))
        window.bind('<Return>',lambda _event:apply()); window.bind('<Escape>',lambda _event:window.destroy()); window.grab_set()

    def new_folder(self):
        self.active_callback(self)
        target=create_folder(self,self.current_path)
        if target: self.refresh_browser()

    def remember_inspector_width(self,_event=None):
        if len(self.inspector_panes.panes())==2 and self.inspector_panes.winfo_width()>100:
            total=self.inspector_panes.winfo_width()
            self.inspector_width=max(120,min(total-self.inspector_panes.sashpos(0),max(120,total-180)))
            self.restore_inspector_width()

    def fit_inspector_content(self,_event=None):
        available=max(80,self.inspector_frame.winfo_width()-16)
        details=getattr(self,'inspector_details_text',None)
        if details is not None:
            style=ttk.Style(self)
            details.configure(background=style.lookup('TLabel','background') or self.winfo_toplevel().cget('background'),
                              foreground=style.lookup('TLabel','foreground') or 'black')
        for widget in self.inspector_frame.winfo_children():
            if isinstance(widget,ttk.Label): widget.configure(wraplength=available)
        x=y=row_height=0
        for button in self.inspector_buttons.winfo_children():
            button.pack_forget()
            width,height=button.winfo_reqwidth(),button.winfo_reqheight()
            if x and x+width>available: y+=row_height+4; x=row_height=0
            button.place(x=x,y=y,width=width,height=height)
            x+=width+4; row_height=max(row_height,height)
        self.inspector_buttons.configure(height=y+row_height)

    def restore_inspector_width(self):
        if len(self.inspector_panes.panes())==2:
            total=self.inspector_panes.winfo_width()
            if total<100: return
            width=min(self.inspector_width,max(120,total-180))
            self.inspector_panes.sashpos(0,max(1,int(total-width)))

    def clamp_folder_width(self):
        total=self.content_panes.winfo_width()
        if total>150:
            position=self.content_panes.sashpos(0)
            if position>total//3: self.content_panes.sashpos(0,total//3)

    def thumbnail_dimensions(self):
        width=int(self.thumbnail_pixels.get())
        return width,round(width*.68),width+25

    def thumbnail_slider_changed(self,_value=None):
        if self.view_mode_var.get()=='Thumbnails': self.schedule_thumbnail_reflow(180)

    def rubber_start(self,event):
        if getattr(self,'rubber_active',False): return 'break'
        widget=event.widget
        self.active_callback(self)
        self.rubber_origin=(event.x_root,event.y_root)
        self.rubber_base={str(item.path) for item in self.highlighted_items()} if event.state&4 else set()
        self.rubber_active=True
        self.checkbox_pending=None
        self.preferred_selection_path=None
        if not event.state&4: self.tree.selection_set(())
        self.rubber_box=[tk.Frame(self,bg='#4a90e2',bd=0) for _ in range(4)]
        # Tk routes a grabbed canvas's events to its child thumbnail labels.
        # Put the selection tag before their native DnD bindings so a drag
        # begun on empty space keeps receiving motion/release over images.
        tag=f'RFMSelection{self.winfo_id()}'
        self.route_pointer_gesture(tag,self.rubber_motion,self.rubber_end)
        widget.grab_set()
        return 'break'

    def rubber_motion(self,event):
        if not getattr(self,'rubber_active',False): return
        x0,y0=self.rubber_origin; x1,y1=event.x_root,event.y_root
        left,right=sorted((x0,x1)); top,bottom=sorted((y0,y1)); keys=set(self.rubber_base); selected=[]
        if self.view_mode_var.get()=='Details':
            for iid in self.tree.get_children():
                box=self.tree.bbox(iid)
                if not box: continue
                x,y,w,h=box; x+=self.tree.winfo_rootx(); y+=self.tree.winfo_rooty()
                if x<=right and x+w>=left and y<=bottom and y+h>=top:
                    tags=self.tree.item(iid,'tags')
                    if tags: keys.add(tags[0]); selected.append(iid)
        else:
            for key,card in self.thumbnail_cells.items():
                x,y=card.winfo_rootx(),card.winfo_rooty()
                if x<=right and x+card.winfo_width()>=left and y<=bottom and y+card.winfo_height()>=top: keys.add(key)
            selected=[self.path_to_iid[k] for k in keys if k in self.path_to_iid]
        selected=list(set(selected)|{self.path_to_iid[k] for k in keys if k in self.path_to_iid})
        self.tree.selection_set(selected)
        self.update_thumbnail_selection()
        viewport=self.tree if self.view_mode_var.get()=='Details' else self.thumbnail_canvas
        left=max(left,viewport.winfo_rootx()); right=min(right,viewport.winfo_rootx()+viewport.winfo_width())
        top=max(top,viewport.winfo_rooty()); bottom=min(bottom,viewport.winfo_rooty()+viewport.winfo_height())
        x,y=left-self.winfo_rootx(),top-self.winfo_rooty(); width=max(1,right-left); height=max(1,bottom-top)
        for edge,box in zip(self.rubber_box,((x,y,width,1),(x,y+height,width,1),(x,y,1,height),(x+width,y,1,height))):
            edge.place(x=box[0],y=box[1],width=box[2],height=box[3])
        return 'break'

    def rubber_end(self,event):
        if not getattr(self,'rubber_active',False): return
        self.rubber_motion(event); self.rubber_active=False
        grabbed=self.grab_current()
        if grabbed: grabbed.grab_release()
        for edge in self.rubber_box: edge.destroy()
        return 'break'
