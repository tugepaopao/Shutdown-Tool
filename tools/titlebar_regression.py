import os,sys,time,tempfile,json,ctypes
from pathlib import Path
p=Path(__file__).resolve().parent.parent;sys.path[:0]=[str(p/'src'),str(p/'tools')]
from main import enable_dpi_awareness
enable_dpi_awareness()
from ui_main import App
from theme import theme,palette_for
import autostart,exe_test
App._init_tray=lambda s:None;autostart.set_enabled=lambda *a:True
checks=[];errors=[];times=[]
def check(name,value):
 checks.append([name,bool(value)]);print(('PASS ' if value else 'FAIL ')+name,flush=True);assert value,name
with tempfile.TemporaryDirectory(prefix='v174-titlebar-') as folder:
 os.environ['APPDATA']=folder;app=App({'given':True,'action':'message'});app.cfg['confirm_on_exit']=False
 app.root.report_callback_exception=lambda *v:errors.append(str(v[1]))
 def pump(t=.2):
  end=time.monotonic()+t
  while time.monotonic()<end:app.root.update();time.sleep(.005)
 u=ctypes.windll.user32;u.GetAncestor.restype=ctypes.c_void_p;u.GetAncestor.argtypes=[ctypes.c_void_p,ctypes.c_uint];u.GetWindowLongW.argtypes=[ctypes.c_void_p,ctypes.c_int]
 try:
  pump();hwnd=u.GetAncestor(app.root.winfo_id(),2)
  check('native caption removed',not u.GetWindowLongW(hwnd,-16)&0xC00000)
  check('native minimize and taskbar style retained',bool(u.GetWindowLongW(hwnd,-16)&0x20000))
  check('four controls in one titlebar',all(b.master is app.titlebar for b in (app.avatar_btn,app.pin_btn,app.minimize_btn,app.close_btn)))
  check('titlebar icons fit',all(b.winfo_width()>=b.winfo_reqwidth() for b in (app.avatar_btn,app.pin_btn,app.minimize_btn,app.close_btn)))
  app.pin_btn.invoke();pump();check('pin sets native topmost',bool(u.GetWindowLongW(hwnd,-20)&8) and app.cfg.get('main_topmost'))
  app.pin_btn.invoke();pump();check('unpin clears native topmost',not u.GetWindowLongW(hwnd,-20)&8 and not app.cfg.get('main_topmost'))
  app.minimize_btn.invoke();pump();check('custom minimize works',app.root.state()=='iconic');app.show_window();pump();check('restore retains custom caption',app.root.state()=='normal' and not u.GetWindowLongW(hwnd,-16)&0xC00000)
  for i in range(3):
   start=time.perf_counter();win=app.open_settings();times.append(round((time.perf_counter()-start)*1000,2));check('settings loads general only '+str(i),win._built_pages=={'general'});win.destroy();app._settings_win=None
  start=time.perf_counter();win=app.open_settings();times.append(round((time.perf_counter()-start)*1000,2));win._show('appearance');pump();check('appearance builds on first selection',win._built_pages=={'general','appearance'})
  page=win.pages['appearance'];win._show('general');win._show('appearance');pump();check('loaded page reused',win.pages['appearance'] is page)
  win._show('display');pump();win.v['language'].set('EN');win.on_apply();pump(.5);win._show('other');pump();check('late loaded page uses current language',win.day_box.cget('values')[0]=='Today')
  win.destroy();app._settings_win=None
  for key in ('blue','green','purple'):
   app.cfg['accent']=key;app.apply_settings();pump(.5);app.root.attributes('-topmost',True);pump();exe_test.grab_window(hwnd,'v174-theme-'+key+'.png');check(key+' tinted background',theme.c('bg')==palette_for(key)['bg'])
  check('theme background differences visible',len({palette_for(k)['bg'] for k in ('blue','green','purple')})==3)
  check('three time icons differ',len({bytes(__import__('PIL.ImageTk',fromlist=['getimage']).getimage(__import__('ui_compact').icon(app,k,23)).tobytes()) for k in ('sleep','hibernate','moon')})==3)
  app.cfg['float_docked']=True;app.cfg['float_enabled']=True;app.floating.apply();pump();f=app.floating.window;check('legacy docking setting ignored',f.winfo_height()==f.panel_height and not app.cfg.get('float_docked'))
  check('no callbacks',not errors)
 finally:app.floating.close();app.engine.stop();app.desktop.close();app.root.destroy()
(p/'tools/v174-titlebar-results.json').write_text(json.dumps(dict(checks=checks,settings_open_ms=times,errors=errors),ensure_ascii=False,indent=2),encoding='utf-8');print('settings_open_ms',times)
