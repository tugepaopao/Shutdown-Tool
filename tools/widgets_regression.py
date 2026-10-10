import os,sys,time,tempfile,json,math,ctypes
from pathlib import Path
from unittest.mock import patch
p=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(p/'src'));sys.stdout.reconfigure(encoding='utf-8')
from main import enable_dpi_awareness
enable_dpi_awareness()
from ui_main import App
import autostart,system_metrics
from ui_floating import clamp_position
from task_store import export_backup,read_backup
from config_backups import validate_settings
from PIL import ImageGrab
checks=[];errors=[]
def check(name,value):
 checks.append([name,bool(value)]);print(('PASS ' if value else 'FAIL ')+name,flush=True);assert value,name
check('rate uses actual elapsed time',system_metrics.rate(3000,1000,2)==1000)
check('counter reset cannot produce negative speed',system_metrics.rate(10,20,1)==0)
check('zero time guarded',system_metrics.rate(10,0,0)==0)
check('position clamped after monitor removed',clamp_position(-1800,90,350,190,[(0,0,1920,1080)])==(0,90))
check('negative monitor position supported',clamp_position(-1500,100,350,190,[(-1920,0,0,1080),(0,0,1920,1080)])==(-1500,100))
with tempfile.TemporaryDirectory(prefix='v169-tests-') as folder:
 os.environ['APPDATA']=folder;App._init_tray=lambda s:None;autostart.set_enabled=lambda *a:True
 app=App({'given':True,'action':'message'});app.cfg['confirm_on_exit']=False;app.root.report_callback_exception=lambda cls,exc,tb:errors.append(str(exc));app.cfg['resume_timer']=False
 def pump(seconds=.3):
  until=time.monotonic()+seconds
  while time.monotonic()<until:app.root.update();time.sleep(.01)
 def shot(w,name):
  hidden=app.floating.window if app.floating.window and w is not app.floating.window else None
  if hidden:hidden.withdraw()
  w.attributes('-topmost',True);w.lift();pump();(p/'tools/shots').mkdir(exist_ok=True);ImageGrab.grab(bbox=(w.winfo_rootx(),w.winfo_rooty(),w.winfo_rootx()+w.winfo_width(),w.winfo_rooty()+w.winfo_height()),all_screens=True).save(p/'tools/shots'/name)
  if hidden:hidden.deiconify()
 try:
  check('floating default off',app.floating.window is None)
  main_children=list(app.root.winfo_children());settings=app.open_settings();pump()
  check('two new settings pages',all(k in settings.pages for k in ('monitor','floating')))
  check('monitor idle on another page',settings.monitor_panel.sampler is None)
  settings._show('monitor');pump(1.5);panel=settings.monitor_panel
  check('monitor shows real CPU/memory/disk',all(panel.last.get(k) is not None for k in ('cpu','memory','disk')))
  check('network real second sample',panel.last.get('download') is not None)
  shot(settings,'v169-monitor-CHS.png');sampler=panel.sampler
  settings._show('floating');pump();check('sampling stops when page changes',sampler.stop_event.is_set() and panel.sampler is None)
  settings.v['float_enabled'].set(True);settings.v['float_opacity'].set(65);settings.v['float_topmost'].set(True);settings.on_apply();pump();floating=app.floating.window
  check('Apply opens floating window',floating is not None and floating.winfo_exists())
  check('opacity saved and applied',app.cfg.get('float_opacity')==65 and abs(floating.attributes('-alpha')-.65)<.01)
  check('idle controls disabled',str(floating.pause.cget('state'))=='disabled')
  settings.destroy();app._settings_win=None
  app._active_task={'action':'message','message_text':'safe test'};app.engine.start_countdown(120);pump(1.3)
  check('float follows existing timer',floating.clock.cget('text').startswith('00:01:'))
  floating.pause_timer();pump();before=app.engine.remaining();pump(.7);check('pause freezes existing timer',app.engine.paused and abs(app.engine.remaining()-before)<.1)
  check('paused text and resume button',floating.pause.cget('text')==app.T('btn_resume_s'))
  app.cfg['float_opacity']=100;floating.refresh();shot(floating,'v169-floating-paused.png');floating.pause_timer();pump();check('resume works',not app.engine.paused)
  floating.move(-1500,100);floating.drag=(0,0,0,0);floating.end_drag(None);check('position is persisted',app.cfg.get('float_positioned'))
  app.root.withdraw();pump();check('float survives tray hide',floating.state()=='normal' and bool(ctypes.windll.user32.IsWindowVisible(floating.winfo_id())))
  app.root.deiconify();app.root.iconify();pump();check('float survives taskbar minimize',bool(ctypes.windll.user32.IsWindowVisible(floating.winfo_id())));app.root.deiconify();pump()
  app.task_queue=[{'action':'message','mode':'countdown','seconds':30}];floating.cancel_timer();pump();check('cancel only stops current timer',not app.engine.is_running() and len(app.task_queue)==1)
  for lang in ('CHS','CHT','EN'):
   app.cfg['language']=lang;app.apply_settings();pump();settings=app.open_settings();settings._show('monitor');pump(1.1)
   shot(app.root,'v169-main-'+lang+'.png')
   check('monitor nav translated '+lang,app.T('mon_title') in settings.nav.item('monitor','text'))
   shot(settings,'v169-monitor-'+lang+'.png');settings._show('floating');pump();shot(settings,'v169-settings-floating-'+lang+'.png');settings.destroy();app._settings_win=None
  app.cfg.update(dict(float_enabled=True,float_x=-1300,float_y=100));backup=Path(folder)/'backup.json';export_backup(app.cfg,backup);restored,_,_=read_backup(backup)
  check('backup accepts negative screen coordinates',restored['float_x']==-1300)
  check('import disables float and resets cross-device position',not restored['float_enabled'] and not restored['float_positioned'])
  app.cfg['float_enabled']=False;app.floating.apply();pump();check('disable destroys floating window',app.floating.window is None)
  try:validate_settings(dict(app.cfg.data,float_opacity=0));valid=True
  except ValueError:valid=False
  check('corrupt opacity cannot become invisible',not valid)
  scale=app.root.tk.call('tk','scaling');app.root.tk.call('tk','scaling',3.0);app.cfg['float_enabled']=True;app.floating.apply();pump();large=app.floating.window
  check('large DPI floating controls fit',large.winfo_height()>=large.winfo_reqheight() and large.winfo_width()>=large.winfo_reqwidth())
  app.cfg['float_enabled']=False;app.floating.apply();app.root.tk.call('tk','scaling',scale)
  check('no Tk callback errors',not errors)
 finally:
  app.cfg['float_enabled']=False;app.floating.close();app.engine.stop();app.desktop.close();app.root.destroy()
(p/'tools/v169-widgets-results.json').write_text(json.dumps(dict(checks=checks,errors=errors),ensure_ascii=False,indent=2),encoding='utf-8')
