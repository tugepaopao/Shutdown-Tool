# -*- coding: utf-8 -*-
r"""
单实例控制：保证同一时间只有一个程序在运行
文件作者：@wenhao

需求背景
--------
程序原来可以无限多开：双击几次图标就出来几个窗口，托盘里也堆好几个图标，
既容易误操作（这个设了定时、那个又取消），也占资源。
现在要求「已经打开了就不能再多开」。

实现原理（全走 Win32，不用 reg.exe）
------------------------------------
① **拦多开**：`CreateMutexW` 建一个具名互斥体。如果这个名字已经存在，
   `GetLastError()` 会返回 `ERROR_ALREADY_EXISTS (183)` —— 说明已经有实例在跑。
   此时本进程应当**直接退出**。

② **让用户知道"程序已经开着了"**：光退出还不够，用户点图标得**有反应**，
   否则会以为程序坏了。做法：再建一个具名事件对象，第二个实例
   `SetEvent()` 发个信号，第一个实例在自己的 Tk 主线程里用 `after()`
   轮询 `WaitForSingleObject(..., 0)`，收到信号就把窗口唤到前台。

为什么不用「FindWindow 找窗口 + 外部 ShowWindow」
-------------------------------------------------
程序最小化到托盘时窗口是 `withdraw` 状态。从**外部**调 `ShowWindow` 虽然
能让窗口显示出来，但 Tk 内部仍然认为自己是隐藏的，之后 `deiconify()` /
`withdraw()` 就会和实际状态打架（典型症状：从托盘点「显示主界面」没反应）。
改成「事件通知 + 已有实例自己调自己的 show_window()」，全程走 Tk 自己的
状态机，永远不会错乱。

命名
----
用 `Local\` 前缀（同一登录会话内唯一）而不是 `Global\`：
`Global\` 需要 SeCreateGlobalPrivilege，普通用户可能创建失败；
而每个用户会话各自允许开一个实例是合理行为。
名字里嵌的 GUID 与 `installer/setup.iss` 的 AppId 一致，便于对账。
"""
import ctypes
from ctypes import wintypes

_k32 = ctypes.WinDLL("kernel32", use_last_error=True)

ERROR_ALREADY_EXISTS = 183
WAIT_OBJECT_0 = 0

_GUID = "8F3C1A72-5B4E-4C9D-9E21-7A6B0C5D3F10"
MUTEX_NAME = "Local\\HaozaiziShutdownTool.SingleInstance." + _GUID
EVENT_NAME = "Local\\HaozaiziShutdownTool.ShowRequest." + _GUID

EVENT_MODIFY_STATE = 0x0002
SYNCHRONIZE = 0x00100000

# ---- 显式声明参数类型：64 位下句柄是 8 字节，不声明容易被 ctypes
#      默认的 c_int 截断（表现为"互斥体明明建了却检测不到"）
_k32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
_k32.CreateMutexW.restype = wintypes.HANDLE
_k32.CreateEventW.argtypes = [ctypes.c_void_p, wintypes.BOOL,
                              wintypes.BOOL, wintypes.LPCWSTR]
_k32.CreateEventW.restype = wintypes.HANDLE
_k32.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
_k32.OpenEventW.restype = wintypes.HANDLE
_k32.SetEvent.argtypes = [wintypes.HANDLE]
_k32.SetEvent.restype = wintypes.BOOL
_k32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
_k32.WaitForSingleObject.restype = wintypes.DWORD
_k32.ResetEvent.argtypes = [wintypes.HANDLE]
_k32.ResetEvent.restype = wintypes.BOOL
_k32.CloseHandle.argtypes = [wintypes.HANDLE]
_k32.CloseHandle.restype = wintypes.BOOL


class SingleInstance(object):
    """单实例闸门。

    典型用法（见 main.py）::

        si = SingleInstance()
        if not si.acquire():          # 已经有实例在跑
            si.notify_existing()      # 把它的窗口唤出来
            si.release()
            return                    # 本进程直接退出
        app = App(cli, single_instance=si)   # App 内部定时调 has_pending_show()
        ...
        si.release()

    出错时一律「放行」（返回 True），宁可多开也不能把程序卡住启动不了。
    """

    def __init__(self):
        self._mutex = None
        self._event = None
        self._is_first = False

    # ---------------------------------------------------------- 启动阶段
    def acquire(self):
        """尝试成为唯一实例。

        返回 True  = 我是第一个（或检测失败，放行）
        返回 False = 已经有实例在跑，调用方应通知它并退出
        """
        try:
            self._mutex = _k32.CreateMutexW(None, False, MUTEX_NAME)
            err = ctypes.get_last_error()
            if self._mutex and err == ERROR_ALREADY_EXISTS:
                self._is_first = False
                return False
            self._is_first = True
            # 只有第一个实例负责创建事件对象
            # 第 2 个参数 True = manual-reset：SetEvent 后一直保持有信号，
            # 直到读的一方 ResetEvent —— 这样即使第一个实例此刻还没开始轮询，
            # 稍后也能读到这次请求，不会丢信号。
            self._event = _k32.CreateEventW(None, True, False, EVENT_NAME)
            return True
        except Exception:
            self._is_first = True
            return True

    def notify_existing(self):
        """第二个实例调用：告诉已有实例「把窗口亮出来」。"""
        try:
            h = _k32.OpenEventW(EVENT_MODIFY_STATE | SYNCHRONIZE, False, EVENT_NAME)
            if h:
                _k32.SetEvent(h)
                _k32.CloseHandle(h)
                return True
        except Exception:
            pass
        return False

    # ---------------------------------------------------------- 运行阶段
    def has_pending_show(self):
        """已有实例轮询调用：有别的实例请求唤出窗口吗？（读后自动清零）"""
        if not self._event:
            return False
        try:
            if _k32.WaitForSingleObject(self._event, 0) == WAIT_OBJECT_0:
                _k32.ResetEvent(self._event)
                return True
        except Exception:
            pass
        return False

    # ---------------------------------------------------------- 退出阶段
    def release(self):
        """释放句柄。进程结束时系统也会自动清理，显式调用更干净。"""
        for attr in ("_event", "_mutex"):
            h = getattr(self, attr, None)
            if h:
                try:
                    _k32.CloseHandle(h)
                except Exception:
                    pass
                setattr(self, attr, None)

    @property
    def is_first(self):
        return self._is_first
