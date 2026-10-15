import os,sys,tempfile,time,json,copy,datetime as dt,tkinter as tk,tkinter.font as font
from pathlib import Path
from unittest.mock import patch
p=Path(__file__).resolve().parent.parent;(p/'核验').mkdir(exist_ok=True);sys.path.insert(0,str(p/'src'));sys.stdout.reconfigure(encoding='utf-8');os.environ['APPDATA']=tempfile.mkdtemp(prefix='v200-features-')
from main import enable_dpi_awareness
enable_dpi_awareness();factor=float(sys.argv[1]) if len(sys.argv)>1 else 1.25
OriginalTk=tk.Tk
class Scaled(OriginalTk):
 def __init__(self,*a,**kw):super().__init__(*a,**kw);self.tk.call('tk','scaling',factor*96/72)
tk.Tk=Scaled
import autostart,actions,quick_presets,task_features,task_store,diagnostics
from ui_main import App
from ui_settings import SettingsWindow,PAGES
from ui_settings_controls import Switch,Expander
from ui_localize import walk,messagebox
from app_config import Config,DEFAULT_SETTINGS
from timer_engine import TimerEngine
from pc_controls import Monitor
from ui_restore import RestorePreview,differences
from PIL import ImageGrab
App._init_tray=lambda a:None;autostart.set_enabled=lambda *a:True;actions.perform=lambda *a,**kw:(_ for _ in ()).throw(AssertionError('Real actions forbidden'))
class Hardware:
 def __init__(self):self.writes=[]
 def monitors(self):return [Monitor('main',True,55,'ddc'),Monitor('sub',False,65,'ddc')]
 def audio(self):return dict(value=25,muted=False)
 def set_brightness(self,m,v):self.writes.append(('brightness',m.key,v))
 def set_volume(self,v):self.writes.append(('volume',v))
 def set_mute(self,v):self.writes.append(('mute',v))
hardware=Hardware();checks=[];errors=[]
def check(name,value):
 checks.append([name,bool(value)]);print(('PASS ' if value else 'FAIL ')+name,flush=True);assert value,name
def pump(t=.08):
 end=time.monotonic()+t
 while time.monotonic()<end:a.root.update();time.sleep(.003)
def snap(w,name):
 from capture_window import capture
 capture(w).save(p/'核验'/name)
a=App({'given':True,'action':'message'});a.root.report_callback_exception=lambda t,v,b:errors.append(str(v));a.cfg.update(dict(confirm_on_exit=False,cancel_at_10s=False,popup_at_10s=False,sound_at_10s=False,force_close_apps=False));a.cfg.save()
try:
 pump(.3)
 import ctypes
 from ctypes import wintypes as W
 from ui_window import prepare,show,activate_dialog
 u=ctypes.windll.user32
 u.GetAncestor.argtypes=[W.HWND,W.UINT];u.GetAncestor.restype=W.HWND
 u.GetWindowLongW.argtypes=[W.HWND,ctypes.c_int];u.GetWindowLongW.restype=ctypes.c_long
 def visible(w):
  h=u.GetAncestor(w.winfo_id(),2)
  return w.winfo_viewable() and getattr(w,'_main_opacity',255)==255 and not u.GetWindowLongW(h,-20)&0x80000
 for lang in ('CHS','CHT','EN'):
  a.cfg['language']=lang;a.apply_settings();pump(.1)
  w=a.open_settings();pump(.15)
  check(lang+' footer compressed to 60 logical pixels',abs(w.footer.winfo_height()-round(60*factor))<=1)
  check(lang+' no category tooltips',all(not hasattr(b,'_tooltip') for b in w.nav.buttons.values()))
  check(lang+' settings body font reduced only locally',font.Font(font=w.font()).actual('size')==font.Font(font=__import__('theme').theme.font()).actual('size')-1)
  w.nav.buttons['general'].event_generate('<Enter>');pump(.7)
  check(lang+' hover does not create tooltip',not any(isinstance(x,tk.Toplevel) and x is not w for x in walk(w)))
  w.v['toast_seconds'].set('27');pump(.05)
  for name,opener in [('settings',a.open_settings),('tasks',a.open_task_center),('log',a.open_log)]:
   dialog=opener();pump(.15)
   for i in range(6):
    same=opener();pump(.04);check(lang+' '+name+' repeat '+str(i),same is dialog and visible(dialog))
   dialog.withdraw();pump(.05);same=opener();pump(.15)
   check(lang+' '+name+' restores hidden instance',same is dialog and visible(dialog))
   u.ShowWindow.argtypes=[W.HWND,ctypes.c_int];u.ShowWindow(u.GetAncestor(dialog.winfo_id(),2),6);pump(.05);same=opener();pump(.15)
   check(lang+' '+name+' restores minimized instance',same is dialog and visible(dialog))
   if name=='settings':check(lang+' reopen retains unsaved draft',dialog.v['toast_seconds'].get()=='27' and dialog.dirty)
   if name=='tasks':
    editor=tk.Toplevel(dialog);prepare(editor);editor.title('Modal test');tk.Label(editor,text='Pending editor').pack(padx=20,pady=20);show(editor);editor.grab_set();pump(.1)
    opener();pump(.1);check(lang+' existing modal editor retains grab',a.root.grab_current() is editor);editor.destroy();pump(.05)
   dialog.destroy();pump(.06)
   fresh=opener();pump(.15);check(lang+' '+name+' reopens after close',fresh is not dialog and visible(fresh));fresh.destroy();pump(.05)
  # Long names and timestamps must never paint over the surrounding fixed border.
  job=task_store.normalize(dict(mode='calendar',action='message',name='测试长任务名称与边界保留 '+('Long task name '*12),at='2026-10-20 22:00:00',repeat='once',enabled=False));job['id']=301;a.automation.jobs=[job]
  center=a.open_task_center('advanced');pump(.2);panel=center.panels['advanced'];tv=panel.tv;border=panel.table_border
  check(lang+' long table remains inside window',border.winfo_rootx()>center.winfo_rootx() and border.winfo_rootx()+border.winfo_width()<center.winfo_rootx()+center.winfo_width())
  for frac in (0,.5,1):
   tv.xview_moveto(frac);pump(.08)
   check(lang+' border margins survive horizontal scroll '+str(frac),tv.winfo_rootx()>border.winfo_rootx() and tv.winfo_rootx()+tv.winfo_width()<border.winfo_rootx()+border.winfo_width())
   center.lift();center.focus_force();pump(.06)
   x=border.winfo_rootx();y=border.winfo_rooty()+border.winfo_height()//2;right=x+border.winfo_width()-1
   from capture_window import capture
   surface=capture(center);shot=surface.crop((x-center.winfo_rootx(),y-center.winfo_rooty(),right+1-center.winfo_rootx(),y+1-center.winfo_rooty()))
   check(lang+' both table edges painted '+str(frac),shot.getpixel((0,0))[:3]==(185,171,225) and shot.getpixel((shot.width-1,0))[:3]==(185,171,225))
  tv.xview_moveto(0);pump(.1)
  if factor==1.25 and lang=='CHS':snap(center,'v2.0_long_task_borders.png')
  center.destroy();a.automation.jobs=[];pump(.05)
 check('no callback errors',not errors or print(errors))
 (p/'核验'/f'v200-regression-{factor}.json').write_text(json.dumps(dict(checks=checks,errors=errors),ensure_ascii=False,indent=2),encoding='utf-8')
finally:
 a.engine.stop();a.automation.close();a.floating.close();a.desktop.close();a.root.destroy()



