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
    """Small capsule with top-edge docking. Independent of the main window."""
    def __init__(self,app):
        super().__init__(app.root);self.withdraw();self.app=app;self.overrideredirect(True);self.attributes('-toolwindow',True);self.drag=None
        from ui_cozy import scale
        self.s=scale(self);self.panel_width=round(220*self.s);self.panel_height=round(76*self.s)
        self._last_draw=None;app.cfg['float_docked']=False
        self.configure(bg=theme.c('card'));self.body=tk.Canvas(self,bg=theme.c('card'),highlightthickness=0);self.body.pack(fill='both',expand=True)
        # Text properties remain available to localization and regression checks.
        self.title_label=tk.Label(self);self.clock=tk.Label(self);self.state_label=tk.Label(self)
        from theme import flat_button
        self.pause=flat_button(self,'',self.pause_timer,kind='ghost',padx=3,pady=2,font=theme.font(delta=-1))
        self.cancel=flat_button(self,'×',self.cancel_timer,kind='ghost',padx=3,pady=2,font=theme.font(bold=True))
        for widget in (self,self.body):
            widget.bind('<ButtonPress-1>',self.begin_drag);widget.bind('<B1-Motion>',self.drag_to);widget.bind('<ButtonRelease-1>',self.end_drag)
        self.bind('<Map>',lambda e:self._hide_from_taskbar() if e.widget is self else None,add='+')
        self.body.bind('<Double-Button-1>',lambda e:app.show_window())
        x=app.cfg.get('float_x',0) if app.cfg.get('float_positioned') else app.root.winfo_rootx()+30
        y=app.cfg.get('float_y',0) if app.cfg.get('float_positioned') else app.root.winfo_rooty()+90
        self.position=(x,y);self._resize();self.move(x,y);self.refresh();self._hide_from_taskbar();self.deiconify()
    def _hide_from_taskbar(self):
        # Tool window style hides both the taskbar button and Alt+Tab entry.
        # Do not make this transient: it must survive main-window minimization.
        u=ctypes.windll.user32
        u.GetAncestor.argtypes=[ctypes.c_void_p,ctypes.c_uint];u.GetAncestor.restype=ctypes.c_void_p
        hwnd=u.GetAncestor(self.winfo_id(),2)
        if not hwnd or hwnd==self.winfo_id():return
        u.GetWindowLongW.argtypes=[ctypes.c_void_p,ctypes.c_int];u.GetWindowLongW.restype=ctypes.c_long
        u.SetWindowLongW.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_long]
        ex=u.GetWindowLongW(hwnd,-20);u.SetWindowLongW(hwnd,-20,(ex|0x80)&~0x40000)
        u.SetWindowPos.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_uint]
        u.SetWindowPos(hwnd,None,0,0,0,0,0x37)
    def area(self,x,y):return min(workareas(self.app.root),key=lambda a:max(a[0]-x,0,x-a[2])**2+max(a[1]-y,0,y-a[3])**2)
    def _resize(self):
        w,h=self.panel_width,self.panel_height
        self.geometry(f'{w}x{h}');self._dimensions=(w,h);self.body.configure(width=w,height=h)
        self.pause.place(x=round(153*self.s),y=round(45*self.s),width=round(29*self.s),height=round(26*self.s))
        self.cancel.place(x=round(183*self.s),y=round(45*self.s),width=round(29*self.s),height=round(26*self.s))
        self.update_idletasks();self._round();self._last_draw=None
    def _round(self):
        try:
            u=ctypes.windll.user32;g=ctypes.windll.gdi32;u.GetAncestor.restype=ctypes.c_void_p;u.GetAncestor.argtypes=[ctypes.c_void_p,ctypes.c_uint]
            hwnd=u.GetAncestor(self.winfo_id(),2) or self.winfo_id();w,h=self._dimensions
            g.CreateRoundRectRgn.argtypes=[ctypes.c_int]*6;g.CreateRoundRectRgn.restype=ctypes.c_void_p
            u.SetWindowRgn.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_bool]
            region=g.CreateRoundRectRgn(0,0,w+1,h+1,h,h)
            if not u.SetWindowRgn(hwnd,region,True):g.DeleteObject(ctypes.c_void_p(region))
        except (OSError,AttributeError):pass
    def move(self,x,y):
        x,y=clamp_position(x,y,*self._dimensions,workareas(self.app.root));self.geometry(f'+{x}+{y}');self.position=(x,y)
    def begin_drag(self,event):
        self.drag=(event.x_root,event.y_root,*self.position)
    def drag_to(self,event):
        if self.drag:
            mx,my,x,y=self.drag;self.move(x+event.x_root-mx,y+event.y_root-my)
    def end_drag(self,event):
        if not self.drag:return
        self.drag=None;self.save_position();self.refresh()
    def save_position(self):
        self.app.cfg.update(dict(float_x=self.position[0],float_y=self.position[1],float_positioned=True,float_docked=False));self.app.cfg.save()
    def pause_timer(self):
        if self.app.engine.is_running():self.app.toggle_pause();self.refresh()
    def cancel_timer(self):
        if self.app.engine.is_running():self.app.stop_timer();self.refresh()
    def refresh(self):
        from PIL import Image,ImageDraw,ImageTk
        from ui_cozy import plate,pil_font
        from ui_summary import control_icon
        T=self.app.T;engine=self.app.engine;running=engine.is_running();paused=engine.paused
        self.attributes('-alpha',max(.4,min(1,self.app.cfg.get('float_opacity',100)/100)));self.attributes('-topmost',bool(self.app.cfg.get('float_topmost',True)))
        title=self.app.describe_action(self.app._active_task or {'action':self.app._current_action()}) if running else T('float_title')
        remain=max(0,math.ceil(engine.remaining())) if running else 0;days,remain=divmod(remain,86400);hours,remain=divmod(remain,3600);minutes,seconds=divmod(remain,60)
        clock=(f'{days}d ' if days else '')+f'{hours:02}:{minutes:02}:{seconds:02}' if running else '--:--:--'
        state=T('float_paused' if paused and running else 'float_running' if running else 'float_idle')
        self.title_label.configure(text=title);self.clock.configure(text=clock);self.state_label.configure(text=state)
        self.pause._theme_photo=control_icon(self.app,paused);self.pause.configure(text=T('btn_resume_s' if paused else 'btn_pause_s'),image=self.pause._theme_photo,compound='none')
        enable_button(self.pause,running);enable_button(self.cancel,running)
        total=getattr(engine,'_total',0);target=max(0,min(100,(1-engine.remaining()/total)*100)) if running and total else 0
        self._smooth=getattr(self,'_smooth',target)+(target-getattr(self,'_smooth',target))*.55
        key=(clock,title,state,theme.accent,round(self._smooth,1),running,paused)
        if key==self._last_draw:return
        self._last_draw=key;w,h=self._dimensions;s=self.s
        im=Image.new('RGB',(w,h),theme.c('card'))
        d=ImageDraw.Draw(im);small=pil_font(round(11*s));big=pil_font(round(18*s),True)
        def fit(text,font,width):
            if d.textlength(text,font=font)<=width:return text
            while text and d.textlength(text+'…',font=font)>width:text=text[:-1]
            return text+'…'
        # Supersampled rounded progress ring avoids jagged native GDI arcs.
        ring=Image.new('RGBA',(168,168));rd=ImageDraw.Draw(ring);rd.ellipse((9,9,159,159),outline=theme.c('divider'),width=10)
        if running:
            extent=max(2,min(359.9,self._smooth*3.6));pts=[]
            for i in range(max(2,math.ceil(extent/4))+1):
                angle=math.radians(-90+extent*i/max(2,math.ceil(extent/4)));pts.append((84+75*math.cos(angle),84+75*math.sin(angle)))
            rd.line(pts,fill=theme.accent,width=10,joint='curve')
            for px,py in (pts[0],pts[-1]):rd.ellipse((px-5,py-5,px+5,py+5),fill=theme.accent)
        ring=ring.resize((round(44*s),round(44*s)),Image.Resampling.LANCZOS);im.paste(ring,(round(10*s),round(16*s)),ring)
        from ui_cozy import cozy_icon
        center_icon=cozy_icon(self,'pause' if paused and running else 'clock',round(20*s))
        center_image=ImageTk.getimage(center_icon).convert('RGBA');im.paste(center_image,(round(22*s),round(28*s)),center_image)
        d=ImageDraw.Draw(im)
        d.text((65*s,10*s),fit(title,small,143*s),font=small,fill=theme.c('fg_dim'),anchor='lt')
        d.text((65*s,29*s),fit(clock,big,143*s),font=big,fill=theme.c('fg'),anchor='lt')
        short=T('float_short_paused' if paused and running else 'float_short_running' if running else 'float_ready')
        d.text((65*s,53*s),fit(short,small,80*s),font=small,fill=theme.c('fg_dim'),anchor='lt')
        self._photo=ImageTk.PhotoImage(im,master=self);self.body.configure(bg=theme.c('card'));self.body.delete('all');self.body.create_image(0,0,image=self._photo,anchor='nw')

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
        self.job=self.app.root.after(100,self.tick)
    def apply(self):
        if self.job:self.app.root.after_cancel(self.job);self.job=None
        self.tick()
    def close(self):
        self.closed=True
        if self.job:self.app.root.after_cancel(self.job);self.job=None
        if self.window and self.window.winfo_exists():self.window.destroy()
        self.window=None
