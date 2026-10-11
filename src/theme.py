# -*- coding: utf-8 -*-
"""
主题系统（v1.3.0 小清新重构版）
文件作者：@wenhao

设计说明
--------
v1.2.1 → v1.3.0 的视觉重构：从「传统 Win32 分组框风」改为
「小清新卡片风」—— 参考侧边导航 + 圆角卡片 + 浅蓝留白的现代桌面应用观感。

重构原则（很重要）：
1. **所有原有色键必须保留**（bg / card / fg / fg_dim / fg_muted / disabled /
   border / header_bg / status_bg / status_fg / hover / select_bg /
   input_bg / input_fg / accent_fg / warn_bg），
   因为 ui_settings / ui_dialogs / ui_queue / ui_log / tray 都在用它们。
   新增色键只能"加"，不能"改名"。
2. 新增小清新专属色键：page（页面渐变底色）、nav_bg / nav_fg / nav_active_bg /
   nav_active_fg（侧边导航）、card_border / shadow / ring（卡片描边与光晕）、
   pill_*（胶囊按钮）。
3. 浅色模式改用「浅蓝白」渐变基调，深色模式保持沉稳但同样走圆角卡片风。

深色模式在 Windows 默认 vista 主题下无法改按钮底色，所以深色切 clam；
浅色同样切 clam（v1.3.0 起改为 clam）—— 因为自绘控件已占绝大多数，
clam 下的 ttk 控件能被完整配色，观感比 vista 更统一、更"扁平小清新"。
"""
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

FONT_FAMILY = "Microsoft YaHei UI"

# ------------------------------------------------------------------ 主题色
# v1.3.0：整体系列调亮、调柔，去掉原来偏"重"的深色系，换成小清新的明亮色。
ACCENTS = {
    "blue":   "#3274D9",
    "teal":   "#13847E",
    "green":  "#268244",
    "orange": "#C67127",
    "red":    "#C43F43",
    "pink":   "#B84072",
    "purple": "#7953BD",
    "indigo": "#5263CF",
}
ACCENT_ORDER = ["blue", "teal", "green", "orange", "red", "pink", "purple", "indigo"]

# ------------------------------------------------------------------ 字号档位
FONT_SIZE_MAP = {"small": 8, "normal": 10, "large": 10, "huge": 11}
FONT_SIZE_ORDER = ["small", "normal", "large", "huge"]

