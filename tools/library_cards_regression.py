"""Exercise the real card controls with isolated config and no system actions."""
import os,sys,tempfile,time,copy,json,datetime as dt
from pathlib import Path
from unittest.mock import patch
p=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(p/'src'));sys.stdout.reconfigure(encoding='utf-8')
temp=tempfile.TemporaryDirectory(prefix='shutdown-library-');os.environ['APPDATA']=temp.name
from main import enable_dpi_awareness
enable_dpi_awareness()
import actions,autostart
from ui_main import App
from ui_localize import messagebox
from task_store import save_template,export_backup,read_backup
from capture_window import capture
from i18n import Texts
App._init_tray=lambda a:None;autostart.set_enabled=lambda *a:True
actions.perform=lambda *a,**k:(_ for _ in ()).throw(AssertionError('Real system actions forbidden'))
a=App({'given':True,'action':'message'});a.cfg.update(dict(confirm_on_exit=False,autostart=False))
checks=[];errors=[];metrics={}
a.root.report_callback_exception=lambda t,v,b:errors.append(str(v))
def check(name,ok):
    checks.append((name,bool(ok)));print(('PASS ' if ok else 'FAIL ')+name,flush=True);assert ok,name
def pump(seconds=.08):
    end=time.perf_counter()+seconds
    while time.perf_counter()<end:a.root.update();time.sleep(.002)
def invoke_menu(cards,index):
    cards.view.owner.focus_force();pump()
    cards.buttons[2].invoke();pump();cards.popup.buttons[index].invoke();pump()
def columns_aligned(cards):
    for row in cards.rows.values():
        for i,key in enumerate(('name','edit','condition','badge')):
            w=row[key];h=cards.headings[i]
            offset=w.winfo_width()/2 if i in (1,3) else 0
            header_offset=h.winfo_width()/2 if i in (1,3) else 0
            if abs(w.winfo_rootx()+offset-h.winfo_rootx()-header_offset)>1:return False
            if w.winfo_x()<0 or w.winfo_x()+w.winfo_width()>row['frame'].winfo_width()+1:return False
    return True
