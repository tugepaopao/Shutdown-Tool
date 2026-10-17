"""Isolated workspace regression; no real power actions or hardware writes."""
import os,sys,tempfile,time,json,copy,tkinter as tk
from pathlib import Path
from unittest.mock import patch,Mock
p=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(p/'src'))
sys.stdout.reconfigure(encoding='utf-8')
temp=tempfile.TemporaryDirectory(prefix='shutdown-workspace-')
os.environ['APPDATA']=temp.name
from main import enable_dpi_awareness
enable_dpi_awareness()
import actions,autostart
from ui_main import App
from ui_window import activate_dialog,prepare,show
from ui_workspace import hide_workspace,restore_workspace,allow_exit,keep_visible
from ui_settings import PAGES
from task_store import normalize
App._init_tray=lambda self:None
autostart.set_enabled=lambda *a:True
actions.perform=lambda *a,**k:(_ for _ in ()).throw(AssertionError('Real actions forbidden'))
checks=[];errors=[];timings={}
factor=float(sys.argv[1]) if len(sys.argv)>1 else 1.0
OriginalTk=tk.Tk
class ScaledTk(OriginalTk):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);self.tk.call('tk','scaling',factor*96/72)
tk.Tk=ScaledTk
def check(name,value):
 print(('PASS ' if value else 'FAIL ')+name,flush=True);checks.append((name,bool(value)));assert value,name
def pump(seconds=.06):
 end=time.perf_counter()+seconds
 while time.perf_counter()<end:a.root.update();time.sleep(.002)
def timed(name,fn):
 start=time.perf_counter();result=fn();a.root.update_idletasks();timings[name]=round((time.perf_counter()-start)*1000,2);return result
class Hardware:
 def monitors(self):return []
 def audio(self):return dict(value=25,muted=False)
