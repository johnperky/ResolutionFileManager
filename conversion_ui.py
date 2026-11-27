"""Small cross-platform destination chooser with explicit folder creation."""
import os
from pathlib import Path
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, simpledialog, ttk


def remember_conversion_choice(app, key, variable, allowed, choices=None, *, trace=True):
    """Persist canonical values, separately for each converter and translated UI."""
    saved = app.settings.get(key)
    if saved in allowed:
        variable.set(choices.label(saved) if choices else saved)
    def remember(*_args):
        try:
            value = variable.get()
        except tk.TclError:
            return
        if choices:
            value = choices.internal(value)
        if value in allowed and app.settings.get(key) != value:
            app.settings[key] = value
            app.save_local_preferences()
    if trace:
        variable.trace_add('write', remember)
    return remember


def checked_counts(paths, visible_items):
    visible = {str(item.path) for item in visible_items}
    return len(paths), len({str(Path(path).parent) for path in paths}), len(set(paths) - visible)


def remaining_seconds(fraction, elapsed):
    if fraction <= 0 or elapsed < 2:
        return None
    return max(0, elapsed * (1 - fraction) / fraction)


def source_folder_choice(app, kind):
    """Default on; retain each converter's last explicit choice in app settings."""
    key = kind + '_same_as_source'
    variable = tk.BooleanVar(master=app, value=app.settings.get(key, True))
    def remember(*_args):
        app.settings[key] = bool(variable.get())
        app.save_local_preferences()
    variable.trace_add('write', remember)
    return variable


def video_quality_choice(app):
    saved = app.settings.get('video_quality', 25)
    if not isinstance(saved, int) or not 18 <= saved <= 35:
        saved = 25
    variable = tk.IntVar(master=app, value=saved)
    def remember(*_args):
        try:
            value = variable.get()
        except tk.TclError:
            return
        if 18 <= value <= 35:
            app.settings['video_quality'] = value
            app.save_local_preferences()
    variable.trace_add('write', remember)
    return variable


def video_preset_choice(app, choices):
    valid = {choices.internal(label) for label in choices.labels}
    saved = app.settings.get('video_preset')
    if saved not in valid:
        saved = 'Keep source H.265 MKV (smaller)'
    variable = tk.StringVar(master=app, value=choices.label(saved))
    def remember(*_args):
        value = choices.internal(variable.get())
        if value in valid:
            app.settings['video_preset'] = value
            app.save_local_preferences()
    variable.trace_add('write', remember)
    return variable


def conversion_items(app, pane, extensions):
    """Resolve a stale ticked group explicitly, without changing either selection."""
    selected = [item for item in pane.selected_items() if item.path.suffix.lower() in extensions]
    highlighted = [item for item in pane.highlighted_items() if item.path.suffix.lower() in extensions]
    if highlighted and {item.path for item in selected} != {item.path for item in highlighted}:
        def names(items):
            return '\n'.join(str(item.path) for item in items[:5]) + ('\n…' if len(items) > 5 else '')
        answer = messagebox.askyesnocancel(
            'Choose files to convert',
            f'Ticked files and highlighted files differ.\n\nYES — use ticked files ({len(selected)}):\n{names(selected)}'
            f'\n\nNO — use highlighted files ({len(highlighted)}):\n{names(highlighted)}'
            '\n\nCancel returns without opening conversion.', parent=app, default=messagebox.CANCEL)
        return selected if answer is True else highlighted if answer is False else None
    return selected


def middle_filename(name, pixels, measure):
    """Keep both ends (including extension), measured using the actual list font."""
    if measure(name) <= pixels:
        return name
    low, high = 0, len(name)
    while low < high:
        count = (low + high + 1) // 2
        left = (count + 1) // 2
        right = count // 2
        candidate = name[:left] + '…' + (name[-right:] if right else '')
        if measure(candidate) <= pixels:
            low = count
        else:
            high = count - 1
    left, right = (low + 1) // 2, low // 2
    return name[:left] + '…' + (name[-right:] if right else '')


