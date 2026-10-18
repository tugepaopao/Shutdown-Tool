"""Place transient surfaces beside their invoker on its current monitor."""
def bounds(anchor, width, height, areas, gap=4):
    x,y,w,h=anchor
    left,top,right,bottom=min(areas,key=lambda a:max(a[0]-x,0,x-a[2])**2+max(a[1]-y,0,y-a[3])**2)
    width=min(width,right-left-12);height=min(height,bottom-top-12)
    px=max(left+6,min(x,right-width-6))
    py=y+h+gap
    if py+height>bottom-6:py=y-height-gap
    py=max(top+6,min(py,bottom-height-6))
    return px,py,width,height

def place(window,anchor,icon=False):
    from ui_floating import workareas
    window.update_idletasks()
    x,y=anchor.winfo_rootx(),anchor.winfo_rooty()
    w,h=anchor.winfo_width(),anchor.winfo_height()
    if icon:x+=max(0,w-round(34*getattr(anchor,'s',1)));w=round(34*getattr(anchor,'s',1))
    x,y,w,h=bounds((x,y,w,h),window.winfo_width(),window.winfo_height(),workareas(anchor))
    window.minsize(min(w,window.winfo_reqwidth()),min(h,window.winfo_reqheight()))
    window.geometry(f'{w}x{h}+{x}+{y}')
    # Use outer HWND coordinates for custom chrome, including negative monitors.
    import ctypes
    from ctypes import wintypes as W
    u=ctypes.windll.user32
    u.GetAncestor.argtypes=[W.HWND,W.UINT];u.GetAncestor.restype=W.HWND
    u.SetWindowPos.argtypes=[W.HWND,W.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,W.UINT]
    u.SetWindowPos(u.GetAncestor(window.winfo_id(),2),None,x,y,w,h,0x14)