a=App({'given':True,'action':'message'})
a.root.report_callback_exception=lambda t,v,b:errors.append(str(v))
a.cfg.update({'confirm_on_exit':False,'autostart':False,'float_enabled':False,'popup_at_10s':False,'sound_at_10s':False,'cancel_at_10s':False})
try:
 pump(.2)
 settings=timed('settings_first_ms',a.open_settings);pump()
 center=timed('center_first_ms',a.open_task_center);pump()
 log=a.open_log();pump()
 check('workspace windows have no transient owner',all(not str(w.transient()) for w in (settings,center,log)))
 check('templates and advanced panels are lazy',set(center.panels)=={'queue'})
 for _ in range(20):
  assert a.open_settings() is settings
  assert a.open_task_center() is center
 check('20 repeated opens reuse live windows',settings.winfo_viewable() and center.winfo_viewable())
 for w in (a.root,settings,center,log,a.root):
  activate_dialog(w);pump()
  stack=tuple(str(x) for x in a.root.tk.call('wm','stackorder',a.root))
  check('activated window reaches top '+str(w),stack[-1]==str(w))
 center.iconify();pump();a.open_task_center();pump()
 check('minimized center restores',center.state()=='normal')
 a.root.iconify();pump();a.open_settings();pump()
 check('settings usable while main minimized',settings.winfo_viewable())
 a.show_window();pump()
 settings.v['toast_seconds'].set('27');draft=settings.v['toast_seconds'].get()
 hide_workspace(a);pump()
 check('tray hides all workspace windows',all(w.state()=='withdrawn' for w in (a.root,settings,center,log)))
 restore_workspace(a);pump()
 check('tray restores windows and draft',all(w.state()=='normal' for w in (a.root,settings,center,log)) and settings.v['toast_seconds'].get()==draft)
 modal=tk.Toplevel(center);prepare(modal);modal.transient(center);tk.Label(modal,text='Test editor').pack();show(modal);modal.grab_set();pump()
 check('open requests respect modal editor',a.open_settings() is modal and a.open_task_center() is modal)
 a.show_window();pump();check('main activation preserves modal grab',a.root.grab_current() is modal)
 hide_workspace(a);check('tray cannot orphan active editor',center.state()=='normal')
 modal.destroy();pump();check('editor closure releases grab',a.root.grab_current() is None)
 from ui_localize import messagebox
 with patch.object(messagebox,'askyesnocancel',return_value=None):check('cancel exit preserves draft',not allow_exit(a) and settings.winfo_exists())
 settings.discard()
 with patch('ui_pc_controls.WindowsControls',Hardware):
  for key,_,_ in PAGES:settings._show(key);pump()
  for key,_,_ in PAGES:timed('settings_cached_'+key+'_ms',lambda key=key:settings._show(key));pump()
  settings._show('pc');pump(.3);pc=settings.pc_panel
  settings._show('general');pump(.2)
  check('hidden idle PC panel has no timers',pc._poll_id is None and pc._periodic_id is None)
  received=[];pc._submit(lambda:42,lambda value,error:received.append(value));pump(.2)
  check('hidden PC request completes then stops polling',received==[42] and pc._poll_id is None)
 a.cfg['templates']=[dict(normalize({'action':'message','seconds':60,'name':'Template '+str(i)}),id=i) for i in range(200)]
 center.select_tab('templates');pump();panel=center.panels['templates'];panel.tv.selection_set('10');panel.tv.yview_moveto(.5);position=panel.tv.yview()
 with patch.object(panel.tv,'item',wraps=panel.tv.item) as item,patch.object(panel,'_layout_columns',wraps=panel._layout_columns) as layout:
  timed('unchanged_200_templates_ms',panel.refresh_status)
  check('unchanged template refresh writes no rows or layout',item.call_count==0 and layout.call_count==0)
 check('refresh preserves selection and scrolling',panel.tv.selection()==('10',) and panel.tv.yview()==position)
 for key in ('queue','templates','advanced')*7:
  timed('center_cached_'+key+'_ms',lambda key=key:center.select_tab(key));pump(.01)
 check('page switches have no screenshot overlay',getattr(settings,'_page_cover',None) is None and getattr(center,'_page_cover',None) is None)
 # Simulate a disconnected right monitor, then a negative-coordinate monitor.
 for areas,start in [([(0,0,1920,1080)],(3000,200)),([(-1920,0,0,1080)],(-3000,100))]:
  center.geometry(f'+{start[0]}+{start[1]}');pump()
  with patch('ui_floating.workareas',return_value=areas):keep_visible(center)
  pump();x,y=center.winfo_x(),center.winfo_y();left,top,right,bottom=areas[0]
  check('display recovery '+str(left),left<=x and top<=y and x+center.winfo_width()<=right and y+center.winfo_height()<=bottom)
 keep_visible(center)
 a.engine.start_countdown(60);generation=a.engine.generation
 hide_workspace(a);pump();restore_workspace(a);pump()
 check('window switching preserves timer',a.engine.is_running() and a.engine.generation==generation)
 a.engine.stop()
 from capture_window import capture
 settings._show('general');activate_dialog(settings);pump(.1)
 (p/'核验').mkdir(exist_ok=True)
 capture(settings).save(p/f'核验/workspace-settings-{factor}.png')
 center.select_tab('queue');activate_dialog(center);pump(.1)
 capture(center).save(p/f'核验/workspace-center-{factor}.png')
 settings.v['toast_seconds'].set('28')
 with patch.object(messagebox,'askyesnocancel',return_value=False):check('discard permits exit',allow_exit(a) and not settings.winfo_exists())
 settings=a.open_settings();settings.v['toast_seconds'].set('29')
 with patch.object(messagebox,'askyesnocancel',return_value=True):check('save permits exit',allow_exit(a) and a.cfg.get('toast_seconds')==29)
 check('no UI callback errors',not errors)
 (p/'核验').mkdir(exist_ok=True)
 (p/f'核验/workspace-regression-{factor}.json').write_text(json.dumps(dict(checks=checks,timings=timings,errors=errors),ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(timings,ensure_ascii=False),flush=True)
finally:
 a.engine.stop();a.automation.close();a.floating.close();a.desktop.close();a.display_awake.close();a.root.destroy();temp.cleanup()
