"""Public edition GUI/audio regression; isolated settings, no power actions."""
import os,sys,json,time,tempfile,wave
from pathlib import Path
from unittest.mock import patch
p=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(p/'src'))
from main import enable_dpi_awareness
enable_dpi_awareness()
from ui_main import App
from ui_sound import SoundDialog
from ui_tasks import TaskEditor,ACTION_NAMES
from sound_library import resolve
from app_config import DEFAULT_SETTINGS
from PIL import ImageGrab
import autostart
checks=[]
def check(name,value):
    checks.append([name,bool(value)])
    print(('PASS ' if value else 'FAIL ')+name,flush=True)
    assert value,name
with tempfile.TemporaryDirectory(prefix='shutdown-public-test-') as folder:
    os.environ['APPDATA']=folder
    App._init_tray=lambda self:None
    autostart.set_enabled=lambda *args:True
    app=App({'given':True,'action':'message'})
    app.cfg['confirm_on_exit']=False
    errors=[]
    app.root.report_callback_exception=lambda cls,value,tb:errors.append(str(value))
    def pump():
        for _ in range(12):app.root.update();time.sleep(.01)
    def shot(win,name):
        win.lift();win.attributes('-topmost',True);pump()
        dest=p/'docs/images'/name;dest.parent.mkdir(parents=True,exist_ok=True)
        ImageGrab.grab(bbox=(win.winfo_rootx(),win.winfo_rooty(),win.winfo_rootx()+win.winfo_width(),win.winfo_rooty()+win.winfo_height()),all_screens=True).save(dest)
    try:
        check('no audio asset directory',not (p/'assets/audio').exists())
        check('no default music',DEFAULT_SETTINGS['sound_file']=='')
        check('legacy builtin does not resolve to missing asset',resolve('builtin:old-track')=='')
        check('custom path unchanged',resolve('C:/audio/test.wav')=='C:/audio/test.wav')
        shot(app.root,'main.png')
        dlg=SoundDialog(app);pump()
        check('sound picker has no builtin selection',not hasattr(dlg,'source'))
        shot(dlg,'sound-picker.png')
        dlg.save();check('empty audio is not accepted',dlg.winfo_exists() and dlg.result is None)
        audio=Path(folder)/'test.wav'
        with wave.open(str(audio),'wb') as output:output.setnchannels(1);output.setsampwidth(2);output.setframerate(8000);output.writeframes(b'\0'*1600)
        dlg.path.set(str(audio));dlg.save()
        check('custom audio file accepted',dlg.result==str(audio))
        app.cfg['sound_file']=str(audio)
        check('selected audio validates',app._validate_action('play_sound'))
        app.cfg['sound_file']=''
        with patch('ui_main.messagebox.showinfo') as notice:
            check('missing audio cannot execute',not app._validate_action('play_sound') and notice.called)
        editor=TaskEditor(app,{'action':'play_sound','mode':'countdown','seconds':30,'sound_file':''})
        try:editor.collect();blank_accepted=True
        except ValueError:blank_accepted=False
        check('sound task requires parameter',not blank_accepted)
        editor.v['parameter'].set(str(audio));check('sound task keeps selected file',editor.collect()['sound_file']==str(audio));editor.destroy()
        center=app.open_queue();pump();shot(center,'task-manager.png');center.destroy()
        settings=app.open_settings();settings._show('pc');pump();shot(settings,'pc-controls.png');settings.destroy();app._settings_win=None
        check('no Tk callback errors',not errors)
        check('no timers/tasks started',not app.engine.is_running() and not app.task_queue)
    finally:
        app.engine.stop();app.desktop.close();app.root.destroy()
(p/'tools/public-results.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print('Public checks passed:',len(checks))
