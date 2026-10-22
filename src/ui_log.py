"""Compact log cards with date selection and viewport-only row rendering."""
import os
import tkinter as tk
from tkinter import ttk,filedialog,font as tkfont
from theme import theme,flat_button
from ui_window import prepare,compact_show
from ui_cozy import CozyFrame,scale,cozy_icon
from ui_dialog_palette import COLORS as C
from ui_soft_controls import SoftInput,SoftChoice
from ui_date_picker import DateInput,pick_date
from ui_localize import messagebox

KIND_KEYS={'setup':'log_kind_setup','done':'log_kind_done','error':'log_kind_error','cancel':'log_kind_cancel','info':'log_kind_info'}

def kind_text(T,kind):
    return {'ui_error':'界面异常','scheduler_error':'调度异常'}.get(kind) or T(KIND_KEYS.get(kind,'log_kind_info'))

def record_detail(rec):
    count=int(rec.get('count',1))
    note=('累计出现 '+str(count)+' 次\n最后出现：'+str(rec.get('last_ts',''))+'\n\n') if count>1 else ''
    return note+str(rec.get('detail',''))

class LogWindow(tk.Toplevel):
    def __init__(self,app):
        super().__init__(app.root);prepare(self);self.app=app;self.T=app.T;self.s=scale(self)
        self.title('执行日志');self.configure(bg=C['bg']);self.resizable(True,True)
        self.query=tk.StringVar(self);self.kind=tk.StringVar(self,value='全部');self.start_date=tk.StringVar(self);self.end_date=tk.StringVar(self)
        self.kind_values={'全部':''};self.kind_values.update({self.T(v):k for k,v in KIND_KEYS.items()})
        self.kind_values.update({'界面异常':'ui_error','调度异常':'scheduler_error'})
        self.filtered_rows=[];self._all_rows=[];self._file_stamp=None;self._filter_stamp=None;self._filter_job=None;self._draw_job=None;self._filter_error=False;self.selected=-1;self.render_count=0
        self._font=tkfont.Font(self,font=theme.font(delta=-1));self._small=tkfont.Font(self,font=theme.font(delta=-2));self._fit_cache={}
        self.row_height=round(48*self.s)
        summary=CozyFrame(self,bg=C['card']);summary.pack(fill='x',padx=8,pady=(5,7))
        inner=tk.Frame(summary,bg=C['card']);inner.pack(fill='x',padx=14,pady=10)
        icon=tk.Label(inner,bg=C['card']);icon.photo=cozy_icon(self,'document',round(32*self.s),ink=theme.accent);icon.config(image=icon.photo);icon.pack(side='left',padx=(0,12))
        texts=tk.Frame(inner,bg=C['card']);texts.pack(side='left',fill='x',expand=True)
        self.eyebrow=self.label(texts,'最近记录',small=True);self.eyebrow.pack(fill='x')
        self.summary_title=self.label(texts,'暂无执行记录',bold=True);self.summary_title.pack(fill='x',pady=(3,2))
        self.summary_title.bind('<Configure>',lambda e:self.paint_summary())
        self.summary_note=self.label(texts,'任务设定、执行结果与取消操作',small=True);self.summary_note.pack(fill='x')
        self.filters=CozyFrame(self,bg=C['card']);self.filters.pack(fill='x',padx=8,pady=(0,7))
        f=tk.Frame(self.filters,bg=C['card']);f.pack(fill='x',padx=12,pady=9);f.columnconfigure(0,weight=1);f.columnconfigure(1,weight=1)
        self.search=SoftInput(f,self.query,placeholder='搜索内容或详情',height=30);self.search.grid(row=0,column=0,sticky='ew',padx=(0,7))
        self.search.entry.bind('<Return>',lambda e:self.refresh())
        self.kind_choice=SoftChoice(f,app,list(self.kind_values));self.kind_choice.configure(height=round(30*self.s));self.kind_choice.grid(row=0,column=1,sticky='ew')
        self.kind_choice.bind('<<ComboboxSelected>>',lambda e:self.choose_kind())
        dates=tk.Frame(f,bg=C['card']);dates.grid(row=1,column=0,columnspan=2,sticky='ew',pady=(7,0));dates.columnconfigure(0,weight=1);dates.columnconfigure(2,weight=1)
        self.start_input=DateInput(dates,self.start_date,lambda:self.pick('start'),placeholder='开始日期',height=30,width=150);self.start_input.grid(row=0,column=0,sticky='ew')
        self.label(dates,'至',small=True).grid(row=0,column=1,padx=8)
        self.end_input=DateInput(dates,self.end_date,lambda:self.pick('end'),placeholder='结束日期',height=30,width=150);self.end_input.grid(row=0,column=2,sticky='ew')
        flat_button(dates,'重置',self._reset,font=theme.font(delta=-1),padx=9,pady=5).grid(row=0,column=3,padx=(7,0))
        self.bottom=tk.Frame(self,bg=C['bg']);self.bottom.pack(side='bottom',fill='x',padx=8,pady=(7,7));self.buttons=[]
        for i,(text,fn,kind) in enumerate([('导出当前筛选 CSV',self._export,'accent'),('清空日志',self._clear,'normal'),('关闭',self.destroy,'normal')]):
            self.bottom.columnconfigure(i,weight=1,uniform='logactions');b=flat_button(self.bottom,text,fn,kind=kind,font=theme.font(delta=-1),padx=4,pady=7)
            b.grid(row=0,column=i,sticky='ew',padx=(0,5) if i<2 else 0);self.buttons.append(b)
        card=CozyFrame(self,bg=C['card']);card.pack(fill='both',expand=True,padx=8)
        self.count_label=self.label(card,'',small=True);self.count_label.pack(side='bottom',fill='x',padx=12,pady=(3,7))
        wrap=tk.Frame(card,bg=C['card']);wrap.pack(fill='both',expand=True,padx=9,pady=(8,0));wrap.columnconfigure(0,weight=1);wrap.rowconfigure(1,weight=1)
        self.header=tk.Canvas(wrap,bg=C['card'],height=round(26*self.s),highlightthickness=0);self.header.grid(row=0,column=0,sticky='ew')
        self.canvas=tk.Canvas(wrap,bg=C['card'],highlightthickness=0,takefocus=True,yscrollincrement=self.row_height);self.canvas.grid(row=1,column=0,sticky='nsew')
        self.scroll=ttk.Scrollbar(wrap,command=self.canvas.yview);self.scroll.grid(row=1,column=1,sticky='ns');self.canvas.config(yscrollcommand=self.scrolled)
        self.canvas.bind('<Configure>',self.resized);self.canvas.bind('<Button-1>',self.select_event);self.canvas.bind('<Double-1>',lambda e:self._show_detail());self.canvas.bind('<Return>',lambda e:self._show_detail())
        for event,step in [('<Up>',-1),('<Down>',1),('<Prior>',-5),('<Next>',5)]:self.canvas.bind(event,lambda e,n=step:self.move_selection(n))
        self.canvas.bind('<Home>',lambda e:self.select_index(0));self.canvas.bind('<End>',lambda e:self.select_index(len(self.filtered_rows)-1))
        self.bind('<MouseWheel>',lambda e:self.canvas.yview_scroll(-int(e.delta/120),'units') if e.widget is self.canvas else None,add='+')
        for var in (self.query,self.kind,self.start_date,self.end_date):var.trace_add('write',self.defer_filter)
        self.bind('<Escape>',lambda e:self.destroy());self.protocol('WM_DELETE_WINDOW',self.destroy)
        self.refresh();compact_show(self,app);self.focus_set()
    def label(self,parent,text,small=False,bold=False):return tk.Label(parent,text=text,bg=C['card'],fg=C['muted'] if small else C['fg'],font=theme.font(delta=-2 if small else 0,bold=bold),anchor='w',bd=0)
    def choose_kind(self):self.kind.set(list(self.kind_values)[self.kind_choice.current()]);self.refresh()
    def pick(self,endpoint):
        var=self.start_date if endpoint=='start' else self.end_date
        pick_date(self,self.app,var,title='选择开始日期' if endpoint=='start' else '选择结束日期',allow_clear=True,minimum=self.start_date.get() if endpoint=='end' else None,maximum=self.end_date.get() if endpoint=='start' else None,range_start=self.start_date.get(),range_end=self.end_date.get(),endpoint=endpoint)
        self.refresh()
    def defer_filter(self,*args):
        if self._filter_job:self.after_cancel(self._filter_job)
        self._filter_job=self.after(150,self.refresh)
    def refresh(self):
        if self._filter_job:self.after_cancel(self._filter_job);self._filter_job=None
        import run_log
        from task_store import filter_logs
        try:st=os.stat(run_log.log_file());stamp=(run_log.log_file(),st.st_mtime_ns,st.st_size)
        except OSError:stamp=(run_log.log_file(),None,0)
        changed=stamp!=self._file_stamp
        if changed:self._all_rows=run_log.entries(limit=run_log.MAX_ENTRIES);self._file_stamp=stamp
        filters=(self.query.get().strip(),self.kind_values.get(self.kind.get(),''),self.start_date.get(),self.end_date.get())
        if not changed and filters==self._filter_stamp and not self._filter_error:return
        try:rows=filter_logs(self._all_rows,*filters)
        except ValueError as exc:self._filter_error=True;self.count_label.config(text=str(exc),fg='#9E354F');return
        self._filter_error=False
        previous=self.filtered_rows[self.selected] if 0<=self.selected<len(self.filtered_rows) else None
        position=self.canvas.yview();tail=not self.filtered_rows or position[1]>=.999
        self.filtered_rows=rows;filter_changed=filters!=self._filter_stamp;self._filter_stamp=filters
        self.selected=rows.index(previous) if previous in rows else len(rows)-1
        self.kind_choice.current(list(self.kind_values).index(self.kind.get()) if self.kind.get() in self.kind_values else 0)
        self.count_label.config(text=f'{len(rows)} / {len(self._all_rows)} 条 · 最多保留500条 · 双击查看完整详情',fg=C['muted'])
        self.update_region()
        if filter_changed or tail:self.canvas.yview_moveto(1)
        else:self.canvas.yview_moveto(position[0])
        self.paint_summary();self.schedule_draw()
    def update_region(self):self.canvas.config(scrollregion=(0,0,max(1,self.canvas.winfo_width()),max(self.canvas.winfo_height(),len(self.filtered_rows)*self.row_height)))
    def resized(self,event):self.update_region();self.paint_header();self.schedule_draw()
    def scrolled(self,*args):self.scroll.set(*args);self.schedule_draw()
    def schedule_draw(self):
        if self._draw_job is None:self._draw_job=self.after_idle(self.draw)
    def columns(self):
        w=max(1,self.canvas.winfo_width());timew=round(105*self.s);kindw=round(72*self.s);detailw=round(50*self.s)
        return (round(9*self.s),timew,timew+kindw,max(timew+kindw+30,w-detailw),w)
    def fit(self,text,width,font=None):
        font=font or self._font;text=str(text).replace('\n',' ');key=(text,width,str(font))
        if key in self._fit_cache:return self._fit_cache[key]
        value=text[:512]
        if len(text)>512 or font.measure(value)>width:
            lo,hi=0,len(value)
            while lo<hi:
                mid=(lo+hi+1)//2
                if font.measure(value[:mid]+'…')<=width:lo=mid
                else:hi=mid-1
            value=value[:lo]+'…'
        if len(self._fit_cache)>2048:self._fit_cache.clear()
        self._fit_cache[key]=value;return value
    def paint_header(self):
        self.header.delete('all')
        for x,text in zip(self.columns(),('时间','事件','内容','详情')):self.header.create_text(x,round(13*self.s),text=text,anchor='w',font=self._small,fill=C['muted'])
    def draw(self):
        self._draw_job=None;self.render_count+=1;c=self.canvas;c.delete('all');self.paint_header();w=c.winfo_width();top=c.canvasy(0);rh=self.row_height
        if not self.filtered_rows:c.create_text(w/2,top+round(60*self.s),text='没有符合条件的记录' if any((self.query.get(),self.start_date.get(),self.end_date.get(),self.kind_values.get(self.kind.get()))) else '暂无执行记录',fill=C['muted'],font=self._small);return
        first=max(0,int(top//rh));last=min(len(self.filtered_rows),int((top+c.winfo_height())//rh)+2);x0,x1,x2,x3,end=self.columns()
        for index in range(first,last):
            rec=self.filtered_rows[index];y=index*rh;cy=y+rh/2
            if index==self.selected:
                r=round(10*self.s);c.create_polygon(0,y+r,0,y+2,r,y+2,w-r,y+2,w,y+2,w,y+r,w,y+rh-r,w,y+rh-2,w-r,y+rh-2,r,y+rh-2,0,y+rh-2,0,y+rh-r,smooth=True,fill=C['hover'],outline='')
            stamp=str(rec.get('ts',''));day,_,clock=stamp.partition(' ')
            c.create_text(x0,cy-round(8*self.s),text=self.fit(day,x1-x0-8,self._small),anchor='w',font=self._small,fill=C['fg'])
            c.create_text(x0,cy+round(9*self.s),text=self.fit(clock,x1-x0-8,self._small),anchor='w',font=self._small,fill=C['muted'])
            kind=kind_text(self.T,rec.get('kind'));ink='#9E354F' if rec.get('kind') in ('error','ui_error','scheduler_error') else '#35624C' if rec.get('kind')=='done' else C['muted']
            c.create_text(x1,cy,text=self.fit(kind,x2-x1-8,self._small),anchor='w',font=self._small,fill=ink)
            c.create_text(x2,cy,text=self.fit(rec.get('text',''),x3-x2-round(12*self.s)),anchor='w',font=self._font,fill=C['fg'])
            c.create_text(x3,cy,text='查看',anchor='w',font=self._small,fill=theme.accent)
    def select_event(self,event):
        index=int(self.canvas.canvasy(event.y)//self.row_height)
        if 0<=index<len(self.filtered_rows):
            self.selected=index;self.paint_summary();self.schedule_draw();self.canvas.focus_set()
            if event.x>=self.columns()[3]:self._show_detail()
    def select_index(self,index):
        if not self.filtered_rows:return 'break'
        self.selected=max(0,min(len(self.filtered_rows)-1,index));self.paint_summary();self.schedule_draw()
        top=self.canvas.canvasy(0);y=self.selected*self.row_height;total=max(self.canvas.winfo_height(),len(self.filtered_rows)*self.row_height)
        if y<top:self.canvas.yview_moveto(y/total)
        elif y+self.row_height>top+self.canvas.winfo_height():self.canvas.yview_moveto((y+self.row_height-self.canvas.winfo_height())/total)
        return 'break'
    def move_selection(self,step):return self.select_index(self.selected+step)
    def paint_summary(self):
        if not 0<=self.selected<len(self.filtered_rows):self.eyebrow.config(text='执行记录');self.summary_title.config(text='暂无匹配记录');self.summary_note.config(text='调整搜索条件或选择日期');return
        rec=self.filtered_rows[self.selected];self.eyebrow.config(text='选中记录');self.summary_title.config(text=self.fit(rec.get('text',''),max(30,self.summary_title.winfo_width()-3)))
        self.summary_note.config(text=str(rec.get('ts',''))+' · '+kind_text(self.T,rec.get('kind')))
    def _show_detail(self,_e=None):
        if not 0<=self.selected<len(self.filtered_rows):return
        rec=self.filtered_rows[self.selected];win=tk.Toplevel(self);prepare(win);win.app=self.app;win.T=self.T;win.title('日志详情');win.transient(self);win.config(bg=C['bg'])
        footer=tk.Frame(win,bg=C['bg']);footer.pack(side='bottom',fill='x',padx=12,pady=(0,10))
        flat_button(footer,'关闭',win.destroy,kind='accent',padx=16,pady=5).pack(side='right')
        card=CozyFrame(win,bg=C['card']);card.pack(fill='both',expand=True,padx=10,pady=6)
        body=tk.Frame(card,bg=C['card']);body.pack(fill='both',expand=True,padx=12,pady=8)
        text=tk.Text(body,wrap='word',width=1,bg=C['card'],fg=C['fg'],font=theme.font(delta=-1),bd=0,highlightthickness=0);text.pack(side='left',fill='both',expand=True)
        scroll=ttk.Scrollbar(body,command=text.yview);scroll.pack(side='right',fill='y');text.config(yscrollcommand=scroll.set)
        text.insert('1.0',str(rec.get('ts',''))+' · '+kind_text(self.T,rec.get('kind'))+'\n\n'+str(rec.get('text',''))+ ('\n'+record_detail(rec) if record_detail(rec) else ''));text.config(state='disabled')
        from ui_window import content_show,text_rows
        rows=text_rows(win,text.get('1.0','end-1c'),350*self.s,text.cget('font'),maximum=13);text.config(height=rows)
        if rows<13:scroll.pack_forget()
        win.bind('<Escape>',lambda e:win.destroy());content_show(win,self.app,width=390,min_height=150,max_height=360);win.grab_set();text.focus_set()
    def _clear(self):
        import run_log
        if not messagebox.askyesno('清空日志','确定清空全部执行日志吗？此操作无法撤销。',parent=self):return
        if run_log.clear():self.refresh()
        else:messagebox.showerror('清空失败','无法写入日志文件，请稍后重试。',parent=self)
    def _reset(self):self.query.set('');self.kind.set('全部');self.start_date.set('');self.end_date.set('');self.refresh()
    def _export(self):
        from task_store import export_csv
        self.refresh()
        if self._filter_error:return
        path=filedialog.asksaveasfilename(parent=self,defaultextension='.csv',initialfile='执行日志.csv',filetypes=[('CSV','*.csv')])
        if not path:return
        try:export_csv(path,self.filtered_rows);messagebox.showinfo('导出完成',f'已导出 {len(self.filtered_rows)} 条筛选结果。',parent=self)
        except OSError as exc:messagebox.showerror('导出失败',str(exc),parent=self)
    def destroy(self):
        for job in (self._filter_job,self._draw_job):
            if job:
                try:self.after_cancel(job)
                except tk.TclError:pass
        super().destroy()
