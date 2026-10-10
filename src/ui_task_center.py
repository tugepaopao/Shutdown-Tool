"""One window for the queue, named templates and advanced jobs."""
import tkinter as tk
from tkinter import ttk
from ui_window import prepare, show, button_grid
from theme import theme
from ui_queue import QueuePanel
from ui_tasks import TaskPanel


class TaskCenter(tk.Toplevel):
    def __init__(self, app, tab='queue', parent=None):
        super().__init__(app.root)
        prepare(self)
        self.app, self.T = app, app.T
        self.previous_grab = app.root.grab_current()
        self.title(self.T('center_title'))
        self.configure(bg=theme.c('bg'))
        self.transient(parent or app.root)
        self.resizable(True, True)
        self.notebook = ttk.Notebook(self, style='TaskCenter.TNotebook')
        self.notebook.pack(fill='both', expand=True, padx=12, pady=(12, 8))
        self.panels = {}
        self.notebook._local_tab_keys = {}
        for key, label_key in [('queue', 'center_queue'), ('templates', 'center_templates'), ('advanced', 'center_advanced')]:
            frame = tk.Frame(self.notebook, bg=theme.c('bg'))
            self.notebook.add(frame, text=self.T(label_key))
            self.notebook._local_tab_keys[str(frame)] = label_key
            panel = QueuePanel(app, frame) if key == 'queue' else TaskPanel(app, frame, advanced=key == 'advanced')
            panel.pack(fill='both', expand=True)
            self.panels[key] = panel
        foot = tk.Frame(self, bg=theme.c('bg')); foot.pack(fill='x', padx=12, pady=(0, 12))
        button_grid(foot, [(self.T('queue_close'), self.destroy, 'normal')])
        self.notebook.bind('<<NotebookTabChanged>>', lambda event: self.refresh_status())
        self.bind('<Escape>', lambda event: self.destroy())
        self.protocol('WM_DELETE_WINDOW', self.destroy)
        self.update_idletasks()
        width = min(max(700, self.winfo_reqwidth()), self.winfo_screenwidth()-60)
        height = min(max(510, self.winfo_reqheight()), self.winfo_screenheight()-100)
        self.geometry(f'{width}x{height}+{app.root.winfo_rootx()+35}+{app.root.winfo_rooty()+35}')
        self.minsize(min(640, width), min(480, height))
        self.select_tab(tab)
        show(self); self.grab_set(); self.focus_set()

    @property
    def tv(self):
        """Legacy queue callbacks address the queue table explicitly."""
        return self.panels['queue'].tv

    def select_tab(self, key):
        if key not in self.panels: key = 'queue'
        self.notebook.select(self.panels[key].master)
        self.refresh_status()

    def refresh_status(self):
        if not self.winfo_exists(): return
        self.panels['queue'].refresh()
        for key in ('templates', 'advanced'): self.panels[key].refresh_status()

    def refresh(self):
        self.refresh_status()

    def destroy(self):
        previous = getattr(self, 'previous_grab', None)
        super().destroy()
        if previous:
            try:
                if previous.winfo_exists(): previous.grab_set()
            except tk.TclError: pass