# ------------------------------------------------------------------ 调色板
PALETTES = {
    "light": {
        # ---- 原有色键（不可删，其它模块依赖）----
        "bg":          "#F5F8FD",   # 窗口底色（原 #F2F4F7 → 偏蓝的极浅灰蓝）
        "card":        "#FFFFFF",   # 卡片 / 输入框底色
        "fg":          "#1F2A37",   # 主文字（原 #14181F → 稍柔和的墨蓝黑）
        "fg_dim":      "#5B6B7F",   # 次要文字
        "fg_muted":    "#93A1B5",   # 更淡的说明文字
        "disabled":    "#A9B7CA",   # 禁用文字（原 #B6C1D0 → 更柔和的雾蓝灰）
        "border":      "#DCE4EF",   # 描边（原 #C3CAD4 → 极浅蓝灰，更"轻"）
        "header_bg":   "#FFFFFF",   # 顶部条 → 白色，与卡片同色
        "status_bg":   "#EEF4FC",   # 底部状态栏 → 浅蓝
        "status_fg":   "#3C4A5E",
        "hover":       "#EDF3FE",   # 悬停（浅蓝）
        "select_bg":   "#DCEAFE",
        "input_bg":    "#FFFFFF",
        "input_fg":    "#1F2A37",
        "accent_fg":   "#FFFFFF",
        "warn_bg":     "#FFF6E5",
        "warn_fg":     "#9A6A15",   # 警示条文字（v1.3.1：队列浮层用，暖棕在浅黄底上够清楚）
        # ---- v1.3.0 新增：小清新专属 ----
        "page_top":    "#EAF2FF",   # 页面渐变起始（上，淡蓝）
        "page_bot":    "#F7FAFF",   # 页面渐变结束（下，近白）
        "nav_bg":      "#FFFFFF",   # 侧边导航底
        "nav_fg":      "#5B6B7F",   # 导航未选中文字
        "nav_active_bg": "#E8F1FE", # 导航选中底（浅蓝块）
        "nav_active_fg": "#3B7BE0", # 导航选中文字
        "nav_hover_bg": "#F1F6FE",
        "card_border": "#E3EBF7",   # 卡片细描边
        "divider":     "#EAF0F9",   # 分隔线
        "shadow":      "#D6E2F5",   # 阴影/光晕色
        "badge_bg":    "#EEF4FC",   # 版本号小胶囊底
        "sel_row_bg":  "#E8F2FE",   # 操作行选中底（浅蓝）
        "sel_row_fg":  "#2E62C4",   # 操作行选中文字
        # ---- v1.3.1 新增：消除「土气灰」----
        # 表头不再用系统默认的灰色渐变，改成比卡片略深的淡蓝，和正文拉开层次
        "head_bg":     "#EDF3FC",   # Treeview 表头底
        "head_fg":     "#5A6B82",   # Treeview 表头文字
        "alt_row_bg":  "#FAFCFF",   # 隔行浅底（可选，目前未启用）
        "scroll_bg":   "#F2F6FC",   # 滚动条槽
        "scroll_fg":   "#C6D4E6",   # 滚动条滑块
        "backdrop_bg": "#EEF4FD",   # 「立即执行」横幅底色（原来直接借 status_bg，偏灰）
    },
    "dark": {
        # ---- 原有色键 ----
        "bg":          "#1B2027",
        "card":        "#252B34",
        "fg":          "#EAF0F7",
        "fg_dim":      "#A9B6C6",
        "fg_muted":    "#7B8798",
        "disabled":    "#6B7686",
        "border":      "#333B47",
        "header_bg":   "#222831",   # → 与卡片接近
        "status_bg":   "#191E25",
        "status_fg":   "#C3CDD9",
        "hover":       "#2F3844",
        "select_bg":   "#2C3B4F",
        "input_bg":    "#1E242C",
        "input_fg":    "#EAF0F7",
        "accent_fg":   "#FFFFFF",
        "warn_bg":     "#3A3021",
        "warn_fg":     "#E8C57A",   # 警示条文字（深底上用暖黄）
        # ---- v1.3.0 新增 ----
        "page_top":    "#20262E",
        "page_bot":    "#181D24",
        "nav_bg":      "#222831",
        "nav_fg":      "#9AA7B7",
        "nav_active_bg": "#2C3B4F",
        "nav_active_fg": "#8FB6FF",
        "nav_hover_bg": "#2A313B",
        "card_border": "#333B47",
        "divider":     "#2B323C",
        "shadow":      "#141920",
        "badge_bg":    "#2A313B",
        "sel_row_bg":  "#2C3B4F",
        "sel_row_fg":  "#9CC0FF",
        # ---- v1.3.1 新增 ----
        "head_bg":     "#2A313B",
        "head_fg":     "#9AA7B7",
        "alt_row_bg":  "#212730",
        "scroll_bg":   "#1E242C",
        "scroll_fg":   "#3D4855",
        "backdrop_bg": "#26313F",
    },
}

MODE_ORDER = ["light", "dark", "system"]

# ------------------------------------------------------------------ 圆角 / 间距
RADIUS = 12          # 卡片圆角半径
RADIUS_SM = 8        # 小控件圆角
RADIUS_PILL = 999    # 胶囊（按实际高度取半）


def system_mode():
    """读取 Windows「应用使用浅色主题」设置，失败回退浅色。"""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        try:
            val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        finally:
            winreg.CloseKey(key)
        return "light" if int(val) else "dark"
    except Exception:
        return "light"


def shade(hex_color, factor):
    """把颜色调暗/调亮：factor<1 变暗，>1 变亮。"""
    try:
        h = hex_color.lstrip("#")
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        r = max(0, min(255, int(r * factor)))
        g = max(0, min(255, int(g * factor)))
        b = max(0, min(255, int(b * factor)))
        return "#%02X%02X%02X" % (r, g, b)
    except Exception:
        return hex_color


