"""Static five-petal progress and runtime context, within the existing status strip."""
import math,tkinter as tk
from PIL import Image,ImageDraw,ImageTk,ImageColor
from i18n import feature_text
from theme import theme
from ui_settings_controls import Tooltip

def blossom(size,percent,running):
    s=4;im=Image.new('RGBA',(size*s,size*s));d=ImageDraw.Draw(im);cx=cy=size*s/2;r=size*s*.46;completed=max(0,min(5,percent/20))
    accent=ImageColor.getrgb(theme.accent);pale=ImageColor.getrgb('#E1D1FA')
    for i in range(5):
        angle=-math.pi/2+i*math.tau/5;points=[]
        for side,steps in ((-1,range(25)),(1,range(24,-1,-1))):
            for step in steps:
                t=step/24;a=angle+side*.57*math.sin(math.pi*t)**.75;points.append((cx+r*t*math.cos(a),cy+r*t*math.sin(a)))
        amount=max(0,min(1,completed-i)) if running else 0
        fill=tuple(round(a+(b-a)*amount) for a,b in zip(pale,accent))+(245 if running else 0,)
        d.polygon(points,fill=fill);d.line(points+[points[0]],fill='#BCA3E8' if not running else '#F6EEFF',width=3,joint='curve')
    return im.resize((size,size),Image.Resampling.LANCZOS)

def edited(app):
    if not app.engine.is_running() or not app._active_task:return False
    try:current=app.current_task_snapshot()
    except (ValueError,TypeError):return True
    keys=('action','mode','seconds','weekday','hour','minute','second','program_path','close_program_path','sound_file','message_text','force_close_apps')
    return any(current.get(k)!=app._active_task.get(k) for k in keys if k in current or k in app._active_task)

def paint(app):
    running=app.engine.is_running();paused=app.engine.paused;percent=float(app.progress['value']) if running else 0
    key=(round(percent),running,theme.accent);cache=getattr(app,'_blossom_cache',None)
    if cache is None:cache=app._blossom_cache={}
    if key not in cache:
        if len(cache)>40:cache.pop(next(iter(cache)))
        cache[key]=ImageTk.PhotoImage(blossom(32,percent,running),master=app.root)
    ring=app.summary_ring;ring.delete('progress_flower');ring.create_image(0,0,image=cache[key],anchor='nw',tags='progress_flower');ring._flower_photo=cache[key]
    if hasattr(app,'queue_badge'):
        lang=app.T.lang;count=len(app.task_queue);app.queue_badge.config(text=feature_text(app.T,'队列')+' '+str(count)+('' if lang=='EN' else ' 項' if lang=='CHT' else ' 项'))
        app.btn_enqueue.config(text=feature_text(app.T,'加入队列'))
    app.summary_title._draft_changed=edited(app)

def more(app,event=None):
    from ui_popup_menu import VioletMenu
    menu=tk.Menu(app.root,tearoff=0)
    commands=[('延后'+str(m)+'分钟',lambda minutes=m:app.postpone(minutes)) for m in (5,10,30)]+[('打开任务中心',app.open_queue)]
    for title,command in commands:menu.add_command(label=feature_text(app.T,title),command=command)
    old=getattr(app,'_status_popup',None)
    if old and old.winfo_exists():old.dismiss()
    app._status_popup=VioletMenu(app,menu,anchor=app.summary_title,icons=('clock','clock','clock','enqueue'));return 'break'

def install(app):
    for w in (app.sbar,app.summary_title,app.status,app.summary_ring):w.bind('<Button-3>',lambda e:more(app,e),add='+')
    app.summary_title.bind('<Shift-F10>',lambda e:more(app,e),add='+')
    Tooltip(app.summary_title,lambda:feature_text(app.T,'上方修改的是下次设定，当前任务保持不变。') if edited(app) else feature_text(app.T,'右键可延后任务或查看队列。'))
    Tooltip(app.queue_badge,lambda:feature_text(app.T,'打开任务中心'))
    for attr,content in [('pin_btn','置顶主窗口'),('avatar_btn','程序设置'),('minimize_btn','最小化到任务栏'),('close_btn','关闭主窗口'),('summary_stop','停止当前任务'),('summary_pause','暂停／继续当前任务')]:
        Tooltip(getattr(app,attr),lambda value=content:feature_text(app.T,value))
    for action,b in app.action_more.items():
        key={'message':'message_text','run_program':'program_path','close_program':'close_program_path','play_sound':'sound_file'}[action]
        Tooltip(b,lambda k=key:feature_text(app.T,'点击编辑：')+str(app.cfg.get(k,'')).replace('\n',' ')[:180])
    variables=[app.action_var,app.mode_var]+[getattr(app,name) for name in ('cd_days','cd_h','cd_m','cd_s','dt_h','dt_m','dt_s','iv_h','iv_m','iv_s')]
    for var in variables:var.trace_add('write',lambda *a:refresh_later(app))

def refresh_later(app):
    if getattr(app,'_context_refresh',None):return
    def run():
        app._context_refresh=None
        if app.root.winfo_exists():
            from ui_summary import refresh
            refresh(app)
    app._context_refresh=app.root.after_idle(run)