class ConversionPaths:
    """Short names in the queue; copyable full paths for the selected row."""
    def __init__(self, tree, parent, output_column, tr):
        self.tree, self.output_column, self.paths = tree, output_column, {}
        self.font = tkfont.nametofont(ttk.Style(tree).lookup('Treeview', 'font') or 'TkDefaultFont')
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=10, pady=3)
        frame.columnconfigure(1, weight=1)
        self.variables = []
        for row, label in enumerate(('Source', 'Output')):
            variable = tk.StringVar(master=tree)
            self.variables.append(variable)
            ttk.Label(frame, text=tr(label)).grid(row=row, column=0, sticky='w', padx=(0, 6))
            ttk.Entry(frame, textvariable=variable, state='readonly').grid(row=row, column=1, sticky='ew')
        tree.bind('<<TreeviewSelect>>', self.show, add='+')
        tree.bind('<Configure>', self.render, add='+')
        tree.bind('<ButtonRelease-1>', self.render, add='+')

    def set(self, iid, source, target):
        self.paths[str(iid)] = (str(source), str(target))
        self.render_row(str(iid), self.paths[str(iid)])
        if not self.tree.selection():
            self.tree.selection_set(iid)
        self.show()

    def render(self, _event=None):
        for iid, paths in list(self.paths.items()):
            if not self.tree.exists(iid):
                del self.paths[iid]
                continue
            self.render_row(iid, paths)

    def render_row(self, iid, paths):
        for column, path in zip(('source', self.output_column), paths):
            self.tree.set(iid, column, middle_filename(Path(path).name,
                          max(15, self.tree.column(column, 'width') - 16), self.font.measure))

    def show(self, _event=None):
        selected = self.tree.selection()
        paths = self.paths.get(selected[0], ('', '')) if selected else ('', '')
        for variable, path in zip(self.variables, paths):
            variable.set(path)


def grow_conversion_options_once(window,content,reserved):
    """Fit normal desktop options, without fighting later manual resizing."""
    if getattr(window,'_conversion_options_sized',False) or window.winfo_height()<50:return
    window._conversion_options_sized=True
    width=max(window.winfo_width(),min(window.winfo_screenwidth()-40,content.winfo_reqwidth()+60))
    height=max(window.winfo_height(),min(window.winfo_screenheight()-80,content.winfo_reqheight()+reserved))
    window.geometry(f'{width}x{height}')


