# -*- coding: utf-8 -*-
"""
定时器引擎：倒计时 / 指定日期（星期几 + 时刻）/ 时间段循环
文件作者：@wenhao
"""
import datetime
import threading
import time

from app_config import M_COUNTDOWN, M_DATETIME, M_INTERVAL

TICK = 0.2          # 刷新间隔（秒）
WARN_SECONDS = 10   # 10 秒预警阈值


class TimerEngine(object):
    """独立的计时线程，通过 emit(event, payload) 把事件交给界面层。"""

    def __init__(self, emit):
        self._emit = emit
        self._stop_evt = threading.Event()
        self._lock = threading.Lock()
        self._due_wall = None
        self._deadline = 0.0
        self._total = 0.0
        self._mode = M_COUNTDOWN
        self._interval = 0.0
        self._paused = False
        self._pause_at = 0.0
        self.warning_seconds = WARN_SECONDS
        self._warned = False
        self._alive = False
        self._thread = None
        # 每「一轮计时」的唯一编号。线程主体持有自己那一轮拿到的号，
        # 一旦发现号变了就说明自己已被更年轻的实例取代，必须立刻退出 ——
        # 光靠 _stop_evt 拦不住（见 _run 里的注释）。
        self._gen = 0

    # ------------------------------------------------------------ 对外接口
    @property
    def mode(self):
        return self._mode

    @property
    def paused(self):
        return self._paused

    def is_running(self):
        return self._alive and not self._stop_evt.is_set()

    @property
    def generation(self):
        """当前这一轮的编号。

        界面层拿它和 tick / warn 事件里带的 gen 比对：
        对不上说明是**上一轮**漏出来的旧事件（stop / 重新开始之后，
        队列里还躺着最后一条），必须丢掉 —— 否则状态栏会被它改写回
        「定时器运行中」，点「取消执行」看着像没生效。
        """
        return self._gen

    # ------------------------------------------------------------ 查询状态
    def remaining(self):
        """本轮的剩余秒数（暂停时按暂停那一刻算）；未运行返回 0。"""
        with self._lock:
            if not self._alive:
                return 0.0
            if self._paused:
                return max(0.0, self._deadline - self._pause_at)
            return max(0.0, self._deadline - time.monotonic())

    def total_seconds(self):
        with self._lock:
            return float(self._total)

    def due_at(self):
        """本轮预计的**墙上时间**触发时刻；未运行返回 None。

        状态栏用它显示「预计 18:00:00 执行」—— 比剩余秒数直观得多
        （用户想知道的是「几点动手」，而不是「还有多少秒」）。
        暂停状态下按「现在 + 剩余」推算，这样恢复后数字仍然对得上。
        """
        with self._lock:
            if not self._alive:return None
            if self._paused:return datetime.datetime.now()+datetime.timedelta(seconds=max(0,self._deadline-self._pause_at))
            return self._due_wall

    # ------------------------------------------------------------ 启动 / 停止
    def start_countdown(self, seconds):
        self._start(float(seconds), M_COUNTDOWN)

    def start_interval(self, seconds):
        self._interval = float(seconds)
        self._start(float(seconds), M_INTERVAL)

    def start_datetime(self, target):
        now = datetime.datetime.now()
        delta = (target - now).total_seconds()
        if delta < 0:
            delta = 0.0
        self._start(delta, M_DATETIME, target)

    def _start(self, seconds, mode, wall_target=None):
        self.stop()                     # 先作废可能在跑的旧线程（gen 会 +1）
        with self._lock:
            self._gen += 1
            gen = self._gen
            self._mode = mode
            self._total = max(0.0, (wall_target-datetime.datetime.now()).total_seconds() if wall_target is not None else seconds)
            self._due_wall = wall_target if wall_target is not None else datetime.datetime.now()+datetime.timedelta(seconds=self._total)
            self._deadline = time.monotonic() + self._total
            self._paused = False
            self._warned = False
            self._stop_evt.clear()
            self._alive = True
        self._emit("started", {"mode": mode, "total": self._total})
        self._thread = threading.Thread(target=self._run, args=(gen,), daemon=True,
                                        name="HaozaiziTimer")
        self._thread.start()

    def pause(self):
        with self._lock:
            if not self.is_running() or self._paused:
                return False
            self._paused = True
            self._pause_at = time.monotonic()
            remain = max(0.0, self._deadline - self._pause_at)
        self._emit("paused", {"remain": remain})
        return True

    def resume(self):
        with self._lock:
            if not self.is_running() or not self._paused:
                return False
            elapsed=time.monotonic()-self._pause_at
            self._deadline += elapsed
            if self._due_wall is not None:self._due_wall += datetime.timedelta(seconds=elapsed)
            self._paused = False
            self._warned = False
        self._emit("resumed", {})
        return True

    def stop(self):
        was = self.is_running()
        with self._lock:
            self._gen += 1              # 作废当前线程（哪怕它正卡在 sleep 里）
        self._stop_evt.set()
        self._alive = False
        if was:
            self._emit("stopped", {})

    # ------------------------------------------------------------ 线程主体
    def _run(self, gen):
        """计时线程主体。gen = 本线程所属那一轮的编号。

        为什么需要 gen（血泪）：
        `_start()` 里 `stop()` 之后紧接着 `_stop_evt.clear()`。旧线程如果
        正好卡在 `time.sleep(TICK)` 里（0.2 秒，占了一轮循环的绝大部分时间，
        所以**几乎必然**命中），醒来后回到循环条件一看事件已被 clear，
        就会当成「没被停过」继续跑下去 —— 于是同一个倒计时有**两个线程**
        在数，到点各发一次 `finished`，界面层的 `perform_action` 就被执行
        **两遍**（弹两个提示框 / 启动两次程序 / 循环模式频率翻倍）。
        实测：3 秒倒计时跑到 0.5 秒时再点一次「开始」→ finished 事件 2 个，
        tick 频率 10 次/秒（正常 5 次/秒）。
        所以判据不能是「事件有没有被 set」，必须是「我这一轮还是不是当前那一轮」。
        """
        while True:
            with self._lock:
                if gen != self._gen or self._stop_evt.is_set():
                    return
                if self._paused:
                    remain = max(0.0, self._deadline - self._pause_at)
                else:
                    remain = self._deadline - time.monotonic()

            if remain <= 0:
                with self._lock:
                    # 出锁前再确认一次：这段时间里用户可能又点了「开始」
                    if gen != self._gen or self._stop_evt.is_set():
                        return
                    mode = self._mode
                    total = self._total
                    interval = self._interval
                self._emit("tick", {"remain": 0.0, "total": total,
                                    "mode": mode, "percent": 100.0,
                                    "gen": gen})
                if mode == M_INTERVAL and interval > 0:
                    # 循环模式：执行完继续下一轮
                    self._emit("finished", {"mode": mode, "repeat": True, "gen": gen})
                    with self._lock:
                        if gen != self._gen:
                            return
                        self._total = interval
                        self._deadline = time.monotonic() + interval
                        self._due_wall = datetime.datetime.now()+datetime.timedelta(seconds=interval)
                        self._warned = False
                    continue
                with self._lock:
                    if gen != self._gen or self._stop_evt.is_set():return
                    self._alive = False
                self._emit("finished", {"mode": mode, "repeat": False, "gen": gen})
                return

            if not self._paused and not self._warned and remain <= self.warning_seconds:
                self._warned = True
                self._emit("warn", {"remain": remain, "gen": gen})

            percent = 0.0
            if self._total > 0:
                percent = min(100.0, max(0.0, (1.0 - remain / self._total) * 100.0))
            self._emit("tick", {"remain": remain, "total": self._total,
                                "mode": self._mode, "percent": percent,
                                "gen": gen})
            time.sleep(TICK)


def next_datetime(weekday, hour, minute, second):
    """计算下一次出现的“星期几 时:分:秒”（星期几为 0=星期一）。"""
    now = datetime.datetime.now()
    days = (int(weekday) - now.weekday()) % 7
    target = (now + datetime.timedelta(days=days)).replace(
        hour=int(hour), minute=int(minute), second=int(second), microsecond=0)
    if target <= now:
        target += datetime.timedelta(days=7)
    return target


def resolve_at(hour, minute, second=0, now=None):
    """把「今天 时:分:秒」解析成一个**将来**的时刻：今天已过就顺延到明天。

    快捷预设按钮用的就是它 —— 点「今天 18:00」时如果已经 19:00，
    用户心里想的是「明天 18:00」，而不是 next_datetime() 给的「下周一 18:00」。
    """
    if now is None:
        now = datetime.datetime.now()
    target = now.replace(hour=int(hour), minute=int(minute),
                         second=int(second), microsecond=0)
    if target <= now:
        target += datetime.timedelta(days=1)
    return target
