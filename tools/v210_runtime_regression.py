"""Isolated clock, error aggregation, log IO and shared sampler regressions."""
import os,sys,tempfile,datetime as dt,copy,threading,time,json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
p=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(p/'src'));sys.stdout.reconfigure(encoding='utf-8')
tmp=tempfile.TemporaryDirectory(prefix='shutdown-v210-runtime-');os.environ['APPDATA']=tmp.name
from automation import AutomationController
import run_log
from task_store import normalize
from shared_sampling import SamplingHub,hub
from transfer_monitor import TransferWatcher,QuietDetector
from condition_jobs import CombinedWatcher
checks=[]
def check(name,ok):
    assert ok,name
    checks.append(name);print('PASS '+name,flush=True)
class Config(dict):
    def save(self):return True
def controller(jobs):
    c=AutomationController.__new__(AutomationController)
    c.jobs=copy.deepcopy(jobs);c.states={};c.tokens={};c.watchers={};c.closed=False;c._startup_pending=set()
    sent=[];callbacks=[]
    root=SimpleNamespace(grab_current=lambda:None,winfo_viewable=lambda:True,after_idle=callbacks.append,after=lambda *a:None)
    c.app=SimpleNamespace(root=root,cfg=Config(automations=copy.deepcopy(jobs)),tray=None,enqueue_task=lambda task,start:sent.append(copy.deepcopy(task)),T=SimpleNamespace(lang='CHS'))
    return c,sent,callbacks
def job(i='a',policy='skip',repeat='daily'):
    t=normalize(dict(name=i,action='message',mode='calendar',at='2026-10-20T14:30:00',repeat=repeat,missed_policy=policy))
    t.update(id=i,enabled=True,next_at=t['at']);return t

at=dt.datetime(2026,10,20,14,30)
for policy in ('skip','ask','run'):
    c,sent,callbacks=controller([job(policy=policy)])
    c.tick(at+dt.timedelta(hours=4))
    check(policy+' missed execution is persisted before recovery',not sent and c.jobs[0]['last_consumed_at']==at.isoformat())
    c._resolve_pending()
    check(policy+' live recovery without application restart',len(callbacks)==(policy=='ask') and len(sent)==(policy=='run'))
    if callbacks:
        from ui_localize import messagebox
        with patch.object(messagebox,'askyesno',return_value=True):callbacks.pop()()
    c._resolve_pending()
    check(policy+' recovery coalesces to one dispatch',len(sent)==(policy!='skip'))

c,sent,_=controller([job(str(i)) for i in range(5)])
c.tick(at);c.tick(at);c.tick(at-dt.timedelta(hours=2));c.tick(at)
check('five simultaneous tasks each dispatch once through backward clock jump',len(sent)==5 and len({x['source_automation'] for x in sent})==5)
c.tick(at+dt.timedelta(days=1));check('next daily occurrence still executes',len(sent)==10)
saved=copy.deepcopy(c.app.cfg['automations']);restarted,again,_=controller(saved)
restarted.tick(at);restarted.tick(at+dt.timedelta(days=1))
check('persisted occurrence guard survives controller recreation',not again)
c,sent,_=controller([job(repeat='once')]);c.tick(at);c.tick(at+dt.timedelta(days=1));check('once remains consumed',len(sent)==1 and not c.jobs[0]['enabled'])
c,sent,_=controller([job()]);c.app.cfg.save=lambda:False;c.tick(at);check('save failure never dispatches',not sent)
bad=job('bad');bad['next_at']='invalid';c,sent,_=controller([bad,job('valid')]);c.tick(at)
check('invalid task does not block a valid due task',len(sent)==1 and sent[0]['source_automation']=='valid')
c,sent,_=controller([job()]);c.jobs[0]['next_at']=at.isoformat();c.jobs[0]['last_consumed_at']=at.isoformat();c.tick(at)
check('stale next_at cannot replay consumed occurrence',not sent and c.jobs[0]['next_at']>at.isoformat())

run_log.clear();c,sent,_=controller([])
def fail_ui():raise KeyError('popdown')
def fail_schedule():raise ValueError('invalid clock record')
c.app._advanced_win=SimpleNamespace(winfo_exists=lambda:True,winfo_viewable=lambda:True,refresh_status=fail_ui)
c.tick=fail_schedule
for _ in range(5):c._tick()
rows=run_log.entries(0)
check('UI and scheduling failures remain separate categories',set(r['kind'] for r in rows)=={'ui_error','scheduler_error'})
check('repeated error episodes aggregate exact counts',len(rows)==2 and all(r['count']==5 for r in rows))
check('full traceback retained',all('Traceback' in r['detail'] and 'v210_runtime_regression.py' in r['detail'] for r in rows))
c.tick=lambda:None;c.app._advanced_win.refresh_status=lambda:None;c._tick()
c.app._advanced_win.refresh_status=fail_ui;c._tick();rows=run_log.entries(0)
check('a new failure after recovery begins a new episode',len(rows)==3 and rows[-1]['count']==1)
run_log.clear();check('clear removes pending aggregates',not run_log.entries(0))
original_trim=run_log._trim
with patch.object(run_log,'_trim',wraps=original_trim) as trim:
    for i in range(1000):run_log.add('info',str(i))
    check('1000 writes perform at most 21 retention reads',trim.call_count<=21)
