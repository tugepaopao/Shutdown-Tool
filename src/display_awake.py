"""Keep-display request owned and released by the Tk main thread."""
import ctypes
import threading

ES_CONTINUOUS=0x80000000
ES_DISPLAY_REQUIRED=0x00000002
ES_SYSTEM_REQUIRED=0x00000001

class DisplayAwake:
    def __init__(self, root, api=None):
        self.root=root; self.task_active=False;self._flags=ES_CONTINUOUS; self.enabled=False; self.closed=False; self.owner=threading.get_ident()
        if api is None:
            api=ctypes.WinDLL('kernel32',use_last_error=True).SetThreadExecutionState
            api.argtypes=[ctypes.c_uint32];api.restype=ctypes.c_uint32
        self.api=api
        root.bind('<Destroy>', self._destroyed, add='+')
    def set_enabled(self, value):
        if threading.get_ident()!=self.owner:raise RuntimeError('Display request must use its owner thread')
        value=bool(value)
        if self.closed:raise OSError('Display request already closed')
        self._apply(value,self.task_active)
        self.enabled=value
    def set_task_active(self,value):
        self._apply(self.enabled,bool(value));self.task_active=bool(value)
    def _apply(self,display,tasks):
        if threading.get_ident()!=self.owner:raise RuntimeError("Power request must use its owner thread")
        if self.closed:raise OSError("Power request already closed")
        flags=ES_CONTINUOUS | (ES_DISPLAY_REQUIRED|ES_SYSTEM_REQUIRED if display else ES_SYSTEM_REQUIRED if tasks else 0)
        if flags==self._flags:return
        if not self.api(flags):
            raise OSError('Windows display request failed')
        self._flags=flags
    def close(self):
        if self.closed:return
        try:self.set_task_active(False);self.set_enabled(False)
        finally:self.closed=True
    def _destroyed(self,event):
        if event.widget is self.root:
            try:self.close()
            except OSError:pass
