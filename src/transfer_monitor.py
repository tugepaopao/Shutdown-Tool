"""后台只读监控。必须先观察到活动；超时/采样失败绝不触发动作。"""
import os
import threading
import time
from pathlib import Path

TEMP_SUFFIXES=('.crdownload','.part','.partial','.download','.tmp','.aria2','.!qb')

def folder_sample(folder):
    root=Path(folder)
    if not root.is_dir():raise OSError('下载文件夹不存在或不可访问')
    rows=[];temporary=False
    # 只检查该目录直接文件，不遍历整块硬盘。
    with os.scandir(root) as entries:
        for item in entries:
            if not item.is_file(follow_symlinks=False):continue
            try:stat=item.stat(follow_symlinks=False)
            except FileNotFoundError:continue
            rows.append((item.name,stat.st_size,stat.st_mtime_ns))
            temporary |= item.name.lower().endswith(TEMP_SUFFIXES)
            if len(rows)>20000:raise OSError('文件夹文件过多，请选择独立下载目录')
    return tuple(sorted(rows)),temporary

def network_sample():
    import psutil
    values=psutil.net_io_counters(pernic=True,nowrap=True)
    stats=psutil.net_if_stats()
    active={name:(v.bytes_sent+v.bytes_recv) for name,v in values.items()
            if stats.get(name) and stats[name].isup and 'loopback' not in name.lower()}
    if not active:raise OSError('没有可用的网络接口')
    return active

class QuietDetector:
    def __init__(self,task,now=None):
        self.task=task;self.started=time.monotonic() if now is None else now
        self.previous=None;self.previous_time=self.started;self.seen=False;self.quiet_since=None
        self.baseline=None;self.completed=False
    def update(self,sample,now):
        if now-self.started>=self.task['timeout_seconds']:return 'timeout'
        if self.previous is not None and now-self.previous_time>max(10,self.task['idle_seconds']):
            self.previous=None;self.seen=False;self.quiet_since=None;self.baseline=None;self.completed=False
        active=False
        if self.task['mode']=='download':
            state,temp=sample
            active=temp or (self.previous is not None and state!=self.previous[0])
            finals={row[0]:row[1:] for row in state if not row[0].lower().endswith(TEMP_SUFFIXES)}
            if self.baseline is None:self.baseline=finals
            self.completed=any(name not in self.baseline or values!=self.baseline[name] for name,values in finals.items())
        elif self.previous is not None:
            # 网卡消失或重置不能被当作安静结束。
            if sample.keys()!=self.previous.keys() or any(sample[k]<self.previous[k] for k in sample):
                raise OSError('网络接口变化或计数器重置，请重新开始监控')
            rate=sum(sample[k]-self.previous[k] for k in sample)/max(.001,now-self.previous_time)/1024
            active=rate>self.task['threshold_kib']
        self.previous=sample;self.previous_time=now
        if active:self.seen=True;self.quiet_since=None
        elif self.seen:
            if self.quiet_since is None:self.quiet_since=now
            if now-self.quiet_since>=self.task['idle_seconds'] and (self.task['mode']!='download' or self.completed):return 'ready'
        return 'active' if active else ('quiet' if self.seen else 'waiting')

class TransferWatcher:
    def __init__(self,task,emit,interval=2):
        self.task=task;self.emit=emit;self.interval=interval;self.cancel=threading.Event()
        self.thread=threading.Thread(target=self.run,daemon=True,name='HaozaiziTransfer')
    def start(self):self.thread.start();return self
    def stop(self):
        self.cancel.set()
        subscription=getattr(self,'_subscription',None)
        if subscription:subscription.close()
    def run(self):
        detector=QuietDetector(self.task)
        from shared_sampling import hub
        folder=os.path.normcase(os.path.abspath(self.task['folder'])) if self.task['mode']=='download' else None
        key=('folder',folder) if folder else ('network',)
        subscription=hub.subscribe(key,lambda:folder_sample(folder) if folder else network_sample(),self.interval)
        self._subscription=subscription
        last=None
        try:
            while not self.cancel.is_set():
                result=subscription.read(self.cancel)
                if result is None:return
                sample,stamp=result
                state=detector.update(sample,stamp)
                if self.cancel.is_set():return
                if state!=last:self.emit(state,'');last=state
                if state in ('ready','timeout'):return
        except Exception as exc:
            if not self.cancel.is_set():self.emit('error',str(exc))
        finally:subscription.close()
