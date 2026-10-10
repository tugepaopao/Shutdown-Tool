# -*- coding: utf-8 -*-
"""
开机自启（写 HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run）
文件作者：@wenhao
"""
import winreg

from app_config import RUN_VALUE_NAME, exe_path

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _command():
    p = exe_path()
    if p.startswith('"'):
        return p + " /min"
    return '"%s" /min' % p


def is_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as k:
            winreg.QueryValueEx(k, RUN_VALUE_NAME)
            return True
    except OSError:
        return False


def enable():
    try:
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, RUN_VALUE_NAME, 0, winreg.REG_SZ, _command())
        return True
    except OSError:
        return False


def disable():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, RUN_VALUE_NAME)
        return True
    except OSError:
        return True


def set_enabled(flag):
    return enable() if flag else disable()
