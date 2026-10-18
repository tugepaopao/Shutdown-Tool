"""Queue cards keep the existing queue operations and selection contract."""
import tkinter as tk
from ui_focus import current_grab, current_focus
from tkinter import ttk
from PIL import Image,ImageDraw,ImageTk
from theme import theme,flat_button,enable_button
from ui_cozy import CozyFrame,CozyButton,scale,cozy_icon
from ui_dialog_palette import COLORS as C
from i18n import feature_text
from ui_runtime_context import blossom


class CircleButton(CozyButton):
    """True circular controls with antialiased symbols, retaining Button semantics."""
    def __init__(self,parent,command,accent=False):
        self.accent=accent;self.paused=False;self._circle_stamp=None
        bg=theme.accent if accent else '#ECE7FC'
        self._bg=bg;self._hover='#7A39DF' if accent else C['hover'];self._fg='white' if accent else C['fg'];self._kind='accent' if accent else 'normal'
        super().__init__(parent,command=command,text='',bg=bg,fg=self._fg,activebackground=self._hover,font=theme.font(),cursor='hand2')
    def _paint(self):
        self._draw_job=None
        if not self.winfo_exists():return
        w=self.winfo_width() if self.winfo_width()>1 else round(40*scale(self));h=self.winfo_height() if self.winfo_height()>1 else w
        disabled=self._state=='disabled';focused=current_focus(self) is self and self._keyboard_focus
        key=(w,h,self.paused,disabled,self._hovering,self._pressed,focused,theme.accent,self.master.cget('bg'))
        if key==self._circle_stamp:return
        self._circle_stamp=key;q=4;im=Image.new('RGB',(w*q,h*q),self.master.cget('bg'));d=ImageDraw.Draw(im)
        size=min(w,h)*q;cx=w*q/2;cy=h*q/2;r=size/2-2*q
        bg=C['selected'] if disabled else ('#6D24D5' if self._hovering or self._pressed else theme.accent) if self.accent else C['hover'] if self._hovering or self._pressed else '#ECE7FC'
        d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=bg,outline=theme.accent if focused else bg,width=q)
        ink='white' if self.accent else C['fg']
        if self.accent:
            if self.paused:d.polygon([(cx-size*.11,cy-size*.19),(cx+size*.19,cy),(cx-size*.11,cy+size*.19)],fill=ink)
            else:
                for x in (-.13,.07):d.rounded_rectangle((cx+x*size,cy-size*.17,cx+(x+.07)*size,cy+size*.17),radius=q,fill=ink)
        else:
            for x in (-.16,0,.16):d.ellipse((cx+x*size-size*.028,cy-size*.028,cx+x*size+size*.028,cy+size*.028),fill=ink)
        self._circle_photo=ImageTk.PhotoImage(im.resize((w,h),Image.Resampling.LANCZOS),master=self)
        tk.Button.configure(self,image=self._circle_photo,bg=self.master.cget('bg'),activebackground=self.master.cget('bg'))
    def set_paused(self,value):
        if self.paused!=value:self.paused=value;self._schedule()