def blend(c1, c2, t):
    """在两个颜色之间线性插值：t=0 取 c1，t=1 取 c2。"""
    try:
        a = c1.lstrip("#")
        b = c2.lstrip("#")
        out = []
        for i in (0, 2, 4):
            x = int(a[i:i + 2], 16)
            y = int(b[i:i + 2], 16)
            out.append(max(0, min(255, int(x + (y - x) * t))))
        return "#%02X%02X%02X" % tuple(out)
    except Exception:
        return c1


@__import__('functools').lru_cache(maxsize=16)
def palette_for(accent_key):
    """方案B：每种主题色派生浅底、卡片、边框，正文保持足够对比度。"""
    accent=ACCENTS.get(accent_key,ACCENTS['orange'])
    p=dict(PALETTES['light'])
    p.update(fg='#493224',fg_dim='#796454',fg_muted='#8A7463',disabled='#A89480',input_fg='#493224',accent_fg='#FFFCF7',warn_bg='#FFF0D8',warn_fg='#85531C')
    tints={'bg':.085,'card':.03,'header_bg':.085,'status_bg':.12,'hover':.17,
           'select_bg':.22,'page_top':.06,'page_bot':.015,'nav_bg':.008,
           'nav_active_bg':.14,'nav_hover_bg':.07,'card_border':.20,'divider':.12,
           'shadow':.15,'badge_bg':.07,'sel_row_bg':.21,'head_bg':.06,
           'alt_row_bg':.025,'scroll_bg':.035,'scroll_fg':.26,'backdrop_bg':.08}
    p.update({key:blend('#FFF9F0' if key in ('bg','page_top','page_bot') else '#FFFCF7',accent,t) for key,t in tints.items()})
    p['input_bg']='#FFFCF7';p['border']=blend('#EDDCC8',accent,.14)
    p['shadow']=blend('#DED1BE',accent,.10)
    p['status_fg']=p['fg_dim'];p['nav_fg']=p['fg_dim'];p['head_fg']=p['fg_dim']
    p['nav_active_fg']=p['sel_row_fg']=shade(accent,.75)
    return p


