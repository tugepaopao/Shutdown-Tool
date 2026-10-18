"""任务编辑器、命名模板与高级任务管理；不改变主页面布局。"""
import copy
import datetime as dt
import os
import tkinter as tk
from ui_window import prepare, show, button_grid
from tkinter import ttk,filedialog
import ui_template_name as simpledialog
from ui_localize import messagebox
from actions import action_label
from task_store import normalize,snapshot,save_template,export_backup,read_backup,import_backup
from theme import theme,flat_button
from i18n import feature_text

def local_text(parent,text):
    window=parent.winfo_toplevel()
    T=getattr(window,'T',None) or getattr(getattr(window,'app',None),'T',None)
    return feature_text(T,text) if T else text

MODE_NAMES={'countdown':'倒计时','datetime':'定点执行（单次）','interval':'循环间隔',
            'calendar':'具体日期／重复预约','download':'下载文件夹结束后','network':'网络传输安静后','combined':'网络安静且无人操作','chain':'程序成功后执行'}
REPEAT_NAMES={'once':'仅一次','workdays':'每周一至周五','weekends':'每周六、周日','daily':'每天','weekly':'每周','custom':'自定义'}
ACTION_NAMES=('shutdown','restart','logoff','lock','sleep','hibernate','close_program','run_program','play_sound','message')

def label(parent,text,**kw):
    opts=dict(text=local_text(parent,text),bg=theme.c('bg'),fg=theme.c('fg'),font=theme.font());opts.update(kw)
    return tk.Label(parent,**opts)

def button(parent,text,command,kind='normal'):
    return flat_button(parent,local_text(parent,text),command,kind=kind,font=theme.font(delta=-1),padx=8,pady=5)

