"""设置内的预约预览和备份恢复列表。"""
import tkinter as tk
from tkinter import ttk
from ui_window import prepare,show,button_grid,compact_show,wrap_to_width
from theme import theme
from ui_tasks import label,local_text
from ui_localize import messagebox
from schedule_preview import schedule_preview

class PreviewWindow(tk.Toplevel):
    def __init__(self,app,parent=None):
        super().__init__(parent or app.root);prepare(self);self.app=app;self.T=app.T
        self.title(local_text(self,'未来7天任务预览'));self.configure(bg=theme.c('bg'));self.transient(parent or app.root)
        wrap_to_width(label(self,'时间明确的预约显示在下表；条件任务和任务链不预测完成时刻。',wraplength=480,justify='left')).pack(fill='x',padx=12,pady=(10,4))
        wrap_to_width(label(self,'只显示已启用任务；工作日指周一至周五，不调整法定节假日。',wraplength=680,justify='left',font=theme.font(delta=-1))).pack(fill='x',padx=12,pady=(0,8))
        wrap=tk.Frame(self,bg=theme.c('bg'));wrap.pack(fill='both',expand=True,padx=12)
        self.tv=ttk.Treeview(wrap,columns=('date','time','name','action','note'),show='headings',height=12)
        for col,text,width in zip(self.tv.cget('columns'),('日期','时刻','任务名称','操作','提示'),(110,90,160,140,240)):
            self.tv.heading(col,text=local_text(self,text),anchor='w');self.tv.column(col,width=width,minwidth=width,stretch=False,anchor='w')
        self.tv.grid(row=0,column=0,sticky='nsew');wrap.columnconfigure(0,weight=1);wrap.rowconfigure(0,weight=1)
        vs=ttk.Scrollbar(wrap,command=self.tv.yview);vs.grid(row=0,column=1,sticky='ns');hs=ttk.Scrollbar(wrap,orient='horizontal',command=self.tv.xview);hs.grid(row=1,column=0,sticky='ew');self.tv.configure(yscrollcommand=vs.set,xscrollcommand=hs.set)
        self.tv.bind('<Double-1>',self.detail)
        bar=tk.Frame(self,bg=theme.c('bg'));bar.pack(side='bottom',before=wrap,fill='x',padx=12,pady=12)
        button_grid(bar,[(local_text(self,'刷新预览'),self.refresh,'normal'),(local_text(self,'关闭'),self.destroy,'normal')]);self.refresh();compact_show(self,app);self.grab_set()
    def refresh(self):
        self.rows=schedule_preview(self.app.automation.jobs)
        self.tv.delete(*self.tv.get_children())
        for i,row in enumerate(self.rows):self.tv.insert('','end',iid=str(i),values=(row['at'].strftime('%Y-%m-%d'),row['at'].strftime('%H:%M:%S'),row['name'],self.app.describe_action(row['task']),local_text(self,'同一分钟重叠；按队列执行') if row['overlap'] else ''))
        if not self.rows:self.tv.insert('','end',iid='empty',values=('','',local_text(self,'暂无预约'),'',''))
    def detail(self,event=None):
        sel=self.tv.selection()
        if sel and sel[0]!='empty':
            row=self.rows[int(sel[0])];messagebox.showinfo(row['name'],row['at'].strftime('%Y-%m-%d %H:%M:%S')+'\n'+self.app.describe_action(row['task']),parent=self)

class RecoveryWindow(tk.Toplevel):
    def __init__(self,app,parent):
        super().__init__(parent);prepare(self);self.app=app;self.T=app.T
        self.title(local_text(self,'备份与恢复'));self.configure(bg=theme.c('bg'));self.transient(parent)
        label(self,'恢复不替换运行中计时、当前队列和自启动项；高级任务保持停用。',wraplength=620,justify='left').pack(fill='x',padx=12,pady=12)
        self.tv=ttk.Treeview(self,columns=('time','templates','jobs'),show='headings',height=10)
        for col,text,width in zip(self.tv.cget('columns'),('备份时间','模板数','高级任务数'),(280,120,160)):
            self.tv.heading(col,text=local_text(self,text),anchor='w');self.tv.column(col,width=width,anchor='w')
        self.tv.pack(fill='both',expand=True,padx=12)
        bar=tk.Frame(self,bg=theme.c('bg'));bar.pack(fill='x',padx=12,pady=12)
        button_grid(bar,[(local_text(self,'恢复选中备份'),self.restore,'accent'),(local_text(self,'关闭'),self.destroy,'normal')]);self.refresh();show(self);self.grab_set()
    def refresh(self):
        from config_backups import files
        from task_store import read_backup
        self.paths={};self.tv.delete(*self.tv.get_children())
        for path in files():
            try:
                settings,templates,jobs=read_backup(path);key=str(len(self.paths));self.paths[key]=path
                stamp=path.name[:15];self.tv.insert('','end',iid=key,values=(stamp[:4]+'-'+stamp[4:6]+'-'+stamp[6:8]+' '+stamp[9:11]+':'+stamp[11:13]+':'+stamp[13:15],len(templates),len(jobs)))
            except (ValueError,OSError):pass
        if not self.paths:self.tv.insert('','end',iid='empty',values=(local_text(self,'暂无自动备份'),'',''))
    def restore(self):
        selected=self.tv.selection()
        if not selected or selected[0]=='empty':messagebox.showinfo('请选择一个备份','请选择一个备份',parent=self);return
        from ui_restore import restore_preview
        try:
            if restore_preview(self.app,self,self.paths[selected[0]]):self.refresh()
        except (ValueError,OSError) as exc:messagebox.showerror('操作未完成',str(exc),parent=self)
