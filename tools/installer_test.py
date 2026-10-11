# -*- coding: utf-8 -*-
"""
安装包实测：自动取 output/ 下最新的两个版本，旧版静默安装 → 新版覆盖安装 →
校验「应用和功能」里只有唯一一条卸载项 → 卸载干净。
文件作者：@wenhao

运行： .venv\\Scripts\\python.exe tools\\installer_test.py
"""
import os
import re
import subprocess
import sys
import time
import winreg

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

APP_ID = "{8F3C1A72-5B4E-4C9D-9E21-7A6B0C5D3F10}"
UNINST_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\%s_is1" % APP_ID
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
EXE_NAME = "豪崽子の自动关机工具.exe"

def _scan_setups():
    """扫描 output/ 下的安装包，按版本号升序返回 [(版本, 路径)]。"""
    d = os.path.join(ROOT, "output")
    found = []
    if os.path.isdir(d):
        for n in os.listdir(d):
            m = re.match(r"豪崽子の自动关机工具_v(\d+\.\d+\.\d+)_安装包\.exe$", n)
            if m:
                found.append((m.group(1), os.path.join(d, n)))
    found.sort(key=lambda t: [int(x) for x in t[0].split(".")])
    return found


_SETUPS = _scan_setups()
if len(_SETUPS) >= 2:
    OLD_VER, OLD_SETUP = _SETUPS[-2]
    NEW_VER, NEW_SETUP = _SETUPS[-1]
elif _SETUPS:
    OLD_VER, OLD_SETUP = _SETUPS[-1]
    NEW_VER, NEW_SETUP = _SETUPS[-1]
else:
    OLD_VER = NEW_VER = "1.0.0"
    OLD_SETUP = NEW_SETUP = os.path.join(
        ROOT, "output", "豪崽子の自动关机工具_v1.0.0_安装包.exe")

APPDATA = os.environ.get("APPDATA")
INSTALL_DIR = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs",
                           "HaozaiziShutdownTool")

RESULT = []


def log(name, ok, detail=""):
    RESULT.append((name, bool(ok), detail))
    print("%-46s %s %s" % (name, "PASS" if ok else "FAIL", detail))


def reg_get(path, name):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as k:
            v, _ = winreg.QueryValueEx(k, name)
            return v
    except Exception:
        return None


def reg_exists(path):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path):
            return True
    except Exception:
        return False


def reg_delete(path, name):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, name)
            return True
    except Exception:
        return False


def count_uninstall_entries():
    """统计卸载列表里属于本程序的条目数（应当恒为 1）。"""
    n = 0
    base = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, base) as k:
            i = 0
            while True:
                try:
                    sub = winreg.EnumKey(k, i)
                except OSError:
                    break
                i += 1
                if "Haozaizi" in sub or APP_ID in sub:
                    n += 1
    except Exception:
        pass
    return n


def run_setup(path, timeout=180, extra=None):
    cmd = [path, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-",
           "/NOICONS"] + list(extra or [])
    p = subprocess.run(cmd, capture_output=True)
    time.sleep(1.5)
    return p.returncode


def uninstall(timeout=180):
    un = os.path.join(INSTALL_DIR, "unins000.exe")
    if not os.path.exists(un):
        return -1
    p = subprocess.run([un, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"],
                       capture_output=True)
    time.sleep(2.0)
    return p.returncode


def exe_version_string(path):
    """读 exe 版本资源里的 FileVersion（版本资源以 UTF-16LE 存储）。"""
    try:
        data = open(path, "rb").read()
    except Exception:
        return ""
    txt = data.decode("utf-16-le", "ignore")
    for key in ("FileVersion", "ProductVersion"):
        i = txt.find(key)
        if i >= 0:
            m = re.search(r"\d+\.\d+\.\d+\.\d+", txt[i:i + 300])
            if m:
                return m.group(0)
    return "?"


def file_mtime(path):
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(path)))
    except Exception:
        return "-"


