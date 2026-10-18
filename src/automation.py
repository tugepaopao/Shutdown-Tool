"""独立预约/条件任务。到点转入现有队列，保留10秒可取消阶段。"""
import copy
import datetime as dt
import time
import uuid
import traceback
import run_log
import execution_journal as journal
from task_store import normalize,next_calendar
from transfer_monitor import TransferWatcher
from condition_jobs import CombinedWatcher,ChainWatcher
ADVANCED_MODES=('calendar','download','network','combined','chain')

class AutomationController:
    def __init__(self,app):
        self.app=app;self.jobs=[];self.watchers={};self.tokens={};self.states={};self.closed=False
        self.reload()
        self._handoffs=[]
        if hasattr(app,'task_queue'):
            try:self._handoffs=journal.reconcile(app)
            except OSError as exc:self._report('handoff-recovery','预约恢复失败',exc)
        self._handoff_candidates=list(self._handoffs)
        for token in self._handoffs:
            row=next(r for r in journal.records(app) if r['id']==token)
            identifier=row['task'].get('source_automation',row['task'].get('id'))
            if identifier:self.states[identifier]='中断预约待确认：'+row.get('updated','')
        self.app.root.after(1000,self._tick)
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
                for key in ('pending_missed','last_state','last_error','last_consumed_at'):
                    if isinstance(raw.get(key),str):task[key]=raw[key]
                if task.get('last_state'):self.states[task['id']]=task['last_state']
                self.jobs.append(task)
                if task['enabled']:self._arm(task,restoring=True)
                if task!=raw:restore_changed=True
            except Exception as exc:self.log('跳过无效高级任务',kind='error',detail=traceback.format_exc())
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
    def close(self):self.closed=True;self.stop_watchers();run_log.flush_errors(force=True)
    def _arm(self,task,restoring=False):
        if task['mode']=='chain' and restoring:
            task['enabled']=False;task['next_at']='';self.states[task['id']]='重开后需重新启用任务链'
            self.log('任务链未自动重新运行：'+task['name']);return
        if task['mode']=='calendar':
            now=dt.datetime.now()
            consumed=self._consumed(task)
            try:at=dt.datetime.fromisoformat(task.get('next_at',''))
            except (ValueError,TypeError):at=None
            if at is None or at<=now or at.date().isoformat()==task.get('skip_date'):
                if restoring and at is not None and at<=now and at.date().isoformat() not in set(task.get('exception_dates',[]))|{task.get('skip_date','')}:
                    self._missed(task,at,now)
                at=next_calendar(task,max(now,consumed) if consumed else now)
            if at and consumed and at<=consumed:at=next_calendar(task,max(now,consumed))
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
        consumed=self._consumed(task)
        at=next_calendar(task,max(dt.datetime.now(),consumed) if consumed else None) if enabled and task['mode']=='calendar' else None
        if enabled and task['mode']=='calendar' and at is None:raise ValueError('该日期已过去，请修改日期')
        if enabled:
            from task_capabilities import validate
            validate(task)
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
            occurrence=journal.prepare(self.app,task) if state=='ready' else None
            try:self.persist()
            except OSError as exc:self.states[identifier]='监控结果保存失败，未执行';self.log('监控结果保存失败，未执行',kind='error',detail=traceback.format_exc());return
            if state=='ready':self._dispatch(task,occurrence)
            else:self.log(self.states[identifier]+'：'+task['name'],kind='error',detail=payload.get('error',''))
    def _dispatch(self,task,occurrence=None):
        queued={k:v for k,v in task.items() if k in ('action','name','close_program_path','program_path','sound_file','message_text','force_close_apps')}
        queued.update(mode='countdown',seconds=10,source_automation=task['id'])
        try:
            from task_capabilities import validate
            validate(task)
            token=journal.prepare(self.app,queued,occurrence)
            queued['occurrence_id']=token
            journal.mark(self.app,token,'pending')
            self.app.enqueue_task(queued,start=True)
            journal.mark(self.app,token,'queued')
        except (ValueError,OSError) as exc:
            self.states[task['id']]='加入队列失败，未执行'
            task['last_state']=self.states[task['id']]
            task['last_error']=str(exc)[:2000]
            try:self.persist()
            except OSError:pass
            self.log('高级任务未能加入队列：'+task['name'],kind='error',detail=traceback.format_exc());return
        self.log('高级任务到点，加入队列（含10秒可取消）：'+task['name'])
    def _missed(self,task,at,now=None):
        now=now or dt.datetime.now()
        consumed=self._consumed(task)
        task['last_consumed_at']=max(at,consumed).isoformat(timespec='seconds') if consumed else at.isoformat(timespec='seconds')
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
            consumed=self._consumed(task)
            nxt=next_calendar(task,max(now,consumed) if consumed else now);task.update(enabled=nxt is not None,next_at=nxt.isoformat(timespec='seconds') if nxt else '')
        occurrence=task['id']+':'+old['pending_missed']
        if execute:journal.prepare(self.app,task,occurrence)
        task['last_state']='已加入队列' if execute else '已错过，未执行'
        try:self.persist()
        except OSError:
            task.clear();task.update(old);raise
        self.states[identifier]=task['last_state']
        self._startup_pending.discard(identifier)
        if execute:self._dispatch(task,occurrence)
    def _grab_active(self):
        """Return whether Tk owns a grab without resolving native popup names.

        ttk comboboxes create a temporary Tcl window named ``popdown``.  Using
        ``grab_current`` asks tkinter to turn that native window into a Python
        widget and can raise ``KeyError('popdown')`` even though nothing is
        wrong with the scheduled task.
        """
        from ui_focus import has_grab
        try:
            return has_grab(self.app.root)
        except Exception:
            # A disappearing popup still means the UI is busy for this pass.
            return True
    def _resolve_pending(self):
        task=next((t for t in self.jobs if t.get('pending_missed') and t['id'] in getattr(self,'_startup_pending',set())),None)
        if not task:return
        if getattr(self,'_asking_missed',False) or self._grab_active():return
        if task.get('missed_policy')=='run':
            try:self.resolve_missed(task['id'],True)
            except OSError as exc:
                self._startup_pending.discard(task['id']);task['last_error']=str(exc);self.log('预约保存失败，未执行',kind='error',detail=traceback.format_exc())
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
            if self.closed or not task or self._grab_active():return
            text=feature_text(self.app.T,'任务“{name}”错过了 {at}。是否补执行一次？加入队列后保留10秒取消时间。').format(name=task['name'],at=task['pending_missed'].replace('T',' '))
            execute=messagebox.askyesno(feature_text(self.app.T,'错过的预约'),text,parent=self.app.root)
            self.resolve_missed(task['id'],execute)
        except OSError as exc:
            self._startup_pending.discard(identifier)
            if task:task['last_error']=str(exc)
            self.log('预约保存失败，未执行',kind='error',detail=traceback.format_exc())
        except Exception as exc:
            self._report('recovery-dialog','界面刷新异常：错过任务确认',exc,'ui_error')
        finally:self._asking_missed=False
    def tick(self,now=None):
        now=now or dt.datetime.now()
        for task in list(self.jobs):
            scope='calendar:'+str(task.get('id'))
            try:self._check_task(task,now);run_log.recovered(scope)
            except Exception as exc:self._report(scope,'预约检查异常：'+str(task.get('name','')),exc)

    @staticmethod
    def _consumed(task):
        try:return dt.datetime.fromisoformat(task.get('last_consumed_at',''))
        except (ValueError,TypeError):return None

    def _check_task(self,task,now):
        if not task.get('enabled') or task['mode']!='calendar':return
        if task.get('end_date') and task['end_date']<now.date().isoformat():
            task.update(enabled=False,next_at='',last_state='已结束');task.pop('pending_missed',None);self.states[task['id']]='已结束';self.persist();return
        if not task.get('next_at'):return
        at=dt.datetime.fromisoformat(task['next_at']);consumed=self._consumed(task)
        if (consumed and at<=consumed) or at.date().isoformat() in set(task.get('exception_dates',[]))|{task.get('skip_date','')}:
            nxt=next_calendar(task,max(now,consumed) if consumed else now)
            task.update(next_at=nxt.isoformat(timespec='seconds') if nxt else '',enabled=nxt is not None);self.persist();return
        if at>now:return
        late=(now-at).total_seconds()
        # Persist occurrence consumption before dispatch. A backward wall-clock
        # jump, restart or manual re-enable cannot enqueue this occurrence twice.
        occurrence=task['id']+':'+at.isoformat(timespec='seconds')
        if late<=90:journal.prepare(self.app,task,occurrence)
        task['last_consumed_at']=at.isoformat(timespec='seconds')
        nxt=next_calendar(task,now) if task.get('repeat','once')!='once' else None
        task.update(enabled=nxt is not None,next_at=nxt.isoformat(timespec='seconds') if nxt else '')
        self.states[task['id']]=('已加入队列' if late<=90 else '已错过，未执行') if not nxt else '等待 '+task['next_at'].replace('T',' ')
        if late>90:self._missed(task,at,now)
        else:
            for key in ('last_state','last_error','pending_missed'):task.pop(key,None)
        try:self.persist()
        except OSError as exc:
            task['enabled']=False;self.states[task['id']]='预约保存失败，未执行'
            self._report('persist:'+task['id'],'预约保存失败，未执行',exc);return
        if late<=90:self._dispatch(task,occurrence)
        elif task.get('pending_missed'):self._startup_pending.add(task['id'])

    def _report(self,scope,text,exc,kind='scheduler_error'):
        if self.app.cfg.get('log_enabled',True):run_log.exception(scope,text,exc,kind)

    def _stage(self,scope,text,callback,kind='scheduler_error'):
        try:callback();run_log.recovered(scope)
        except Exception as exc:self._report(scope,text,exc,kind)

    def review_handoffs(self):
        queued={t.get('occurrence_id') for t in self.app.task_queue}
        states={r['id']:r.get('state') for r in journal.records(self.app)}
        self._handoffs=[t for t in getattr(self,'_handoff_candidates',[]) if states.get(t) not in journal.TERMINAL and t not in queued]
        self._resolve_handoff()
    def _resolve_handoff(self):
        if not getattr(self,'_handoffs',[]) or getattr(self,'_handoff_asking',False) or self._grab_active():return
        self._handoff_asking=True
        self.app.root.after_idle(self._ask_handoff)
    def _ask_handoff(self):
        try:self._show_handoff()
        finally:self._handoff_asking=False
    def _show_handoff(self):
        from ui_localize import messagebox
        token=self._handoffs[0];row=next((r for r in journal.records(self.app) if r['id']==token),None)
        if row is None:self._handoffs.pop(0);return
        choice=messagebox.askyesnocancel('预约需确认',f"预约“{row['task'].get('name','未命名')}”上次运行被中断。\n状态：{ {'pending':'尚未确认入队','queued':'已记录入队','submitting':'操作提交期间中断'}.get(row.get('state'),'需确认') }，无法确认是否已执行。\n是否重新加入队列？重新加入后需手动开始。",parent=self.app.root,default='cancel',labels={'yes':'重新加入队列','no':'不再执行','cancel':'下次启动处理'})
        if choice is not None:
            journal.resolve(self.app,token,choice)
            identifier=row['task'].get('source_automation',row['task'].get('id'))
            if identifier:self.states[identifier]='已加入队列' if choice else '已停用'
        self._handoffs.pop(0)
    def _tick(self):
        if self.closed:return
        self._stage('handoff','预约恢复处理异常',self._resolve_handoff)
        self._stage('scheduler','预约检查异常',self.tick)
        self._stage('recovery','错过任务处理异常',self._resolve_pending)
        if self.app.tray:self._stage('tray','界面刷新异常：系统托盘',self.app.tray.refresh_status,'ui_error')
        def refresh_window():
            win=getattr(self.app,'_advanced_win',None)
            if win and win.winfo_exists() and win.winfo_viewable():win.refresh_status()
        self._stage('task-center','界面刷新异常：任务中心',refresh_window,'ui_error')
        run_log.flush_errors()
        try:self.app.root.after(1000 if any(t.get('enabled') or t.get('pending_missed') for t in self.jobs) else 5000,self._tick)
        except Exception:pass
