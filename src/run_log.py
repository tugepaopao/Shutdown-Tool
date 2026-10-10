# -*- coding: utf-8 -*-
"""
执行日志：记录「什么时候设定了什么、有没有执行成功」。
文件作者：@wenhao

落地位置：%APPDATA%\\HaozaiziShutdownTool\\run_log.jsonl（每行一条 JSON）
为什么用 JSONL：追加写，某一行写坏了也不会连累整份日志读不出来；
条数超过上限时自动裁掉最旧的记录（默认保留 500 条）。

设计原则：**日志永远是副作用，不是主流程** —— 任何写失败都被吞掉，
绝不会因为日志问题影响关机/提示等真正的功能。
"""
import datetime
import json
import os
import threading

from app_config import data_dir

MAX_ENTRIES = 500

# 事件类型（界面按类型给不同标题）
KIND_SETUP = "setup"      # 设定定时
KIND_DONE = "done"        # 执行成功
KIND_ERROR = "error"      # 执行失败
KIND_CANCEL = "cancel"    # 取消 / 停止
KIND_INFO = "info"        # 其它信息（入队、恢复、错过…）

_lock = threading.Lock()


def log_file():
    return os.path.join(data_dir(), "run_log.jsonl")


def add(kind, text, ok=None, detail=""):
    """追加一条日志，返回记录 dict（写失败也一样返回，不影响调用方）。"""
    rec = {
        "ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "kind": kind,
        "text": text,
        "ok": ok,
        "detail": detail or "",
    }
    try:
        with _lock:
            with open(log_file(), "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            _trim()
    except Exception:
        pass
    return rec


def _trim():
    """超出上限（留一点余量避免每次追加都重写）时只保留最后 MAX_ENTRIES 条。"""
    try:
        path = log_file()
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) > MAX_ENTRIES + 50:
            with open(path, "w", encoding="utf-8") as f:
                f.writelines(lines[-MAX_ENTRIES:])
    except Exception:
        pass


def entries(limit=300):
    """按时间从旧到新返回最近 limit 条记录（读不到就返回空列表）。"""
    out = []
    try:
        with open(log_file(), "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if isinstance(rec, dict):
                    out.append(rec)
    except Exception:
        return []
    if limit and len(out) > limit:
        out = out[-limit:]
    return out


def clear():
    """清空日志（保留文件，避免句柄问题）。"""
    try:
        with _lock:
            with open(log_file(), "w", encoding="utf-8") as f:
                f.write("")
        return True
    except Exception:
        return False
