import sys,os,time,tempfile,json,traceback,ctypes
from pathlib import Path
p=Path(__file__).resolve().parent.parent;r=p;sys.path[:0]=[str(p/'src'),str(p/'tools')]
from main import enable_dpi_awareness
enable_dpi_awareness()
from ui_main import App,MODE_KEYS
import autostart,skins,config_backups,exe_test as ui
from theme import theme
from app_config import Config
App._init_tray=lambda s:None;autostart.set_enabled=lambda *a:True
ui.SHOTS=str(p/'tools/shots');Path(ui.SHOTS).mkdir(parents=True,exist_ok=True)
u=ctypes.windll.user32;u.GetAncestor.argtypes=[ctypes.c_void_p,ctypes.c_uint];u.GetAncestor.restype=ctypes.c_void_p
checks=[];errors=[]
def check(n,v):checks.append([n,bool(v)]);print(('PASS ' if v else 'FAIL ')+n,flush=True);assert v,n
with tempfile.TemporaryDirectory(prefix='v1711-skins-') as folder:
 os.environ['APPDATA']=folder;app=App({'given':True,'action':'message'});app.cfg['confirm_on_exit']=False
 app.root.report_callback_exception=lambda c,e,t:(errors.append(str(e)),traceback.print_exception(c,e,t))
 def pump(t=.2):
  end=time.monotonic()+t
  while time.monotonic()<end:app.root.update();time.sleep(.004)
 try:
  pump(.7);size=(app.root.winfo_width(),app.root.winfo_height());original_buttons=app.btn_start,app.btn_pause,app.btn_stop,app.btn_clear
  check('fixed main size',not any(app.root.resizable()) and app.root.minsize()==app.root.maxsize())
  check('all eight prepared wallpapers present',all(skins.artwork(k).size[0]>500 and skins.preview(k).size[0]>50 for k in skins.SKIN_ORDER))
  app.apply_preset(('sec',600));pump();check('preset really starts timer',app.engine.is_running());app.btn_pause.invoke();pump();check('pause button really pauses',app.engine.paused);due=(app.engine.generation,app.engine.remaining())
  settings=app.open_settings();settings._show('appearance');pump();check('eight live skin choices',set(settings.skin_tiles)==set(skins.SKIN_ORDER))
  settings._pick_skin('pink');pump();check('choice before apply leaves existing skin',app.skin_renderer.key=='solid');settings.destroy();app._settings_win=None
  check('cancel leaves persisted skin',app.cfg.get('skin')=='solid')
  settings=app.open_settings();settings._show('appearance');pump()
  for key in skins.SKIN_ORDER:
   settings.skin_tiles[key].invoke();settings.on_apply();pump(.8)
   check(key+' applied and persisted',app.skin_renderer.key==key and app.cfg.get('skin')==key and json.loads(Path(__import__('app_config').config_file()).read_text(encoding='utf-8'))['skin']==key)
   check(key+' keeps timer and real controls',app.engine.is_running() and app.engine.paused and (app.engine.generation,app.engine.remaining())==due and (app.btn_start,app.btn_pause,app.btn_stop,app.btn_clear)==original_buttons)
   check(key+' native layout fully visible',app.sbar.winfo_rooty()+app.sbar.winfo_height()<=app.root.winfo_rooty()+app.root.winfo_height() and app.btn_start.winfo_ismapped())
   check(key+' fixed geometry unchanged',(app.root.winfo_width(),app.root.winfo_height())==size)
   ui.grab_window(u.GetAncestor(app.root.winfo_id(),2),'v1711-skin-'+key+'.png')
  ui.grab_window(u.GetAncestor(settings.winfo_id(),2),'v1711-settings-skins.png');settings.destroy();app._settings_win=None
  generation=app.skin_renderer.generation;rects=[app.skin_renderer.box(w) for w in app.action_widgets.values()];pump(2)
  check('idle does not grow controls or recomposite background',rects==[app.skin_renderer.box(w) for w in app.action_widgets.values()] and generation==app.skin_renderer.generation)
  x,y=app.root.winfo_x(),app.root.winfo_y();app.root.geometry(f'+{x+35}+{y+15}');pump(.4)
  check('moving main does not regenerate artwork',generation==app.skin_renderer.generation)
  app.root.withdraw();pump(.1);app.show_window();pump(.45);check('hide and restore preserves skin cards',app.skin_renderer.active and app.skin_renderer.scene is not None and app.btn_start.winfo_ismapped())
  app.btn_pause.invoke();pump();check('resume after skin switches',app.engine.is_running() and not app.engine.paused);app.btn_stop.invoke();pump();check('stop after skin switches',not app.engine.is_running())
  for action,b in app.action_widgets.items():
   b.invoke();pump(.04);check(action+' actual selection callback',app.action_var.get()==action)
  app.action_widgets['message'].invoke()
  for lang in ('CHS','CHT','EN'):
   app.cfg['language']=lang;app.apply_settings();pump(.65)
   for mode in MODE_KEYS:
    app.mode_var.set(mode);app._refresh_time_groups();app._refresh_mode_btns();pump(.2)
    check(lang+' '+mode+' fields visible',app.btn_start.winfo_ismapped() and app.sbar.winfo_rooty()+app.sbar.winfo_height()<=app.root.winfo_rooty()+app.root.winfo_height())
   ui.grab_window(u.GetAncestor(app.root.winfo_id(),2),'v1711-main-'+lang+'.png')
  try:config_backups.validate_settings({'skin':'not-real'})
  except ValueError:check('invalid imported skin rejected',True)
  else:check('invalid imported skin rejected',False)
  check('missing legacy skin selects solid default',skins.valid(None)=='solid')
  check('no Tcl callbacks',not errors)
 finally:
  app.skin_renderer.suspend();app.engine.stop();app.floating.close();app.desktop.close();app.root.destroy()
(p/'tools/v1711-skin-results.json').write_text(json.dumps({'checks':checks,'errors':errors,'size':size},ensure_ascii=False,indent=2),encoding='utf-8')
