import sys,os,time,tempfile,json,copy,ctypes,traceback
from pathlib import Path
p=Path(__file__).resolve().parent.parent;sys.path[:0]=[str(p/'src'),str(p/'tools')]
from main import enable_dpi_awareness
enable_dpi_awareness()
from ui_main import App
from theme import theme,ACCENT_ORDER
import skins,autostart,exe_test as ui
from app_config import config_file
from ui_dialogs import ConfirmActionDialog
App._init_tray=lambda s:None;autostart.set_enabled=lambda *a:True
checks=[];errors=[];timings=[]
u=ctypes.windll.user32;u.GetAncestor.argtypes=[ctypes.c_void_p,ctypes.c_uint];u.GetAncestor.restype=ctypes.c_void_p

def check(n,v):checks.append([n,bool(v)]);print(('PASS ' if v else 'FAIL ')+n,flush=True);assert v,n
with tempfile.TemporaryDirectory(prefix='v1711-chrome-') as folder:
 os.environ['APPDATA']=folder;app=App({'given':True,'action':'message'});app.cfg['confirm_on_exit']=False
 app.root.report_callback_exception=lambda c,e,t:(errors.append(str(e)),traceback.print_exception(c,e,t))
 def pump(t=.15):
  end=time.monotonic()+t
  while time.monotonic()<end:app.root.update();time.sleep(.003)
 def chrome(w):
  hwnd=u.GetAncestor(w.winfo_id(),2)
  return not u.GetWindowLongW(ctypes.c_void_p(hwnd),-16)&0xC00000 and w._dialog_caption.cget('bg')==theme.c('bg') and w._dialog_title.cget('text')==w.title()
 try:
  pump(.4);settings=app.open_settings();settings._show('appearance');pump(.3)
  check('settings caption integrated',chrome(settings));shape=(settings.winfo_width(),settings.winfo_height());pack_calls=[]
  for name in ('gallery','color_group'):
   widget=getattr(settings,name);original=widget.pack_forget
   def tracked(fn=original,n=name):pack_calls.append(n);return fn()
   widget.pack_forget=tracked
  app.cfg.save();saved=Path(config_file()).read_bytes();cfg=copy.deepcopy(app.cfg.data);canvas_items=settings.color_preview.find_all();view=settings._scroll_pages['appearance'][0].yview()
  for key in ACCENT_ORDER:
   begin=time.perf_counter();settings._pick_accent(key);pump(.05);timings.append((key,(time.perf_counter()-begin)*1000-50))
   check(key+' pending color does not hide/repack',not pack_calls)
   check(key+' preview items and geometry stable',settings.color_preview.find_all()==canvas_items and (settings.winfo_width(),settings.winfo_height())==shape and settings._scroll_pages['appearance'][0].yview()==view)
  check('pending color never applies or saves',app.cfg.data==cfg and Path(config_file()).read_bytes()==saved)
  ui.grab_window(u.GetAncestor(settings.winfo_id(),2),'v1711-settings-solid.png')
  settings._pick_skin('violet');pump(.1);pack_calls.clear();view=settings._scroll_pages['appearance'][0].yview()
  for key in skins.SKIN_ORDER:
   settings._pick_skin(key);pump(.05)
   check(key+' pending skin keeps gallery mapped',not pack_calls and settings.gallery.winfo_ismapped() and settings._scroll_pages['appearance'][0].yview()==view)
  check('pending skins never apply or save',app.cfg.data==cfg and Path(config_file()).read_bytes()==saved)
  settings.on_apply();pump(.5);check('apply selected skin and caption',app.cfg['skin']=='red' and chrome(settings))
  settings.grab_release();about=app.open_about();pump(.2);check('about caption integrated',chrome(about));about.grab_release()
  app.apply_preset(('sec',600));app.btn_pause.invoke();due=(app.engine.generation,app.engine.remaining())
  for key in ACCENT_ORDER:
   settings._pick_accent(key);settings.on_apply();pump(.5)
   check(key+' open dialog captions follow applied color',chrome(settings) and chrome(about) and about._dialog_icon_stamp[0]==theme.accent)
  for key in skins.SKIN_ORDER:
   settings._pick_skin(key);settings.on_apply();pump(.5)
   check(key+' open dialog captions follow applied skin',chrome(settings) and chrome(about))
  check('caption updates preserve paused timer',(app.engine.generation,app.engine.remaining())==due and app.engine.paused)
  app.cfg['language']='EN';app.apply_settings();pump(.5);check('captions follow translated native titles',chrome(settings) and chrome(about) and about.title()=='About')
  app.cfg['language']='CHS';app.cfg['skin']='solid';app.cfg['accent']='orange';app.apply_settings();pump(.5)
  ui.grab_window(u.GetAncestor(about.winfo_id(),2),'v1711-about.png');about._dialog_close.invoke();pump(.1);check('about close button respects protocol',not about.winfo_exists())
  for name,open_window in [('parameters',app.open_params),('tasks',app.open_queue),('log',app.open_log)]:
   win=open_window();pump(.25);check(name+' caption integrated',chrome(win));ui.grab_window(u.GetAncestor(win.winfo_id(),2),'v1711-'+name+'.png');win._dialog_close.invoke();pump(.1);check(name+' caption close works',not win.winfo_exists())
  confirm=ConfirmActionDialog(app.root,app.T,'Safe caption test');pump(.15);confirm._dialog_close.invoke();check('confirmation close remains cancellation',confirm.result is False and not confirm.winfo_exists())
  old=(settings.winfo_x(),settings.winfo_y());title=settings._dialog_title;x,y=title.winfo_rootx()+20,title.winfo_rooty()+12
  title.event_generate('<ButtonPress-1>',x=20,y=12,rootx=x,rooty=y);title.event_generate('<B1-Motion>',x=20,y=12,rootx=x+50,rooty=y+25);pump(.1);title.event_generate('<ButtonRelease-1>',rootx=x+50,rooty=y+25);pump(.1)
  check('dialog title drag moves native window',(settings.winfo_x(),settings.winfo_y())==(old[0]+50,old[1]+25))
  old=(settings.winfo_width(),settings.winfo_height());x,y=settings.winfo_rootx()+old[0]-2,settings.winfo_rooty()+old[1]//2
  settings.event_generate('<ButtonPress-1>',rootx=x,rooty=y);settings.event_generate('<B1-Motion>',rootx=x+60,rooty=y);pump(.1);settings.event_generate('<ButtonRelease-1>',rootx=x+60,rooty=y);pump(.1)
  check('settings ignore edge resize',settings.winfo_width()==old[0] and settings.winfo_height()==old[1] and settings.resizable()==(0,0))
  settings.geometry(f'{shape[0]}x{shape[1]}');pump(.2);ui.grab_window(u.GetAncestor(settings.winfo_id(),2),'v1711-settings-caption.png')
  settings._dialog_close.invoke();pump(.1);check('settings close discards pending selection',not settings.winfo_exists());check('no Tcl callbacks',not errors)
 finally:
  app.engine.stop();app.floating.close();app.desktop.close();app.root.destroy()
(p/'tools/v1711-chrome-results.json').write_text(json.dumps({'checks':checks,'errors':errors,'pending_selection_ms':timings},ensure_ascii=False,indent=2),encoding='utf-8')
