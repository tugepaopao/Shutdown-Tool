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
import time
import traceback
import uuid

from app_config import data_dir

MAX_ENTRIES = 500

# 事件类型（界面按类型给不同标题）
KIND_SETUP = "setup"      # 设定定时
KIND_DONE = "done"        # 执行成功
KIND_ERROR = "error"      # 执行失败
KIND_CANCEL = "cancel"    # 取消 / 停止
KIND_INFO = "info"        # 其它信息（入队、恢复、错过…）

_lock = threading.Lock()
_maintenance = {}
_error_lock = threading.RLock()
_errors = {}


def _fold(rows):
    result=[]; groups={}
    for row in rows:
        key=row.get('error_id')
        if key and key in groups:result[groups[key]]=row
        else:
            if key:groups[key]=len(result)
            result.append(row)
    return result


def log_file():
    return os.path.join(data_dir(), "run_log.jsonl")


def add(kind, text, ok=None, detail="", **metadata):
    """追加一条日志，返回记录 dict（写失败也一样返回，不影响调用方）。"""
    rec = {
        "ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "kind": kind,
        "text": text,
        "ok": ok,
        "detail": detail or "",
    }
    rec.update(metadata)
    try:
        with _lock:
            path=log_file()
            try:st=os.stat(path);stamp=(st.st_size,st.st_mtime_ns)
            except OSError:stamp=None
            previous,count=_maintenance.get(path,(None,49))
            if previous!=stamp:count=49
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            count+=1
            if count>=50:_trim();count=0
            st=os.stat(path);_maintenance[path]=((st.st_size,st.st_mtime_ns),count)
    except Exception:
        pass
    return rec


def _trim():
    """超出上限（留一点余量避免每次追加都重写）时只保留最后 MAX_ENTRIES 条。"""
    try:
        path = log_file()
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) >= MAX_ENTRIES + 50:
            rows=[]
            for line in lines:
                try:
                    row=json.loads(line)
                    if isinstance(row,dict):rows.append(row)
                except (ValueError,TypeError):pass
            with open(path, "w", encoding="utf-8") as f:
                for row in _fold(rows)[-MAX_ENTRIES:]:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    except Exception:
        pass


def entries(limit=300):
    """按时间从旧到新返回最近 limit 条记录（读不到就返回空列表）。"""
    flush_errors(force=True)
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
    out=_fold(out)
    if limit and len(out) > limit:
        out = out[-limit:]
    return out


def clear():
    """清空日志（保留文件，避免句柄问题）。"""
    try:
        with _error_lock:
            _errors.clear()
            with _lock:
                with open(log_file(), "w", encoding="utf-8") as f:f.write("")
                _maintenance.pop(log_file(),None)
        return True
    except Exception:
        return False


def exception(scope, text, exc, kind='scheduler_error'):
    """Coalesce one failure episode; retain a full traceback and exact count."""
    now=time.monotonic();path=log_file()
    key=(path,scope,type(exc).__name__,str(exc))
    with _error_lock:
        state=_errors.get(key)
        if state is None:
            if len(_errors)>=64:
                _,old=_errors.popitem();_write_error(old)
            row=dict(kind=kind,text=text,detail=''.join(traceback.format_exception(type(exc),exc,exc.__traceback__)),
                     error_id=uuid.uuid4().hex,scope=scope,count=1,ts=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            row['last_ts']=row['ts'];state=dict(row=row,dirty=True,flushed=now,path=path);_errors[key]=state
            _write_error(state)
            return True
        state['row']['count']+=1;state['row']['last_ts']=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S');state['dirty']=True
        if now-state['flushed']>=30:_write_error(state)
        return False


def _write_error(state):
    if state['dirty'] and state['path']==log_file():
        add(**state['row']);state['dirty']=False;state['flushed']=time.monotonic()


def flush_errors(force=False):
    with _error_lock:
        for state in _errors.values():
            if force or time.monotonic()-state['flushed']>=30:_write_error(state)


def recovered(scope):
    with _error_lock:
        for key in list(_errors):
            if key[0]==log_file() and key[1]==scope:_write_error(_errors.pop(key))
