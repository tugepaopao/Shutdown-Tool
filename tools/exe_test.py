# -*- coding: utf-8 -*-
"""
打包后 exe 的端到端实测（不触发关机类动作）
文件作者：@wenhao

运行： .venv\\Scripts\\python.exe tools\\exe_test.py
"""
import ctypes
import ctypes.wintypes as wt
import os
import subprocess
import sys
import time

from PIL import Image, ImageGrab

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'src'))
from main import enable_dpi_awareness
enable_dpi_awareness()  # GetWindowRect 与 PrintWindow 使用相同物理像素，避免截图裁切。
EXE_NAME = "定时关机工具.exe"
_CANDIDATES = [os.path.join(ROOT, d, EXE_NAME)
               for d in ("dist_v49", "dist_v48", "dist_v47", "dist_v46", "dist_v45", "dist_v44", "dist_v43", "dist_v42", "dist_v41", "dist_v40", "dist_v39", "dist_v38", "dist_v37", "dist_v36", "dist_v35", "dist_v34", "dist_v33", "dist_v32", "dist_v31", "dist_v30", "dist_v29", "dist_v28", "dist_v27", "dist_v26", "dist_v25", "dist_v24", "dist_v23", "dist_v22", "dist_v21", "dist_v19", "dist_v17", "dist_v16", "dist_v15", "dist_v14", "dist_v13", "dist_v12", "dist_v11", "dist_v10", "dist_v9", "dist_v8", "dist_v7", "dist_v6", "dist_v5", "dist_v4", "dist_v3", "dist_v2",
                         "dist_out", "dist")]
_exist = [p for p in _CANDIDATES if os.path.exists(p)]
EXE = max(_exist, key=os.path.getmtime) if _exist else _CANDIDATES[0]
SHOTS = os.path.join(HERE, "shots")
os.makedirs(SHOTS, exist_ok=True)

user32 = ctypes.windll.user32
TITLE = "定时关机工具"

RESULT = []


def log(name, ok, detail=""):
    RESULT.append((name, bool(ok), detail))
    print("%-40s %s %s" % (name, "PASS" if ok else "FAIL", detail))


def find_window(title=TITLE):
    hwnd = user32.FindWindowW(None, title)
    return hwnd or None


def wait_window(title=TITLE, timeout=20.0):
    """轮询等待窗口出现（打包版 onefile 解压启动较慢）。"""
    t0 = time.time()
    while time.time() - t0 < timeout:
        hwnd = find_window(title)
        if hwnd:
            return hwnd
        time.sleep(0.5)
    return None


def find_visible_window(title=TITLE):
    """枚举所有顶层窗口，返回第一个「标题匹配且可见」的窗口（防止抓到隐藏实例）。"""
    hits = []
    WNDENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

    def _cb(hwnd, _lparam):
        buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, buf, 512)
        if buf.value == title and user32.IsWindowVisible(hwnd):
            hits.append(hwnd)
            return False
        return True

    user32.EnumWindows(WNDENUMPROC(_cb), 0)
    return hits[0] if hits else None