out=p/'核验/library-cards';out.mkdir(parents=True,exist_ok=True)
try:
    pump(.2);center=a.open_task_center('templates');pump()
    view=center.panels['templates'];cards=view.cards
    check('empty template state disables selection actions',not cards.rows and cards.buttons[0].cget('state')=='disabled')
    cards.buttons[2].invoke();pump()
    check('empty menu enables new and disables edit',cards.popup.buttons[0].cget('state')=='normal' and cards.popup.buttons[1].cget('state')=='disabled')
    cards.popup.dismiss();pump()
    capture(center).save(out/'templates-empty.png')
    samples=[('午休提醒','message','countdown',900),('工作结束','lock','datetime',0),('喝水提醒','message','interval',3600),('晚间提醒','message','datetime',0)]
    for name,action,mode,seconds in samples:
        task=dict(name=name,action=action,mode=mode,seconds=seconds,weekday=dt.datetime.now().weekday(),hour=18 if action=='lock' else 22,minute=0,second=0)
        save_template(a.cfg,name,task)
    view.commit();pump()
    check('four template cards and only one edit button per row',len(cards.rows)==4 and all(len([w for w in row['frame'].winfo_children() if w.winfo_class()=='Button'])==1 for row in cards.rows.values()))
    check('template text and control centers align with headings',columns_aligned(cards))
    check('footer three equally sized buttons',len(cards.buttons)==3 and max(b.winfo_width() for b in cards.buttons)-min(b.winfo_width() for b in cards.buttons)<=6)
    check('footer reaches both content edges',abs(cards.bottom.winfo_x()-cards.card.winfo_x())<=1 and abs(cards.bottom.winfo_width()-cards.card.winfo_width())<=1)
    selected=view.selected();identifier=selected['id'];cards.favorite_button.invoke();pump()
    check('favorite saved and star updated',view.selected()['favorite'] and cards.favorite_button.cget('text')=='★' and a.cfg.get('templates')[0]['favorite'])
    backup=Path(temp.name)/'favorites.json';export_backup(a.cfg,backup)
    check('favorite survives backup validation',read_backup(backup)[1][0]['favorite'])
    with patch.object(a.cfg,'save',return_value=False),patch.object(messagebox,'showerror') as error:
        cards.favorite_button.invoke();pump();check('failed favorite save rolls back',view.selected()['favorite'] and error.called)
    view.refresh_status();pump()
    capture(center).save(out/'templates.png')
    changed=copy.deepcopy(view.selected());changed['name']='午休提醒（已编辑）'
    with patch.object(view,'editor',return_value=changed):cards.rows[str(identifier)]['edit'].invoke();pump()
    check('row edit changes selected template',view.selected()['name']==changed['name'])
    duplicate=copy.deepcopy(changed);duplicate.pop('id');duplicate['name']='午休提醒 副本'
    with patch.object(view,'editor',return_value=duplicate):invoke_menu(cards,2)
    check('copy menu creates a new template',len(view.items())==5)
    cards.select(str(identifier));pump()
    with patch.object(messagebox,'askyesno',return_value=True):invoke_menu(cards,3)
    check('delete menu records undo',len(view.items())==4 and a.undo.available())
    invoke_menu(cards,4)
    check('undo menu restores deleted template with favorite',len(view.items())==5 and next(t for t in view.items() if t['id']==identifier)['favorite'])
    cards.select(str(identifier));pump();cards.buttons[0].invoke();pump()
    check('add-to-queue copies selected template',len(a.task_queue)==1 and a.engine.is_running() and a._active_task['name']==changed['name'])
    a.engine.stop();a.task_queue=[];a._active_task=None
    with patch('ui_tasks.simpledialog.askstring',return_value='从主页面保存'),patch.object(a,'current_task_snapshot',return_value=dict(action='message',mode='countdown',seconds=120)):
        cards.buttons[1].invoke();pump()
    check('save current setup remains accessible',any(t['name']=='从主页面保存' for t in view.items()))
    center.select_tab('advanced');pump();advanced=center.panels['advanced'];ac=advanced.cards
    check('empty advanced state and no fake next task',not ac.rows and ac.next_task() is None and ac.buttons[1].cget('state')=='disabled')
    capture(center).save(out/'advanced-empty.png')
    for i,name in enumerate(('资料备份','午后休息','周末清理')):
        at=(dt.datetime.now()+dt.timedelta(days=1,hours=i)).replace(second=0,microsecond=0)
        job=a.automation.add(dict(name=name,mode='calendar',action='message',at=at.isoformat(),repeat='workdays' if i<2 else 'weekends'))
        if i<2:a.automation.enable(job['id'],True)
    advanced.refresh_status();pump()
    check('summary chooses earliest enabled task',ac.next_task()['name']=='资料备份')
    check('advanced text and control centers align with headings',columns_aligned(ac))
    third=a.automation.jobs[2];ac.select(str(third['id']));pump()
    check('selection detail independent of next summary',ac.next_task()['name']=='资料备份' and advanced.selected()['id']==third['id'] and '尚未启用' in ac.next_label._full_text)
    ac.buttons[1].invoke();pump();check('enable button arms selected task',third['enabled'] and bool(third['next_at']))
    ac.buttons[1].invoke();pump();check('disable button disarms selected task',not third['enabled'])
    ac.select(str(a.automation.jobs[0]['id']));pump();capture(center).save(out/'advanced.png')
    invoke_menu(ac,4)
    check('skip today menu persists exception date',advanced.selected()['skip_date']==dt.date.today().isoformat())
    invoke_menu(ac,5)
    from ui_extras import PreviewWindow
    previews=[w for w in center.winfo_children() if isinstance(w,PreviewWindow)]
    check('seven day preview opens from menu',bool(previews) and a.root.grab_current() is previews[0])
    previews[0].destroy();pump();check('preview closes back to modeless workspace',a.root.grab_current() is None)
    center.select_tab('templates');pump();long=next(iter(view.items()));long['name']='超长模板名称用于验证固定列宽和完整详情不会挤出屏幕'*3
    view.refresh_status();pump()
    widths=cards.column_widths
    check('long name elides without expanding columns',cards.rows[str(long['id'])]['name'].cget('text').endswith('…') and sum(widths)==cards.canvas.winfo_width())
    check('long name retains full data',view.selected()['name']==long['name'])
    saved=copy.deepcopy(view.items())
    many=[]
    for i in range(200):
        task=copy.deepcopy(saved[0]);task.update(id='many-'+str(i),name='滚动验证模板 '+str(i+1));many.append(task)
    a.cfg['templates']=many;view.refresh_status();pump()
    first=cards.rows['many-0'];before=cards.canvas.yview()
    first['name'].event_generate('<MouseWheel>',delta=-120);pump()
    check('mouse wheel over row scrolls list',cards.canvas.yview()[0]>before[0])
    identities={key:str(row['frame']) for key,row in cards.rows.items()};position=cards.canvas.yview()[0]
    cards.favorite_button.invoke();pump()
    check('favorite reuses all 200 rows and preserves scroll',identities=={key:str(row['frame']) for key,row in cards.rows.items()} and abs(cards.canvas.yview()[0]-position)<.001)
    start=time.perf_counter()
    for _ in range(10):view.refresh_status()
    metrics['unchanged_200_rows_refresh_ms']=(time.perf_counter()-start)*100
    check('unchanged refresh retains row widgets',identities=={key:str(row['frame']) for key,row in cards.rows.items()})
    a.cfg['templates']=saved;view.refresh_status();pump()
    for lang in ('CHT','EN'):
        center.destroy();a.T=Texts(lang);center=a.open_task_center('templates');pump()
        for key in ('templates','advanced'):
            center.select_tab(key);pump();c=center.panels[key].cards
            check(lang+' '+key+' footer visible',all(b.winfo_y()+b.winfo_height()<=c.bottom.winfo_height()+1 for b in c.buttons))
            check(lang+' '+key+' columns aligned',columns_aligned(c))
            original=center.geometry()
            for width in (560,800):
                center.geometry(f'{round(width*c.s)}x{round(520*c.s)}');pump()
                check(lang+' '+key+' columns aligned at '+str(width),columns_aligned(c))
            center.geometry(original);pump()
            capture(center).save(out/(key+'-'+lang+'.png'))
    check('no UI callback errors',not errors or print(errors))
    (out/'results.json').write_text(json.dumps(dict(checks=checks,errors=errors,metrics=metrics),ensure_ascii=False,indent=2),encoding='utf-8')
finally:
    a.engine.stop();a.automation.close();a.floating.close();a.desktop.close();a.display_awake.close();a.root.destroy();temp.cleanup()
