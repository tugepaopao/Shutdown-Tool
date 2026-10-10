"""Force-end user-selected programs by exact executable path, including their children."""
import ctypes as C
from ctypes import wintypes as W
import os
import sys
import time
import psutil

u=C.WinDLL('user32',use_last_error=True)
u.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM];u.PostMessageW.restype=W.BOOL
u.GetWindowThreadProcessId.argtypes=[W.HWND,C.POINTER(W.DWORD)];u.GetWindowThreadProcessId.restype=W.DWORD
u.GetWindowTextW.argtypes=[W.HWND,W.LPWSTR,C.c_int]
u.GetWindowTextLengthW.argtypes=[W.HWND];u.IsWindowVisible.argtypes=[W.HWND];u.IsWindowVisible.restype=W.BOOL
ENUM=C.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
u.EnumWindows.argtypes=[ENUM,W.LPARAM];u.EnumWindows.restype=W.BOOL
PROTECTED={'explorer.exe','winlogon.exe','csrss.exe','services.exe','lsass.exe','smss.exe','svchost.exe','dwm.exe','sihost.exe','taskhostw.exe','定时关机工具.exe','豪崽子の自动关机工具.exe'}

def canonical(path):return os.path.normcase(os.path.realpath(os.path.abspath(path)))

def validate_target(path):
    path=str(path or '').strip().strip('"')
    if not path or not os.path.isabs(path) or not path.lower().endswith('.exe'):
        raise ValueError('请选择要关闭的程序 exe 文件')
    path=canonical(path)
    if os.path.basename(path).lower() in PROTECTED or path==canonical(sys.executable):
        raise ValueError('不能选择本工具或系统关键程序')
    return path

def running_programs():
    items=[]
    def visit(hwnd,_):
        if not u.IsWindowVisible(hwnd):return True
        pid=W.DWORD();u.GetWindowThreadProcessId(hwnd,C.byref(pid))
        if pid.value==os.getpid():return True
        try:
            proc=psutil.Process(pid.value);path=validate_target(proc.exe())
            length=u.GetWindowTextLengthW(hwnd)
            if length<=0:return True
            text=C.create_unicode_buffer(length+1);u.GetWindowTextW(hwnd,text,length+1)
            items.append(dict(hwnd=int(hwnd),pid=pid.value,created=proc.create_time(),path=path,title=text.value))
        except (psutil.Error,ValueError,OSError):pass
        return True
    u.EnumWindows(ENUM(visit),0)
    return items

def matching_processes(path):
    """Snapshot identity and exact path, including hidden/tray-only processes."""
    found=[]
    for proc in psutil.process_iter(['pid','exe','create_time']):
        try:
            exe=proc.info['exe']
            if exe and canonical(exe)==path:
                # Re-read identity before adding; process_iter data can be cached.
                if canonical(proc.exe())==path:
                    found.append(proc)
        except (psutil.Error,OSError):continue
    return found


def force_close_program(path, timeout=6):
    try:path=validate_target(path)
    except ValueError as exc:return False,str(exc)
    roots=matching_processes(path)
    if not roots:return False,'目标程序当前没有运行'
    # Protect this tool and its launchers, as well as Windows critical processes.
    own=psutil.Process(os.getpid())
    protected={own.pid}
    try:protected.update(parent.pid for parent in own.parents())
    except psutil.Error:pass
    captured={};failed=[]
    def capture(proc):
        try:
            exe=proc.exe()
            if proc.pid in protected or os.path.basename(exe).lower() in PROTECTED:
                failed.append('protected');return
            captured[(proc.pid,proc.create_time())]=proc
        except psutil.NoSuchProcess:pass
        except psutil.AccessDenied:failed.append('permission')
    for root in roots:
        capture(root)
        try:
            for child in root.children(recursive=True):capture(child)
        except psutil.NoSuchProcess:pass
        except psutil.AccessDenied:failed.append('permission')
    # Stop the root(s) first so they cannot keep launching helper processes.
    root_ids={proc.pid for proc in roots}
    ordered=sorted(captured.items(),key=lambda item:item[0][0] not in root_ids)
    for (pid,created),proc in ordered:
        try:
            if proc.create_time()!=created:continue
            proc.kill()  # Windows TerminateProcess; never WM_CLOSE / name-wide taskkill.
        except psutil.NoSuchProcess:pass
        except psutil.AccessDenied:failed.append('permission')
        except psutil.Error:failed.append('failed')
    _,alive=psutil.wait_procs(list(captured.values()),timeout=max(0,float(timeout)))
    remaining=matching_processes(path)
    if failed or alive or remaining:
        if 'permission' in failed:return False,'部分进程无法结束，请以管理员身份运行本工具后重试'
        if 'protected' in failed:return False,'已跳过系统关键进程或本工具，未全部结束'
        return False,'程序仍有进程运行或被其他软件重新启动，请重试'
    return True,''


def close_program(path, timeout=6):
    """Compatibility name; closing now always means force-ending the process tree."""
    return force_close_program(path,timeout)
