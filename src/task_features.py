"""App扩展接口：任务快照、队列编辑、延后、持久化。"""
import copy
import datetime as dt
import time
from task_store import snapshot,normalize,next_calendar
from actions import A_MESSAGE
from i18n import format_remain

def current_task(app):
    mode=app.mode_var.get();task={'mode':mode,'action':app._current_action()}
    if mode=='datetime':task.update(weekday=max(0,app.weekday_box.current()),hour=int(app.dt_h.get()),minute=int(app.dt_m.get()),second=int(app.dt_s.get()))
    else:
        task['seconds']=app._read_time(mode)[0]
        if task['seconds']<=0:raise ValueError(app.T('tip_need_time'))
    return snapshot(task,app.cfg)

def start_current(app):
    from ui_localize import messagebox
    continue_queue=False
    try:task=current_task(app)
    except (ValueError,TypeError) as exc:
        messagebox.showinfo(app.T('tip_title'),str(exc),parent=app.root);return
    if not app._validate_action(task['action']):return
    if app.engine.is_running():
        generation=app.engine.generation
        current=app.describe_action(app._active_task or {})
        choice=messagebox.askyesnocancel('已有任务正在运行',
            f'{current}正在计时\n替换会按上方设置重新开始\n加入队列会等待当前任务结束后执行\n循环任务需要先结束循环',
            parent=app.root,default='cancel',labels={'yes':'替换当前任务','no':'加入队列','cancel':'取消'})
        if choice is None:return
        # A modal dialog continues pumping timer events. Never replace a task
        # which started while the user was considering the old task.
        if app.engine.generation!=generation or not app.engine.is_running():
            messagebox.showinfo('任务状态已变化','当前任务已结束或发生变化，请重新确认安排。',parent=app.root);return
        if not choice:
            try:enqueue(app,task);app._queued_after_generation=generation
            except (ValueError,OSError) as exc:messagebox.showerror('加入队列失败',str(exc),parent=app.root)
            return
        app._close_cancel_toast()
        continue_queue=(getattr(app,'_queued_after_generation',None)==generation or app._active_task in app.task_queue)
        # Remove the replaced active queue entry so it cannot execute again.
        if app._active_task in app.task_queue:
            old=list(app.task_queue);app.task_queue.remove(app._active_task)
            try:refresh_queue(app)
            except OSError as exc:
                app.task_queue=old;app._save_queue()
                messagebox.showerror('替换失败',str(exc),parent=app.root);return
    app.engine.warning_seconds=int(app.cfg.get("warning_seconds",10))
    app._save_time_fields();app._active_task=task
    target=None
    if task['mode']=='datetime':
        from timer_engine import next_datetime
        target=next_datetime(task['weekday'],task['hour'],task['minute'],task['second'])
        app.cfg.update({'dt_weekday':task['weekday'],'dt_hour':task['hour'],'dt_minute':task['minute'],'dt_second':task['second']})
        app.engine.start_datetime(target)
    elif task['mode']=='interval':app.engine.start_interval(task['seconds'])
    else:app.engine.start_countdown(task['seconds'])
    if continue_queue:app._queued_after_generation=app.engine.generation
    app._set_running_ui(True);app._log_setup(task,target=target)

def enqueue_current(app):
    from ui_localize import messagebox
    try:
        task=current_task(app);app._save_time_fields();enqueue(app,task,start=True)
        app._log('info','log_queue_text',a=app.describe_action(task),w=app.describe_when(task))
    except (ValueError,TypeError,OSError) as exc:messagebox.showinfo(app.T('tip_title'),str(exc),parent=app.root)

def refresh_queue(app):
    app._save_queue()
    from ui_summary import refresh
    refresh(app)
    if not app.cfg.save():raise OSError('队列保存失败')
    if app._queue_win and app._queue_win.winfo_exists():app._queue_win.refresh()

def enqueue(app,task,start=False):
    if task.get('occurrence_id'):
        existing=next((t for t in app.task_queue if t.get('occurrence_id')==task['occurrence_id']),None)
        if existing:return existing
    if len(app.task_queue)>=200:raise ValueError('队列已达200个上限')
    task=snapshot(task,app.cfg)
    if task['mode'] not in ('countdown','datetime','interval'):
        raise ValueError('年月日／重复预约和传输任务请在高级任务中启用')
    task['id']=app._next_task_id;app._next_task_id+=1;app.task_queue.append(task)
    try:refresh_queue(app)
    except OSError:app.task_queue.remove(task);app._save_queue();raise
    app._set_status('queue_added',n=len(app.task_queue))
    desktop=getattr(app,'desktop',None)
    if desktop:desktop.notify('setup',app.T('queue_added',n=len(app.task_queue)))
    if start and not app.engine.is_running():app._start_next_task()
    return task

def editable(app,identifier):
    if app._active_task and app._active_task.get('id')==identifier and app.engine.is_running():
        raise ValueError('运行中的任务不能编辑或排序，请先停止')

def edit_queue(app,identifier,value):
    editable(app,identifier);old=next(t for t in app.task_queue if t['id']==identifier)
    task=snapshot(value,app.cfg)
    if task['mode'] not in ('countdown','datetime','interval'):raise ValueError('该方式请使用高级任务')
    task['id']=identifier;index=app.task_queue.index(old);app.task_queue[index]=task
    try:refresh_queue(app)
    except OSError:app.task_queue[index]=old;app._save_queue();raise

