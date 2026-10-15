"""Hold the old viewport until a new settings page has finished painting."""
import ctypes
import tkinter as tk
from PIL import ImageGrab,ImageTk

def cover(window,viewport):
    old=getattr(window,'_page_cover',None)
    if old is not None and old.winfo_exists():return old
    if not window.winfo_viewable() or getattr(window,'_main_opacity',255)!=255:return None
    try:
        x,y=viewport.winfo_rootx(),viewport.winfo_rooty();w,h=viewport.winfo_width(),viewport.winfo_height()
        if w<2 or h<2:return None
        snapshot=ImageTk.PhotoImage(ImageGrab.grab((x,y,x+w,y+h),all_screens=True),master=window)
        label=tk.Label(viewport,image=snapshot,bd=0,highlightthickness=0,padx=0,pady=0);label._snapshot=snapshot;label._theme_fixed=True;label.place(x=0,y=0,relwidth=1,relheight=1);label.lift();window._page_cover=label;window.update_idletasks();return label
    except (OSError,tk.TclError):return None

def reveal(window,label):
    if label is None:return
    job=getattr(window,'_page_cover_job',None)
    if job:
        try:window._root().after_cancel(job)
        except tk.TclError:pass
    def ready():
        window._page_cover_job=None
        try:
            if not window.winfo_exists():return
            window.update_idletasks()
            if label.winfo_exists():label.destroy()
            window._page_cover=None
        except tk.TclError:pass
    window._page_cover_job=window._root().after(16,ready)
