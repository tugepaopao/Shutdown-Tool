"""Main time controls: background-matched idle fields and native editing."""
import tkinter as tk
from PIL import Image,ImageTk
from ui_soft_controls import SoftInput,SoftChoice
from theme import theme,blend
from ui_cozy import scale
from ui_skin import background


def surface(widget):
    w,h=widget.winfo_width(),widget.winfo_height()
    if min(w,h)<2:return False
    im=background(widget)
    if im is None:im=Image.new('RGB',(w,h),theme.c('card'))
    widget.photo=ImageTk.PhotoImage(im,master=widget)
    widget.delete('all');widget.create_image(0,0,image=widget.photo,anchor='nw')
    return True


class NumberInput(tk.Canvas):
    """Canvas-rendered numeric editing; no opaque native Entry is ever mapped."""
    def __init__(self,parent,variable,maximum):
        self.variable=variable;self.maximum=maximum;self.s=scale(parent)
        self.focused=False;self.selected=False;self.cursor=len(variable.get())
        super().__init__(parent,width=round(80*self.s),height=round(46*self.s),bg=parent.cget('bg'),bd=0,highlightthickness=0,takefocus=True)
        self.trace=variable.trace_add('write',self.changed)
        self.bind('<Configure>',lambda e:self.draw())
        self.bind('<FocusIn>',self.focus_in);self.bind('<FocusOut>',self.focus_out)
        self.bind('<Button-1>',self.click);self.bind('<KeyPress>',self.key)
        self.bind('<Destroy>',self.dispose)
    def dispose(self,event):
        if event.widget is self:self.variable.trace_remove('write',self.trace)
    def changed(self,*args):
        self.cursor=min(self.cursor,len(self.variable.get()));self.draw()
    def focus_in(self,event):
        self.focused=True;self.selected=True;self.cursor=len(self.variable.get());self.draw()
    def focus_out(self,event):
        self.focused=False;self.selected=False;self.normalize();self.draw()
    def normalize(self):
        value=self.variable.get().strip()
        if value.isdecimal() and 0<=int(value)<=self.maximum:self.variable.set(f'{int(value):02d}')
    def step(self,amount):
        try:value=int(self.variable.get())
        except ValueError:value=0
        self.variable.set(f'{max(0,min(self.maximum,value+amount)):02d}');self.cursor=len(self.variable.get());self.draw()
        return 'break'
    def click(self,event):
        # Explicit pointer activation also restores keyboard focus after a popup closes.
        self.focus_force()
        if event.x>=self.winfo_width()-round(24*self.s):self.step(1 if event.y<self.winfo_height()/2 else -1)
        else:self.selected=True;self.cursor=len(self.variable.get());self.draw()
    def insert(self,text):
        if not text or not text.isascii() or not text.isdecimal():return
        value=self.variable.get();start=0 if self.selected else self.cursor
        result=text if self.selected else value[:start]+text+value[start:]
        if len(result)>2 or int(result)>self.maximum:return
        self.selected=False;self.variable.set(result);self.cursor=start+len(text);self.draw()
    def key(self,event):
        key=event.keysym;ctrl=bool(event.state&4)
        if key in ('Tab','ISO_Left_Tab'):return
        if ctrl and key.lower()=='a':self.selected=True;self.draw()
        elif ctrl and key.lower()=='c':
            if self.selected:self.clipboard_clear();self.clipboard_append(self.variable.get())
        elif ctrl and key.lower()=='v':
            try:self.insert(self.clipboard_get().strip())
            except tk.TclError:pass
        elif key in ('Up','Down'):return self.step(1 if key=='Up' else -1)
        elif key in ('Left','Right','Home','End'):
            self.cursor=0 if key=='Home' else len(self.variable.get()) if key=='End' else max(0,min(len(self.variable.get()),self.cursor+(-1 if key=='Left' else 1)))
            self.selected=False;self.draw()
        elif key in ('BackSpace','Delete'):
            value=self.variable.get();pos=self.cursor
            if self.selected:value='';pos=0
            elif key=='BackSpace' and pos:value=value[:pos-1]+value[pos:];pos-=1
            elif key=='Delete':value=value[:pos]+value[pos+1:]
            self.selected=False;self.variable.set(value);self.cursor=pos;self.draw()
        elif key in ('Return','KP_Enter'):self.normalize();self.selected=True;self.draw()
        elif key=='Escape':return
        elif not ctrl:
            # Windows keypads and input methods can omit char while retaining keysym.
            digit=key[3:] if key.startswith('KP_') else key
            self.insert(digit if len(digit)==1 and digit.isascii() and digit.isdecimal() else event.char)
        return 'break'
    def draw(self):
        if not surface(self):return
        import tkinter.font as tkfont
        w,h=self.winfo_width(),self.winfo_height();text=self.variable.get();font=theme.font(delta=9,bold=True)
        center=(w-round(16*self.s))/2
        self.create_text(center,h/2,text=text,font=font,fill=blend(theme.c('fg'),theme.c('card'),.14))
        if self.focused:
            f=tkfont.Font(root=self,font=font);left=center-f.measure(text)/2
            r=round(4*self.s);y=h-2
            self.create_polygon(center-r,y,center+r,y,center,y-r*1.5,fill=theme.accent,outline='',tags='time-selection')
            if not self.selected:
                x=left+f.measure(text[:self.cursor]);self.create_line(x,h*.22,x,h*.78,fill=theme.accent,width=1)
        x=w-round(12*self.s);r=max(3,round(3*self.s))
        for y,direction in ((h*.32,-1),(h*.68,1)):
            self.create_polygon(x-r,y-direction*r/2,x+r,y-direction*r/2,x,y+direction*r,fill=theme.c('fg_muted'),outline='')


class WeekdayInput(SoftChoice):
    def __init__(self,parent,app,values,variable):
        self.variable=variable;self.show_focus_ring=False
        super().__init__(parent,app,values)
        import tkinter.font as tkfont
        self.configure(height=round(46*scale(parent)),width=tkfont.Font(root=self,font=theme.font(delta=9,bold=True)).measure('星期三')+round(30*self.s))
    def open(self):
        from ui_popup_menu import VioletMenu
        old=getattr(self,'popup',None)
        if old is not None and old.winfo_exists():old.dismiss();return
        menu=tk.Menu(self,tearoff=0)
        for i,text in enumerate(self.values):menu.add_command(label=text,command=lambda i=i:self.choose(i))
        self.popup=VioletMenu(self.app,menu,anchor=self,compact=True)
    def __setitem__(self,key,value):
        if key=='values':self.values=list(value);self.draw()
        else:super().__setitem__(key,value)
    def current(self,index=None):
        if index is None:return self.index
        self.index=max(0,index);self.variable.set(self.values[self.index]);self.draw()
    def draw(self):
        if not surface(self):return
        w,h=self.winfo_width(),self.winfo_height();s=self.s
        self.create_text((w-round(16*s))/2,h/2,text=self.values[self.index],font=theme.font(delta=9,bold=True),fill=blend(theme.c('fg'),theme.c('card'),.14))
        x=w-round(12*s)
        self.create_line(x-4*s,h/2-2*s,x,h/2+2*s,x+4*s,h/2-2*s,fill=theme.c('fg_muted'),width=max(1,round(s)))
