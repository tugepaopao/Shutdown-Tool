"""No real power actions; crash-boundary and local capability regressions."""
import sys,os,tempfile,copy,json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
p=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(p/'src'))
tmp=tempfile.TemporaryDirectory();os.environ['APPDATA']=tmp.name
import execution_journal as j
from display_awake import DisplayAwake,ES_CONTINUOUS,ES_SYSTEM_REQUIRED,ES_DISPLAY_REQUIRED
from task_capabilities import validate
from ui_anchor import bounds
from task_store import normalize,export_backup
from config_backups import portable
from actions import _shutdown_result
checks=[]
def check(name,condition):
    assert condition,name
    checks.append(name);print('PASS',name,flush=True)
class Config(dict):
    def save(self):self.saved=copy.deepcopy(dict(self));return True
cfg=Config();app=SimpleNamespace(cfg=cfg,task_queue=[])
app._save_queue=lambda:cfg.update(queue=copy.deepcopy(app.task_queue))
def enqueue(task,start):
    old=next((t for t in app.task_queue if t.get('occurrence_id')==task.get('occurrence_id')),None)
    if old:return old
    app.task_queue.append(copy.deepcopy(task));app._save_queue();cfg.save()
app.enqueue_task=enqueue
task=dict(id='job',name='恢复测试',mode='calendar',at='2026-11-01T22:00:00',action='message',message_text='test')
token=j.prepare(app,task,'job:2026-11-01');cfg.save()
check('crash before enqueue requires confirmation',j.reconcile(app)==[token] and not app.task_queue)
j.resolve(app,token,True)
check('confirmed recovery is queued once without automatic start',len(app.task_queue)==1 and j.records(app)[0]['state']=='queued')
check('queued occurrence survives restart without extra enqueue',j.reconcile(app)==[] and len(app.task_queue)==1)
j.mark(app,token,'submitting');cfg['pending_timer']=dict(occurrence_id=token)
check('unknown submission removed from automatic queue recovery',j.reconcile(app)==[token] and not app.task_queue and not cfg['pending_timer'])
j.resolve(app,token,False)
check('declined recovery remains consumed',j.reconcile(app)==[])
token=j.prepare(app,task,'second');j.mark(app,token,'queued');enqueue(dict(task,occurrence_id=token),False)
j.cancel_in_memory(app,app.task_queue);app.task_queue.clear();cfg.save()
check('intentional deletion does not prompt recovery',j.reconcile(app)==[])
token=j.prepare(app,task,'third');j.mark(app,token,'submitted');enqueue(dict(task,occurrence_id=token),False)
check('completed handoff cannot replay stale queue',j.reconcile(app)==[] and not app.task_queue)
cfg.save=lambda:False
try:j.mark(app,token,'submitting');raise AssertionError('expected failure')
except OSError:check('journal save failure rolls back in-memory state',j.records(app)[-1]['state']=='submitted')
cfg.save=lambda:True
check('automatic backup excludes execution journal','execution_journal' not in portable(cfg)['settings'])
out=Path(tmp.name)/'backup.json';export_backup(cfg,out)
check('manual backup excludes execution journal','execution_journal' not in json.loads(out.read_text(encoding='utf-8'))['settings'])
calls=[];awake=DisplayAwake(SimpleNamespace(bind=lambda *a,**k:None),api=lambda f:calls.append(f) or 1)
awake.set_task_active(True)
check('task awake permits display sleep',calls[-1]==ES_CONTINUOUS|ES_SYSTEM_REQUIRED)
awake.set_task_active(True);check('unchanged power request makes no API call',len(calls)==1)
awake.set_enabled(True);awake.set_task_active(False)
check('manual display awake survives task completion',calls[-1]==ES_CONTINUOUS|ES_SYSTEM_REQUIRED|ES_DISPLAY_REQUIRED)
awake.set_enabled(False);check('last power request released',calls[-1]==ES_CONTINUOUS)
awake.set_task_active(True);awake.close();check('exit releases task power request',calls[-1]==ES_CONTINUOUS)
for data,label in [(dict(action='run_program',program_path='Z:/missing/task.exe'),'missing executable'),(dict(action='message',mode='download',folder='Z:/missing'),'missing folder')]:
    try:validate(data);raise AssertionError(label)
    except ValueError:check(label+' rejected before execution',True)
with patch('task_capabilities.hibernate_available',return_value=False):
    try:validate(dict(action='hibernate'));raise AssertionError('hibernate')
    except ValueError:check('unavailable hibernate rejected',True)
check('shutdown timeout is explicitly unconfirmed','结果未确认' in _shutdown_result(None)[1])
check('shutdown rejection remains failure',_shutdown_result(5)[0] is False)
x,y,w,h=bounds((1800,950,34,34),380,480,[(0,0,1920,1080)])
check('popup flips above at lower edge',y<950 and x+w<=1920 and y+h<=1080)
x,y,w,h=bounds((-1700,100,34,34),380,480,[(-1920,0,0,1080),(0,0,1920,1080)])
check('popup stays on negative-coordinate monitor',-1920<=x and x+w<=0)
from transfer_monitor import QuietDetector
d=QuietDetector(dict(mode='network',timeout_seconds=1000,idle_seconds=10,threshold_kib=1),now=0)
d.update({'nic':0},0);d.update({'nic':100000},1);d.update({'nic':100000},2)
check('sleep gap cannot masquerade as quiet completion',d.update({'nic':100000},100)=='waiting')
out=p/'核验/v211';out.mkdir(parents=True,exist_ok=True)
(out/'runtime.json').write_text(json.dumps(dict(passed=len(checks),checks=checks),ensure_ascii=False,indent=2),encoding='utf-8')
print(len(checks),'checks passed')
