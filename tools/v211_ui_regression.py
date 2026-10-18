"""Isolated editor popup, keyboard and source performance baseline."""
import os,sys,tempfile,time,json,tkinter as tk
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import psutil
p=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(p/'src'))
tmp=tempfile.TemporaryDirectory();os.environ['APPDATA']=tmp.name
from main import enable_dpi_awareness
enable_dpi_awareness()
import autostart,ui_main
autostart.set_enabled=lambda *a:True;ui_main.App._init_tray=lambda a:None
ui_main.perform=lambda *a,**k:(_ for _ in ()).throw(AssertionError('real actions forbidden'))
from ui_tasks import TaskEditor
from ui_date_picker import DatePicker
from ui_soft_controls import SoftToggle,SoftRadio,Segments,SoftChoice
scale=float(sys.argv[1]) if len(sys.argv)>1 else 1.5
start=time.perf_counter();a=ui_main.App({'given':True,'action':'message'});a.cfg.update(dict(confirm_on_exit=False,autostart=False))
a.root.tk.call('tk','scaling',scale*96/72)
errors=[];checks=[];measurements={};a.root.report_callback_exception=lambda t,v,b:errors.append(str(v))
def pump(seconds=.08):
    end=time.perf_counter()+seconds
    while time.perf_counter()<end:a.root.update();time.sleep(.002)
def check(name,value):
    assert value,name
    checks.append(name);print('PASS',name,flush=True)
out=p/('核验/v211/scale-'+str(scale));out.mkdir(parents=True,exist_ok=True)
try:
    pump(.15);measurements['source_start_ms']=round((time.perf_counter()-start)*1000,2)
    editor=TaskEditor(a,dict(name='测试预约',mode='calendar',action='message',message_text='测试',at='2026-11-01T22:00:00'),modes=('calendar','download','network','combined','chain'))
    pump();layout=editor.advanced_layout;field=layout.inputs['date']
    invoked=[];original=field.command;field.command=lambda:invoked.append(True)
    field.click(SimpleNamespace(x=8));field.entry.event_generate('<Button-1>',x=8,y=8);pump()
    check('date text does not open picker',not invoked)
    field.click(SimpleNamespace(x=field.winfo_width()-10));check('calendar icon invokes picker',len(invoked)==1)
    field.command=original
    picker=DatePicker(editor,a,editor.v['date'].get(),anchor=field);pump()
    x,y=picker.winfo_rootx(),picker.winfo_rooty()
    check('calendar adjacent to invoking field',abs(y-(field.winfo_rooty()+field.winfo_height()))<15 or abs(y+picker.winfo_height()-field.winfo_rooty())<15 or y==6)
    from capture_window import capture
    # Native HWND helper captures the real calendar/editor pair without executing tasks.
    try:
        import ctypes
        from ctypes import wintypes as W
        u=ctypes.windll.user32;u.GetAncestor.argtypes=[W.HWND,W.UINT];u.GetAncestor.restype=W.HWND
        capture(picker).save(out/'calendar.png')
        capture(editor).save(out/'editor.png')
    except (ImportError,TypeError):pass
    picker.outside(SimpleNamespace(x_root=field.winfo_rootx()+field.winfo_width()-10,y_root=field.winfo_rooty()+10));pump()
    check('click calendar icon again dismisses picker',not picker.winfo_exists())
    check('closing calendar restores editor grab',editor.grab_current() is editor)
    box=SoftToggle(layout.footer,tk.BooleanVar(editor,False));box.pack(side='left');pump();box.focus_force();pump()
    box.event_generate('<Return>');pump();check('toggle Enter changes value without saving editor',box.variable.get() and editor.winfo_exists())
    check('focused custom control has visible focus indicator',bool(box.find_withtag('focus-ring')))
    box.event_generate('<space>');pump();check('toggle Space switches off',not box.variable.get())
    layout.segment.focus_force();pump();layout.segment.event_generate('<Right>');pump()
    check('segments keyboard arrows work',layout.segment.index==1)
    editor.destroy();pump()
    process=psutil.Process();before=process.memory_info().rss;threads=process.num_threads()
    for count in (0,50,200):
        a.cfg['templates']=[dict(id=str(i),name=f'模板 {i}',action='message',message_text='测试',mode='countdown',seconds=600) for i in range(count)]
        start=time.perf_counter();a.open_task_center('templates');pump(.05)
        measurements[f'open_{count}_ms']=round((time.perf_counter()-start)*1000,2)
        samples=[]
        for _ in range(10):
            start=time.perf_counter();a._task_center_win.refresh_status();samples.append((time.perf_counter()-start)*1000)
        measurements[f'unchanged_{count}_mean_ms']=round(sum(samples)/len(samples),3)
    for _ in range(15):a.open_settings();a.open_task_center('templates');pump(.01)
    measurements['switch_memory_delta_mib']=round((process.memory_info().rss-before)/1024**2,2)
    measurements['thread_delta']=process.num_threads()-threads
    from ui_workspace import hide_workspace
    hide_workspace(a);pump(.1);cpu=process.cpu_times();start=time.perf_counter();pump(2)
    now=process.cpu_times();measurements['hidden_cpu_one_core_percent']=round(100*((now.user+now.system)-(cpu.user+cpu.system))/(time.perf_counter()-start),2)
    check('no callback exceptions',not errors)
finally:
    for child in list(a.root.winfo_children()):
        if isinstance(child,tk.Toplevel):child.destroy()
    a.cfg['confirm_on_exit']=False;a.quit_app()
    (out/'results.json').write_text(json.dumps(dict(passed=len(checks),checks=checks,errors=errors,measurements=measurements),ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(measurements,ensure_ascii=False))
