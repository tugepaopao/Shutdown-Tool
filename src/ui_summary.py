"""Compact two-line status strip matching the approved reference."""
import math
import tkinter as tk
from tkinter import ttk
from theme import theme,flat_button,enable_button,blend
from i18n import feature_text

class ProgressStrip(tk.Canvas):
    """Five-pixel progress without the native theme's clipped inner element.

    Keep the value/maximum configuration contract used by the timer UI.
    """
    def __init__(self,parent,maximum=100.0):
        self._value=0.0;self._shown=0.0;self._animation=None;self._maximum=float(maximum)
        super().__init__(parent,width=1,height=5,bg=theme.c('divider'),bd=0,highlightthickness=0)
        self._track=self.create_line(2,2,2,2,width=3,capstyle='round')
        self._fill=self.create_rectangle(0,0,0,5,fill=theme.accent,outline='')
        self.bind('<Configure>',lambda e:self.redraw())
        self.bind('<Destroy>',self._dispose,add='+')
    def configure(self,cnf=None,**kw):
        if isinstance(cnf,dict):kw={**cnf,**kw};cnf=None
        changed=False
        for option,attr in (('value','_value'),('maximum','_maximum')):
            if option in kw:setattr(self,attr,float(kw.pop(option)));changed=True
        result=super().configure(cnf,**kw) if cnf is not None or kw or not changed else None
        if hasattr(self,'_fill'):
            if changed and self._animation is None:self._step()
            else:self.redraw()
        return result
    config=configure
    def cget(self,key):
        if key=='value':return self._value
        if key=='maximum':return self._maximum
        return super().cget(key)
    __getitem__=cget
    def _dispose(self,event):
        if event.widget is self and self._animation:self.after_cancel(self._animation);self._animation=None
    def _step(self):
        self._animation=None;delta=self._value-self._shown
        self._shown=self._value if abs(delta)<.05 else self._shown+delta*.28
        self.redraw()
        if self._shown!=self._value:self._animation=self.after(16,self._step)
    def redraw(self):
        percent=max(0,min(1,self._shown/self._maximum)) if self._maximum>0 else 0
        width=round(self.winfo_width()*percent)
        middle=self.winfo_height()/2
        self.coords(self._track,2,middle,max(2,self.winfo_width()-2),middle)
        self.itemconfigure(self._track,fill=blend(theme.accent,'#FFFFFF',.72))
        self.coords(self._fill,0,0,width,self.winfo_height())
        self.itemconfigure(self._fill,fill=theme.accent,state='normal' if width else 'hidden')
        super().configure(bg=theme.c('divider'))

def control_icon(app,paused):
    # The main Start button uses a white play asset. This light card needs
    # its own contrasting glyph for both pause and resume.
    from PIL import Image,ImageDraw,ImageTk
    cache=getattr(app,'_summary_icon_cache',None)
    if cache is None:app._summary_icon_cache={};cache=app._summary_icon_cache
    key=(paused,theme.accent)
    if key not in cache:
        im=Image.new('RGBA',(56,56));draw=ImageDraw.Draw(im)
        if paused:draw.polygon([(17,9),(44,28),(17,47)],fill=theme.accent)
        else:
            draw.rounded_rectangle((13,9,23,47),radius=3,fill=theme.accent)
            draw.rounded_rectangle((33,9,43,47),radius=3,fill=theme.accent)
        cache[key]=ImageTk.PhotoImage(im.resize((14,14),Image.Resampling.LANCZOS))
    return cache[key]

