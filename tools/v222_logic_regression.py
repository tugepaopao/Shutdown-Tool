"""New behavior tests with isolated data, no real actions or installation."""
import sys,os,tempfile,time,json,threading,io,hashlib
from pathlib import Path
from unittest.mock import patch
p=Path(__file__).resolve().parents[1];sys.path[:0]=[str(p/'src'),str(p/'tools')]
tmp=tempfile.TemporaryDirectory();os.environ['APPDATA']=tmp.name
from main import enable_dpi_awareness
enable_dpi_awareness()
import ui_main,autostart,release_update as updates
ui_main.App._init_tray=lambda a:None;autostart.set_enabled=lambda *a:True
ui_main.perform=lambda *a,**k:(_ for _ in ()).throw(AssertionError('No real action'))
checks=[]
def check(name,value):
    assert value,name
    checks.append(name)
def pump(a,n=.1):
    end=time.monotonic()+n
    while time.monotonic()<end:a.root.update();time.sleep(.003)
a=ui_main.App({'given':True,'action':'message'});a.perform_action=lambda *a,**k:None
errors=[];a.root.report_callback_exception=lambda t,v,b:errors.append(str(v))
try:
    pump(a,.3);a.cd_days.set('0');a.cd_h.set('0');a.cd_m.set('30');a.cd_s.set('0');a.start_timer();pump(a)
    check('status names running action','计时中' in a.summary_title.cget('text') and '弹出提示' in a.summary_title.cget('text'))
    check('remaining and due shown','剩余' in a.status.cget('text') and '预计' in a.status.cget('text'))
    gen=a.engine.generation
    with patch('ui_localize.messagebox.askyesnocancel',return_value=None):a.start_timer()
    check('cancel preserves generation',a.engine.generation==gen)
    a.cd_m.set('20')
    with patch('ui_localize.messagebox.askyesnocancel',return_value=False):a.start_timer()
    check('queue preserves current',a.engine.generation==gen and len(a.task_queue)==1 and a.task_queue[0]['seconds']==1200)
    a._save_pending_timer();check('queue continuation persisted',a.cfg['pending_timer']['continue_queue'])
    # Simulate this generation completing without invoking any OS action.
    with a.engine._lock:a.engine._alive=False
    a._handle('finished',{'gen':gen,'repeat':False});pump(a,1.4)
    check('direct task hands off queued task',a.engine.is_running() and a._active_task['seconds']==1200)
    a.cd_m.set('10');old=a._active_task
    with patch('ui_localize.messagebox.askyesnocancel',return_value=True):a.start_timer()
    check('replace does not rerun old queued item',old not in a.task_queue and a._active_task['seconds']==600)
    a.toggle_pause();pump(a)
    check('paused has no misleading due','已暂停' in a.summary_title.cget('text') and '预计' not in a.status.cget('text'))
    def changed(*args,**kw):a.engine.stop();return True
    with patch('ui_localize.messagebox.askyesnocancel',side_effect=changed),patch('ui_localize.messagebox.showinfo'):
        a.start_timer()
    check('stale modal never replaces new state',not a.engine.is_running())
    from ui_messagebox import MessageDialog
    d=MessageDialog(a.root,'已有任务正在运行','替换当前任务、加入队列或取消。','askyesnocancel',labels={'yes':'替换当前任务','no':'加入队列','cancel':'取消'})
    pump(a);from capture_window import capture
    out=p/'核验/v222';out.mkdir(exist_ok=True);capture(d).save(out/'start-choice.png');d.destroy()
    from ui_release_update import UpdateWindow
    with patch('release_update.check',return_value=None):
        u=UpdateWindow(a,a.root);pump(a,.4)
        check('update latest feedback','暂无更新' in u.label.cget('text'));capture(u).save(out/'update.png');u.destroy()
    check('no UI callback exceptions',not errors)
finally:a.engine.stop();a.quit_app()

check('numeric version comparison',updates.version('v2.0.100')>updates.version('2.0.22'))
payload=b'MZ-test-only';sha=hashlib.sha256(payload).hexdigest()
release={'tag_name':'v2.0.23','draft':False,'prerelease':False,'body':'Test notes','assets':[{'name':'Shutdown-Tool-v2.0.23-Setup.exe','size':len(payload),'digest':'sha256:'+sha,'browser_download_url':updates.REPO+'/releases/download/v2.0.23/Shutdown-Tool-v2.0.23-Setup.exe'}]}
with patch.object(updates,'_bytes',return_value=json.dumps(release).encode()):
    item=updates.check('2.0.22');check('official new version selected',item['sha256']==sha)
    check('no downgrade',updates.check('2.0.24') is None)
with patch.object(updates,'_open',return_value=io.BytesIO(payload)):
    target=updates.download(item,threading.Event(),lambda *a:None)
    check('verified installer bytes',target.read_bytes()==payload);target.unlink();target.parent.rmdir()
with patch.object(updates,'_open',return_value=io.BytesIO(b'broken')):
    try:updates.download(item,threading.Event(),lambda *a:None);raise AssertionError('bad hash accepted')
    except ValueError:checks.append('corrupt download rejected')
cancel=threading.Event();cancel.set()
with patch.object(updates,'_open',return_value=io.BytesIO(payload)):
    try:updates.download(item,cancel,lambda *a:None);raise AssertionError('cancel ignored')
    except InterruptedError:checks.append('cancelled download removed')
check('external package rejected',not updates.official_asset('https://example.com/Setup.exe'))
from ui_anchor import bounds
for anchor in ((-1900,800,80,30),(3800,2000,30,30),(0,0,20,20)):
    areas=[(-1920,0,0,1040),(0,0,1920,1040),(1920,0,3840,2120)]
    x,y,w,h=bounds(anchor,800,700,areas)
    check('popup within workarea '+str(anchor),any(l<=x and t<=y and x+w<=r and y+h<=b for l,t,r,b in areas))
from shared_sampling import SamplingHub
hub=SamplingHub();reads=[]
def sample():reads.append(time.perf_counter());return {'bytes':1}
start=time.perf_counter();cpu=time.process_time();subs=[hub.subscribe(('network','test'),sample,.05) for _ in range(20)]
cancel=threading.Event()
for sub in subs:check('shared monitor receives sample '+str(len(checks)),sub.read(cancel)[0]['bytes']==1)
time.sleep(.3)
metrics={'subscribers':len(subs),'raw_samples':len(reads),'cpu_seconds':time.process_time()-cpu,'elapsed_ms':(time.perf_counter()-start)*1000}
check('20 monitors share one source',len(hub.sources)==1 and len(reads)<10)
for sub in subs:sub.close()
check('sampler released',not hub.sources)
(p/'核验/v222/logic.json').write_text(json.dumps(dict(checks=checks,errors=errors,sampling=metrics),ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(passed=len(checks),sampling=metrics),ensure_ascii=False))
