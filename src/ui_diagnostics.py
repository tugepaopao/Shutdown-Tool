"""On-demand service snapshots. No polling or extra background worker."""
import datetime as dt
import tkinter as tk
from theme import flat_button
from ui_dialog_palette import COLORS as C
import run_log
from ui_cozy import cozy_icon
from ui_library_cards import StatusBadge
from ui_runtime_context import blossom
from PIL import ImageTk

def runtime_status(app):
    auto=getattr(app,'automation',None);desktop=getattr(app,'desktop',None)
    hotkeys=getattr(desktop,'hotkeys',None);floating=getattr(app,'floating',None);awake=getattr(app,'display_awake',None)
    hotkey_ok=bool(hotkeys and not hotkeys.closed and hotkeys.thread.is_alive() and len(hotkeys.mapping)==4)
    float_ok=bool(floating and not floating.closed and floating.window and floating.window.winfo_exists())
    return [('任务调度', '正常' if auto and not auto.closed else '未运行'),
            ('全局快捷键','已注册' if hotkey_ok else '需处理' if app.cfg.get('hotkeys_enabled') else '未启用'),
            ('悬浮倒计时','运行中' if float_ok else '需处理' if app.cfg.get('float_enabled') else '未启用'),
            ('屏幕常亮','已开启' if awake and awake.enabled else '已关闭')]

def recent_anomalies(rows,now=None):
    cutoff=(now or dt.datetime.now())-dt.timedelta(days=7)
    result=[]
    for r in reversed(rows):
        try:at=dt.datetime.fromisoformat(str(r.get('ts','')))
        except ValueError:continue
        if at>=cutoff and (r.get('kind')=='error' or r.get('ok') is False or any(k in str(r.get('text','')) for k in ('错过','恢复','missed','recover'))):result.append(r)
    return result

class DiagnosticsPanel:
    def __init__(self,settings,pad):
        from ui_tasks import backup_export
        from ui_restore import choose_backup
        from ui_extras import RecoveryWindow
        self.settings=settings;self.app=settings.app;self.labels={};self.refresh_count=0
        g=settings._card(pad,'运行状态')
        head=self.decorate(g)
        flat_button(head,settings.tr('刷新状态'),self.refresh,font=settings.font(delta=-1),padx=10,pady=4).pack(side='right')
        for title,icon in (('任务调度','document'),('全局快捷键','keyboard'),('悬浮倒计时','monitor'),('屏幕常亮','sun')):
            row=tk.Frame(g,bg=C['card']);row.pack(fill='x',pady=2)
            image=tk.Label(row,bg=C['card']);image._photo=cozy_icon(row,icon,round(19*settings.s));image.config(image=image._photo);image.pack(side='left',padx=(0,8))
            settings._lab(row,title).pack(side='left');v=StatusBadge(row,'');v.config(width=round(85*settings.s),height=round(24*settings.s));v.pack(side='right');self.labels[title]=v
        g=settings._card(pad,'最近异常',note='最近7天，仅打开页面或手动刷新时更新')
        self.decorate(g)
        self.empty_flower=tk.Label(g,bg=C['card']);self.empty_flower._photo=ImageTk.PhotoImage(blossom(round(24*settings.s),0,False),master=settings);self.empty_flower.config(image=self.empty_flower._photo)
        self.empty_flower.pack(pady=(3,0))
        self.events=settings._lab(g,'',wraplength=430,fg=C['muted'],font=settings.font(delta=-1));self.events.pack(fill='x',pady=2)
        g=settings._card(pad,'诊断与恢复')
        self.decorate(g)
        buttons=settings._actions(g,[(settings.tr('复制诊断'),settings.copy_diagnostics,'normal'),(settings.tr('打开日志'),self.app.open_log,'normal'),(settings.tr('导出备份'),lambda:backup_export(self.app,settings),'normal')])
        for b in buttons:b._bg=C['input'];b._selection_outline='#D8CDEF';b.config(bg=C['input'],fg=C['fg'])
        extra=settings._expander(g,'备份与恢复',[]).body
        settings._actions(extra,[(settings.tr('导入备份'),lambda:choose_backup(self.app,settings),'normal'),(settings.tr('查看自动备份'),lambda:RecoveryWindow(self.app,settings),'normal')])
        settings._check(extra,'log_enabled',settings.T('set_log_enabled'))
        settings._expander(extra,'备份范围',['包含：常用设置、命名模板、高级任务定义','不包含：运行中的定时、队列、自启动项','配置损坏时自动尝试恢复；手动恢复前会显示预览。'])
    def decorate(self,body):
        head=body.master.pack_slaves()[0];icon=tk.Label(head,bg=C['card'])
        icon._photo=ImageTk.PhotoImage(blossom(round(26*self.settings.s),0,False),master=self.settings);icon.config(image=icon._photo)
        icon.pack(side='left',before=head.pack_slaves()[0],padx=(0,8));return head
    def refresh(self):
        self.refresh_count+=1;s=self.settings
        for title,state in runtime_status(self.app):
            badge=self.labels[title];badge.text=s.tr(state);good=state in ('正常','已注册','运行中','已开启')
            badge.fill='#C8E8D2' if good else '#F5D8DD' if state=='需处理' else '#E3DFEC';badge.ink='#285F40' if good else '#9E354F' if state=='需处理' else C['muted'];badge.redraw()
        rows=recent_anomalies(run_log.entries(550))
        if not self.app.cfg.get('log_enabled',True):text=s.tr('日志记录已关闭，仅显示已有记录')+'\n'
        else:text=''
        text+='\n'.join(str(r['ts'])[5:16]+'  '+s.tr(str(r.get('text',''))) for r in rows[:3]) if rows else s.tr('最近7天暂无异常记录')
        if len(rows)>3:text+='\n'+s.tr('更多记录可在执行日志中查看')
        if rows:self.empty_flower.pack_forget()
        elif not self.empty_flower.winfo_manager():self.empty_flower.pack(before=self.events,pady=(3,0))
        self.events.config(text=text,anchor='w' if rows else 'center',justify='left' if rows else 'center')
