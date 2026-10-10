# -*- coding: utf-8 -*-
"""
配置与常量 —— 豪崽子の自动关机工具
文件作者：@wenhao
"""
import json
import os
import sys
import copy

from i18n import APP_NAME_CHS, AUTHOR, VERSION  # noqa: F401  (统一出口)

APP_ID = "HaozaiziShutdownTool"
RUN_VALUE_NAME = "豪崽子の自动关机工具"

# 动作编码
A_SHUTDOWN = "shutdown"
A_RESTART = "restart"
A_LOGOFF = "logoff"
A_SLEEP = "sleep"
A_MONITOR = "monitor_off"
A_LOCK = "lock"
A_HIBERNATE = "hibernate"
A_CLOSE = "close_program"
A_RUN = "run_program"
A_SOUND = "play_sound"
A_MESSAGE = "message"

# 关键操作（关机 / 重启 / 注销）
KEY_ACTIONS = (A_SHUTDOWN, A_RESTART, A_LOGOFF)

# 定时器模式
M_COUNTDOWN = "countdown"
M_DATETIME = "datetime"
M_INTERVAL = "interval"

DEFAULT_SETTINGS = {
    'quick_day_offset': 1,
    'hotkeys_enabled': False,
    'hotkey_show': 'Ctrl+Alt+H',
    'hotkey_pause': 'Ctrl+Alt+P',
    'hotkey_resume': 'Ctrl+Alt+R',
    'notifications_enabled': False,
    'notify_setup': True,
    'notify_done': True,
    'notify_error': True,
    'templates': [],
    'automations': [],
    # 通用设置
    "confirm_before_action": False,
    "confirm_key_only": False,
    "confirm_on_exit": True,
    "confirm_on_exit_only_timer": True,
    "force_close_apps": True,
    "sound_at_10s": False,
    # 显示界面设置
    "esc_to_minimize": False,
    "minimize_to_tray": True,
    # 旧版遗留键：进度条已改为整行铺满、不再在右侧显示文字（v1.1.2），
    # 保留仅为兼容旧配置文件，程序已不再读取。
    "progress_display": "remain",   # none | percent | remain
    "language": "CHS",
    # 外观（主题色 / 字号 / 深浅色）
    "theme_mode": "light",          # light | dark | system
    "accent": "blue",               # blue|teal|green|orange|red|pink|purple|indigo
    "font_size": "normal",          # small | normal | large | huge
    # 其他设置
    "popup_at_10s": False,
    "autostart": False,
    # 记忆项
    "action": A_SHUTDOWN,
    "mode": M_COUNTDOWN,
    "cd_days": 0, "cd_hours": 0, "cd_minutes": 0, "cd_seconds": 0,
    "dt_weekday": 1, "dt_hour": 0, "dt_minute": 0, "dt_second": 0,
    "iv_hours": 0, "iv_minutes": 0, "iv_seconds": 0,
    "program_path": "",
    "close_program_path": "",
    "keep_display_on": False,
    "sound_file": "",
    "message_text": "系统即将关机，请及时保存您的工作！",
    "last_folder": "",
    # ---- v1.2.0 新增 ----
    "toast_seconds": 15,            # 消息提示框停留时长（秒），原来固定 15
    "cancel_at_10s": True,          # 到点前 10 秒弹「可取消」提示框
    "log_enabled": True,            # 是否记录执行日志
    "resume_timer": True,           # 重开程序时接着跑上次没跑完的定时
    "queue": [],                    # 定时任务队列（list[dict]）
    "pending_timer": {},            # 上次退出时还没跑完的定时（用于恢复 / 到点提醒）
    # ---- v1.3.1 新增 ----
    # 快捷预设最后两个按钮可自定义（"H:MM" 文本，界面上是「时:分」两个输入框）。
    # 存文本而不是 (时,分) 元组，是因为设置窗口里用户就是在文本框里敲字，
    # 存原文可以保留用户输入的样子（例如 "8:00" 而不是被规范化成 "08:00"）。
    "quick_at_today": "22:00",      # 第 5 个预设：今天几点
    "quick_at_tomorrow": "08:00",   # 第 6 个预设：明天几点
}


def parse_hm(text, default_h, default_m):
    """把 "H:MM" / "HH:MM" 文本解析成 (时, 分)；非法输入回落到默认值。

    这是「快捷预设可自定义」的唯一解析入口 —— 设置窗口存的是原文，
    主界面渲染按钮和真正执行预设时都走这里，保证两处口径一致。
    容错策略：超出范围（负数、>23 时、>59 分）一律回落，
    而不是截断 —— 截断会让用户以为"我填的 25:00 生效了"。
    """
    try:
        s = str(text).strip()
        if not s:
            raise ValueError("empty")
        # 允许中文冒号「：」——中文输入法下很容易打出来
        s = s.replace("：", ":")
        if ":" in s:
            hh, mm = s.split(":", 1)
        else:
            hh, mm = s, "0"
        h, m = int(hh.strip()), int(mm.strip())
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError("out of range")
        return h, m
    except Exception:
        return int(default_h), int(default_m)


def data_dir():
    """数据目录：%APPDATA%\\HaozaiziShutdownTool"""
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    d = os.path.join(base, APP_ID)
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return d


def config_file():
    return os.path.join(data_dir(), "settings.json")


class Config(object):
    """极简配置对象，读写 JSON。"""

    def __init__(self):
        self.data = copy.deepcopy(DEFAULT_SETTINGS)
        self.recovery_notice = ''
        self.backup_error = ''
        self.load()

    def load(self):
        path = config_file()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                from config_backups import validate_settings
                validate_settings(loaded)
                self.data.update(loaded)
            except Exception:
                from config_backups import recover_corrupt
                recovered, notice = recover_corrupt(path)
                if recovered is not None:self.data.update(recovered)
                self.recovery_notice = notice
        self.data['theme_mode']='light'
        self.data['font_size']='normal'

    def save(self):
        self.data['theme_mode']='light'
        self.data['font_size']='normal'
        try:
            from config_backups import before_save,validate_settings
            validate_settings(self.data)
            try:before_save(config_file(), self.data);self.backup_error=''
            except Exception as exc:self.backup_error=str(exc)
            tmp = config_file() + ".tmp"

            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, config_file())
            return True
        except Exception:
            return False

    def __getitem__(self, k):
        return self.data.get(k, DEFAULT_SETTINGS.get(k))

    def __setitem__(self, k, v):
        if k=='theme_mode':v='light'
        if k=='font_size':v='normal'
        self.data[k] = v

    def get(self, k, default=None):
        return self.data.get(k, DEFAULT_SETTINGS.get(k, default))

    def update(self, mapping):
        self.data.update(mapping)
        self.data['theme_mode']='light'
        self.data['font_size']='normal'


def app_dir():
    """程序所在目录（打包后为 exe 所在目录）。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def exe_path():
    """当前可执行文件路径（打包后为 exe，未打包时为 pythonw.exe + 脚本）。"""
    if getattr(sys, "frozen", False):
        return os.path.abspath(sys.executable)
    exe = sys.executable
    pyw = os.path.join(os.path.dirname(exe), "pythonw.exe")
    if os.path.exists(pyw):
        exe = pyw
    script = os.path.join(app_dir(), "src", "main.py")
    return '"%s" "%s"' % (exe, script)
