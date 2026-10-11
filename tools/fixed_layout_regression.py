"""Fixed, fully visible main layout and control-state visual regression."""
import os,sys,time,tempfile,json
from pathlib import Path
p=Path(__file__).resolve().parent.parent;sys.path[:0]=[str(p/'src'),str(p/'tools')]
from main import enable_dpi_awareness
enable_dpi_awareness()
import tkinter as tk,tkinter.font as tkfont
from ui_main import App,MODE_KEYS
from ui_transition import walk
from theme import theme
import autostart,exe_test,ctypes
def root_hwnd(root):
 u=ctypes.windll.user32;u.GetAncestor.argtypes=[ctypes.c_void_p,ctypes.c_uint];u.GetAncestor.restype=ctypes.c_void_p;return u.GetAncestor(root.winfo_id(),2)
App._init_tray=lambda s:None;autostart.set_enabled=lambda *a:True
checks=[];errors=[]
def check(n,v):checks.append([n,bool(v)]);print(('PASS ' if v else 'FAIL ')+n,flush=True);assert v,n
with tempfile.TemporaryDirectory(prefix='v174-fixed-') as folder:
 os.environ['APPDATA']=folder;app=App({'given':True,'action':'message'});app.cfg['confirm_on_exit']=False;app.root.report_callback_exception=lambda *a:errors.append(str(a[1]))
 def pump(t=.15):
  end=time.monotonic()+t
  while time.monotonic()<end:app.root.update();time.sleep(.003)
 try:
  pump();size=(app.root.winfo_width(),app.root.winfo_height())
  check('main has no scroll canvas',not any(isinstance(w,tk.Canvas) and w.cget('yscrollcommand') for w in walk(app.root)))
  check('main cannot resize',not any(app.root.resizable()) and app.root.minsize()==app.root.maxsize())
  app.root.geometry(f'{size[0]+90}x{size[1]+150}');pump();check('requested larger size is blocked',(app.root.winfo_width(),app.root.winfo_height())==size)
  app.root.geometry(f'{size[0]-90}x560');pump();check('requested smaller size is blocked',(app.root.winfo_width(),app.root.winfo_height())==size)
  before=app.pages['actions'].winfo_rooty();app.root.event_generate('<MouseWheel>',delta=-120);pump();check('wheel cannot displace main content',app.pages['actions'].winfo_rooty()==before)
  check('title to actions gap compact',app.pages['actions'].winfo_rooty()-app.titlebar.winfo_rooty()-app.titlebar.winfo_height()<=12)
  check('time to footer gap compact',app.now_box.winfo_rooty()-app.pages['time'].winfo_rooty()-app.pages['time'].winfo_height()<=16)
  check('no bottom filler',app.root.winfo_rooty()+app.root.winfo_height()-app.sbar.winfo_rooty()-app.sbar.winfo_height()<=12)
  check('time starts with heading, no top separator',not any(isinstance(w,tk.Frame) and int(w.cget('height'))==1 for w in app.pages['time'].winfo_children()))
  gp=app.preset_row.master;check('preset heading matches body size',tkfont.Font(root=app.root,font=gp.cget('font')).actual('size')==theme.base_size)
  check('controls share card background',app.time_btn_row.cget('bg')==theme.c('card'))
  for lang in ('CHS','CHT','EN'):
   app.cfg['language']=lang;app.apply_settings();pump()
   for mode in MODE_KEYS:
    app.mode_var.set(mode);app._refresh_time_groups();app._refresh_mode_btns();pump()
    bottom=app.root.winfo_rooty()+app.root.winfo_height()
    check(lang+' '+mode+' content fully visible',app.btn_start.winfo_ismapped() and app.sbar.winfo_rooty()+app.sbar.winfo_height()<=bottom and app.pages['actions'].winfo_rooty()>=app.root.winfo_rooty())
   exe_test.grab_window(root_hwnd(app.root),'v174-fixed-'+lang+'.png')
  app.cfg['language']='CHS';app.apply_settings();app.mode_var.set('countdown');app._refresh_time_groups();pump()
  app.btn_start._interaction(hover=True,pressed=True);pump();exe_test.grab_window(root_hwnd(app.root),'v174-start-pressed.png');app.btn_start._interaction(hover=False,pressed=False)
  check('pressed start plate has zero native border',int(app.btn_start.cget('borderwidth'))==0 and app.btn_start.master.cget('bg')==theme.c('card'))
  check('no callbacks',not errors)
 finally:app.engine.stop();app.floating.close();app.desktop.close();app.root.destroy()
(p/'tools/v174-fixed-results.json').write_text(json.dumps(dict(checks=checks,errors=errors,size=size),ensure_ascii=False,indent=2),encoding='utf-8')
