"""Read-only system metrics; no Tk calls from the sampling thread."""
import os,time,queue,threading
import psutil

def rate(current,previous,elapsed):
    return max(0,current-previous)/elapsed if elapsed>0 and current>=previous else 0.0

def size(value):
    value=float(value)
    for unit in ('B','KiB','MiB','GiB','TiB'):
        if abs(value)<1024 or unit=='TiB':return f'{value:.1f} {unit}'
        value/=1024

class Sampler:
    def __init__(self):self.stop_event=threading.Event();self.results=queue.Queue(maxsize=1);self.drive=os.environ.get('SystemDrive','C:')+'\\';self.thread=None
    def start(self):
        if self.thread and self.thread.is_alive():return
        self.stop_event=threading.Event();self.thread=threading.Thread(target=self._run,daemon=True,name='ShutdownMetrics');self.thread.start()
    def close(self):self.stop_event.set()
    def _run(self):
        previous=None;clock=None;psutil.cpu_percent(None)
        while not self.stop_event.is_set():
            result={};now=time.monotonic()
            for key,fn in [('cpu',lambda:psutil.cpu_percent(None)),('memory',psutil.virtual_memory),('disk',lambda:psutil.disk_usage(self.drive)),('uptime',lambda:max(0,time.time()-psutil.boot_time()))]:
                try:result[key]=fn()
                except (OSError,psutil.Error):result[key]=None
            try:
                net=psutil.net_io_counters(pernic=True)
                common=set(net)&set(previous or {})
                result['download']=sum(rate(net[k].bytes_recv,previous[k].bytes_recv,now-clock) for k in common) if previous is not None else None
                result['upload']=sum(rate(net[k].bytes_sent,previous[k].bytes_sent,now-clock) for k in common) if previous is not None else None
                previous=net;clock=now
            except (OSError,psutil.Error,AttributeError):result['download']=result['upload']=None;previous=None;clock=None
            result['drive']=self.drive
            try:self.results.get_nowait()
            except queue.Empty:pass
            self.results.put_nowait(result)
            if self.stop_event.wait(1):break
