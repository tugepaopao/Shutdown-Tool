"""组合条件和程序任务链：工作线程只发事件，最终动作仍经主队列。"""
import ctypes
from ctypes import wintypes
import os
import subprocess
import threading
import time
from transfer_monitor import QuietDetector,network_sample

class LASTINPUTINFO(ctypes.Structure):
    _fields_=[('cbSize',wintypes.UINT),('dwTime',wintypes.DWORD)]

def user_idle_seconds():
    info=LASTINPUTINFO();info.cbSize=ctypes.sizeof(info)
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):raise OSError('无法读取用户空闲时间')
    tick=ctypes.windll.kernel32.GetTickCount()
    return ((tick-info.dwTime)&0xffffffff)/1000

class CombinedWatcher:
    def __init__(self,task,emit,network=None,idle=user_idle_seconds,clock=time.monotonic,interval=2):
        self.task=task;self.emit=emit;self.network=network;self.idle=idle;self.clock=clock;self.interval=interval;self.cancel=threading.Event()
    def start(self):
        self.thread=threading.Thread(target=self.run,daemon=True,name='CombinedCondition');self.thread.start();return self
    def stop(self):
        self.cancel.set()
        subscription=getattr(self,'_subscription',None)
        if subscription:subscription.close()
    def run(self):
        detector=QuietDetector(dict(self.task,mode='network'),self.clock());last=None
        from shared_sampling import hub
        subscription=hub.subscribe(('network',),network_sample,self.interval) if self.network is None else None
        self._subscription=subscription
        try:
            while not self.cancel.is_set():
                if subscription:
                    result=subscription.read(self.cancel)
                    if result is None:return
                    sample,stamp=result
                else:sample,stamp=self.network(),self.clock()
                state=detector.update(sample,stamp)
                if state=='ready' and self.idle()<self.task['user_idle_seconds']:state='waiting_user'
                if self.cancel.is_set():return
                if state!=last:self.emit(state,'');last=state
                if state in ('ready','timeout'):return
                if subscription is None:self.cancel.wait(self.interval)
        except Exception as exc:
            if not self.cancel.is_set():self.emit('error',str(exc))
        finally:
            if subscription:subscription.close()

class ChainWatcher:
    def __init__(self,task,emit):self.task=task;self.emit=emit;self.cancel=threading.Event();self.process=None
    def start(self):
        self.thread=threading.Thread(target=self.run,daemon=True,name='TaskChain');self.thread.start();return self
    def stop(self):
        self.cancel.set()
        subscription=getattr(self,'_subscription',None)
        if subscription:subscription.close()  # 不结束用户的备份程序；撤销后续动作。
    def run(self):
        try:
            path=self.task['prepare_path']
            if not os.path.isfile(path) or not path.lower().endswith('.exe'):raise ValueError('备份程序不存在或不是exe文件')
            if self.cancel.is_set():return
            command=subprocess.list2cmdline([path])
            if self.task.get('prepare_args'):command+=' '+self.task['prepare_args']
            self.process=subprocess.Popen(command,shell=False,cwd=os.path.dirname(path),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            self.emit('preparing','');deadline=time.monotonic()+self.task['timeout_seconds']
            while not self.cancel.wait(.1):
                code=self.process.poll()
                if code is not None:
                    self.emit('ready' if code==0 else 'error','' if code==0 else '备份程序退出码：'+str(code));return
                if time.monotonic()>=deadline:self.emit('timeout','备份程序超时，后续操作未执行；备份程序继续运行。');return
        except Exception as exc:
            if not self.cancel.is_set():self.emit('error',str(exc))
