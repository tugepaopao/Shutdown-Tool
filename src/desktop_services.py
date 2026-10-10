"""原生全局热键使用独立消息线程；桌面通知沿用Windows托盘后端。"""
import ctypes
from ctypes import wintypes
import queue
import threading
import time

MODIFIERS={'CTRL':2,'ALT':1,'SHIFT':4}
KEYS={**{chr(v):v for v in range(65,91)},**{str(v):48+v for v in range(10)},**{'F'+str(v):111+v for v in range(1,13)}}

def parse_hotkey(text):
    parts=[x.strip().upper() for x in str(text).split('+')];mods=0
    if len(parts)<2 or parts[-1] not in KEYS:raise ValueError('快捷键格式：Ctrl+Alt+H（字母、数字或F1～F12）')
    for part in parts[:-1]:
        if part not in MODIFIERS or mods&MODIFIERS[part]:raise ValueError('快捷键修饰键有误或重复')
        mods|=MODIFIERS[part]
    if not mods&3:raise ValueError('快捷键至少包含Ctrl或Alt')
    return mods|0x4000,KEYS[parts[-1]]

class HotkeyManager:
    def __init__(self,post):
        self.post=post;self.commands=queue.Queue();self.closed=False;self.mapping={}
        self.thread=threading.Thread(target=self.run,daemon=True,name='GlobalHotkeys');self.thread.start()
    def configure(self,mapping):
        parsed={key:parse_hotkey(text) for key,text in mapping.items()}
        if parsed==self.mapping:return
        if len(set(parsed.values()))!=len(parsed):raise ValueError('不同操作不能使用相同快捷键')
        done=threading.Event();result={};self.commands.put((parsed,done,result))
        if not done.wait(3):raise OSError('快捷键注册线程无响应')
        if result.get('error'):raise ValueError(result['error'])
        self.mapping=parsed
    def close(self):self.closed=True;self.thread.join(1)
    def run(self):
        user=ctypes.WinDLL('user32',use_last_error=True)
        user.RegisterHotKey.argtypes=[wintypes.HWND,ctypes.c_int,wintypes.UINT,wintypes.UINT];user.RegisterHotKey.restype=wintypes.BOOL
        user.UnregisterHotKey.argtypes=[wintypes.HWND,ctypes.c_int];user.UnregisterHotKey.restype=wintypes.BOOL
        user.PeekMessageW.argtypes=[ctypes.POINTER(wintypes.MSG),wintypes.HWND,wintypes.UINT,wintypes.UINT,wintypes.UINT];user.PeekMessageW.restype=wintypes.BOOL
        current={};ids={};msg=wintypes.MSG()
        def clear():
            for ident in list(ids):user.UnregisterHotKey(None,ident)
            ids.clear()
        def register(values):
            for ident,(key,(mods,vk)) in enumerate(values.items(),1):
                if not user.RegisterHotKey(None,ident,mods,vk):return False,key
                ids[ident]=key
            return True,''
        try:
            while not self.closed:
                try:
                    mapping,done,result=self.commands.get_nowait();previous=current.copy();clear()
                    ok,key=register(mapping)
                    if ok:current=mapping
                    else:
                        clear();restored,_=register(previous);current=previous if restored else {};result['error']='快捷键已被其他程序占用：'+key
                    done.set()
                except queue.Empty:pass
                while user.PeekMessageW(ctypes.byref(msg),None,0,0,1):
                    if msg.message==0x0312 and int(msg.wParam) in ids:self.post(ids[int(msg.wParam)])
                time.sleep(.02)
        finally:clear()

class DesktopServices:
    def __init__(self,app):
        self.app=app;self.hotkeys=None;self.last={};self.error=''
        try:self.apply()
        except Exception:self.close();raise
        app.root.bind('<Destroy>',self._destroy,add='+')
    def apply(self):
        cfg=self.app.cfg
        if cfg.get('hotkeys_enabled'):
            if self.hotkeys is None:self.hotkeys=HotkeyManager(lambda kind:self.app.post(self.handle,kind))
            self.hotkeys.configure({kind:cfg.get('hotkey_'+kind) for kind in ('show','pause','resume')})
        elif self.hotkeys:self.hotkeys.configure({})
    def handle(self,kind):
        if kind=='show':self.app.show_window()
        elif self.app.engine.is_running():
            if kind=='pause' and not self.app.engine.paused:self.app.toggle_pause()
            if kind=='resume' and self.app.engine.paused:self.app.toggle_pause()
    def notify(self,kind,text,force=False):
        cfg=self.app.cfg;tray=self.app.tray
        if not tray or (not force and (not cfg.get('notifications_enabled') or not cfg.get('notify_'+kind))):return False
        key=(kind,text);now=time.monotonic()
        if not force and now-self.last.get(key,-100)<3:return False
        try:
            sent=tray.notify(self.app.T('app_name'),text)
            if sent is False:return False
            self.last[key]=now
            self.last={k:v for k,v in self.last.items() if now-v<60};return True
        except Exception as exc:self.error=str(exc);return False
    def _destroy(self,event):
        if event.widget is self.app.root:self.close()
    def close(self):
        if self.hotkeys:self.hotkeys.close();self.hotkeys=None