def copy_queue(app,ids):
    originals=[copy.deepcopy(t) for t in app.task_queue if t['id'] in ids]
    if len(app.task_queue)+len(originals)>200:raise ValueError('队列已达200个上限')
    before=list(app.task_queue);last=app._next_task_id
    for task in originals:
        task.pop('occurrence_id',None);task.pop('source_automation',None)
        task['id']=app._next_task_id;app._next_task_id+=1
        if task.get('name'):task['name']+=' 副本'
        app.task_queue.append(task)
    try:refresh_queue(app)
    except OSError:app.task_queue=before;app._next_task_id=last;app._save_queue();raise

def move_queue(app,ids,direction):
    if direction not in (-1,1):raise ValueError('排序方向错误')
    for identifier in ids:editable(app,identifier)
    protected=app._active_task.get('id') if app._active_task and app.engine.is_running() else None
    before=list(app.task_queue);indices=range(len(before)) if direction==-1 else range(len(before)-1,-1,-1)
    for index in indices:
        other=index+direction
        if app.task_queue[index]['id'] not in ids or not 0<=other<len(before):continue
        if app.task_queue[other]['id'] in ids or app.task_queue[other]['id']==protected:continue
        app.task_queue[index],app.task_queue[other]=app.task_queue[other],app.task_queue[index]
    try:refresh_queue(app)
    except OSError:app.task_queue=before;app._save_queue();raise

def postpone(app,minutes):
    if minutes not in (5,10,30):raise ValueError('只支持延后5、10或30分钟')
    if not app.engine.is_running():return False
    remain=app.engine.remaining();paused=app.engine.paused;mode=app.engine.mode
    continue_queue=getattr(app,'_queued_after_generation',None)==app.engine.generation
    # 重建这一轮使所有已排队的 tick/warn/finished 都作废，循环间隔本身保持。
    seconds=remain+minutes*60
    interval=app.engine._interval
    if mode=='interval':
        app.engine._start(seconds,mode);app.engine._interval=interval
    else:app.engine.start_countdown(seconds)
    if continue_queue:app._queued_after_generation=app.engine.generation
    if paused:app.engine.pause()
    app._close_cancel_toast();app._last_remain=seconds;app._set_running_ui(True)
    app._set_status('status_due_paused' if paused else 'status_due',t=format_remain(seconds,app.T),d=app._due_text())
    app._save_pending_timer();app.cfg.save()
    if app.cfg.get('log_enabled',True):
        import run_log
        run_log.add('info',f'本次任务延后 {minutes} 分钟')
    if app.tray:app.tray.refresh()
    return True

def save_pending(app):
    pending={}
    if app.engine.is_running():
        task=copy.deepcopy(app._active_task or current_task(app))
        pending={**task,'deadline':time.time()+app.engine.remaining(),'paused':app.engine.paused,
                 'continue_queue':getattr(app,'_queued_after_generation',None)==app.engine.generation,
                 'remaining':app.engine.remaining(),'engine_mode':app.engine.mode,'interval_seconds':app.engine._interval,
                 'queued':bool(app._active_task and 'id' in app._active_task and any(t.get('id')==app._active_task['id'] for t in app.task_queue))}
    app.cfg['pending_timer']=pending

def resume_pending(app):
    pending=app.cfg.get('pending_timer') or {};app.cfg['pending_timer']={};app.cfg.save()
    strategy=app.cfg.get('resume_strategy','continue')
    if not pending or strategy=='off' or not app.cfg.get('resume_timer',True) or app.engine.is_running() or app.cli.get('given'):return
    try:
        remaining=float(pending.get('remaining',0)) if pending.get('paused') else float(pending.get('deadline',0))-time.time()
        if remaining<=1:
            app._log('info','log_missed_text');return
        pause_recovery=strategy=='paused'
        if strategy=='ask':
            from ui_localize import messagebox
            choice=messagebox.askyesnocancel('恢复上次定时','上次的任务还没有完成\n可以继续计时，也可以先恢复为暂停状态',parent=app.root,default='cancel',labels={'yes':'继续计时','no':'恢复为暂停','cancel':'不恢复'})
            if choice is None:return
            pause_recovery=not choice
            if not pending.get('paused'):remaining=float(pending.get('deadline',0))-time.time()
            if remaining<=1:app._log('info','log_missed_text');return
        task=snapshot(pending,app.cfg)
        # 恢复对应队列项，避免重开后同一个任务又从队列头执行一次。
        active=next((t for t in app.task_queue if {k:v for k,v in t.items() if k!='id'}=={k:v for k,v in task.items() if k!='id'}),None) if pending.get('queued') else None
        app._active_task=active or task
        app.engine.start_countdown(remaining)
        if pending.get('continue_queue'):app._queued_after_generation=app.engine.generation
        if pending.get('engine_mode')=='interval' or task['mode']=='interval':
            with app.engine._lock:
                app.engine._mode='interval';app.engine._interval=float(pending.get('interval_seconds',task['seconds']))
        if pending.get('paused') or pause_recovery:app.engine.pause()
        app._set_running_ui(True);app._log('info','log_resume_text',a=app.describe_action(task),w=format_remain(remaining,app.T))
    except (ValueError,TypeError,KeyError) as exc:
        app._log('error','log_missed_text',detail=str(exc))
