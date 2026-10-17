"""Reference layout, rounded fields, Chinese-only migration and editor behavior."""
import os,sys,tempfile,time,json,datetime as dt,copy
from pathlib import Path
from unittest.mock import patch
p=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(p/'src'));sys.stdout.reconfigure(encoding='utf-8')
temp=tempfile.TemporaryDirectory(prefix='shutdown-v207-');os.environ['APPDATA']=temp.name
from main import enable_dpi_awareness
enable_dpi_awareness()
import actions,autostart
from ui_main import App
from ui_tasks import TaskEditor
from task_store import normalize,export_backup,read_backup
from app_config import Config,config_file
from i18n import Texts
from capture_window import capture
App._init_tray=lambda a:None;autostart.set_enabled=lambda *a:True
actions.perform=lambda *a,**k:(_ for _ in ()).throw(AssertionError('System action forbidden'))
a=App({'given':True,'action':'message'});a.cfg.update(dict(confirm_on_exit=False,autostart=False))
errors=[];checks=[];a.root.report_callback_exception=lambda t,v,b:errors.append(str(v));out=p/'核验/v207';out.mkdir(parents=True,exist_ok=True)
def pump(seconds=.10):
    end=time.perf_counter()+seconds
    while time.perf_counter()<end:a.root.update();time.sleep(.003)
def check(name,ok):
    checks.append((name,bool(ok)));print(('PASS ' if ok else 'FAIL ')+name,flush=True);assert ok,name
