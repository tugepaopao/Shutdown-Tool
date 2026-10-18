"""Real Tcl popdown windows, modal restoration and library debounce checks."""
import os,sys,tempfile,time,json,tkinter as tk
from tkinter import ttk
from pathlib import Path
from unittest.mock import patch
p=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(p/'src'));sys.stdout.reconfigure(encoding='utf-8')
tmp=tempfile.TemporaryDirectory(prefix='shutdown-v210-ui-');os.environ['APPDATA']=tmp.name
from main import enable_dpi_awareness
enable_dpi_awareness()
import actions,autostart
from ui_main import App
from ui_focus import current_grab,current_focus,has_grab
from ui_window import prepare,show,activate_dialog
from ui_workspace import hide_workspace,restore_workspace,allow_exit
App._init_tray=lambda a:None;autostart.set_enabled=lambda *a:True
actions.perform=lambda *a,**k:(_ for _ in ()).throw(AssertionError('Real actions forbidden'))
a=App({'given':True,'action':'message'});a.cfg.update(dict(confirm_on_exit=False,autostart=False))
errors=[];checks=[];a.root.report_callback_exception=lambda t,v,b:errors.append(str(v))
def pump(seconds=.06):
    end=time.perf_counter()+seconds
    while time.perf_counter()<end:a.root.update();time.sleep(.002)
def check(name,ok):
    assert ok,name
    checks.append(name);print('PASS '+name,flush=True)
def dropdown(parent):
    c=ttk.Combobox(parent,values=('一','二','三'),state='readonly');c.place(x=8,y=50,width=130);c.current(0);pump();return c
def post(c):
    c.winfo_toplevel().lift();c.tk.call('ttk::combobox::Post',str(c));pump()
    check('native dropdown owns the grab',str(c.tk.call('grab','current',c._w)).endswith('.popdown'))
try:
    pump(.2);combo=dropdown(a.root);post(combo)
    try:a.root.grab_current()
    except KeyError as exc:check('reproduces original popdown failure',str(exc)=="'popdown'")
    else:raise AssertionError('Native popup did not reproduce original failure')
    current_focus(a.root);check('focus inspection keeps native popup open',has_grab(a.root))
    check('navigation closes native popup without stale grab',current_grab(a.root) is None and not has_grab(a.root))
    post(combo);center=a.open_task_center('templates');pump();check('open task center with posted dropdown',center.winfo_viewable() and not has_grab(a.root))
    post(combo);settings=a.open_settings();pump();check('open settings with posted dropdown',settings.winfo_viewable() and not has_grab(a.root))
    post(combo);hide_workspace(a);pump();check('hide workspace with dropdown',not a.root.winfo_viewable() and not has_grab(a.root));restore_workspace(a);pump()
    post(combo);check('exit guard handles native dropdown',allow_exit(a) and not has_grab(a.root))
    post(combo);a.hide_to_tray();pump();check('minimize closes dropdown and releases grab',a.root.state()=='iconic' and not has_grab(a.root));a.show_window();pump()
    modal=tk.Toplevel(a.root);prepare(modal);modal.title('test modal');show(modal);modal.grab_set();modal_combo=dropdown(modal);post(modal_combo)
    check('native dropdown restores previous modal owner',current_grab(a.root) is modal)
    post(modal_combo);check('switching windows retains modal editor',a.open_task_center() is modal)
    post(modal_combo);nested=tk.Toplevel(modal);prepare(nested);show(nested);nested.grab_set();nested.destroy();pump()
    check('nested dialog restores editor grab',current_grab(a.root) is modal)
    modal.destroy();combo.destroy();pump();check('closing editor releases grab',not has_grab(a.root))
    center=a.open_task_center('templates');cards=center.panels['templates'].cards
    a.cfg['templates']=[dict(id=str(i),name='模板'+str(i),action='message',mode='countdown',seconds=60,favorite=False) for i in range(200)]
    cards.refresh();pump(.2)
    with patch.object(cards,'refresh',wraps=cards.refresh) as refresh:
        cards.query.set('模');cards.query.set('模板');cards.query.set('模板199')
        center.refresh_status();check('periodic refresh respects pending search',refresh.call_count==0)
        pump(.22);check('rapid input merges into one search',refresh.call_count==1 and list(cards.rows)==['199'])
    with patch.object(cards.title,'config',wraps=cards.title.config) as title,patch.object(cards.favorite_button,'config',wraps=cards.favorite_button.config) as favorite:
        for _ in range(10):cards.refresh()
        check('unchanged refresh skips summary and controls',title.call_count==favorite.call_count==0)
    cards.query.set('模板1');cards.search.entry.event_generate('<Return>');pump(.22)
    check('search remains correct after keyboard confirmation','199' in cards.rows and '0' not in cards.rows)
    cards.query.set('模板');center.destroy();pump(.22)
    check('closing center cancels delayed search',not errors)
    check('no Tk callback errors',not errors)
    out=p/'核验/v210';out.mkdir(parents=True,exist_ok=True)
    (out/'ui.json').write_text(json.dumps(dict(checks=checks,errors=errors,passed=len(checks)),ensure_ascii=False,indent=2),encoding='utf-8')
finally:
    a.engine.stop();a.automation.close();a.floating.close();a.desktop.close();a.display_awake.close();a.root.destroy();tmp.cleanup()
print(str(len(checks))+' checks passed')
