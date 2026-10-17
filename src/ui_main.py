# -*- coding: utf-8 -*-
"""
主窗口与程序控制器 —— 豪崽子の自动关机工具
文件作者：@wenhao
"""
import datetime
import os
import queue
import threading
import time
import tkinter as tk
from tkinter import filedialog, ttk
from ui_localize import messagebox
from ui_window import show

import autostart
import i18n
import run_log
from actions import (A_LOGOFF, A_MESSAGE, A_MONITOR, A_RESTART, A_RUN, A_SHUTDOWN,
                     A_SLEEP, A_SOUND, A_LOCK, A_HIBERNATE, A_CLOSE, action_label, beep_warning, perform, stop_sound)
from app_config import (KEY_ACTIONS, M_COUNTDOWN, M_DATETIME, M_INTERVAL,
                        VERSION, Config, parse_hm)
from i18n import Texts, format_remain, resource_path, weekday_names
from theme import (apply_nav_state, card_frame, draw_round_rect, enable_button,
                   flat_button, make_gradient_image, section_card, shade, theme)
from timer_engine import WARN_SECONDS, TimerEngine, next_datetime, resolve_at

ACTION_ROWS = [
    (A_SHUTDOWN, "act_shutdown", False),
    (A_RESTART, "act_restart", False),
    (A_LOGOFF, "act_logoff", False),
    (A_LOCK, "act_lock", False),
    (A_SLEEP, "act_sleep", False),
    (A_HIBERNATE, "act_hibernate", False),
    (A_CLOSE, "act_close_program", True),
    (A_RUN, "act_run_program", True),
    (A_SOUND, "act_play_sound", True),
    (A_MESSAGE, "act_message", True),
]

COL_GAP = 5          # 左右两栏间距（v1.3.0 起仅子窗口部分仍在用）
PAD = 6              # 窗口内边距
GROUP_GAP = 10       # 三个时间板块之间的间隔（必须留足，肉眼可见）

# v1.3.0：侧边导航版式的尺寸常量
NAV_WIDTH = 132      # 左侧导航栏固定宽度
CARD_GAP = 10        # 导航栏与内容卡片之间的间距
PAGE_PAD = 10        # 内容区四周留白

# v1.3.0：时间板块标题前缀（用一个固定标记给测试脚本识别板块）
T_HEAD_TAG = "   "

# v1.3.0：三种时间模式（顺序即界面呈现顺序）
MODE_KEYS = (M_COUNTDOWN, M_DATETIME, M_INTERVAL)

# 快捷预设（v1.2.0）：(文案键, 规格)
#   规格 ("sec", 秒数)   → 从现在起倒计时
#   规格 ("at", 时, 分)  → 今天那个时刻（已过则顺延到明天，见 timer_engine.resolve_at）
#   规格 ("tmr", 时, 分) → 明天那个时刻
#   规格 ("cfg_at", 配置键)   → 时刻来自设置（v1.3.1 新增，可自定义）
#   规格 ("cfg_tmr", 配置键)  → 明天的时刻来自设置（v1.3.1 新增，可自定义）
QUICK_PRESETS = [
    ("quick_30m", ("sec", 1800)),
    ("quick_1h", ("sec", 3600)),
    ("quick_2h", ("sec", 7200)),
    ("quick_18", ("at", 18, 0)),
    ("quick_22", ("at", 22, 0)),
    ("quick_tmr8", ("cfg_tmr", "quick_at_tomorrow")),
]
# 排成 3 列 2 行：如果排成一行 6 个，光这一行就能把窗口顶宽 70 多像素
QUICK_COLS = 3

# 自定义预设的默认值（设置界面「恢复默认」按钮用；与 app_config 保持一致）
QUICK_DEFAULTS = {"quick_at_today": (22, 0), "quick_at_tomorrow": (8, 0)}


# ---------------------------------------------------------------- 系统版本判定
def windows_build():
    """返回当前 Windows 的 build 号；识别失败返回 0。

    注意：**不能用 platform.release() / platform.version()** —— 没做 manifest
    声明的话，Win10 及以上会被报告成 "10"，Win11 也报 "10"，区分不出来。
    这里直接读注册表 CurrentBuildNumber，最稳（不依赖 manifest，不用 reg.exe）。

      · Win10 RTM           10240
      · Win10 22H2          19045   ← 本机
      · Win11 21H2/22H2     22000 / 22621
    """
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
        try:
            val, _ = winreg.QueryValueEx(key, "CurrentBuildNumber")
        finally:
            winreg.CloseKey(key)
        return int(str(val).strip())
    except Exception:
        return 0


def is_win11():
    return windows_build() >= 22000


def is_win10():
    build = windows_build()
    return 10240 <= build < 22000


def os_display_name():
    """给「关于」窗口用的人类可读系统名。"""
    build = windows_build()
    if build >= 22000:
        return "Windows 11 (build %d)" % build
    if build >= 10240:
        return "Windows 10 (build %d)" % build
    if 7600 <= build <= 7601:
        return "Windows 7 (build %d)" % build
    if build > 0:
        return "Windows (build %d)" % build
    return "Windows"