class TaskEditor(tk.Toplevel):
    def __init__(self,app,task=None,parent=None,modes=None,title='编辑任务',validate=None):
        super().__init__(parent or app.root);prepare(self);self.app=app;self.result=None;self.validate=validate
        if task is None:
            try:task=app.current_task_snapshot()
            except ValueError:task={'action':app._current_action(),'mode':'countdown','seconds':60,**{k:app.cfg.get(k) for k in ('program_path','sound_file','message_text','force_close_apps')}}
        self.original=copy.deepcopy(task)
        from ui_advanced_editor import AdvancedLayout
        self.advanced_layout=AdvancedLayout(self,modes,title,parent)
    def add_row(self,key,title,widget=None):
        row=tk.Frame(self.body,bg=theme.c('bg'));row.pack(fill='x',pady=4);self.rows[key]=row
        label(row,title,anchor='w',wraplength=225,justify='left',font=theme.font(delta=-1)).grid(row=0,column=0,sticky='ew',padx=(0,10))
        row.columnconfigure(0,minsize=235)
        if widget is not None:
            # Combobox must be constructed with the row as parent.
            opts={k:widget.cget(k) for k in ('values','state','width')};widget.destroy()
            widget=ttk.Combobox(row,**opts)
            if key=='action':self.action=widget
            elif key=='mode':self.mode=widget
            elif key=='repeat':self.repeat=widget
            widget.grid(row=0,column=1,sticky='ew')
        row.columnconfigure(1,weight=1);return row
    def add_field(self,key,title,value):
        self.v[key]=tk.StringVar(value=value);row=self.add_row(key,title)
        ttk.Entry(row,textvariable=self.v[key],width=28).grid(row=0,column=1,sticky='ew')
    def action_changed(self, event=None):
        action=ACTION_NAMES[self.action.current()]
        if action != self._parameter_action:
            key={"close_program":"close_program_path","run_program":"program_path","play_sound":"sound_file","message":"message_text"}.get(action)
            self.v["parameter"].set(self.app.cfg.get(key, "") if key else "")
            self._parameter_action=action
        self.update_fields()

    def update_fields(self):
        if hasattr(self,'advanced_layout'):return self.advanced_layout.update_fields()
        mode=self.mode_keys[self.mode.current()];action=ACTION_NAMES[self.action.current()]
        visible={'name','action','mode'}
        if action in ('close_program','run_program','play_sound','message'):visible.add('parameter')
        if mode in ('countdown','interval'):visible.add('seconds')
        if mode=='datetime':visible.update(('weekday','clock'))
        if mode=='calendar':visible.update(('date','clock','repeat'))
        if mode in ('download','network','combined'):visible.update(('idle_seconds','timeout_hours'))
        if mode=='combined':visible.add('user_idle_minutes')
        if mode=='chain':visible.update(('prepare_path','prepare_args','timeout_hours'))
        if mode=='download':visible.add('folder')
        if mode in ('network','combined'):visible.add('threshold_kib')
        # Pack in original order before the fixed check/tip/button area.
        anchor=next(w for w in self.body.winfo_children() if isinstance(w,tk.Checkbutton))
        for key,row in self.rows.items():
            row.pack_forget()
            if key in visible:row.pack(fill='x',pady=4,before=anchor)
        self.browse.grid_remove() if action=='message' else self.browse.grid()
    def pick_prepare(self):
        f=filedialog.askopenfilename(parent=self,filetypes=[('Executable','*.exe')])
        if f:self.v['prepare_path'].set(f)
    def pick_file(self,parent=None):
        parent=parent or self
        if ACTION_NAMES[self.action.current()]=="close_program":
            from ui_close_program import CloseProgramDialog
            dlg=CloseProgramDialog(self.app,parent=parent,initial=self.v["parameter"].get());self.wait_window(dlg)
            f=dlg.result
        else:f=filedialog.askopenfilename(parent=parent)
        if f:self.v['parameter'].set(f)
        if parent.winfo_exists():parent.grab_set()
    def pick_folder(self):
        f=filedialog.askdirectory(parent=self)
        if f:self.v['folder'].set(f)
    def collect(self):
        action=ACTION_NAMES[self.action.current()];mode=self.mode_keys[self.mode.current()]
        task={'name':self.v['name'].get(),'action':action,'mode':mode,'force_close_apps':self.force.get()}
        parameter={'close_program':'close_program_path','run_program':'program_path','play_sound':'sound_file','message':'message_text'}.get(action)
        if parameter:
            value=self.v['parameter'].get().strip()
            if not value:raise ValueError('请填写操作参数')
            task[parameter]=value
        if action=="close_program":
            from program_control import validate_target
            validate_target(task["close_program_path"])
        if mode in ('countdown','interval'):task['seconds']=self.v['seconds'].get()
        if mode in ('datetime','calendar'):
            try:
                parts=[int(v) for v in self.v['clock'].get().split(':')]
                if len(parts)==2:parts.append(0)
                h,m,s=parts;dt.time(h,m,s)
            except (ValueError,TypeError):raise ValueError('时刻应为 HH:MM:SS，例如 22:00:00')
            if mode=='datetime':task.update(weekday=int(self.v['weekday'].get())-1,hour=h,minute=m,second=s)
            else:
                task.update(at=self.v['date'].get()+f'T{h:02}:{m:02}:{s:02}',repeat=list(REPEAT_NAMES)[self.repeat.current()])
                if hasattr(self,'advanced_layout'):task.update(self.advanced_layout.calendar_values())
        if mode in ('network','download','combined'):
            task.update(idle_seconds=self.v['idle_seconds'].get(),timeout_seconds=float(self.v['timeout_hours'].get())*3600)
            if mode in ('network','combined'):task['threshold_kib']=self.v['threshold_kib'].get()
            else:task['folder']=self.v['folder'].get()
        if mode=='combined':task['user_idle_seconds']=float(self.v['user_idle_minutes'].get())*60
        if mode=='chain':task.update(prepare_path=self.v['prepare_path'].get(),prepare_args=self.v['prepare_args'].get(),timeout_seconds=float(self.v['timeout_hours'].get())*3600)
        return normalize(task)
    def save(self):
        try:
            result=self.collect()
            from task_capabilities import validate
            validate(result)
            if self.validate:self.validate(result)
            self.result=result
        except (ValueError,TypeError) as exc:messagebox.showerror('任务设置有误',str(exc),parent=self);return
        self.destroy()

