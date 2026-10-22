"""Reviewed, selective backup restore; active timers, queue and startup stay intact."""
import copy,tkinter as tk
from tkinter import ttk,filedialog
from ui_window import prepare,show,button_grid
from ui_settings_controls import label,text
from ui_dialog_palette import COLORS as C
from theme import theme
from ui_localize import messagebox
from task_store import read_backup,import_backup

LABELS={'language':'显示语言','minimize_to_tray':'关闭主窗口时隐藏到托盘','esc_to_minimize':'Esc 最小化','sound_at_10s':'提示音','popup_at_10s':'显示主窗口','cancel_at_10s':'可取消提醒','warning_seconds':'提醒提前量','toast_seconds':'消息停留时长','quick_presets':'六格快捷预设','resume_strategy':'重开后的定时恢复','resume_timer':'恢复未完成定时','float_enabled':'开启悬浮窗','float_topmost':'悬浮窗置顶','float_opacity':'悬浮窗不透明度','log_enabled':'执行日志','notifications_enabled':'Windows 通知','notify_setup':'任务已设置通知','notify_done':'任务已完成通知','notify_error':'任务失败通知','hotkeys_enabled':'全局快捷键','hotkey_show':'唤出主窗口快捷键','hotkey_pause':'暂停快捷键','hotkey_resume':'继续快捷键','hotkey_floating':'悬浮倒计时快捷键','message_text':'消息内容','program_path':'程序路径','close_program_path':'关闭程序路径','sound_file':'声音文件','action':'操作记忆','mode':'时间方式记忆','keep_display_on':'屏幕常亮','force_close_apps':'强制关闭应用','confirm_before_action':'执行前确认','confirm_key_only':'仅确认关键操作','confirm_on_exit':'退出前确认','confirm_on_exit_only_timer':'仅运行中确认退出','quick_day_offset':'旧版预设日期','quick_at_tomorrow':'旧版预设时间'}

def differences(cfg,values):
    result=[]
    for key,value in values.items():
        if cfg.get(key)==value:continue
        def display(v):
            if isinstance(v,bool):return '开启' if v else '关闭'
            if isinstance(v,list):
                if key=='quick_presets':
                    import quick_presets
                    return ' / '.join(quick_presets.caption(x,type('Language',(),{'lang':'CHS'})()) for x in v)
                return str(len(v))+' 项'
            return str(v)
        result.append((LABELS.get(key,'其他设置：'+key),display(cfg.get(key)),display(value)))
    return result

class RestorePreview(tk.Toplevel):
    def __init__(self,app,parent,path):
        super().__init__(parent);prepare(self);self.app=app;self.T=app.T;self.path=path;self.result=False;self.data=read_backup(path);self.title(text(self,'恢复预览'));self.transient(parent.winfo_toplevel());self.configure(bg=C['bg'])
        body=tk.Frame(self,bg=C['bg']);body.pack(fill='both',expand=True,padx=14,pady=12)
        label(body,'选择恢复范围；运行中计时、当前队列与自启动项保留。',wraplength=600).pack_configure(pady=(0,8))
        self.scopes={key:tk.BooleanVar(self,value=True) for key in ('settings','templates','automations')}
        for key,name,count in [('settings','常用设置',len(differences(app.cfg,self.data[0]))),('templates','常用模板',len(self.data[1])),('automations','高级任务',len(self.data[2]))]:
            tk.Checkbutton(body,text=text(self,name)+f' · {count}',variable=self.scopes[key],bg=C['bg'],fg=C['fg'],selectcolor=C['card'],font=theme.font()).pack(anchor='w',pady=2)
        tv=ttk.Treeview(body,columns=('name','old','new'),show='headings',height=10);tv.pack(fill='both',expand=True,pady=10);self.tv=tv
        for key,name,width in zip(('name','old','new'),('设置项','当前','备份'),(230,200,200)):tv.heading(key,text=text(self,name));tv.column(key,width=width,stretch=True)
        for i,row in enumerate(differences(app.cfg,self.data[0])):tv.insert('','end',iid=str(i),values=tuple(text(self,v) for v in row))
        hs=ttk.Scrollbar(body,orient='horizontal',command=tv.xview);hs.pack(fill='x');tv.configure(xscrollcommand=hs.set)
        label(body,'恢复的高级任务保持停用；仅恢复模板不会修改其他设置。',wraplength=610,fg=C['muted'],font=theme.font(delta=-1)).pack_configure(pady=(8,5))
        foot=tk.Frame(body,bg=C['bg']);foot.pack(fill='x',pady=6)
        button_grid(foot,[(text(self,'取消'),self.destroy,'normal'),(text(self,'确认恢复'),self.restore,'accent')]);self.bind('<Escape>',lambda e:self.destroy());show(self);self.grab_set()
    def restore(self):
        scopes={key for key,var in self.scopes.items() if var.get()}
        if not scopes:messagebox.showinfo('请选择恢复范围','请选择恢复范围',parent=self);return
        try:
            import_backup(self.app.cfg,self.path,scopes=scopes,data=self.data)
            if 'automations' in scopes:self.app.automation.reload()
            if 'settings' in scopes:self.app.apply_settings()
            self.app.undo.stack=[]
            win=getattr(self.app,'_settings_win',None)
            if win and win.winfo_exists():win.sync_vars()
            self.result=True;self.destroy()
        except (ValueError,OSError) as exc:messagebox.showerror('操作未完成',str(exc),parent=self)

def restore_preview(app,parent,path):
    win=getattr(app,'_settings_win',None)
    if win and win.winfo_exists() and win.dirty:
        result=messagebox.askyesnocancel('保留当前设置','你修改的设置还没有保存\n恢复备份前，可以先保存这次修改',parent=parent,default='cancel',labels={'yes':'先保存','no':'放弃更改','cancel':'继续编辑'})
        if result is None:return False
        if result:
            if not win.on_apply():return False
        else:win.discard()
    dialog=RestorePreview(app,parent,path);parent.wait_window(dialog);return dialog.result

def choose_backup(app,parent):
    path=filedialog.askopenfilename(parent=parent,title=text(parent,'导入设置与模板'),filetypes=[('JSON','*.json')])
    if not path:return
    try:restore_preview(app,parent,path)
    except (ValueError,OSError) as exc:messagebox.showerror('导入失败',str(exc),parent=parent)
