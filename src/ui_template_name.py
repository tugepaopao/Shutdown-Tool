"""Current styled input for the public edition's named templates."""
import tkinter as tk
from ui_focus import current_grab, current_focus
from tkinter import ttk
from ui_window import prepare,show,button_grid
from theme import theme

class TemplateNameDialog(tk.Toplevel):
    def __init__(self,parent,title,prompt,initialvalue='',**kw):
        super().__init__(parent);prepare(self);self.result=None;self.parent=parent;self.previous_grab=current_grab(parent);self.title(title);self.transient(parent.winfo_toplevel());self.resizable(False,False)
        owner=getattr(parent._root(),'_theme_owner',None);self.T=getattr(owner,'T',None)
        if self.T:
            from ui_localize import translate
            self.title(translate(title,'CHS',self.T.lang));prompt=translate(prompt,'CHS',self.T.lang)
        body=tk.Frame(self,bg=theme.c('bg'));body.pack(fill='both',expand=True,padx=18,pady=16)
        tk.Label(body,text=prompt,bg=theme.c('bg'),fg=theme.c('fg'),font=theme.font(),anchor='w',wraplength=380).pack(fill='x',pady=(0,10))
        self.value=tk.StringVar(self,value=initialvalue or '');self.entry=ttk.Entry(body,textvariable=self.value,width=34);self.entry.pack(fill='x',ipady=4);self.entry.select_range(0,'end')
        footer=tk.Frame(self,bg=theme.c('bg'));footer.pack(fill='x',padx=18,pady=(0,16))
        labels=(self.T('btn_cancel'),self.T('btn_ok')) if self.T else ('取消','确定')
        self.buttons=button_grid(footer,[(labels[0],self.cancel,'normal'),(labels[1],self.ok,'accent')]);self.entry.bind('<Return>',lambda e:self.ok());self.bind('<Escape>',lambda e:self.cancel());self.protocol('WM_DELETE_WINDOW',self.cancel)
        self.update_idletasks();self.geometry(f'+{parent.winfo_rootx()+35}+{parent.winfo_rooty()+35}');show(self);self.grab_set();self.entry.focus_set()
    def ok(self):self.result=self.value.get();self.destroy()
    def cancel(self):self.result=None;self.destroy()
    def destroy(self):
        previous=self.previous_grab;super().destroy()
        if previous:
            try:
                if previous.winfo_exists():previous.grab_set()
            except tk.TclError:pass

def askstring(title,prompt,**kw):
    parent=kw.pop('parent',None) or tk._default_root;dialog=TemplateNameDialog(parent,title,prompt,**kw);parent.wait_window(dialog);return dialog.result
