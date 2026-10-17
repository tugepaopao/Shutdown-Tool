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
    """Live illustrated countdown, drawn over the supplied glass capsule artwork."""
    def __init__(self,app):
        super().__init__(app.root);self.withdraw();self.app=app;self.overrideredirect(True);self.attributes('-toolwindow',True);self.drag=None
        from ui_cozy import scale
        from PIL import Image
        import sys
        from pathlib import Path
        self.s=scale(self);asset=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent.parent))/'assets/ui/violet_float.png'
        with Image.open(asset) as image:self.art=image.convert('RGBA')
        self.panel_width=round(420*self.s);self.panel_height=round(self.panel_width*self.art.height/self.art.width);self._dimensions=(self.panel_width,self.panel_height)
        self.art=self.art.resize(self._dimensions,Image.Resampling.LANCZOS);self._last_draw=None;self._theme_fixed=True;self.configure(bg='#202060')
        self.body=tk.Canvas(self,bg='#202060',highlightthickness=0);self.body._theme_fixed=True;self.body.pack(fill='both',expand=True)
        self.title_label=tk.Label(self);self.clock=tk.Label(self);self.state_label=tk.Label(self)
        self.pause=tk.Button(self,command=self.pause_timer);self.cancel=tk.Button(self,command=self.cancel_timer)
        for widget in (self.title_label,self.clock,self.state_label,self.pause,self.cancel):widget._theme_fixed=True
        self.geometry(f'{self.panel_width}x{self.panel_height}')
        for widget in (self,self.body):
            widget.bind('<ButtonPress-1>',self.begin_drag);widget.bind('<B1-Motion>',self.drag_to);widget.bind('<ButtonRelease-1>',self.end_drag)
        self.body.bind('<Double-Button-1>',lambda e:app.show_window())
        self.bind('<Map>',lambda e:self.after_idle(self._present) if e.widget is self else None,add='+')
        self.update_idletasks()
        if app.cfg.get('float_positioned'):x,y=app.cfg.get('float_x',0),app.cfg.get('float_y',0)
        else:
            cx=app.root.winfo_rootx()+app.root.winfo_width()//2;cy=app.root.winfo_rooty()+app.root.winfo_height()//2
            left,top,right,bottom=self.area(cx,cy);x=right-round((right-left)*.1)-self.panel_width;y=top+round((bottom-top)*.1)
        self.position=clamp_position(x,y,*self._dimensions,workareas(app.root));self.geometry(f'+{self.position[0]}+{self.position[1]}');self.refresh();self.deiconify();self._present()
    def _present(self):
        if not self.winfo_exists() or not hasattr(self,'_image'):return
        from ui_float_surface import present
        present(self,self._image,round(255*max(.4,min(1,self.app.cfg.get('float_opacity',100)/100))))
    def area(self,x,y):return min(workareas(self.app.root),key=lambda a:max(a[0]-x,0,x-a[2])**2+max(a[1]-y,0,y-a[3])**2)
    def move(self,x,y):
        self.position=clamp_position(x,y,*self._dimensions,workareas(self.app.root));self.geometry(f'+{self.position[0]}+{self.position[1]}')
        # Only move the existing composited surface during drag.
    def hit(self,event):
        w,h=self._dimensions
        for key,cx in [('pause',.782),('cancel',.870)]:
            if ((event.x-cx*w)/(.037*w))**2+((event.y-.715*h)/(.105*h))**2<=1:return key
        return None
    def begin_drag(self,event):
        self._pressed=self.hit(event)
        if not self._pressed:self.drag=(event.x_root,event.y_root,*self.position)
    def drag_to(self,event):
        if self.drag:
            mx,my,x,y=self.drag;self.move(x+event.x_root-mx,y+event.y_root-my)
    def end_drag(self,event):
        pressed=getattr(self,'_pressed',None);self._pressed=None
        if pressed and self.hit(event)==pressed:
            self.pause_timer() if pressed=='pause' else self.cancel_timer()
        if self.drag:self.drag=None;self.save_position()
    def save_position(self):
        self.app.cfg.update(dict(float_x=self.position[0],float_y=self.position[1],float_positioned=True,float_docked=False));self.app.cfg.save()
    def pause_timer(self):
        if self.app.engine.is_running():self.app.toggle_pause();self.refresh()
    def cancel_timer(self):
        if self.app.engine.is_running():self.app.stop_timer();self.refresh()
    def refresh(self):
        from PIL import Image,ImageDraw,ImageFilter
        from ui_cozy import pil_font
        engine=self.app.engine;running=engine.is_running();paused=engine.paused;T=self.app.T
        title=T('float_title');remain=max(0,math.ceil(engine.remaining())) if running else 0;days,remain=divmod(remain,86400);hours,remain=divmod(remain,3600);minutes,seconds=divmod(remain,60)
        clock=(f'{days}d ' if days else '')+f'{hours:02}:{minutes:02}:{seconds:02}' if running else '--:--:--'
        state=T('float_short_paused' if running and paused else 'float_short_running' if running else 'float_ready')
        self.title_label.configure(text=title);self.clock.configure(text=clock);self.state_label.configure(text=state)
        self.pause.configure(state='normal' if running else 'disabled');self.cancel.configure(state='normal' if running else 'disabled')
        topmost=bool(self.app.cfg.get('float_topmost',False))
        if getattr(self,'_topmost_state',None)!=topmost:
            self.attributes('-topmost',topmost);self._topmost_state=topmost
        key=(clock,title,state,paused,running,self.app.cfg.get('float_opacity',100))
        if key==self._last_draw:return
        self._last_draw=key;w,h=self._dimensions;im=self.art.copy();ink=Image.new('RGBA',im.size);d=ImageDraw.Draw(ink)
        def text(value,y,size,bold=False):
            font=pil_font(round(size*self.s),bold)
            while d.textlength(value,font=font)>w*.26 and font.size>8:font=pil_font(font.size-1,bold)
            d.text((w*.405,h*y),value,font=font,fill='#FFFFFF',anchor='mm')
        text(title,.31,13);text(clock,.515,24,True);text(state,.765,12)
        cx=w*.782;cy=h*.715;r=w*.010
        if paused and running:d.polygon([(cx-r,cy-r*1.5),(cx-r,cy+r*1.5),(cx+r*1.5,cy)],fill='white')
        else:
            for x in (cx-r,cx+r*.35):d.rounded_rectangle((x,cy-r*1.5,x+r*.65,cy+r*1.5),radius=max(1,r*.3),fill='white')
        cx=w*.870;r=w*.012;d.line([(cx-r,cy-r),(cx+r,cy+r)],fill='white',width=max(2,round(3*self.s)));d.line([(cx-r,cy+r),(cx+r,cy-r)],fill='white',width=max(2,round(3*self.s)))
        glow=ink.filter(ImageFilter.GaussianBlur(2*self.s));im=Image.alpha_composite(im,glow);im=Image.alpha_composite(im,ink)
        self._image=im;self._present()

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
        # Disabled windows have no polling job; settings/shortcuts call apply().
        if self.app.cfg.get("float_enabled"):
            self.job=self.app.root.after(250,self.tick)
    def apply(self):
        if self.job:self.app.root.after_cancel(self.job);self.job=None
        self.tick()
    def close(self):
        self.closed=True
        if self.job:self.app.root.after_cancel(self.job);self.job=None
        if self.window and self.window.winfo_exists():self.window.destroy()
        self.window=None
