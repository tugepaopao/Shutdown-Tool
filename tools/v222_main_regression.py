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
out=p/'核验/v222'/str(scale);out.mkdir(parents=True,exist_ok=True)
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
 from theme import theme
 for action,button in a.action_widgets.items():
  button.invoke();pump(.02)
  check('action selection '+action,a.action_var.get()==action and button.cget('fg')==theme.accent)
 calls=[];pick=a.pick_for;a.pick_for=lambda action:calls.append(action)
 for action,button in a.action_more.items():
  button.invoke();check('parameter button dispatch '+action,calls[-1]==action and button.cget('text')=='…')
 a.pick_for=pick
 a.action_widgets['run_program'].invoke();pump()
 renderer=a.skin_renderer;renderer.render(force=True)
 from PIL import ImageChops
 for name,frame in list(a.pages.items())+[('status',a.sbar)]:
  x0,y0,x1,y1=renderer.box(frame)
  # Interior artwork must remain unchanged, including the selected action.
  box=(x0+3,y0+round(3*scale),x1-3,y1-3)
  if name=='time':continue  # The secondary-row dividers live in this section.
  check('no opaque '+name+' panel',ImageChops.difference(renderer.scene.crop(box),renderer._art_base.crop(box)).getbbox() is None)
 check('main window stays opaque',float(a.root.attributes('-alpha'))==1.0)
 check('idle progress track visible',a.progress.type(a.progress._track)=='line' and a.progress.itemcget(a.progress._track,'state')!='hidden')
 check('short sleep label',a.action_widgets['sleep'].cget('text')=='睡眠模式')
 check('short message label',a.action_widgets['message'].cget('text')=='弹出提示')
 from PIL import ImageTk
 button=a.btn_start;normal_image=None
 for state in ('idle','hover','pressed','keyboard','disabled'):
  button._hovering=state=='hover';button._pressed=state=='pressed';button._keyboard_focus=state=='keyboard'
  button.config(state='disabled' if state=='disabled' else 'normal')
  button._root()._cozy_keyboard_navigation=state=='keyboard'
  if state=='keyboard':button.focus_force()
  else:a.root.focus_force()
  pump(.03);button._paint()
  actual=ImageTk.getimage(button._plate).convert('RGB');base=renderer.crop(button).convert('RGB')
  w,h=actual.size;box=(round(w*.1),h//2-2,round(w*.25),h//2+2)
  check('Start interior transparent '+state,ImageChops.difference(actual.crop(box),base.crop(box)).getbbox() is None)
  edge=(w//2-8,0,w//2+8,round(5*scale))
  check('Start border visible '+state,ImageChops.difference(actual.crop(edge),base.crop(edge)).getbbox() is not None)
  if state=='idle':normal_image=actual.copy()
  if state in ('hover','pressed','keyboard','disabled'):check('Start state visible '+state,ImageChops.difference(actual,normal_image).getbbox() is not None)
 button._hovering=False;button._pressed=False;button._keyboard_focus=False;button.config(state='normal');a.root.focus_force();pump()
 check('Start purple foreground',button.cget('fg')==theme.accent)
 from PIL import ImageColor
 expected=ImageColor.getrgb(theme.accent)
 icon_image=ImageTk.getimage(button._theme_photo).convert('RGBA')
 check('Start play icon purple',any(pixel[3]>200 and max(abs(pixel[i]-expected[i]) for i in range(3))<=2 for pixel in icon_image.getdata()))
 a.root.focus_force();pump();capture(a.root).save(out/'main.png')
 a.action_widgets['message'].invoke();pump()
 fixed=(a.root.winfo_width(),a.root.winfo_height())
 check('all mode surfaces prepainted',all(g.winfo_ismapped() for g in a.time_groups.values()) and all(hasattr(f,'_main_surface_stamp') for fs in a.time_inputs.values() for f in fs))
 unmapped=[]
 for g in a.time_groups.values():g.bind('<Unmap>',lambda e:unmapped.append(str(e.widget)),add='+')
 a.root.focus_force();pump(.05);a.avatar_btn.invoke();a.root.update_idletasks()
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
 check('moderately narrow main width',a.root.winfo_width()<=round(430*scale)+24)
 from ui_cozy import scale as ui_scale
 rows=[grp for grp,_,_ in a.action_row_frames.values()]
 bottom=max(w.winfo_y()+w.winfo_height() for w in rows)
 check('action card has no fixed-height empty band',0<=a.actions_body.winfo_height()-bottom<=4)
 for action,b in a.action_widgets.items():
  check('action text fits '+action,b.winfo_width()>=b._content()[7]+8)
 check('action body remains within card',a.actions_body.winfo_width()<=a.pages['actions'].winfo_width()-12)
 left=a.action_row_frames['shutdown'][0];right=a.action_row_frames['restart'][0]
 check('action columns stay close',right.winfo_x()-(left.winfo_x()+left.winfo_width())<=8)
 check('columns use natural content widths',all(w.winfo_width()<=max(v.winfo_reqwidth() for v in rows if v.grid_info()['column']==w.grid_info()['column'])+2 for w in rows))
 for mode,fields in a.time_inputs.items():
  for i,field in enumerate(fields):
   import tkinter.font as tkfont
   from theme import theme
   label=field.values[field.index] if field is a.weekday_box else '00'
   check('time text fits '+mode+' '+str(i),tkfont.Font(root=field,font=theme.font(delta=8,bold=True)).measure(label)+round(24*ui_scale(field))<=field.winfo_width())
 metrics=dict(width=fixed[0],height=fixed[1],ratio=round(fixed[0]/fixed[1],3),action_body_height=a.actions_body.winfo_height(),action_bottom_gap=a.actions_body.winfo_height()-bottom,column_pitch=right.winfo_x()-left.winfo_x())
 (out/'layout.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
 check('weekday same height as time fields',len({f.winfo_height() for f in a.time_inputs['datetime']})==1)
 a.weekday_box.open();pump();capture(a.weekday_box.popup).save(out/'weekday-menu.png');check('weekday menu centered below field',abs(a.weekday_box.popup.winfo_rootx()+a.weekday_box.popup.winfo_width()/2-a.weekday_box.winfo_rootx()-a.weekday_box.winfo_width()/2)<3 and a.weekday_box.popup.winfo_rooty()>=a.weekday_box.winfo_rooty()+a.weekday_box.winfo_height());a.weekday_box.popup.select(4);pump();check('weekday selection updates timer',a.weekday_var.get()==a.weekday_box.values[4] and a.weekday_box.current()==4)
 capture(a.root).save(out/'datetime.png')
 a._pick_mode('countdown');a.root.update_idletasks()
 target=a.time_inputs['countdown'][2];target.event_generate('<Button-1>',x=25,y=20);pump()
 check('mode change does not steal clicked field focus',a.root.focus_get() is target)
 for mode in ('datetime','interval','countdown')*3:
  a._pick_mode(mode);a.root.update_idletasks();chosen=a.time_inputs[mode][-1]
  a.root.focus_force();chosen.event_generate('<Button-1>',x=25,y=20);pump(.04)
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
 a.cd_m.set('00');a.cd_s.set('30');a.btn_start.invoke();pump(.7)
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

