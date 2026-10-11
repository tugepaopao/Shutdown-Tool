import sys,os,time,tempfile,json,subprocess
from pathlib import Path
p=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(p/'src'));sys.stdout.reconfigure(encoding='utf-8')
if len(sys.argv)==1:
 results={}
 for ratio in (1,1.25,1.5,2):
  run=subprocess.run([sys.executable,__file__,str(ratio)],cwd=p,capture_output=True,text=True,encoding='utf-8',env=dict(os.environ,PYTHONIOENCODING='utf-8'),timeout=70)
  print(run.stdout,flush=True);assert run.returncode==0,run.stderr;results[str(ratio)]=json.loads(run.stdout.strip().splitlines()[-1])
 (p/'tools/v177-dpi-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8');raise SystemExit()
from main import enable_dpi_awareness
enable_dpi_awareness()
import tkinter as tk
ratio=float(sys.argv[1]);original=tk.Tk
class ScaledTk(original):
 def __init__(self,*a,**kw):
  super().__init__(*a,**kw);self.tk.call('tk','scaling',(96/72)*ratio)
tk.Tk=ScaledTk
import autostart
from ui_main import App
from ui_cozy import CozyButton
App._init_tray=lambda s:None;autostart.set_enabled=lambda *a:True
with tempfile.TemporaryDirectory(prefix='cozy-dpi-') as folder:
 os.environ['APPDATA']=folder;app=App({'given':True,'action':'message'});app.cfg['confirm_on_exit']=False;errors=[];checks=[];app.root.report_callback_exception=lambda *a:errors.append(str(a[1]))
 def pump(t=.15):
  end=time.monotonic()+t
  while time.monotonic()<end:app.root.update();time.sleep(.005)
 def check(name,value):checks.append([name,bool(value)]);assert value,name
 try:
  pump();app.cfg['language']='EN';app.apply_settings();pump(.65)
  check('main fits screen',app.root.winfo_height()<app.root.winfo_screenheight()-35 and app.root.winfo_width()<app.root.winfo_screenwidth())
  check('actions readable',all(w.winfo_width()+3>=w.winfo_reqwidth() for w in app.action_widgets.values()))
  check('disabled action cannot invoke',app.summary_stop.invoke()=='')
  width,height=app.root.winfo_width(),app.root.winfo_height();app.root.geometry(f'{width+100}x560');pump()
  check('fixed window keeps footer',app.btn_start.winfo_ismapped() and app.sbar.winfo_rooty()+app.sbar.winfo_height()<=app.root.winfo_rooty()+app.root.winfo_height())
  check('fixed dimensions resist resize',app.root.winfo_width()==width and app.root.winfo_height()==height and not any(app.root.resizable()))
  settings=app.open_settings();pump();settings._show('appearance');settings._pick_skin('orange');settings.on_apply();pump(.65);check('skin applied at scale',app.skin_renderer.key=='orange');settings._show('floating');settings.v['float_enabled'].set(True);settings.on_apply();pump();floating=app.floating.window
  check('floating scaled compactly',floating.winfo_width()==round(220*floating.s))
  check('floating controls fit',floating.pause.winfo_x()+floating.pause.winfo_width()<floating.winfo_width() and floating.cancel.winfo_y()+floating.cancel.winfo_height()<floating.winfo_height())
  floating.move(350,0);floating.drag=(0,0,0,0);floating.end_drag(None);pump();check('top edge stays expanded',floating.winfo_height()==floating.panel_height)
  check('no callbacks',not errors)
 finally:app.floating.close();app.engine.stop();app.desktop.close();app.root.destroy()
 print(json.dumps(dict(scale=ratio,checks=checks,errors=errors)),flush=True)
