"""Isolated prompt state/layout checks. No network, installation or OS action."""
import sys,os,tempfile,time,json
from pathlib import Path
from unittest.mock import patch
p=Path(__file__).resolve().parents[1];sys.path[:0]=[str(p/'src'),str(p/'tools')]
temp=tempfile.TemporaryDirectory();os.environ['APPDATA']=temp.name
from main import enable_dpi_awareness
enable_dpi_awareness()
import ui_main,autostart
ui_main.App._init_tray=lambda a:None;autostart.set_enabled=lambda *a:True
ui_main.perform=lambda *a,**k:(_ for _ in ()).throw(AssertionError('No real action'))
factor=float(sys.argv[1]);build=ui_main.App.build_ui
def scaled(a):a.root.tk.call('tk','scaling',factor*96/72);return build(a)
ui_main.App.build_ui=scaled;a=ui_main.App({'given':True,'action':'message'})
errors=[];a.root.report_callback_exception=lambda t,v,b:errors.append(str(v))
out=p/'核验/v224'/str(factor);out.mkdir(parents=True,exist_ok=True)
checks=[];sizes={}
def pump():
    end=time.monotonic()+.18
    while time.monotonic()<end:a.root.update();time.sleep(.003)
def check(name,value):assert value,name;checks.append(name)
from capture_window import capture
def shot(w,name):
    pump();capture(w).save(out/(name+'.png'));sizes[name]=(w.winfo_width(),w.winfo_height())
try:
    pump()
    a._active_task={'action':'sleep','mode':'countdown','seconds':1800};a.engine.start_countdown(1800);pump()
    from ui_summary import refresh
    refresh(a);a.skin_renderer.render(force=True);pump()
    for name,widget in [('headline',a.summary_title),('remaining',a.status)]:
        record=a.skin_renderer.tiles[widget];box=record['ink'].getbbox()
        check(name+' glyphs have vertical margin',box is not None and box[1]>=2 and box[3]<=record['ink'].height-2)
    shot(a.root,'running-summary');a.engine.stop();pump()
    from ui_messagebox import MessageDialog
    d=MessageDialog(a.root,'保存设置','你修改的设置还没有保存\n保存后即可在下次启动时继续使用','askyesnocancel',default='cancel',labels={'yes':'保存并关闭','no':'放弃更改','cancel':'继续编辑'})
    shot(d,'save-settings');d.destroy()
    from ui_release_update import UpdateWindow
    with patch.object(UpdateWindow,'worker',lambda *a:None):
        u=UpdateWindow(a,a.root);shot(u,'checking')
        check('checking hides empty notes and progress',not u.notes_frame.winfo_ismapped() and not u.progress.winfo_ismapped())
        u.events.put(('done',('release',None)));shot(u,'no-update')
        check('no update compact',u.winfo_height()<200*factor and u.winfo_width()<400*factor)
        check('accurate no update text','暂无更新' in u.label.cget('text'))
        u.events.put(('error','网络暂时不可用，请稍后重试。'));shot(u,'error')
        check('error hides empty controls',not u.notes_frame.winfo_ismapped() and not u.progress.winfo_ismapped())
        release={'tag':'v9.0.0','notes':'优化更新提示框。\n缩小普通确认框，长内容支持滚动。'}
        u.events.put(('done',('release',release)));shot(u,'new-version-short')
        check('release shows notes only',u.notes_frame.winfo_ismapped() and not u.progress.winfo_ismapped())
        release={'tag':'v9.0.0','notes':'较长的更新内容，可滚动查看完整信息。\n'*60}
        u.events.put(('done',('release',release)));shot(u,'new-version-long')
        check('long release bounded',u.winfo_height()<=365*factor)
        u.fetch();shot(u,'download')
        check('download has progress without notes',u.progress.winfo_ismapped() and not u.notes_frame.winfo_ismapped())
        u.destroy();pump();check('close cancels worker',u.cancel.is_set())
    from ui_messagebox import MessageDialog
    for name,text,kind in [('info','设置已保存。','showinfo'),('confirm','已有任务正在运行。请选择替换当前任务、加入队列或取消。','askyesnocancel'),('long-error','详细错误信息，请检查目标文件与目录。\n'*60,'showerror')]:
        labels={'yes':'替换当前任务','no':'加入队列','cancel':'取消'} if kind=='askyesnocancel' else None
        d=MessageDialog(a.root,'提示',text,kind,default='cancel',labels=labels);shot(d,name)
        check(name+' bounded',d.winfo_height()<=385*factor)
        if name=='info':check('short prompt compact',d.winfo_height()<160*factor)
        if name=='confirm':d.event_generate('<Escape>');pump();check('escape cancels',d.result=='cancel')
        else:d.destroy()
    from ui_log import LogWindow
    log=LogWindow(a)
    for name,detail in [('log-short','目标程序不存在。'),('log-long','文件路径或错误详情。\n'*60)]:
        log.filtered_rows=[dict(ts='2026-10-21 12:00:00',kind='error',text='执行失败',detail=detail)];log.selected=0;log._show_detail()
        wins=[w for w in log.winfo_children() if isinstance(w,__import__('tkinter').Toplevel)]
        d=wins[-1];shot(d,name);check(name+' bounded',d.winfo_height()<=365*factor);d.destroy()
    log.destroy();check('no callback errors',not errors)
finally:a.quit_app()
(out/'results.json').write_text(json.dumps(dict(checks=checks,sizes=sizes,errors=errors),ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(scale=factor,checks=len(checks),sizes=sizes),ensure_ascii=False))