class Theme(object):
    """全局主题单例。"""

    def __init__(self):
        self.mode_key = "light"      # light | dark | system（用户选择）
        self.mode = "light"          # 实际生效：light | dark
        self.accent_key = "orange"
        self.size_key = "normal"

    # ---------------------------------------------------------- 读配置
    def load(self, cfg):
        self.mode_key = self.mode = "light"
        self.accent_key = self._pick(cfg.get("accent"), ACCENT_ORDER, "orange")
        self.size_key = "normal"
        return self

    @staticmethod
    def _pick(value, allowed, default):
        return value if value in allowed else default

    # ---------------------------------------------------------- 取色 / 取字
    @property
    def p(self):
        return getattr(self, '_transition_palette', None) or palette_for(self.accent_key)

    def c(self, key):
        """取调色板颜色；accent 单独走主题色。"""
        if key == "accent":
            return self.accent
        return self.p.get(key, "#FF00FF")

    @property
    def accent(self):
        return getattr(self, '_transition_accent', None) or ACCENTS[self.accent_key]

    @property
    def accent_soft(self):
        """主题色的浅色版（用于选中底、浅色块）。"""
        return blend(self.accent, self.p["card"],
                     0.14 if not self.is_dark else 0.22)

    @property
    def is_dark(self):
        return self.mode == "dark"

    @property
    def base_size(self):
        return FONT_SIZE_MAP[self.size_key]

    def font(self, delta=0, bold=False):
        """按当前字号档位取字体：delta=-1 得小字，bold=True 得粗体。"""
        size = max(7, self.base_size + delta)
        return (FONT_FAMILY, size, "bold") if bold else (FONT_FAMILY, size)

    def mono(self, delta=1):
        return ("Consolas", max(8, self.base_size + delta))

    # ---------------------------------------------------------- ttk 样式
    def apply_ttk(self, root):
        style = ttk.Style(root)
        p = self.p
        # v1.3.0：浅色也统一走 clam，配色才可控（vista 主题不吃自定义底色）
        try:
            if style.theme_use() != "clam":
                style.theme_use("clam")
        except Exception:
            pass

        style.configure('TaskCenter.TNotebook', background=p['bg'], borderwidth=0)
        style.configure('TaskCenter.TNotebook.Tab', padding=(16, 8), background=p['head_bg'], foreground=p['fg'])
        style.map('TaskCenter.TNotebook.Tab', background=[('selected', p['sel_row_bg'])], foreground=[('selected', self.accent)], padding=[('selected', (16, 8)), ('!selected', (16, 8))], expand=[('selected', (0, 0, 0, 0)), ('!selected', (0, 0, 0, 0))])

        # 所有 ttk 控件统一字体
        base = self.font()
        for name in ("TButton", "TCheckbutton", "TRadiobutton", "TCombobox",
                     "TSpinbox", "TEntry", "TMenubutton", "TLabel",
                     "Treeview", "TNotebook.Tab"):
            try:
                style.configure(name, font=base)
            except Exception:
                pass
        try:
            style.configure("Treeview", rowheight=max(22, tkfont.Font(font=base).metrics("linespace") + 8))
            style.configure("Treeview.Heading", font=self.font(bold=True))
        except Exception:
            pass
        try:
            style.configure("TFrame", background=p["bg"])
            style.configure("TLabel", background=p["bg"], foreground=p["fg"])
        except Exception:
            pass

        # 进度条：v1.3.0 改细 + 圆润，纯主题色无边框
        try:
            style.configure("Horizontal.TProgressbar",
                            troughcolor=p["divider"],
                            background=self.accent, bordercolor=p["divider"],
                            lightcolor=self.accent, darkcolor=self.accent,
                            thickness=10)
            style.configure('Summary.Horizontal.TProgressbar',troughcolor=p['divider'],background=self.accent,bordercolor=p['divider'],lightcolor=self.accent,darkcolor=self.accent,thickness=4,borderwidth=0)
            style.layout('Summary.Horizontal.TProgressbar',[('Horizontal.Progressbar.trough',{'sticky':'nswe','children':[('Horizontal.Progressbar.pbar',{'side':'left','sticky':'ns'})]})])
        except Exception:
            pass

        # ---- clam 下逐项配色（浅色深色都走这里了）----
        try:
            style.configure("TButton", background=p["card"], foreground=p["fg"],
                            bordercolor=p["card_border"], lightcolor=p["card"],
                            darkcolor=p["card"], focuscolor=self.accent,
                            relief="flat", padding=(10, 5))
            style.map("TButton",
                      background=[("pressed", p["hover"]), ("active", p["hover"]),
                                  ("disabled", p["bg"])],
                      foreground=[("disabled", p["disabled"])])
            style.configure("TCheckbutton", background=p["bg"], foreground=p["fg"],
                            indicatorcolor=p["input_bg"], focuscolor=self.accent)
            style.map("TCheckbutton",
                      background=[("active", p["bg"])],
                      foreground=[("disabled", p["disabled"])])
            style.configure("TRadiobutton", background=p["bg"], foreground=p["fg"],
                            indicatorcolor=p["input_bg"], focuscolor=self.accent)
            style.map("TRadiobutton",
                      background=[("active", p["bg"])],
                      foreground=[("disabled", p["disabled"])])
            style.configure("TCombobox", fieldbackground=p["input_bg"],
                            background=p["card"], foreground=p["input_fg"],
                            arrowcolor=p["fg_dim"], bordercolor=p["card_border"],
                            lightcolor=p["card_border"], darkcolor=p["card_border"],
                            selectbackground=p["select_bg"], selectforeground=p["fg"],
                            padding=(6, 3))
            style.map("TCombobox",
                      fieldbackground=[("readonly", p["input_bg"]),
                                       ("disabled", p["bg"])],
                      foreground=[("readonly", p["input_fg"]),
                                  ("disabled", p["disabled"])])
            style.configure("TSpinbox", fieldbackground=p["input_bg"],
                            background=p["card"], foreground=p["input_fg"],
                            arrowcolor=p["fg_dim"], bordercolor=p["card_border"],
                            lightcolor=p["card_border"], darkcolor=p["card_border"],
                            insertcolor=p["fg"], padding=(4, 3))
            style.map("TSpinbox",
                      fieldbackground=[("disabled", p["bg"])],
                      foreground=[("disabled", p["disabled"])])
            style.configure("TEntry", fieldbackground=p["input_bg"],
                            foreground=p["input_fg"], bordercolor=p["card_border"],
                            insertcolor=p["fg"])
            style.configure("Treeview", background=p["card"], fieldbackground=p["card"],
                            foreground=p["fg"], bordercolor=p["card_border"],
                            lightcolor=p["card"], darkcolor=p["card"],
                            borderwidth=0, relief="flat")
            style.map("Treeview",
                      background=[("selected", p["sel_row_bg"])],
                      foreground=[("selected", p["sel_row_fg"])])
            # ---- 表头：默认 clam 是一坨灰色渐变（用户说的「土里土气」），
            #      改成淡蓝平涂 + 柔和文字色，和卡片融为一体
            style.configure("Treeview.Heading",
                            background=p["head_bg"], foreground=p["head_fg"],
                            bordercolor=p["card_border"], relief="flat",
                            borderwidth=0, padding=(6, 5))
            style.map("Treeview.Heading",
                      background=[("active", p["hover"])],
                      foreground=[("active", p["fg_dim"])])
            # ---- 滚动条：默认是很重的立体灰条，改成细窄浅色
            for orient in ("Vertical", "Horizontal"):
                style.configure("%s.TScrollbar" % orient,
                                background=p["scroll_fg"],
                                troughcolor=p["scroll_bg"],
                                bordercolor=p["scroll_bg"],
                                lightcolor=p["scroll_fg"],
                                darkcolor=p["scroll_fg"],
                                arrowcolor=p["fg_muted"],
                                relief="flat", borderwidth=0,
                                width=10, arrowsize=12)
                style.map("%s.TScrollbar" % orient,
                          background=[("active", theme.accent),
                                      ("pressed", theme.accent)],
                          arrowcolor=[("active", p["fg_dim"])])
        except Exception:
            pass

        # 下拉列表（Tk 原生 Listbox）配色
        try:
            root.option_add("*TCombobox*Listbox.background", p["input_bg"])
            root.option_add("*TCombobox*Listbox.foreground", p["input_fg"])
            root.option_add("*TCombobox*Listbox.selectBackground", self.accent)
            root.option_add("*TCombobox*Listbox.selectForeground", p["accent_fg"])
            root.option_add("*TCombobox*Listbox.borderWidth", 0)
        except Exception:
            pass


