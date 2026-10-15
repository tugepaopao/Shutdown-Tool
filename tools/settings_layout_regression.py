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
 pump(.3);w=a.open_settings();pump(.25);w.v['toast_seconds'].set('27')
 from ui_settings import NAV_LABELS
 violations=[]
 for lang in ('CHS','CHT','EN'):
  a.cfg['language']=lang;a.apply_settings();pump(.15)
  fixed=(w.winfo_width(),w.winfo_height());footer=None
  check(lang+' exact compact size',fixed==w._compact_size)
  print(lang,'size',fixed,'nav',w.nav.winfo_width(),flush=True)
  for key,_,_ in PAGES:
   with patch('ui_pc_controls.WindowsControls',return_value=hardware):w._show(key);pump(.2)
   canvas,pad,scroll,item=w._scroll_pages[key]
   check(lang+' '+key+' stable window',fixed==(w.winfo_width(),w.winfo_height()))
   bounds=(w.footer.winfo_y(),w.footer.winfo_height())
   if footer is None:footer=bounds
   check(lang+' '+key+' fixed footer',bounds==footer and w.footer.winfo_rooty()+w.footer.winfo_height()<=w.winfo_rooty()+w.winfo_height())
   check(lang+' '+key+' footer matches content',abs(w.footer.winfo_width()-canvas.winfo_width())<=3)
   for b in (w.save_btn,w.discard_btn,*w.nav.buttons.values()):
    image_width=b.tk.call('image','width',b.cget('image')) if b.cget('image') else 0
    needed=font.Font(root=b,font=b.cget('font')).measure(b.cget('text'))+int(image_width)+10
    if needed>b.winfo_width():violations.append((lang,key,'button',b.cget('text'),needed,b.winfo_width()))
   for child in walk(pad):
    if not child.winfo_ismapped():continue
    if isinstance(child,(tk.Label,tk.Canvas,tk.Button)):
     if child.winfo_rootx()<canvas.winfo_rootx()-2 or child.winfo_rootx()+child.winfo_width()>canvas.winfo_rootx()+canvas.winfo_width()+2:
      violations.append((lang,key,'horizontal',str(child),child.winfo_width()))
   if key=='tasks':check(lang+' preset days translate',tuple(w.preset_day.cget('values'))==w._preset_days())
   if key=='hotkeys':
    recorder=w.hotkey_panel.recorders['floating'];w.v['hotkey_floating'].set('Ctrl+Alt+Shift+F12');pump(.05)
    check(lang+' four-key combination fits',recorder.bbox('all')[2]<=recorder.winfo_width())
   check(lang+' '+key+' save status fits',w.save_note.winfo_height()>=w.save_note.winfo_reqheight() and w.save_state.winfo_width()>=w.save_state.winfo_reqwidth())
   old=(w.footer.winfo_rooty(),w.nav.winfo_rooty(),w.winfo_height());canvas.yview_moveto(1);pump(.04)
   check(lang+' '+key+' scroll affects content only',old==(w.footer.winfo_rooty(),w.nav.winfo_rooty(),w.winfo_height()))
   canvas.yview_moveto(0);pump(.05)
   if factor==1.25 and lang in ('CHS','EN'):snap(w,'v2.0_'+lang+'_'+key+'.png')
  check(lang+' short navigation names',[b.cget('text') for b in w.nav.buttons.values()]==list(NAV_LABELS[lang]))
 print('VIOLATIONS',json.dumps(violations,ensure_ascii=False),flush=True)
 check('buttons and page controls fit horizontally',not violations)
 check('no callback errors',not errors or print(errors))
 (p/'核验'/f'v200-layout-{factor}.json').write_text(json.dumps(dict(checks=checks,errors=errors,violations=violations),ensure_ascii=False,indent=2),encoding='utf-8')
finally:
 a.engine.stop();a.automation.close();a.floating.close();a.desktop.close();a.root.destroy()
