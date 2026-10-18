"""Keep the fixed main HWND size correct before a taskbar restore is painted."""
import ctypes
from ctypes import wintypes as W
import tkinter as tk


class MinMaxInfo(ctypes.Structure):
    _fields_=[('reserved',W.POINT),('max_size',W.POINT),('max_position',W.POINT),
              ('min_track',W.POINT),('max_track',W.POINT)]


class WindowPos(ctypes.Structure):
    _fields_=[("hwnd",W.HWND),("insert_after",W.HWND),("x",ctypes.c_int),("y",ctypes.c_int),
              ("cx",ctypes.c_int),("cy",ctypes.c_int),("flags",W.UINT)]


_CALLBACK=ctypes.WINFUNCTYPE(ctypes.c_ssize_t,W.HWND,W.UINT,W.WPARAM,W.LPARAM,
                            ctypes.c_size_t,ctypes.c_size_t)
_ID=0x7317


def install(window):
    """Only this Tk main wrapper is subclassed; callbacks never call Tcl."""
    if not getattr(window,'_main_ready',False):return
    try:
        u=ctypes.windll.user32;cc=ctypes.windll.comctl32
        u.GetAncestor.argtypes=[W.HWND,W.UINT];u.GetAncestor.restype=W.HWND
        hwnd=u.GetAncestor(window.winfo_id(),2)
        if not hwnd or hwnd==window.winfo_id():return
        hooks=getattr(window,'_native_restore_hooks',None)
        if hooks is None:window._native_restore_hooks=hooks={}
        if hwnd in hooks:return
        cc.SetWindowSubclass.argtypes=[W.HWND,_CALLBACK,ctypes.c_size_t,ctypes.c_size_t]
        cc.SetWindowSubclass.restype=W.BOOL
        cc.RemoveWindowSubclass.argtypes=[W.HWND,_CALLBACK,ctypes.c_size_t]
        cc.DefSubclassProc.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
        cc.DefSubclassProc.restype=ctypes.c_ssize_t
        u.IsIconic.argtypes=[W.HWND];u.IsIconic.restype=W.BOOL

        restoring={"pending":False,"hidden":False}
        @_CALLBACK
        def native(h,message,wp,lp,ident,ref):
            if message in (0x7E,0x2E0):window._system_display_changed=True
            if message==0x1E or message==0x218 and wp in (7,18):window._system_clock_changed=True
            if message==0x82:  # WM_NCDESTROY: retire only this native wrapper.
                cc.RemoveWindowSubclass(h,native,ident)
                # Retain the Python callback through native destruction; a new
                # wrapper receives its own hook, even if Windows reuses its HWND.
                hooks.pop(h,None)
                return cc.DefSubclassProc(h,message,wp,lp)
            # Keep the DWM surface hidden only while the restore paint settles.
            if message==0x112 and (wp&0xFFF0)==0xF020:restoring.update(pending=True,hidden=False);hold(window,h)
            if message==0x5 and wp==1 or message==0x18 and not wp:restoring.update(pending=True,hidden=True);hold(window,h)
            show=message==0x18 and wp or message==0x112 and (wp&0xFFF0)==0xF120
            if message==0x46 and lp:
                pos=ctypes.cast(lp,ctypes.POINTER(WindowPos)).contents
                if pos.flags&0x80 or pos.x==-32000 and pos.y==-32000:restoring.update(pending=True,hidden=True);hold(window,h)
                show=show or (restoring['pending'] and restoring['hidden'] and not pos.flags&0x80 and (pos.x!=-32000 or pos.y!=-32000))
            if show and restoring['pending'] and getattr(window,'_main_presented',False):
                hold(window,h)
                restoring.update(pending=False,hidden=False)
            result=cc.DefSubclassProc(h,message,wp,lp)
            if message==0x46 and lp:  # WM_WINDOWPOSCHANGING: before any visible resize.
                renderer=getattr(window,"_skin_renderer",None)
                if renderer and renderer.active and getattr(window,"_main_presented",False):
                    pos=ctypes.cast(lp,ctypes.POINTER(WindowPos)).contents
                    # Leave Windows' iconic sentinel and no-size/move requests intact.
                    if not pos.flags & 1 and (pos.x!=-32000 or pos.y!=-32000):
                        pos.cx,pos.cy=renderer.fixed_size
            if message==0x47 and u.IsIconic(h):restoring.update(pending=True,hidden=True);hold(window,h)
            if message==0x47 and not u.IsIconic(h):
                rect=W.RECT();u.GetWindowRect(W.HWND(h),ctypes.byref(rect))
                if rect.left!=-32000 or rect.top!=-32000:window._native_normal_position=(rect.left,rect.top)
            if message==0x24 and lp and not u.IsIconic(h):  # WM_GETMINMAXINFO
                renderer=getattr(window,'_skin_renderer',None)
                if renderer and renderer.active and getattr(window,'_main_ready',False):
                    width,height=renderer.fixed_size
                    if width>1 and height>1:
                        info=ctypes.cast(lp,ctypes.POINTER(MinMaxInfo)).contents
                        info.min_track.x=info.max_track.x=width
                        info.min_track.y=info.max_track.y=height
            return result

        if cc.SetWindowSubclass(hwnd,native,_ID,0):
            hooks[hwnd]=native
            # Lifetime includes the final WM_NCDESTROY and any recreated wrappers.
            window.__dict__.setdefault('_native_restore_callbacks',[]).append(native)
    except (AttributeError,OSError,tk.TclError):
        return


