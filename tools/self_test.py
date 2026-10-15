# -*- coding: utf-8 -*-
"""
自测脚本（不执行任何关机/重启等破坏性动作）
文件作者：@wenhao

运行： .venv\\Scripts\\python.exe tools\\self_test.py
"""
import datetime
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print("%-46s %s %s" % (name, "PASS" if ok else "FAIL", detail))


def main():
    # ---------------------------------------------------------- i18n
    import i18n
    base = set(i18n._TEXTS["CHS"].keys())
    for lang in ("CHT", "EN"):
        missing = base - set(i18n._TEXTS[lang].keys())
        extra = set(i18n._TEXTS[lang].keys()) - base
        check("i18n 键完整 · %s" % lang, not missing and not extra,
              "missing=%s extra=%s" % (sorted(missing), sorted(extra)))
    T = i18n.Texts("CHS")
    check("format_remain 秒", i18n.format_remain(65, T) == "00:01:05",
          i18n.format_remain(65, T))
    check("format_remain 天", i18n.format_remain(90061, T) == "1 天 01:01:01",
          i18n.format_remain(90061, T))

    # ---------------------------------------------------------- 命令行参数
    from actions import parse_argv
    cli = parse_argv(["/s", "/t=60", "/min"])
    check("参数 /s /t=60 /min", cli["action"] == "shutdown" and cli["seconds"] == 60
          and cli["minimized"] and cli["auto_start"], str(cli))
    cli = parse_argv(["/r", "/w"])
    check("参数 /r /w", cli["action"] == "restart" and cli["auto_start"] is False, str(cli))
    cli = parse_argv(['/m=测试消息', "/t=5"])
    check("参数 /m=text", cli["action"] == "message" and cli["text"] == "测试消息", str(cli))
    cli = parse_argv([r"/rp=C:\Windows\notepad.exe"])
    check("参数 /rp=path", cli["action"] == "run_program"
          and cli["path"].endswith("notepad.exe"), str(cli))
    cli = parse_argv(["/?"])
    check("参数 /?", cli["help"] is True, str(cli))

    # ---------------------------------------------------------- 配置读写
    tmp = tempfile.mkdtemp(prefix="haozai_cfg_")
    os.environ["APPDATA"] = tmp
    import importlib
    import app_config
    importlib.reload(app_config)
    cfg = app_config.Config()
    cfg["cd_seconds"] = 42
    cfg["language"] = "CHT"
    ok = cfg.save()
    cfg2 = app_config.Config()
    check("配置保存/读取", ok and cfg2["cd_seconds"] == 42 and cfg2["language"] == "CHT",
          "file=%s" % os.path.basename(app_config.config_file()))

    # ---------------------------------------------------------- 日期模式
    from timer_engine import next_datetime
    now = datetime.datetime.now()
    target = next_datetime(now.weekday(), 0, 0, 0)
    delta = (target - now).total_seconds()
    check("日期模式：本周已过则顺延7天", 0 < delta <= 7 * 86400 + 60,
          "%.0f 秒后 (%s)" % (delta, target.strftime("%m-%d %a %H:%M:%S")))
    target2 = next_datetime((now.weekday() + 1) % 7, 12, 0, 0)
    check("日期模式：明天12点", target2.weekday() == (now.weekday() + 1) % 7
          and target2.hour == 12, target2.strftime("%m-%d %H:%M:%S"))

    # ---------------------------------------------------------- 定时器引擎
    events = []
    from timer_engine import TimerEngine
    eng = TimerEngine(lambda e, p: events.append((e, p)))
    eng.start_countdown(1.0)
    t0 = time.time()
    while eng.is_running() and time.time() - t0 < 6:
        time.sleep(0.05)
    kinds = [e for e, _ in events]
    check("倒计时 1 秒后触发 finished", "finished" in kinds, "events=%s" % kinds[:3])
    check("倒计时 10 秒预警事件存在", "warn" in kinds, "")

    events.clear()
    eng.start_countdown(3.0)
    time.sleep(0.6)
    eng.pause()
    p_remain = [p["remain"] for e, p in events if e == "paused"]
    time.sleep(1.0)
    eng.resume()
    t0 = time.time()
    while eng.is_running() and time.time() - t0 < 10:
        time.sleep(0.05)
    check("暂停/继续后仍能触发", "finished" in [e for e, _ in events],
          "暂停时剩余 %.2f 秒" % (p_remain[0] if p_remain else -1))

    events.clear()
    eng.start_interval(1.0)
    t0 = time.time()
    while time.time() - t0 < 3.6:
        time.sleep(0.05)
    repeats = [p for e, p in events if e == "finished"]
    eng.stop()
    check("时间段模式循环执行", len(repeats) >= 3 and all(r["repeat"] for r in repeats),
          "3.6 秒内触发 %d 次" % len(repeats))

    # ---------------------------------------------------------- 动作（安全项）
    import actions
    ok_msg, _ = actions.perform("message", cfg)
    check("动作：消息提示框（由界面层实现）", ok_msg, "")
    p = os.path.join(tmp, "t.wav")
    from i18n import Texts
    check("动作：播放不存在的文件被拦截", actions.do_play_sound(p)[0] is False, "")
    ok_run, err = actions.do_run_program(r"C:\Windows\System32\cmd.exe /c exit")
    check("动作：运行程序（cmd /c exit）", ok_run, err)
    check("动作：关机命令拼装（不执行）",
          actions.CREATE_NO_WINDOW == 0x08000000, "shutdown /s /t 0 /f 由 subprocess 静默调用")

    # --- v1.1.6 修复 ①：关机类动作不再「无条件报成功」---
    sr = actions._shutdown_result
    check("动作：返回码 0 → 成功", sr(0) == (True, ""), "")
    check("动作：拿不到返回码（超时）不误报失败", sr(None) == (True, ""), "")
    check("动作：已在关机/重启流程（1116/1190）→ 视为成功",
          bool(sr(1116)[0]) and bool(sr(1190)[0]),
          "1116=%r 1190=%r" % (sr(1116), sr(1190)))
    _ok5, _e5 = sr(5)
    check("动作：拒绝访问（5）→ 报失败且给人话", (not _ok5) and ("权限" in _e5), _e5)
    _okx, _ex = sr(1)
    check("动作：其他错误码 → 报失败并带码", (not _okx) and ("1" in _ex), _ex)

    # --- v1.1.6 修复 ②：/rp= 不再经过 shell（含 & | 的合法路径会被拆坏）---
    _parts = actions._split_cmd(r"C:\a&b\tool.exe /x")
    check("动作：含 & 的路径不被拆坏",
          bool(_parts) and _parts[0] == r"C:\a&b\tool.exe" and _parts[1] == "/x",
          "parts=%s" % (_parts,))
    check("动作：空路径被拦截", actions.do_run_program("")[0] is False, "")

    # 机制验证：wait=True 必须真能拿到退出码（拿不到的话上面那套翻译就是空的）
    # 用 `cmd /c exit 3` —— 纯空操作，不碰 shutdown.exe
    _rc = actions._run_hidden(["cmd", "/c", "exit", "3"], wait=True)
    check("动作：_run_hidden(wait=True) 能拿到退出码", _rc == 3, "rc=%s" % _rc)

    # ---------------------------------------------------------- v1.2.0 新增能力
    # ① 计时器查询接口（状态栏「预计几点执行」+ 定时状态持久化都靠它）
    from timer_engine import resolve_at
    _now = datetime.datetime(2026, 9, 23, 19, 30, 0)
    _t1 = resolve_at(18, 0, 0, now=_now)
    check("预设：今天 18:00 已过 → 顺延到明天",
          _t1.date() == _now.date() + datetime.timedelta(days=1) and _t1.hour == 18,
          _t1.strftime("%Y-%m-%d %H:%M:%S"))
    _t2 = resolve_at(23, 0, 0, now=_now)
    check("预设：今天 23:00 未到 → 就是今天",
          _t2.date() == _now.date() and _t2.hour == 23,
          _t2.strftime("%Y-%m-%d %H:%M:%S"))

    eng2 = TimerEngine(lambda e, p: None)
    check("引擎：未运行时 due_at() 为 None", eng2.due_at() is None, "")
    eng2.start_countdown(5.0)
    _due = eng2.due_at()
    _delta = (_due - datetime.datetime.now()).total_seconds() if _due else -1
    check("引擎：due_at() ≈ 现在 + 5 秒", 3.5 <= _delta <= 6.0, "%.2f 秒后" % _delta)
    check("引擎：remaining() 与 total 对得上",
          4.0 <= eng2.remaining() <= 5.0 and abs(eng2.total_seconds() - 5.0) < 1e-6,
          "remaining=%.2f total=%.2f" % (eng2.remaining(), eng2.total_seconds()))
    eng2.stop()
    check("引擎：停止后 remaining() 归零", eng2.remaining() == 0.0, "")

    # ② 执行日志（走临时 APPDATA，不碰用户真实日志）
    import run_log
    run_log.clear()
    run_log.add(run_log.KIND_SETUP, "设定定时：测试", ok=True, detail="单元测试")
    run_log.add(run_log.KIND_ERROR, "执行失败：测试", ok=False, detail="错误码 5")
    rows = run_log.entries(limit=10)
    check("日志：写入 / 读回 2 条",
          len(rows) == 2 and rows[0]["kind"] == "setup" and rows[1]["ok"] is False,
          "条数=%d" % len(rows))
    check("日志：文件落在数据目录里",
          os.path.dirname(run_log.log_file()) == app_config.data_dir()
          and run_log.log_file().startswith(os.path.abspath(tmp)),
          run_log.log_file())
    run_log.clear()
    check("日志：清空后为空", run_log.entries() == [], "")

    # ③ 新配置项默认值
    cfg3 = app_config.Config()
    check("配置：v1.2.0 新增键都有默认值",
          cfg3.get("toast_seconds") == 15 and cfg3.get("cancel_at_10s") is True
          and cfg3.get("log_enabled") is True and cfg3.get("resume_timer") is True
          and cfg3.get("queue") == [] and cfg3.get("pending_timer") == {},
          "toast=%s queue=%s" % (cfg3.get("toast_seconds"), cfg3.get("queue")))

    # ④ 快捷预设定义自检（文案键必须在语言表里存在）
    import ui_main
    check("预设：6 个快捷键且文案键齐全",
          len(ui_main.QUICK_PRESETS) == 6
          and all(k in i18n._TEXTS["CHS"] for k, _ in ui_main.QUICK_PRESETS),
          "、".join(k for k, _ in ui_main.QUICK_PRESETS))

    # ⑤ v1.2.1：最小化不再弹托盘提醒，只有「点×关闭」才提醒一次
    #    判据落在 hide_to_tray 的签名与默认值上（纯静态检查，不建窗口）。
    #    为什么要加：业主明确反馈「每次最小化都弹提醒，没必要」——
    #    用户主动最小化时他知道窗口去哪了；点×才容易误以为程序被关掉。
    import inspect
    sig = inspect.signature(ui_main.App.hide_to_tray)
    hint = sig.parameters.get("hint")
    check("v1.2.1：最小化静默（hide_to_tray 默认不提醒）",
          hint is not None and hint.default is False,
          "hint 默认=%r（最小化/ESC 不提醒）" % (hint.default if hint else None))
    src_close = inspect.getsource(ui_main.App.on_close)
    check("v1.2.1：点×关闭仍提醒一次",
          "hint=True" in src_close,
          "on_close 调 hide_to_tray(hint=True)" if "hint=True" in src_close
          else "on_close 未传 hint=True —— 关闭提示丢了")

    # ⑥ v1.3.1：快捷预设最后两个可自定义（配置键 + 规格 + 解析容错）
    #    为什么要加：这两个预设的时间从"写死在代码里"变成了"读配置"，
    # v1.5.0 用户定案：第5项固定22:00，只有第6项引用设置。
    cfg6 = app_config.Config()
    check("v1.3.1：自定义预设的配置键有默认值",
          cfg6.get("quick_at_today") == "22:00"
          and cfg6.get("quick_at_tomorrow") == "08:00",
          "today=%s tomorrow=%s" % (cfg6.get("quick_at_today"),
                                    cfg6.get("quick_at_tomorrow")))
    # 第5项固定、第6项可自定义。
    specs = [s for _, s in ui_main.QUICK_PRESETS]
    check("v1.5.0：22:00固定，仅最后一项自定义",
          specs[4] == ("at", 22, 0) and specs[5][0] == "cfg_tmr",
          "spec[4]=%r spec[5]=%r" % (specs[4], specs[5]))
    # 动态文案模板必须在语言表里
    check("v1.3.1：动态文案键齐全（quick_at_fmt / quick_tmr_fmt）",
          all(k in i18n._TEXTS["CHS"] for k in ("quick_at_fmt", "quick_tmr_fmt")),
          "两键均在语言表")

    # ⑦ v1.3.1：parse_hm 解析容错（设置里手敲的时间全靠它兜底）
    hm_cases = [
        ("22:00", (22, 0)), ("8:30", (8, 30)), ("7", (7, 0)),
        ("08：00", (8, 0)),            # 中文全角冒号（中文输入法极易打出）
        ("", (9, 9)), ("aa", (9, 9)), ("25:00", (9, 9)), ("12:99", (9, 9)),
    ]
    bad = []
    for text, want in hm_cases:
        got = app_config.parse_hm(text, 9, 9)
        if got != want:
            bad.append("%r→%s 期望 %s" % (text, got, want))
    check("v1.3.1：parse_hm 容错（含全角冒号 / 超范围回落）",
          not bad, "；".join(bad) if bad else "%d 组用例全对" % len(hm_cases))

    # ⑧ v1.3.1：三个模式都有常显入口（修「找不到日期选项」）
    #    判据：模式入口的构建函数独立存在，且不再是「板块内部的单选钮」。
    #    这是本轮的核心可用性修复 —— 原来入口随板块一起折叠，
    #    非当前模式**完全没有入口**，用户根本切不过去。
    check("v1.3.1：模式入口独立于时间板块（三个都常显）",
          hasattr(ui_main.App, "_build_mode_selector")
          and hasattr(ui_main.App, "_pick_mode")
          and hasattr(ui_main.App, "_refresh_mode_btns"),
          "_build_mode_selector / _pick_mode / _refresh_mode_btns 三件套齐全")
    src_tg = inspect.getsource(ui_main.App._time_group)
    # 只看代码，不看注释/文档串 —— 函数说明里为了讲清缘由提到了
    # Radiobutton，直接 `in src_tg` 会被自己的注释误伤（踩过一次）。
    src_tg_code = "\n".join(
        ln for ln in src_tg.splitlines()
        if not ln.strip().startswith("#"))
    src_tg_code = src_tg_code.split('"""', 2)[-1] if '"""' in src_tg_code else src_tg_code
    check("v1.3.1：时间板块内部不再放模式单选钮",
          "Radiobutton" not in src_tg_code,
          "板块只剩标题 Label + 内容区（切换交给上方常显按钮）")

    # ⑨ v1.3.1：快捷预设改时间后按钮文案要跟着走（往返同步）
    #    判据：apply_settings 里调了 _refresh_preset_labels —— 否则用户改完
    #    设置点「应用」，按钮还显示旧时间，会以为没生效。
    src_apply = inspect.getsource(ui_main.App.apply_settings)
    check("v1.3.1：点应用后刷新预设按钮文案",
          "_refresh_preset_labels" in src_apply,
          "apply_settings 调了 _refresh_preset_labels")

    # v1.3.2：业主确认彻底删除底部队列提示，仅保留左侧入口。
    src_foot = inspect.getsource(ui_main.App._build_footer)
    check("v1.3.2：底部不再创建队列提示条",
          "queue_bar" not in src_foot and "queue_label" not in src_foot,
          "有无队列都只显示进度与状态")
    check("v1.3.3：齿轮任务队列入口仍打开管理窗口",
          'self.open_queue' in inspect.getsource(ui_main.App._build_avatar_menu),
          "齿轮菜单保留队列管理")
    src_status = inspect.getsource(ui_main.App._set_status)
    check("v1.3.2：状态直接显示，不因队列隐藏",
          "self.status.config(text=self.T(key, **kw))" in src_status
          and "_status_saved" not in src_status,
          "最新状态始终写入状态栏")

    # ---------------------------------------------------------- 开机自启
    import autostart
    autostart.set_enabled(False)
    before = autostart.is_enabled()
    autostart.enable()
    after = autostart.is_enabled()
    autostart.disable()
    final = autostart.is_enabled()
    check("开机自启 注册表写/读/删", (not before) and after and (not final),
          "写入命令已就绪")

    # ---------------------------------------------------------- 结果
    print("\n" + "=" * 62)
    total = len(RESULTS)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    print("总计 %d 项，通过 %d 项，失败 %d 项" % (total, passed, total - passed))
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