def bind_conversion_scrolling(canvas,content,horizontal,vertical):
    """Scoped wheel routing and scrollbars only when the options overflow."""
    tag='ConversionOptions'+str(canvas)
    def scroll(event):
        delta=getattr(event,'delta',0);number=getattr(event,'num',None)
        units=-1 if number==4 else 1 if number==5 else (-max(1,abs(delta)//120) if delta>0 else max(1,abs(delta)//120) if delta<0 else 0)
        if units:
            if event.state & 1:canvas.xview_scroll(units,'units')
            else:canvas.yview_scroll(units,'units')
        return 'break'
    def bar_update(bar,side,first,last):
        bar.set(first,last)
        if float(first)<=0 and float(last)>=1:
            if bar.winfo_manager():bar.pack_forget()
        elif not bar.winfo_manager():bar.pack(side=side,fill='y' if side=='right' else 'x',before=canvas)
    canvas.configure(xscrollcommand=lambda a,b:bar_update(horizontal,'bottom',a,b),yscrollcommand=lambda a,b:bar_update(vertical,'right',a,b))
    sequences=('<MouseWheel>','<Shift-MouseWheel>','<Button-4>','<Button-5>')
    ids=[canvas.bind_class(tag,event,scroll) for event in sequences]
    def install(widget):
        widget.bindtags((tag,*widget.bindtags()))
        for child in widget.winfo_children():install(child)
    install(canvas)
    def cleanup(event):
        if event.widget is not content:return
        for sequence,identifier in zip(sequences,ids):
            canvas.unbind_class(tag,sequence)
            if identifier:canvas._root().deletecommand(identifier)
    content.bind('<Destroy>',cleanup,add='+')


def set_conversion_activity(bar, fraction):
    """Animate unknown work, then display only measured completion."""
    if fraction is None:
        if str(bar.cget('mode')) != 'indeterminate':
            bar.configure(mode='indeterminate',value=0)
            bar.start(40)
    else:
        bar.stop()
        bar.configure(mode='determinate',value=max(0,min(1,fraction))*100)


def conversion_locations():
    """List drive roots without probing each device; Linux exposes mount locations."""
    if os.name == 'nt':
        import ctypes
        mask = ctypes.windll.kernel32.GetLogicalDrives()
        return [Path(f'{chr(65 + index)}:/') for index in range(26) if mask & (1 << index)]
    locations = [Path('/'), Path.home()]
    for base in (Path('/media'), Path('/run/media'), Path('/mnt')):
        try:
            for child in base.iterdir():
                if not child.is_dir(): continue
                if child.name == Path.home().name and base != Path('/mnt'):
                    locations.extend(path for path in child.iterdir() if path.is_dir())
                else: locations.append(child)
        except OSError: continue
    return list(dict.fromkeys(locations))


def choose_conversion_folder(parent, initial):
    window = tk.Toplevel(parent)
    window.title('Choose conversion destination')
    window.geometry('640x430')
    window.minsize(440, 300)
    window.transient(parent)
    result = {'path': None}
    current = Path(initial).expanduser()
    while not current.is_dir() and current.parent != current:
        current = current.parent
    path_var = tk.StringVar(value=str(current))
    top = ttk.Frame(window, padding=10); top.pack(fill='x')
    entry = ttk.Entry(top, textvariable=path_var); entry.pack(side='left', fill='x', expand=True)
    listing = tk.Listbox(window, exportselection=False)
    scroll = ttk.Scrollbar(window, command=listing.yview)
    listing.configure(yscrollcommand=scroll.set)
    buttons = ttk.Frame(window, padding=10); buttons.pack(side='bottom', fill='x')
    scroll.pack(side='right', fill='y'); listing.pack(fill='both', expand=True, padx=(10, 0))
    folders = []
    locations_title = 'This PC — choose a drive' if os.name == 'nt' else 'Choose a location'

    def show(path):
        nonlocal current, folders
        try:
            path = Path(path).expanduser().resolve()
            folders = sorted((child for child in path.iterdir() if child.is_dir()), key=lambda child: child.name.casefold())
        except (OSError, ValueError) as exc:
            messagebox.showerror('Cannot open folder', str(exc), parent=window)
            return
        current = path; path_var.set(str(path)); listing.delete(0, 'end')
        for folder in folders: listing.insert('end', folder.name)

    def show_locations():
        nonlocal current, folders
        current = None; folders = conversion_locations()
        path_var.set(locations_title); listing.delete(0, 'end')
        for folder in folders: listing.insert('end', str(folder))

    def up():
        if current is None or current.parent == current: show_locations()
        else: show(current.parent)

    def enter(_event=None):
        selected = listing.curselection()
        if selected: show(folders[selected[0]])

    def create():
        name = simpledialog.askstring('New folder', 'Folder name:', parent=window)
        if not name: return
        if name in ('.', '..') or any(char in '<>:"/\\|?*' or ord(char) < 32 for char in name) or name.endswith((' ', '.')):
            messagebox.showerror('Invalid folder name', 'Enter a single folder name without reserved characters.', parent=window)
            return
        try:
            parent = Path(path_var.get()).expanduser().resolve()
            if not parent.is_dir():
                raise NotADirectoryError('Open an existing parent folder before creating a new folder.')
            target = parent / name
            target.mkdir()
            show(target)
        except (OSError, ValueError) as exc:
            messagebox.showerror('Cannot create folder', str(exc), parent=window)

    def select():
        selected = listing.curselection()
        if current is None and path_var.get() == locations_title:
            if not selected:
                messagebox.showinfo('Choose a folder', 'Open or select a drive or location first.', parent=window)
                return
            chosen = folders[selected[0]]
        else:
            chosen = Path(path_var.get()).expanduser()
        if not chosen.is_dir():
            messagebox.showerror('Folder not found', 'Open or create an existing destination folder first.', parent=window)
            return
        selected = listing.curselection()
        result['path'] = str(folders[selected[0]] if selected and chosen.resolve() == current else chosen.resolve())
        window.destroy()

    ttk.Button(top, text='Open', command=lambda: show(path_var.get())).pack(side='left', padx=5)
    ttk.Button(top, text='Up', command=up).pack(side='left')
    ttk.Button(top, text='Drives' if os.name == 'nt' else 'Locations', command=show_locations).pack(side='left', padx=(5, 0))
    ttk.Button(buttons, text='New folder…', command=create).pack(side='left')
    ttk.Button(buttons, text='Cancel', command=window.destroy).pack(side='right')
    ttk.Button(buttons, text='Select folder', command=select).pack(side='right', padx=6)
    listing.bind('<Double-1>', enter); listing.bind('<Return>', enter)
    entry.bind('<Return>', lambda _event: show(path_var.get()))
    window.bind('<Escape>', lambda _event: window.destroy())
    show(current); window.grab_set(); parent.wait_window(window)
    return result['path']
