import sys,os,time,tempfile,json,ctypes,traceback
from pathlib import Path
p=Path(__file__).resolve().parent.parent;sys.path[:0]=[str(p/'src'),str(p/'tools')]
from main import enable_dpi_awareness
enable_dpi_awareness()
from ui_main import App
import autostart,skins,config_backups,exe_test as ui
from theme import theme,ACCENT_ORDER,ACCENTS
from app_config import config_file,Config
App._init_tray=lambda s:None;autostart.set_enabled=lambda *a:True
ui.SHOTS=str(p/'tools/shots');checks=[];errors=[];samples=[]
u=ctypes.windll.user32;u.GetAncestor.argtypes=[ctypes.c_void_p,ctypes.c_uint];u.GetAncestor.restype=ctypes.c_void_p
def check(n,v):checks.append([n,bool(v)]);print(('PASS ' if v else 'FAIL ')+n,flush=True);assert v,n
with tempfile.TemporaryDirectory(prefix='v1711-appearance-') as folder:
 os.environ['APPDATA']=folder
 # Existing custom backgrounds migrate to solid without discarding other settings.
 c=Config();c.data.update(skin='custom',background_image='missing.jpg',accent='green',message_text='migration-proof');Path(config_file()).write_text(json.dumps(c.data),encoding='utf-8');c=Config()
 check('v176 custom config safely migrates',c['skin']=='solid' and c['accent']=='green' and c['message_text']=='migration-proof' and 'background_image' not in c.data and not c.recovery_notice)
 app=App({'given':True,'action':'message'});app.cfg['confirm_on_exit']=False
 app.root.report_callback_exception=lambda c,e,t:(errors.append(str(e)),traceback.print_exception(c,e,t))
 def pump(t=.2):
  end=time.monotonic()+t
  while time.monotonic()<end:app.root.update();time.sleep(.003)
 try:
  pump(.5);size=(app.root.winfo_width(),app.root.winfo_height());settings=app.open_settings();settings._show('appearance');pump(.3)
  check('solid and builtin modes only',set(settings.skin_mode_buttons)=={'solid','builtin'} and not hasattr(settings,'custom_group') and not hasattr(settings,'_pick_background'))
  check('pure mode hides character thumbnails',settings.color_group.winfo_ismapped() and not settings.gallery.winfo_ismapped())
  settings._pick_accent('orange');pump();check('preview selection does not apply early',app.cfg['accent']=='green' and settings.color_preview.find_all())
  app.apply_preset(('sec',600));app.btn_pause.invoke();due=(app.engine.generation,app.engine.remaining())
  for key in ACCENT_ORDER:
   settings._pick_accent(key);start=time.perf_counter();settings.on_apply();elapsed=(time.perf_counter()-start)*1000;pump(.65)
   check(key+' solid color applies with preview',app.cfg['skin']=='solid' and theme.accent==ACCENTS[key] and not app.skin_renderer.has_picture and settings.color_group.winfo_ismapped() and not settings.gallery.winfo_ismapped())
   check(key+' swatches retain original colors',all(b.cget('background').lower()==ACCENTS[k].lower() for k,b in settings.color_buttons.items()))
   samples.append({'selection':'solid-'+key,'apply_ms':elapsed,**app._last_skin_fade_stats})
  ui.grab_window(u.GetAncestor(settings.winfo_id(),2),'v1711-settings-solid.png')
  settings.v['float_enabled'].set(True);app.cfg['float_enabled']=True;app.floating.apply();pump(.15);floating=app.floating.window;reference=floating._image.tobytes()
  for key in skins.SKIN_ORDER:
   settings._pick_skin(key);pump(.05);check(key+' gallery excludes solid swatches',settings.gallery.winfo_ismapped() and not settings.color_group.winfo_ismapped())
   start=time.perf_counter();settings.on_apply();elapsed=(time.perf_counter()-start)*1000;pump(.65)
   sample={'selection':key,'apply_ms':elapsed,**app._last_skin_fade_stats};samples.append(sample)
   check(key+' fade completes without overlay',sample['frames'][-1]==1 and len(sample['frames'])>=4 and all(x<=y for x,y in zip(sample['frames'],sample['frames'][1:])) and app._skin_fade is None and not app.skin_renderer.fade_surface.winfo_ismapped())
   check(key+' floating palette and artwork independent',floating._image.tobytes()==reference and floating.pause.cget('background')=='#FFF9EF' and floating.cancel.cget('foreground')=='#765338')
   check(key+' swatches stay fixed after skin apply',all(b.cget('background').lower()==ACCENTS[k].lower() for k,b in settings.color_buttons.items()))
  check('cat on right clear of labels and controls',floating._cat_box[0]>=round(150*floating.s) and floating._cat_box[3]<floating.pause.winfo_y() and floating._cat_art.getbbox() is not None)
  ui.grab_window(u.GetAncestor(floating.winfo_id(),2),'v1711-floating.png')
  check('timer and pause preserved',(app.engine.generation,app.engine.remaining())==due and app.engine.paused)
  check('compact window unchanged',size==(app.root.winfo_width(),app.root.winfo_height()))
  settings._pick_skin('solid');settings.on_apply();pump(.4);settings._pick_skin('pink');settings.destroy();app._settings_win=None;check('cancel retains applied solid mode',app.cfg['skin']=='solid')
  app.cfg['skin']='violet';app.apply_settings();app.action_widgets['play_sound'].invoke();app.mode_btns['interval'].invoke();pump(.5)
  from PIL import ImageChops
  print('fade input evidence:',app.action_var.get(),app.mode_var.get(),ImageChops.difference(app.skin_renderer.scene,app.skin_renderer._compose()).getbbox(),flush=True)
  check('selection and mode respond during fade',app.action_var.get()=='play_sound' and app.mode_var.get()=='interval' and ImageChops.difference(app.skin_renderer.scene,app.skin_renderer._compose()).getbbox() is None)
  app.action_widgets['message'].invoke();app.mode_btns['countdown'].invoke();pump(.1);ui.grab_window(u.GetAncestor(app.root.winfo_id(),2),'v1711-home-violet.png')
  check('no callbacks',not errors)
 finally:
  fade=getattr(app,'_skin_fade',None)
  if fade:fade.finish()
  app.floating.close();app.engine.stop();app.desktop.close();app.root.destroy()
(p/'tools/v1711-appearance-results.json').write_text(json.dumps({'checks':checks,'samples':samples,'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
print('Switch latency max:',max(s['apply_ms'] for s in samples))