def main():
    for p in (OLD_SETUP, NEW_SETUP):
        if not os.path.exists(p):
            print("找不到安装包：%s" % p)
            return 1
    print("旧版安装包：%s" % os.path.basename(OLD_SETUP))
    print("新版安装包：%s" % os.path.basename(NEW_SETUP))
    print("安装目录　：%s" % INSTALL_DIR)
    print("-" * 70)

    # 先清干净（万一上次残留）
    subprocess.run(["taskkill", "/f", "/im", EXE_NAME], capture_output=True)
    if os.path.exists(os.path.join(INSTALL_DIR, "unins000.exe")):
        uninstall()
        time.sleep(1.0)
    reg_delete(RUN_KEY, "豪崽子の自动关机工具")

    exe_old = os.path.join(INSTALL_DIR, EXE_NAME)

    # ---------------------------------------------------- 1) 装旧版
    rc = run_setup(OLD_SETUP)
    log("① v%s 静默安装成功" % OLD_VER, rc == 0 and os.path.exists(exe_old),
        "rc=%s exe=%s" % (rc, os.path.exists(exe_old)))
    log("  卸载列表出现 1 条记录", count_uninstall_entries() == 1,
        "count=%d" % count_uninstall_entries())
    ver_old = exe_version_string(exe_old)
    log("  已安装 exe 版本 = %s.0" % OLD_VER, ver_old == OLD_VER + ".0",
        "ver=%s" % ver_old)
    disp_old = reg_get(UNINST_KEY, "DisplayVersion")
    log("  注册表 DisplayVersion = %s" % OLD_VER, disp_old == OLD_VER,
        "value=%s" % disp_old)

    # ---------------------------------------------------- 2) 覆盖安装新版
    rc = run_setup(NEW_SETUP)
    log("② v%s 覆盖安装成功（无需先卸载）" % NEW_VER,
        rc == 0 and os.path.exists(exe_old), "rc=%s" % rc)
    log("  卸载列表仍然只有 1 条记录（没装成两份）",
        count_uninstall_entries() == 1, "count=%d" % count_uninstall_entries())
    ver_new = exe_version_string(exe_old)
    log("  程序已替换为 %s.0" % NEW_VER, ver_new == NEW_VER + ".0",
        "ver=%s" % ver_new)
    disp_new = reg_get(UNINST_KEY, "DisplayVersion")
    log("  注册表 DisplayVersion 已变 %s" % NEW_VER, disp_new == NEW_VER,
        "value=%s" % disp_new)
    print("  安装时间：%s" % file_mtime(exe_old))

    # 桌面快捷方式 / 开机自启（向导默认勾选，静默安装按默认执行）
    run_val = reg_get(RUN_KEY, "豪崽子の自动关机工具")
    log("  向导默认勾选「开机自启」→ Run 项已写入",
        bool(run_val) and EXE_NAME in str(run_val), "Run=%s" % (run_val,))

    # ---------------------------------------------------- 3) 配置保留
    cfg = os.path.join(APPDATA, "HaozaiziShutdownTool", "settings.json")
    log("  用户配置目录仍存在（覆盖安装不动它）", os.path.isdir(
        os.path.join(APPDATA, "HaozaiziShutdownTool")), cfg)

    # ---------------------------------------------------- 4) 卸载
    rc = uninstall()
    gone = not os.path.exists(INSTALL_DIR)
    log("③ 静默卸载成功、目录已删除", gone, "rc=%s dir_gone=%s" % (rc, gone))
    log("  卸载列表记录已清除", count_uninstall_entries() == 0,
        "count=%d" % count_uninstall_entries())
    log("  开机自启 Run 项已被卸载程序清除",
        reg_get(RUN_KEY, "豪崽子の自动关机工具") is None, "")
    log("  配置目录未被卸载程序删除", os.path.isdir(
        os.path.join(APPDATA, "HaozaiziShutdownTool")), cfg)

    # ---------------------------------------------------- 5) 静默安装不选任务时不写 Run
    rc = run_setup(NEW_SETUP, extra=["/TASKS="])
    log("④ /TASKS=\"\" 静默安装时不写开机自启",
        reg_get(RUN_KEY, "豪崽子の自动关机工具") is None, "rc=%s" % rc)
    uninstall()
    log("  目录已清除", not os.path.exists(INSTALL_DIR), "")

    print("\n" + "=" * 70)
    total = len(RESULT)
    passed = sum(1 for _, ok, _ in RESULT if ok)
    print("安装包实测 %d 项，通过 %d 项，失败 %d 项" % (total, passed, total - passed))
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
