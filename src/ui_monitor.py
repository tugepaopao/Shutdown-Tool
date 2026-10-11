"""Compact monitor page, sampled only while this settings page is selected."""
import tkinter as tk
from tkinter import ttk
from theme import theme
from ui_cozy import CozyFrame
from ui_summary import ProgressStrip
from system_metrics import Sampler,size

class MonitorPanel(tk.Frame):
    def __init__(self,parent,settings):
        super().__init__(parent,bg=theme.c('bg'));self.pack(fill='both',expand=True,padx=10,pady=10);self.settings=settings;self.sampler=None;self.poll_id=None;self.last={};self.labels={};self.bars={}
        for key in ('cpu','memory','disk','network','uptime'):
            box=CozyFrame(self,bg=theme.c('card'),highlightthickness=1,highlightbackground=theme.c('card_border'));box.pack(fill='x',pady=(0,8))
            row=tk.Frame(box,bg=theme.c('card'));row.pack(fill='x',padx=10,pady=(8,5))
            title=tk.Label(row,text=settings.T('mon_'+key),bg=theme.c('card'),fg=theme.c('fg'),font=theme.font(bold=True),anchor='w');title.pack(side='left')
            value=tk.Label(row,text='—',bg=theme.c('card'),fg=theme.accent,font=theme.font(),anchor='e');value.pack(side='right');self.labels[key]=value
            if key in ('cpu','memory','disk'):
                bar=ProgressStrip(box);bar.pack(fill='x',padx=10,pady=(0,10));self.bars[key]=bar
            if key=='disk':
                import ctypes
                mask=ctypes.windll.kernel32.GetLogicalDrives()
                options=[f'{chr(n)}:\\' for n in range(65,91) if mask&(1<<(n-65)) and ctypes.windll.kernel32.GetDriveTypeW(f'{chr(n)}:\\') in (3,6)]
                self.drive=tk.StringVar(value=__import__('os').environ.get('SystemDrive','C:')+'\\')
                selector=ttk.Combobox(box,textvariable=self.drive,values=options,state='readonly',width=9);selector.pack(anchor='w',padx=10,pady=(0,8));selector.bind('<<ComboboxSelected>>',lambda e:self.change_drive())
        tk.Label(self,text=settings.T('mon_hint'),bg=theme.c('bg'),fg=theme.c('fg_muted'),font=theme.font(),justify='left',wraplength=440,anchor='w').pack(fill='x',pady=(2,0))
        self.bind('<Destroy>',self.destroyed,add='+')
    def change_drive(self):
        if self.sampler:self.sampler.drive=self.drive.get()
    def set_active(self,active):
        if active and self.sampler is None:
            self.sampler=Sampler();self.change_drive();self.sampler.start();self.poll()
        elif not active and self.sampler is not None:
            self.sampler.close();self.sampler=None
            if self.poll_id:
                self.after_cancel(self.poll_id);self.poll_id=None
    def destroyed(self,event):
        if event.widget is self:self.set_active(False)
    def poll(self):
        self.poll_id=None
        if self.sampler is None:return
        try:self.last=self.sampler.results.get_nowait()
        except __import__('queue').Empty:pass
        self.render();self.poll_id=self.after(250,self.poll)
    def render(self):
        data=self.last;cpu=data.get('cpu');mem=data.get('memory');disk=data.get('disk')
        for key,value in [('cpu',cpu),('memory',mem.percent if mem else None),('disk',disk.percent if disk else None)]:
            self.bars[key].configure(value=value or 0)
        self.labels['cpu'].configure(text=f'{cpu:.0f}%' if cpu is not None else '—',fg=theme.accent)
        for key,value in [('memory',mem),('disk',disk)]:
            self.labels[key].configure(text=f'{size(value.used)} / {size(value.total)} · {value.percent:.0f}%' if value else '—',fg=theme.accent)
        down,up=data.get('download'),data.get('upload')
        self.labels['network'].configure(text=f'↓ {size(down)}/s    ↑ {size(up)}/s' if down is not None and up is not None else '—',fg=theme.accent)
        elapsed=data.get('uptime')
        self.labels['uptime'].configure(text=f'{int(elapsed)//86400} d  {int(elapsed)%86400//3600:02}:{int(elapsed)%3600//60:02}:{int(elapsed)%60:02}' if elapsed is not None else '—',fg=theme.accent)
