"""Borderless violet popup with mouse, keyboard and outside-click dismissal."""
import ctypes
import tkinter as tk
from ui_focus import current_grab, current_focus
import tkinter.font as tkfont
from ctypes import wintypes as W
from theme import theme,flat_button
from ui_cozy import cozy_icon,scale
from ui_dialog_palette import COLORS
from ui_window import _main_opacity,present_dialog

class VioletMenu(tk.Toplevel):
    def __init__(self,app,menu,anchor=None,icons=None,title=None):
        super().__init__(app.root);self.withdraw();self.app=app;self.menu=menu;self.closed=False;self._ready_for_dismiss=False;self.previous_grab=current_grab(app.root);self.buttons=[];self.items=[];self.active=-1
        self.overrideredirect(True);self.owner=(anchor or app.avatar_btn).winfo_toplevel();self.transient(self.owner);self.attributes('-toolwindow',True);self.attributes('-topmost',bool(app.root.attributes('-topmost')));self.configure(bg=COLORS['menu'],bd=0,highlightthickness=0);self._dialog_ready=False;self._dialog_presenting=False
        s=scale(self);inset=round(7*s);row_height=round(32*s)
        body=tk.Frame(self,bg=COLORS['menu']);body.pack(fill='both',expand=True,padx=inset,pady=inset)
        if title:tk.Label(body,text=title,bg=COLORS['menu'],fg=COLORS['fg'],font=theme.font(delta=-2,bold=True),anchor='w').pack(fill='x',padx=round(8*s),pady=(2,round(5*s)))
        icons=icons or ('gear','parameters','enqueue','clock','power_badge');icon_index=0;longest=0;font=tkfont.Font(root=self,font=theme.font())
        for index in range(menu.index('end')+1):
            if menu.type(index)=='separator':
                tk.Frame(body,bg=COLORS['border'],height=1).pack(fill='x',padx=round(9*s),pady=round(5*s));continue
            label=menu.entrycget(index,'label').strip();longest=max(longest,font.measure(label));slot=tk.Frame(body,bg=COLORS['menu'],height=row_height);slot.pack(fill='x',pady=1);slot.pack_propagate(False)
            b=flat_button(slot,label,lambda i=index:self.select(i),kind='normal',padx=round(9*s),pady=3);b._bg=COLORS['menu'];b._hover=COLORS['hover'];b._fg=COLORS['fg'];b.configure(bg=b._bg,activebackground=b._hover,fg=b._fg,anchor='w',compound='left',image=menu_icon(self,icons[icon_index],round(17*s)))
            b._theme_photo=b.cget('image');b.pack(fill='both',expand=True);self.buttons.append(b);self.items.append(index);icon_index+=1
            if menu.entrycget(index,'state')=='disabled':b.configure(state='disabled')
            b.bind('<Enter>',lambda e,k=len(self.buttons)-1:self.highlight(k),add='+')
        self.update_idletasks();width=max(round(180*s),longest+round(58*s));height=self.winfo_reqheight();button=anchor or app.avatar_btn
        from ui_floating import workareas
        cx=button.winfo_rootx();cy=button.winfo_rooty();left,top,right,bottom=min(workareas(app.root),key=lambda a:max(a[0]-cx,0,cx-a[2])**2+max(a[1]-cy,0,cy-a[3])**2)
        x=max(left,min(right-width,button.winfo_rootx()+button.winfo_width()-width));y=button.winfo_rooty()+button.winfo_height()+round(5*s)
        if y+height>bottom:y=max(top,button.winfo_rooty()-height-round(5*s))
        self.geometry(f'{width}x{height}+{x}+{y}')
        self.bind('<Map>',self._mapped,add='+');self.bind('<Escape>',lambda e:self.dismiss());self.bind('<Up>',lambda e:self.navigate(-1));self.bind('<Down>',lambda e:self.navigate(1));self.bind('<Home>',lambda e:self.highlight(0,True));self.bind('<End>',lambda e:self.highlight(len(self.buttons)-1,True));self.bind('<ButtonPress-1>',self._outside,add='+');self.bind('<FocusOut>',lambda e:app.root.after_idle(self._lost_focus),add='+')
        self._move_binding=self.owner.bind('<Configure>',lambda e:self.dismiss() if e.widget is self.owner else None,add='+')
        self._dialog_ready=True;_main_opacity(self,0);self.deiconify();self.grab_set();self.focus_set()
    def _mapped(self,event):
        if event.widget is not self:return
        _main_opacity(self,0);self.app.root.after_idle(self._reveal)
    def _reveal(self):
        if self.closed:return
        # Only this small, stationary popup uses a native rounded region.
        u=ctypes.windll.user32;g=ctypes.windll.gdi32;u.GetAncestor.argtypes=[W.HWND,W.UINT];u.GetAncestor.restype=W.HWND
        hwnd=u.GetAncestor(self.winfo_id(),2);g.CreateRoundRectRgn.argtypes=[ctypes.c_int]*6;g.CreateRoundRectRgn.restype=W.HRGN;u.SetWindowRgn.argtypes=[W.HWND,W.HRGN,W.BOOL]
        radius=round(15*scale(self));region=g.CreateRoundRectRgn(0,0,self.winfo_width()+1,self.winfo_height()+1,radius,radius)
        if region and not u.SetWindowRgn(hwnd,region,True):g.DeleteObject(W.HGDIOBJ(region))
        present_dialog(self)
        if self.closed:return
        self._ready_for_dismiss=True
        u.GetForegroundWindow.restype=W.HWND
        foreground=u.GetForegroundWindow();owner=u.GetAncestor(self.owner.winfo_id(),2)
        if foreground in (hwnd,owner,u.GetAncestor(self.app.root.winfo_id(),2)):self.focus_force()
        self.app.root.after_idle(self._lost_focus)
    def highlight(self,index,focus=False):
        if self.closed:return 'break'
        self.active=index
        for i,b in enumerate(self.buttons):b.configure(bg=COLORS['hover'] if i==index else COLORS['menu'])
        if focus:self._root()._cozy_keyboard_navigation=True;self.buttons[index].focus_set()
        return 'break'
    def navigate(self,step):
        self._root()._cozy_keyboard_navigation=True;return self.highlight((0 if step>0 else len(self.buttons)-1) if self.active<0 else (self.active+step)%len(self.buttons),True)
    def _outside(self,event):
        if not (self.winfo_rootx()<=event.x_root<self.winfo_rootx()+self.winfo_width() and self.winfo_rooty()<=event.y_root<self.winfo_rooty()+self.winfo_height()):self.dismiss();return 'break'
    def _lost_focus(self):
        if self.closed or not self._ready_for_dismiss:return
        focus=current_focus(self)
        if focus is None or focus.winfo_toplevel() is not self:self.dismiss()
    def select(self,index):
        menu=self.menu;root=self.app.root;self.dismiss(False)
        def invoke():
            try:menu.invoke(index)
            finally:menu.destroy()
        root.after_idle(invoke)
    def dismiss(self,destroy_menu=True):
        if self.closed:return
        self.closed=True
        if getattr(self,'_move_binding',None) and self.owner.winfo_exists():self.owner.unbind('<Configure>',self._move_binding)
        try:self.grab_release()
        except tk.TclError:pass
        self.destroy()
        if destroy_menu:self.menu.destroy()
        if self.previous_grab:
            try:
                if self.previous_grab.winfo_exists():self.previous_grab.grab_set()
            except tk.TclError:pass

def menu_icon(widget,name,size):
    if name not in ('copy','broom'):return cozy_icon(widget,name,size)
    from PIL import Image,ImageDraw,ImageTk
    im=Image.new('RGBA',(96,96));d=ImageDraw.Draw(im);ink=COLORS['fg']
    if name=='copy':
        d.rounded_rectangle((22,10,66,67),radius=7,outline=ink,width=5)
        d.rounded_rectangle((36,27,80,85),radius=7,fill=COLORS['menu'],outline=ink,width=5)
    else:
        d.line([(76,9),(46,55)],fill=ink,width=5)
        d.polygon([(42,43),(65,59),(53,85),(14,69)],outline=ink,width=5)
        for x in (27,39,50):d.line([(x+8,58),(x,75)],fill=ink,width=3)
    return ImageTk.PhotoImage(im.resize((size,size),Image.Resampling.LANCZOS),master=widget)
