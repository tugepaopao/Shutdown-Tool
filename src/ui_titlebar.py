"""Client title bar with native taskbar/minimize and resize behavior."""
import ctypes
import tkinter as tk
from theme import theme,flat_button
from ui_cozy import cozy_icon,scale

def apply_chrome(root):
    try:
        u=ctypes.windll.user32
        u.GetAncestor.argtypes=[ctypes.c_void_p,ctypes.c_uint];u.GetAncestor.restype=ctypes.c_void_p
        hwnd=u.GetAncestor(root.winfo_id(),2)
        if not hwnd or hwnd==root.winfo_id():return
        u.GetWindowLongW.argtypes=[ctypes.c_void_p,ctypes.c_int];u.GetWindowLongW.restype=ctypes.c_long
        u.SetWindowLongW.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_long]
        style=u.GetWindowLongW(hwnd,-16);new=(style & ~0xC00000 & ~0x10000 & ~0x40000)|0x20000|0x80000
        if style!=new:
            u.SetWindowLongW(hwnd,-16,new)
            u.SetWindowPos.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_uint]
            u.SetWindowPos(hwnd,None,0,0,0,0,0x37)
    except (OSError,AttributeError,tk.TclError):pass

def build(app):
    root=app.root;s=scale(root)
    bar=tk.Frame(root,bg=theme.c('bg'));bar.pack(fill='x',padx=14,pady=(8,0));app.titlebar=bar
    power=tk.Label(bar,bg=theme.c('bg'));power._theme_icon=('power_badge',22);power._theme_photo=cozy_icon(root,'power_badge',round(22*s));power.config(image=power._theme_photo);power.pack(side='left',padx=(0,7))
    title=tk.Label(bar,text=app.T('app_name'),bg=theme.c('bg'),fg=theme.c('fg'),font=theme.font(bold=True),anchor='w');title.pack(side='left',fill='x',expand=True);app.title_label=title
    def toggle_pin():
        enabled=not bool(root.attributes('-topmost'));root.attributes('-topmost',enabled);app.cfg['main_topmost']=enabled;app.cfg.save();paint_pin()
    def paint_pin():
        if not app.pin_btn.winfo_exists():return
        enabled=bool(root.attributes('-topmost'));app.pin_btn._kind='ghost';app.pin_btn._bg=theme.c('bg');app.pin_btn.config(bg=app.pin_btn._bg)
    for attr,name,command in [('close_btn','close',app.on_close),('minimize_btn','minimize',root.iconify),('avatar_btn','gear',app._open_avatar_menu),('task_center_btn','document',app.open_queue),('pin_btn','pin',toggle_pin)]:
        b=flat_button(bar,'',command,kind='ghost',padx=4,pady=5);b._title_control=True;b._bare_glyph=True;b._theme_icon=(name,17);b._theme_photo=cozy_icon(root,name,round(17*s));b.config(image=b._theme_photo);b.pack(side='right',padx=2);setattr(app,attr,b)
    app.queue_badge=app.task_center_btn
    root.attributes('-topmost',bool(app.cfg.get('main_topmost',False)));paint_pin()
    app._paint_pin=paint_pin
    # Coalesce pointer input and move the existing HWND. The opaque surface
    # can be reused by DWM without a Tk geometry/layout request on each motion.
    state={'job':None,'pending':None,'origin':None,'edge':''}
    u=ctypes.windll.user32
    u.SetWindowPos.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_uint]
    def flush():
        state['job']=None;pending=state['pending'];state['pending']=None
        if pending is None or not root.winfo_exists():return
        hwnd=u.GetAncestor(root.winfo_id(),2)
        x,y,w,h=pending
        flags=0x14 | (0x1 if state['edge']=='' else 0)
        u.SetWindowPos(hwnd,None,x,y,w,h,flags)
    def rect():
        from ctypes import wintypes as W
        r=W.RECT();u.GetWindowRect(ctypes.c_void_p(u.GetAncestor(root.winfo_id(),2)),ctypes.byref(r));return r.left,r.top,r.right-r.left,r.bottom-r.top
    def begin(e,edge=''):
        state['origin']=(e.x_root,e.y_root,*rect());state['edge']=edge
    def move(e):
        if state['origin'] is None:return
        mx,my,x,y,w,h=state['origin'];dx=e.x_root-mx;dy=e.y_root-my;edge=state['edge']
        if edge:
            minw,minh=root.minsize()
            if 'e' in edge:w=max(minw,w+dx)
            if 's' in edge:h=max(minh,h+dy)
            if 'w' in edge:neww=max(minw,w-dx);x+=w-neww;w=neww
            if 'n' in edge:newh=max(minh,h-dy);y+=h-newh;h=newh
        else:x+=dx;y+=dy
        state['pending']=(x,y,w,h)
        if state['job'] is None:state['job']=root.after(16,flush)
    def end(e=None):
        if state['job'] is not None:root.after_cancel(state['job']);state['job']=None
        if state['pending'] is not None:flush()
        state['origin']=None;state['edge']=''
    for widget in (bar,title,power):
        widget.bind('<ButtonPress-1>',begin);widget.bind('<B1-Motion>',move);widget.bind('<ButtonRelease-1>',end)
    # Keep edge resizing available without the white non-client frame.
    def edge_at(e):
        x=e.x_root-root.winfo_rootx();y=e.y_root-root.winfo_rooty();margin=round(6*s)
        return ('n' if y<margin else 's' if y>=root.winfo_height()-margin else '')+('w' if x<margin else 'e' if x>=root.winfo_width()-margin else '')
    def edge_press(e):
        edge=edge_at(e)
        if edge and any(root.resizable()):begin(e,edge)
    def edge_move(e):
        if state['origin'] is not None and state['edge']:move(e)
    root.bind('<ButtonPress-1>',edge_press,add='+');root.bind('<B1-Motion>',edge_move,add='+');root.bind('<ButtonRelease-1>',end,add='+')
    def dispose(e):
        if e.widget is root and state['job'] is not None:root.after_cancel(state['job']);state['job']=None
    root.bind('<Destroy>',dispose,add='+')
    root.bind('<Map>',lambda e:root.after_idle(lambda:apply_chrome(root)) if e.widget is root else None,add='+')
