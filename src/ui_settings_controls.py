"""Small matching controls for the approved settings composition."""
import tkinter as tk
from theme import theme,flat_button
from ui_cozy import CozyFrame,scale,cozy_icon
from ui_dialog_palette import COLORS as C
from i18n import feature_text

def text(w,value):
    win=w.winfo_toplevel();T=getattr(win,'T',None) or win.app.T
    return feature_text(T,value)

def label(parent,value,**kw):
    args=dict(text=text(parent,value),bg=parent.cget('bg'),fg=C['fg'],font=theme.font(),anchor='w',justify='left');args.update(kw)
    w=tk.Label(parent,**args);w.pack(fill='x');return w

class Switch(tk.Canvas):
    def __init__(self,parent,variable,checkbox=False,command=None):
        self.command=command;self.variable=variable;self.checkbox=checkbox;self.disabled=False;self.s=scale(parent)
        super().__init__(parent,width=round((25 if checkbox else 89)*self.s),height=round(25*self.s),bg=parent.cget('bg'),highlightthickness=0,takefocus=True,cursor='hand2')
        self.trace=variable.trace_add('write',lambda *a:self.draw());self.bind('<Configure>',lambda e:self.draw());self.bind('<Button-1>',self.toggle);self.bind('<space>',self.toggle);self.bind('<Return>',self.toggle);self.bind('<Destroy>',self.dispose,add='+');self.draw()
    def toggle(self,e=None):
        if not self.disabled:
            self.variable.set(not self.variable.get())
            if self.command:self.command()
        return 'break'
    def dispose(self,e):
        if e.widget is self:self.variable.trace_remove('write',self.trace)
    def set_disabled(self,value):self.disabled=value;self.configure(takefocus=not value,cursor='arrow' if value else 'hand2');self.draw()
    def draw(self):
        self.delete('all');s=self.s;on=bool(self.variable.get());ink=C['muted'] if self.disabled else theme.accent
        if self.checkbox:
            from PIL import Image,ImageDraw,ImageTk
            im=Image.new('RGBA',(100,100));d=ImageDraw.Draw(im)
            d.rounded_rectangle((12,16,80,84),radius=14,fill=ink if on else C['input'],outline=ink,width=4)
            if on:d.line([(24,48),(40,64),(68,32)],fill='white',width=8,joint='curve')
            self._photo=ImageTk.PhotoImage(im.resize((round(25*s),round(25*s)),Image.Resampling.LANCZOS),master=self);self.create_image(0,0,image=self._photo,anchor='nw')
        else:
            from PIL import Image,ImageDraw,ImageTk,ImageColor
            size=(round(44*s),round(25*s));key=(size,on,self.disabled,ink)
            if getattr(self,'_switch_key',None)!=key:
                q=4;w,h=size;im=Image.new('RGBA',(w*q,h*q));mask=Image.new('L',im.size)
                d=ImageDraw.Draw(mask);box=(2*s*q,3*s*q,42*s*q,23*s*q)
                d.rounded_rectangle(box,radius=10*s*q,fill=255)
                top,bottom=('#9471F2','#6729D9') if on and not self.disabled else ('#C5C1D4','#A9A3BD')
                a,b=ImageColor.getrgb(top),ImageColor.getrgb(bottom);paint=ImageDraw.Draw(im)
                for y in range(h*q):
                    f=max(0,min(1,(y-3*s*q)/(20*s*q)))
                    paint.line((0,y,w*q,y),fill=tuple(round(v+(z-v)*f) for v,z in zip(a,b)))
                im.putalpha(mask);d=ImageDraw.Draw(im)
                d.rounded_rectangle(box,radius=10*s*q,outline='#AB8FF3' if on and not self.disabled else '#C9C5D7',width=max(1,round(.6*s*q)))
                cx=(32 if on else 12)*s*q;cy=13*s*q;r=8*s*q
                d.ellipse((cx-r,cy-r+.6*s*q,cx+r,cy+r+.6*s*q),fill='#6536B2' if on else '#9690AA')
                d.ellipse((cx-r,cy-r,cx+r,cy+r),fill='#FCFBFF',outline='#E6DFF7',width=max(1,round(.5*s*q)))
                self._photo=ImageTk.PhotoImage(im.resize(size,Image.Resampling.LANCZOS),master=self);self._switch_key=key
            self.create_image(0,0,image=self._photo,anchor='nw')
            self.create_text(48*s,13*s,text=('On' if on else 'Off') if getattr(self.winfo_toplevel().T,'lang','CHS')=='EN' else text(self,'开启' if on else '关闭'),anchor='w',font=theme.font(delta=-1),fill=C['muted'] if self.disabled else C['fg'])

class Expander(tk.Frame):
    def __init__(self,parent,title):
        super().__init__(parent,bg=parent.cget('bg'));self.opened=False;self.title=title
        self.button=flat_button(self,'+ '+text(self,title),self.toggle,padx=10,pady=5);self.button.config(anchor='w',bg=C['hover'],fg=C['muted']);self.button._bg=C['hover'];self.button.pack(fill='x')
        self.body=tk.Frame(self,bg=parent.cget('bg'))
    def toggle(self):
        self.opened=not self.opened
        if self.opened:self.body.pack(fill='x',padx=8,pady=6)
        else:self.body.pack_forget()
        self.button.config(text=('− ' if self.opened else '+ ')+text(self,self.title))

class Tooltip:
    def __init__(self,widget,content):
        self.widget=widget;self.content=content;self.job=None;self.win=None
        widget.bind('<Enter>',self.enter,add='+');widget.bind('<Leave>',self.hide,add='+');widget.bind('<ButtonPress-1>',self.hide,add='+');widget.bind('<Destroy>',self.hide,add='+')
    def enter(self,e=None):
        self.hide();self.job=self.widget.after(550,self.show)
    def show(self):
        self.job=None
        if not self.widget.winfo_exists() or not self.widget.winfo_viewable():return
        value=self.content() if callable(self.content) else self.content
        self.win=tk.Toplevel(self.widget);self.win.overrideredirect(True);self.win.attributes('-topmost',True);self.win.configure(bg=C['border'])
        tk.Label(self.win,text=value,bg=C['menu'],fg=C['fg'],font=theme.font(delta=-1),padx=8,pady=5,wraplength=320,justify='left').pack(padx=1,pady=1)
        self.win.update_idletasks();self.win.geometry(f'+{min(self.widget.winfo_rootx(),self.widget.winfo_screenwidth()-self.win.winfo_reqwidth()-10)}+{min(self.widget.winfo_rooty()+self.widget.winfo_height()+5,self.widget.winfo_screenheight()-self.win.winfo_reqheight()-10)}')
    def hide(self,e=None):
        if self.job:
            try:self.widget.after_cancel(self.job)
            except tk.TclError:pass
            self.job=None
        if self.win:
            try:self.win.destroy()
            except tk.TclError:pass
            self.win=None
