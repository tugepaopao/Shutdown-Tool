import os,sys,time,tempfile,json,ctypes
from pathlib import Path
p=Path(__file__).resolve().parent.parent;sys.path[:0]=[str(p/'src'),str(p/'tools')]
from main import enable_dpi_awareness
enable_dpi_awareness()
from ui_main import App
from app_config import Config,config_file,DEFAULT_SETTINGS
import autostart,ui_window,ui_floating,skins,exe_test as ui
App._init_tray=lambda s:None;autostart.set_enabled=lambda *a:True
checks=[];errors=[];reveals=[];native=ui_window._main_opacity
u=ctypes.windll.user32;u.GetAncestor.argtypes=[ctypes.c_void_p,ctypes.c_uint];u.GetAncestor.restype=ctypes.c_void_p

def check(n,v):
 checks.append([n,bool(v)]);print(('PASS ' if v else 'FAIL ')+n,flush=True);assert v,n

def opacity(window,alpha):
 if alpha==255:
  renderer=getattr(window,'_skin_renderer',None)
  reveals.append({'ready':getattr(window,'_main_ready',False),'renderer':bool(renderer),'scene':bool(renderer and renderer.scene is not None),'key':renderer.key if renderer else None})
 return native(window,alpha)
ui_window._main_opacity=opacity
check('fresh configuration disables floating countdown',DEFAULT_SETTINGS['float_enabled'] is False)
for key in ('violet','red','solid'):
 with tempfile.TemporaryDirectory(prefix='v1711-start-') as folder:
  os.environ['APPDATA']=folder;c=Config();c.data.update(skin=key,action='message',confirm_on_exit=False);c.save();reveals.clear()
  app=App({'given':True,'action':'message'});app.root.report_callback_exception=lambda c,e,t:errors.append(str(e))
  def pump(t=.2):
   until=time.monotonic()+t
   while time.monotonic()<until:app.root.update();time.sleep(.004)
  try:
   pump(.3);check(key+' first reveal uses completed saved skin',bool(reveals) and all(item['ready'] and item['renderer'] and item['scene'] and item['key']==key for item in reveals))
   check(key+' floating remains absent until enabled',app.floating.window is None)
   if key!='violet':continue
   ui.grab_window(u.GetAncestor(app.root.winfo_id(),2),'v1711-startup.png')
   settings=app.open_settings();pump(.15);shape=(settings.winfo_width(),settings.winfo_height());check('settings has fixed constraints',settings.resizable()==(0,0) and settings.minsize()==settings.maxsize())
   x,y=settings.winfo_rootx()+shape[0]-2,settings.winfo_rooty()+shape[1]//2
   settings.event_generate('<ButtonPress-1>',rootx=x,rooty=y);settings.event_generate('<B1-Motion>',rootx=x+100,rooty=y);settings.event_generate('<ButtonRelease-1>',rootx=x+100,rooty=y);pump(.1)
   check('settings ignores resize edge gesture',(settings.winfo_width(),settings.winfo_height())==shape)
   for page in settings._builders:
    settings._show(page);pump(.1);check(page+' fixed page viewport stable',(settings.winfo_width(),settings.winfo_height())==shape)
   settings._show('appearance');pump(.1);ui.grab_window(u.GetAncestor(settings.winfo_id(),2),'v1711-settings-fixed.png');settings.destroy()
   app.cfg['float_enabled']=True;app.floating.apply();pump(.2);f=app.floating.window
   center=(app.root.winfo_rootx()+app.root.winfo_width()//2,app.root.winfo_rooty()+app.root.winfo_height()//2);area=f.area(*center);margin=round(16*f.s)
   check('first enabled countdown occupies upper right',f.position==(area[2]-f.panel_width-margin,area[1]+margin))
   hwnd=u.GetAncestor(f.winfo_id(),2);u.GetWindowLongW.argtypes=[ctypes.c_void_p,ctypes.c_int];ex=u.GetWindowLongW(hwnd,-20);check('floating stays off taskbar',bool(ex&0x80) and not ex&0x40000)
   ui.grab_window(hwnd,'v1711-floating.png')
   custom=(area[0]+70,area[1]+85);f.move(*custom);app.cfg.update(dict(float_positioned=True,float_x=custom[0],float_y=custom[1]));app.cfg['float_enabled']=False;app.floating.apply();app.cfg['float_enabled']=True;app.floating.apply();pump(.15)
   check('explicitly positioned countdown remembers placement',app.floating.window.position==custom)
   app.root.withdraw();pump(.1);app.show_window();pump(.2);check('restore also reveals completed skin',all(item['scene'] and item['key']=='violet' for item in reveals))
  finally:
   app.floating.close();app.desktop.close()
   for job in app.root.tk.splitlist(app.root.tk.call('after','info')):app.root.after_cancel(job)
   app.root.destroy()
check('no Tk callback errors',not errors)
(p/'tools/v1711-startup-results.json').write_text(json.dumps({'checks':checks,'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
