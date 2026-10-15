"""Capture the test window's own surface without including other desktop apps."""
import ctypes
from ctypes import wintypes as W
from PIL import Image

def capture(window):
 u=ctypes.windll.user32;g=ctypes.windll.gdi32
 u.GetAncestor.argtypes=[W.HWND,W.UINT];u.GetAncestor.restype=W.HWND
 h=u.GetAncestor(window.winfo_id(),2)
 u.GetWindowDC.argtypes=[W.HWND];u.GetWindowDC.restype=W.HDC
 u.ReleaseDC.argtypes=[W.HWND,W.HDC]
 g.CreateCompatibleDC.argtypes=[W.HDC];g.CreateCompatibleDC.restype=W.HDC
 g.CreateCompatibleBitmap.argtypes=[W.HDC,ctypes.c_int,ctypes.c_int];g.CreateCompatibleBitmap.restype=W.HBITMAP
 g.SelectObject.argtypes=[W.HDC,W.HANDLE];g.SelectObject.restype=W.HANDLE
 g.DeleteObject.argtypes=[W.HANDLE];g.DeleteDC.argtypes=[W.HDC]
 u.PrintWindow.argtypes=[W.HWND,W.HDC,W.UINT]
 rect=W.RECT();u.GetWindowRect(h,ctypes.byref(rect));w=rect.right-rect.left;hh=rect.bottom-rect.top
 dc=u.GetWindowDC(h);mem=g.CreateCompatibleDC(dc);bitmap=g.CreateCompatibleBitmap(dc,w,hh);old=g.SelectObject(mem,bitmap)
 class Header(ctypes.Structure):
  _fields_=[('size',W.DWORD),('width',W.LONG),('height',W.LONG),('planes',W.WORD),('bits',W.WORD),('compression',W.DWORD),('imagesize',W.DWORD),('xp',W.LONG),('yp',W.LONG),('used',W.DWORD),('important',W.DWORD)]
 info=Header(ctypes.sizeof(Header),w,-hh,1,32,0,0,0,0,0,0);buf=ctypes.create_string_buffer(w*hh*4)
 try:
  assert u.PrintWindow(h,mem,2),'PrintWindow failed'
  g.SelectObject(mem,old)
  g.GetDIBits.argtypes=[W.HDC,W.HBITMAP,W.UINT,W.UINT,ctypes.c_void_p,ctypes.c_void_p,W.UINT]
  assert g.GetDIBits(mem,bitmap,0,hh,buf,ctypes.byref(info),0)==hh
  return Image.frombytes('RGB',(w,hh),buf.raw,'raw','BGRX')
 finally:g.SelectObject(mem,old);g.DeleteObject(bitmap);g.DeleteDC(mem);u.ReleaseDC(h,dc)
