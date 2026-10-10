"""公开版自选音频文件入口。"""
import tkinter as tk
from ui_window import prepare, show, button_grid
from tkinter import filedialog
from sound_library import resolve
from theme import theme, flat_button

class SoundDialog(tk.Toplevel):
    def __init__(self,app):
        super().__init__(app.root);prepare(self);self.app=app;self.result=None;T=app.T
        self.title(T('sound_title'));self.configure(bg=theme.c('bg'));self.transient(app.root);self.resizable(False,False)
        self.path=tk.StringVar(value=resolve(app.cfg.get('sound_file')))
        tk.Label(self,text=T('sound_custom'),bg=theme.c('bg'),fg=theme.c('fg'),font=theme.font()).pack(anchor='w',padx=16,pady=(12,2))
        row=tk.Frame(self,bg=theme.c('bg'));row.pack(fill='x',padx=16,pady=6)
        tk.Entry(row,textvariable=self.path,width=36,bg=theme.c('input_bg'),fg=theme.c('input_fg'),font=theme.font()).pack(side='left',fill='x',expand=True)
        flat_button(row,T('sound_browse'),self.browse).pack(side='left',padx=6)
        bar=tk.Frame(self,bg=theme.c('bg'));bar.pack(fill='x',padx=16,pady=12)
        button_grid(bar,[(T('btn_cancel'),self.destroy,'normal'),(T('btn_ok'),self.save,'accent')])
        self.bind('<Escape>',lambda e:self.destroy());app._apply_window_chrome(self);show(self);self.grab_set();self.focus_set()
    def browse(self):
        f=filedialog.askopenfilename(parent=self,filetypes=[(self.app.T('dlg_audio'),'*.wav;*.mp3;*.wma;*.m4a;*.aac;*.flac;*.ogg'),(self.app.T('dlg_all_files'),'*.*')])
        if f:self.path.set(f)
    def save(self):
        value=self.path.get().strip()
        if not value:return
        self.result=value;self.destroy()
