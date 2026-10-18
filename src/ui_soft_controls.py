"""Rounded, keyboard-accessible controls for the compact task editors."""
import tkinter as tk
from PIL import Image,ImageDraw,ImageTk
from theme import theme
from ui_cozy import scale,cozy_icon
from ui_dialog_palette import COLORS as C

def keyboard_control(widget,activate):
    original=widget.draw
    def paint():
        original()
        from ui_focus import current_focus
        if current_focus(widget) is widget and getattr(widget,'show_focus_ring',True):
            widget.create_rectangle(2,2,max(3,widget.winfo_width()-3),max(3,widget.winfo_height()-3),outline=theme.accent,dash=(2,2),tags='focus-ring')
    widget.draw=paint
    widget.bind('<FocusIn>',lambda e:widget.draw(),add='+');widget.bind('<FocusOut>',lambda e:widget.draw(),add='+')
    def invoke(event):
        widget.focus_set();activate();return 'break'
    widget.bind('<Return>',invoke);widget.bind('<space>',invoke)
    widget.bind('<Button-1>',lambda e:widget.focus_set(),add='+')

class SoftInput(tk.Canvas):
    def __init__(self,parent,variable,placeholder='',icon=None,command=None,width=180,height=34):
        self.s=scale(parent);self.variable=variable;self.placeholder=placeholder;self.icon=icon;self.command=command;self.disabled=False;self.focused=False;self.syncing=False
        super().__init__(parent,width=round(width*self.s),height=round(height*self.s),bg=parent.cget('bg'),highlightthickness=0,bd=0)
        self.display=tk.StringVar(self);self.entry=tk.Entry(self,textvariable=self.display,relief='flat',bd=0,highlightthickness=0,font=theme.font(),insertbackground=theme.accent,bg=C['input'],fg=C['fg'],disabledbackground='#E7E3F2',disabledforeground='#A59DB6')
        self.entry.place(x=round(12*self.s),rely=.5,anchor='w',relwidth=1,width=-round((42 if icon else 24)*self.s))
        self.entry.bind('<FocusIn>',lambda e:self.focus(True));self.entry.bind('<FocusOut>',lambda e:self.focus(False))
        self.trace=variable.trace_add('write',lambda *a:self.sync());self.display.trace_add('write',self.changed)
        self.bind('<Configure>',lambda e:self.draw());self.bind('<Button-1>',self.click);self.bind('<Destroy>',self.dispose,add='+');self.sync()
    def dispose(self,event):
        if event.widget is self:
            try:self.variable.trace_remove('write',self.trace)
            except tk.TclError:pass
    def focus(self,value):self.focused=value;self.sync();self.draw()
    def focus_set(self):self.entry.focus_set()
    def changed(self,*args):
        if not self.syncing:self.variable.set(self.display.get())
    def sync(self):
        value=self.variable.get();ghost=not value and not self.focused
        self.syncing=True;self.display.set(self.placeholder if ghost else value);self.syncing=False
        self.entry.config(fg='#AAA2BD' if ghost else C['fg'])
    def set_enabled(self,value):
        self.disabled=not value;self.entry.config(state='normal' if value else 'disabled');self.draw()
    def click(self,event):
        if self.disabled:return
        if self.icon and event.x>self.winfo_width()-round(34*self.s) and self.command:self.command()
        else:self.focus_set()
    def draw(self):
        w,h=self.winfo_width(),self.winfo_height()
        if min(w,h)<2:return
        fill='#E7E3F2' if self.disabled else C['input'];bg=self.master.cget('bg');self.config(bg=bg);self.entry.config(bg=fill)
        image=Image.new('RGB',(w*3,h*3),bg);d=ImageDraw.Draw(image)
        d.rounded_rectangle((1,1,w*3-2,h*3-2),radius=round(9*self.s*3),fill=fill,outline=theme.accent if self.focused and not self.disabled else '#D8CDEF',width=3)
        self.photo=ImageTk.PhotoImage(image.resize((w,h),Image.Resampling.LANCZOS),master=self);self.delete('all');self.create_image(0,0,image=self.photo,anchor='nw')
        if self.icon:
            self.icon_photo=cozy_icon(self,self.icon,round(17*self.s),ink='#8A7FA7');self.create_image(w-round(18*self.s),h/2,image=self.icon_photo)

