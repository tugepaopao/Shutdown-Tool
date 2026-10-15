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


from ui_reminder import FadeMessageBox


def _center(win, master):
    try:
        win.update_idletasks()
        w, h = win.winfo_width(), win.winfo_height()
        px, py = master.winfo_rootx(), master.winfo_rooty()
        pw, ph = master.winfo_width(), master.winfo_height()
        win.geometry("+%d+%d" % (px + (pw - w) // 2, py + (ph - h) // 3))
    except Exception:
        pass
