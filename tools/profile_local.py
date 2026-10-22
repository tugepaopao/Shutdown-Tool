"""Isolated, non-destructive UI timings; never executes power actions."""
import os, sys, tempfile, time, json, cProfile, pstats, io, platform
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(p/'src'),str(p/'tools')]
tmp=tempfile.TemporaryDirectory();os.environ['APPDATA']=tmp.name
from main import enable_dpi_awareness
enable_dpi_awareness()
import ui_main, autostart
ui_main.App._init_tray=lambda a:None
autostart.set_enabled=lambda *a:True
ui_main.perform=lambda *a,**k:(_ for _ in ()).throw(AssertionError('Real action forbidden'))
start=time.perf_counter();a=ui_main.App({'given':True,'action':'message'})
def drain(seconds=.1):
    end=time.perf_counter()+seconds
    while time.perf_counter()<end:a.root.update();time.sleep(.002)
result={'os':platform.platform(),'startup_ms':(time.perf_counter()-start)*1000}
try:
    drain(.4)
    start=time.perf_counter();a.open_task_center();a.root.update();result['task_center_first_ms']=(time.perf_counter()-start)*1000
    result['tabs_ms']={}
    for key in ('templates','advanced','queue','templates','advanced'):
        start=time.perf_counter();a._task_center_win.select_tab(key);a.root.update()
        result['tabs_ms'].setdefault(key,[]).append((time.perf_counter()-start)*1000)
    a._task_center_win.destroy()
    start=time.process_time();drain(3);result['idle_cpu_seconds_per_3s']=time.process_time()-start
    a.cd_days.set('0');a.cd_h.set('0');a.cd_m.set('30');a.cd_s.set('0');a.start_timer()
    profiler=cProfile.Profile();profiler.enable();start=time.process_time();drain(3)
    result['timer_cpu_seconds_per_3s']=time.process_time()-start;profiler.disable()
    stream=io.StringIO();pstats.Stats(profiler,stream=stream).sort_stats('cumulative').print_stats(25)
    result['timer_profile']=stream.getvalue()
    a.engine.stop();a.root.withdraw();drain(.2)
    start=time.process_time();drain(3);result['background_idle_cpu_seconds_per_3s']=time.process_time()-start
finally:a.engine.stop();a.quit_app()
out=p/'核验'/('profile-'+sys.argv[1]+'.json');out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False))
