# -*- coding: utf-8 -*-
"""
系统托盘图标与菜单（pystray）
文件作者：@wenhao
"""
import os
import threading

from i18n import resource_path

try:
    import pystray
    from pystray import Menu, MenuItem
except Exception:               # pragma: no cover
    pystray = None


def load_icon_image():
    """托盘图标：优先「电源开关球」icon_app.png，依次回退 icon_app.ico /
    icon.png / icon.ico，都读不到就程序化画一个蓝色电源圆环。"""
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return None

    for name in ("assets/icon_app.png", "assets/icon_app.ico",
                 "assets/icon.png", "assets/icon.ico"):
        p = resource_path(name)
        if os.path.exists(p):
            try:
                return Image.open(p).convert("RGBA")
            except Exception:
                pass

    # 兜底：画一个蓝色电源按钮
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((2, 2, 62, 62), fill=(0, 102, 204, 255))
    d.ellipse((10, 10, 54, 54), fill=(255, 255, 255, 255))
    d.rectangle((28, 12, 36, 34), fill=(0, 102, 204, 255))
    d.ellipse((12, 14, 52, 54), outline=(0, 102, 204, 255), width=5)
    return img


class TrayIcon(object):
    """托盘图标，所有回调都通过 app.post() 抛回 Tk 主线程执行。"""

    def __init__(self, app):
        self.app = app
        self._icon = None
        self._thread = None

    def available(self):
        return pystray is not None

    def _build_menu(self):
        T = self.app.T
        app = self.app
        return Menu(
            MenuItem(lambda item: T("tray_show"), lambda: app.post(app.show_window), default=True),
            Menu.SEPARATOR,
            MenuItem(lambda item: T("tray_start"), lambda: app.post(app.tray_start_timer)),
            MenuItem(lambda item: T("btn_resume") if app.engine.paused else T("tray_pause"),
                     lambda: app.post(app.toggle_pause), enabled=self._timer_enabled),
            MenuItem(lambda item:__import__('i18n').feature_text(T,'延后5分钟'),lambda:app.post(app.postpone,5),enabled=self._timer_enabled),
            MenuItem(lambda item:__import__('i18n').feature_text(T,'延后10分钟'),lambda:app.post(app.postpone,10),enabled=self._timer_enabled),
            MenuItem(lambda item:__import__('i18n').feature_text(T,'延后30分钟'),lambda:app.post(app.postpone,30),enabled=self._timer_enabled),
            MenuItem(lambda item: T("tray_now"), lambda: app.post(app.perform_now)),
            MenuItem(lambda item: T("tray_queue"), lambda: app.post(app.open_queue)),
            MenuItem(lambda item: T("tray_clear"), lambda: app.post(app.clear_timer)),
            Menu.SEPARATOR,
            MenuItem(lambda item: T("tray_settings"), lambda: app.post(app.open_settings)),
            MenuItem(lambda item: T("tray_floating"), lambda: app.post(app.toggle_floating),
                     checked=lambda item:bool(app.cfg.get("float_enabled"))),
            MenuItem(lambda item: T("tray_exit"), lambda: app.post(app.quit_app)),
        )

    def _timer_enabled(self, item=None):
        try:
            return self.app.engine.is_running()
        except Exception:
            return False

    def start(self):
        if pystray is None:
            return False
        image = load_icon_image()
        if image is None:
            return False
        self._icon = pystray.Icon("haozai_shutdown", image,
                                  self.app.T("tray_tip", n=self.app.T("app_name")),
                                  menu=self._build_menu())
        self._thread = threading.Thread(target=self._icon.run, daemon=True, name="HaozaiziTray")
        self._thread.start()
        return True

    def stop(self):
        try:
            if self._icon is not None:
                self._icon.stop()
        except Exception:
            pass
        self._icon = None

    def notify(self, title, text):
        try:
            if self._icon is not None:
                self._icon.notify(text, title)
                return True
        except Exception:
            return False
        return False

    def refresh(self):
        self.refresh_status()
        try:
            if self._icon is not None:
                self._icon.update_menu()
        except Exception:
            pass

    def refresh_status(self):
        if self._icon is None:return
        from i18n import format_remain
        try:
            if self.app.engine.is_running():
                text=__import__('i18n').feature_text(self.app.T,'已暂停' if self.app.engine.paused else '剩余')+' '+format_remain(self.app.engine.remaining(),self.app.T)
            else:text=__import__('i18n').feature_text(self.app.T,'就绪')
            self._icon.title=(self.app.T('app_name')+' · '+text)[:127]
        except Exception:pass
