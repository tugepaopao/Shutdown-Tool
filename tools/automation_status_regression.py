"""Check failure states against the controller, without any system actions."""
import sys,datetime as dt
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'src'))
from automation import AutomationController
from automation_status import status
def fail(*a,**k):raise OSError('test save failure')
class Config(dict):
 def save(self):return True

def controller(task):
 c=AutomationController.__new__(AutomationController);c.states={};c.jobs=[task];c.tokens={'t':'token'};c.watchers={};c.closed=False;c.log=lambda *a,**k:None
 c.app=SimpleNamespace(enqueue_task=fail,cfg=Config(log_enabled=False));c.persist=lambda:None
 return c
task=dict(id='t',name='test',mode='calendar',action='message',enabled=False)
c=controller(task);c._dispatch(task)
assert status(task,c.states)[0]=='入队失败'
print('PASS enqueue failure is not reported as queued')
now=dt.datetime.now();task.update(enabled=True,repeat='once',next_at=(now-dt.timedelta(seconds=1)).isoformat())
c=controller(task);c.persist=fail;c.tick(now)
assert not task['enabled'] and status(task,c.states)[0]=='保存失败'
print('PASS calendar persistence failure stops dispatch and reports failure')
task.update(enabled=True,mode='network');c=controller(task);c.persist=fail
c.handle(dict(id='t',token='token',state='ready',error=''))
assert not task['enabled'] and status(task,c.states)[0]=='保存失败'
print('PASS condition persistence failure is not reported as queued')
task.update(enabled=True,mode='calendar',repeat='daily');c=controller(task);c._dispatch(task)
assert task['enabled'] and status(task,c.states)[0]=='入队失败'
print('PASS repeating task retains next schedule while reporting queue failure')