class SoftChoice(tk.Canvas):
    def __init__(self,parent,app,values,extra=None):
        self.app=app;self.values=list(values);self.index=0;self.extra=extra;self.s=scale(parent)
        super().__init__(parent,height=round(34*self.s),width=100,bg=parent.cget('bg'),highlightthickness=0,bd=0,takefocus=True,cursor='hand2')
        self.bind('<Configure>',lambda e:self.draw());self.bind('<Button-1>',lambda e:self.open());self.bind('<space>',lambda e:self.open());self.bind('<Return>',lambda e:self.open())
        keyboard_control(self,self.open)
    def current(self,index=None):
        if index is None:return self.index
        self.index=index;self.draw()
    def choose(self,index):self.current(index);self.event_generate('<<ComboboxSelected>>')
    def open(self):
        from ui_popup_menu import VioletMenu
        menu=tk.Menu(self,tearoff=0)
        for i,text in enumerate(self.values):menu.add_command(label=text,command=lambda i=i:self.choose(i))
        if self.extra:menu.add_separator();menu.add_command(label=self.extra[0],command=self.extra[1])
        self.popup=VioletMenu(self.app,menu,anchor=self,icons=('parameters',)*(len(self.values)+bool(self.extra)))
    def draw(self):
        w,h=self.winfo_width(),self.winfo_height()
        if min(w,h)<2:return
        im=Image.new('RGB',(w*3,h*3),self.master.cget('bg'));d=ImageDraw.Draw(im);d.rounded_rectangle((1,1,w*3-2,h*3-2),radius=round(9*self.s*3),fill=C['input'],outline='#D8CDEF',width=3)
        self.photo=ImageTk.PhotoImage(im.resize((w,h),Image.Resampling.LANCZOS),master=self);self.delete('all');self.create_image(0,0,image=self.photo,anchor='nw')
        self.create_text(round(12*self.s),h/2,text=self.values[self.index],anchor='w',fill=C['fg'],font=theme.font())
        x=w-round(16*self.s);y=h/2;self.create_line(x-4*self.s,y-2*self.s,x,y+2*self.s,x+4*self.s,y-2*self.s,fill=C['muted'],width=max(1,round(self.s)))

class Segments(tk.Canvas):
    def __init__(self,parent,labels,command):
        self.labels=labels;self.command=command;self.index=0;self.s=scale(parent)
        super().__init__(parent,height=round(34*self.s),bg=parent.cget('bg'),highlightthickness=0,takefocus=True,cursor='hand2')
        self.bind('<Configure>',lambda e:self.draw());self.bind('<Button-1>',lambda e:self.choose(min(len(labels)-1,int(e.x/max(1,self.winfo_width())*len(labels)))))
        self.bind('<Left>',lambda e:self.choose(max(0,self.index-1)));self.bind('<Right>',lambda e:self.choose(min(len(labels)-1,self.index+1)))
        keyboard_control(self,lambda:self.choose(self.index))
    def choose(self,index):self.index=index;self.draw();self.command(index);return 'break'
    def draw(self):
        w,h=self.winfo_width(),self.winfo_height()
        if min(w,h)<2:return
        q=3;im=Image.new('RGB',(w*q,h*q),self.master.cget('bg'));d=ImageDraw.Draw(im);r=round(9*self.s*q)
        d.rounded_rectangle((1,1,w*q-2,h*q-2),radius=r,fill=C['card'],outline='#D8CDEF',width=q)
        cell=w/len(self.labels)
        for i in range(1,len(self.labels)):d.line((round(i*cell*q),2,round(i*cell*q),h*q-3),fill='#E1D8F4',width=q)
        x=round(self.index*cell*q);d.rounded_rectangle((x+3,3,round((self.index+1)*cell*q)-4,h*q-4),radius=r,fill=theme.accent)
        self.photo=ImageTk.PhotoImage(im.resize((w,h),Image.Resampling.LANCZOS),master=self);self.delete('all');self.create_image(0,0,image=self.photo,anchor='nw')
        for i,t in enumerate(self.labels):self.create_text(cell*(i+.5),h/2,text=t,fill='white' if i==self.index else C['fg'],font=theme.font())