class TaskView:
    def _init_view(self,app,advanced=False,parent=None,embedded=False):
        if embedded: tk.Frame.__init__(self,parent,bg=theme.c('bg'))
        else: tk.Toplevel.__init__(self,parent or app.root);prepare(self)
        self.app=app;self.advanced=advanced;self.owner=self.winfo_toplevel()
        self.configure(bg=theme.c('bg'))
        if embedded:
            from ui_library_cards import LibraryCards
            self.cards=LibraryCards(self)
            self.refresh_status()
            return
        if not embedded:
            self.title(local_text(self,'高级任务' if advanced else '常用任务模板'))
            self.transient(parent or app.root);self.resizable(True,True)
        from ui_window import wrap_to_width
        wrap_to_width(label(self,'具体日期与重复预约在这里设置；保存后需手动启用。' if advanced else '按名称保存任务，双击编辑；使用时会复制到队列。',wraplength=480,justify='left')).pack(fill='x',padx=8,pady=8)
        cols=('name','action','when','state');wrap=tk.Frame(self,bg=theme.c('bg'));wrap.pack(fill='both',expand=True,padx=12)
        self.table_border=tk.Frame(wrap,bg='#B9ABE1',padx=1,pady=1)
        self.table_border.grid(row=0,column=0,sticky='nsew');wrap.columnconfigure(0,weight=1);wrap.rowconfigure(0,weight=1)
        table_body=tk.Frame(self.table_border,bg=theme.c('card'));table_body.pack(fill='both',expand=True)
        self.tv=ttk.Treeview(table_body,columns=cols,show='headings',height=10,selectmode='browse')
        for key,title,width in zip(cols,('名称','操作','执行方式','状态'),(140,110,220,160)):
            self.tv.heading(key,text=local_text(self,title),anchor='w');self.tv.column(key,width=width,anchor='w')
        self.tv.pack(fill='both',expand=True,padx=3,pady=2);sb=ttk.Scrollbar(wrap,command=self.tv.yview);sb.grid(row=0,column=1,sticky='ns');self.tv.config(yscrollcommand=sb.set)
        controls=tk.Frame(self,bg=theme.c('bg'));controls.pack(side='bottom',before=wrap,fill='x')
        hs=ttk.Scrollbar(self,orient='horizontal',command=self.tv.xview);hs.pack(side='bottom',before=wrap,fill='x',padx=12);self.tv.config(xscrollcommand=hs.set)
        for col in cols:self.tv.column(col,stretch=False,minwidth=40)
        self._column_layout=None
        self.tv.bind('<Configure>',lambda e:self._layout_columns())
        self.tv.bind('<Double-1>',lambda e:self.safe(self.edit))
        bar=tk.Frame(controls,bg=theme.c('bg'));bar.pack(fill='x',padx=12,pady=10)
        edits=[('新建',self.add),('编辑',self.edit),('复制',self.duplicate),('删除',self.remove)]
        button_grid(bar,[(local_text(self,text),lambda fn=fn:self.safe(fn),'normal') for text,fn in edits])
        foot=tk.Frame(controls,bg=theme.c('bg'));foot.pack(fill='x',padx=12,pady=(0,12))
        actions=[('启用／停用',self.toggle)] if advanced else [('加入队列',self.use),('保存主页面当前设定',self.capture)]
        items=[(local_text(self,text),lambda fn=fn:self.safe(fn),'accent' if index==0 else 'normal') for index,(text,fn) in enumerate(actions)]
        if not embedded: items.append((local_text(self,'关闭'),self.destroy,'normal'))
        button_grid(foot,items)
        extra=tk.Frame(controls,bg=theme.c('bg'));extra.pack(fill='x',padx=12,pady=(0,12))
        if advanced:
            from ui_extras import PreviewWindow
            button_grid(extra,[(local_text(self,'今天跳过一次'),lambda:self.safe(self.skip_today),'normal'),(local_text(self,'未来7天任务预览'),lambda:PreviewWindow(app,self.owner),'normal')])
        else:button_grid(extra,[(local_text(self,'撤销上一次删除'),lambda:self.safe(self.undo_delete),'normal')])
        self.refresh_status()
        if not embedded:
            app._apply_window_chrome(self);self.bind('<Escape>',lambda e:self.destroy());show(self);self.grab_set();self.focus_set()
    def _layout_columns(self):
        # Measure the actual localized text; retain horizontal scrolling for narrow windows.
        from tkinter import font as tkfont
        from ui_cozy import scale
        style=ttk.Style(self);name=self.tv.cget('style') or 'Treeview';s=scale(self)
        body=tkfont.Font(root=self,font=style.lookup(name,'font') or theme.font())
        heading=tkfont.Font(root=self,font=style.lookup(name+'.Heading','font') or theme.font(bold=True))
        cols=('name','action','when','state');padding=round(24*s)
        values=[self.tv.item(i,'values') for i in self.tv.get_children()]
        widths=[max(round(minimum*s),heading.measure(self.tv.heading(col,'text'))+padding,
                    max((body.measure(row[i])+padding for row in values),default=0))
                for i,(col,minimum) in enumerate(zip(cols,(80,100,180,70)))]
        extra=max(0,self.tv.winfo_width()-4-sum(widths))
        widths[0]+=round(extra*.35);widths[2]+=extra-round(extra*.35)
        key=(tuple(widths),name)
        if key==self._column_layout:return
        self._column_layout=key
        for col,width in zip(cols,widths):self.tv.column(col,width=width,stretch=False)
    def items(self):return self.app.automation.jobs if self.advanced else self.app.cfg.get('templates') or []
    def safe(self,fn):
        old_templates=copy.deepcopy(self.app.cfg.get('templates') or [])
        old_jobs=copy.deepcopy(self.app.automation.jobs)
        try:fn()
        except (ValueError,OSError) as exc:
            if isinstance(exc,OSError):
                self.app.cfg['templates']=old_templates
                # 所有模板/高级编辑均要求未运行；启用的保存失败本身已回滚。
                self.app.automation.jobs=old_jobs
                self.app.cfg['automations']=copy.deepcopy(old_jobs)
            messagebox.showerror('操作未完成',str(exc),parent=self)
    def selected(self):
        ids=self.tv.selection();return next((t for t in self.items() if ids and str(t['id'])==ids[0]),None)
    def refresh_status(self):
        if hasattr(self,'cards'):
            if self.cards._search_job:return
            self.cards.refresh()
            return
        items=self.items()
        signature=(repr(items),repr(self.app.automation.states) if self.advanced else '',self.app.T.lang)
        if signature==getattr(self,'_rows_signature',None):return
        self._rows_signature=signature
        selected=self.tv.selection();ids={str(t['id']) for t in items}
        for iid in self.tv.get_children():
            if iid not in ids:self.tv.delete(iid)
        for task in items:
            state=self.app.automation.states.get(task['id'],'已启用' if task.get('enabled') else '已停用') if self.advanced else '可用'
            values=(task.get('name',''),self.app.describe_action(task),self.app.describe_when(task),local_text(self,state))
            iid=str(task['id'])
            if self.tv.exists(iid):
                if tuple(self.tv.item(iid,'values'))!=tuple(str(v) for v in values):self.tv.item(iid,values=values)
            else:self.tv.insert('','end',iid=iid,values=values)
        if selected and self.tv.exists(selected[0]):self.tv.selection_set(selected)
        self._layout_columns()
    def editor(self,task=None):
        modes=('calendar','download','network','combined','chain') if self.advanced else None
        identifier=task.get('id') if task else None
        def validate(result):
            if not self.advanced and identifier is None:return
            if not result['name'] or any(t['name']==result['name'] and t['id']!=identifier for t in self.items()):
                raise ValueError('请输入不重复的任务名称。')
        dlg=TaskEditor(self.app,task,parent=self.owner,modes=modes,validate=validate)
        self.wait_window(dlg)
        return dlg.result
    def commit(self):
        if self.advanced:self.app.automation.persist()
        elif not self.app.cfg.save():raise OSError('模板保存失败')
        self.refresh_status()
    def add(self):
        task=self.editor()
        if not task:return
        if self.advanced:self.app.automation.add(task);self.refresh_status()
        else:save_template(self.app.cfg,task['name'],task);self.commit()
    def edit(self):
        old=self.selected()
        if not old:return
        if self.advanced and old.get('enabled'):
            messagebox.showinfo('先停用任务','请先停用该任务，再编辑。',parent=self);return
        task=self.editor(old)
        if not task:return
        if not task['name'] or any(t['name']==task['name'] and t['id']!=old['id'] for t in self.items()):
            messagebox.showerror('名称有误','名称不能为空或重复。',parent=self);return
        previous=copy.deepcopy(old);old.clear();old.update(task);old['id']=previous['id']
        if self.advanced:old.update(enabled=False,next_at='')
        elif 'favorite' in previous:old['favorite']=previous['favorite']
        try:self.commit()
        except OSError:old.clear();old.update(previous);raise
        if self.advanced:self.app.automation.states.pop(old['id'],None);self.refresh_status()
    def duplicate(self):
        task=self.selected()
        if not task:return
        task=copy.deepcopy(task);task['name']+=' 副本';task.pop('id',None)
        result=self.editor(task)
        if result:
            if self.advanced:self.app.automation.add(result);self.refresh_status()
            else:save_template(self.app.cfg,result['name'],result);self.commit()
    def remove(self):
        task=self.selected()
        if not task or not messagebox.askyesno('删除任务','删除「'+task['name']+'」？',parent=self):return
        if self.advanced:self.app.automation.remove(task['id']);self.refresh_status()
        else:
            index=self.items().index(task);old=copy.deepcopy(task)
            self.app.cfg['templates']=[t for t in self.items() if t['id']!=task['id']];self.commit()
            self.app.undo.record('templates',[(index,old)])
    def skip_today(self):
        task=self.selected()
        if task:self.app.automation.skip_today(task['id']);self.refresh_status()
    def undo_delete(self):
        self.app.undo.undo();self.refresh_status()
    def favorite(self):
        task=self.selected()
        if task is None or self.advanced:return
        previous=task.get('favorite',False)
        task['favorite']=not previous
        try:self.commit()
        except OSError:
            task['favorite']=previous
            raise
    def toggle(self):
        task=self.selected()
        if not task:return
        try:self.app.automation.enable(task['id'],not task.get('enabled'));self.refresh_status()
        except (ValueError,OSError) as exc:messagebox.showerror('无法启用',str(exc),parent=self)
    def use(self):
        task=self.selected()
        if task:
            if task['mode'] in ('calendar','download','network','combined','chain'):
                self.app.automation.add(task);messagebox.showinfo('已保存高级任务','已保存到高级任务，请在那里手动启用。',parent=self)
            else:self.app.enqueue_task(task,start=True)
    def capture(self):
        name=simpledialog.askstring('保存模板','为主页面当前任务命名：',parent=self)
        if name:
            save_template(self.app.cfg,name,self.app.current_task_snapshot());self.commit()