def wait_visible(title=TITLE, timeout=25.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        hwnd = find_visible_window(title)
        if hwnd:
            return hwnd
        time.sleep(0.5)
    return None


def kill_all():
    # 只关闭构建目录里的测试exe，避免误关正式安装的用户实例。
    import psutil
    from pathlib import Path
    owned=Path(ROOT).resolve()
    for process in psutil.process_iter(['name','exe']):
        try:
            if process.info['name']==EXE_NAME:
                exe=Path(process.info['exe']).resolve()
                if owned in exe.parents:process.terminate()
                else:raise RuntimeError('User instance is running; do not terminate it')
        except (psutil.NoSuchProcess,psutil.AccessDenied):pass

    time.sleep(1.0)


def count_processes(samples=3, gap=0.35):
    """当前同名进程数量（用于验证「不会多开」）。tasklist 系统自带，无额外依赖。

    两个坑：
    ① **onefile 打包的程序，一个实例会占 2 个进程** —— 外层的引导父进程
       （几 MB，负责解压到临时目录并回收）+ 真正的应用子进程。
       所以「只有一个实例」时该函数的返回值是 2，不能硬编码成 1。
    ② 刚启动时进程是陆续起来的，单次快照可能少算一个。
       所以连续采几次取**最大值**。
    """
    best = 0
    for i in range(samples):
        try:
            out = subprocess.run(["tasklist", "/fi", "imagename eq %s" % EXE_NAME, "/nh"],
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                 creationflags=0x08000000)
            text = out.stdout.decode("gbk", "replace")
            best = max(best, sum(1 for ln in text.splitlines()
                                 if EXE_NAME.lower() in ln.lower()))
        except Exception:
            return -1
        if i < samples - 1:
            time.sleep(gap)
    return best


def wait_exit(proc, timeout=10.0):
    """等进程自己退出（单实例下第二个实例应当很快自行退出）。"""
    t0 = time.time()
    while time.time() - t0 < timeout:
        if proc.poll() is not None:
            return True
        time.sleep(0.25)
    return False


# ---- 只数「真正在跑程序本体」的进程 ------------------------------------
# 为什么不能直接数同名进程：onefile 的**引导器**是一个纯 C 进程，它把 exe 里
# 附带的归档解到 %TEMP%\_MEIxxxx 后再派生应用子进程、自己等在后面。
# 实测（v1.1.6 与 v1.2.0 表现一致）：当已有实例在跑时，第二个引导器会因为
# 临时目录被占用而**多停留约 2 分钟**才自己退出 —— 它没有窗口、不占单实例
# 闸门、不加载 python/tk，纯粹是在等清理，对用户完全无感。
# 所以判据要落在「有没有多出一个**应用**进程」上：应用子进程必然加载了
# python3xx.dll（引导器不会），据此区分两层。
_psapi = ctypes.windll.psapi
_k32 = ctypes.windll.kernel32
_psapi.EnumProcessModulesEx.argtypes = [wt.HANDLE, ctypes.POINTER(wt.HMODULE),
                                        wt.DWORD, ctypes.POINTER(wt.DWORD), wt.DWORD]
_psapi.GetModuleBaseNameW.argtypes = [wt.HANDLE, wt.HMODULE, wt.LPWSTR, wt.DWORD]
_psapi.GetModuleBaseNameW.restype = wt.DWORD
_k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
_k32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
_k32.Process32FirstW.argtypes = [wt.HANDLE, ctypes.c_void_p]
_k32.Process32NextW.argtypes = [wt.HANDLE, ctypes.c_void_p]


class _PE32(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD), ("th32ProcessID", wt.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)), ("th32ModuleID", wt.DWORD),
                ("cntThreads", wt.DWORD), ("th32ParentProcessID", wt.DWORD),
                ("pcPriClassBase", ctypes.c_long), ("dwFlags", wt.DWORD),
                ("szExeFile", wt.WCHAR * 260)]


