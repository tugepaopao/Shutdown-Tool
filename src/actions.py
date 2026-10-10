# -*- coding: utf-8 -*-
"""
动作执行模块：关闭/重启/注销/睡眠/关闭显示器/运行程序/播放声音/消息提示
文件作者：@wenhao
"""
import ctypes
import os
import shlex
import subprocess
import winsound
from ctypes import wintypes

from app_config import (
    A_LOGOFF, A_MESSAGE, A_MONITOR, A_RESTART, A_RUN, A_SHUTDOWN, A_SLEEP, A_SOUND,
    A_LOCK, A_HIBERNATE, A_CLOSE,
)

CREATE_NO_WINDOW = 0x08000000

# ---------------------------------------------------------------- Windows API
_user32 = ctypes.WinDLL("user32", use_last_error=True)

HWND_BROADCAST = 0xFFFF
WM_SYSCOMMAND = 0x0112
SC_MONITORPOWER = 0xF170

_MONITOR_OFF = 2
_MONITOR_ON = -1

EWX_LOGOFF = 0x00000000
EWX_FORCE = 0x00000004
EWX_FORCEIFHUNG = 0x00000010

_user32.SendMessageTimeoutW.argtypes = [
    wintypes.HWND, wintypes.UINT, ctypes.c_size_t, ctypes.c_ssize_t,
    wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_size_t),
]
_user32.SendMessageTimeoutW.restype = wintypes.LPARAM

_mci = ctypes.windll.winmm.mciSendStringW
_SND_ALIAS = "haozai_sound"


def _run_hidden(cmd, wait=False, timeout=8.0):
    """静默启动外部命令（不弹黑框）。

    wait=False（默认）：只管发出，立刻返回 None —— 适合「广播」类动作。
    wait=True：等命令结束并返回 returncode；超时或异常时返回 None
               （表示「已发出但拿不到结果」，调用方不应据此判定失败）。
    """
    if not wait:
        subprocess.Popen(cmd, creationflags=CREATE_NO_WINDOW, close_fds=True)
        return None
    try:
        p = subprocess.Popen(cmd, creationflags=CREATE_NO_WINDOW, close_fds=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return p.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return -1


# shutdown.exe / ExitWindowsEx 的失败原因 → 人话（界面会直接弹给用户看）
def _shutdown_result(rc):
    """把 shutdown.exe 的返回码翻译成 (ok, 错误描述)。

    ⚠️ 以前这里是「无条件 return True, ''」：Popen 只负责把进程拉起来，
    关机命令真被拒绝（组策略 / 权限不足 / 被杀软拦）也不会抛异常，
    于是界面照样显示「操作已执行」，用户以为设好了、到点却什么都没发生。
    """
    if rc is None:
        return True, ""            # 已发出但拿不到码（超时）→ 不当失败处理
    if rc == 0:
        return True, ""
    if rc in (1116, 1190):         # 系统已在关机/重启流程中 → 目的已达到
        return True, ""
    if rc == 5:
        return False, "权限不足（拒绝访问）：可能被安全软件或组策略拦截"
    return False, "系统拒绝了该操作（错误码 %d）" % rc


# ---------------------------------------------------------------- 各类动作
def do_shutdown(force=True):
    cmd = ["shutdown", "/s", "/t", "0"]
    if force:
        cmd.append("/f")
    return _shutdown_result(_run_hidden(cmd, wait=True))


def do_restart(force=True):
    cmd = ["shutdown", "/r", "/t", "0"]
    if force:
        cmd.append("/f")
    return _shutdown_result(_run_hidden(cmd, wait=True))


def do_logoff(force=True):
    """注销当前用户。force=True 时先试 ExitWindowsEx 强制注销。"""
    if force:
        try:
            if _user32.ExitWindowsEx(EWX_LOGOFF | EWX_FORCE | EWX_FORCEIFHUNG, 0):
                return True, ""
        except Exception:
            pass
    return _shutdown_result(_run_hidden(["shutdown", "/l"], wait=True))


def do_sleep():
    try:
        api=ctypes.WinDLL('powrprof',use_last_error=True).SetSuspendState
        api.argtypes=[ctypes.c_ubyte,ctypes.c_ubyte,ctypes.c_ubyte];api.restype=ctypes.c_ubyte
        if api(0,0,0):return True,""
        return False,"睡眠请求失败（错误码 %d）" % ctypes.get_last_error()
    except Exception as exc:return False,str(exc)


def do_lock():
    try:
        if _user32.LockWorkStation(): return True, ""
        return False, "锁定电脑失败（错误码 %d）" % ctypes.get_last_error()
    except Exception as exc: return False, str(exc)


def do_hibernate():
    # shutdown /h enables the required privilege and returns a failure code when unavailable.
    return _shutdown_result(_run_hidden(["shutdown.exe", "/h"], wait=True))


_user32.LockWorkStation.argtypes = []
_user32.LockWorkStation.restype = wintypes.BOOL


def do_monitor_off():
    """广播消息关闭显示器。"""
    res = ctypes.c_size_t(0)
    _user32.SendMessageTimeoutW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER,
                                _MONITOR_OFF, 2, 3000, ctypes.byref(res))
    return True, ""