def pending(window):
    """ShowWindow can clear WS_MINIMIZE before moving out of its sentinel rect."""
    try:
        u=ctypes.windll.user32
        u.GetAncestor.argtypes=[W.HWND,W.UINT];u.GetAncestor.restype=W.HWND
        hwnd=u.GetAncestor(window.winfo_id(),2)
        if not hwnd:return False
        if u.IsIconic(hwnd):return True
        rect=W.RECT();u.GetWindowRect(ctypes.c_void_p(hwnd),ctypes.byref(rect))
        offscreen=rect.left==-32000 and rect.top==-32000
        position=getattr(window,'_native_normal_position',None)
        if offscreen and position and getattr(window,'_native_restore_cloaked',False):
            renderer=getattr(window,'_skin_renderer',None)
            if renderer:
                u.SetWindowPos.argtypes=[W.HWND,W.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,W.UINT]
                u.SetWindowPos(hwnd,None,*position,*renderer.fixed_size,0x14)
                return False
        return offscreen
    except (AttributeError,OSError,tk.TclError):return False


def _cloak(hwnd,hidden):
    try:
        value=W.BOOL(bool(hidden));dwm=ctypes.windll.dwmapi
        dwm.DwmSetWindowAttribute.argtypes=[W.HWND,W.DWORD,ctypes.c_void_p,W.DWORD]
        return dwm.DwmSetWindowAttribute(hwnd,13,ctypes.byref(value),ctypes.sizeof(value))==0
    except (AttributeError,OSError):return False


def hold(window,hwnd=None):
    """Prepare the hidden surface at minimize/hide time, before restore starts."""
    if not getattr(window,'_main_presented',False) or getattr(window,'_native_restore_cloaked',False):return
    if hwnd is None:hwnd=ctypes.windll.user32.GetAncestor(window.winfo_id(),2)
    # Guard before calling DWM, since native window messages can be reentrant.
    window._native_restore_cloaked=True
    if not _cloak(hwnd,True):window._native_restore_cloaked=False


def finish_paint(window):
    """Present the complete native controls together, retaining ordinary GDI."""
    if not getattr(window,'_native_restore_cloaked',False):return
    u=ctypes.windll.user32;h=None
    try:
        h=u.GetAncestor(window.winfo_id(),2)
        u.RedrawWindow(W.HWND(h),None,None,0x185)
        ctypes.windll.dwmapi.DwmFlush()
    except (AttributeError,OSError,tk.TclError):pass
    finally:
        # Always release presentation, including cancellation/destruction paths.
        if h:_cloak(h,False)
        window._native_restore_cloaked=False
        ctypes.windll.dwmapi.DwmFlush()
