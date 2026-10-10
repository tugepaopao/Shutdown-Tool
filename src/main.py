# -*- coding: utf-8 -*-
"""
豪崽子の自动关机工具 —— 程序入口
文件作者：@wenhao

用法示例：
    python main.py                 # 正常启动
    python main.py /min            # 启动后最小化到托盘
    python main.py /s /t=60        # 60 秒后关机
    python main.py /r /t=120 /w    # 预选重启、120 秒倒计时但不自动开始
    python main.py /rp="C:\\Windows\\notepad.exe"
    python main.py /ra="D:\\music\\bell.mp3"
    python main.py /m="记得喝水" /t=30
"""
import os
import sys

# 让 src 目录下的模块可以直接互相 import（打包后同样有效）
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)


def enable_dpi_awareness():
    """开启 DPI 感知，避免高分屏（125% / 150% / 200% 缩放）下界面发虚。

    这是 Win10 / Win11 高缩放笔记本上「界面模糊」的根因：进程没声明 DPI 感知时，
    Windows 会把整个窗口按 96 DPI 渲染完再**位图拉伸**，字体和图标全都糊。

    按新→旧逐级尝试，谁成功算谁（每一项在失败时都不抛异常）：
      1. SetProcessDpiAwarenessContext(PER_MONITOR_AWARE_V2)  Win10 1703+
         —— Win11 首选，支持多显示器不同缩放比
      2. SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE) Win8.1+（shcore）
      3. SetProcessDPIAware()                                  Vista+（user32）
    """
    try:
        import ctypes
        # ① Win10 1703+ / Win11：Per-Monitor V2
        try:
            DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)
            if ctypes.windll.user32.SetProcessDpiAwarenessContext(
                    DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2):
                return "per-monitor-v2"
        except Exception:
            pass
        # ② Win8.1+
        try:
            PROCESS_PER_MONITOR_DPI_AWARE = 2
            if ctypes.windll.shcore.SetProcessDpiAwareness(
                    PROCESS_PER_MONITOR_DPI_AWARE) == 0:
                return "per-monitor"
        except Exception:
            pass
        # ③ Vista+
        try:
            if ctypes.windll.user32.SetProcessDPIAware():
                return "system"
        except Exception:
            pass
    except Exception:
        pass
    return "none"


def main():
    enable_dpi_awareness()

    from actions import parse_argv
    from single_instance import SingleInstance
    from ui_main import App

    argv = sys.argv[1:]
    cli = parse_argv(argv)

    # ---- 单实例闸门 -------------------------------------------------
    # 已经有一个程序在跑，就把它的窗口唤到前台，本进程直接退出。
    # 必须放在建 Tk 之前：否则会先闪一个空窗口再退出，观感很差。
    # 注意 /min 这类参数在「已有实例」时不会重新生效 —— 这是刻意的简化，
    # 避免把命令行参数往已有实例里传（那需要额外的 IPC 通道）。
    si = SingleInstance()
    if not si.acquire():
        si.notify_existing()
        si.release()
        return 0

    app = App(cli, single_instance=si)
    try:
        app.root.mainloop()
    except KeyboardInterrupt:
        app.quit_app()
    finally:
        si.release()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
