# -*- coding: utf-8 -*-
"""
对话框集合：命令行参数窗口 / 关于窗口 / 淡出消息提醒框 / 消息内容输入 / 操作确认
文件作者：@wenhao
"""
import tkinter as tk
from ui_window import prepare, show, button_grid

from i18n import AUTHOR, VERSION
from theme import flat_button, theme

# 参数表：(参数, 对应描述键)
PARAM_ROWS = [
    ("param_s", "param_s_desc"),
    ("param_r", "param_r_desc"),
    ("param_l", "param_l_desc"),
    ("param_sm", "param_sm_desc"),
    ("param_som", "param_som_desc"),
    ("param_rp", "param_rp_desc"),
    ("param_ra", "param_ra_desc"),
    ("param_m", "param_m_desc"),
    None,                          # 分隔线
    ("param_w", "param_w_desc"),
    ("param_t", "param_t_desc"),
    ("param_min", "param_min_desc"),
    ("param_h", "param_h_desc"),
]


class ParamDialog(tk.Toplevel):
    """「程序参数」窗口（对应截图 2）。"""

    def __init__(self, master, T):
        tk.Toplevel.__init__(self, master)
        prepare(self)
        self.T = T
        self.title(T("params_title"))
        self.configure(bg=theme.c("bg"))
        self.resizable(False, False)
        self.transient(master)

        tip = tk.Label(self, text=T("params_hint"), bg=theme.c("bg"), fg=theme.c("fg"),
                       font=theme.font(bold=True), anchor="w", justify="left")
        tip.pack(fill="x", padx=12, pady=(10, 6))

        body = tk.Frame(self, bg=theme.c("bg"))
        body.pack(fill="both", expand=True, padx=18, pady=(0, 6))

        # 信息图标
        canvas = tk.Canvas(body, width=40, height=40, bg=theme.c("bg"),
                           highlightthickness=0)
        canvas.create_oval(2, 2, 38, 38, fill=theme.accent, outline="")
        canvas.create_text(20, 21, text="i", fill="#FFFFFF",
                           font=("Times New Roman", 20, "bold"))
        canvas.grid(row=0, column=0, rowspan=len(PARAM_ROWS), sticky="n", padx=(0, 14))

        for i, row in enumerate(PARAM_ROWS):
            if row is None:
                sep = tk.Frame(body, bg=theme.c("border"), height=1)
                sep.grid(row=i, column=1, columnspan=2, sticky="ew", pady=6)
                continue
            key, desc_key = row
            tk.Label(body, text=T(key), bg=theme.c("bg"), fg=theme.c("fg"),
                     font=theme.mono(), anchor="w").grid(row=i, column=1, sticky="w",
                                                         padx=(0, 26))
            tk.Label(body, text=T(desc_key), bg=theme.c("bg"), fg=theme.c("fg"),
                     font=theme.font(), anchor="w").grid(row=i, column=2, sticky="w")

        footer = tk.Frame(self, bg=theme.c("bg"))
        footer.pack(fill="x", padx=12, pady=(4, 12))
        button_grid(footer, [(T("params_ok"),self.destroy,"accent")])

        self.bind("<Escape>", lambda e: self.destroy())
        self.update_idletasks()
        _center(self, master)
        show(self);self.grab_set()
        self.focus_set()


