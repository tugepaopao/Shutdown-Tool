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
    """Small independent capsule with a fixed warm palette."""
    def __init__(self,app):
        super().__init__(app.root);self.withdraw();self.app=app;self.overrideredirect(True);self.attributes('-toolwindow',True);self.drag=None
        from ui_cozy import scale
        self.s=scale(self);self.panel_width=round(220*self.s);self.panel_height=round(76*self.s)
        self._last_draw=None;app.cfg['float_docked']=False
        self._theme_fixed=True;self.configure(bg='#FFF9EF');self.body=tk.Canvas(self,bg='#FFF9EF',highlightthickness=0);self.body._theme_fixed=True;self.body.pack(fill='both',expand=True)
        # Text properties remain available to localization and regression checks.
        self.title_label=tk.Label(self);self.clock=tk.Label(self);self.state_label=tk.Label(self)
        from theme import flat_button
        self.pause=flat_button(self,'',self.pause_timer,kind='ghost',padx=3,pady=2,font=theme.font(delta=-1))
        self.cancel=flat_button(self,'×',self.cancel_timer,kind='ghost',padx=3,pady=2,font=theme.font(bold=True))
        for widget in (self.title_label,self.clock,self.state_label,self.pause,self.cancel):widget._theme_fixed=True
        for widget in (self.pause,self.cancel):
            widget._fixed_accent='#CB772B';widget._fixed_ink='#533C2B';widget.configure(bg='#FFF9EF',fg='#765338',activebackground='#F3E8D5',disabledforeground='#A68D72')
        for widget in (self,self.body):
            widget.bind('<ButtonPress-1>',self.begin_drag);widget.bind('<B1-Motion>',self.drag_to);widget.bind('<ButtonRelease-1>',self.end_drag)
        self.bind('<Map>',lambda e:self._hide_from_taskbar() if e.widget is self else None,add='+')
        self.body.bind('<Double-Button-1>',lambda e:app.show_window())
        if app.cfg.get('float_positioned'):
            x,y=app.cfg.get('float_x',0),app.cfg.get('float_y',0)
        else:
            center=(app.root.winfo_rootx()+app.root.winfo_width()//2,app.root.winfo_rooty()+app.root.winfo_height()//2)
            left,top,right,bottom=self.area(*center)
            margin=round(16*self.s)
            x,y=right-self.panel_width-margin,top+margin
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

        T=self.app.T;engine=self.app.engine;running=engine.is_running();paused=engine.paused
        self.attributes('-alpha',max(.4,min(1,self.app.cfg.get('float_opacity',100)/100)));self.attributes('-topmost',bool(self.app.cfg.get('float_topmost',True)))
        title=self.app.describe_action(self.app._active_task or {'action':self.app._current_action()}) if running else T('float_title')
        remain=max(0,math.ceil(engine.remaining())) if running else 0;days,remain=divmod(remain,86400);hours,remain=divmod(remain,3600);minutes,seconds=divmod(remain,60)
        clock=(f'{days}d ' if days else '')+f'{hours:02}:{minutes:02}:{seconds:02}' if running else '--:--:--'
        state=T('float_paused' if paused and running else 'float_running' if running else 'float_idle')
        self.title_label.configure(text=title);self.clock.configure(text=clock);self.state_label.configure(text=state)
        if getattr(self,'_pause_state',None)!=(running,paused):
            self._pause_state=(running,paused);s=self.s;icon=Image.new('RGBA',(round(16*s),round(16*s)));d=ImageDraw.Draw(icon);ink='#765338'
            if paused:d.polygon([(5*s,3*s),(5*s,13*s),(12*s,8*s)],fill=ink)
            else:
                for x in (5,10):d.rounded_rectangle((x*s,4*s,(x+2)*s,12*s),radius=s/2,fill=ink)
            self.pause._theme_photo=ImageTk.PhotoImage(icon,master=self)
        self.pause.configure(text=T('btn_resume_s' if paused else 'btn_pause_s'),image=self.pause._theme_photo,compound='none')
        for widget in (self.pause,self.cancel):widget.configure(state='normal' if running else 'disabled',bg='#FFF9EF',fg='#765338',disabledforeground='#A68D72',cursor='hand2' if running else 'arrow')
        total=getattr(engine,'_total',0);target=max(0,min(100,(1-engine.remaining()/total)*100)) if running and total else 0
        self._smooth=getattr(self,'_smooth',target)+(target-getattr(self,'_smooth',target))*.55
        key=(clock,title,state,round(self._smooth,1),running,paused)
        if key==self._last_draw:return
        self._last_draw=key;w,h=self._dimensions;s=self.s
        im=plate(w,h,'#FFF9EF','#DFC6A5',None,radius=h//2,raised=False,base='#FFF9EF')
        d=ImageDraw.Draw(im);small=pil_font(round(11*s));big=pil_font(round(17*s),True)
        def fit(text,font,width):
            if d.textlength(text,font=font)<=width:return text
            while text and d.textlength(text+'…',font=font)>width:text=text[:-1]
            return text+'…'
        # The left clock stays distinct; the supplied cat occupies the empty right.
        cx,cy,r=32*s,38*s,18*s
        d.ellipse((cx-r,cy-r,cx+r,cy+r),outline='#F0DEC3',width=max(1,round(s)))
        if running and self._smooth>0:d.arc((cx-r,cy-r,cx+r,cy+r),-90,-90+3.6*self._smooth,fill='#CB772B',width=max(2,round(2*s)))
        cr=7*s;d.ellipse((cx-cr,cy-cr,cx+cr,cy+cr),outline='#D47B29',width=max(2,round(1.5*s)))
        d.line([(cx,cy-4*s),(cx,cy),(cx+3*s,cy+2*s)],fill='#D47B29',width=max(2,round(1.5*s)))
        if not hasattr(self,'_cat_art'):
            from i18n import resource_path
            with Image.open(resource_path('assets/ui/floating-cat.png')) as image:self._cat_art=image.convert('RGBA')
            self._cat_art.thumbnail((round(56*s),round(28*s)),Image.Resampling.LANCZOS)
        cat=self._cat_art;self._cat_box=(round(157*s),round(7*s),round(157*s)+cat.width,round(7*s)+cat.height)
        im.paste(cat,self._cat_box[:2],cat)
        d=ImageDraw.Draw(im)
        d.text((65*s,10*s),fit(title,small,86*s),font=small,fill='#82654C',anchor='lt')
        # Shrink long multi-day countdowns, rather than truncating useful digits.
        while d.textlength(clock,font=big)>88*s and big.size>round(11*s):big=pil_font(big.size-1,True)
        d.text((65*s,29*s),clock,font=big,fill='#533C2B',anchor='lt')
        short=T('float_short_paused' if paused and running else 'float_short_running' if running else 'float_ready')
        d.text((65*s,53*s),fit(short,small,80*s),font=small,fill='#82654C',anchor='lt')
        self._image=im;self._photo=ImageTk.PhotoImage(im,master=self);self.body.configure(bg='#FFF9EF');self.body.delete('all');self.body.create_image(0,0,image=self._photo,anchor='nw')

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
