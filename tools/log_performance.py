"""Compare 500-row log opening, unchanged refresh and filter latency."""
import os,sys,tempfile,time,json,statistics
from pathlib import Path
p=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(p/'src'))
temp=tempfile.TemporaryDirectory(prefix='shutdown-perf-');os.environ['APPDATA']=temp.name
from main import enable_dpi_awareness
enable_dpi_awareness()
import actions,autostart,run_log
from ui_main import App
App._init_tray=lambda a:None;autostart.set_enabled=lambda *a:True;actions.perform=lambda *a,**k:None
a=App({'given':True,'action':'message'});a.cfg.update(dict(confirm_on_exit=False,autostart=False));a.root.update()
records=[dict(ts=f'2026-10-{i%28+1:02d} 08:20:30',kind='error' if i%10==0 else 'done',text='演示任务 '+str(i),detail='示例详情 '*40) for i in range(500)]
Path(run_log.log_file()).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),encoding='utf-8')
def timed(fn):
 start=time.perf_counter();fn();a.root.update_idletasks();return round((time.perf_counter()-start)*1000,2)
try:
 result={'open_500_ms':timed(a.open_log)};w=a._log_win;a.root.update()
 result['unchanged_refresh_median_ms']=statistics.median(timed(w.refresh) for _ in range(15))
 times=[]
 for value in ('演示任务 1','演示任务 2','','不存在')*4:
  w.query.set(value);times.append(timed(w.refresh))
 result['filter_median_ms']=statistics.median(times);result['filter_max_ms']=max(times)
 out=p/'核验/v208';out.mkdir(parents=True,exist_ok=True);(out/('logs-'+sys.argv[1]+'.json')).write_text(json.dumps(result,indent=2),encoding='utf-8');print(result)
finally:
 a.engine.stop();a.automation.close();a.floating.close();a.desktop.close();a.display_awake.close();a.root.destroy();temp.cleanup()