class App(object):
    def __init__(self, cli=None, single_instance=None):
        self.cli = cli or {}
        self._single = single_instance      # 单实例闸门（见 single_instance.py）
        self.cfg = Config()
        if self.cli.get("action"):
            self.cfg["action"] = self.cli["action"]
        if self.cfg.get("action") == A_MONITOR: self.cfg["action"] = A_CLOSE
        self.T = Texts(self.cfg.get("language"))
        theme.load(self.cfg)

        self.queue = queue.Queue()
        self.cli_help_only = bool(self.cli.get("help"))
        self._imgs = {}

        self.root = tk.Tk()
        self.root._theme_owner = self
        theme.apply_ttk(self.root)
        self.root.withdraw()
        from ui_window import prepare_main
        prepare_main(self.root)
        self.root.title(self.T("app_name"))
        self._set_icon()
        self.root.configure(bg=theme.c("bg"))

        from display_awake import DisplayAwake
        self.display_awake = DisplayAwake(self.root)
        try: self.display_awake.set_enabled(bool(self.cfg.get("keep_display_on")))
        except OSError:
            self.cfg["keep_display_on"] = False
        self.engine = TimerEngine(self.emit)
        self.engine.warning_seconds=int(self.cfg.get("warning_seconds",10))
        self.tray = None
        self.toast = None
        self.action_widgets = {}
        self._last_remain = 0
        self._status_key = ("status_idle", {})
        self._running = False
        self._tray_hint_shown = False
        self._settings_win = None
        # ---- v1.2.0 新增状态 ----
        self.task_queue = []            # 排队等待执行的定时任务
        self._active_task = None        # 当前正在跑的那个任务
        self._next_task_id = 1
        self._confirm_skipped = False   # 「本次启动不再询问」
        self._queue_win = None
        self._log_win = None
        self.cancel_toast = None        # 到点前 10 秒的「可取消」提示框
        self._load_queue()
        from undo_store import UndoManager
        self.undo=UndoManager(self)

        self.build_ui()
        self.bind_events()
        from ui_runtime_context import install
        install(self)
        self._init_tray()

        self.root.after(100, self._pump)
        self._apply_cli()
        # 恢复上次没跑完的定时（v1.2.0）；放在 CLI 之后，命令行参数优先
        self.root.after(600, self._maybe_resume_timer)
        from automation import AutomationController
        self.automation = AutomationController(self)
        from desktop_services import DesktopServices
        try:self.desktop=DesktopServices(self)
        except (ValueError,OSError) as exc:
            self.cfg['hotkeys_enabled']=False;self.desktop=DesktopServices(self)
            self.root.after(800,lambda e=str(exc):messagebox.showwarning(self.T('tip_title'),e,parent=self.root))
        from ui_floating import FloatingController
        self.floating = FloatingController(self)
        self._settle_fixed_main()
        from ui_skin import SkinRenderer
        self.skin_renderer=SkinRenderer(self);self.skin_renderer.apply()
        # Initialization may map the HWND to measure native layout. Keep it
        # hidden until the saved skin and all child surfaces are ready.
        self.root._main_ready=True
        from ui_window import present_main
        present_main(self.root)
        if self.cfg.recovery_notice:self.root.after(1000,lambda:messagebox.showinfo(self.T('tip_title'),i18n.feature_text(self.T,self.cfg.recovery_notice),parent=self.root))

    # ================================================================ 图标 / 窗口装饰
    def _set_icon(self):
        """窗口左上角 + 任务栏图标，并让系统标题栏跟随当前深浅色。"""
        self._apply_window_chrome(self.root)

    def _apply_window_chrome(self, win, delay=110):
        """给一个窗口套上「程序图标 + 跟随主题的标题栏深浅色」。

        为什么要分开做：图标是 Tk 的事（iconbitmap），
        标题栏是**系统画的非客户区**，Tk 完全管不到，必须走 DWM（见下）。

        为什么要延后 delay 毫秒：
        Tk 一旦改动窗口属性（resizable / geometry / minsize / title ...），
        它会**重建最外层的原生窗口**；如果这时刚把 DWM 属性设上去，
        属性是设在旧窗口上的，重建后自然就"丢"了 —— 这正是之前切深色模式
        客户区变深、标题栏却依旧白的原因。
        所以等 Tk 把这一轮布局忙完（约 0.1 秒）再套，确保落在最终那个窗口上。
        """
        self._apply_icon(win)
        from ui_window import disable_native_animation
        disable_native_animation(win)
        try:
            win.after(delay, lambda w=win: self._apply_dark_titlebar(w))
        except Exception:
            self._apply_dark_titlebar(win)

    def _apply_icon(self, win):
        try:
            ico = resource_path("assets/icon.ico")
            if not os.path.exists(ico):
                ico = resource_path("assets/icon.ico")
            if os.path.exists(ico):
                import ctypes
                hwnd=ctypes.windll.user32.GetAncestor(win.winfo_id(),2) or win.winfo_id()
                if getattr(win,'_icon_stamp',None)==(ico,hwnd):return
                win.iconbitmap(ico)
                hwnd=ctypes.windll.user32.GetAncestor(win.winfo_id(),2) or win.winfo_id()
                win._icon_stamp=(ico,hwnd)
        except Exception:
            pass

    # 兼容旧调用名
    apply_window_icon = _apply_icon

    def _apply_dark_titlebar(self, win):
        """让 Windows 系统标题栏跟着界面的深浅色模式走。

        背景：tkinter / ttk 只能画**客户区**，窗口最顶上那条标题栏（含最小化、
        最大化、关闭按钮）是系统绘制的**非客户区**，所以之前切到深色模式时，
        客户区已经变深、**标题栏还是白的**，看着就像「最上面一层没跟着变深」。

        第一步：设 DWM 的 DWMWA_USE_IMMERSIVE_DARK_MODE
        （Win10 20H1 起属性号是 20，更早的版本是 19，两个都试，谁成功算谁）；
        浅色模式显式设 0，避免系统是深色、程序是浅色时标题栏不匹配。

        第二步（本机实测出来的关键，缺了它第一步等于白设）：
        对**已经显示出来**的窗口只设属性，系统根本不会重画 ——
        DwmGetWindowAttribute 回读确实是 1，标题栏照样是白的。
        Win10 22H2 / build 19045 上把各种刷新方式都试了一遍：
          · SetWindowPos(SWP_FRAMECHANGED)           —— 无效
          · RedrawWindow(RDW_FRAME | RDW_UPDATENOW)  —— 无效
          · SendMessage(WM_THEMECHANGED)             —— 无效
          · ShowWindow(SW_HIDE) → SW_SHOWNOACTIVATE  —— 有效
        隐藏会让窗口丢掉前台焦点，所以用不激活的方式显示，必要时再把焦点抢回来。

        另外：先读一次当前属性值，已经对了就直接返回，
        免得每次重建界面、每次从托盘恢复都白白闪一下窗口。
        """
        from ui_dialog_chrome import update
        if update(win):return
        try:
            import ctypes
            u = ctypes.windll.user32
            dwm = ctypes.windll.dwmapi
            hwnd = u.GetAncestor(win.winfo_id(), 2) or win.winfo_id()   # GA_ROOT
            if not hwnd or not u.IsWindow(hwnd):
                return
            dwm.DwmSetWindowAttribute.restype = ctypes.c_long
            dwm.DwmSetWindowAttribute.argtypes = [
                ctypes.c_void_p, ctypes.c_uint,
                ctypes.POINTER(ctypes.c_int), ctypes.c_uint]
            dwm.DwmGetWindowAttribute.argtypes = [
                ctypes.c_void_p, ctypes.c_uint,
                ctypes.POINTER(ctypes.c_int), ctypes.c_uint]
            want = 1 if theme.is_dark else 0

            # 已经是目标值就收工（浅色下默认就是 0，通常直接跳过，不闪窗口）
            try:
                cur = ctypes.c_int(-1)
                if dwm.DwmGetWindowAttribute(ctypes.c_void_p(hwnd), 20,
                                             ctypes.byref(cur),
                                             ctypes.sizeof(cur)) == 0:
                    if cur.value == want:
                        return
            except Exception:
                pass

            val = ctypes.c_int(want)
            for attr in (20, 19):
                try:
                    if dwm.DwmSetWindowAttribute(ctypes.c_void_p(hwnd), attr,
                                                 ctypes.byref(val),
                                                 ctypes.sizeof(val)) == 0:
                        break
                except Exception:
                    continue

            # 已经显示出来的窗口：必须隐藏→显示，系统才会按新属性重画标题栏
            try:
                if u.IsWindowVisible(ctypes.c_void_p(hwnd)):
                    u.GetForegroundWindow.restype = ctypes.c_void_p
                    was_fg = (u.GetForegroundWindow() == hwnd)
                    u.ShowWindow(ctypes.c_void_p(hwnd), 0)   # SW_HIDE
                    u.ShowWindow(ctypes.c_void_p(hwnd), 4)   # SW_SHOWNOACTIVATE
                    if was_fg:
                        u.SetForegroundWindow(ctypes.c_void_p(hwnd))
            except Exception:
                pass
        except Exception:
            pass

    def _img(self, rel, size):
        """取一张缩放到 size×size 的 PhotoImage（带缓存，防止被回收）。"""
        key = (rel, size)
        if key in self._imgs:
            return self._imgs[key]
        try:
            from PIL import Image, ImageTk
            path = resource_path(rel)
            if not os.path.exists(path):
                return None
            im = Image.open(path).convert("RGBA").resize((size, size), Image.LANCZOS)
            ph = ImageTk.PhotoImage(im)
            self._imgs[key] = ph
            return ph
        except Exception:
            return None

    # ================================================================ 界面
    def _hint_wrap(self):
        """提示文字的换行宽度（跟随字号 + 系统 DPI，避免文字被截断）。"""
        try:
            sc = float(self.root.tk.call("tk", "scaling")) / (96.0 / 72.0)
        except Exception:
            sc = 1.0
        sc = min(2.2, max(1.0, sc))
        return max(360, int(theme.base_size * 42 * sc))

    def _build_header(self, parent):
        """顶栏（v1.3.1 精简版）：只保留**一行**，右侧放版本胶囊 + 设置齿轮。

        为什么把品牌行删了（v1.3.1 用户反馈）：
        原来顶栏是两行 ——
          第 1 行：操作提示文字
          第 2 行：应用图标 + 程序名 + 副标题「轻巧的定时管家」
        ——但第 2 行里「图标 + 程序名」跟**系统标题栏**完全重复（标题栏已经写着
        「豪崽子の自动关机工具」），而「设置」这一项左侧导航里也已经有入口了，
        整个第二行属于纯占地。删掉后：

        · 齿轮 / 版本胶囊移到第 1 行最右侧，成为**全窗口唯一**的设置入口；
        · 内容区整体上移，多出来的一行高度让给卡片（卡片留白更舒展）；
        · 原来挂在内容卡片里的操作提示（self.hint_label）位置不变。

        注意：`self.avatar_btn` 这个名字必须保留（托盘 / 单实例 / ui_smoke
        都在按名字找它），只是它现在挂在第 1 行。
        """
        T = self.T
        p = theme.p
        bar = tk.Frame(parent, bg=p["header_bg"], bd=0,
                       highlightthickness=0)
        bar.pack(fill="x")
        self.header_bar = bar
        inner = tk.Frame(bar, bg=p["header_bg"])
        inner.pack(fill="x", padx=(2, 2), pady=(2, 4))
        self.header_inner = inner

        # ---- 右侧：齿轮（先 pack 抢右边缘），再版本号胶囊
        gear_size = 22
        gear = self._img("assets/icon_gear.png", gear_size)
        self.avatar_btn = tk.Label(inner, image=gear, bd=0, bg=p["header_bg"],
                                   cursor="hand2", padx=2, pady=2)
        if gear is None:
            self.avatar_btn.config(text="⚙", font=theme.font(delta=3, bold=True),
                                   fg=p["fg_dim"])
        self.avatar_btn.pack(side="right", padx=(4, 2))
        self.avatar_btn.bind("<Button-1>", self._open_avatar_menu)
        self.avatar_btn.bind("<Enter>",
                             lambda e: self.avatar_btn.config(bg=p["hover"]))
        self.avatar_btn.bind("<Leave>",
                             lambda e: self.avatar_btn.config(bg=p["header_bg"]))

        # 版本号：做成一个浅色小胶囊（比裸文字更精致）
        ver_badge = tk.Label(inner, text="v" + VERSION, bg=p["badge_bg"],
                             fg=p["fg_muted"], font=theme.font(delta=-2),
                             padx=7, pady=1)
        ver_badge.pack(side="right", padx=(0, 0), pady=(3, 0))
        self.ver_badge = ver_badge

        # ---- 左侧：只剩一句当前所在页的提示（内容卡片里还有更详细的说明）
        #      不再重复程序名 —— 系统标题栏已经写着。
        self.header_hint = tk.Label(inner, text="", bg=p["header_bg"],
                                    fg=p["fg_dim"], font=theme.font(), anchor="w")
        self.header_hint.pack(side="left", padx=(4, 0))

        # ---- 分隔线（顶栏与下方内容之间）
        tk.Frame(parent, bg=p["divider"], height=1).pack(fill="x")

    def _build_avatar_menu(self):
        """头像菜单内容：程序设置 / 程序参数 / 关于本程序。"""
        T = self.T
        p = theme.p
        menu = tk.Menu(self.root, tearoff=0, font=theme.font(),
                       bg=p["card"], fg=p["fg"], bd=0, relief="flat",
                       activebackground=theme.accent, activeforeground=p["accent_fg"],
                       activeborderwidth=0, selectcolor=theme.accent)
        menu.add_command(label="  " + T("menu_settings"), command=self.open_settings)
        menu.add_command(label="  " + T("menu_params"), command=self.open_params)
        menu.add_command(label="  " + T("menu_queue"), command=self.open_queue)
        menu.add_command(label="  " + T("menu_log"), command=self.open_log)
        menu.add_separator()
        menu.add_command(label="  " + T("menu_about"), command=self.open_about)
        return menu

    def _open_avatar_menu(self, event=None):
        from ui_popup_menu import VioletMenu
        popup=getattr(self,'_avatar_popup',None)
        if popup and popup.winfo_exists():popup.dismiss()
        menu=self._build_avatar_menu();self._avatar_popup=VioletMenu(self,menu)
        return menu

    # ------------------------------------------------------------ 侧边导航
    def _build_sidebar(self, parent):
        """左侧竖向导航栏（v1.3.0 新增）。

        结构（自上而下）：
          品牌已上移到顶栏，这里只放导航：
            「定时设置」分组 → 选择操作 / 设定时间
            辅助功能统一放在右上角齿轮菜单。

        为什么用「导航 + 内容页」而不是原来的「左右两栏」：
        原来左栏只放操作单选项、右栏放时间设置，两边功能其实是一条流水线
        （先选操作 → 再设时间），并列摆放反而让人不知道该先点哪边；
        改成导航后，一屏只聚焦一件事，符合参考图那种"一页一主题"的观感。

        导航项用 flat_button(kind="nav")，选中态由 apply_nav_state 切换。
        """
        T = self.T
        p = theme.p
        nav = tk.Frame(parent, bg=p["nav_bg"], width=NAV_WIDTH, bd=0)
        nav.pack(side="left", fill="y")
        # 固定宽度：不让内容把导航挤变形（pack_propagate(False) 是关键，
        # 否则 Frame 会被子控件的请求宽度撑开）
        nav.pack_propagate(False)
        self.sidebar = nav

        inner = tk.Frame(nav, bg=p["nav_bg"])
        inner.pack(fill="both", expand=True, padx=8, pady=10)

        self.nav_btns = {}

        def _group_label(text):
            tk.Label(inner, text=text, bg=p["nav_bg"], fg=p["fg_muted"],
                     font=theme.font(delta=-2, bold=True), anchor="w").pack(
                fill="x", padx=6, pady=(6, 3))

        def _nav_item(key, label, command):
            b = flat_button(inner, label, command, kind="nav",
                            pady=7, padx=10, font=theme.font())
            b.config(anchor="w")
            b.pack(fill="x", pady=1)
            self.nav_btns[key] = b
            return b

        _group_label(T("nav_group_main"))
        _nav_item("actions", "   " + T("nav_actions"),
                  lambda: self.show_page("actions"))
        _nav_item("time", "   " + T("nav_time"),
                  lambda: self.show_page("time"))

        # 底部留白，把导航项顶到上方
        tk.Frame(inner, bg=p["nav_bg"]).pack(fill="both", expand=True)

    def show_page(self, key):
        import ui_compact
        return ui_compact.show_page(self, key)


    def _focus_first_time_widget(self):
        try:
            w = self.timer_panel.winfo_children()
            for c in w:
                for cc in getattr(c, "winfo_children", lambda: [])():
                    if cc.winfo_class() == "TSpinbox":
                        cc.focus_set()
                        return
        except Exception:
            pass

    def _build_actions(self, parent):
        import ui_compact
        return ui_compact.build_actions(self, parent)


    def _bind_action_rows(self):
        """让整行（含指示条、空白处）都能点选，并做悬停高亮。"""
        p = theme.p
        for action, (grp, row, ind) in self.action_row_frames.items():
            rb = self.action_widgets[action]

            def _pick(_e=None, a=action):
                self.action_var.set(a)
                self._on_action_pick()

            def _enter(_e=None, a=action):
                if self.action_var.get() != a:
                    self._paint_action_row(a, hover=True)

            def _leave(_e=None, a=action):
                self._refresh_action_styles()

            for w in (row, ind):
                w.bind("<Button-1>", _pick)
                w.bind("<Enter>", _enter)
                w.bind("<Leave>", _leave)

    def _paint_action_row(self, action, hover=False, selected=False):
        import ui_compact
        return ui_compact.paint_action(self, action, hover, selected)


    def _refresh_action_styles(self):
        """按当前选中项，刷新全部操作行的底色。"""
        cur = self.action_var.get()
        for action in self.action_row_frames:
            self._paint_action_row(action, selected=(action == cur))

    # ------------------------------------------------------------ 时间设置
    def _time_group(self, parent, mode, title, pack_now=True):
        """一个时间设置板块，返回可放内容的内部 Frame。

        v1.3.1 改动（用户反馈「找不到日期这个选项」）：
        v1.3.0 把「切换模式的单选钮」放进了各自板块的框内并随板块一起折叠 ——
        结果是**只有当前选中那个模式的入口可见**，另外两个模式（尤其是「日期」）
        就没有任何入口了，用户根本切不过去。这是一个真实的可用性缺陷。

        现在拆成两层：
          · 模式入口统一收到上方的 `_build_mode_selector()` 里（三个按钮常显）；
          · 板块自己只剩一个标题标签 + 内容区，不再承载单选钮。

        pack_now=False 时不立刻 pack —— 用于「三个模式只显示当前选中那个」
        的折叠交互（见 self._refresh_time_groups）。控件仍然创建，
        所以 timer_panel 的子控件数量不变，测试契约照旧。
        """
        p = theme.p
        # 外框：视觉上的"卡片"（浅描边），不承载标题
        outer = tk.Frame(parent, bg=p["card"], bd=0, highlightthickness=1,
                         highlightbackground=p["card_border"],
                         highlightcolor=p["card_border"])
        # 标记：测试脚本靠它识别「时间板块」（v1.3.0 起是 Frame 而非 Labelframe）
        outer._time_group_mode = mode
        if not hasattr(self, "time_groups"):
            self.time_groups = {}
        self.time_groups[mode] = outer
        if pack_now:
            outer.pack(fill="x", pady=(0, GROUP_GAP))

        # 标题标签：只是说明"下面这一块是什么"，不再承担切换职责。
        # 用 Label 而不是 Radiobutton —— 后者在 disabled/未选中时会出现
        # 一圈灰色指示器（正是用户说的"土里土气"来源之一）。
        tk.Label(outer, text=title, bg=p["card"], fg=p["fg"],
                 font=theme.font(bold=True), anchor="w", padx=2).pack(
            fill="x", padx=8, pady=(6, 0))

        inner = tk.Frame(outer, bg=p["card"])
        inner.pack(fill="x", padx=10, pady=(4, 8))
        return inner

    def _build_mode_selector(self, parent):
        """三个时间模式常显的切换入口（v1.3.1 新增，修「找不到日期选项」）。

        形态：一行三个等宽胶囊，选中那个用主题色实心，其余描边款。
        为什么不做成 ttk.Notebook 的标签页：本程序固定尺寸窗口，
        Notebook 会额外吃掉几像素高的标签栏，而且它的标签样式在 clam 下
        很难调成参考图那种干净观感（v1.3.0 建版式时已经权衡过一次）。

        返回外框 Frame；三个按钮存进 self.mode_btns，选中态由
        _refresh_mode_btns() 统一切换。
        """
        p = theme.p
        wrap = tk.Frame(parent, bg=p["card"])
        wrap.pack(fill="x", pady=(0, GROUP_GAP))
        self.mode_bar = wrap

        tk.Label(wrap, text=self.T("group_mode"), bg=p["card"], fg=p["fg"],
                 font=theme.font(bold=True), anchor="w").pack(fill="x", padx=2)

        row = tk.Frame(wrap, bg=p["card"])
        row.pack(fill="x", pady=(4, 0))
        self.mode_btn_row = row
        for c in range(len(MODE_KEYS)):
            row.grid_columnconfigure(c, weight=1, uniform="modebtn")

        labels = {
            M_COUNTDOWN: self.T("group_countdown"),
            M_DATETIME: self.T("group_datetime"),
            M_INTERVAL: self.T("group_interval"),
        }
        self.mode_btns = {}
        for c, mode in enumerate(MODE_KEYS):
            b = flat_button(row, labels[mode],
                            (lambda m=mode: self._pick_mode(m)),
                            kind="plain", pady=5, padx=4,
                            font=theme.font(bold=True))
            # 关键：显式把最小宽度定成同一个值。
            # grid 的 weight+uniform 只在"容器有富余空间可分配"时才保证等宽；
            # 三个按钮的自然宽度本来就不同（"倒计时" 3 字 vs "指定时刻" 4 字），
            # 实测选中那个（实心、字重相同）会被撑到 112px、另两个 107px，
            # 差 5px 肉眼能看出来。这里用 width 统一"字符数宽度"堵掉。
            b.config(width=6)
            b.grid(row=0, column=c, sticky="ew", padx=(0 if c == 0 else 5, 0))
            self.mode_btns[mode] = b
        self._refresh_mode_btns()

    def _pick_mode(self, mode):
        """点模式按钮：改单选变量 + 刷新按钮态 + 展开对应板块。"""
        try:
            self.mode_var.set(mode)
            self.cfg["mode"] = mode
        except Exception:
            pass
        self._refresh_mode_btns()
        self._refresh_time_groups()
        try:
            self.root.after(20, lambda: self._focus_first_time_widget())
        except Exception:
            pass

    def _refresh_mode_btns(self):
        import ui_compact
        return ui_compact.paint_modes(self)


    def _refresh_time_groups(self):
        """三个时间模式只显示**当前选中的那一个**，其余收起。

        为什么这么改（v1.3.0 的核心交互变更）：
        旧版三个板块（倒计时 / 日期 / 时间段）全堆在一页，窗口被撑到很高，
        在 1080p 屏上接近半屏；而且用户每次只用一种模式，另外两块纯属干扰。
        改成"选中即展开"后：一屏只呈现当前要填的东西，干净且矮，
        与「小清新 + 一页一主题」的设计意图一致。

        v1.3.1 修（用户反馈「少了日期这个选项」）：
        原来切换入口藏在各板块自己的标题行里、随板块一起折叠，导致
        非当前模式**没有任何入口**。现在入口统一提到
        `_build_mode_selector()` 的三个常显按钮上，这里只管展开/收起。
        """
        if not getattr(self, "time_groups", None):
            return
        cur = self.mode_var.get()
        # 锚点用按钮排：时间板块统一 pack 到它之前，
        # 于是顺序恒为「快捷预设 → 模式入口 → 展开的板块 → 按钮排 → spacer」。
        anchor = getattr(self, "time_btn_row", None)
        for mode, frame in self.time_groups.items():
            try:
                if mode == cur:
                    if anchor is not None:
                        frame.pack(fill="x", pady=(0, GROUP_GAP), before=anchor)
                    else:
                        frame.pack(fill="x", pady=(0, GROUP_GAP))
                else:
                    frame.pack_forget()
            except Exception:
                try:
                    if mode == cur:
                        frame.pack(fill="x", pady=(0, GROUP_GAP))
                    else:
                        frame.pack_forget()
                except Exception:
                    pass
        try:
            self.root.update_idletasks()
        except Exception:
            pass

    def _col_min(self):
        """每列最小宽度：跟随字号，保证「小时数」等文字完整显示不被裁切。"""
        return max(58, int(theme.base_size * 6.6))

    def _fit_cols(self, frame, count):
        for i in range(count):
            frame.grid_columnconfigure(i, minsize=self._col_min())

    def _spin(self, parent, text, var, maximum, row, col, fmt="%02.0f"):
        tk.Label(parent, text=text, bg=theme.c("card"), fg=theme.c("fg_dim"),
                 font=theme.font(delta=-1)).grid(row=row, column=col, sticky="w",
                                                 padx=(1, 1), pady=(0, 1))
        sp = ttk.Spinbox(parent, from_=0, to=maximum, width=4, textvariable=var,
                         format=fmt, justify="center")
        sp.grid(row=row + 1, column=col, padx=(1, 2), sticky="w", pady=(0, 1))
        return sp

    def _build_timer_panel(self, parent):
        import ui_compact
        return ui_compact.build_timer(self, parent)

    def _build_timer_panel_legacy(self, parent):
        """「第 2 步：设定执行时间」卡片（v1.3.0 版式）。

        保留 self.timer_panel（ui_smoke 会进去数 Labelframe），
        但外层从裸 Frame 换成白底卡片，并加一行步骤标题 + 说明。
        """
        T = self.T
        p = theme.p
        box, body, _ = section_card(parent, title=T("panel_time"),
                                    desc=T("panel_time_desc"),
                                    wrap=self._hint_wrap())
        box.pack(fill="both", expand=True)
        self.timer_box = box

        panel = tk.Frame(body, bg=p["card"])
        panel.pack(fill="both", expand=True)
        self.timer_panel = panel

        # ---- 快捷预设（v1.2.0 新增）
        #      日常最高频的几个时刻一键搞定：点一下就把时间填好并直接开始，
        #      比一格一格填「天 / 时 / 分 / 秒」快得多。
        #      v1.3.0：外观改为卡片内嵌的浅色块（去掉 groove 立体边框）。
        #      v1.3.1：最后两个按钮的时间改为**可在设置里自定义**
        #              （quick_at_today / quick_at_tomorrow），
        #              按钮文案实时跟着设置走，所以这里不写死文本。
        gp = tk.LabelFrame(panel, text="   " + T("quick_group") + "   ",
                           bg=p["card"], fg=p["fg"],
                           font=theme.font(bold=True), bd=0, relief="flat",
                           labelanchor="nw", highlightthickness=1,
                           highlightbackground=p["card_border"],
                           highlightcolor=p["card_border"])
        gp.pack(fill="x", pady=(2, GROUP_GAP))
        prow = tk.Frame(gp, bg=p["card"])
        prow.pack(fill="x", padx=6, pady=(2, 6))
        self.preset_row = prow
        for c in range(QUICK_COLS):
            prow.grid_columnconfigure(c, weight=1, uniform="quickbtn")
        # 前 4 个是固定规格，后 2 个走配置（见 quick_preset_specs）
        self.preset_btns = {}
        for i, (key, spec) in enumerate(QUICK_PRESETS):
            r, c = divmod(i, QUICK_COLS)
            b = flat_button(prow, T(key), (lambda s=spec: self.apply_preset(s)),
                            kind="plain", pady=3, padx=2,
                            font=theme.font(delta=-1))
            b.grid(row=r, column=c, sticky="ew",
                   padx=(0 if c == 0 else 4, 0),
                   pady=(0 if r == 0 else 3, 0))
            self.preset_btns[key] = b
        self._refresh_preset_labels()

        # ---- 模式切换入口（v1.3.1 新增：修「找不到日期选项」）
        self._build_mode_selector(panel)

        # ---- 倒计时
        g = self._time_group(panel, M_COUNTDOWN, T("group_countdown"), pack_now=False)
        self.cd_days = tk.StringVar(value=str(self.cfg.get("cd_days")))
        self.cd_h = tk.StringVar(value="%02d" % int(self.cfg.get("cd_hours")))
        self.cd_m = tk.StringVar(value="%02d" % int(self.cfg.get("cd_minutes")))
        self.cd_s = tk.StringVar(value="%02d" % int(self.cfg.get("cd_seconds")))
        self._fit_cols(g, 4)
        tk.Label(g, text=T("lbl_days"), bg=p["card"], fg=p["fg_dim"],
                 font=theme.font(delta=-1)).grid(row=0, column=0, sticky="w",
                                                 padx=(1, 1), pady=(0, 1))
        ttk.Combobox(g, width=4, textvariable=self.cd_days, justify="center",
                     values=[str(i) for i in range(0, 61)]).grid(
            row=1, column=0, padx=(1, 2), sticky="w", pady=(0, 1))
        self._spin(g, T("lbl_hours"), self.cd_h, 23, 0, 1)
        self._spin(g, T("lbl_minutes"), self.cd_m, 59, 0, 2)
        self._spin(g, T("lbl_seconds"), self.cd_s, 59, 0, 3)

        # ---- 日期（星期几 + 时刻）
        g2 = self._time_group(panel, M_DATETIME, T("group_datetime"), pack_now=False)
        self.weekday_var = tk.StringVar()
        self.dt_h = tk.StringVar(value="%02d" % int(self.cfg.get("dt_hour")))
        self.dt_m = tk.StringVar(value="%02d" % int(self.cfg.get("dt_minute")))
        self.dt_s = tk.StringVar(value="%02d" % int(self.cfg.get("dt_second")))
        self._fit_cols(g2, 4)
        tk.Label(g2, text=T("lbl_weekday"), bg=p["card"], fg=p["fg_dim"],
                 font=theme.font(delta=-1)).grid(row=0, column=0, sticky="w",
                                                 padx=(1, 1), pady=(0, 1))
        self.weekday_box = ttk.Combobox(g2, width=7, state="readonly",
                                        textvariable=self.weekday_var, justify="center")
        self.weekday_box.grid(row=1, column=0, sticky="w", padx=(1, 2), pady=(0, 1))
        self._spin(g2, T("lbl_h_short"), self.dt_h, 23, 0, 1)
        self._spin(g2, T("lbl_m_short"), self.dt_m, 59, 0, 2)
        self._spin(g2, T("lbl_s_short"), self.dt_s, 59, 0, 3)

        # ---- 时间段
        g3 = self._time_group(panel, M_INTERVAL, T("group_interval"), pack_now=False)
        self.iv_h = tk.StringVar(value="%02d" % int(self.cfg.get("iv_hours")))
        self.iv_m = tk.StringVar(value="%02d" % int(self.cfg.get("iv_minutes")))
        self.iv_s = tk.StringVar(value="%02d" % int(self.cfg.get("iv_seconds")))
        self._fit_cols(g3, 3)
        self._spin(g3, T("lbl_hours"), self.iv_h, 23, 0, 0)
        self._spin(g3, T("lbl_minutes"), self.iv_m, 59, 0, 1)
        self._spin(g3, T("lbl_seconds"), self.iv_s, 59, 0, 2)

        # 时间板块插到这里 ↑（_refresh_time_groups 以 self.time_spacer 为锚点）

        # ---- 定时器按钮：四个等宽小板块（开始 / 暂停 / 停止 / 清除）
        #      用 grid + uniform 让四块严格等宽并铺满整行，跟右侧时间区同宽。
        # v1.3.0：整排改为胶囊按钮 —— 「开始」用主题色实心（主操作要最显眼），
        #         其余三个为描边款，视觉上主次分明。
        #
        # 布局顺序（重要）：板块 → 按钮排 → spacer（可伸缩，吃掉剩余高度）
        # 把 spacer 放在**按钮之后**，是为了让「内容 + 按钮」整体贴顶、
        # 多余留白沉到卡片底部 —— 比挤在中间好看得多（第一版放在按钮前，
        # 结果内容被顶到上半截、中间空一坨）。
        btn = tk.Frame(panel, bg=p["card"])
        btn.pack(fill="x", pady=(0, 0))
        self.time_btn_row = btn
        for c in range(4):
            btn.grid_columnconfigure(c, weight=1, uniform="timerbtn")
        self.btn_start = flat_button(btn, T("btn_go"), self.start_timer,
                                     kind="accent", pady=5, padx=4,
                                     font=theme.font(bold=True))
        self.btn_pause = flat_button(btn, T("btn_pause_s"), self.toggle_pause,
                                     kind="plain", pady=5, padx=4)
        self.btn_stop = flat_button(btn, T("btn_stop_s"), self.stop_timer,
                                    kind="plain", pady=5, padx=4)
        self.btn_clear = flat_button(btn, T("btn_clear"), self.clear_timer,
                                     kind="plain", pady=5, padx=4)
        self.btn_enqueue = flat_button(btn, T("btn_enqueue"), self.enqueue_current,
                                       kind="plain", pady=4, padx=4)
        for c, b in enumerate((self.btn_start, self.btn_pause,
                               self.btn_stop, self.btn_clear)):
            b.grid(row=0, column=c, sticky="ew", padx=(0 if c == 0 else 4, 0))
        # 第二行：把当前设定排进队列（v1.2.0）。横跨整行，
        # 上面那排四个按钮的等宽布局一点都不受影响。
        self.btn_enqueue.grid(row=1, column=0, columnspan=4, sticky="ew",
                              pady=(4, 0))
        enable_button(self.btn_pause, False)
        enable_button(self.btn_stop, False)

        # spacer：放在按钮排之后，吸收卡片剩余高度（见上方注释）
        spacer = tk.Frame(panel, bg=p["card"])
        spacer.pack(fill="both", expand=True)
        self.time_spacer = spacer

        self._refresh_weekdays()
        self.mode_var.set(self.cfg.get("mode") or M_COUNTDOWN)
        # v1.3.0：只展开当前选中的那个时间板块
        self._refresh_time_groups()


    def _build_footer(self, parent):
        import ui_compact
        return ui_compact.build_footer(self, parent)


    def build_ui(self):
        import ui_compact
        return ui_compact.build_ui(self)


    def _measure_window_size(self):
        import ui_compact
        return ui_compact.measure(self)


    def _lock_window_buttons(self):
        """去掉标题栏右上角的「最大化」按钮（窗口已是固定尺寸，不需要它）。

        只用 ctypes 改窗口样式（WS_MAXIMIZEBOX），不调用 reg.exe。

        Win10 / Win11 差异（重要）：
          · **Win10**：把 WS_MAXIMIZEBOX 置灰即可，按钮会变成「灰色不可点」的样子。
          · **Win11**：Win11 用了新的 DWM 标题栏绘制，**只清 MAXIMIZEBOX 时按钮
            不会真的消失**，只是点不动，看着还很突兀 —— 这正是很多小工具在
            Win11 上「最大化按钮还在但点了没反应」的原因。
            要让它真正**隐藏**，必须同时（a）保留 WS_THICKFRAME（否则窗口边框
            样式会崩）并清掉 WS_MAXIMIZEBOX，再（b）走 DWM 的
            DWMWA_NCRENDERING_POLICY 保持系统重绘。
            实测：Win11 下清掉 WS_MAXIMIZEBOX + WS_THICKFRAME 后窗口会变成
            无边框样式，所以这里改为「只清 MAXIMIZEBOX，并额外清掉
            WS_MAXIMIZE + 复核 MINIMIZEBOX 保留」，让系统按固定尺寸窗口渲染。
        """
        if hasattr(self,'titlebar'):
            from ui_titlebar import apply_chrome
            apply_chrome(self.root)
        try:
            import ctypes
            u = ctypes.windll.user32
            modal=self.root.grab_current()
            target=modal.winfo_toplevel() if modal is not None else self.root
            u.GetAncestor.argtypes=[ctypes.c_void_p,ctypes.c_uint]
            u.GetAncestor.restype=ctypes.c_void_p
            hwnd = u.GetAncestor(target.winfo_id(), 2) or target.winfo_id()
            if not hwnd or not u.IsWindow(hwnd):
                return
            u.GetWindowLongW.restype = ctypes.c_long
            u.GetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int]
            u.SetWindowLongW.restype = ctypes.c_long
            u.SetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_long]
            GWL_STYLE = -16
            WS_MAXIMIZEBOX = 0x00010000
            WS_MAXIMIZE = 0x01000000
            WS_MINIMIZEBOX = 0x00020000
            style = u.GetWindowLongW(ctypes.c_void_p(hwnd), GWL_STYLE)
            # 清掉「最大化按钮」与「最大化状态」；最小化按钮保留（要能最小化）
            new_style = (style & ~WS_MAXIMIZEBOX & ~WS_MAXIMIZE) | WS_MINIMIZEBOX
            if new_style==style:return
            u.SetWindowLongW(ctypes.c_void_p(hwnd), GWL_STYLE, new_style)
            SWP_NOSIZE, SWP_NOMOVE, SWP_NOZORDER, SWP_FRAMECHANGED = 0x1, 0x2, 0x4, 0x20
            u.SetWindowPos(ctypes.c_void_p(hwnd), None, 0, 0, 0, 0,
                           SWP_NOSIZE | SWP_NOMOVE | SWP_NOZORDER | SWP_FRAMECHANGED)

            # Win11 额外处理：新标题栏绘制下按钮容易残留，让 DWM 重新按
            # 当前样式渲染一次非客户区（属性 2 = DWMWA_NCRENDERING_POLICY，
            # DWMNCRP_ENABLED = 2）。失败也无所谓，Win10 上本来就不需要。
            try:
                dwm = ctypes.windll.dwmapi
                dwm.DwmSetWindowAttribute.restype = ctypes.c_long
                dwm.DwmSetWindowAttribute.argtypes = [
                    ctypes.c_void_p, ctypes.c_uint,
                    ctypes.POINTER(ctypes.c_int), ctypes.c_uint]
                val = ctypes.c_int(2)     # DWMNCRP_ENABLED
                dwm.DwmSetWindowAttribute(ctypes.c_void_p(hwnd), 2,
                                          ctypes.byref(val), ctypes.sizeof(val))
            except Exception:
                pass
        except Exception:
            pass

    def rebuild_ui(self):
        """切换语言 / 主题 / 字号后重建主界面。

        v1.2.0：**这里不再停表**。以前切外观一定会把定时器停掉，是当初为了
        规避「重建期间计时错乱」；现在引擎的「轮次编号（_gen）」机制已经从
        根上解决了重复启动（见 timer_engine._run 的注释），而且引擎和界面
        本来就是解耦的（事件统一走 queue 回抛主线程），所以重建界面期间
        定时器照常跑 —— 用户改个字体不会再丢掉定时。
        """
        running = self.engine.is_running()
        paused = getattr(self.engine, "paused", False)
        # 队列 / 日志窗口的文字是建窗口时按当时的语言写死的，重建时一并关掉
        for attr in ("_queue_win", "_log_win"):
            w = getattr(self, attr, None)
            if w is not None:
                try:
                    w.destroy()
                except Exception:
                    pass
                setattr(self, attr, None)
        for child in list(self.container.winfo_children()):
            child.destroy()
        self.container.destroy()
        self.root.title(self.T("app_name"))
        self.root.configure(bg=theme.c("bg"))
        self._set_icon()
        self.build_ui()
        # v1.3.1：重建会回到「选择操作」页。如果用户正停在「设定时间」页
        # （或者正在设置窗口里改快捷预设、改完顺手点「应用」），
        # 会把页面弹回首页，体验很跳。这里记一个 _prev_page 做**往返同步**，
        # 只在重建后恢复，不影响 build_ui 里「默认首页」的初始逻辑。
        try:
            prev = getattr(self, "_prev_page_key", None)
            if prev == "time":
                self.show_page("time")
        except Exception:
            pass
        self._apply_start_hidden()
        if running:
            self._set_running_ui(True)
            try:
                self.btn_pause.config(text=self.T("btn_resume_s") if paused
                                      else self.T("btn_pause_s"))
            except Exception:
                pass
            self._set_status("status_due_paused" if paused else "status_due",
                             t=format_remain(self._last_remain, self.T),
                             d=self._due_text())
        else:
            self._set_status("status_idle")

    # ================================================================ 事件
    def bind_events(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind("<Escape>", self._on_esc)
        self.root.bind("<F5>", lambda e: self.start_timer())

    def _on_esc(self, _e=None):
        if self.cfg.get("esc_to_minimize"):
            self.root.iconify()

    def _on_action_pick(self):
        self.cfg["action"] = self.action_var.get()
        self._refresh_details()
        try:
            self._refresh_action_styles()
        except Exception:
            pass

    def _on_mode_pick(self):
        self.cfg["mode"] = self.mode_var.get()
        # v1.3.1：切换时间模式时，同步刷新模式按钮态 + 展开对应板块、收起其它两个
        try:
            self._refresh_mode_btns()
        except Exception:
            pass
        try:
            self._refresh_time_groups()
        except Exception:
            pass

    def _refresh_details(self):
        import ui_compact
        return ui_compact.refresh_details(self)


    def _refresh_weekdays(self):
        names = weekday_names(self.T.lang)
        self.weekday_box["values"] = names
        idx = int(self.cfg.get("dt_weekday", 1)) % 7
        self.weekday_box.current(idx)

    # ------------------------------------------------------------ 选择文件
    def pick_for(self, action):
        T = self.T
        if action == A_RUN:
            path = filedialog.askopenfilename(
                parent=self.root, title=T("dlg_pick_program"),
                filetypes=[(T("dlg_files"), "*.exe;*.bat;*.cmd;*.com;*.lnk;*.msc;*.ps1"),
                           (T("dlg_all_files"), "*.*")])
            if path:
                self.cfg["program_path"] = path
                self.action_var.set(A_RUN)
                self.cfg["action"] = A_RUN
        elif action == A_CLOSE:
            from ui_close_program import CloseProgramDialog
            dlg = CloseProgramDialog(self)
            self.root.wait_window(dlg)
            if dlg.result:
                self.cfg["close_program_path"] = dlg.result
                self.action_var.set(A_CLOSE)
                self.cfg["action"] = A_CLOSE
        elif action == A_SOUND:
            from ui_sound import SoundDialog
            dlg = SoundDialog(self)
            self.root.wait_window(dlg)
            path = dlg.result
            if path:
                self.cfg["sound_file"] = path
                self.action_var.set(A_SOUND)
                self.cfg["action"] = A_SOUND
        else:
            from ui_dialogs import MessageInputDialog
            dlg = MessageInputDialog(self.root, T, self.cfg.get("message_text") or "")
            self._apply_window_chrome(dlg)
            self.root.wait_window(dlg)
            if dlg.result is not None:
                self.cfg["message_text"] = dlg.result
                self.action_var.set(A_MESSAGE)
                self.cfg["action"] = A_MESSAGE
        self._refresh_details()

    # ------------------------------------------------------------ 定时器
    def _read_time(self, mode):
        def num(var, default=0):
            try:
                return int(str(var.get()).strip() or 0)
            except Exception:
                return default
        if mode == M_COUNTDOWN:
            total = (num(self.cd_days) * 86400 + num(self.cd_h) * 3600
                     + num(self.cd_m) * 60 + num(self.cd_s))
            return total, total
        if mode == M_INTERVAL:
            total = num(self.iv_h) * 3600 + num(self.iv_m) * 60 + num(self.iv_s)
            return total, total
        return 0, 0

    def start_timer(self):
        import task_features
        return task_features.start_current(self)


    def _save_time_fields(self):
        def num(v):
            try:
                return int(str(v.get()).strip() or 0)
            except Exception:
                return 0
        self.cfg.update({
            "cd_days": num(self.cd_days), "cd_hours": num(self.cd_h),
            "cd_minutes": num(self.cd_m), "cd_seconds": num(self.cd_s),
            "iv_hours": num(self.iv_h), "iv_minutes": num(self.iv_m),
            "iv_seconds": num(self.iv_s),
        })

    def toggle_pause(self):
        if self.engine.paused:
            self.engine.resume()
        else:
            self.engine.pause()

    def stop_timer(self):
        self.engine.stop()
        self._close_cancel_toast()
        self._set_running_ui(False)
        self.progress["value"] = 0
        self._set_status("status_stopped")
        self._log(run_log.KIND_CANCEL, "log_stop_text")
        if hasattr(self,'_paint_pin'):self._paint_pin()
        if self.tray:
            self.tray.refresh()

    def clear_timer(self):
        """清除：停表 + 时间输入复位 + **清空队列**（不动已选操作 / 外观 / 语言）。"""
        self.engine.stop()
        self._close_cancel_toast()
        self._set_running_ui(False)
        self.progress["value"] = 0
        self._active_task = None
        self.task_queue = []
        self._save_queue()

        self.cd_days.set("0")
        for var in (self.cd_h, self.cd_m, self.cd_s,
                    self.iv_h, self.iv_m, self.iv_s,
                    self.dt_h, self.dt_m, self.dt_s):
            try:
                var.set("00")
            except Exception:
                pass
        self._save_time_fields()
        self._set_status("status_cleared")
        self._log(run_log.KIND_INFO, "log_clear_text")
        if self._queue_win:
            try:
                self._queue_win.refresh()
            except Exception:
                pass
        if hasattr(self,'_paint_pin'):self._paint_pin()
        if self.tray:
            self.tray.refresh()

    def _set_running_ui(self, running):
        self._running = running
        pause_text = self.T("btn_resume_s") if self.engine.paused else self.T("btn_pause_s")
        try:
            enable_button(self.btn_pause, running)
            enable_button(self.btn_stop, running)
            self.btn_pause.config(text=pause_text)
        except Exception:
            pass

        from ui_summary import refresh
        refresh(self)

    def _set_status(self, key, **kw):
        """状态栏唯一写入口，始终直接显示最新状态。"""
        self._status_key = (key, kw)
        try:
            self.status.config(text=self.T(key, **kw))
        except Exception:
            pass

        from ui_summary import refresh
        refresh(self)

    # ------------------------------------------------------------ 执行动作
    def _current_action(self):
        return self.action_var.get()

    def _validate_action(self, action, settings=None):
        T = self.T
        settings = self.cfg if settings is None else settings
        if action == A_RUN and not (settings.get("program_path") or "").strip():
            messagebox.showinfo(T("tip_title"), T("tip_need_program"), parent=self.root)
            return False
        if action == A_CLOSE:
            from program_control import validate_target
            try: validate_target(settings.get("close_program_path"))
            except ValueError as exc:
                messagebox.showinfo(T("tip_title"), i18n.feature_text(T, str(exc)), parent=self.root)
                return False
        if action == A_SOUND:
            from sound_library import resolve
            if not resolve(settings.get("sound_file")):
                messagebox.showinfo(T("tip_title"), T("tip_need_sound"), parent=self.root)
                return False
        if action == A_MESSAGE and not (settings.get("message_text") or "").strip():
            messagebox.showinfo(T("tip_title"), T("tip_need_message"), parent=self.root)
            return False
        return True

    def _need_confirm(self, action):
        if not self.cfg.get("confirm_before_action"):
            return False
        if self.cfg.get("confirm_key_only") and action not in KEY_ACTIONS:
            return False
        return True

    def perform_action(self, action, ask=True):
        T = self.T
        settings = dict(self.cfg.data)
        if not ask and self._active_task:
            for key in ("program_path", "close_program_path", "sound_file", "message_text", "force_close_apps"):
                if key in self._active_task: settings[key] = self._active_task[key]
        if not self._validate_action(action, settings):
            return False
        if ask and self._need_confirm(action) and not self._confirm_skipped:
            # v1.2.0：确认框换成自绘对话框，多一个「本次启动不再询问」
            # （messagebox 塞不进去勾选项）。勾了只对本次进程生效，不写配置。
            from ui_dialogs import ConfirmActionDialog
            dlg = ConfirmActionDialog(self.root, T,
                                      T("tip_confirm_action",
                                        a=action_label(action, T)))
            self._apply_window_chrome(dlg)
            self.root.wait_window(dlg)
            if not dlg.result:
                return False
            if dlg.dont_ask:
                self._confirm_skipped = True
        self._log(run_log.KIND_INFO, "log_exec_text", a=action_label(action, T))
        if action == A_MESSAGE:
            self.show_toast(settings.get("message_text") or "")
            self._set_status("status_executed", a=action_label(action, T))
            self._log(run_log.KIND_DONE, "log_done_text", a=action_label(action,T),ok=True)
            return True

        def worker():
            ok, err = perform(action, settings)
            if not ok:
                self.queue.put(("action_error", {"err": err, "action": action}))
            else:
                self.queue.put(("action_done", {"action": action}))
        threading.Thread(target=worker, daemon=True, name="HaozaiziAction").start()
        return True

    def perform_now(self):
        action = self._current_action()
        self._validate_action(action)
        self.perform_action(action, ask=True)

    def tray_start_timer(self):
        self.show_window()
        self.start_timer()

    # ------------------------------------------------------------ 提示框
    def show_toast(self, text, seconds=None):
        """弹出淡出提示框。seconds 不传就取设置里的「消息提示框停留时长」（v1.2.0）。"""
        from ui_dialogs import FadeMessageBox
        if seconds is None:
            try:
                seconds = int(self.cfg.get("toast_seconds", 15))
            except Exception:
                seconds = 15
        seconds = max(3, min(600, seconds))
        if self.toast is not None:
            try:
                self.toast.close()
            except Exception:
                pass
        self.toast = FadeMessageBox(self.root, self.T("app_name"), text, seconds=seconds,
                                    on_close=self._toast_closed)

    def _toast_closed(self):
        self.toast = None

    # ------------------------------------------------------------ 到点前可取消
    def _show_cancel_toast(self):
        """到点前 10 秒弹一个带「取消执行」按钮的提示框（v1.2.0）。

        以前一旦进入最后 10 秒就只能眼睁睁看着它执行（想反悔只有提前去点停止）；
        现在给一个明确的出口。
        """
        from ui_dialogs import FadeMessageBox
        import math
        warning=max(1,min(int(self.cfg.get("warning_seconds",10)),math.ceil(self.engine.remaining())))
        task = self._active_task or {}
        action = task.get("action") or self._current_action()
        self._close_cancel_toast()
        try:
            toast = FadeMessageBox(
                self.root, self.T("tip_cancel_title"),
                self.T("cancel_toast_text", a=action_label(action, self.T),
                       s=warning),
                seconds=warning, on_close=lambda: self._cancel_toast_closed(toast),
                button_text=self.T("btn_cancel_action"),
                on_button=self._cancel_by_user,
                extra_buttons=[(f"延后 {m} 分钟", lambda minutes=m: self.postpone(minutes)) for m in (5,10,30)])
            self.cancel_toast = toast
        except Exception as exc:
            self.cancel_toast = None
            self._cancel_toast_error = str(exc)

    def _cancel_toast_closed(self, toast=None):
        if toast is None or self.cancel_toast is toast:
            self.cancel_toast = None

    def _close_cancel_toast(self):
        t = self.cancel_toast
        self.cancel_toast = None
        if t is not None:
            try:
                t.close()
            except Exception:
                pass

    def _cancel_by_user(self):
        """用户在提示框里点了「取消执行」。"""
        self.engine.stop()
        self._set_running_ui(False)
        self.progress["value"] = 0
        self._set_status("status_cancelled")
        self._log(run_log.KIND_CANCEL, "log_cancel_text")
        if hasattr(self,'_paint_pin'):self._paint_pin()
        if self.tray:
            self.tray.refresh()

    # ------------------------------------------------------------ 引擎事件
    def emit(self, event, payload):
        """由计时线程调用，只做入队。"""
        self.queue.put((event, payload))

    def _pump(self):
        if getattr(self,"_closing_app",False):return
        # Native restore can arrive without a Tk Map event; complete it on
        # the existing UI pump, without Tcl calls from the Win32 callback.
        if getattr(self.root,"_native_restore_cloaked",False) and self.root.state()=="normal":
            from ui_window import present_main
            present_main(self.root)
        self._poll_single_instance()
        import time
        budget=time.perf_counter()+.008
        try:
            for _ in range(100):
                event, payload = self.queue.get_nowait()
                self._handle(event, payload)
                if getattr(self,"_closing_app",False):return
                if time.perf_counter()>=budget:break
        except queue.Empty:
            pass
        self.root.after(1 if not self.queue.empty() else 100, self._pump)

    def _handle(self, event, payload):
        if event == "ui_call":
            payload["func"](*payload["args"])
            return
        if event == "automation_state":
            self.automation.handle(payload)
            return
        T = self.T
        # 作废轮次的 tick / warn / finished 全部丢弃，取消后不执行旧到点动作。
        # 不丢的话，「取消执行 / 清除」之后状态栏会被一条迟到的旧 tick
        # 覆盖回「定时器运行中」，用户以为取消没生效。
        if event in ("tick", "warn", "finished"):
            _g = payload.get("gen")
            if _g is not None and _g != self.engine.generation:
                return
        if event == "tick":
            remain = payload["remain"]
            self._last_remain = remain
            self.progress["value"] = payload.get("percent", 0.0)
            # v1.2.0：状态栏除了剩余时间，再给出「预计几点执行」
            key = "status_due_paused" if self.engine.paused else "status_due"
            self._set_status(key, t=format_remain(remain, T), d=self._due_text())
        elif event == "warn":
            if self.cfg.get("sound_at_10s"):
                beep_warning()
            if self.cfg.get("popup_at_10s"):
                self.show_window()
            if self.cfg.get("cancel_at_10s", True):
                self._show_cancel_toast()
        elif event == "paused":
            self._close_cancel_toast()
            self._set_status("status_due_paused",
                             t=format_remain(payload.get("remain", 0), T),
                             d=self._due_text())
            try:
                self.btn_pause.config(text=T("btn_resume_s"))
            except Exception:
                pass
            if self.tray:
                self.tray.refresh()
        elif event == "resumed":
            try:
                self.btn_pause.config(text=T("btn_pause_s"))
            except Exception:
                pass
        elif event == "started":
            self._set_running_ui(True)

            if self.tray:
                self.tray.refresh()
        elif event == "stopped":
            self._close_cancel_toast()
            if not self.engine.is_running():
                self._set_running_ui(False)
                self.progress["value"] = 0
        elif event == "finished":
            # 动作取「当前正在跑的那个任务」，而不是界面上此刻选中的操作 ——
            # 队列模式下用户完全可能已经改了界面选择，用界面值会执行错动作。
            task = self._active_task or {}
            action = task.get("action") or self._current_action()
            if payload.get("repeat"):
                self.perform_action(action, ask=False)
                self._set_status("status_executed", a=action_label(action, T))
            else:
                self._close_cancel_toast()
                self._set_running_ui(False)
                self.progress["value"] = 100
                self.perform_action(action, ask=False)
                self._set_status("status_executed", a=action_label(action, T))
                if self.tray:
                    self.tray.refresh()
                # 跑完的这个任务从队列里摘掉，稍后接着跑下一个
                queued = self._active_task is not None and self._active_task in self.task_queue
                if queued:
                    self.task_queue.remove(self._active_task)
                    self._save_queue()
                    self.cfg.save()
                self._active_task = None

                # A directly started single task never resumes an unrelated queue.
                if queued and self.task_queue:
                    generation=self.engine.generation
                    self.root.after(1200,lambda:self._start_next_task() if self.engine.generation==generation else None)
        elif event == "action_done":
            a = payload.get("action") or self._current_action()
            self._set_status("status_executed", a=action_label(a, T))
            self._log(run_log.KIND_DONE, "log_done_text",
                      a=action_label(a, T), ok=True)
        elif event == "action_error":
            a = payload.get("action") or self._current_action()
            err = str(payload.get("err"))
            self._log(run_log.KIND_ERROR, "log_error_text",
                      a=action_label(a, T), ok=False, detail=err)
            messagebox.showwarning(T("tip_title"), err, parent=self.root)

    # ================================================================ 窗口行为
    def show_window(self):
        try:
            from ui_workspace import restore_workspace
            restore_workspace(self)
        except Exception:
            pass
        # 窗口重新显示后，再确认一次「最大化」按钮处于隐藏状态。
        # 标题栏颜色不在这里补 —— 之前已经在窗口隐藏状态下设好，
        # 重新显示本身就是一次「隐藏→显示」，DWM 会直接按深色画出来；
        # 这里再补一次反而会把这个窗口多闪一下。
        self._lock_window_buttons()

    # ================================================================ 单实例
    def _poll_single_instance(self):
        """有别的实例启动时（它已用 SetEvent 通知我们），把窗口唤到前台。

        为什么用轮询而不是直接收 Windows 消息：
        复用主事件队列的检查，不再额外创建 400 ms 的 Tk 定时器。
        Tk 没有对外暴露「任意 Win32 消息」的回调口子，自己子类化窗口过程太重。
        改成已有实例定时问一次事件对象 —— 收到通知后走的是本进程自己的
        show_window()，Tk 的窗口状态永远是对的（这一点比 FindWindow +
        外部 ShowWindow 可靠得多，后者会让 Tk 内部状态和实际可见性脱节）。
        """
        try:
            if self._single is not None and self._single.has_pending_show():
                self.show_window()
                self._force_foreground()
        except Exception:
            pass

    def _force_foreground(self):
        """尽量把窗口抢到最前面。

        Windows 有「前台窗口锁定」：非前台进程调 SetForegroundWindow 可能被
        直接拒绝。Tk 的 focus_force() 已经试过一次，这里再补一次原生调用；
        若仍被拒，就用「先最小化再还原」绕一下（系统会把这当作由用户操作
        引发的前台切换，从而放行）。
        """
        try:
            import ctypes
            u = ctypes.windll.user32
            modal=self.root.grab_current()
            target=modal.winfo_toplevel() if modal is not None else self.root
            u.GetAncestor.argtypes=[ctypes.c_void_p,ctypes.c_uint]
            u.GetAncestor.restype=ctypes.c_void_p
            hwnd = u.GetAncestor(target.winfo_id(), 2) or target.winfo_id()
            if not hwnd or not u.IsWindow(hwnd):
                return
            u.SetForegroundWindow.argtypes = [ctypes.c_void_p]
            u.SetForegroundWindow.restype = ctypes.c_int
            if u.SetForegroundWindow(ctypes.c_void_p(hwnd)):
                return
            # 焦点限制不应通过再次最小化/还原绕过，否则会再启动一轮闪帧。
            u.BringWindowToTop(ctypes.c_void_p(hwnd))
            u.SetForegroundWindow(ctypes.c_void_p(hwnd))
        except Exception:
            pass

    def _apply_start_hidden(self):
        """按 /min 启动时，把主窗口明确收起来（不依赖任何副作用）。

        为什么单独做一个方法（v1.1.4）：
        原来 /min 的窗口是靠 `_apply_dark_titlebar` 里那次
        「ShowWindow(SW_HIDE) → SW_SHOWNOACTIVATE」顺带收掉的 —— 一旦深浅色
        已经是目标值，那个函数会提前 return（省掉一次没必要的闪烁），
        结果窗口就留在屏幕上了。启动行为不该依赖别的函数的副作用，
        所以这里改成显式的：等窗口真正建好（约 0.35 秒，等 DWM 刷完标题栏）
        再 withdraw 一次，避免"先闪一下再消失"。
        """
        if not self.cli.get("minimized") or self.cli_help_only:
            return
        try:
            self.root.after(350, self._withdraw_at_start)
        except Exception:
            pass

    def _withdraw_at_start(self):
        try:
            self.root.withdraw()
        except Exception:
            pass

    def hide_to_tray(self, hint=False):
        """最小化：优先收进托盘；托盘不可用时退回普通最小化，避免窗口“消失”。

        hint：
          · False（默认）—— 用户**主动最小化**（点最小化按钮 / 按 ESC），
            他知道窗口去哪了，**不再弹托盘提醒**。v1.2.1 起静默。
          · True —— 用户点「×」关闭窗口，他多半以为程序被关掉了，
            这时给一次「已收进托盘」的说明。每个程序只提醒一次。
        """
        tray_ok = bool(self.tray and self.tray.available())
        if not tray_ok or not self.cfg.get("minimize_to_tray", True):
            try:
                self.root.iconify()
                return
            except Exception:
                pass
        from ui_workspace import hide_workspace
        hide_workspace(self)
        if hint and self.tray and not self._tray_hint_shown:
            self._tray_hint_shown = True
            self.tray.notify(self.T("app_name"), self.T("tray_minimized_tip"))

    def on_close(self):
        """点窗口右上角 × ：按设置缩到托盘，或（确认后）真正退出。"""
        T = self.T
        tray_ok = bool(self.tray and self.tray.available())
        if self.cfg.get("minimize_to_tray", True) and tray_ok:
            # 点 × 会让人以为程序已被关闭 → 给一次「已收进托盘」说明（只一次）
            self.hide_to_tray(hint=True)
            return
        if self.cfg.get("confirm_on_exit"):
            only_timer = self.cfg.get("confirm_on_exit_only_timer", True)
            if (not only_timer) or self.engine.is_running():
                if not messagebox.askyesno(T("tip_title"), T("tip_exit_confirm"), parent=self.root):
                    return
        self.quit_app()

    def quit_app(self):
        from ui_workspace import allow_exit
        if not allow_exit(self):return
        self._closing_app=True
        if getattr(self, "floating", None): self.floating.close()
        self.display_awake.close()
        if getattr(self, "automation", None): self.automation.close()
        try:
            self._save_time_fields()
            self.cfg.update({"action": self._current_action(), "mode": self.mode_var.get()})
            self._save_queue()
            self._save_pending_timer()
            self.cfg.save()
        except Exception:
            pass
        try:
            stop_sound()
            self.engine.stop()
        except Exception:
            pass
        if self.tray:
            self.tray.stop()
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass

    # ================================================================ 设置 / 关于
    def toggle_floating(self):
        previous=bool(self.cfg.get('float_enabled'));self.cfg['float_enabled']=not previous
        if not self.cfg.save():
            self.cfg['float_enabled']=previous
            messagebox.showerror(self.T('tip_title'),self.T('float_save_error'),parent=self.root);return
        self.floating.apply()
        settings=getattr(self,'_settings_win',None)
        if settings and settings.winfo_exists():
            settings.sync_external('float_enabled',not previous)
        if self.tray:self.tray.refresh()

    def open_settings(self):
        from ui_workspace import active_modal
        modal=active_modal(self.root)
        if modal is not None:return modal
        from ui_settings import SettingsWindow
        win = self._settings_win
        if win is not None:
            try:
                if win.winfo_exists():
                    from ui_window import activate_dialog
                    activate_dialog(win)
                    return win
            except Exception:
                pass
        self._settings_win = SettingsWindow(self)
        self._apply_window_chrome(self._settings_win)
        return self._settings_win

    def open_params(self):
        from ui_dialogs import ParamDialog
        win = ParamDialog(self.root, self.T)
        self._apply_window_chrome(win)
        return win

    def open_about(self):
        from ui_dialogs import AboutDialog
        win = AboutDialog(self.root, self.T, self._img("assets/icon.png", 72))
        self._apply_window_chrome(win)
        return win

    def open_task_center(self, tab='queue', parent=None):
        from ui_workspace import active_modal
        modal=active_modal(self.root)
        if modal is not None:return modal
        from ui_task_center import TaskCenter
        win=getattr(self,'_task_center_win',None)
        if win and win.winfo_exists():
            win.select_tab(tab)
            from ui_window import activate_dialog
            activate_dialog(win);return win
        win=TaskCenter(self, tab=tab, parent=parent)
        self._task_center_win=self._queue_win=self._advanced_win=win
        return win

    def open_queue(self):
        return self.open_task_center('queue')

    def open_log(self):
        """打开「执行日志」窗口。"""
        from ui_workspace import active_modal
        modal=active_modal(self.root)
        if modal is not None:return modal
        from ui_log import LogWindow
        win = self._log_win
        if win is not None:
            try:
                if win.winfo_exists():
                    win.refresh()
                    from ui_window import activate_dialog
                    activate_dialog(win)
                    return win
            except Exception:
                pass
        self._log_win = LogWindow(self)
        self._apply_window_chrome(self._log_win)
        return self._log_win

    # ============================================================ v1.2.0 新增
    # 执行日志 / 下次触发时刻 / 快捷预设 / 定时任务队列 / 定时状态持久化
    def _log(self, kind, key, ok=None, detail="", **kw):
        """写一条执行日志（受设置开关控制；出任何问题都不影响主流程）。"""
        try:
            desktop=getattr(self,'desktop',None)
            if desktop and kind in ('setup','done','error'):desktop.notify(kind,self.T(key,**kw))
            if not self.cfg.get("log_enabled", True):
                return
            run_log.add(kind, self.T(key, **kw), ok=ok, detail=detail)
        except Exception:
            pass

    def _due_text(self):
        """状态栏用的「预计 HH:MM:SS 执行」。"""
        due = self.engine.due_at()
        return due.strftime("%H:%M:%S") if due else "--:--:--"

    def _log_setup(self, task, target=None):
        """记录一次「设定定时」。"""
        try:
            a = action_label(task.get("action") or self._current_action(), self.T)
            if task.get("mode") == M_DATETIME:
                when = (target or next_datetime(task.get("weekday", 0),
                                                task.get("hour", 0),
                                                task.get("minute", 0),
                                                task.get("second", 0))
                        ).strftime("%Y-%m-%d %H:%M:%S")
            else:
                when = self.T("when_after",
                              t=format_remain(task.get("seconds", 0), self.T))
            self._log(run_log.KIND_SETUP, "log_setup_text", a=a, w=when)
        except Exception:
            pass

    # ------------------------------------------------------------ 快捷预设
    def preset_spec(self, spec):
        """把 "cfg_at"/"cfg_tmr" 这类**引用设置**的规格解析成具体 (时, 分)。

        这样主界面渲染按钮文案（_refresh_preset_labels）和真正执行预设
        （apply_preset）用的是**同一个**解析结果，不会出现
        「按钮写 22:00、点下去按 21:00 执行」这种不一致。
        """
        if not spec:
            return spec
        kind = spec[0]
        if kind == "cfg_at":
            h, m = parse_hm(self.cfg.get(spec[1]), *QUICK_DEFAULTS.get(spec[1], (22, 0)))
            return ("at", h, m)
        if kind == "cfg_tmr":
            h, m = parse_hm(self.cfg.get(spec[1]), *QUICK_DEFAULTS.get(spec[1], (8, 0)))
            offset=max(0,min(7,int(self.cfg.get('quick_day_offset',1))))
            return ('tmr',h,m) if offset==1 else ('custom',offset,h,m)
        return spec

    def _refresh_preset_labels(self):
        import quick_presets
        from ui_compact import set_icon
        values=quick_presets.get(self.cfg)
        for index,(key,_) in enumerate(QUICK_PRESETS):
            btn=getattr(self,'preset_btns',{}).get(key)
            if btn:
                value=values[index];btn.config(text=quick_presets.caption(value,self.T))
                name='clock'
                set_icon(self,btn,name,20)

    def apply_preset(self, spec):
        """快捷预设：一键把时间填好并立即开始。

        spec = ("sec", 秒数) / ("at", 时, 分) / ("tmr", 时, 分)，
        也可以是 ("cfg_at"/"cfg_tmr", 配置键)（v1.3.1 可自定义的两个）。
        「今天 xx:xx」如果在设定时刻之前点，就用今天；已经过了就顺延到明天
        同一时刻（timer_engine.resolve_at）。
        """
        spec = self.preset_spec(spec)
        if not spec:
            return
        if spec[0] == "sec":
            total = int(spec[1])
            d, rem = divmod(total, 86400)
            h, rem = divmod(rem, 3600)
            m, s = divmod(rem, 60)
            self.cd_days.set(str(d))
            self.cd_h.set("%02d" % h)
            self.cd_m.set("%02d" % m)
            self.cd_s.set("%02d" % s)
            self._set_mode(M_COUNTDOWN)
            self._save_time_fields()
            self.start_timer()
            return
        if spec[0]=='custom':
            now=datetime.datetime.now();target=(now+datetime.timedelta(days=spec[1])).replace(hour=spec[2],minute=spec[3],second=0,microsecond=0)
            if target<=now:
                messagebox.showinfo(self.T('tip_title'),i18n.feature_text(self.T,'今天的时间已过去，请在设置中选择其他日期或更晚的时间。'),parent=self.root);return
            if spec[1]==7:
                self.apply_preset(('sec',int((target-now).total_seconds())));return
        elif spec[0] == "tmr":
            nxt = datetime.datetime.now() + datetime.timedelta(days=1)
            target = nxt.replace(hour=int(spec[1]), minute=int(spec[2]),
                                 second=0, microsecond=0)
        else:
            target = resolve_at(int(spec[1]), int(spec[2]), 0)
        try:
            self.weekday_box.current(target.weekday())
        except Exception:
            pass
        self._set_mode(M_DATETIME)
        self.dt_h.set("%02d" % target.hour)
        self.dt_m.set("%02d" % target.minute)
        self.dt_s.set("%02d" % target.second)
        self.start_timer()

    def _set_mode(self, mode):
        """切到指定时间模式，并把三处状态（变量/配置/按钮态/板块）一起同步。

        v1.3.1 抽出这个辅助方法：以前 apply_preset 里是
        `self.mode_var.set(...)` + `self.cfg["mode"] = ...` 各写一遍，
        而 UI 上的模式按钮和展开的板块**没有被同步**——结果点「今天 22:00」
        后，按钮还高亮在「倒计时」上，展开的也还是倒计时那块。
        """
        try:
            self.mode_var.set(mode)
            self.cfg["mode"] = mode
        except Exception:
            pass
        try:
            self._refresh_mode_btns()
            self._refresh_time_groups()
        except Exception:
            pass

    # ------------------------------------------------------------ 定时任务队列
    def get_queue(self):
        return list(self.task_queue)

    def describe_action(self, task):
        return action_label(task.get("action") or A_SHUTDOWN, self.T)

    def describe_when(self, task):
        if task.get("mode") == "calendar":
            from ui_tasks import REPEAT_NAMES
            return task.get("at", "").replace("T", " ") + " · " + i18n.feature_text(self.T,REPEAT_NAMES.get(task.get("repeat", "once"), ""))
        if task.get('mode')=='combined':return i18n.feature_text(self.T,'网络安静且无人操作')+f" · {task['user_idle_seconds']/60:g} min"
        if task.get('mode')=='chain':return i18n.feature_text(self.T,'程序成功后执行')+' · '+os.path.basename(task.get('prepare_path',''))
        if task.get("mode") in ("download", "network"):
            name=i18n.feature_text(self.T,'下载文件夹' if task['mode']=='download' else '网络流量')
            seconds=task.get('idle_seconds',60)
            return name+(f' · quiet {seconds:g}s' if self.T.lang=='EN' else f' · 安静{seconds:g}秒')
        """队列 / 日志里显示的人类可读执行时间。"""
        try:
            mode = task.get("mode")
            if mode == M_DATETIME:
                target = next_datetime(int(task.get("weekday", 0)),
                                       int(task.get("hour", 0)),
                                       int(task.get("minute", 0)),
                                       int(task.get("second", 0)))
                return target.strftime("%m-%d %H:%M:%S")
            if mode == M_INTERVAL:
                return self.T("when_interval",
                              t=format_remain(task.get("seconds", 0), self.T))
            return self.T("when_after",
                          t=format_remain(task.get("seconds", 0), self.T))
        except Exception:
            return "-"

    def describe_note(self, task):
        """队列「说明」列：这个任务属于哪种定时方式。"""
        try:
            mode = task.get("mode")
            if mode == M_DATETIME:
                return self.T("note_datetime")
            if mode == M_INTERVAL:
                return self.T("note_interval")
            return self.T("note_countdown")
        except Exception:
            return ""

    def add_current_to_queue(self):
        """队列窗口里的「把当前设定加入队列」按钮。"""
        self.enqueue_current()

    def enqueue_current(self):
        import task_features
        return task_features.enqueue_current(self)

    def remove_queue_tasks(self, ids):
        from undo_store import remove_queue
        return remove_queue(self,set(ids))

    def clear_queue(self):
        self.remove_queue_tasks([t['id'] for t in self.task_queue])
        self._set_status('queue_cleared')

    def _start_next_task(self):
        """从队列头取一个任务开始跑（正跑着 / 队列空则什么也不做）。"""
        if self.engine.is_running():
            return
        if not self.task_queue:
            self._active_task = None

            return
        task = self.task_queue[0]
        self._active_task = task
        mode = task.get("mode")
        if mode == M_DATETIME:
            target = next_datetime(int(task.get("weekday", 0)),
                                   int(task.get("hour", 0)),
                                   int(task.get("minute", 0)),
                                   int(task.get("second", 0)))
            self.engine.start_datetime(target)
        elif mode == M_INTERVAL:
            self.engine.start_interval(float(task.get("seconds", 0)))
        else:
            self.engine.start_countdown(float(task.get("seconds", 0)))
        self._set_running_ui(True)


    def _load_queue(self):
        raw = self.cfg.get("queue") or []
        self.task_queue = []
        self._next_task_id = 1
        if isinstance(raw, list):
            for item in raw:
                if not isinstance(item, dict):
                    continue
                from task_store import snapshot
                try: task = snapshot(item, self.cfg)
                except (ValueError, TypeError): continue
                if task["mode"] not in (M_COUNTDOWN, M_DATETIME, M_INTERVAL): continue
                task["id"] = self._next_task_id
                self._next_task_id += 1
                task.setdefault("mode", M_COUNTDOWN)
                task.setdefault("action", A_SHUTDOWN)
                self.task_queue.append(task)

    def _save_queue(self):
        out = []
        for t in self.task_queue:
            out.append({k: v for k, v in t.items() if k != "id"})
        self.cfg["queue"] = out

    # ------------------------------------------------------------ 定时状态持久化
    def _save_pending_timer(self):
        import task_features
        return task_features.save_pending(self)

    def _maybe_resume_timer(self):
        import task_features
        return task_features.resume_pending(self)


    def apply_settings(self):
        """设置点「保存」时调用：外观原位更新，保留控件与计时。"""
        self.engine.warning_seconds=int(self.cfg.get("warning_seconds",10))
        import ui_transition
        ui_transition.finish(self)
        from ui_skin_transition import SkinFade
        fade=SkinFade(self)
        if hasattr(self,"skin_renderer"):
            self.skin_renderer._hold=True;self.skin_renderer._updating=True
            self.skin_renderer._localizing=self.T.lang!=self.cfg.get("language")
            # Virtual text stays on its cached skin surface during localization;
            # restoring native labels here would expose white blocks and reflow.
        old_palette, old_accent, old_dark = dict(theme.p), theme.accent, theme.is_dark
        before = (theme.mode, theme.accent_key, theme.size_key, self.T.lang, getattr(theme,"skin_key",None))
        theme.load(self.cfg)
        self.T.set_language(self.cfg.get("language"))
        after = (theme.mode, theme.accent_key, theme.size_key, self.T.lang, getattr(theme,"skin_key",None))
        if before[3]!=after[3]:
            from ui_localize import update_app
            update_app(self,before[3])
        if after[:2] != before[:2] or after[4]!=before[4]:ui_transition.animate(self,old_palette,old_accent,old_dark,duration=0)
        else:theme.apply_ttk(self.root)
        self._refresh_preset_labels()
        awake=getattr(self,'display_awake',None)
        if awake:
            try:awake.set_enabled(bool(self.cfg.get('keep_display_on')))
            except OSError as exc:
                self.cfg['keep_display_on']=awake.enabled;self.cfg.save()
                messagebox.showwarning(self.T('tip_title'),str(exc),parent=self.root)
        settings=getattr(self,'_settings_win',None)
        if settings and settings.winfo_exists() and getattr(settings,'_pc_panel',None) is not None:
            settings.pc_panel.awake_var.set(bool(self.cfg.get('keep_display_on')))
        desktop=getattr(self,'desktop',None)
        if desktop:desktop.apply()
        floating=getattr(self,"floating",None)
        if floating:floating.apply()
        if hasattr(self,'_paint_pin'):self._paint_pin()
        if self.tray:
            self.tray.refresh()
        if hasattr(self,"skin_renderer"):
            self.skin_renderer.apply();self.skin_renderer._hold=False;self.skin_renderer._updating=False;self.skin_renderer._localizing=False;self.skin_renderer.schedule()
        fade.start()
        return False

    def reload_texts(self):
        """兼容旧调用：等价于 apply_settings。"""
        return self.apply_settings()

    # ================================================================ 托盘
    def _init_tray(self):
        from tray import TrayIcon
        self.tray = TrayIcon(self)
        if not self.tray.start():
            self.tray = None

    def post(self, func, *args):
        """把托盘线程里的回调丢回 Tk 主线程。"""
        self.emit("ui_call", {"func": func, "args": args})

    # ================================================================ CLI
    def _apply_cli(self):
        cli = self.cli
        if cli.get("help"):
            self.show_window()
            self.root.after(200, self.open_params)
            return
        if not cli.get("given"):
            return
        action = cli.get("action")
        if action:
            self.action_var.set(action)
            self.cfg["action"] = action
        if cli.get("path"):
            if action == A_RUN:
                self.cfg["program_path"] = cli["path"]
            elif action == A_SOUND:
                self.cfg["sound_file"] = cli["path"]
        if cli.get("text"):
            self.cfg["message_text"] = cli["text"]
        self._refresh_details()
        self.mode_var.set(M_COUNTDOWN)
        seconds = cli.get("seconds")
        if seconds is None and cli.get("auto_start"):
            seconds = 30
        if seconds is not None:
            d, rem = divmod(int(seconds), 86400)
            h, rem = divmod(rem, 3600)
            m, s = divmod(rem, 60)
            self.cd_days.set(str(d))
            self.cd_h.set("%02d" % h)
            self.cd_m.set("%02d" % m)
            self.cd_s.set("%02d" % s)
        if cli.get("auto_start") and seconds and seconds > 0:
            self.root.after(300, self.start_timer)

    def current_task_snapshot(self):
        import task_features
        return task_features.current_task(self)

    def enqueue_task(self, task, start=False):
        import task_features
        return task_features.enqueue(self, task, start)

    def edit_queue_task(self, identifier, task):
        import task_features
        return task_features.edit_queue(self, identifier, task)

    def copy_queue_tasks(self, ids):
        import task_features
        return task_features.copy_queue(self, ids)

    def move_queue_tasks(self, ids, direction):
        import task_features
        return task_features.move_queue(self, ids, direction)

    def postpone(self, minutes):
        import task_features
        return task_features.postpone(self, minutes)

    def open_templates(self, parent=None):
        return self.open_task_center('templates',parent)

    def open_advanced(self, parent=None):
        return self.open_task_center('advanced',parent)



def run(cli=None):
    app = App(cli or {})
    try:
        app.root.mainloop()
    except KeyboardInterrupt:
        app.quit_app()
