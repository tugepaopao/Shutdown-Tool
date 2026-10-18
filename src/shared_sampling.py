"""One read-only sampler per resource, with independent subscriber cursors."""
import copy
import threading
import time


class _Source:
    def __init__(self, read, interval):
        self.read=read;self.interval=interval;self.condition=threading.Condition()
        self.stop=threading.Event();self.sequence=0;self.value=None;self.error=None;self.stamp=0;self.users=0
        self.thread=threading.Thread(target=self.run,daemon=True,name='SharedTaskSampler')

    def run(self):
        while not self.stop.is_set():
            try:value=self.read();error=None
            except Exception as exc:value=None;error=str(exc)
            with self.condition:
                if self.stop.is_set():return
                self.value=value;self.error=error;self.stamp=time.monotonic();self.sequence+=1
                self.condition.notify_all()
            if error is not None:return
            self.stop.wait(self.interval)


class Subscription:
    def __init__(self,hub,key,source):self.hub=hub;self.key=key;self.source=source;self.cursor=0;self.closed=False
    def read(self,cancel):
        source=self.source
        with source.condition:
            while source.sequence<=self.cursor and not self.closed and not cancel.is_set():source.condition.wait(2)
            if self.closed or cancel.is_set():return None
            self.cursor=source.sequence
            if source.error is not None:raise OSError(source.error)
            return copy.deepcopy(source.value),source.stamp
    def close(self):
        with self.hub.lock:
            if self.closed:return
            self.closed=True
        self.hub.release(self)


class SamplingHub:
    def __init__(self):self.lock=threading.Lock();self.sources={}
    def subscribe(self,key,read,interval=2):
        with self.lock:
            source=self.sources.get(key)
            if source is None:
                source=_Source(read,interval);self.sources[key]=source;source.thread.start()
            source.users+=1
            return Subscription(self,key,source)
    def release(self,subscription):
        with self.lock:
            source=subscription.source;source.users-=1
            if not source.users:
                source.stop.set()
                if self.sources.get(subscription.key) is source:self.sources.pop(subscription.key)
            with source.condition:source.condition.notify_all()


hub=SamplingHub()
