"""Durable handoff ledger. Unknown side effects are never retried automatically."""
import copy
import datetime as dt
import uuid

TERMINAL={'submitted','done','failed','cancelled'}

def records(app):return app.cfg.get('execution_journal') or []

def prepare(app,task,occurrence=None):
    token=occurrence or uuid.uuid4().hex
    rows=copy.deepcopy(records(app))
    if not any(r['id']==token for r in rows):
        rows=[r for r in rows if r.get('state') not in TERMINAL]+[r for r in rows if r.get('state') in TERMINAL][-100:]
        rows.append(dict(id=token,state='pending',task=copy.deepcopy(task),updated=dt.datetime.now().isoformat(timespec='seconds')))
        app.cfg['execution_journal']=rows
    return token

def mark(app,token,state,detail=''):
    if not token:return
    previous=copy.deepcopy(records(app));rows=copy.deepcopy(previous)
    row=next((r for r in rows if r['id']==token),None)
    if row is None:raise OSError('预约交接记录不存在，未执行')
    row.update(state=state,detail=detail,updated=dt.datetime.now().isoformat(timespec='seconds'))
    app.cfg['execution_journal']=rows
    if not app.cfg.save():app.cfg['execution_journal']=previous;raise OSError('预约执行状态保存失败，未执行')

def reconcile(app):
    """Called once at startup before any queue recovery or execution."""
    rows=records(app);queued={t.get('occurrence_id') for t in app.task_queue}
    uncertain=[];blocked=set()
    for r in rows:
        token=r['id'];state=r.get('state')
        if state in TERMINAL:blocked.add(token)
        elif state=='submitting' or token not in queued:
            uncertain.append(token);blocked.add(token)
    if blocked:
        app.task_queue[:]=[t for t in app.task_queue if t.get('occurrence_id') not in blocked]
        app._save_queue()
        if (app.cfg.get('pending_timer') or {}).get('occurrence_id') in blocked:app.cfg['pending_timer']={}
        if not app.cfg.save():raise OSError('异常预约恢复状态保存失败')
    return uncertain

def cancel_in_memory(app,tasks):
    tokens={t.get('occurrence_id') for t in tasks}
    rows=copy.deepcopy(records(app))
    for row in rows:
        if row['id'] in tokens and row.get('state') in ('pending','queued'):row['state']='cancelled'
    app.cfg['execution_journal']=rows

def resolve(app,token,retry):
    row=next(r for r in records(app) if r['id']==token)
    if retry:
        task=copy.deepcopy(row['task']);task.update(mode='countdown',seconds=10,occurrence_id=token,source_automation=task.get('source_automation',task.get('id','')))
        mark(app,token,'pending')
        app.enqueue_task(task,start=False)
        mark(app,token,'queued')
    else:mark(app,token,'cancelled','用户选择不重复执行')
