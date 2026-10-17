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
 task_features.enqueue(a,dict(mode='countdown',action='message',seconds=600),start=True)
 task_features.enqueue(a,dict(mode='countdown',action='message',seconds=900,name='休息提醒'))
 task_features.enqueue(a,dict(mode='countdown',action='message',seconds=1800,name='稍后提醒'))
 center=a.open_task_center();center.lift();center.focus_force();pump(.2)
 cards=center.panels['queue'].cards
 check('main remains modeless',a.root.grab_current() is None)
 check('pause and current more are circular size',cards.pause.winfo_width()==cards.pause.winfo_height() and cards.more_current.winfo_width()==cards.more_current.winfo_height())
 check('row actions only contain edit',all(len(widgets[-1].winfo_children())==1 for widgets in cards.rows.values()))
 check('undo disabled without deletion history',cards.undo.cget('state')=='disabled')
 buttons=cards.more_button.master.grid_slaves(row=0);buttons.sort(key=lambda w:int(w.grid_info()['column']))
 check('footer has exactly three ordered buttons',[b.cget('text') for b in buttons]==['保存为模板','撤销上一次删除','更多操作'])
 check('footer buttons share baseline',len({b.winfo_rooty() for b in buttons})==1 and max(b.winfo_width() for b in buttons)-min(b.winfo_width() for b in buttons)<=6)
 def aligned():
  for widgets in cards.rows.values():
   for i,w in enumerate(widgets[1:]):
    h=cards.headings[i]
    if i in (0,3):
     if abs(w.winfo_rootx()+w.winfo_width()/2-h.winfo_rootx()-h.winfo_width()/2)>2:return False
    elif abs(w.winfo_rootx()+(w._photo.width() if i==1 else 0)-h.winfo_rootx())>1:return False
  return True
 check('queue columns align at default width',aligned())
 original=(center.winfo_width(),center.winfo_height())
 center.geometry(f'{round(560*factor)}x{round(520*factor)}');pump(.2)
 check('queue columns align at minimum width',aligned())
 center.geometry(f'{round(800*factor)}x{round(550*factor)}');pump(.2)
 check('queue columns align after widening',aligned())
 __import__('ui_window').compact_show(center,a);__import__('ui_window').present_dialog(center);center.lift();center.focus_force();pump(.2)
 def click(button):
  button.winfo_toplevel().focus_force();pump(.05);button.event_generate('<Enter>');button.event_generate('<ButtonPress-1>',x=10,y=10);button.event_generate('<ButtonRelease-1>',x=10,y=10);pump(.25)
 click(cards.pause);check('circle pause click pauses real timer',a.engine.paused and cards.pause.paused)
 click(cards.pause);check('circle pause becomes resume and resumes',not a.engine.paused and not cards.pause.paused)
 click(cards.more_current);menu=cards.popup_window;pump(.2)
 check('current more menu remains visible',menu.winfo_exists() and not menu.closed)
 check('current menu anchored at top control',abs(menu.winfo_rootx()+menu.winfo_width()-cards.more_current.winfo_rootx()-cards.more_current.winfo_width())<4)
 menu.dismiss();pump(.1);check('dismiss returns modeless main',a.root.grab_current() is None)
 ids=cards.tv.get_children();cards.select(ids[0]);center.focus_force();pump(.1)
 click(cards.more_button);menu=cards.popup_window;pump(.4)
 check('bottom more click stays open',menu.winfo_exists() and not menu.closed and a.root.grab_current() is menu)
 check('menu actions and heading match reference',len(menu.buttons)==3 and any(isinstance(x,tk.Label) and x.cget('text')=='更多操作' for x in walk(menu)))
 check('menu aligns with more button',abs(menu.winfo_rootx()+menu.winfo_width()-cards.more_button.winfo_rootx()-cards.more_button.winfo_width())<4)
 if factor==1.25:
  x=min(center.winfo_rootx(),menu.winfo_rootx());y=min(center.winfo_rooty(),menu.winfo_rooty());right=max(center.winfo_rootx()+center.winfo_width(),menu.winfo_rootx()+menu.winfo_width());bottom=max(center.winfo_rooty()+center.winfo_height(),menu.winfo_rooty()+menu.winfo_height())
  ImageGrab.grab((x,y,right,bottom),all_screens=True).save(p/'核验/v2.0_任务中心_菜单.png')
 before=len(a.task_queue);click(menu.buttons[0]);pump(.15);check('copy item executes via menu',len(a.task_queue)==before+1 and a.root.grab_current() is None)
 cards.select(str(a.task_queue[-1]['id']));click(cards.more_button);menu=cards.popup_window;click(menu.buttons[1]);pump(.15)
 check('remove item executes via menu',len(a.task_queue)==before and a.undo.available())
 cards.refresh();check('undo becomes enabled',cards.undo.cget('state')=='normal')
 click(cards.undo);check('undo button restores deletion',len(a.task_queue)==before+1)
 # Cards keep fixed columns; long text elides within its own bounds.
 template=task_store.normalize(dict(mode='countdown',action='message',seconds=900,name='休息提醒'))
 template['id']=101;a.cfg['templates']=[template]
 advanced=task_store.normalize(dict(mode='calendar',action='message',name='休息提醒',at='2026-10-20 22:00:00',repeat='once',enabled=False))
 advanced['id']=201;a.automation.jobs=[advanced]
 def table_fits(panel):
  cards=panel.cards
  return sum(cards.column_widths)==cards.canvas.winfo_width() and all(
   w.winfo_x()>=0 and w.winfo_x()+w.winfo_width()<=row['frame'].winfo_width()+1
   and font.Font(root=w,font=w.cget('font')).measure(w.cget('text'))<=w.winfo_width()
   for row in cards.rows.values() for w in (row['name'],row['condition'],row['edit']))
 from tkinter import ttk
 for lang in ('CHS','EN'):
  a.cfg['language']=lang;a.apply_settings();pump(.2)
  for key in ('templates','advanced'):
   center.select_tab(key);pump(.2);panel=center.panels[key]
   check(lang+' '+key+' rendered text fits fixed columns',table_fits(panel))
   if lang=='CHS' and factor==1.25:
    center.lift();center.focus_force();pump(.15);snap(center,'v2.0_'+key+'.png')
   center.geometry(f'{round(560*factor)}x{round(520*factor)}');pump(.15)
   check(lang+' '+key+' narrow window retains card bounds',table_fits(panel))
   __import__('ui_window').compact_show(center,a);__import__('ui_window').present_dialog(center);center.lift();center.focus_force();pump(.1)
 a.cfg['language']='CHS';a.apply_settings();center.select_tab('queue');__import__('ui_window').compact_show(center,a);__import__('ui_window').present_dialog(center);pump(.2)
 if factor==1.25:
  center.lift();center.focus_force();pump(.15);snap(center,'v2.0_任务队列.png')
 # Root gear menu uses the same popup component; it must remain usable.
 center.withdraw();a.root.lift();a.root.focus_force();pump(.15)
 from ui_popup_menu import VioletMenu
 native=tk.Menu(a.root,tearoff=0);native.add_command(label='Safe test',command=lambda:None)
 gear=VioletMenu(a,native,anchor=a.avatar_btn,icons=('gear',));pump(.3)
 print('gear focus diagnostic',a.root.focus_get(),a.root.state(),gear.closed,flush=True);check('main gear popup still opens',gear.winfo_exists() and not gear.closed);gear.dismiss();pump(.1)
 center.deiconify();center.lift();center.focus_force();pump(.15)
 a.cfg['language']='EN';a.apply_settings();pump(.2);click(cards.more_button);menu=cards.popup_window
 print('menu labels',[b.cget('text') for b in menu.buttons],flush=True)
 check('English action menu opens and translates',menu.winfo_exists() and [b.cget('text') for b in menu.buttons]==['Copy task','Delete selected','Clear queue'])
 menu.dismiss();check('no callback errors',not errors or print(errors))
finally:
 a.engine.stop();a.automation.close();a.floating.close();a.desktop.close();a.root.destroy()
(p/'核验'/f'v200-task-center-{factor}.json').write_text(json.dumps({'checks':checks,'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')



