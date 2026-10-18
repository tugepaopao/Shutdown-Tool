"""Peer workspace windows; modal dialogs retain their own owner and grab."""
import tkinter as tk
from ui_focus import current_grab, current_focus


def windows(app):
    seen=set()
    for name in ('_settings_win','_task_center_win','_log_win'):
        window=getattr(app,name,None)
        if window is not None and id(window) not in seen and window.winfo_exists():
            seen.add(id(window));yield window


def active_modal(root):
    modal=current_grab(root)
    if modal is not None and modal.winfo_exists():
        from ui_window import activate_dialog
        return activate_dialog(modal.winfo_toplevel())
    return None


def keep_visible(window):
    """Recover a window after a display was disconnected, on explicit activation."""
    from ui_floating import workareas,clamp_position
    window.update_idletasks()
    x,y=window.winfo_x(),window.winfo_y()
    width,height=window.winfo_width(),window.winfo_height()
    areas=workareas(window);resized=False
    if getattr(window,'_compact_size',None):
        area=min(areas,key=lambda a:max(a[0]-x,0,x-a[2])**2+max(a[1]-y,0,y-a[3])**2)
        fitted=(min(width,max(1,area[2]-area[0]-20)),min(height,max(1,area[3]-area[1]-20)))
        if fitted!=(width,height):
            width,height=fitted
            # Tk retains native sizing margins after our caption removes the frame.
            # Leave that margin below the fitted outer size so WM_GETMINMAXINFO
            # cannot enlarge the HWND beyond the replacement monitor.
            import ctypes
            u=ctypes.windll.user32
            margin=2*(u.GetSystemMetrics(32)+u.GetSystemMetrics(92))
            window.minsize(max(1,width-margin),max(1,height-margin));resized=True
    nx,ny=clamp_position(x,y,width,height,areas)
    if resized or (nx,ny)!=(x,y):
        if getattr(window,'_violet_dialog',False):
            # Custom chrome uses outer HWND bounds; Tk geometry adds stale frame margins.
            import ctypes
            from ctypes import wintypes as W
            u=ctypes.windll.user32
            u.GetAncestor.argtypes=[W.HWND,W.UINT];u.GetAncestor.restype=W.HWND
            u.SetWindowPos.argtypes=[W.HWND,W.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,W.UINT]
            if u.SetWindowPos(u.GetAncestor(window.winfo_id(),2),None,nx,ny,width,height,0x14):return
        window.geometry(f'{width}x{height}+{nx}+{ny}')


def hide_workspace(app):
    if active_modal(app.root) is not None:return
    hidden=getattr(app,'_workspace_hidden',[])
    for window in windows(app):
        state=window.state()
        if state!='withdrawn':
            hidden.append((window,state));window.withdraw()
    app._workspace_hidden=hidden
    app.root.withdraw()


def restore_workspace(app):
    from ui_window import show,activate_dialog
    show(app.root)
    hidden=getattr(app,'_workspace_hidden',[]);app._workspace_hidden=[]
    for window,state in hidden:
        try:
            if window.winfo_exists():
                show(window);keep_visible(window)
                if state=='iconic':window.iconify()
        except tk.TclError:pass
    return activate_dialog(app.root)


def allow_exit(app):
    if active_modal(app.root) is not None:return False
    settings=getattr(app,'_settings_win',None)
    if settings is not None and settings.winfo_exists() and settings.dirty:
        from ui_window import activate_dialog
        activate_dialog(settings);settings.request_close()
        return not settings.winfo_exists()
    return True