class SoftToggle(tk.Canvas):
    def __init__(self,parent,variable,command=None):
        self.variable=variable;self.command=command;self.s=scale(parent)
        super().__init__(parent,width=round(46*self.s),height=round(26*self.s),bg=parent.cget('bg'),highlightthickness=0,takefocus=True,cursor='hand2')
        self.trace=variable.trace_add('write',lambda *a:self.draw());self.bind('<Configure>',lambda e:self.draw());self.bind('<Button-1>',self.toggle);self.bind('<space>',self.toggle)
        self.bind('<Destroy>',lambda e:variable.trace_remove('write',self.trace) if e.widget is self else None)
        keyboard_control(self,self.toggle)
    def toggle(self,event=None):self.variable.set(not self.variable.get());self.command and self.command();return 'break'
    def draw(self):
        s=self.s*3;im=Image.new('RGB',(round(46*s),round(26*s)),self.master.cget('bg'));d=ImageDraw.Draw(im);on=self.variable.get()
        d.rounded_rectangle((0,2*s,46*s,24*s),radius=11*s,fill=theme.accent if on else '#BCB4D0');x=(34 if on else 12)*s
        d.ellipse((x-9*s,4*s,x+9*s,22*s),fill='#FEFDFF');self.photo=ImageTk.PhotoImage(im.resize((round(46*self.s),round(26*self.s)),Image.Resampling.LANCZOS),master=self)
        self.delete('all');self.create_image(0,0,image=self.photo,anchor='nw')

class SoftRadio(tk.Canvas):
    def __init__(self,parent,variable,value,text):
        self.variable=variable;self.value=value;self.text=text;self.s=scale(parent)
        super().__init__(parent,width=round(158*self.s),height=round(32*self.s),bg=parent.cget('bg'),highlightthickness=0,takefocus=True,cursor='hand2')
        self.trace=variable.trace_add('write',lambda *a:self.draw());self.bind('<Configure>',lambda e:self.draw());self.bind('<Button-1>',lambda e:variable.set(value));self.bind('<space>',lambda e:variable.set(value))
        self.bind('<Destroy>',lambda e:variable.trace_remove('write',self.trace) if e.widget is self else None)
        keyboard_control(self,lambda:self.variable.set(self.value))
    def draw(self):
        self.delete('all');s=self.s;cy=self.winfo_height()/2;on=self.variable.get()==self.value
        q=4;im=Image.new('RGB',(round(25*s*q),max(1,self.winfo_height()*q)),self.master.cget('bg'));d=ImageDraw.Draw(im)
        d.ellipse((2*s*q,(cy-10*s)*q,22*s*q,(cy+10*s)*q),outline=theme.accent if on else '#B397EB',width=max(1,round(s*q)))
        if on:d.ellipse((6*s*q,(cy-6*s)*q,18*s*q,(cy+6*s)*q),fill=theme.accent)
        self.photo=ImageTk.PhotoImage(im.resize((round(25*s),max(1,self.winfo_height())),Image.Resampling.LANCZOS),master=self)
        self.create_image(0,0,image=self.photo,anchor='nw')
        self.create_text(32*s,cy,anchor='w',text=self.text,font=theme.font(delta=-1),fill=C['fg'])
