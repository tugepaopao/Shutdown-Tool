"""Independent, draggable countdown window; uses the existing timer only."""
import ctypes,math,tkinter as tk
from ctypes import wintypes as W
from theme import theme,enable_button
from ui_window import button_grid
from ui_summary import ProgressStrip

def workareas(root):
    areas=[]
    try:
        u=ctypes.windll.user32
        class Info(ctypes.Structure):_fields_=[('size',W.DWORD),('monitor',W.RECT),('work',W.RECT),('flags',W.DWORD)]
        callback=ctypes.WINFUNCTYPE(W.BOOL,W.HMONITOR,W.HDC,ctypes.POINTER(W.RECT),W.LPARAM)
        u.GetMonitorInfoW.argtypes=[W.HMONITOR,ctypes.POINTER(Info)]
        def visit(handle,dc,rect,data):
            info=Info();info.size=ctypes.sizeof(info)
            if u.GetMonitorInfoW(handle,ctypes.byref(info)):areas.append((info.work.left,info.work.top,info.work.right,info.work.bottom))
            return True
        u.EnumDisplayMonitors(None,None,callback(visit),0)
    except (OSError,AttributeError):pass
    return areas or [(0,0,root.winfo_screenwidth(),root.winfo_screenheight())]

def clamp_position(x,y,width,height,areas):
    area=min(areas,key=lambda a:max(a[0]-x,0,x-a[2])**2+max(a[1]-y,0,y-a[3])**2)
    left,top,right,bottom=area
    return int(max(left,min(x,right-width))),int(max(top,min(y,bottom-height)))

class FloatingWindow(tk.Toplevel):
    def __init__(self,app):
        super().__init__(app.root);self.withdraw();self.app=app;self.overrideredirect(True);self.drag=None
        self.configure(bg=theme.c('card'),highlightthickness=1,highlightbackground=theme.c('card_border'))
        self.body=tk.Frame(self,bg=theme.c('card'));self.body.pack(fill='both',expand=True,padx=12,pady=10)
        self.title_label=tk.Label(self.body,bg=theme.c('card'),fg=theme.c('fg'),font=theme.font(bold=True),anchor='w');self.title_label.pack(fill='x')
        self.clock=tk.Label(self.body,bg=theme.c('card'),fg=theme.accent,font=theme.font(delta=16,bold=True),anchor='w');self.clock.pack(fill='x',pady=(3,0))
        self.state_label=tk.Label(self.body,bg=theme.c('card'),fg=theme.c('fg_dim'),font=theme.font(),anchor='w');self.state_label.pack(fill='x',pady=(0,7))
        self.progress=ProgressStrip(self.body);self.progress.pack(fill='x',pady=(0,8))
        self.bar=tk.Frame(self.body,bg=theme.c('card'));self.bar.pack(fill='x')
        self.pause,self.cancel=button_grid(self.bar,[('',self.pause_timer,'normal'),('',self.cancel_timer,'normal')])
        for widget in (self,self.body,self.title_label,self.clock,self.state_label):
            widget.bind('<ButtonPress-1>',self.begin_drag);widget.bind('<B1-Motion>',self.drag_to);widget.bind('<ButtonRelease-1>',self.end_drag)
        self.refresh();self.update_idletasks()
        self.panel_width=max(350,self.winfo_reqwidth());self.panel_height=max(190,self.winfo_reqheight())
        self.geometry(f'{self.panel_width}x{self.panel_height}');self.update_idletasks()
        x=app.cfg.get('float_x',0) if app.cfg.get('float_positioned') else app.root.winfo_rootx()+30
        y=app.cfg.get('float_y',0) if app.cfg.get('float_positioned') else app.root.winfo_rooty()+90
        self.move(x,y);self.refresh();self.deiconify()
    def move(self,x,y):
        width=max(self.panel_width,self.winfo_width());height=max(self.panel_height,self.winfo_height())
        x,y=clamp_position(x,y,width,height,workareas(self.app.root));self.geometry(f'+{x}+{y}');self.position=(x,y)
    def begin_drag(self,event):self.drag=(event.x_root,event.y_root,*self.position)
    def drag_to(self,event):
        if self.drag:
            mx,my,x,y=self.drag;self.move(x+event.x_root-mx,y+event.y_root-my)
    def end_drag(self,event):
        if not self.drag:return
        self.drag=None;self.app.cfg.update(dict(float_x=self.position[0],float_y=self.position[1],float_positioned=True));self.app.cfg.save()
    def pause_timer(self):
        if self.app.engine.is_running():self.app.toggle_pause();self.refresh()
    def cancel_timer(self):
        if self.app.engine.is_running():self.app.stop_timer();self.refresh()
    def refresh(self):
        T=self.app.T;engine=self.app.engine;running=engine.is_running();paused=engine.paused
        self.attributes('-alpha',max(.4,min(1,self.app.cfg.get('float_opacity',100)/100)));self.attributes('-topmost',bool(self.app.cfg.get('float_topmost',True)))
        self.configure(bg=theme.c('card'),highlightbackground=theme.c('card_border'))
        self.body.configure(bg=theme.c('card'));self.bar.configure(bg=theme.c('card'))
        for widget in (self.title_label,self.clock,self.state_label):widget.configure(bg=theme.c('card'))
        title=self.app.describe_action(self.app._active_task or {'action':self.app._current_action()}) if running else T('float_title')
        self.title_label.configure(text=title,fg=theme.c('fg'))
        remain=max(0,math.ceil(engine.remaining())) if running else 0;days,remain=divmod(remain,86400);hours,remain=divmod(remain,3600);minutes,seconds=divmod(remain,60)
        self.clock.configure(text=(f'{days}d ' if days else '')+f'{hours:02}:{minutes:02}:{seconds:02}' if running else '— — : — —',fg=theme.accent)
        self.state_label.configure(text=T('float_paused' if paused and running else 'float_running' if running else 'float_idle'),fg=theme.c('fg_dim'))
        self.pause.configure(text=T('btn_resume_s' if paused else 'btn_pause_s'));self.cancel.configure(text=T('float_cancel'))
        enable_button(self.pause,running);enable_button(self.cancel,running)
        total=getattr(engine,'_total',0);self.progress.configure(value=max(0,min(100,(1-engine.remaining()/total)*100)) if running and total else 0)

class FloatingController:
    def __init__(self,app):self.app=app;self.window=None;self.job=None;self.closed=False;app.root.bind("<Destroy>",lambda event:self.close() if event.widget is app.root else None,add="+");self.tick()
    def tick(self):
        self.job=None
        if self.closed:return
        if self.app.cfg.get('float_enabled'):
            if self.window is None or not self.window.winfo_exists():self.window=FloatingWindow(self.app)
            self.window.refresh()
        elif self.window is not None:
            if self.window.winfo_exists():self.window.destroy()
            self.window=None
        self.job=self.app.root.after(500,self.tick)
    def apply(self):
        if self.job:self.app.root.after_cancel(self.job);self.job=None
        self.tick()
    def close(self):
        self.closed=True
        if self.job:self.app.root.after_cancel(self.job);self.job=None
        if self.window and self.window.winfo_exists():self.window.destroy()
        self.window=None