def do_monitor_on():
    res = ctypes.c_size_t(0)
    _user32.SendMessageTimeoutW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER,
                                _MONITOR_ON, 2, 3000, ctypes.byref(res))
    return True, ""


def _split_cmd(path):
    """把 '程序 参数' 拆成 [程序, 参数...]（Windows 风格引号处理）。

    posix=False 才不会把反斜杠当转义符吃掉（否则 C:\\a\\b.exe 会变成 C:ab.exe）。
    """
    try:
        parts = shlex.split(path, posix=False)
    except ValueError:
        return None
    out = []
    for p in parts:
        if len(p) >= 2 and p[0] == '"' and p[-1] == '"':
            p = p[1:-1]
        if p:
            out.append(os.path.expandvars(os.path.expanduser(p)))
    return out or None


def do_run_program(path):
    """运行程序 / 打开文档，允许带参数。

    ⚠️ 以前这里是 `subprocess.Popen(path, shell=True)`：路径会先被交给 cmd.exe
    解释，所以路径里只要含 `&` `|` `^` `>`（这些在 Windows 文件名里**是合法的**）
    就会被当成命令分隔符拆开 —— 轻则打不开，重则把后半截当命令执行。
    现在改成：能拆成「程序 + 参数」就直接 Popen（不经 shell），
    否则退化为交给系统按关联方式打开。
    """
    path = (path or "").strip()
    if not path:
        return False, "未设置要运行的程序"
    raw = path
    if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
        raw = raw[1:-1]
    cmd_path = os.path.expandvars(os.path.expanduser(raw))
    try:
        if os.path.isfile(cmd_path):
            os.startfile(cmd_path)          # 单个已存在的文件：交给系统按关联方式打开
            return True, ""
        parts = _split_cmd(raw)
        if parts and os.path.isfile(parts[0]):
            # 程序存在、后面还有参数 → 直接启动，不经 shell（参数里的 & | 不会被解释）
            subprocess.Popen(parts, creationflags=CREATE_NO_WINDOW, close_fds=True)
            return True, ""
        # 兜底：可能是文件夹、URL、shell: 之类的协议 → 交给系统
        os.startfile(parts[0] if parts else raw)
        return True, ""
    except Exception as exc:
        return False, str(exc)


def do_play_sound(path):
    """播放声音：wav 用 winsound，其它格式（mp3/wma/m4a…）走 MCI。"""
    from sound_library import resolve
    path = resolve(path)
    if not path or not os.path.exists(path):
        return False, "找不到该音频文件"
    try:
        stop_sound()
        if path.lower().endswith(".wav"):
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            if path.lower().endswith(('.mp3','.flac','.ogg')):
                import audio_player
                audio_player.play(path)
                return True, ""
            buf = ctypes.create_unicode_buffer(256)
            if _mci('open "%s" alias %s' % (path, _SND_ALIAS), buf, 256, None) != 0:
                return False, "无法打开该音频文件（格式可能不受支持）"
            if _mci("play %s" % _SND_ALIAS, None, 0, None) != 0:
                stop_sound()
                return False, "无法播放该音频文件"
        return True, ""
    except Exception as exc:
        return False, str(exc)