class AboutDialog(tk.Toplevel):
    """「关于本程序」窗口：图标 + 程序名 + 版本 + 作者 + 简介。"""

    def __init__(self, master, T, logo_image=None):
        tk.Toplevel.__init__(self, master)
        prepare(self)
        self.T = T
        self.title(T("about_title"))
        self.configure(bg=theme.c("bg"))
        self.resizable(False, False)
        self.transient(master)

        head = tk.Frame(self, bg=theme.c("header_bg"))
        head.pack(fill="x")
        if logo_image is not None:
            self._logo = logo_image
            tk.Label(head, image=logo_image, bg=theme.c("header_bg"),
                     bd=0).pack(side="left", padx=(14, 12), pady=12)
        right = tk.Frame(head, bg=theme.c("header_bg"))
        right.pack(side="left", fill="both", expand=True, pady=12)
        tk.Label(right, text=T("about_app_name"), bg=theme.c("header_bg"), fg=theme.c("fg"),
                 font=theme.font(delta=4, bold=True), anchor="w").pack(fill="x")
        tk.Label(right, text=T("about_version", v=VERSION), bg=theme.c("header_bg"),
                 fg=theme.c("accent"), font=theme.font(delta=1, bold=True),
                 anchor="w").pack(fill="x", pady=(2, 0))
        tk.Label(right, text=T("about_author", a=AUTHOR), bg=theme.c("header_bg"),
                 fg=theme.c("fg_dim"), font=theme.font(), anchor="w").pack(fill="x")
        # 运行系统（v1.1.4 新增）：方便确认当前是 Win10 还是 Win11
        try:
            from ui_main import os_display_name
            os_name = os_display_name()
        except Exception:
            os_name = "Windows"
        if T("about_os", o="") is not None:
            tk.Label(right, text=T("about_os", o=os_name), bg=theme.c("header_bg"),
                     fg=theme.c("fg_muted"), font=theme.font(delta=-1),
                     anchor="w").pack(fill="x")

        tk.Frame(self, bg=theme.accent, height=2).pack(fill="x")

        body = tk.Frame(self, bg=theme.c("bg"))
        body.pack(fill="both", expand=True, padx=16, pady=12)
        tk.Label(body, text=T("about_desc"), bg=theme.c("bg"), fg=theme.c("fg"),
                 font=theme.font(), justify="left", anchor="w",
                 wraplength=380).pack(fill="x")
        tk.Label(body, text=T("about_tip"), bg=theme.c("bg"), fg=theme.c("fg_dim"),
                 font=theme.font(delta=-1), justify="left", anchor="w",
                 wraplength=380).pack(fill="x", pady=(10, 0))

        tk.Label(body, text=T("about_contact_line"),
                 font=theme.font(), bg=theme.c("bg"), fg=theme.c("fg"),
                 anchor="w").pack(fill="x", pady=(12, 0))

        footer = tk.Frame(self, bg=theme.c("bg"))
        footer.pack(fill="x", padx=16, pady=(0, 14))
        button_grid(footer, [(T("btn_ok"),self.destroy,"accent")])

        self.bind("<Escape>", lambda e: self.destroy())
        self.update_idletasks()
        _center(self, master)
        show(self);self.grab_set()
        self.focus_set()


class MessageInputDialog(tk.Toplevel):
    """输入消息提示框内容。"""

    def __init__(self, master, T, initial=""):
        tk.Toplevel.__init__(self, master)
        prepare(self)
        self.T = T
        self.result = None
        self.title(T("dlg_message_title"))
        self.configure(bg=theme.c("bg"))
        self.resizable(False, False)
        self.transient(master)

        tk.Label(self, text=T("dlg_message_hint"), bg=theme.c("bg"), fg=theme.c("fg"),
                 font=theme.font(), anchor="w").pack(fill="x", padx=12, pady=(12, 4))
        self.txt = tk.Text(self, width=48, height=6, font=theme.font(), wrap="word",
                           relief="solid", bd=1, bg=theme.c("input_bg"),
                           fg=theme.c("input_fg"), insertbackground=theme.c("fg"),
                           highlightthickness=1, highlightbackground=theme.c("border"),
                           highlightcolor=theme.accent)
        self.txt.pack(padx=12)
        self.txt.insert("1.0", initial or "")

        bar = tk.Frame(self, bg=theme.c("bg"))
        bar.pack(fill="x", padx=12, pady=12)
        button_grid(bar, [(T("btn_cancel"),self.destroy,"normal"),(T("btn_ok"),self._ok,"accent")])

        self.bind("<Escape>", lambda e: self.destroy())
        self.update_idletasks()
        _center(self, master)
        show(self);self.grab_set()
        self.txt.focus_set()

    def _ok(self):
        self.result = self.txt.get("1.0", "end").strip()
        self.destroy()