check('retention preserves newest 500 entries',len(run_log.entries(500))==500 and run_log.entries(1)[0]['text']=='999')
run_log.clear();run_log.add('info','fresh');check('append works after clear',len(run_log.entries(0))==1)

samplers=SamplingHub();calls=[];cancel=threading.Event()
def read():calls.append(1);return {'nic':len(calls)*1024}
sub1=samplers.subscribe(('test',),read,.05);sub2=samplers.subscribe(('test',),read,.05)
first=sub1.read(cancel);second=sub2.read(cancel)
check('two subscribers share one raw sample',len(calls)==1 and first==second)
first[0]['nic']=0;check('subscribers cannot modify each others snapshots',second[0]['nic']==1024)
sub1.close();second=sub2.read(cancel);check('stopping one subscriber retains other sampler',second[0]['nic']>1024)
source=sub2.source;sub2.close();source.thread.join(1);check('last unsubscribe stops worker and releases resource',not source.thread.is_alive() and not samplers.sources)
def broken():raise OSError('network disconnected')
s1=samplers.subscribe(('broken',),broken);s2=samplers.subscribe(('broken',),broken)
failures=0
for sub in (s1,s2):
    try:sub.read(cancel)
    except OSError:failures+=1
    finally:sub.close()
check('sampling failure reaches every subscriber',failures==2)
lo=QuietDetector(dict(mode='network',threshold_kib=1,idle_seconds=2,timeout_seconds=30),0)
hi=QuietDetector(dict(mode='network',threshold_kib=10,idle_seconds=2,timeout_seconds=30),0)
for detector in (lo,hi):detector.update({'nic':0},0)
check('threshold decisions are task-local',lo.update({'nic':5*1024},1)=='active' and hi.update({'nic':5*1024},1)=='waiting')
for detector in (lo,hi):detector.update({'nic':5*1024},2)
check('shared quiet input does not trigger an inactive task',lo.update({'nic':5*1024},4)=='ready' and hi.update({'nic':5*1024},4)=='waiting')

events=[[],[],[]];reads=[]
def shared_network():reads.append(1);return {'nic':100}
task=dict(mode='network',threshold_kib=1,idle_seconds=2,timeout_seconds=30)
with patch('transfer_monitor.network_sample',shared_network),patch('condition_jobs.network_sample',shared_network):
    watchers=[TransferWatcher(task,lambda state,error,i=i:events[i].append(state),interval=.05).start() for i in range(2)]
    watchers.append(CombinedWatcher(dict(task,user_idle_seconds=60),lambda state,error:events[2].append(state),idle=lambda:0,interval=.05).start())
    time.sleep(.22)
    for watcher in watchers:watcher.stop()
    for watcher in watchers:watcher.thread.join(1)
check('transfer and combined monitors share network sampling',len(reads)<=7 and all(e==['waiting'] for e in events))
check('watchers release all shared sources',not hub.sources)
folder_events=[[],[]];folder_reads=[]
def shared_folder(path):folder_reads.append(path);return (('file.zip',1024,1),),False
folder=str(Path(tmp.name)/'downloads')
with patch('transfer_monitor.folder_sample',shared_folder):
    watchers=[TransferWatcher(dict(mode='download',folder=folder if i==0 else folder+'/../downloads',idle_seconds=2,timeout_seconds=30),lambda state,error,i=i:folder_events[i].append(state),interval=.05).start() for i in range(2)]
    time.sleep(.18)
    for watcher in watchers:watcher.stop()
    for watcher in watchers:watcher.thread.join(1)
check('equivalent folder paths share scans and suppress duplicate states',len(folder_reads)<=6 and all(e==['waiting'] for e in folder_events))
check('folder subscriptions release after stopping',not hub.sources)
samplers=SamplingHub();x=samplers.subscribe(('folder','a'),lambda:1);y=samplers.subscribe(('folder','b'),lambda:2)
check('different folders retain independent samplers',x.read(cancel)[0]==1 and y.read(cancel)[0]==2)
x.close();y.close()
failure_events=[[],[]]
with patch('transfer_monitor.network_sample',side_effect=OSError('lost interface')):
    watchers=[TransferWatcher(task,lambda state,error,i=i:failure_events[i].append(state),interval=.05).start() for i in range(2)]
    for watcher in watchers:watcher.thread.join(1)
check('shared read failure stops tasks without reporting ready',all(e==['error'] for e in failure_events) and not hub.sources)
from task_store import export_csv
run_log.clear()
for _ in range(3):
    try:raise RuntimeError('same exception')
    except RuntimeError as exc:run_log.exception('test','界面刷新异常',exc,'ui_error')
rows=run_log.entries(0);csv_path=Path(tmp.name)/'log.csv';export_csv(csv_path,rows)
check('CSV retains coalesced counts and full details','累计出现 3 次' in csv_path.read_text(encoding='utf-8-sig') and 'Traceback' in csv_path.read_text(encoding='utf-8-sig'))
out=p/'核验/v210';out.mkdir(parents=True,exist_ok=True)
(out/'runtime.json').write_text(json.dumps(dict(checks=checks,passed=len(checks)),ensure_ascii=False,indent=2),encoding='utf-8')
tmp.cleanup();print(str(len(checks))+' checks passed')