def _loads_python(pid):
    """这个进程加载了 python3xx.dll 吗？（= 它是应用，不是引导器）"""
    h = _k32.OpenProcess(0x0410, False, pid) or _k32.OpenProcess(0x1000, False, pid)
    if not h:
        return False
    arr = (wt.HMODULE * 1024)()
    need = wt.DWORD()
    ok = _psapi.EnumProcessModulesEx(h, ctypes.cast(arr, ctypes.POINTER(wt.HMODULE)),
                                     ctypes.sizeof(arr), ctypes.byref(need), 0x03)
    found = False
    if ok:
        for i in range(min(need.value // ctypes.sizeof(wt.HMODULE), 1024)):
            buf = ctypes.create_unicode_buffer(512)
            if _psapi.GetModuleBaseNameW(h, arr[i], buf, 512) and buf.value.lower().startswith("python3"):
                found = True
                break
    _k32.CloseHandle(h)
    return found


def count_app_processes():
    """同名进程里，「应用层」的进程有几个（引导器不算）。"""
    snap = _k32.CreateToolhelp32Snapshot(0x2, 0)
    e = _PE32(); e.dwSize = ctypes.sizeof(_PE32)
    pids = []
    if _k32.Process32FirstW(snap, ctypes.byref(e)):
        while True:
            if e.szExeFile.lower() == EXE_NAME.lower():
                pids.append(e.th32ProcessID)
            if not _k32.Process32NextW(snap, ctypes.byref(e)):
                break
    _k32.CloseHandle(snap)
    return sum(1 for p in pids if _loads_python(p))


def find_tray_hwnd():
    """枚举窗口找 pystray 的隐藏消息窗口（类名以 SystemTrayIcon 结尾）。"""
    found = []
    WNDENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

    def _cb(hwnd, _lparam):
        buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, buf, 256)
        if buf.value.endswith("SystemTrayIcon"):
            found.append((hwnd, buf.value))
            return False
        return True

    user32.EnumWindows(WNDENUMPROC(_cb), 0)
    return found[0] if found else (None, "")


def wait_tray_hwnd(timeout=10.0):
    """等 pystray 的托盘消息窗口出现。

    注意：主窗口比托盘图标先建好（App.build_ui 先跑、_init_tray 后跑），
    所以主窗口一出现就立刻查托盘会查不到 —— 这里必须轮询等待，
    否则这条断言会偶发失败（实测托盘窗口一般在 1 秒内就注册好了）。
    """
    t0 = time.time()
    while time.time() - t0 < timeout:
        hwnd, cls = find_tray_hwnd()
        if hwnd:
            return hwnd, cls
        time.sleep(0.4)
    return None, ""


def grab_tray_area(name):
    """截取屏幕右下角托盘区域，肉眼确认图标是否出现。"""
    try:
        img = ImageGrab.grab()
        w, h = img.size
        img.crop((max(0, w - 420), max(0, h - 70), w, h)).resize(
            (min(420, w) * 2, min(70, h) * 2)).save(os.path.join(SHOTS, name))
        print("shot -> %s（托盘区域，已放大 2 倍）" % name)
    except Exception as exc:
        print("!! 托盘截图失败: %s" % exc)


def window_rect(hwnd):
    r = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom


def grab_window(hwnd, name):
    """Capture owned-window content with explicit 64-bit Win32 handle types."""
    g = ctypes.windll.gdi32
    user32.GetWindowDC.argtypes=[wt.HWND];user32.GetWindowDC.restype=wt.HDC
    user32.ReleaseDC.argtypes=[wt.HWND,wt.HDC];user32.ReleaseDC.restype=ctypes.c_int
    user32.PrintWindow.argtypes=[wt.HWND,wt.HDC,wt.UINT];user32.PrintWindow.restype=wt.BOOL
    g.CreateCompatibleDC.argtypes=[wt.HDC];g.CreateCompatibleDC.restype=wt.HDC
    g.CreateCompatibleBitmap.argtypes=[wt.HDC,ctypes.c_int,ctypes.c_int];g.CreateCompatibleBitmap.restype=wt.HBITMAP
    g.SelectObject.argtypes=[wt.HDC,wt.HGDIOBJ];g.SelectObject.restype=wt.HGDIOBJ
    g.DeleteObject.argtypes=[wt.HGDIOBJ];g.DeleteObject.restype=wt.BOOL
    g.DeleteDC.argtypes=[wt.HDC];g.DeleteDC.restype=wt.BOOL
    g.GetDIBits.argtypes=[wt.HDC,wt.HBITMAP,wt.UINT,wt.UINT,ctypes.c_void_p,ctypes.c_void_p,wt.UINT];g.GetDIBits.restype=ctypes.c_int
    user32.RedrawWindow(ctypes.c_void_p(hwnd),None,None,0x0001|0x0080|0x0100|0x0400)
    time.sleep(.25)
    rect=wt.RECT();user32.GetWindowRect(ctypes.c_void_p(hwnd),ctypes.byref(rect))
    width,height=rect.right-rect.left,rect.bottom-rect.top
    if width<=1 or height<=1:raise RuntimeError('Invalid capture window dimensions')
    hdc=user32.GetWindowDC(hwnd);mdc=None;bmp=None;previous=None
    try:
        if not hdc:raise OSError('GetWindowDC failed')
        mdc=g.CreateCompatibleDC(hdc);bmp=g.CreateCompatibleBitmap(hdc,width,height)
        if not mdc or not bmp:raise OSError('GDI allocation failed')
        previous=g.SelectObject(mdc,bmp)
        if not user32.PrintWindow(hwnd,mdc,2):raise OSError('PrintWindow failed')
        time.sleep(.12)
        if not user32.PrintWindow(hwnd,mdc,2):raise OSError('PrintWindow refresh failed')
        class BIH(ctypes.Structure):
            _fields_=[('biSize',wt.DWORD),('biWidth',wt.LONG),('biHeight',wt.LONG),('biPlanes',wt.WORD),('biBitCount',wt.WORD),('biCompression',wt.DWORD),('biSizeImage',wt.DWORD),('biXPelsPerMeter',wt.LONG),('biYPelsPerMeter',wt.LONG),('biClrUsed',wt.DWORD),('biClrImportant',wt.DWORD)]
        bi=BIH();bi.biSize=ctypes.sizeof(bi);bi.biWidth=width;bi.biHeight=-height;bi.biPlanes=1;bi.biBitCount=32
        buf=ctypes.create_string_buffer(width*height*4)
        # GetDIBits requires a bitmap not currently selected into a DC.
        g.SelectObject(mdc,previous);previous=None
        if g.GetDIBits(mdc,bmp,0,height,buf,ctypes.byref(bi),0)!=height:raise OSError('GetDIBits incomplete')
        Image.frombuffer('RGBA',(width,height),buf,'raw','BGRA',0,1).convert('RGB').save(os.path.join(SHOTS,name))
        print('shot -> %s (%dx%d) [PrintWindow]' % (name,width,height))
    finally:
        if previous and mdc:g.SelectObject(mdc,previous)
        if bmp:g.DeleteObject(bmp)
        if mdc:g.DeleteDC(mdc)
        if hdc:user32.ReleaseDC(hwnd,hdc)


def main():
    if not os.path.exists(EXE):
        print("找不到 exe：%s" % EXE)
        return 1
    print("被测 exe：%s" % EXE)
    kill_all()

    # ---------------------------------------------------- 1) 便携版直接运行
    proc = subprocess.Popen([EXE, "/min"], cwd=os.path.dirname(EXE))
    hwnd_min = wait_window(TITLE, 25)
    log("便携 exe 启动并建好主窗口（/min）", proc.poll() is None and bool(hwnd_min),
        "pid=%s hwnd=%s" % (proc.pid, hwnd_min or 0))

    # 托盘图标窗口（pystray 在 win32 上创建 <name><id>SystemTrayIcon 类窗口）
    tray_hwnd, tray_cls = wait_tray_hwnd()
    log("系统托盘图标已注册", bool(tray_hwnd), "class=%s" % (tray_cls or "-"))
    grab_tray_area("14_tray_area.png")

    # /min 时主窗口应当是隐藏的
    visible = bool(hwnd_min) and bool(user32.IsWindowVisible(hwnd_min))
    log("主窗口已按 /min 隐藏到托盘", bool(hwnd_min) and not visible,
        "visible=%s" % visible)

    # ---------------------------------------------------- 2) 单实例：不允许再开第二个
    # 判据落在**「应用进程有没有多出来」**上，而不是同名进程总数 ——
    # onefile 的引导器是纯 C 进程，已有实例在跑时它会因为 %TEMP%\_MEI 目录
    # 被占用而多停留约 2 分钟（无窗口 / 不占闸门 / 不加载 python，用户无感）。
    # 应用子进程必然加载 python3xx.dll，据此把两层区分开，
    # 断言「启动第二个实例前后，应用进程数不变」= 真的没有多开。
    before = count_app_processes()
    proc2 = subprocess.Popen([EXE], cwd=os.path.dirname(EXE))
    exited = wait_exit(proc2, 10)
    time.sleep(1.2)
    after = count_app_processes()
    log("再启动一个时，第二个实例不产生新应用进程（不会多开）",
        after == before and before >= 1,
        "应用进程数 %d → %d；同名进程总数现为 %d（多出的是引导器：%s）"
        % (before, after, count_processes(),
           "已退出" if exited else "仍在等临时目录清理，约 2 分钟后自行退出"))

    # 第二个实例退出前应当把已有实例的窗口唤到前台（从托盘里出来）
    hwnd = wait_visible(TITLE, 15)
    log("已有实例的窗口被唤到前台（从托盘恢复）", bool(hwnd), "hwnd=%s" % (hwnd or 0))
    if hwnd:
        grab_window(hwnd, "10_exe_main.png")

    # 窗口图标（标题栏左上角 / 任务栏）：WM_GETICON 应能取到图标句柄
    if hwnd:
        WM_GETICON = 0x007F
        small = user32.SendMessageW(hwnd, WM_GETICON, 0, 0)   # ICON_SMALL
        big = user32.SendMessageW(hwnd, WM_GETICON, 1, 0)     # ICON_BIG
        if not small:
            small = user32.GetClassLongPtrW(hwnd, -34)        # GCLP_HICONSM
        if not big:
            big = user32.GetClassLongPtrW(hwnd, -14)          # GCLP_HICON
        log("窗口图标已设置（左上角/任务栏=透明底蓝色电源开关球）",
            bool(small or big), "small=%s big=%s" % (small or 0, big or 0))

    # 关闭窗口（应缩到托盘而不是退出）
    if hwnd:
        user32.PostMessageW(hwnd, 0x0010, 0, 0)      # WM_CLOSE
        time.sleep(3)
        still = proc.poll() is None and count_processes() >= 1
        hidden = not user32.IsWindowVisible(hwnd)
        log("点关闭后缩到托盘且进程仍在运行", still,
            "进程存活=%s 窗口隐藏=%s" % (still, hidden))
    kill_all()

    # ---------------------------------------------------- 3) 命令行参数 + 定时
    proc3 = subprocess.Popen([EXE, "/m=测试：定时器已到点执行", "/t=6"],
                             cwd=os.path.dirname(EXE))
    time.sleep(12)                                  # 等倒计时走完，弹出消息框
    full = ImageGrab.grab()
    full.save(os.path.join(SHOTS, "11_exe_cli_toast_full.png"))
    w, h = full.size
    full.crop((max(0, w - 520), max(0, h - 260), w, h)).save(
        os.path.join(SHOTS, "12_exe_cli_toast.png"))
    log("命令行 /m= + /t= 到点弹出消息框", proc3.poll() is None,
        "已截图 12_exe_cli_toast.png")
    kill_all()

    # 参数帮助窗口
    proc4 = subprocess.Popen([EXE, "/?"], cwd=os.path.dirname(EXE))
    help_hwnd = wait_window("程序参数", 25)
    log("命令行 /? 弹出参数帮助窗口", bool(help_hwnd), "hwnd=%s" % (help_hwnd or 0))
    if help_hwnd:
        grab_window(help_hwnd, "13_exe_params.png")
    kill_all()

    print("\n" + "=" * 62)
    total = len(RESULT)
    passed = sum(1 for _, ok, _ in RESULT if ok)
    print("exe 实测 %d 项，通过 %d 项，失败 %d 项" % (total, passed, total - passed))
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

