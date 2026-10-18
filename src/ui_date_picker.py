"""Theme-matched calendar selection; values commit only on confirmation."""
import calendar
import datetime as dt
import tkinter as tk
from PIL import Image,ImageDraw,ImageTk
from theme import theme,flat_button
from ui_cozy import CozyFrame,scale
from ui_dialog_palette import COLORS as C
from ui_soft_controls import SoftInput
from ui_window import prepare,compact_show

def as_date(value):
    try:return dt.date.fromisoformat(value) if value else None
    except (ValueError,TypeError):return None

class DateInput(SoftInput):
    """Only the calendar affordance opens the popup; keyboard remains supported."""
    def __init__(self,parent,variable,command,placeholder='选择日期',**kwargs):
        super().__init__(parent,variable,placeholder=placeholder,icon='calendar',command=command,**kwargs)
        self.configure(cursor='hand2');self.entry.configure(state='readonly',readonlybackground=C['input'],cursor='hand2')
        self.entry.bind('<Button-1>',lambda e:self.focus_set())
        for key in ('<Return>','<space>','<Down>'):self.entry.bind(key,self.open)
    def click(self,event):
        if event.x>=self.winfo_width()-round(34*self.s):return self.open(event)
        self.focus_set()

    def open(self,event=None):
        if not self.disabled:
            owner=self.winfo_toplevel();owner._date_anchor=self
            self.command()
        return 'break'
    def set_enabled(self,value):
        self.disabled=not value;self.entry.configure(state='readonly' if value else 'disabled');self.draw()

