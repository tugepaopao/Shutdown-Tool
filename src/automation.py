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
        self.stop_watchers();self.jobs=[];restore_changed=False;self._startup_pending=set()
        for raw in self.app.cfg.get('automations') or []:
            try:
                task=normalize(raw)
                if task['mode'] not in ADVANCED_MODES:raise ValueError('高级任务方式错误')
                task['id']=str(raw.get('id') or uuid.uuid4().hex)
                if any(j['id']==task['id'] for j in self.jobs):raise ValueError('任务标识重复')
                task['enabled']=bool(raw.get('enabled',False));task['next_at']=raw.get('next_at','');task['skip_date']=str(raw.get('skip_date',''))
                for key in ('pending_missed','last_state','last_error'):
                    if isinstance(raw.get(key),str):task[key]=raw[key]
                if task.get('last_state'):self.states[task['id']]=task['last_state']
                self.jobs.append(task)
                if task['enabled']:self._arm(task,restoring=True)
                if task!=raw:restore_changed=True
            except Exception as exc:self.log('跳过无效高级任务',kind='error',detail=str(exc))
        self._startup_pending={t['id'] for t in self.jobs if t.get('pending_missed')}
        if restore_changed:
            self.app.cfg['automations']=copy.deepcopy(self.jobs)
            if not self.app.cfg.save():
                for task in self.jobs:
                    task['enabled']=False;task.pop('pending_missed',None)
                    self.states[task['id']]='预约保存失败，未执行'
                self.stop_watchers();self.log('任务恢复状态未保存；本次任务已停用',kind='error')
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
                if restoring and at is not None and at<=now and at.date().isoformat() not in set(task.get('exception_dates',[]))|{task.get('skip_date','')}:
                    self._missed(task,at,now)
                at=next_calendar(task,now)
            if at is None:
                task['enabled']=False;task['next_at']=''
                if not task.get('last_state'):self.states[task['id']]='已结束' if task.get('end_date') else '已过期，未补执行'
                return
            task['next_at']=at.isoformat(timespec='seconds');self.states[task['id']]=task.get('last_state') or '等待 '+task['next_at'].replace('T',' ')
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
        task.pop('pending_missed',None);task.pop('last_state',None);task.pop('last_error',None)
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
        task['enabled']=nxt is not None
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
            task['last_state']=self.states[identifier]
            task['last_error']=str(payload.get('error',''))[:2000]
            try:self.persist()
            except OSError as exc:self.states[identifier]='监控结果保存失败，未执行';self.log('监控结果保存失败，未执行',kind='error',detail=str(exc));return
            if state=='ready':self._dispatch(task)
            else:self.log(self.states[identifier]+'：'+task['name'],kind='error',detail=payload.get('error',''))
    def _dispatch(self,task):
        queued={k:v for k,v in task.items() if k in ('action','name','close_program_path','program_path','sound_file','message_text','force_close_apps')}
        queued.update(mode='countdown',seconds=10,source_automation=task['id'])
        try:self.app.enqueue_task(queued,start=True)
        except (ValueError,OSError) as exc:
            self.states[task['id']]='加入队列失败，未执行'
            task['last_state']=self.states[task['id']]
            task['last_error']=str(exc)[:2000]
            try:self.persist()
            except OSError:pass
            self.log('高级任务未能加入队列：'+task['name'],kind='error',detail=str(exc));return
        self.log('高级任务到点，加入队列（含10秒可取消）：'+task['name'])
    def _missed(self,task,at,now=None):
        now=now or dt.datetime.now()
        if task.get('end_date') and task['end_date']<now.date().isoformat():
            task.pop('pending_missed',None);task['last_state']='已结束';self.states[task['id']]='已结束';return
        policy=task.get('missed_policy','skip')
        # Coalesce missed occurrences. Never enqueue every missed day on restart.
        if policy in ('ask','run'):task.setdefault('pending_missed',at.isoformat(timespec='seconds'))
        task['last_state']='错过待确认' if policy=='ask' else '等待补执行' if policy=='run' else '已错过，未执行'
        self.states[task['id']]=task['last_state']
        self.log('预约已错过：'+task['name'],detail=task['last_state'])
    def resolve_missed(self,identifier,execute,now=None):
        task=next((t for t in self.jobs if t['id']==identifier),None)
        if not task or not task.get('pending_missed'):return
        old=copy.deepcopy(task);task.pop('pending_missed',None)
        now=now or dt.datetime.now()
        if task.get('end_date') and task['end_date']<now.date().isoformat():execute=False
        if task.get('enabled'):
            nxt=next_calendar(task,now);task.update(enabled=nxt is not None,next_at=nxt.isoformat(timespec='seconds') if nxt else '')
        task['last_state']='已加入队列' if execute else '已错过，未执行'
        try:self.persist()
        except OSError:
            task.clear();task.update(old);raise
        self.states[identifier]=task['last_state']
        if execute:self._dispatch(task)
    def _resolve_pending(self):
        if getattr(self,'_asking_missed',False) or self.app.root.grab_current():return
        task=next((t for t in self.jobs if t.get('pending_missed') and t['id'] in getattr(self,'_startup_pending',set())),None)
        if not task:return
        if task.get('missed_policy')=='run':
            try:self.resolve_missed(task['id'],True)
            except OSError as exc:
                self._startup_pending.discard(task['id']);task['last_error']=str(exc);self.log('预约保存失败，未执行',kind='error',detail=str(exc))
            return
        if not self.app.root.winfo_viewable():return
        # Let _tick schedule its next pass before opening a nested modal event loop.
        self._asking_missed=True
        self.app.root.after_idle(lambda identifier=task['id']:self._ask_missed(identifier))
    def _ask_missed(self,identifier):
        from ui_localize import messagebox
        from i18n import feature_text
        try:
            task=next((t for t in self.jobs if t['id']==identifier and t.get('pending_missed')),None)
            if self.closed or not task or self.app.root.grab_current():return
            text=feature_text(self.app.T,'任务“{name}”错过了 {at}。是否补执行一次？加入队列后保留10秒取消时间。').format(name=task['name'],at=task['pending_missed'].replace('T',' '))
            execute=messagebox.askyesno(feature_text(self.app.T,'错过的预约'),text,parent=self.app.root)
            self.resolve_missed(task['id'],execute)
        except OSError as exc:
            self._startup_pending.discard(identifier)
            if task:task['last_error']=str(exc)
            self.log('预约保存失败，未执行',kind='error',detail=str(exc))
        finally:self._asking_missed=False
    def tick(self,now=None):
        now=now or dt.datetime.now()
        for task in list(self.jobs):
            if not task.get('enabled') or task['mode']!='calendar':continue
            if task.get('end_date') and task['end_date']<now.date().isoformat():
                task.update(enabled=False,next_at='',last_state='已结束');task.pop('pending_missed',None);self.states[task['id']]='已结束';self.persist();continue
            if not task.get('next_at'):continue
            at=dt.datetime.fromisoformat(task['next_at'])
            if at.date().isoformat() in set(task.get('exception_dates',[]))|{task.get('skip_date','')}:
                nxt=next_calendar(task,now);task['next_at']=nxt.isoformat(timespec='seconds') if nxt else '';task['enabled']=nxt is not None;self.persist();continue
            if at>now:continue
            late=(now-at).total_seconds()
            if task.get('repeat','once')=='once':task['enabled']=False;task['next_at']=''
            else:
                nxt=next_calendar(task,now);task['next_at']=nxt.isoformat(timespec='seconds') if nxt else '';task['enabled']=nxt is not None
            self.states[task['id']]=('已加入队列' if late<=90 else '已错过，未执行') if not task['enabled'] else '等待 '+task['next_at'].replace('T',' ')
            if late>90:self._missed(task,at,now)
            else:
                for key in ('last_state','last_error','pending_missed'):task.pop(key,None)
            try:self.persist()
            except OSError as exc:
                task['enabled']=False;self.states[task['id']]='预约保存失败，未执行';self.log('预约保存失败，未执行',kind='error',detail=str(exc));continue
            if late<=90:self._dispatch(task)
    def _tick(self):
        if self.closed:return
        try:
            self.tick()
            self._resolve_pending()
            if self.app.tray:self.app.tray.refresh_status()
            win=getattr(self.app,'_advanced_win',None)
            if win and win.winfo_exists():win.refresh_status()
        except Exception as exc:self.log('高级任务检查失败',kind='error',detail=str(exc))
        try:self.app.root.after(1000,self._tick)
        except Exception:pass
