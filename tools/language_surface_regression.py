import os,sys,time,tempfile,json,ctypes,tkinter as tk
from pathlib import Path
p=Path(__file__).resolve().parent.parent;sys.path[:0]=[str(p/'src'),str(p/'tools')]
from main import enable_dpi_awareness
enable_dpi_awareness()
from ui_main import App
from ui_dialogs import FadeMessageBox
from ui_localize import walk
import autostart,exe_test as ui
App._init_tray=lambda s:None;autostart.set_enabled=lambda *a:True
checks=[];errors=[];u=ctypes.windll.user32;u.GetAncestor.argtypes=[ctypes.c_void_p,ctypes.c_uint];u.GetAncestor.restype=ctypes.c_void_p

def check(n,v):checks.append([n,bool(v)]);print(('PASS ' if v else 'FAIL ')+n,flush=True);assert v,n
with tempfile.TemporaryDirectory(prefix='v1711-language-') as folder:
 os.environ['APPDATA']=folder;app=App({'given':True,'action':'message'});app.cfg['confirm_on_exit']=False;app.root.report_callback_exception=lambda c,e,t:errors.append(str(e))
 def pump(t=.25):
  until=time.monotonic()+t
  while time.monotonic()<until:app.root.update();time.sleep(.004)
 try:
  pump();app.apply_preset(('sec',600));app.btn_pause.invoke();due=(app.engine.generation,app.engine.remaining());selected=app.action_var.get()
  renderer=app.skin_renderer;calls=[];original=renderer.suspend
  def suspend():calls.append(True);original()
  renderer.suspend=suspend
  tracked=list(app.action_widgets.values())+[app.avatar_btn]+list(app.mode_btns.values())+[app.btn_start,app.btn_now,app.btn_enqueue]
  box=lambda w:(w.winfo_x(),w.winfo_y(),w.winfo_width(),w.winfo_height())
  for skin in ('solid','violet','red'):
   app.cfg.update(dict(skin=skin,language='CHS'));app.apply_settings();pump(.5);baseline={w:box(w) for w in tracked};identity={w:id(record) for w,record in renderer.tiles.items()};photos={w:record['photo'] for w,record in renderer.tiles.items()}
   unmapped=[]
   for w in renderer.surfaces.values():w.bind('<Unmap>',lambda e:unmapped.append(str(e.widget)),add='+')
   for lang in ('EN','CHT','CHS'):
    app.cfg['language']=lang;app.apply_settings();pump(.5)
    check(skin+' '+lang+' never dismantles cached surfaces',not calls and not unmapped and all(id(renderer.tiles[w])==record for w,record in identity.items()))
    check(skin+' '+lang+' retains skin text photos',all(renderer.tiles[w]['photo'] is photo for w,photo in photos.items()))
    changes=[(str(w),baseline[w],box(w)) for w in tracked if box(w)!=baseline[w]]
    if changes:print('layout differences',changes,flush=True)
    check(skin+' '+lang+' preserves control rectangles',not changes)
    check(skin+' '+lang+' preserves paused timer',(app.engine.generation,app.engine.remaining())==due and app.engine.paused and app.action_var.get()==selected)
    ui.grab_window(u.GetAncestor(app.root.winfo_id(),2),'v1711-language-'+skin+'-'+lang+'.png')
  app.cfg['skin']='violet';app.apply_settings();app.action_widgets['play_sound'].invoke();app.mode_btns['interval'].invoke();renderer.render();pump(.5)
  from PIL import ImageChops
  check('interleaved redraw keeps the latest selection after fade',app.action_var.get()=='play_sound' and app.mode_var.get()=='interval' and ImageChops.difference(renderer.scene,renderer._compose()).getbbox() is None)
  called=[]
  for title in (app.T('tip_cancel_title'),'操作已完成','提醒'):
   toast=FadeMessageBox(app.root,title,'这是一条安全测试提醒',seconds=30,button_text='取消执行',on_button=lambda:called.append(True));pump(.2)
   check(title+' has only its own reminder heading',not hasattr(toast,'_dialog_caption') and len([w for w in walk(toast) if isinstance(w,tk.Label) and str(w.cget('text'))==title])==1)
   if title==app.T('tip_cancel_title'):ui.grab_window(u.GetAncestor(toast.winfo_id(),2),'v1711-toast.png');toast._btn.invoke();check('reminder action button still calls callback',called==[True])
   else:toast.close()
   pump(.6)
  check('no callbacks',not errors)
 finally:
  app.engine.stop();app.floating.close();app.desktop.close()
  for job in app.root.tk.splitlist(app.root.tk.call('after','info')):app.root.after_cancel(job)
  app.root.destroy()
(p/'tools/v1711-language-results.json').write_text(json.dumps({'checks':checks,'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
