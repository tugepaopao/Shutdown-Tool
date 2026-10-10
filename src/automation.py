"""独立预约/条件任务。到点转入现有队列，保留10秒可取消阶段。"""
import copy
import datetime as dt
import time
import uuid
import run_log
from task_store import normalize,next_calendar
from transfer_monitor import TransferWatcher
from condition_jobs import CombinedWatcher,ChainWatcher
ADVANCED_MODES=('calendar','download','network','combined','chain')

class AutomationController:
    def __init__(self,app):
        self.app=app;self.jobs=[];self.watchers={};self.tokens={};self.states={};self.closed=False
        self.reload();self.app.root.after(1000,self._tick)
    def log(self,text,kind='info',detail=''):
        desktop=getattr(self.app,'desktop',None)
        if desktop and kind in ('setup','done','error'):desktop.notify(kind,text)
        if self.app.cfg.get('log_enabled',True):run_log.add(kind,text,detail=detail)
    def persist(self):
        self.app.cfg['automations']=copy.deepcopy(self.jobs)
        if not self.app.cfg.save():raise OSError('高级任务保存失败')
    def reload(self):
        self.stop_watchers();self.jobs=[];restore_changed=False
        for raw in self.app.cfg.get('automations') or []:
            try:
                task=normalize(raw)
                if task['mode'] not in ADVANCED_MODES:raise ValueError('高级任务方式错误')
                task['id']=str(raw.get('id') or uuid.uuid4().hex)
                if any(j['id']==task['id'] for j in self.jobs):raise ValueError('任务标识重复')
                task['enabled']=bool(raw.get('enabled',False));task['next_at']=raw.get('next_at','');task['skip_date']=str(raw.get('skip_date',''))
                self.jobs.append(task)
                if task['enabled']:self._arm(task,restoring=True)
                if raw.get('enabled') and not task['enabled']:restore_changed=True
            except Exception as exc:self.log('跳过无效高级任务',kind='error',detail=str(exc))
        if restore_changed:
            self.app.cfg['automations']=copy.deepcopy(self.jobs)
            if not self.app.cfg.save():self.log('任务恢复状态未保存；本次任务已停用',kind='error')
    def stop_watchers(self):
        for watcher in self.watchers.values():watcher.stop()
        self.watchers={};self.tokens={}
    def close(self):self.closed=True;self.stop_watchers()
    def _arm(self,task,restoring=False):
        if task['mode']=='chain' and restoring:
            task['enabled']=False;task['next_at']='';self.states[task['id']]='重开后需重新启用任务链'
            self.log('任务链未自动重新运行：'+task['name']);return
        if task['mode']=='calendar':
            now=dt.datetime.now()
            try:at=dt.datetime.fromisoformat(task.get('next_at',''))
            except (ValueError,TypeError):at=None
            if at is None or at<=now or at.date().isoformat()==task.get('skip_date'):
                if restoring and at is not None:self.log('高级预约已错过，不补执行：'+task['name'])
                at=next_calendar(task,now)
            if at is None:
                task['enabled']=False;task['next_at']='';self.states[task['id']]='已过期，未补执行';return
            task['next_at']=at.isoformat(timespec='seconds');self.states[task['id']]='等待 '+task['next_at'].replace('T',' ')
        else:
            token=uuid.uuid4().hex;self.tokens[task['id']]=token;self.states[task['id']]='等待活动'
            emit=lambda state,error:self.app.emit('automation_state',{'id':task['id'],'token':token,'state':state,'error':error})
            watcher={'combined':CombinedWatcher,'chain':ChainWatcher}.get(task['mode'],TransferWatcher)
            self.watchers[task['id']]=watcher(copy.deepcopy(task),emit).start()
    def add(self,task):
        task=normalize(task)
        if len(self.jobs)>=200:raise ValueError('高级任务已达200个上限')
        if not task['name'] or any(t['name']==task['name'] for t in self.jobs):raise ValueError('请输入不重复的任务名称')
        if task['mode'] not in ADVANCED_MODES:raise ValueError('请选择高级任务方式')
        task.update(id=uuid.uuid4().hex,enabled=False,next_at='');self.jobs.append(task)
        try:self.persist()
        except Exception:self.jobs.remove(task);raise
        return task
    def enable(self,identifier,enabled=True):
        task=next(j for j in self.jobs if j['id']==identifier)
        previous=copy.deepcopy(task)
        at=next_calendar(task) if enabled and task['mode']=='calendar' else None
        if enabled and task['mode']=='calendar' and at is None:raise ValueError('该日期已过去，请修改日期')
        if enabled and task['mode']=='chain':
            import os
            if not os.path.isfile(task['prepare_path']) or not task['prepare_path'].lower().endswith('.exe'):raise ValueError('备份程序不存在或不是exe文件')
        task['enabled']=bool(enabled);task['next_at']=at.isoformat(timespec='seconds') if at else ''
        try:self.persist()
        except OSError:
            task.clear();task.update(previous);raise
        if identifier in self.watchers:self.watchers.pop(identifier).stop()
        self.tokens.pop(identifier,None)
        if enabled:
            self._arm(task)
            self.log(('Enabled advanced task: ' if self.app.T.lang=='EN' else '已启用高级任务：')+task['name'],kind='setup')
        else:self.states[identifier]='已停用'
    def skip_today(self,identifier,now=None):
        now=now or dt.datetime.now();task=next(j for j in self.jobs if j['id']==identifier)
        if task['mode']!='calendar' or task.get('repeat','once')=='once' or not task.get('enabled'):raise ValueError('请选择已启用的重复预约')
        old=copy.deepcopy(task);task['skip_date']=now.date().isoformat()
        nxt=next_calendar(task,now);task['next_at']=nxt.isoformat(timespec='seconds') if nxt else ''
        try:self.persist()
        except OSError:task.clear();task.update(old);raise
        self.states[identifier]='今天已跳过；下次 '+task['next_at'].replace('T',' ')
        self.log('今天跳过一次：'+task['name'])
    def remove(self,identifier):
        old=self.jobs;self.jobs=[j for j in self.jobs if j['id']!=identifier]
        try:self.persist()
        except OSError:self.jobs=old;raise
        if identifier in self.watchers:self.watchers.pop(identifier).stop()
        self.tokens.pop(identifier,None);self.states.pop(identifier,None)
    def handle(self,payload):
        identifier=payload['id']
        if self.closed or self.tokens.get(identifier)!=payload.get('token'):return
        task=next((j for j in self.jobs if j['id']==identifier and j['enabled']),None)
        if not task:return
        state=payload['state'];self.states[identifier]={'active':'传输中','quiet':'确认安静中','waiting':'等待活动','ready':'已完成，加入队列','timeout':'等待超时，未执行','error':'监控失败，未执行','waiting_user':'等待无人操作','preparing':'前置程序运行中'}.get(state,state)
        if state in ('ready','timeout','error'):
            task['enabled']=False;self.tokens.pop(identifier,None);self.watchers.pop(identifier,None)
            try:self.persist()
            except OSError as exc:self.log('监控结果保存失败，未执行',kind='error',detail=str(exc));return
            if state=='ready':self._dispatch(task)
            else:self.log(self.states[identifier]+'：'+task['name'],kind='error',detail=payload.get('error',''))
    def _dispatch(self,task):
        queued={k:v for k,v in task.items() if k in ('action','name','close_program_path','program_path','sound_file','message_text','force_close_apps')}
        queued.update(mode='countdown',seconds=10,source_automation=task['id'])
        try:self.app.enqueue_task(queued,start=True)
        except (ValueError,OSError) as exc:
            self.log('高级任务未能加入队列：'+task['name'],kind='error',detail=str(exc));return
        self.log('高级任务到点，加入队列（含10秒可取消）：'+task['name'])
    def tick(self,now=None):
        now=now or dt.datetime.now()
        for task in list(self.jobs):
            if not task.get('enabled') or task['mode']!='calendar':continue
            at=dt.datetime.fromisoformat(task['next_at'])
            if at.date().isoformat()==task.get('skip_date'):
                nxt=next_calendar(task,now);task['next_at']=nxt.isoformat(timespec='seconds') if nxt else '';task['enabled']=nxt is not None;self.persist();continue
            if at>now:continue
            late=(now-at).total_seconds()
            if task.get('repeat','once')=='once':task['enabled']=False;task['next_at']=''
            else:
                nxt=next_calendar(task,now);task['next_at']=nxt.isoformat(timespec='seconds')
            self.states[task['id']]=('已加入队列' if late<=90 else '已错过，未执行') if not task['enabled'] else '等待 '+task['next_at'].replace('T',' ')
            try:self.persist()
            except OSError as exc:
                task['enabled']=False;self.log('预约保存失败，未执行',kind='error',detail=str(exc));continue
            if late<=90:self._dispatch(task)
            else:self.log('预约已错过（电脑睡眠或程序关闭），未补执行：'+task['name'])
    def _tick(self):
        if self.closed:return
        try:
            self.tick()
            if self.app.tray:self.app.tray.refresh_status()
            win=getattr(self.app,'_advanced_win',None)
            if win and win.winfo_exists():win.refresh_status()
        except Exception as exc:self.log('高级任务检查失败',kind='error',detail=str(exc))
        try:self.app.root.after(1000,self._tick)
        except Exception:pass