theme = Theme()


def init_theme(cfg):
    """在创建 Tk 根窗口之前调用。"""
    theme.load(cfg)
    return theme


# ==================================================================== 绘制工具
def round_points(x1, y1, x2, y2, r):
    """生成圆角矩形的多边形顶点（Tk canvas 用 smooth=True 会自动圆化）。"""
    r = max(0, min(r, (x2 - x1) / 2.0, (y2 - y1) / 2.0))
    return [
        x1 + r, y1,  x2 - r, y1,  x2, y1,
        x2, y1 + r,  x2, y2 - r,  x2, y2,
        x2 - r, y2,  x1 + r, y2,  x1, y2,
        x1, y2 - r,  x1, y1 + r,  x1, y1,
    ]


def draw_round_rect(canvas, x1, y1, x2, y2, radius=RADIUS, fill="#FFFFFF",
                    outline="", width=1, tags=None):
    """在 canvas 上画一个圆角矩形，返回 item id。"""
    pts = round_points(x1, y1, x2, y2, radius)
    kw = dict(fill=fill or "", outline=outline or "", width=width,
              smooth=True, splinesteps=24)
    if tags:
        kw["tags"] = tags
    return canvas.create_polygon(pts, **kw)


# ==================================================================== 控件工厂
def flat_button(parent, text, command=None, kind="normal", pady=5, padx=12,
                width=None, font=None, height=None):
    """扁平按钮（自绘配色，浅色 / 深色都能跟随主题）。

    kind:
      accent —— 主题色实心（强调色按钮）
      normal —— 卡片色实心（普通按钮）
      plain  —— 完全透明，只有文字 + 一圈浅色细边框（悬停才浮起浅色）
      ghost  —— 透明底 + 次要文字色（给「…」这类小按钮用）
      nav    —— 侧边导航项：无边框，选中态由外部用 apply_nav_state 切换
    """
    p = theme.p
    if kind == "accent":
        bg, fg = theme.accent, p["accent_fg"]
        hover = shade(theme.accent, 1.12 if theme.is_dark else 0.90)
        border = theme.accent
    elif kind == "plain":
        bg, fg = p["bg"], p["fg"]
        hover = p["hover"]
        border = p["border"]
    elif kind == "ghost":
        bg, fg = p["bg"], p["fg_dim"]
        hover = p["hover"]
        border = p["card_border"]
    elif kind == "nav":
        bg, fg = p["nav_bg"], p["nav_fg"]
        hover = p["nav_hover_bg"]
        border = p["nav_bg"]
    else:
        bg, fg = p["card"], p["fg"]
        hover = p["hover"]
        border = p["card_border"]

    from ui_cozy import CozyButton
    btn = CozyButton(parent, text=text, command=command, bg=bg, fg=fg,
                    activebackground=hover, activeforeground=fg,
                    relief="flat", bd=0, highlightthickness=1,
                    highlightbackground=border, highlightcolor=theme.accent,
                    cursor="hand2", font=font or theme.font(),
                    padx=padx, pady=pady)
    if width is not None:
        btn.config(width=width)
    if height is not None:
        btn.config(height=height)
    btn._bg = bg
    btn._fg = fg
    btn._hover = hover
    btn._border = border
    btn._kind = kind

    def _enter(_e=None):
        if str(btn["state"]) != "disabled" and not getattr(btn, "_nav_active", False):
            btn.config(bg=btn._hover)

    def _leave(_e=None):
        if str(btn["state"]) != "disabled" and not getattr(btn, "_nav_active", False):
            btn.config(bg=btn._bg)

    btn.bind("<Enter>", _enter)
    btn.bind("<Leave>", _leave)
    return btn


