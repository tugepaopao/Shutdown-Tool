"""Deterministic recurrence, missed-run and persistence regression checks."""
import sys,datetime as dt,copy,tempfile
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'src'))
from task_store import normalize,next_calendar,export_backup,read_backup
from automation import AutomationController
from schedule_preview import schedule_preview
checks=[]
def check(name,condition):
    assert condition,name
    checks.append(name);print('PASS '+name)
def job(**kw):return normalize(dict(name='test',action='message',message_text='test',mode='calendar',at='2026-10-19T14:30:00',repeat='custom',weekdays=[0,2,4],**kw))
t=job();now=dt.datetime(2026,10,19,15)
check('custom weekdays skip Tuesday',next_calendar(t,now)==dt.datetime(2026,10,21,14,30))
t['exception_dates']=['2026-10-21','2026-10-23'];check('multiple excluded dates',next_calendar(t,now)==dt.datetime(2026,10,26,14,30))
t['end_date']='2026-10-23';check('end date exhausts recurrence',next_calendar(t,now) is None)
t['exception_dates']=[];check('end date includes last day',next_calendar(t,dt.datetime(2026,10,23,14))==dt.datetime(2026,10,23,14,30))
t.update(at='2028-02-28T14:30:00',repeat='daily',end_date='2028-03-01');check('leap day',next_calendar(t,dt.datetime(2028,2,28,15))==dt.datetime(2028,2,29,14,30))
t.update(at='2026-10-19T14:30:00',repeat='daily',end_date='2027-12-31',exception_dates=[(dt.date(2026,10,19)+dt.timedelta(days=i)).isoformat() for i in range(366)])
check('366 exclusions find next date',next_calendar(t,now)==dt.datetime(2027,10,20,14,30))
for change in (dict(weekdays=[]),dict(weekdays=[True]),dict(weekdays=[7]),dict(end_date='2026-10-01'),dict(exception_dates=['bad']),dict(missed_policy='bad')):
    try:normalize({**job(),**change})
    except ValueError:pass
    else:raise AssertionError(change)
check('invalid rules rejected',True)
t=normalize(dict(name='legacy',mode='calendar',action='message',at='2026-10-19T14:30:00',repeat='workdays'))
check('legacy policy defaults to skip',t['missed_policy']=='skip' and next_calendar(t,dt.datetime(2026,10,23,15)).weekday()==0)
t=job();t.update(id='t',enabled=True,end_date='2026-10-23',exception_dates=['2026-10-21'])
check('preview honors repeat exceptions and end',len(schedule_preview([t],dt.datetime(2026,10,19)))==2)
class Config(dict):
    def save(self):return True
def controller(task):
    c=AutomationController.__new__(AutomationController);c.states={};c.jobs=[task];c.tokens={};c.watchers={};c.closed=False;c._startup_pending=set()
    c.log=lambda *a,**k:None;sent=[]
    c.app=SimpleNamespace(cfg=Config(automations=[copy.deepcopy(task)]),enqueue_task=lambda task,start:sent.append(task),T=SimpleNamespace(lang='CHS'),root=SimpleNamespace(grab_current=lambda:None,winfo_viewable=lambda:True,after_idle=lambda fn:fn()))
    return c,sent
for policy in ('skip','ask','run'):
    t=job(missed_policy=policy);t.update(id='t',enabled=True,next_at='2026-10-19T14:30:00')
    c,sent=controller(t);c.tick(dt.datetime(2026,10,23,18))
    check(policy+' missed never directly executes',not sent)
    if policy!='skip':
        check(policy+' pending saved',bool(c.app.cfg['automations'][0].get('pending_missed')))
        c._resolve_pending();check(policy+' waits for reopening',not sent and 'pending_missed' in t)
        c.resolve_missed('t',True,dt.datetime(2026,10,23,18));c.resolve_missed('t',True)
        check(policy+' coalesces to one cancellable run',len(sent)==1 and sent[0]['seconds']==10 and sent[0]['source_automation']=='t')
    else:check('skip advances without catchup',t['next_at']=='2026-10-26T14:30:00')
t=job(missed_policy='run');t.update(id='t',enabled=True,next_at='2026-10-19T14:30:00',end_date='2026-10-20')
c,sent=controller(t);c.tick(dt.datetime(2026,10,21));check('end date stops catchup',not sent and not t['enabled'] and 'pending_missed' not in t)
t=job(missed_policy='ask');t.update(id='t',enabled=False,pending_missed='2026-10-19T14:30:00')
c,sent=controller(t)
def fail():raise OSError('disk full')
c.persist=fail
try:c.resolve_missed('t',True)
except OSError:pass
check('pending resolution save failure cannot execute',not sent and t.get('pending_missed'))
with tempfile.TemporaryDirectory() as folder:
    from app_config import DEFAULT_SETTINGS
    path=Path(folder)/'backup.json';cfg=Config(copy.deepcopy(DEFAULT_SETTINGS));cfg.update(automations=[t],templates=[]);export_backup(cfg,path)
    restored=read_backup(path)[2][0]
    check('backup preserves rule but strips runtime decisions',restored['weekdays']==[0,2,4] and not restored['enabled'] and 'pending_missed' not in restored)
from unittest.mock import patch
from ui_localize import messagebox
for policy in ('skip','ask','run'):
    now=dt.datetime.now();past=now-dt.timedelta(days=2)
    t=normalize(dict(name='restart',mode='calendar',action='message',message_text='test',at=past.isoformat(),repeat='daily',missed_policy=policy))
    t.update(id='t',enabled=True,next_at=past.isoformat());c,sent=controller(t);c.reload()
    check(policy+' startup recovery persisted before action',not sent and c.app.cfg['automations'][0]['next_at']>now.isoformat())
    with patch.object(messagebox,'askyesno',return_value=True) as prompt:
        c._resolve_pending();c._resolve_pending()
        check(policy+' startup policy dispatch count',len(sent)==(0 if policy=='skip' else 1))
        check(policy+' startup prompt count',prompt.call_count==(1 if policy=='ask' else 0))
t=normalize(dict(name='modal',mode='calendar',action='message',at=(dt.datetime.now()-dt.timedelta(days=1)).isoformat(),repeat='once',missed_policy='run'))
t.update(id='t',enabled=False,pending_missed=t['at']);c,sent=controller(t);c._startup_pending={'t'};c.app.root.grab_current=lambda:object();c._resolve_pending()
check('recovery waits for an open editor',not sent and t.get('pending_missed'))
t['missed_policy']='ask';c.app.root.grab_current=lambda:None;callbacks=[];c.app.root.after_idle=callbacks.append
c._resolve_pending();check('confirmation scheduled without blocking scheduler',len(callbacks)==1 and not sent)
with patch.object(messagebox,'askyesno',return_value=False):callbacks[0]()
check('declining recovery consumes pending decision',not t.get('pending_missed') and not sent)
print(str(len(checks))+' checks passed')