class ConfirmActionDialog(tk.Toplevel):
    """执行操作前的确认框：确定 / 取消 + 「本次启动不再询问」。

    比 messagebox.askyesno 多一个勾选项（v1.2.0）：
    用户「这次不想被反复打断」时可以勾上，之后本次进程内不再询问；
    刻意**不写进配置文件** —— 下次打开程序仍然会照常询问。
    """

    def __init__(self, master, T, text):
        tk.Toplevel.__init__(self, master)
        prepare(self)
        self.T = T
        self.result = False
        self.dont_ask = False
        self.title(T("tip_confirm_action_title"))
        self.configure(bg=theme.c("bg"))
        self.resizable(False, False)
        self.transient(master)

        head = tk.Frame(self, bg=theme.c("header_bg"))
        head.pack(fill="x")
        tk.Label(head, text=T("tip_confirm_action_title"), bg=theme.c("header_bg"),
                 fg=theme.c("fg"), font=theme.font(bold=True),
                 anchor="w").pack(side="left", padx=12, pady=8)

        body = tk.Frame(self, bg=theme.c("bg"))
        body.pack(fill="both", expand=True, padx=16, pady=(12, 4))
        tk.Label(body, text=text, bg=theme.c("bg"), fg=theme.c("fg"),
                 font=theme.font(), justify="left", anchor="w",
                 wraplength=340).pack(fill="x")
        self.skip_var = tk.BooleanVar(value=False)
        tk.Checkbutton(body, text=T("confirm_dont_ask"), variable=self.skip_var,
                       bg=theme.c("bg"), fg=theme.c("fg"), font=theme.font(),
                       activebackground=theme.c("bg"),
                       activeforeground=theme.c("accent"),
                       selectcolor=theme.c("bg"), bd=0, highlightthickness=0,
                       anchor="w").pack(fill="x", pady=(10, 0))

        bar = tk.Frame(self, bg=theme.c("bg"))
        bar.pack(fill="x", padx=16, pady=(4, 14))
        button_grid(bar, [(T("btn_cancel"),self._cancel,"normal"),(T("btn_ok"),self._ok,"accent")])

        self.bind("<Escape>", lambda e: self._cancel())
        self.bind("<Return>", lambda e: self._ok())
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.update_idletasks()
        _center(self, master)
        show(self);self.grab_set()
        self.focus_set()

    def _ok(self):
        self.result = True
        self.dont_ask = bool(self.skip_var.get())
        self.destroy()

    def _cancel(self):
        self.result = False
        self.dont_ask = False
        self.destroy()