def build(app,parent):
    from ui_cozy import CozyFrame
    app.sbar=CozyFrame(parent,bg=theme.c('card'),highlightthickness=0,highlightbackground=theme.c('card_border'))
    app.sbar.pack(fill='x',pady=(3,0))
    line=tk.Frame(app.sbar,bg=theme.c('card'));line.pack(fill='x',padx=10,pady=(7,4))
    app.summary_ring=tk.Canvas(line,width=32,height=32,bg=theme.c('card'),highlightthickness=0);app.summary_ring.pack(side='left',padx=(0,10))
    controls=tk.Frame(line,bg=theme.c('card'));controls.pack(side='right',padx=(8,0))
    for index,(attr,text,command) in enumerate((('summary_pause','Ⅱ',app.toggle_pause),('summary_stop','×',app.stop_timer))):
        from ui_cozy import scale
        slot=tk.Frame(controls,width=round(32*scale(controls)),height=round(30*scale(controls)),bg=theme.c('card'),highlightthickness=0,highlightbackground=theme.c('card_border'));slot.pack(side='left',padx=(0,7) if index==0 else 0);slot.pack_propagate(False)
        b=flat_button(slot,text,command,padx=0,pady=0,font=theme.font(bold=True));b._bare_glyph=True;b.configure(highlightthickness=0);b.pack(fill='both',expand=True);setattr(app,attr,b)
    text=tk.Frame(line,bg=theme.c('card'));text.pack(side='left',fill='x',expand=True)
    headline=tk.Frame(text,bg=theme.c('card'));headline.pack(fill='x')
    app.summary_dot=tk.Canvas(headline,width=10,height=12,bg=theme.c('card'),highlightthickness=0);app.summary_dot.pack(side='left',padx=(0,6))
    app.summary_title=tk.Label(headline,text=feature_text(app.T,'就绪'),anchor='w',bg=theme.c('card'),fg=theme.c('fg'),font=theme.font(bold=True));app.summary_title.pack(side='left',fill='x',expand=True)
    app.status=tk.Label(text,text=app.T('status_idle'),bg=theme.c('card'),fg=theme.c('fg_dim'),font=theme.font(delta=-1),anchor='w',justify='left',height=1);app.status.pack(fill='x',pady=(1,0))
    track=tk.Frame(app.sbar,height=5,bg=theme.c('divider'));track.pack(fill='x',padx=10,pady=(0,7));track.pack_propagate(False)
    app.progress=ProgressStrip(track,maximum=100.0);app.progress.pack(fill='both',expand=True)
    refresh(app)

def refresh(app):
    if not hasattr(app,'summary_ring'):return
    app.progress.redraw()
    running=app.engine.is_running();paused=app.engine.paused;lang=app.T.lang
    title=feature_text(app.T,'就绪')
    if running:
        task=app._active_task or {'action':app._current_action()}
        action=app.describe_action(task)
        if task.get('action')=='message':action={'EN':'Message box','CHT':'提示框','CHS':'提示框'}[lang]
        remaining=max(0,int(app.engine.remaining()));minutes=math.ceil(remaining/60)
        delay=(f'in {minutes} min' if remaining>=60 else f'in {remaining} sec') if lang=='EN' else (f'{minutes}分鐘後執行' if remaining>=60 else f'{remaining}秒後執行') if lang=='CHT' else (f'{minutes}分钟后执行' if remaining>=60 else f'{remaining}秒后执行')
        single=('Repeat' if app.engine.mode=='interval' else 'Once') if lang=='EN' else ('循環' if lang=='CHT' else '循环') if app.engine.mode=='interval' else ('單次' if lang=='CHT' else '单次')
        title=action+' · '+single+' · '+(('Paused' if lang=='EN' else '已暫停' if lang=='CHT' else '已暂停') if paused else delay)
        due=app.engine.due_at()
        if due:
            import datetime as dt
            weekdays=('Mon','Tue','Wed','Thu','Fri','Sat','Sun') if lang=='EN' else ('週一','週二','週三','週四','週五','週六','週日') if lang=='CHT' else ('周一','周二','周三','周四','周五','周六','周日')
            when=due.strftime('%H:%M') if due.date()==dt.datetime.now().date() else due.strftime('%m-%d ')+weekdays[due.weekday()]+due.strftime(' %H:%M')
            state=('Paused' if paused else 'Counting down') if lang=='EN' else ('已暫停' if paused else '正在計時') if lang=='CHT' else ('已暂停' if paused else '正在计时')
            from ui_runtime_context import edited
            if edited(app):state+=' · '+('Editing next' if lang=='EN' else '編輯下次設定' if lang=='CHT' else '编辑下次设定')
            app.status.config(text=('Due ' if lang=='EN' else '預計 ' if lang=='CHT' else '预计 ')+when+' · '+state)
    app.summary_title.config(text=title)
    import tkinter.font as font
    for w,bold in ((app.summary_title,True),(app.status,False)):
        if w.winfo_width()<=1:continue
        for delta in ((0,-1,-2,-3) if bold else (-1,-2,-3)):
            selected=theme.font(delta=delta,bold=bold)
            if font.Font(root=w,font=selected).measure(w.cget('text'))<=max(1,w.winfo_width()-4):break
        w.config(font=selected)
    enable_button(app.summary_pause,running);enable_button(app.summary_stop,running)
    app.summary_pause._theme_photo=control_icon(app,paused)
    app.summary_pause.config(text='',image=app.summary_pause._theme_photo)
    from ui_runtime_context import paint
    paint(app)
    dot=app.summary_dot;dot.delete('all');dot.create_oval(1,2,9,10,outline='',fill=theme.c('fg_muted') if not running else ('#e3a533' if paused else '#26b850'))
    renderer=getattr(app,'skin_renderer',None)
    if renderer:renderer.canvas_backgrounds()
