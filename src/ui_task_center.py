"""One window for the queue, named templates and advanced jobs."""
import tkinter as tk
from ui_focus import current_grab, current_focus
from tkinter import ttk
from ui_window import prepare, show, button_grid, compact_show
from theme import theme,flat_button,apply_nav_state
from ui_queue import QueuePanel
from ui_tasks import TaskPanel


class TaskCenter(tk.Toplevel):
    def __init__(self, app, tab='queue', parent=None):
        super().__init__(app.root)
        prepare(self)
        self.app, self.T = app, app.T
        self.previous_grab = current_grab(app.root)
        from i18n import feature_text
        self.title(feature_text(self.T,'任务中心'))
        self.configure(bg=theme.c('bg'))
        self.resizable(True, True)
        self.tab_bar=tk.Frame(self,bg=theme.c('bg'));self.tab_bar.pack(fill='x',padx=8,pady=(8,0));self.tab_buttons={}
        ttk.Style(self).layout('TaskCenter.TNotebook.Tab',[])
        ttk.Style(self).layout('TaskCenter.TNotebook',[])
        self.notebook = ttk.Notebook(self, style='TaskCenter.TNotebook')
        self.notebook.pack(fill='both', expand=True, padx=8, pady=(8, 8))
        self.panels = {}
        self._painted_tab=None;self._last_counts=None
        self.frames = {}
        self.notebook._local_tab_keys = {}
        for key, label_key in [('queue', 'center_queue'), ('templates', 'center_templates'), ('advanced', 'center_advanced')]:
            b=flat_button(self.tab_bar,self.T(label_key),lambda key=key:self.select_tab(key),kind='nav',font=theme.font(delta=-1),padx=10,pady=6);b._local_text_key=label_key;b.grid(row=0,column=len(self.tab_buttons),sticky='ew',padx=3);self.tab_bar.columnconfigure(len(self.tab_buttons),weight=1,uniform='tabs');self.tab_buttons[key]=b
            frame = tk.Frame(self.notebook, bg=theme.c('bg'))
            frame.pack_propagate(False)
            self.notebook.add(frame, text=self.T(label_key))
            self.notebook._local_tab_keys[str(frame)] = label_key
            self.frames[key]=frame
        self._ensure_panel('queue')
        self.notebook.bind('<<NotebookTabChanged>>', lambda event: self._paint_tabs())
        self.bind('<Escape>', lambda event: self.destroy())
        self.protocol('WM_DELETE_WINDOW', self.destroy)
        self.select_tab(tab)
        compact_show(self,app);self.focus_set()

    @property
    def tv(self):
        """Legacy queue callbacks address the queue table explicitly."""
        return self.panels['queue'].tv

    def _ensure_panel(self,key):
        if key in self.panels:return
        frame=self.frames[key]
        panel=QueuePanel(self.app,frame) if key=='queue' else TaskPanel(self.app,frame,advanced=key=='advanced')
        panel.pack(fill='both',expand=True);self.panels[key]=panel
        from ui_dialog_palette import apply
        apply(self,panel)

    def select_tab(self, key):
        if key not in self.frames: key = 'queue'
        self._ensure_panel(key)
        target=self.frames[key]
        if self.notebook.select()!=str(target):self.notebook.select(target)
        if self._painted_tab==str(target):self.refresh_status(force=True)
        else:self._paint_tabs()

    def _paint_tabs(self):
        selected=self.notebook.select()
        if selected==self._painted_tab:return
        self._painted_tab=selected
        for key,b in self.tab_buttons.items():apply_nav_state(b,str(self.frames[key])==selected)
        from ui_dialog_palette import apply
        apply(self,self.tab_bar)
        self.refresh_status(force=True)

    def refresh_status(self, force=False):
        if not self.winfo_exists() or (not force and not self.winfo_viewable()): return
        self.T=self.app.T
        active=(self.app._active_task or {}).get('id') if self.app.engine.is_running() else None
        counts={'queue':sum(t.get('id')!=active for t in self.app.task_queue),'templates':len(self.app.cfg.get('templates') or []),'advanced':len(self.app.automation.jobs)}
        if counts!=self._last_counts:
            for key,b in self.tab_buttons.items():b.config(text=self.T('center_'+key)+'  '+str(counts[key]))
            self._last_counts=counts
        selected=self.notebook.select()
        for key,panel in self.panels.items():
            if str(panel.master)==selected:
                panel.refresh() if key=='queue' else panel.refresh_status()

    def refresh(self):
        self.refresh_status()

    def destroy(self):
        previous = getattr(self, 'previous_grab', None)
        super().destroy()
        if previous:
            try:
                if previous.winfo_exists(): previous.grab_set()
            except tk.TclError: pass