class FadeMessageBox(tk.Toplevel):
    """淡入 / 淡出的消息提醒框（无边框，右下角弹出，自动淡出）。

    v1.2.0 起支持：
      · seconds 由调用方（配置项「消息提示框停留时长」）决定；
      · 可选带一个动作按钮（button_text / on_button）——
        「到点前 10 秒可取消」就是靠它实现的。
    """

    def __init__(self, master, title, text, seconds=15, on_close=None,
                 button_text=None, on_button=None, extra_buttons=None):
        tk.Toplevel.__init__(self, master)
        prepare(self)
        self.on_close = on_close
        self.on_button = on_button
        self._button_clicked = False
        self._closed = False
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        try:
            self.attributes("-alpha", 0.0)
        except Exception:
            pass

        accent = theme.accent
        card = theme.c("card")
        outer = tk.Frame(self, bg=accent, bd=0)
        outer.pack(fill="both", expand=True)
        inner = tk.Frame(outer, bg=card)
        inner.pack(fill="both", expand=True, padx=2, pady=2)

        head = tk.Frame(inner, bg=accent)
        head.pack(fill="x")
        tk.Label(head, text=title, bg=accent, fg="#FFFFFF",
                 font=theme.font(bold=True), anchor="w").pack(side="left", padx=10, pady=6)
        close = tk.Label(head, text="✕", bg=accent, fg="#FFFFFF",
                         font=("Segoe UI", 10, "bold"), cursor="hand2")
        close.pack(side="right", padx=8)
        close.bind("<Button-1>", lambda e: self.close())

        body = tk.Frame(inner, bg=card)
        body.pack(fill="both", expand=True, padx=14, pady=12)
        tk.Label(body, text=text, bg=card, fg=theme.c("fg"), font=theme.font(),
                 wraplength=320, justify="left", anchor="w").pack(fill="x")

        self._btn = None
        items=[(label,callback,"plain") for label,callback in (extra_buttons or [])]
        if button_text:items.append((button_text,self._fire_button,"accent"))
        if items:
            row = tk.Frame(body, bg=card)
            row.pack(fill="x", pady=(12,0))
            buttons=button_grid(row,items,columns=2 if len(items)==4 else len(items))
            if button_text:self._btn=buttons[-1]
        self._tick_label = tk.Label(head, text="", bg=accent, fg="#FFFFFF",font=theme.font(delta=-1))
        self._tick_label.pack(side="right",padx=8)

        self.update_idletasks()
        self._place_bottom_right()
        self.deiconify()
        self._fade_in()
        try:
            self._countdown = max(1, int(seconds))
        except Exception:
            self._countdown = 15
        self._auto_close()

    # ---------------------------------------------------------- 位置与动画
    def _place_bottom_right(self):
        try:
            w = self.winfo_reqwidth()
            h = self.winfo_reqheight()
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            self.geometry("%dx%d+%d+%d" % (max(w, 360), h, sw - max(w, 360) - 24, sh - h - 64))
        except Exception:
            pass

    def _fade_in(self, step=0, steps=12):
        if self._closed:
            return
        alpha = min(0.97, 0.97 * (step + 1) / steps)
        try:
            self.attributes("-alpha", alpha)
        except Exception:
            return
        if step + 1 < steps:
            self.after(25, lambda: self._fade_in(step + 1, steps))

    def _fade_out(self, step=0, steps=16):
        if self._closed:
            return
        alpha = max(0.0, 0.97 * (steps - step) / steps)
        try:
            self.attributes("-alpha", alpha)
        except Exception:
            pass
        if step + 1 < steps:
            self.after(25, lambda: self._fade_out(step + 1, steps))
        else:
            self._finish()

    def _auto_close(self):
        if self._closed:
            return
        if self._countdown > 0:
            self._tick_label.config(text="%ds" % self._countdown)
            self._countdown -= 1
            self.after(1000, self._auto_close)
        else:
            self._fade_out()

    # ---------------------------------------------------------- 对外
    def _fire_button(self):
        """点动作按钮：先关掉自己，再执行回调（回调里可能弹别的窗口）。"""
        if self._button_clicked or self._closed:
            return
        self._button_clicked = True
        cb = self.on_button
        self.close()
        if cb:
            try:
                cb()
            except Exception:
                pass

    def close(self):
        if self._closed:
            return
        self._fade_out()

    def _finish(self):
        if self._closed:
            return
        self._closed = True
        try:
            self.destroy()
        except Exception:
            pass
        if self.on_close:
            try:
                self.on_close()
            except Exception:
                pass


def _center(win, master):
    try:
        win.update_idletasks()
        w, h = win.winfo_width(), win.winfo_height()
        px, py = master.winfo_rootx(), master.winfo_rooty()
        pw, ph = master.winfo_width(), master.winfo_height()
        win.geometry("+%d+%d" % (px + (pw - w) // 2, py + (ph - h) // 3))
    except Exception:
        pass