class TaskManager(TaskView, tk.Toplevel):
    def __init__(self,app,advanced=False,parent=None): self._init_view(app,advanced,parent)


class TaskPanel(TaskView, tk.Frame):
    def __init__(self,app,parent,advanced=False): self._init_view(app,advanced,parent,embedded=True)


def backup_export(app,parent):
    path=filedialog.asksaveasfilename(parent=parent,defaultextension='.json',initialfile='豪崽子设置与模板备份.json',filetypes=[('JSON备份','*.json')])
    if not path:return
    try:export_backup(app.cfg,path);messagebox.showinfo('导出完成','设置、模板和高级任务已保存。运行中定时、队列和开机自启动不包含在备份内。',parent=parent)
    except (ValueError,OSError) as exc:messagebox.showerror('导出失败',str(exc),parent=parent)

def backup_import(app,parent):
    path=filedialog.askopenfilename(parent=parent,filetypes=[('JSON备份','*.json')])
    if not path:return
    try:
        settings,templates,jobs=read_backup(path)
        if not messagebox.askyesno('导入预览',f'将替换常用设置、{len(templates)}个模板和{len(jobs)}个高级任务。\n高级任务全部停用；当前队列、运行中计时和自启动项保留。\n是否继续？',parent=parent):return
        n,j=import_backup(app.cfg,path);app.automation.reload();app.apply_settings()
        messagebox.showinfo('导入完成',f'已导入{n}个模板、{j}个停用的高级任务。',parent=app.root)
        app.undo.stack=[]
        if hasattr(parent,'sync_vars'):parent.sync_vars()
    except (ValueError,OSError) as exc:messagebox.showerror('导入失败',str(exc),parent=parent)