def stop_sound():
    try:
        import audio_player
        audio_player.stop()
        winsound.PlaySound(None, 0)
    except Exception:
        pass
    try:
        _mci("close %s" % _SND_ALIAS, None, 0, None)
    except Exception:
        pass


def beep_warning():
    """仅剩 10 秒时的提示音（系统提示音，无需外部文件）。"""
    try:
        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
    except Exception:
        pass


# ---------------------------------------------------------------- 统一入口
def perform(action, cfg, message_text=None, program_path=None, sound_file=None):
    """执行一个动作，返回 (ok, error_message)。"""
    force = bool(cfg.get("force_close_apps", True))
    if action == A_SHUTDOWN:
        return do_shutdown(force)
    if action == A_RESTART:
        return do_restart(force)
    if action == A_LOGOFF:
        return do_logoff(force)
    if action == A_SLEEP:
        return do_sleep()
    if action == A_LOCK:
        return do_lock()
    if action == A_HIBERNATE:
        return do_hibernate()
    if action == A_CLOSE:
        from program_control import close_program
        return close_program(cfg.get("close_program_path"))
    if action == A_MONITOR:
        return False, "旧版关闭显示器任务已停用，请选择其他操作"
    if action == A_RUN:
        return do_run_program(program_path if program_path is not None else cfg.get("program_path"))
    if action == A_SOUND:
        return do_play_sound(sound_file if sound_file is not None else cfg.get("sound_file"))
    if action == A_MESSAGE:
        # 消息提示框由界面层负责显示
        return True, ""
    return False, "未知的操作"


def action_label(action, T):
    mapping = {
        A_SHUTDOWN: "act_shutdown",
        A_RESTART: "act_restart",
        A_LOGOFF: "act_logoff",
        A_SLEEP: "act_sleep",
        A_LOCK: "act_lock", A_HIBERNATE: "act_hibernate", A_CLOSE: "act_close_program",
        A_MONITOR: "act_monitor_off",
        A_RUN: "act_run_program",
        A_SOUND: "act_play_sound",
        A_MESSAGE: "act_message",
    }
    return T(mapping.get(action, "act_shutdown"))


CLI_ACTIONS = {
    "/s": A_SHUTDOWN,
    "/r": A_RESTART,
    "/l": A_LOGOFF,
    "/sm": A_SLEEP,
    "/lock": A_LOCK,
    "/hibernate": A_HIBERNATE,
    "/som": A_MONITOR,
    "/rp": A_RUN,
    "/ra": A_SOUND,
    "/m": A_MESSAGE,
}


def parse_argv(argv):
    """解析命令行参数（参照 PShutDown 风格）。

    返回 dict: action / mode / seconds / auto_start / minimized / help / path / text
    未提供任何动作参数时 action=None。
    """
    out = {
        "action": None, "seconds": None, "auto_start": True,
        "minimized": False, "help": False, "path": "", "text": "",
        "given": False,
    }
    lower = [a.lower() for a in argv]
    if "/?" in argv or "/h" in lower or "--help" in lower or "-h" in lower:
        out["help"] = True

    for arg in argv:
        a = arg.strip()
        low = a.lower()
        if low in CLI_ACTIONS:
            out["action"] = CLI_ACTIONS[low]
            out["given"] = True
        elif low.startswith("/t="):
            try:
                out["seconds"] = max(0, int(float(a.split("=", 1)[1])))
                out["given"] = True
            except Exception:
                pass
        elif low == "/w":
            out["auto_start"] = False
        elif low == "/min":
            out["minimized"] = True
        elif low.startswith("/rp="):
            out["action"] = A_RUN
            out["path"] = a.split("=", 1)[1]
            out["given"] = True
        elif low.startswith("/ra="):
            out["action"] = A_SOUND
            out["path"] = a.split("=", 1)[1]
            out["given"] = True
        elif low.startswith("/m="):
            out["action"] = A_MESSAGE
            out["text"] = a.split("=", 1)[1]
            out["given"] = True
    return out
