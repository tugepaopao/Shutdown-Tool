"""Per-pixel alpha presentation for the violet illustrated floating window."""
import ctypes
from ctypes import wintypes as W

def present(window,image,opacity=255):
    u=ctypes.windll.user32;g=ctypes.windll.gdi32
    u.GetAncestor.argtypes=[W.HWND,W.UINT];u.GetAncestor.restype=W.HWND
    hwnd=u.GetAncestor(window.winfo_id(),2) or window.winfo_id()
    u.GetWindowLongW.argtypes=[W.HWND,ctypes.c_int];u.SetWindowLongW.argtypes=[W.HWND,ctypes.c_int,ctypes.c_long]
    if not getattr(window,'_alpha_ready',False):
        ex=u.GetWindowLongW(hwnd,-20);u.SetWindowLongW(hwnd,-20,ex&~0x80000);u.SetWindowLongW(hwnd,-20,ex|0x80000|0x80);window._alpha_ready=True
    class Header(ctypes.Structure):_fields_=[('size',W.DWORD),('width',W.LONG),('height',W.LONG),('planes',W.WORD),('bits',W.WORD),('compression',W.DWORD),('bytes',W.DWORD),('x',W.LONG),('y',W.LONG),('used',W.DWORD),('important',W.DWORD)]
    class Blend(ctypes.Structure):_fields_=[('op',ctypes.c_ubyte),('flags',ctypes.c_ubyte),('alpha',ctypes.c_ubyte),('format',ctypes.c_ubyte)]
    class Size(ctypes.Structure):_fields_=[('cx',W.LONG),('cy',W.LONG)]
    g.CreateCompatibleDC.argtypes=[W.HDC];g.CreateCompatibleDC.restype=W.HDC
    g.CreateDIBSection.argtypes=[W.HDC,ctypes.POINTER(Header),W.UINT,ctypes.POINTER(ctypes.c_void_p),W.HANDLE,W.DWORD];g.CreateDIBSection.restype=W.HBITMAP
    g.SelectObject.argtypes=[W.HDC,W.HANDLE];g.SelectObject.restype=W.HANDLE
    g.DeleteObject.argtypes=[W.HANDLE];g.DeleteDC.argtypes=[W.HDC]
    u.UpdateLayeredWindow.argtypes=[W.HWND,W.HDC,ctypes.POINTER(W.POINT),ctypes.POINTER(Size),W.HDC,ctypes.POINTER(W.POINT),W.COLORREF,ctypes.POINTER(Blend),W.DWORD]
    w,h=image.size;info=Header();info.size=ctypes.sizeof(info);info.width=w;info.height=-h;info.planes=1;info.bits=32
    bits=ctypes.c_void_p();dc=g.CreateCompatibleDC(None);bitmap=g.CreateDIBSection(dc,ctypes.byref(info),0,ctypes.byref(bits),None,0);assert bitmap
    selected=g.SelectObject(dc,bitmap)
    try:
        # Windows requires premultiplied BGRA for AC_SRC_ALPHA.
        raw=image.convert('RGBa').tobytes('raw','BGRa');ctypes.memmove(bits,raw,len(raw))
        src=W.POINT(0,0);dst=W.POINT(*window.position);size=Size(w,h);blend=Blend(0,0,opacity,1)
        if not u.UpdateLayeredWindow(hwnd,None,ctypes.byref(dst),ctypes.byref(size),dc,ctypes.byref(src),0,ctypes.byref(blend),2):raise ctypes.WinError()
    finally:g.SelectObject(dc,selected);g.DeleteObject(bitmap);g.DeleteDC(dc)