try:
    pump();future=(dt.date.today()+dt.timedelta(days=1)).isoformat()
    task=normalize(dict(name='资料备份',action='run_program',program_path='C:/Windows/System32/notepad.exe',mode='calendar',at=future+'T22:00:00',repeat='custom',weekdays=[0,2,4],exception_dates=['2026-10-21','2026-10-28']))
    e=TaskEditor(a,task,modes=('calendar','download','network','combined','chain'));pump();v=e.advanced_layout
    check('reference window uses 600 DIP width',abs(e.winfo_width()-round(600*v.s))<3)
    check('advanced editor values preserved',e.collect()['weekdays']==[0,2,4] and e.collect()['program_path']==task['program_path'])
    check('calendar weekday columns follow reference',v.segment.winfo_rootx()==v.dayrow.winfo_rootx()==e.rows['clock'].winfo_rootx())
    check('date fields stay narrow',v.inputs['date'].winfo_width()<v.calendar.winfo_width()*.5)
    check('end date disabled initially',v.inputs['end_date'].disabled)
    v.end_enabled.set(True);v.end_changed();e.v['end_date'].set('2027-12-31');check('end switch enables date',e.collect()['end_date']=='2027-12-31')
    v.end_enabled.set(False);v.end_changed();check('end switch removes date','end_date' not in e.collect())
    v.toggle_day(1);check('weekday selection saved',e.collect()['weekdays']==[0,1,2,4]);v.toggle_day(1)
    check('footer stays inside client area',v.footer.winfo_y()+v.footer.winfo_height()<=e.winfo_height())
    capture(e).save(out/'advanced-editor.png')
    v.policy.set('run');pump();check('legacy run policy stays inside card',v.run_radio.winfo_rootx()+v.run_radio.winfo_width()<=v.missed.winfo_rootx()+v.missed.winfo_width());v.policy.set('skip')
    e.after(80,lambda:next(w for w in e.winfo_children() if getattr(w,'title',lambda:'' )()=='选择日期').destroy())
    old=e.v['date'].get();v.date_picker(e.v['date']);pump();check('date cancellation keeps value and restores modal',e.v['date'].get()==old and e.grab_current()==e)
    def parameter_dialog(save=False):
        win=next(w for w in e.winfo_children() if getattr(w,'title',lambda:'')()=='操作参数')
        e.v['parameter'].set('changed.exe');win.saved=save;win.destroy()
    old_parameter=e.v['parameter'].get();e.after(80,parameter_dialog);v.parameters();pump()
    check('parameter cancel preserves value and modal',e.v['parameter'].get()==old_parameter and e.grab_current()==e)
    e.after(80,lambda:parameter_dialog(True));v.parameters();pump()
    check('parameter confirmation updates task',e.collect()['program_path']=='changed.exe');e.v['parameter'].set(old_parameter)
    e.mode.current(2);e.update_fields();pump();check('network mode parameters remain editable',e.collect()['mode']=='network' and v.condition_rows['threshold_kib'].winfo_viewable())
    e.mode.current(0);e.update_fields();pump();check('mode switch keeps window dimensions',e.winfo_width()==e._compact_size[0]);e.destroy();pump()
    for mode in ('countdown','datetime','interval'):
        sample=dict(name='休息提醒',action='message',message_text='休息一下',mode=mode,seconds=900,weekday=1,hour=14,minute=30,second=0)
        e=TaskEditor(a,sample);pump();check(mode+' uses rounded editor and roundtrips',e.collect()['mode']==mode and hasattr(e.advanced_layout,'name_input'))
        capture(e).save(out/(mode+'-editor.png'));e.destroy();pump()
    center=a.open_task_center('advanced');pump();cards=center.panels['advanced'].cards
    check('placeholder never becomes query',not cards.query.get() and cards.search.display.get()=='搜索名称')
    cards.search.focus_set();pump();check('placeholder clears on focus',cards.search.display.get()=='')
    cards.search.entry.insert(0,'测试');pump();check('native search input updates query',cards.query.get()=='测试')
    cards.query.set('');cards.canvas.focus_set();pump();check('placeholder returns on blur',cards.search.display.get()=='搜索名称')
    entry=cards.search.entry;check('placeholder entry fits rounded boundary',entry.winfo_x()>0 and entry.winfo_x()+entry.winfo_width()<cards.search.winfo_width() and entry.winfo_y()>=0)
    capture(center).save(out/'advanced-search.png')
    center.select_tab('templates');center.lift();center.focus_force();pump();cards=center.panels['templates'].cards
    check('template filter inside content card',str(cards.filters.pack_info()['in'])==str(cards.card))
    check('template tabs are visible above card',cards.filter_buttons['all'][0].winfo_containing(cards.filter_buttons['all'][0].winfo_rootx()+10,cards.filter_buttons['all'][0].winfo_rooty()+10)==cards.filter_buttons['all'][0])
    check('template all tab starts at left',cards.filter_buttons['all'][0].winfo_x()<5)
    check('small library hides search without blank left column',not cards.search.winfo_manager() and cards.filter_buttons['favorites'][0].winfo_x()<150*cards.s)
    capture(center).save(out/'templates-empty.png')
    a.cfg['templates']=[dict(id=str(i),name='休息提醒 '+str(i),action='message',message_text='test',mode='countdown',seconds=900,favorite=i%2==0) for i in range(10)]
    cards.refresh();cards.set_filter('favorites');pump();check('favorite filter works with search',len(cards.rows)==5 and cards.search.winfo_manager())
    cards.query.set('2');pump();check('name and favorite filters combine',list(cards.rows)==['2']);cards.query.set('');pump();capture(center).save(out/'templates.png')
    a.open_settings();pump();s=a._settings_win;check('language page and nav removed','language' not in s.pages and 'language' not in s.nav.buttons)
    check('legacy language request becomes Chinese',Texts('EN').lang==Texts('CHT').lang=='CHS')
    a.cfg.update({'language':'EN'});a.cfg.save();check('settings enforce Chinese',Config().get('language')=='CHS')
    raw=json.loads(Path(config_file()).read_text(encoding='utf-8'));raw['language']='CHT';Path(config_file()).write_text(json.dumps(raw),encoding='utf-8');check('old config migrates without reset',Config().get('language')=='CHS' and len(Config().get('templates'))==10)
    backup=Path(temp.name)/'backup.json';export_backup(a.cfg,backup);data=json.loads(backup.read_text(encoding='utf-8'));data['settings']['language']='EN';backup.write_text(json.dumps(data),encoding='utf-8');check('old English backup imports as Chinese',read_backup(backup)[0]['language']=='CHS')
    capture(s).save(out/'settings.png');check('no callback exceptions',not errors or print(errors))
    (out/'results.json').write_text(json.dumps(dict(checks=checks,errors=errors),ensure_ascii=False,indent=2),encoding='utf-8')
finally:
    a.engine.stop();a.automation.close();a.floating.close();a.desktop.close();a.display_awake.close();a.root.destroy();temp.cleanup()
