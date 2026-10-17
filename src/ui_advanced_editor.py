"""Task editors follow the approved compact, rounded calendar composition."""
import datetime as dt
import calendar
import os
import tkinter as tk
from tkinter import ttk
from PIL import ImageTk
from theme import theme,flat_button
from ui_cozy import CozyFrame,scale,cozy_icon
from ui_dialog_palette import COLORS as C
from ui_window import compact_show,prepare,show
from ui_runtime_context import blossom
from ui_soft_controls import SoftInput,SoftChoice,Segments,SoftToggle,SoftRadio

class AdvancedLayout:
    def __init__(self,e,modes,title,parent):
        from ui_tasks import MODE_NAMES,REPEAT_NAMES,ACTION_NAMES
        from actions import action_label
        self.e=e;self.s=scale(e);e.T=e.app.T;e.advanced_layout=self;e.v={};e.rows={}
        self.advanced=bool(modes and 'countdown' not in modes);e.mode_keys=list(modes or MODE_NAMES)
        e.title('编辑高级任务' if self.advanced else title);e.config(bg=C['bg']);e.transient(parent or e.app.root);e.resizable(False,False)
        self.footer=tk.Frame(e,bg=C['bg']);self.footer.pack(side='bottom',fill='x',padx=self.p(8),pady=self.p(8))
        for text,fn,kind in [('保存任务',e.save,'accent'),('取消',e.destroy,'normal')]:
            slot=tk.Frame(self.footer,bg=C['bg'],width=self.p(150),height=self.p(38));slot.pack(side='right',padx=(self.p(8),0));slot.pack_propagate(False)
            b=flat_button(slot,text,fn,kind=kind,font=theme.font(),padx=8,pady=7);b._selection_outline='#D8CDEF';b.pack(fill='both',expand=True)
        wrap=tk.Frame(e,bg=C['bg']);wrap.pack(fill='both',expand=True,padx=self.p(7),pady=(self.p(5),0))
        self.canvas=tk.Canvas(wrap,bg=C['bg'],highlightthickness=0);self.canvas.pack(side='left',fill='both',expand=True)
        self.scroll=ttk.Scrollbar(wrap,command=self.canvas.yview);self.canvas.config(yscrollcommand=self.scroll.set)
        e.body=self.body=tk.Frame(self.canvas,bg=C['bg']);self.item=self.canvas.create_window(0,0,window=self.body,anchor='nw')
        self.canvas.bind('<Configure>',self.resize);self.body.bind('<Configure>',self.resize);e.bind('<MouseWheel>',self.wheel,add='+')
        at=dt.datetime.fromisoformat(e.original.get('at',(dt.datetime.now()+dt.timedelta(days=1)).isoformat()))
        defaults=dict(name=e.original.get('name',''),clock=at.strftime('%H:%M' if not at.second else '%H:%M:%S'),date=at.date().isoformat(),end_date=e.original.get('end_date',at.date().isoformat()),
            seconds=e.original.get('seconds',60),weekday=int(e.original.get('weekday',0))+1,folder=e.original.get('folder',os.path.expanduser('~/Downloads')),
            threshold_kib=e.original.get('threshold_kib',10),idle_seconds=e.original.get('idle_seconds',60),timeout_hours=float(e.original.get('timeout_seconds',43200))/3600,
            user_idle_minutes=float(e.original.get('user_idle_seconds',600))/60,prepare_path=e.original.get('prepare_path',''),prepare_args=e.original.get('prepare_args',''))
        if e.original.get('mode')=='datetime':defaults['clock']='%02d:%02d:%02d'%tuple(e.original.get(k,0) for k in ('hour','minute','second'))
        for k,v in defaults.items():e.v[k]=tk.StringVar(e,value=str(v))
        action=e.original.get('action','message');key={'close_program':'close_program_path','run_program':'program_path','play_sound':'sound_file','message':'message_text'}.get(action,'message_text')
        e.v['parameter']=tk.StringVar(e,value=e.original.get(key,e.app.cfg.get(key,'')));e.force=tk.BooleanVar(e,value=bool(e.original.get('force_close_apps',False)));e._parameter_action=action
        top=self.card();top.columnconfigure(1,weight=3,uniform='top');top.columnconfigure(2,weight=2,uniform='top')
        flower=tk.Label(top,bg=C['card']);flower.photo=ImageTk.PhotoImage(blossom(self.p(48),0,False),master=e);flower.config(image=flower.photo);flower.grid(row=0,column=0,rowspan=2,padx=(0,self.p(16)))
        self.lab(top,'任务名称').grid(row=0,column=1,sticky='w',pady=(0,self.p(4)))
        self.lab(top,'执行操作').grid(row=0,column=2,sticky='w',padx=(self.p(12),0),pady=(0,self.p(4)))
        self.name_input=SoftInput(top,e.v['name']);self.name_input.grid(row=1,column=1,sticky='ew')
        e.action=SoftChoice(top,e.app,[action_label(a,e.T) for a in ACTION_NAMES],extra=('操作参数…',self.parameters))
        e.action.grid(row=1,column=2,sticky='ew',padx=(self.p(12),0));e.action.current(ACTION_NAMES.index('close_program' if action=='monitor_off' else action));e.action.bind('<<ComboboxSelected>>',self.action_selected)
        e.mode=ttk.Combobox(e,state='readonly',values=list(MODE_NAMES))
        current=e.original.get('mode','calendar' if self.advanced else 'countdown');e.mode.current(e.mode_keys.index(current) if current in e.mode_keys else 0)
        self.calendar=self.card();self.calendar.columnconfigure(1,weight=1);self.calendar.columnconfigure(0,minsize=self.p(106))
        self.heading=self.heading_label(self.calendar,'重复规则','calendar');self.heading.grid(row=0,column=0,sticky='nw',pady=(self.p(3),0))
        self.heading.bind('<Button-1>',lambda ev:self.mode_menu());self.heading.config(cursor='hand2')
        from ui_settings_controls import Tooltip
        Tooltip(self.heading,'点击切换执行方式：预约、下载、网络或程序链');Tooltip(e.action,'选择操作；菜单底部可设置程序路径、消息内容和强制关闭选项')
        self.repeat_keys=('once','daily','weekly','custom');self.repeat_value=e.original.get('repeat','once')
        e.repeat=ttk.Combobox(e,state='readonly',values=list(REPEAT_NAMES));e.repeat.current(list(REPEAT_NAMES).index(self.repeat_value))
        self.segment=Segments(self.calendar,['仅一次','每天','每周','自定义'],lambda i:self.set_repeat(self.repeat_keys[i]))
        self.segment.grid(row=0,column=1,sticky='ew',pady=(self.p(17),self.p(12)))
        self.day_label=self.lab(self.calendar,'重复星期');self.day_label.grid(row=1,column=0,sticky='w')
        self.dayrow=tk.Frame(self.calendar,bg=C['card']);self.dayrow.grid(row=1,column=1,sticky='ew',pady=(0,self.p(10)))
        days={'workdays':list(range(5)),'weekends':[5,6],'daily':list(range(7))}.get(self.repeat_value,[at.weekday()])
        self.days=[tk.BooleanVar(e,value=i in e.original.get('weekdays',days)) for i in range(7)];self.day_buttons=[]
        for i,name in enumerate('一二三四五六日'):
            self.dayrow.columnconfigure(i,weight=1,uniform='days')
            slot=tk.Frame(self.dayrow,bg=C['card'],height=self.p(38));slot.grid(row=0,column=i,sticky='ew',padx=(0,self.p(10)) if i<6 else 0);slot.pack_propagate(False)
            b=flat_button(slot,name,lambda i=i:self.toggle_day(i),font=theme.font(),padx=2,pady=4);b.pack(fill='both',expand=True);self.day_buttons.append(b)
        self.inputs={};self.calendar_labels={}
        for row,key,text,icon in [(2,'clock','执行时间','clock'),(3,'date','开始日期','calendar'),(4,'end_date','结束日期','calendar')]:
            lab=self.lab(self.calendar,text);lab.grid(row=row,column=0,sticky='w');self.calendar_labels[key]=lab
            line=tk.Frame(self.calendar,bg=C['card']);line.grid(row=row,column=1,sticky='ew',pady=self.p(4));e.rows[key]=line
            if key=='end_date':
                self.end_enabled=tk.BooleanVar(e,value=bool(e.original.get('end_date')))
                SoftToggle(line,self.end_enabled,self.end_changed).pack(side='left',padx=(0,self.p(25)))
            control=SoftInput(line,e.v[key],width=195 if key!='end_date' else 207,icon=icon,command=(lambda k=key:self.date_picker(e.v[k])) if icon=='calendar' else None)
            control.pack(side='left');self.inputs[key]=control
        self.end_changed()
        self.exceptions=self.card();self.exceptions.columnconfigure(0,minsize=self.p(106));self.exceptions.columnconfigure(1,weight=1)
        self.heading_label(self.exceptions,'例外日期','exclude').grid(row=0,column=0,sticky='nw',pady=self.p(2))
        self.exception_dates=list(e.original.get('exception_dates',[]));self.chips=tk.Frame(self.exceptions,bg=C['card']);self.chips.grid(row=0,column=1,sticky='ew',pady=(self.p(12),0))
        self.lab(self.exceptions,'这些日期将跳过执行',muted=True).grid(row=1,column=1,sticky='w',pady=(self.p(7),self.p(2)));self.paint_dates()
        self.missed=self.card();self.policy=tk.StringVar(e,value=e.original.get('missed_policy','skip'))
        mh=self.heading_label(self.missed,'错过执行处理','gear');mh.pack(side='left',padx=(0,self.p(18)));mh.config(cursor='hand2');mh.bind('<Button-1>',lambda ev:self.policy_menu(mh));Tooltip(mh,'点击查看全部错过处理策略')
        SoftRadio(self.missed,self.policy,'skip','跳过，不补执行').pack(side='left',padx=(0,self.p(4)))
        self.ask_radio=SoftRadio(self.missed,self.policy,'ask','下次启动后询问')
        self.run_radio=SoftRadio(self.missed,self.policy,'run','启动后执行一次')
        self.policy.trace_add('write',lambda *a:self.paint_policy());self.paint_policy()
        self.conditions=self.card();self.conditions.columnconfigure(1,weight=1);self.conditions.columnconfigure(0,minsize=self.p(106))
        self.condition_heading=self.heading_label(self.conditions,'执行方式','clock');self.condition_heading.grid(row=0,column=0,sticky='w')
        self.condition_heading.bind('<Button-1>',lambda ev:self.mode_menu());self.condition_heading.config(cursor='hand2')
        self.mode_choice=SoftChoice(self.conditions,e.app,[MODE_NAMES[k] for k in e.mode_keys]);self.mode_choice.grid(row=0,column=1,sticky='ew',pady=(0,self.p(8)))
        self.mode_choice.bind('<<ComboboxSelected>>',lambda ev:(e.mode.current(self.mode_choice.current()),self.update_fields()))
        self.condition_rows={}
        for index,(key,text) in enumerate([('seconds','时长（秒）'),('weekday','执行星期（1–7）'),('folder','下载文件夹'),('threshold_kib','网络阈值（KB/s）'),('idle_seconds','连续安静（秒）'),('timeout_hours','最长等待（小时）'),('user_idle_minutes','无人操作（分钟）'),('prepare_path','前置程序'),('prepare_args','程序参数')],1):
            line=tk.Frame(self.conditions,bg=C['card']);line.grid(row=index,column=0,columnspan=2,sticky='ew',pady=self.p(4));line.columnconfigure(1,weight=1);line.columnconfigure(0,minsize=self.p(106))
            self.lab(line,text).grid(row=0,column=0,sticky='w');SoftInput(line,e.v[key]).grid(row=0,column=1,sticky='ew');self.condition_rows[key]=line;e.rows[key]=line
            if key in ('folder','prepare_path'):
                flat_button(line,'浏览',e.pick_folder if key=='folder' else e.pick_prepare,font=theme.font(delta=-1),pady=4).grid(row=0,column=2,padx=(self.p(6),0))
        self.normal_clock=tk.Frame(self.conditions,bg=C['card']);self.normal_clock.columnconfigure(0,minsize=self.p(106))
        self.lab(self.normal_clock,'执行时间').grid(row=0,column=0,sticky='w');SoftInput(self.normal_clock,e.v['clock'],icon='clock').grid(row=0,column=1,sticky='ew');self.normal_clock.columnconfigure(1,weight=1)
        self.update_fields();e.app._apply_window_chrome(e);e.bind('<Escape>',lambda ev:e.destroy());compact_show(e,e.app,height=624 if self.advanced or current=='calendar' else 300,width=600);e.grab_set();e.focus_set()
    def p(self,v):return round(v*self.s)
    def lab(self,parent,text,muted=False):return tk.Label(parent,text=text,bg=C['card'],fg='#968DAA' if muted else C['muted'],font=theme.font(delta=-1),anchor='w',bd=0)
    def heading_label(self,parent,text,icon):
        lab=tk.Label(parent,text=' '+text,bg=C['card'],fg=C['fg'],font=theme.font(bold=True),anchor='w',compound='left',bd=0)
        lab.photo=cozy_icon(parent,icon,self.p(21),ink=theme.accent);lab.config(image=lab.photo);return lab
    def card(self):
        card=CozyFrame(self.body,bg=C['card'],radius=18);card.pack(fill='x',pady=(0,self.p(7)))
        inner=tk.Frame(card,bg=C['card']);inner.pack(fill='x',padx=self.p(16),pady=self.p(14));inner.card=card;return inner
    def resize(self,event=None):
        self.canvas.itemconfigure(self.item,width=self.canvas.winfo_width());self.canvas.config(scrollregion=self.canvas.bbox('all'))
        overflow=self.body.winfo_reqheight()>self.canvas.winfo_height()+2
        if overflow and not self.scroll.winfo_manager():self.scroll.pack(side='right',fill='y')
        elif not overflow and self.scroll.winfo_manager():self.scroll.pack_forget()
    def wheel(self,event):
        if self.body.winfo_height()>self.canvas.winfo_height():self.canvas.yview_scroll(-int(event.delta/120),'units');return 'break'
    def end_changed(self):self.inputs['end_date'].set_enabled(self.end_enabled.get())
    def set_repeat(self,value):
        from ui_tasks import REPEAT_NAMES
        self.repeat_value=value;self.e.repeat.current(list(REPEAT_NAMES).index(value));self.paint_repeat()
    def toggle_day(self,index):self.days[index].set(not self.days[index].get());self.set_repeat('custom')
    def paint_repeat(self):
        self.segment.index=self.repeat_keys.index(self.repeat_value) if self.repeat_value in self.repeat_keys else 3;self.segment.draw()
        for i,b in enumerate(self.day_buttons):
            on=self.repeat_value=='daily' or self.days[i].get();b._bg=theme.accent if on else '#E8E2F8';b._fg='white' if on else C['fg'];b._nav_active=on;b._hover=C['selected'];b.config(bg=b._bg,fg=b._fg)
        # Preserve the reference geometry when choosing Once; inactive weekdays stay visible.
        for b in self.day_buttons:b.configure(state='disabled' if self.repeat_value=='once' else 'normal')
    def paint_dates(self):
        for w in self.chips.winfo_children():w.destroy()
        for i,date in enumerate(self.exception_dates):
            b=flat_button(self.chips,date+'  ×',lambda d=date:self.remove_date(d),font=theme.font(delta=-1),padx=8,pady=6);b._selection_outline='#D8CDEF';b._bg='#E9E3FA';b.config(bg=b._bg);b.grid(row=i//3,column=i%3,sticky='ew',padx=(0,self.p(8)),pady=self.p(2))
        i=len(self.exception_dates);b=flat_button(self.chips,'＋ 添加日期',self.add_date,font=theme.font(delta=-1),padx=8,pady=6);b._selection_outline='#B99BEF';b._dashed_outline=True;b.grid(row=i//3,column=i%3,sticky='ew',padx=(0,self.p(8)),pady=self.p(2))
        for col in range(3):self.chips.columnconfigure(col,weight=1,uniform='dates')
    def remove_date(self,date):self.exception_dates.remove(date);self.paint_dates()
    def add_date(self):
        variable=tk.StringVar(self.e,value=self.e.v['date'].get());value=self.date_picker(variable)
        if value and value not in self.exception_dates:
            if len(self.exception_dates)>=366:
                from ui_localize import messagebox
                messagebox.showerror('提示','例外日期最多366个',parent=self.e);return
            self.exception_dates.append(value);self.exception_dates.sort();self.paint_dates()
    def date_picker(self,variable):
        from ui_localize import messagebox
        e=self.e;win=tk.Toplevel(e);prepare(win);win.app=e.app;win.T=e.T;win.title('选择日期');win.transient(e);win.config(bg=C['bg']);win.resizable(False,False);win.result=None
        try:date=dt.date.fromisoformat(variable.get())
        except ValueError:date=dt.date.today()
        displayed=[date.year,date.month];v=tk.StringVar(win,value=date.isoformat())
        area=CozyFrame(win,bg=C['card']);area.pack(fill='both',expand=True,padx=10,pady=10)
        bar=tk.Frame(area,bg=C['card']);bar.pack(fill='x',padx=12,pady=8);heading=tk.Label(bar,bg=C['card'],fg=C['fg'],font=theme.font(bold=True));heading.pack(side='left',expand=True)
        grid=tk.Frame(area,bg=C['card']);grid.pack(fill='both',expand=True,padx=10,pady=4)
        def select(value):variable.set(value);win.result=value;win.destroy()
        def redraw(delta=0):
            month=displayed[0]*12+displayed[1]-1+delta;year,zero=divmod(month,12)
            if not 1<=year<=9999:return
            displayed[:]=[year,zero+1];heading.config(text=f'{year}年 {zero+1}月')
            for w in grid.winfo_children():w.destroy()
            for col,text in enumerate('一二三四五六日'):
                grid.columnconfigure(col,weight=1,uniform='week');self.lab(grid,text).grid(row=0,column=col,pady=4)
            for row,week in enumerate(calendar.monthcalendar(year,zero+1),1):
                for col,day in enumerate(week):
                    if day:flat_button(grid,str(day),lambda d=day:select(dt.date(displayed[0],displayed[1],d).isoformat()),font=theme.font(delta=-1),padx=2,pady=4).grid(row=row,column=col,sticky='ew',padx=2,pady=2)
        flat_button(bar,'‹',lambda:redraw(-1),padx=8,pady=3).pack(side='left');flat_button(bar,'›',lambda:redraw(1),padx=8,pady=3).pack(side='left')
        entry=SoftInput(area,v,placeholder='YYYY-MM-DD');entry.pack(fill='x',padx=12,pady=6)
        def accept():
            try:select(dt.date.fromisoformat(v.get()).isoformat())
            except ValueError:messagebox.showerror('提示','日期格式应为 YYYY-MM-DD',parent=win)
        flat_button(area,'确定',accept,kind='accent',pady=6).pack(fill='x',padx=12,pady=(0,10));redraw()
        win.bind('<Escape>',lambda ev:win.destroy());e.app._apply_window_chrome(win);compact_show(win,e.app,height=350,width=290);win.grab_set();e.wait_window(win)
        if e.winfo_exists():e.grab_set();e.focus_set()
        return win.result
    def action_selected(self,event=None):
        from ui_tasks import ACTION_NAMES
        self.e.action_changed()
        if ACTION_NAMES[self.e.action.current()] in ('close_program','run_program','play_sound','message'):self.parameters()
    def parameters(self):
        from ui_tasks import ACTION_NAMES
        e=self.e;action=ACTION_NAMES[e.action.current()];old=e.v['parameter'].get();old_force=e.force.get()
        win=tk.Toplevel(e);prepare(win);win.app=e.app;win.T=e.T;win.title('操作参数');win.transient(e);win.config(bg=C['bg']);win.resizable(False,False);win.saved=False
        area=CozyFrame(win,bg=C['card']);area.pack(fill='both',expand=True,padx=10,pady=10)
        self.lab(area,{'message':'消息内容','play_sound':'声音文件','run_program':'程序路径','close_program':'待关闭程序'}.get(action,'应用关闭选项')).pack(fill='x',padx=16,pady=(14,8))
        if action in ('close_program','run_program','play_sound','message'):
            SoftInput(area,e.v['parameter']).pack(fill='x',padx=16,pady=4)
            if action!='message':flat_button(area,'选择文件',lambda:e.pick_file(parent=win),pady=5).pack(anchor='e',padx=16,pady=4)
        else:tk.Checkbutton(area,text='允许强制关闭应用（关机／重启／注销）',variable=e.force,bg=C['card'],fg=C['fg'],font=theme.font(delta=-1)).pack(fill='x',padx=16,pady=8)
        def save():win.saved=True;win.destroy()
        flat_button(area,'确定',save,kind='accent',pady=6).pack(fill='x',padx=16,pady=12)
        win.bind('<Escape>',lambda ev:win.destroy());e.app._apply_window_chrome(win);compact_show(win,e.app,height=220,width=430);win.grab_set();e.wait_window(win)
        if not win.saved:e.v['parameter'].set(old);e.force.set(old_force)
        if e.winfo_exists():e.grab_set();e.focus_set()
    def mode_menu(self):
        from ui_tasks import MODE_NAMES
        from ui_popup_menu import VioletMenu
        menu=tk.Menu(self.e,tearoff=0)
        for i,k in enumerate(self.e.mode_keys):menu.add_command(label=MODE_NAMES[k],command=lambda i=i:(self.e.mode.current(i),self.update_fields()))
        self.popup=VioletMenu(self.e.app,menu,anchor=self.heading if self.heading.winfo_viewable() else self.condition_heading,icons=('clock',)*len(self.e.mode_keys))
    def policy_menu(self,anchor):
        from ui_popup_menu import VioletMenu
        menu=tk.Menu(self.e,tearoff=0)
        for k,t in [('skip','跳过，不补执行'),('ask','下次启动后询问'),('run','启动后执行一次')]:menu.add_command(label=t,command=lambda k=k:self.policy.set(k))
        self.popup=VioletMenu(self.e.app,menu,anchor=anchor,icons=('clock',)*3)
    def paint_policy(self):
        self.ask_radio.pack_forget();self.run_radio.pack_forget()
        (self.run_radio if self.policy.get()=='run' else self.ask_radio).pack(side='left')
    def calendar_values(self):
        result=dict(exception_dates=list(self.exception_dates),missed_policy=self.policy.get())
        if self.repeat_value in ('weekly','custom'):result['weekdays']=[i for i,v in enumerate(self.days) if v.get()]
        if self.end_enabled.get():result['end_date']=self.e.v['end_date'].get().strip()
        return result
    def update_fields(self):
        e=self.e;mode=e.mode_keys[e.mode.current()]
        for p in (self.calendar,self.exceptions,self.missed,self.conditions):p.card.pack_forget()
        if mode=='calendar':
            for p in (self.calendar,self.exceptions,self.missed):p.card.pack(fill='x',pady=(0,self.p(7)))
            self.paint_repeat()
        else:
            self.conditions.card.pack(fill='x',pady=(0,self.p(7)));self.mode_choice.current(e.mode.current())
            visible={'countdown':{'seconds'},'interval':{'seconds'},'datetime':{'weekday'},'download':{'folder','idle_seconds','timeout_hours'},'network':{'threshold_kib','idle_seconds','timeout_hours'},'combined':{'threshold_kib','idle_seconds','timeout_hours','user_idle_minutes'},'chain':{'prepare_path','prepare_args','timeout_hours'}}.get(mode,set())
            for k,row in self.condition_rows.items():row.grid() if k in visible else row.grid_remove()
            self.normal_clock.grid(row=20,column=0,columnspan=2,sticky='ew',pady=self.p(4)) if mode=='datetime' else self.normal_clock.grid_remove()
        self.canvas.yview_moveto(0)
