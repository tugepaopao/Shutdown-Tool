"""Safe main-layout and timer regression; isolated settings and no real actions."""
import os,sys,time,tempfile,json
from pathlib import Path
p=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(p/'src'),str(p/'tools')]
tmp=tempfile.TemporaryDirectory();os.environ['APPDATA']=tmp.name
from main import enable_dpi_awareness
enable_dpi_awareness()
import ui_main,autostart
ui_main.App._init_tray=lambda a:None
autostart.set_enabled=lambda *a:True
ui_main.perform=lambda *a,**k:(_ for _ in ()).throw(AssertionError('Real action forbidden'))
from capture_window import capture
scale=float(sys.argv[1]) if len(sys.argv)>1 else 1
# Set scaling before building widgets.
original=ui_main.App.build_ui
def build(a):
 a.root.tk.call('tk','scaling',scale*96/72)
 return original(a)
ui_main.App.build_ui=build
a=ui_main.App({'given':True,'action':'message'})
a.cfg.update(dict(confirm_on_exit=False,autostart=False,confirm_before_action=False))
a.automation.closed=True
errors=[];a.root.report_callback_exception=lambda t,v,b:errors.append(str(v))
out=p/'核验/v218'/str(scale);out.mkdir(parents=True,exist_ok=True)
checks=[]
def pump(n=.15):
 end=time.monotonic()+n
 while time.monotonic()<end:a.root.update();time.sleep(.004)
def check(name,value):
 assert value,name
 checks.append(name);print('PASS',name,flush=True)
try:
 pump(.4)
 a.cd_days.set('00');a.cd_h.set('00');a.cd_m.set('30');a.cd_s.set('00');pump()
 a.root.focus_force();pump();capture(a.root).save(out/'main.png')
 fixed=(a.root.winfo_width(),a.root.winfo_height())
 check('all mode surfaces prepainted',all(g.winfo_ismapped() for g in a.time_groups.values()) and all(hasattr(f,'_main_surface_stamp') for fs in a.time_inputs.values() for f in fs))
 unmapped=[]
 for g in a.time_groups.values():g.bind('<Unmap>',lambda e:unmapped.append(str(e.widget)),add='+')
 a.avatar_btn.invoke();pump()
 check('settings menu contains six working rows',len(a._avatar_popup.buttons)==6)
 a._avatar_popup.select(0);pump()
 check('settings opens from gear menu',a._settings_win.winfo_exists())
 a._settings_win.destroy();pump()
 check('top buttons have no text',a.avatar_btn.cget('text')==a.task_center_btn.cget('text')=='')
 for mode,g in a.time_groups.items():
  a._pick_mode(mode);pump()
  check('mode/input/preset/start order '+mode,a.mode_bar.winfo_rooty()<g.winfo_rooty()<a.time_content_anchor.winfo_rooty()<a.btn_start.winfo_rooty())
  check('stable window on mode switch '+mode,(a.root.winfo_width(),a.root.winfo_height())==fixed)
  check('controls within window '+mode,a.sbar.winfo_rooty()+a.sbar.winfo_height()<=a.root.winfo_rooty()+a.root.winfo_height())
 a._pick_mode('datetime');pump();a.root.focus_force();pump()
 check('narrow main proportions restored',a.root.winfo_width()/a.root.winfo_height()<.75)
 check('weekday same height as time fields',len({f.winfo_height() for f in a.time_inputs['datetime']})==1)
 a.weekday_box.open();pump();capture(a.weekday_box.popup).save(out/'weekday-menu.png');check('weekday menu centered below field',abs(a.weekday_box.popup.winfo_rootx()+a.weekday_box.popup.winfo_width()/2-a.weekday_box.winfo_rootx()-a.weekday_box.winfo_width()/2)<3 and a.weekday_box.popup.winfo_rooty()>=a.weekday_box.winfo_rooty()+a.weekday_box.winfo_height());a.weekday_box.popup.select(4);pump();check('weekday selection updates timer',a.weekday_var.get()==a.weekday_box.values[4] and a.weekday_box.current()==4)
 capture(a.root).save(out/'datetime.png')
 a._pick_mode('countdown');a.root.update_idletasks()
 target=a.time_inputs['countdown'][2];target.event_generate('<Button-1>',x=25,y=20);pump()
 check('mode change does not steal clicked field focus',a.root.focus_get() is target)
 for mode in ('datetime','interval','countdown')*3:
  a._pick_mode(mode);a.root.update_idletasks();chosen=a.time_inputs[mode][-1]
  chosen.event_generate('<Button-1>',x=25,y=20);pump(.04)
  chosen.event_generate('<KeyPress-1>');chosen.event_generate('<KeyPress-2>');pump(.01)
  check('rapid switch and type '+mode+' '+str(len(checks)),chosen.variable.get()=='12' and a.root.focus_get() is chosen)
 from types import SimpleNamespace
 chosen.key(SimpleNamespace(keysym='a',state=4,char='a'));chosen.key(SimpleNamespace(keysym='KP_4',state=0,char=''));check('keypad digits with empty char',chosen.variable.get()=='4')
 field=a.time_inputs['countdown'][2];field.variable.set('30');field.step(1)
 check('large field shares countdown variable',a.cd_m.get()=='31')
 field.focus_force();pump();field.event_generate('<Control-a>');field.event_generate('<KeyPress-4>');field.event_generate('<KeyPress-2>');pump();check('transparent typing updates value',a.cd_m.get()=='42');capture(a.root).save(out/'editing.png');check('selected time uses triangle',bool(field.find_withtag('time-selection')));a.root.focus_force();pump();check('triangle hidden on blur',not field.find_withtag('time-selection'));field.focus_force();pump();field.selected=False;field.cursor=2
 field.event_generate('<BackSpace>');pump();check('backspace edits value',a.cd_m.get()=='4')
 field.variable.set('59');field.step(1);check('increment respects limit',a.cd_m.get()=='59')
 field.variable.set('00');field.step(-1);check('decrement respects zero',a.cd_m.get()=='00')
 a.cd_m.set('00');a.cd_s.set('30');a.start_timer();pump(.7)
 check('start timer',a.engine.is_running())
 pump(1.2);check('progress advances',float(a.progress['value'])>0)
 a.toggle_pause();pump(.2);value=float(a.progress['value']);pump(.6)
 check('pause preserves progress',a.engine.paused and abs(float(a.progress['value'])-value)<.01)
 capture(a.root).save(out/'paused.png')
 a.toggle_pause();pump(.3);check('resume timer',not a.engine.paused)
 a.stop_timer();pump();check('stop resets progress',not a.engine.is_running() and float(a.progress['value'])==0)
 a.task_center_btn.invoke();pump();check('dedicated task center button',a._task_center_win.winfo_exists())
 a._task_center_win.destroy();pump()
 from theme import theme
 old_mode=theme.mode;theme.mode='dark'
 field=a.time_inputs['countdown'][2];field.variable.set('05');field.draw();pump()
 check('focused numeric field has no native entry',not field.winfo_children())
 theme.mode=old_mode;field.draw()
 a._pick_mode('datetime');pump();a.weekday_box.focus_force();pump();check('weekday has no dashed focus rectangle',not a.weekday_box.find_withtag('focus-ring'))
 check('mode switching never unmaps input surfaces',not unmapped)
 check('no callback exceptions',not errors)
finally:
 a.engine.stop();a.automation.close();a.floating.close();a.desktop.close();a.display_awake.close();a.root.destroy()
 (out/'results.json').write_text(json.dumps(dict(checks=checks,errors=errors),ensure_ascii=False,indent=2),encoding='utf-8')

