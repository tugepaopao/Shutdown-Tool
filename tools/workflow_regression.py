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
 pump(.3);w=a.open_settings();pump(.2)
 from ui_floating import workareas
 check('settings fits current monitor work area',any(l<=w.winfo_rootx() and top<=w.winfo_rooty() and w.winfo_rootx()+w.winfo_width()<=right+2 and w.winfo_rooty()+w.winfo_height()<=bottom+2 for l,top,right,bottom in workareas(w)))
 from theme import theme
 from desktop_services import HotkeyManager,parse_hotkey
 import ctypes
 check('settings does not grab main-window input',a.root.grab_current() is None)
 w.v['toast_seconds'].set('27');check('modified label and save explanation',w.dirty and w.save_state.cget('text').startswith('已修改') and '保存' in w.save_note.cget('text'))
 for lang in ('CHS','CHT','EN'):
  a.cfg['language']=lang;a.apply_settings();pump(.2)
  for key,_,_ in PAGES:
   with patch('ui_pc_controls.WindowsControls',return_value=hardware):w._show(key);pump(.12)
   canvas=w._scroll_pages[key][0]
   check(lang+' '+key+' footer aligns with content',abs(w.footer.winfo_rootx()-canvas.winfo_rootx())<3 and abs(w.footer.winfo_width()-canvas.winfo_width())<4)
   check(lang+' '+key+' footer buttons fit',all(font.Font(root=b,font=b.cget('font')).measure(b.cget('text'))+20<=b.winfo_width() for b in (w.save_btn,w.discard_btn)))
   check(lang+' '+key+' footer remains visible',w.footer.winfo_rooty()+w.footer.winfo_height()<=w.winfo_rooty()+w.winfo_height())
  if factor==1.25:snap(w,'v2.0_底栏_'+lang+'.png')
 a.cfg['language']='CHS';a.apply_settings();w._show('general');pump(.2)
 if factor==1.25:snap(w,'v2.0_设置_已修改.png')
 # Main window can process real Tk pointer events with settings left open.
 a.root.lift();a.root.focus_force();pump(.15)
 button=list(a.preset_btns.values())[0];button.event_generate('<Enter>');button.event_generate('<ButtonPress-1>',x=10,y=10);button.event_generate('<ButtonRelease-1>',x=10,y=10);pump(.2)
 check('main preset click works while settings remains open',a.engine.is_running() and w.winfo_exists() and w.dirty and a.root.grab_current() is None)
 a.stop_timer();pump(.05)
 x,y=a.root.winfo_x(),a.root.winfo_y();a.root.geometry(f'+{x+12}+{y+8}');pump(.12);check('main window moves with settings open',a.root.winfo_x()!=x and w.winfo_exists())
 # Fourth binding is present, registered and dispatched without any active timer.
 w._show('general');check('floating shortcut field has default',w.v['hotkey_floating'].get()=='Ctrl+Alt+F')
 for kind,key in zip(('show','pause','resume','floating'),('F9','F10','F11','F12')):w.v['hotkey_'+kind].set('Ctrl+Shift+'+key)
 w.v['hotkeys_enabled'].set(True);check('save registers four custom shortcuts',w.on_apply() and set(a.desktop.hotkeys.mapping)=={'show','pause','resume','floating'})
 check('saved clean state is not falsely modified',not w.dirty and w.save_state.cget('text')=='未修改')
 w.v['toast_seconds'].set('28');a.cfg['float_enabled']=False;a.floating.apply();w.sync_external('float_enabled',False)
 generation=a.engine.generation
 def hotkey():
  ctypes.windll.user32.PostThreadMessageW(a.desktop.hotkeys.thread.native_id,0x0312,4,0);pump(.3)
 hotkey();check('registered floating shortcut opens idle floating window',a.cfg['float_enabled'] and a.floating.window is not None and a.floating.window.winfo_exists())
 check('shortcut preserves unrelated unsaved draft',w.dirty and w.v['toast_seconds'].get()=='28' and a.cfg['toast_seconds']==27 and w.v['float_enabled'].get() and w._baseline['float_enabled'])
 hotkey();check('registered floating shortcut closes floating window',not a.cfg['float_enabled'] and not w.v['float_enabled'].get())
 check('floating toggle leaves timer untouched',a.engine.generation==generation and not a.engine.is_running())
 w.discard();check('discard preserves externally updated floating state',not w.dirty and not a.cfg['float_enabled'] and not w.v['float_enabled'].get())
 oldmap=a.desktop.hotkeys.mapping.copy();w.v['hotkey_floating'].set(w.v['hotkey_show'].get())
 with patch.object(messagebox,'showerror',return_value='ok'):check('duplicate binding rejected without losing registered keys',not w.on_apply() and a.desktop.hotkeys.mapping==oldmap and w.dirty)
 w.discard();w.v['hotkey_floating'].set('invalid')
 with patch.object(messagebox,'showerror',return_value='ok'):check('invalid shortcut format rejected',not w.on_apply() and a.desktop.hotkeys.mapping==oldmap)
 w.discard();blocker=HotkeyManager(lambda kind:None)
 try:
  blocker.configure({'reserved':'Ctrl+Alt+Shift+F8'});w.v['hotkey_floating'].set('Ctrl+Alt+Shift+F8')
  with patch.object(messagebox,'showerror',return_value='ok'):check('occupied shortcut rolls back registration',not w.on_apply() and a.desktop.hotkeys.mapping==oldmap)
 finally:blocker.close()
 w.discard()
 with patch.object(a.cfg,'save',return_value=False),patch.object(messagebox,'showerror',return_value='ok'):
  a.toggle_floating();check('failed immediate floating save keeps UI and configuration',not a.cfg['float_enabled'] and not w.v['float_enabled'].get() and not w.dirty)
 w.v['toast_seconds'].set('29')
 with patch.object(messagebox,'askyesnocancel',return_value=None):w.request_close()
 check('continue editing leaves both windows usable',w.winfo_exists() and w.dirty and a.root.grab_current() is None)
 w._show('tasks');w.preset_menu(0);pump(.12);w._preset_popup.dismiss();pump(.08);check('closing nested menu does not relock main',a.root.grab_current() is None)
 w.discard();w._show('pc');check('PC footer labels immediate changes',w.save_state.cget('text')=='立即生效' and '立即生效' in w.save_note.cget('text'))
 w._show('hotkeys');pump(.2)
 if factor==1.25:snap(w,'v2.0_全局快捷键.png')
 # Legacy R10 files receive the fourth shortcut default; backups preserve its value.
 legacy=dict(DEFAULT_SETTINGS);legacy.pop('hotkey_floating',None)
 with tempfile.TemporaryDirectory() as folder:
  path=Path(folder)/'settings.json';path.write_text(json.dumps(legacy),encoding='utf-8')
  with patch('app_config.config_file',return_value=str(path)):config=Config()
  check('R10 configuration gains floating shortcut default',config.get('hotkey_floating')=='Ctrl+Alt+F')
  backup=Path(folder)/'backup.json';task_store.export_backup(a.cfg,backup);values,_,_=task_store.read_backup(backup);check('backup preserves custom floating shortcut',values['hotkey_floating']==a.cfg['hotkey_floating'])
 check('no callback exceptions',not errors or print(errors,flush=True))
 (p/'核验'/f'v200-workflow-{factor}.json').write_text(json.dumps(dict(checks=checks,errors=errors),ensure_ascii=False,indent=2),encoding='utf-8')
finally:
 a.engine.stop();a.automation.close();a.floating.close();a.desktop.close();a.root.destroy()