class QueueCards:
    def __init__(self,view):
        self.view=view;self.app=view.app;self.s=scale(view);self.signature=None;self.rows={};self.flower_key=None
        self.tv=view.tv=ttk.Treeview(view,columns=('when','action','note'),show='headings',selectmode='extended')
        self.tv.bind('<<TreeviewSelect>>',lambda e:self.paint_selection())
        self.current=CozyFrame(view,bg=C['card']);self.current.pack(fill='x',padx=4,pady=(3,8))
        inner=tk.Frame(self.current,bg=C['card']);inner.pack(fill='x',padx=12,pady=10)
        self.flower=tk.Label(inner,bg=C['card']);self.flower.pack(side='left',padx=(0,14))
        for attr,command,accent in [('more_current',self.current_menu,False),('pause',self.toggle_pause,True)]:
            slot=tk.Frame(inner,bg=C['card'],width=round(40*self.s),height=round(40*self.s));slot.pack(side='right',padx=(7,0) if not accent else 0);slot.pack_propagate(False)
            button=CircleButton(slot,command,accent);button.pack(fill='both',expand=True);setattr(self,attr,button)
        texts=tk.Frame(inner,bg=C['card']);texts.pack(side='left',fill='x',expand=True)
        self.caption=self.label(texts,'当前任务',small=True);self.caption.pack(fill='x')
        self.title=self.label(texts,'',bold=True);self.title.config(wraplength=round(390*self.s));self.title.pack(fill='x',pady=3)
        self.subtitle=self.label(texts,'',small=True);self.subtitle.config(wraplength=round(390*self.s));self.subtitle.pack(fill='x')
        from ui_window import wrap_to_width
        wrap_to_width(self.title);wrap_to_width(self.subtitle)
        self.wait_label=self.label(view,'等待队列 · 前一项完成后自动开始下一项',small=True);self.wait_label.pack(fill='x',padx=6,pady=(0,7))
        self.card=CozyFrame(view,bg=C['card']);self.card.pack(fill='both',expand=True,padx=4)
        wrap=tk.Frame(self.card,bg=C['card']);wrap.pack(fill='both',expand=True,padx=round(10*self.s),pady=(round(10*self.s),0))
        wrap.columnconfigure(0,weight=1);wrap.rowconfigure(1,weight=1)
        self.header=tk.Frame(wrap,bg=C['card']);self.header.grid(row=0,column=0,sticky='ew',pady=(0,4))
        self.headings=[]
        for i,title in enumerate(('顺序','任务','执行条件','操作')):
            heading=self.label(self.header,title,small=True);heading.config(width=1,anchor='center' if i in (0,3) else 'w')
            heading.grid(row=0,column=i,sticky='ew',padx=round(6*self.s));self.headings.append(heading)
        self.canvas=tk.Canvas(wrap,bg=C['card'],highlightthickness=0,height=round(175*self.s));self.canvas.grid(row=1,column=0,sticky='nsew')
        scrollbar=ttk.Scrollbar(wrap,command=self.canvas.yview);scrollbar.grid(row=1,column=1,sticky='ns');self.canvas.config(yscrollcommand=scrollbar.set)
        self.body=tk.Frame(self.canvas,bg=C['card']);self.body_item=self.canvas.create_window(0,0,window=self.body,anchor='nw')
        self.body.bind('<Configure>',lambda e:self.canvas.config(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>',lambda e:self.layout_columns(e.width))
        view.bind('<MouseWheel>',lambda e:self.canvas.yview_scroll(-int(e.delta/120),'units'),add='+')
        foot=tk.Frame(self.card,bg=C['card']);foot.pack(side='bottom',before=wrap,fill='x',padx=14,pady=8)
        self.selection_label=self.label(foot,'',small=True);self.selection_label.pack(side='left')
        self.down=flat_button(foot,self.tr('下移'),lambda:view._move(1),width=7,padx=5,pady=4);self.down.pack(side='right')
        self.up=flat_button(foot,self.tr('上移'),lambda:view._move(-1),width=7,padx=5,pady=4);self.up.pack(side='right',padx=6)
        bar=tk.Frame(view,bg=C['bg']);bar.pack(side='bottom',before=self.card,fill='x',padx=4,pady=(8,4))
        for i,(label,fn,kind) in enumerate([('保存为模板',view._template,'accent'),('撤销上一次删除',view._undo,'normal'),('更多操作',self.menu,'normal')]):
            bar.columnconfigure(i,weight=1,uniform='queueactions')
            button=flat_button(bar,self.tr(label),fn,kind=kind,padx=8,pady=7,font=theme.font(delta=-1));button.grid(row=0,column=i,sticky='ew',padx=(0,5) if i<2 else 0)
            if i>0:button._selection_outline='#D8CDEF';button._last_paint=None
            if i==1:self.undo=button
            if i==2:
                self.more_button=button
                im=Image.new('RGBA',(48,48));d=ImageDraw.Draw(im);d.line([(10,17),(24,31),(38,17)],fill=C['fg'],width=5,joint='curve')
                button._theme_photo=ImageTk.PhotoImage(im.resize((round(11*self.s),round(11*self.s)),Image.Resampling.LANCZOS),master=view);button.config(image=button._theme_photo,compound='right')
        self.refresh()
    def layout_columns(self,width=None):
        # One pixel layout for headings and every row, excluding the scrollbar gutter.
        width=max(1,width or self.canvas.winfo_width())
        self.canvas.itemconfigure(self.body_item,width=width)
        order=round(44*self.s);actions=round(78*self.s)
        available=max(2,width-order-actions);task=round(available*.40)
        widths=(order,task,available-task,actions);gap=round(6*self.s)
        # Align the heading with the text after the task icon, not the icon itself.
        self.headings[1].grid_configure(padx=(gap+round(20*self.s),gap))
        for frame in [self.header]+[widgets[0] for widgets in self.rows.values()]:
            for i,value in enumerate(widths):frame.columnconfigure(i,minsize=value,weight=0)
        for row,number,title,condition,buttons in self.rows.values():
            title.config(wraplength=max(1,task-2*gap-round(30*self.s)))
            condition.config(wraplength=max(1,widths[2]-2*gap))
    def toggle_pause(self):
        self.app.toggle_pause();self.refresh()
    def tr(self,t):return feature_text(self.app.T,t)
    def label(self,p,text,small=False,bold=False):return tk.Label(p,text=self.tr(text),bg=p.cget('bg'),fg=C['muted'] if small else C['fg'],font=theme.font(delta=-2 if small else 0,bold=bold),anchor='w',justify='left',bd=0,padx=0)
    def refresh(self):
        running=self.app.engine.is_running();active=self.app._active_task or {};identifier=active.get('id') if running else None
        tasks=[t for t in self.app.get_queue() if t.get('id')!=identifier]
        signature=(repr(tasks),identifier,self.app.T.lang)
        if signature!=self.signature:
            self.signature=signature;keep=self.tv.selection()
            for child in self.body.winfo_children():child.destroy()
            self.rows={}
            for iid in self.tv.get_children():self.tv.delete(iid)
            for index,task in enumerate(tasks,1):
                iid=str(task['id']);when=self.app.describe_when(task)
                if task.get('mode')=='countdown':when=self.tr('前一项完成后')+' '+when
                name=task.get('name') or self.app.describe_action(task)
                self.tv.insert('','end',iid=iid,values=(when,name,self.app.describe_note(task)))
                row=CozyFrame(self.body,bg=C['card']);row.pack(fill='x',pady=2)
                number=self.label(row,str(index));number.config(width=1,anchor='center');number.grid(row=0,column=0,padx=round(6*self.s),pady=11,sticky='ew')
                title=self.label(row,name,bold=True);title.config(width=1,wraplength=round(155*self.s));title._user_text=True;title._photo=cozy_icon(row,{'message':'message','lock':'lock','shutdown':'power'}.get(task.get('action'),'clock'),round(20*self.s));title.config(image=title._photo,compound='left',padx=0);title.grid(row=0,column=1,sticky='ew',padx=round(6*self.s))
                condition=self.label(row,when,small=True);condition.config(width=1,wraplength=round(220*self.s));condition.grid(row=0,column=2,sticky='ew',padx=round(6*self.s))
                actions=tk.Frame(row,bg=C['card']);actions.grid(row=0,column=3,padx=5)
                edit=flat_button(actions,self.tr('编辑'),lambda i=iid:self.row_action(i,self.view._edit),padx=6,pady=4,font=theme.font(delta=-2));edit.pack(side='left')
                for widget in (row,number,title,condition):
                    widget.bind('<Button-1>',lambda e,i=iid:self.select(i,e.state&4));widget.bind('<Double-1>',lambda e,i=iid:self.row_action(i,self.view._edit));widget.bind('<MouseWheel>',lambda e:self.canvas.yview_scroll(-int(e.delta/120),'units'))
                self.rows[iid]=(row,number,title,condition,actions)
            if not tasks:self.label(self.body,'队列为空，将当前设定加入队列即可开始',small=True).pack(pady=35,padx=12)
            self.layout_columns()
            self.tv.selection_set([i for i in keep if self.tv.exists(i)])
        self.caption.config(text=self.tr('当前任务'))
        self.title.config(text=' · '.join(self.app.summary_title.cget('text').split(' · ')[:2]) if running else self.tr('就绪'))
        from i18n import format_remain
        self.subtitle.config(text=self.tr('剩余 {t}').format(t=format_remain(self.app.engine.remaining(),self.app.T))+' · '+self.app.status.cget('text') if running else self.tr('当前没有正在运行的任务'))
        self.wait_label.config(text=self.tr('等待队列 · 前一项完成后自动开始下一项'))
        self.pause.set_paused(self.app.engine.paused);enable_button(self.pause,running);enable_button(self.more_current,running)
        key=(round(float(self.app.progress['value'])),running)
        if key!=self.flower_key:
            self.flower_key=key;self.flower._photo=ImageTk.PhotoImage(blossom(round(48*self.s),key[0],running),master=self.view);self.flower.config(image=self.flower._photo)
        self.paint_selection()
    def paint_selection(self):
        selected=self.tv.selection()
        for iid,widgets in self.rows.items():
            color=C['hover'] if iid in selected else C['card']
            changed=widgets[0].cget('bg')!=color
            for widget in widgets:widget.config(bg=color)
            if changed:
                for button in widgets[-1].winfo_children():button._last_paint=None;button._schedule()
        self.selection_label.config(text=self.tr('选中 {n} 项').format(n=len(selected)))
        enable_button(self.up,bool(selected));enable_button(self.down,bool(selected))
        enable_button(self.undo,self.app.undo.available())
    def select(self,iid,multi=False):
        if multi and iid in self.tv.selection():self.tv.selection_remove(iid)
        elif multi:self.tv.selection_add(iid)
        else:self.tv.selection_set(iid)
        self.paint_selection()
    def row_action(self,iid,fn):self.select(iid);fn()
    def popup(self,items,anchor,title=None,icons=None):
        from ui_popup_menu import VioletMenu
        old=getattr(self,'popup_window',None)
        if old and old.winfo_exists():old.dismiss()
        menu=tk.Menu(self.view,tearoff=0)
        for label,fn in items:menu.add_command(label=self.tr(label),command=fn)
        self.popup_window=VioletMenu(self.app,menu,anchor=anchor,title=self.tr(title) if title else None,icons=icons)
    def menu(self):self.popup([('复制任务',self.view._copy),('删除选中',self.view._remove),('清空队列',self.view._clear)],self.more_button,title='更多操作',icons=('copy','clear','broom'))
    def current_menu(self):self.popup([('停止当前任务',self.app.stop_timer)]+[('延后'+str(n)+'分钟',lambda m=n:self.app.postpone(m)) for n in (5,10,30)],self.more_current)
