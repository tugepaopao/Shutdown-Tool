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
 import wave,app_config,single_instance,i18n
 from sound_library import resolve
 from ui_sound import SoundDialog
 from ui_tasks import TaskEditor
 from capture_window import capture
 check('public app identity unchanged',app_config.APP_ID=='HaozaiziShutdownTool' and app_config.RUN_VALUE_NAME=='豪崽子の自动关机工具')
 check('public single instance identity unchanged',single_instance._GUID=='8F3C1A72-5B4E-4C9D-9E21-7A6B0C5D3F10' and 'Personal' not in single_instance.MUTEX_NAME)
 check('public product version and name',i18n.VERSION=='2.0' and a.root.title()=='定时关机工具')
 check('no bundled audio',not (p/'assets/audio').exists() and not any(f.suffix.lower() in ('.mp3','.wav','.ogg','.flac','.m4a','.wma') for f in (p/'assets').rglob('*')))
 check('no default music',DEFAULT_SETTINGS['sound_file']=='')
 check('legacy builtin tokens disabled',resolve('builtin:old-track')=='')
 check('custom audio path preserved',resolve('C:/audio/track.wav')=='C:/audio/track.wav')
 dlg=SoundDialog(a);pump(.1);check('no builtin music control',not hasattr(dlg,'source'))
 dlg.save();check('empty music selection rejected',dlg.winfo_exists() and dlg.result is None)
 dest=Path(os.environ['APPDATA'])/'test.wav'
 with wave.open(str(dest),'wb') as stream:stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(8000);stream.writeframes(b'\0'*1600)
 dlg.path.set(str(dest));dlg.save();check('chosen local audio accepted',dlg.result==str(dest))
 a.cfg['sound_file']=str(dest);check('custom music task validates',a._validate_action('play_sound'));a.cfg['sound_file']=''
 with patch('ui_main.messagebox.showinfo') as notice:check('missing music cannot run',not a._validate_action('play_sound') and notice.called)
 editor=TaskEditor(a,dict(action='play_sound',mode='countdown',seconds=30,sound_file=''))
 try:editor.collect();accepted=True
 except ValueError:accepted=False
 check('sound task no longer substitutes builtin music',not accepted and not hasattr(editor,'builtin'))
 editor.v['parameter'].set(str(dest));check('task editor keeps local sound',editor.collect()['sound_file']==str(dest));editor.destroy()
 # Read an old public configuration without writing its real data directory.
 old=dict(DEFAULT_SETTINGS,skin='blue',resume_timer=False,sound_file='builtin:old-track',templates=[dict(id=9,name='Preserved template',action='message',mode='countdown',seconds=60)])
 for key in ('quick_presets','resume_strategy','hotkey_floating'):old.pop(key,None)
 path=Path(os.environ['APPDATA'])/'legacy.json';path.write_text(json.dumps(old),encoding='utf-8')
 with patch('app_config.config_file',return_value=str(path)):legacy=Config()
 check('legacy configuration preserves named templates',legacy['templates'][0]['name']=='Preserved template')
 check('legacy configuration gains six presets',len(quick_presets.get(legacy))==6)
 check('legacy configuration migrates to violet appearance',legacy['skin']=='violet' and legacy['accent']=='purple')
 check('legacy restore preference preserved',legacy['resume_strategy']=='off')
 check('legacy gains floating shortcut',legacy['hotkey_floating']=='Ctrl+Alt+F')
 for skin in ('solid','blue','plum','pink','green','orange','teal','red','custom'):
  old['skin']=skin;path.write_text(json.dumps(old),encoding='utf-8')
  with patch('app_config.config_file',return_value=str(path)):migrated=Config()
  check('old skin '+skin+' retains data',migrated['templates'][0]['id']==9 and migrated['skin']=='violet')
 from config_backups import portable
 archive=Path(os.environ['APPDATA'])/'old-backup.json';archive.write_text(json.dumps(portable(old)),encoding='utf-8')
 values,templates,jobs=task_store.read_backup(archive);check('old public backup can still be imported',templates[0]['name']=='Preserved template')

 a.cfg['language']='CHS';a.apply_settings();pump(.1)
 w=a.open_settings();pump(.15)
 for key,name in [('general','settings.png'),('tasks','presets.png'),('hotkeys','hotkeys.png'),('pc','pc-controls.png')]:
  with patch('ui_pc_controls.WindowsControls',return_value=hardware):w._show(key);pump(.15)
  capture(w).save(p/'docs/images'/name)
 w.destroy();pump(.1)
 task_features.enqueue(a,dict(mode='countdown',action='message',seconds=600,name='消息提醒'),start=True)
 task_features.enqueue(a,dict(mode='countdown',action='message',seconds=900,name='休息提醒'))
 task_features.enqueue(a,dict(mode='countdown',action='lock',seconds=1800,name='锁定电脑'))
 center=a.open_task_center();pump(.15);capture(center).save(p/'docs/images/task-center.png');center.destroy();pump(.1)
 __import__('ui_summary').refresh(a);pump(.1);capture(a.root).save(p/'docs/images/main.png')
 a.cfg['float_enabled']=True;a.floating.apply();pump(.2);a.floating.window._image.save(p/'docs/images/floating-countdown.png');a.cfg['float_enabled']=False;a.floating.apply()
 from ui_reminder import FadeMessageBox
 preview=FadeMessageBox(a.root,'提醒预览','这是预览，不会执行操作或改变当前计时。',seconds=30,button_text='取消操作',on_button=lambda:None);pump(.1);preview._image.save(p/'docs/images/reminder.png');preview.close();pump(.2)
 check('reminder preview preserves active timer',a.engine.is_running() and len(a.task_queue)==3)
 check('no callback exceptions',not errors or print(errors))
 (p/'核验/public-results.json').write_text(json.dumps(dict(checks=checks,errors=errors),ensure_ascii=False,indent=2),encoding='utf-8')
finally:
 a.engine.stop();a.automation.close();a.floating.close();a.desktop.close();a.root.destroy()