def apply_nav_state(btn, active):
    """切换侧边导航项的选中态（选中 = 浅蓝底 + 主题色文字 + 加粗）。"""
    if btn is None:
        return
    p = theme.p
    try:
        btn._nav_active = bool(active)
        if active:
            btn.config(bg=p["nav_active_bg"], fg=p["nav_active_fg"],
                       highlightbackground=p["nav_active_bg"],
                       activebackground=p["nav_active_bg"],
                       activeforeground=p["nav_active_fg"],
                       font=theme.font(bold=True))
        else:
            btn.config(bg=p["nav_bg"], fg=p["nav_fg"],
                       highlightbackground=p["nav_bg"],
                       activebackground=p["nav_hover_bg"],
                       activeforeground=p["nav_fg"],
                       font=theme.font())
    except Exception:
        pass


def enable_button(btn, enabled):
    """启用 / 禁用扁平按钮（同时处理配色，别用 config(state=...) 直接切）。"""
    if btn is None:
        return
    p = theme.p
    try:
        if enabled:
            btn.config(state="normal", fg=btn._fg, cursor="hand2")
            if getattr(btn, "_nav_active", False):
                apply_nav_state(btn, True)
            else:
                btn.config(bg=btn._bg)
        else:
            # v1.3.1：禁用态改成「淡底 + 淡字」，而不是原来的纯底色 + 灰字。
            # 原来 disabled 的按钮直接融进背景，看起来像"消失了一块"，
            # 现在留一圈极浅的底，仍是"不可点"但形状还在，观感柔和很多。
            btn.config(state="disabled", fg=p["disabled"], cursor="arrow",
                       bg=p["divider"],
                       disabledforeground=p["disabled"])
    except Exception:
        pass


