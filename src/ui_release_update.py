"""Manual update flow; worker threads never call Tk."""
import queue
import threading
import tkinter as tk
import subprocess
from tkinter import ttk
from theme import theme,flat_button,enable_button
from ui_window import prepare,content_show,text_rows
from ui_dialog_palette import COLORS as C
from ui_localize import messagebox
from i18n import VERSION
import release_update

class UpdateWindow(tk.Toplevel):
    def __init__(self,app,parent):
        super().__init__(parent);prepare(self);self.app=app;self.T=app.T
        self.title('检查更新');self.events=queue.Queue();self.cancel=threading.Event();self.release=None;self.path=None;self.busy=False
        self.label=tk.Label(self,text=f'当前版本 v{VERSION}',bg=C['bg'],fg=C['fg'],font=theme.font(),anchor='w',justify='left',wraplength=460)
        self.label.pack(fill='x',padx=16,pady=12)
        frame=self.notes_frame=tk.Frame(self,bg=C['bg'])
        self.notes=tk.Text(frame,wrap='word',bg=C['card'],fg=C['fg'],font=theme.font(delta=-1),bd=0,width=1,height=9)
        scroll=ttk.Scrollbar(frame,command=self.notes.yview);scroll.pack(side='right',fill='y');self.notes.config(yscrollcommand=scroll.set);self.notes.pack(fill='both',expand=True)
        self.progress=ttk.Progressbar(self,maximum=100)
        bar=self.footer=tk.Frame(self,bg=C['bg']);bar.pack(fill='x',padx=16,pady=(4,12))
        flat_button(bar,'关闭',self.destroy,padx=14,pady=5).pack(side='right')
        self.button=flat_button(bar,'检查更新',self.check,kind='accent',padx=14,pady=5);self.button.pack(side='right',padx=(0,8))
        self.protocol('WM_DELETE_WINDOW',self.destroy);self.bind('<Escape>',lambda e:self.destroy())
        self.poll=self.after(100,self.receive);self.check()
    def layout(self,notes=False,progress=False):
        self.notes_frame.pack_forget();self.progress.pack_forget()
        from ui_cozy import scale
        self.label.config(wraplength=round((378 if notes else 328)*scale(self)))
        if notes:
            self.notes.config(height=text_rows(self,self.notes.get('1.0','end-1c'),360*scale(self),self.notes.cget('font'),maximum=9))
            self.notes_frame.pack(fill='both',expand=True,padx=16,pady=(0,8),before=self.footer)
        if progress:self.progress.pack(fill='x',padx=16,pady=(0,10),before=self.footer)
        content_show(self,self.app,width=410 if notes else 360,min_height=125,max_height=360)
    def worker(self,operation):
        self.busy=True;enable_button(self.button,False)
        def run():
            try:self.events.put(('done',operation()))
            except Exception as exc:self.events.put(('error',str(exc)))
        threading.Thread(target=run,daemon=True,name='ManualUpdate').start()
    def check(self):
        if self.busy:return
        self.label.config(text='正在检查更新…\n当前版本 v'+VERSION);self.layout();self.worker(lambda:('release',release_update.check(VERSION)))
    def fetch(self):
        if self.busy:return
        self.label.config(text='正在下载并校验安装包…')
        self.progress['value']=0;self.layout(progress=True)
        self.worker(lambda:('package',release_update.download(self.release,self.cancel,lambda n,t:self.events.put(('progress',n/t*100)))))
    def receive(self):
        try:
            for _ in range(100):
                kind,value=self.events.get_nowait()
                if kind=='progress':self.progress['value']=value;continue
                self.busy=False;enable_button(self.button,True)
                if kind=='error':
                    self.label.config(text='更新未完成：'+value[:150]);self.button.config(text='重新检查',command=self.check);self.layout();continue
                kind,value=value
                if kind=='release':
                    self.release=value
                    self.label.config(text=f'发现新版本 {value["tag"]}' if value else f'暂无更新\n当前版本 v{VERSION}')
                    self.notes.config(state='normal');self.notes.delete('1.0','end');self.notes.insert('1.0',value['notes'] if value else '无需更新。');self.notes.config(state='disabled')
                    self.button.config(text='下载更新' if value else '重新检查',command=self.fetch if value else self.check)
                    self.layout(notes=bool(value))
                else:
                    self.path=value;self.label.config(text='下载完成，SHA256 校验通过。安装向导将保留现有配置。')
                    self.button.config(text='安装更新',command=self.install)
                    self.layout()
        except queue.Empty:pass
        self.poll=self.after(100,self.receive)
    def install(self):
        app=self.app
        if app.engine.is_running() or getattr(app,'_actions_inflight',0) or getattr(app.automation,'watchers',{}) or any(j.get('enabled') for j in app.automation.jobs):
            messagebox.showinfo('请先处理运行中的安排','请先停止当前计时，并停用高级任务，再安装更新。',parent=self);return
        settings=getattr(app,'_settings_win',None)
        if settings and settings.winfo_exists() and settings.dirty:
            messagebox.showinfo('请先保存设置','请先保存或放弃设置中的更改，再安装更新。',parent=self);return
        if not messagebox.askokcancel('安装更新','即将关闭本程序并打开安装向导。完成安装后可重新启动。',parent=self):return
        if app.engine.is_running() or getattr(app,'_actions_inflight',0):return
        try:
            import hashlib
            if not self.path or hashlib.sha256(self.path.read_bytes()).hexdigest()!=self.release['sha256']:
                raise OSError('安装包已改变，请重新下载')
            subprocess.Popen([str(self.path)],cwd=str(self.path.parent))
        except OSError as exc:messagebox.showerror('无法启动安装向导',str(exc),parent=self);return
        self.path=None  # The installation wizard owns the verified file now.
        self.destroy();app.quit_app()
    def destroy(self):
        self.cancel.set()
        if getattr(self,'poll',None):self.after_cancel(self.poll);self.poll=None
        if self.path:
            try:self.path.unlink(missing_ok=True);self.path.parent.rmdir()
            except OSError:pass
        super().destroy()

def open_update(app,parent):
    current=getattr(app,'_update_window',None)
    if current is not None and current.winfo_exists():current.lift();return
    app._update_window=UpdateWindow(app,parent)