class DatePicker(tk.Toplevel):
    def __init__(self,parent,app,value='',title='选择日期',allow_clear=False,minimum=None,maximum=None,range_start='',range_end='',endpoint='start',anchor=None):
        super().__init__(parent);prepare(self);self.app=app;self.T=app.T;self.title(title);self.transient(parent);self.resizable(False,False);self.configure(bg=C['bg'])
        self.result=None;self.minimum=as_date(minimum);self.maximum=as_date(maximum);self.start=as_date(range_start);self.end=as_date(range_end);self.endpoint=endpoint
        self.selected=as_date(value) or dt.date.today()
        if self.minimum:self.selected=max(self.selected,self.minimum)
        if self.maximum:self.selected=min(self.selected,self.maximum)
        self.year,self.month=self.selected.year,self.selected.month;self.mode='days';self.s=scale(self);self.hits=[]
        card=CozyFrame(self,bg=C['card']);card.pack(fill='both',expand=True,padx=8,pady=(4,6))
        tk.Label(card,text=title,bg=C['card'],fg=C['muted'],font=theme.font(delta=-1),anchor='w').pack(fill='x',padx=16,pady=(12,2))
        self.caption=tk.Label(card,bg=C['card'],fg=C['fg'],font=theme.font(delta=5),anchor='w');self.caption.pack(fill='x',padx=16,pady=(0,8))
        bar=tk.Frame(card,bg=C['card']);bar.pack(fill='x',padx=12,pady=(0,2))
        flat_button(bar,'‹',lambda:self.navigate(-1),padx=9,pady=3).pack(side='left')
        self.month_button=flat_button(bar,'',self.choose_month,font=theme.font(bold=True),padx=6,pady=3);self.month_button.pack(side='left',expand=True)
        flat_button(bar,'›',lambda:self.navigate(1),padx=9,pady=3).pack(side='right')
        self.calendar=tk.Canvas(card,bg=C['card'],highlightthickness=0,height=round(224*self.s),takefocus=True,cursor='hand2');self.calendar.pack(fill='both',expand=True,padx=12,pady=(0,4))
        self.calendar.bind('<Configure>',lambda e:self.draw());self.calendar.bind('<Button-1>',self.click)
        for key,delta in [('<Left>',-1),('<Right>',1),('<Up>',-7),('<Down>',7)]:self.calendar.bind(key,lambda e,d=delta:self.move_day(d))
        self.calendar.bind('<Prior>',lambda e:self.navigate(-1));self.calendar.bind('<Next>',lambda e:self.navigate(1))
        bar=self.footer=tk.Frame(self,bg=C['bg']);bar.pack(side='bottom',before=card,fill='x',padx=8,pady=(0,8))
        flat_button(bar,'今天',self.today,font=theme.font(delta=-1),padx=6,pady=6).pack(side='left')
        if allow_clear:flat_button(bar,'不限',lambda:self.finish(''),font=theme.font(delta=-1),padx=6,pady=6).pack(side='left',padx=(4,0))
        flat_button(bar,'确定',self.accept,kind='accent',font=theme.font(delta=-1),padx=12,pady=6).pack(side='right')
        flat_button(bar,'取消',self.destroy,font=theme.font(delta=-1),padx=8,pady=6).pack(side='right',padx=5)
        self.bind('<Escape>',lambda e:self.destroy());self.bind('<Return>',lambda e:self.accept());self.render()
        compact_show(self,app,width=310,height=390,anchor=anchor)
        self.anchor=anchor
        if anchor:
            from ui_anchor import place
            place(self,anchor,icon=isinstance(anchor,DateInput))
        self.grab_set();self.calendar.focus_set()
        self.bind('<ButtonPress-1>',self.outside,add='+')
        self._parent_move=parent.bind('<Configure>',self.parent_moved,add='+')
        self._parent_hide=parent.bind('<Unmap>',lambda e:self.destroy() if e.widget is parent else None,add='+')
        self.bind('<Destroy>',self.cleanup,add='+')
    def outside(self,event):
        if self.anchor and self.anchor.winfo_exists():
            a=self.anchor;x=a.winfo_rootx()+max(0,a.winfo_width()-round(34*getattr(a,'s',1)));y=a.winfo_rooty()
            if x<=event.x_root<a.winfo_rootx()+a.winfo_width() and y<=event.y_root<y+a.winfo_height():
                self.destroy();return 'break'
        if not (self.winfo_rootx()<=event.x_root<self.winfo_rootx()+self.winfo_width() and self.winfo_rooty()<=event.y_root<self.winfo_rooty()+self.winfo_height()):
            self.destroy();return 'break'
    def parent_moved(self,event):
        if event.widget is self.master and self.anchor and self.anchor.winfo_exists():
            from ui_anchor import place
            place(self,self.anchor,icon=isinstance(self.anchor,DateInput))
    def cleanup(self,event):
        if event.widget is self and self.master.winfo_exists():
            self.master.unbind('<Configure>',self._parent_move);self.master.unbind('<Unmap>',self._parent_hide)
    def valid(self,date):return (not self.minimum or date>=self.minimum) and (not self.maximum or date<=self.maximum)
    def finish(self,value):self.result=value;self.destroy()
    def accept(self):
        if self.valid(self.selected):self.finish(self.selected.isoformat())
    def today(self):
        date=dt.date.today()
        if self.valid(date):self.selected=date;self.year,self.month=date.year,date.month;self.mode='days';self.render()
    def move_day(self,delta):
        try:date=self.selected+dt.timedelta(days=delta)
        except OverflowError:return 'break'
        if self.valid(date):self.selected=date;self.year,self.month=date.year,date.month;self.mode='days';self.render()
        return 'break'
    def navigate(self,delta):
        if self.mode=='days':
            year,month=divmod(self.year*12+self.month-1+delta,12)
            if 1<=year<=9999:self.year,self.month=year,month+1
        else:self.year=max(1,min(9999,self.year+delta*(12 if self.mode=='years' else 1)))
        self.render()
    def choose_month(self):self.mode='months' if self.mode=='days' else 'years' if self.mode=='months' else 'days';self.render()
    def render(self):
        self.caption.config(text=f'{self.selected.year}年{self.selected.month}月{self.selected.day}日')
        self.month_button.config(text=f'{self.year}年 {self.month}月' if self.mode=='days' else f'{self.year}年 · 选择月份' if self.mode=='months' else '选择年份')
        self.draw()
    def click(self,event):
        for (x0,y0,x1,y1),value in self.hits:
            if x0<=event.x<x1 and y0<=event.y<y1:
                if self.mode=='years':self.year=value;self.mode='months'
                elif self.mode=='months':self.month=value;self.mode='days'
                elif self.valid(value):self.selected=value
                self.render();break
        self.calendar.focus_set()
    def draw(self):
        c=self.calendar;w,h=c.winfo_width(),c.winfo_height()
        if min(w,h)<2:return
        c.delete('all');self.hits=[];q=3;im=Image.new('RGB',(w*q,h*q),C['card']);d=ImageDraw.Draw(im);texts=[]
        if self.mode!='days':
            values=range(1,13) if self.mode=='months' else range(max(1,min(9988,self.year-5)),max(1,min(9988,self.year-5))+12)
            for i,v in enumerate(values):
                x0=(i%3)*w/3;y0=(i//3)*h/4;x1=x0+w/3;y1=y0+h/4
                self.hits.append(((x0,y0,x1,y1),v));texts.append(((x0+x1)/2,(y0+y1)/2,str(v)+('月' if self.mode=='months' else ''),C['fg']))
        else:
            header=round(26*self.s);cell=w/7;rh=(h-header)/6
            for col,word in enumerate('一二三四五六日'):texts.append((cell*(col+.5),header/2,word,C['muted']))
            weeks=calendar.monthcalendar(self.year,self.month)
            start=self.selected if self.endpoint=='start' else self.start;end=self.selected if self.endpoint=='end' else self.end
            for row,week in enumerate(weeks):
                for col,day in enumerate(week):
                    if not day:continue
                    date=dt.date(self.year,self.month,day);x0=col*cell;y0=header+row*rh;x1=x0+cell;y1=y0+rh;cx=(x0+x1)/2;cy=(y0+y1)/2;radius=min(cell,rh)*.40
                    self.hits.append(((x0,y0,x1,y1),date));inside=start and end and start<=date<=end
                    if inside:d.rectangle((x0*q,(cy-radius)*q,x1*q,(cy+radius)*q),fill='#E6DCF8')
                    on=date==self.selected or bool(inside and date in (start,end));today=date==dt.date.today()
                    if on or today:d.ellipse(((cx-radius)*q,(cy-radius)*q,(cx+radius)*q,(cy+radius)*q),fill=theme.accent if on else C['card'],outline=theme.accent,width=q)
                    texts.append((cx,cy,str(day),'white' if on else C['fg'] if self.valid(date) else '#BCB5CB'))
        self.photo=ImageTk.PhotoImage(im.resize((w,h),Image.Resampling.LANCZOS),master=c);c.create_image(0,0,image=self.photo,anchor='nw')
        for x,y,text,color in texts:c.create_text(x,y,text=text,fill=color,font=theme.font(delta=-1))

def pick_date(parent,app,variable,**kwargs):
    old=getattr(parent,'_date_popup',None)
    if old is not None and old.winfo_exists():old.destroy();return None
    anchor=kwargs.pop('anchor',getattr(parent,'_date_anchor',None))
    parent._date_anchor=None
    win=DatePicker(parent,app,variable.get(),anchor=anchor,**kwargs);parent._date_popup=win
    parent.wait_window(win);parent._date_popup=None
    if win.result is not None:variable.set(win.result)
    return win.result
