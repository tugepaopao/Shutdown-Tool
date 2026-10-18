"""Compact target picker: running window or exact exe path."""
import tkinter as tk
from ui_focus import current_grab, current_focus
from tkinter import ttk,filedialog
from ui_window import prepare,show,button_grid
from ui_localize import messagebox
from theme import theme
from program_control import running_programs,validate_target

class CloseProgramDialog(tk.Toplevel):
    def __init__(self,app,parent=None,initial=None):
        super().__init__(parent or app.root);prepare(self)
        self.app,self.T=app,app.T;self.result=None;self.previous_grab=current_grab(app.root)
        self.title(self.T('close_title'));self.transient(parent or app.root);self.configure(bg=theme.c('bg'));self.resizable(False,False)
        body=tk.Frame(self,bg=theme.c('bg'));body.pack(fill='both',expand=True,padx=14,pady=12)
        self.path=tk.StringVar(value=initial if initial is not None else app.cfg.get('close_program_path',''))
        self.combo=ttk.Combobox(body,state='readonly',width=42)
        tk.Label(body,text=self.T('close_running'),bg=theme.c('bg'),fg=theme.c('fg'),font=theme.font(),anchor='w').pack(fill='x')
        self.combo.pack(fill='x',pady=(5,8));self.combo.bind('<<ComboboxSelected>>',self.select)
        ttk.Entry(body,textvariable=self.path,width=42).pack(fill='x',pady=(0,8))
        bar=tk.Frame(body,bg=theme.c('bg'));bar.pack(fill='x')
        button_grid(bar,[(self.T('close_refresh'),self.refresh,'normal'),(self.T('close_browse'),self.browse,'normal')])
        tk.Label(body,text=self.T('close_hint'),bg=theme.c('bg'),fg=theme.c('fg_muted'),font=theme.font(),wraplength=420,justify='left',anchor='w').pack(fill='x',pady=(10,8))
        foot=tk.Frame(body,bg=theme.c('bg'));foot.pack(fill='x');button_grid(foot,[(self.T('btn_cancel'),self.destroy,'normal'),(self.T('btn_ok'),self.accept,'accent')])
        self.bind('<Escape>',lambda e:self.destroy());self.refresh();self.update_idletasks()
        self.geometry('+%d+%d'%(app.root.winfo_rootx()+30,app.root.winfo_rooty()+55));show(self);self.grab_set();self.focus_set()
    def refresh(self):
        self.programs=running_programs();self.combo['values']=[__import__('os').path.basename(w['path'])+' · '+w['title'][:70] for w in self.programs]
        self.combo.set(self.T('close_choose') if self.programs else self.T('close_none'))
    def select(self,event=None):
        index=self.combo.current()
        if 0<=index<len(self.programs):self.path.set(self.programs[index]['path'])
    def browse(self):
        path=filedialog.askopenfilename(parent=self,title=self.T('close_title'),filetypes=[('Executable','*.exe')])
        if path:self.path.set(path)
    def accept(self):
        try:self.result=validate_target(self.path.get())
        except ValueError as exc:messagebox.showinfo(self.T('tip_title'),str(exc),parent=self);return
        self.destroy()
    def destroy(self):
        previous=getattr(self,'previous_grab',None);super().destroy()
        if previous:
            try:
                if previous.winfo_exists():previous.grab_set()
            except tk.TclError:pass
