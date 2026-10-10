"""仅恢复本次会话删除的项目，保留删除后发生的其他修改。"""
import copy
import time

class UndoManager:
    def __init__(self,app,clock=time.monotonic):self.app=app;self.clock=clock;self.stack=[]
    def record(self,kind,rows):
        if not rows:return
        self.stack.append((self.clock(),kind,copy.deepcopy(rows)));self.stack=self.stack[-20:]
    def available(self):
        self.stack=[x for x in self.stack if self.clock()-x[0]<=300]
        return bool(self.stack)
    def undo(self):
        if not self.available():raise ValueError('没有可撤销的删除（保留5分钟，退出后清除）')
        _,kind,rows=self.stack[-1];app=self.app
        current=copy.deepcopy(app.task_queue if kind=='queue' else app.cfg.get('templates') or [])
        if len(current)+len(rows)>200:raise ValueError('恢复后超过200个上限，请先整理任务')
        ids={x.get('id') for x in current};names={x.get('name') for x in current}
        for index,value in rows:
            value=copy.deepcopy(value)
            if value.get('id') in ids:raise ValueError('原任务标识已存在，未覆盖现有任务')
            if kind=='templates' and value.get('name') in names:raise ValueError('模板名称已存在，请先重命名现有模板')
            ids.add(value.get('id'));names.add(value.get('name'))
            current.insert(min(index,len(current)),value)
        old=copy.deepcopy(app.cfg.data);old_queue=app.task_queue
        if kind=='queue':app.task_queue=current;app._save_queue()
        else:app.cfg['templates']=current
        if not app.cfg.save():
            app.cfg.data=old;app.task_queue=old_queue;raise OSError('保存失败，删除记录仍可撤销')
        self.stack.pop()
        if kind=='queue':
            app._next_task_id=max([app._next_task_id]+[int(x['id'])+1 for x in current])
            if app._queue_win and app._queue_win.winfo_exists():app._queue_win.refresh()
        return kind,len(rows)

def remove_queue(app,ids):
    rows=[(i,t) for i,t in enumerate(app.task_queue) if t['id'] in ids]
    if not rows:return
    old=app.task_queue;old_data=copy.deepcopy(app.cfg.data)
    app.task_queue=[t for t in old if t['id'] not in ids];app._save_queue()
    if app._active_task and app._active_task.get('id') in ids:app.cfg['pending_timer']={} 
    if not app.cfg.save():app.task_queue=old;app.cfg.data=old_data;raise OSError('删除未保存，原队列已保留')
    app.undo.record('queue',rows)
    if app._active_task and app._active_task.get('id') in ids:app.stop_timer();app._active_task=None
    app._set_status('queue_removed',n=len(rows))
    if app._queue_win and app._queue_win.winfo_exists():app._queue_win.refresh()