def card_frame(parent, pad=0, bg=None):
    """一块小清新卡片：白底 + 极浅描边（用 highlight 模拟圆角观感）。

    说明：Tk 原生 Frame 画不出真圆角，这里用「1px 极浅描边 + 白底」
    配合外层留白来营造卡片感；需要真圆角的地方用 draw_round_rect 画在 canvas 上。

    ⚠️ highlightthickness=1 会让控件四周各多占 1px，且**这 1px 是画在
    highlightbackground 上的**——若父容器有背景色，会比"纯白卡片"更贴边。
    因此调用方应当在 pack 时留出 padx/pady，不要让它贴到窗口边缘。
    """
    p = theme.p
    from ui_cozy import CozyFrame
    f = CozyFrame(parent, bg=bg or p["card"], bd=0,
                 highlightthickness=1,
                 highlightbackground=p["card_border"],
                 highlightcolor=p["card_border"])
    return f


def section_card(parent, title=None, desc=None, pad=14, wrap=520):
    """标准「内容卡片」：白底 + 浅描边 + 可选标题行。

    返回 (卡片 Frame, 内容容器 Frame, 描述 Label 或 None)。

    描述 Label 单独返回，是因为主界面需要把它存成 self.hint_label
    （ui_smoke 会读它的 text / height）——比事后遍历控件树找它稳得多。

    这样统一封装，是为了避免每个页面各自手写 padx/pady 导致
    卡片留白不一致（实测很容易做出一块宽一块窄的观感）。
    """
    p = theme.p
    from ui_cozy import CozyFrame
    card = CozyFrame(parent, bg=p["card"], bd=0, highlightthickness=1,
                    highlightbackground=p["card_border"],
                    highlightcolor=p["card_border"])
    body = tk.Frame(card, bg=p["card"])
    desc_lab = None
    if title:
        head = tk.Frame(card, bg=p["card"])
        head.pack(fill="x", padx=pad, pady=(pad - 2, 0))
        tk.Label(head, text=title, bg=p["card"], fg=p["fg"],
                 font=theme.font(delta=1, bold=True), anchor="w").pack(side="left")
        if desc:
            desc_lab = tk.Label(card, text=desc, bg=p["card"], fg=p["fg_muted"],
                                font=theme.font(delta=-2), anchor="w",
                                justify="left", wraplength=wrap)
            desc_lab.pack(fill="x", padx=pad, pady=(1, 0))
        body.pack(fill="both", expand=True, padx=pad, pady=(6, pad))
    else:
        body.pack(fill="both", expand=True, padx=pad, pady=pad)
    return card, body, desc_lab


def make_gradient_image(width, height, c_top, c_bottom):
    """生成竖向渐变的 PhotoImage（用于页面背景）。

    必须持有返回对象的引用，否则会被 GC 回收导致画面空白 —— 调用方负责保存。
    """
    try:
        from PIL import Image, ImageDraw, ImageTk
    except Exception:
        return None
    try:
        w = max(1, int(width))
        h = max(1, int(height))
        img = Image.new("RGB", (1, h), c_top)
        dr = ImageDraw.Draw(img)
        for y in range(h):
            dr.point((0, y), fill=blend(c_top, c_bottom, y / float(h - 1 or 1)))
        img = img.resize((w, h), Image.BILINEAR)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


def make_circle_image(size, fill, outline=None, width=0, bg=None):
    """生成圆形图片（用于状态圆点、环形进度底座等）。bg 用于圆外区域的填充色。"""
    try:
        from PIL import Image, ImageDraw, ImageTk
    except Exception:
        return None
    try:
        s = max(2, int(size))
        base = bg or theme.p["card"]
        img = Image.new("RGBA", (s, s), base)
        dr = ImageDraw.Draw(img)
        pad = max(0, width // 2)
        dr.ellipse([pad, pad, s - 1 - pad, s - 1 - pad],
                   fill=fill, outline=outline, width=width)
        return ImageTk.PhotoImage(img.convert("RGB"))
    except Exception:
        return None
