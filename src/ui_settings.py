# -*- coding: utf-8 -*-
"""
设置窗口：通用设置 / 显示界面设置 / 外观 / 其他设置
文件作者：@wenhao
"""
import tkinter as tk
from ui_pc_controls import ControlPanel
from ui_window import prepare, show, button_grid
import tkinter.font as tkfont
from tkinter import ttk
from i18n import Texts,feature_text
from ui_localize import messagebox

import autostart
from app_config import parse_hm
from i18n import AUTHOR, LANGUAGE_FILES, language_desc
from theme import palette_for, ACCENTS, ACCENT_ORDER, enable_button, flat_button, theme


def _group(parent, title):
    """带标题的分组框（v1.3.0 小清新版式）。

    旧版是 `bd=1 + relief="groove"` —— Windows 经典的凹陷立体边框；
    新版改成浅色描边 + 白底卡片，与主界面统一。
    仍然返回 LabelFrame，这样调用方 `pack` 的写法完全不用改。
    """
    p = theme.p
    return tk.LabelFrame(parent, text="   " + title + "   ", bg=p["bg"],
                         fg=p["fg"], font=theme.font(bold=True), bd=0,
                         relief="flat", labelanchor="nw", highlightthickness=1,
                         highlightbackground=p["card_border"],
                         highlightcolor=p["card_border"])


class SettingsWindow(tk.Toplevel):
    def __init__(self, app):
        tk.Toplevel.__init__(self, app.root)
        prepare(self)
        self.app = app
        self.T = app.T
        self.cfg = app.cfg
        self.dirty = False
        self.title(self.T("set_title"))
        self.configure(bg=theme.c("bg"))
        self.resizable(False, False)
        self.transient(app.root)

        self.v = {}
        self.accent_rings = {}
        self.apply_btn = None
        self._load_vars()

        body = tk.Frame(self, bg=theme.c("bg"))
        body.pack(fill="both", expand=True, padx=10, pady=10)

        # ---- 左侧导航
        nav_wrap = tk.Frame(body, bg=theme.c("bg"))
        nav_wrap.pack(side="left", fill="y")
        style = ttk.Style()
        try:
            style.configure("Nav.Treeview", font=theme.font(),
                            rowheight=tkfont.Font(font=theme.font()).metrics("linespace") + 8)
        except Exception:
            pass
        self.nav = ttk.Treeview(nav_wrap, show="tree", height=16,
                                style="Nav.Treeview", selectmode="browse")
        self.nav.pack(side="left", fill="y")
        nav_font=tkfont.Font(font=theme.font())
        labels=[Texts(lang)(key) for lang in ('CHS','CHT','EN') for key in ('set_general','set_display','set_appearance','set_other','set_tasks','set_backup')]
        labels += [Texts(lang)('pc_title') for lang in ('CHS','CHT','EN')]
        labels += [feature_text(Texts(lang),text) for lang in ('CHS','CHT','EN') for text in ('自动化与预览','快捷键与通知')]
        self.nav.column('#0',width=max(nav_font.measure(text) for text in labels)+38,stretch=False)
        pages = [("general", self.T("set_general")),
                 ("display", self.T("set_display")),
                 ("appearance", self.T("set_appearance")),
                 ("other", self.T("set_other")), ("tasks", self.T("set_tasks")), ("backup", self.T("set_backup"))]
        pages += [('pc',self.T('pc_title'))]
        pages += [('automation',feature_text(self.T,'自动化与预览')),('desktop',feature_text(self.T,'快捷键与通知'))]
        for key, label in pages:
            self.nav.insert("", "end", iid=key, text="  " + label)
        self.nav.bind("<<TreeviewSelect>>", self._on_nav)

        # ---- 右侧内容（v1.3.0：浅色描边取代原来硬朗的 solid 黑框）
        self.right = tk.Frame(body, bg=theme.c("bg"), bd=0, relief="flat",
                              highlightthickness=1,
                              highlightbackground=theme.c("card_border"),
                              highlightcolor=theme.c("card_border"))
        self.right.pack(side="left", fill="both", expand=True, padx=(10, 0))
        self.pages = {}
        self._build_general()
        self._build_display()
        self._build_appearance()
        self._build_other()
        self._build_tasks()
        self._build_backup()
        self._build_automation()
        self._build_desktop()
        self.pc_panel = ControlPanel(self._page("pc", self.T("pc_title")), self)
        self._current = None
        self._show("general")

        # ---- 底部按钮
        bar = tk.Frame(self, bg=theme.c("bg"))
        bar.pack(fill="x", padx=10, pady=(0, 10))
        buttons = button_grid(bar, [
            (self.T("btn_apply"), self.on_apply, "normal"),
            (self.T("btn_cancel"), self.destroy, "normal"),
            (self.T("btn_ok"), self.on_ok, "accent")])
        self.apply_btn = buttons[0]
        self._set_apply_enabled(False)

        self.bind("<Escape>", lambda e: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.update_idletasks()
        self.geometry("+%d+%d" % (app.root.winfo_rootx() + 40, app.root.winfo_rooty() + 40))
        show(self);self.grab_set()
        self.focus_set()

    # ------------------------------------------------------------ 变量初始化
    def _load_vars(self):
        c = self.cfg
        for key in ("confirm_before_action", "confirm_key_only",
                    "confirm_on_exit", "confirm_on_exit_only_timer",
                    "force_close_apps", "sound_at_10s",
                    "esc_to_minimize", "minimize_to_tray", "popup_at_10s",
                    "autostart",
                    # v1.2.0 新增的三个开关
                    "cancel_at_10s", "log_enabled", "resume_timer", "hotkeys_enabled", "notifications_enabled", "notify_setup", "notify_done", "notify_error"):
            self.v[key] = tk.BooleanVar(value=bool(c.get(key)))
        # v1.2.0：消息提示框停留时长（秒）。用字符串变量装，收的时候再转成 int
        try:
            _toast = int(c.get("toast_seconds", 15))
        except Exception:
            _toast = 15
        self.v["toast_seconds"] = tk.StringVar(value=str(max(3, min(600, _toast))))
        self.v["language"] = tk.StringVar(value=str(c.get("language", "CHS")))
        self.v["accent"] = tk.StringVar(value=str(c.get("accent", "blue")))
        # v1.3.1：快捷预设最后两个按钮的时间（文本 "H:MM"，解析见 app_config.parse_hm）
        for key, dflt in (("quick_at_today", "22:00"),
                          ("quick_at_tomorrow", "08:00")):
            self.v[key] = tk.StringVar(value=str(c.get(key, dflt)))
        self.v["quick_at_today"].set("22:00")
        self.v['quick_day_offset']=tk.IntVar(value=int(c.get('quick_day_offset',1)))
        for key in ('hotkey_show','hotkey_pause','hotkey_resume'):self.v[key]=tk.StringVar(value=c.get(key))
        for var in self.v.values():
            var.trace_add("write", self._mark_dirty)

    def _set_apply_enabled(self, enabled):
        enable_button(self.apply_btn, enabled)

    def _mark_dirty(self, *_a):
        self.dirty = True
        if getattr(self, "apply_btn", None) is not None:
            enable_button(self.apply_btn, True)

    # ------------------------------------------------------------ 页面构建
    def _page(self, key, title):
        f = tk.Frame(self.right, bg=theme.c("bg"))
        self.pages[key] = f
        head = tk.Label(f, text=title, bg=theme.accent, fg=theme.c("accent_fg"),
                        font=theme.font(delta=3, bold=True), anchor="w")
        head.pack(fill="x", ipady=6, padx=1, pady=1)
        wrap=tk.Frame(f,bg=theme.c('bg'));wrap.pack(fill='both',expand=True)
        canvas=tk.Canvas(wrap,bg=theme.c('bg'),highlightthickness=0,width=470,height=min(520,self.winfo_screenheight()-180))
        canvas.pack(side='left',fill='both',expand=True)
        gutter=tk.Frame(wrap,bg=theme.c('bg'),width=12,height=1);gutter.pack(side='right',fill='y');gutter.pack_propagate(False)
        scroll=ttk.Scrollbar(gutter,command=canvas.yview);scroll.pack(side='right',fill='y');canvas.config(yscrollcommand=scroll.set)
        gutter.configure(width=scroll.winfo_reqwidth())
        # Reserve a stable page viewport; hiding an unused scrollbar must not
        # resize the settings dialog when moving between pages.
        wrap.configure(width=470+scroll.winfo_reqwidth(),height=min(520,self.winfo_screenheight()-180));wrap.pack_propagate(False)
        pad=tk.Frame(canvas,bg=theme.c('bg'));item=canvas.create_window(0,0,window=pad,anchor='nw')
        self._scroll_pages=getattr(self,'_scroll_pages',{})
        self._scroll_pages[key]=(canvas,pad,scroll,item)
        def layout(e=None):
            from ui_localize import walk
            for widget in walk(pad):
                if isinstance(widget,tk.Label) and int(float(str(widget.cget('wraplength'))))>0 and not getattr(widget,'_wrap_bound',False):
                    widget._wrap_bound=True
                    def fit(event,w=widget):
                        width=max(50,event.width-4)
                        if abs(int(float(str(w.cget('wraplength'))))-width)>1:w.configure(wraplength=width)
                    widget.bind('<Configure>',fit,add='+')
            height=max(1,canvas.winfo_height());content=pad.winfo_reqheight()
            canvas.configure(scrollregion=(0,0,max(1,canvas.winfo_width()),max(height,content)))
            if content<=height:
                canvas.yview_moveto(0)
                if scroll.winfo_manager():scroll.pack_forget()
            elif not scroll.winfo_manager():scroll.pack(side='right',fill='y')
        def resize(e):
            canvas.itemconfigure(item,width=e.width);layout()
        pad.bind('<Configure>',layout)
        canvas.bind('<Configure>',resize)
        def wheel(e):
            if self._current==key and e.widget.winfo_class() not in ('TSpinbox','TCombobox') and pad.winfo_reqheight()>canvas.winfo_height():
                canvas.yview_scroll(-int(e.delta/120),'units')
        self.bind('<MouseWheel>',wheel,add='+')
        return pad

    def _build_general(self):
        T = self.T
        pad = self._page("general", T("set_general"))

        g1 = _group(pad, T("set_msghint_group"))
        g1.pack(fill="x")
        self._check(g1, "confirm_before_action", T("set_confirm_before"), indent=10)
        self._check(g1, "confirm_key_only", T("set_confirm_key"), indent=34,
                    dep="confirm_before_action")
        self._check(g1, "confirm_on_exit", T("set_confirm_on_exit"), indent=10)
        self._check(g1, "confirm_on_exit_only_timer", T("set_confirm_exit_timer"), indent=34,
                    dep="confirm_on_exit")

        g2 = _group(pad, T("set_force_group"))
        g2.pack(fill="x", pady=(12, 0))
        self._check(g2, "force_close_apps", T("set_force_close"), indent=10, wraplength=430)

        g3 = _group(pad, T("set_sound_group"))
        g3.pack(fill="x", pady=(12, 0))
        self._check(g3, "sound_at_10s", T("set_sound_10s"), indent=10)

        # ---- 消息提示框（v1.2.0）：停留时长可配，以前是写死的 15 秒
        g4 = _group(pad, T("set_notify_group"))
        g4.pack(fill="x", pady=(12, 0))
        trow = tk.Frame(g4, bg=theme.c("bg"))
        trow.pack(fill="x", padx=10, pady=(2, 2))
        tk.Label(trow, text=T("set_toast_seconds"), bg=theme.c("bg"),
                 fg=theme.c("fg"), font=theme.font(), anchor="w").pack(side="left")
        ttk.Spinbox(trow, from_=3, to=600, width=6, justify="center",
                    textvariable=self.v["toast_seconds"]).pack(side="left", padx=(8, 0))
        tk.Label(g4, text=T("set_toast_tip"), bg=theme.c("bg"), fg=theme.c("fg_muted"),
                 font=theme.font(delta=-1), anchor="w").pack(fill="x", padx=10,
                                                             pady=(0, 6))

    def _build_display(self):
        T = self.T
        pad = self._page("display", T("set_display"))

        g1 = _group(pad, T("set_exit_group"))
        g1.pack(fill="x")
        self._check(g1, "esc_to_minimize", T("set_esc"), indent=10)
        self._check(g1, "minimize_to_tray", T("set_tray"), indent=10)

        # 说明（v1.1.2）：原「在界面下方的进度条中显示内容」分组已移除——
        # 进度条改成整行铺满、右侧不再有文字位，剩余时间统一由状态栏显示。
        g3 = _group(pad, T("set_lang_group"))
        g3.pack(fill="x", pady=(12, 0))
        tk.Label(g3, text=T("set_lang_file"), bg=theme.c("bg"), fg=theme.c("fg"),
                 font=theme.font(), anchor="w").pack(fill="x", padx=10, pady=(4, 2))
        wrap = tk.Frame(g3, bg=theme.c("bg"))
        wrap.pack(fill="x", padx=10, pady=(0, 4))
        cols = ("desc", "file", "author")
        tv = ttk.Treeview(wrap, columns=cols, show="headings", height=3, selectmode="browse")
        tv.heading("desc", anchor="w", text=T("set_lang_desc"))
        tv.heading("file", anchor="w", text=T("set_lang_name"))
        tv.heading("author", anchor="w", text=T("set_lang_author"))
        tv.column("desc", width=150, minwidth=80, stretch=False, anchor="w")
        tv.column("file", width=110, minwidth=80, stretch=False, anchor="w")
        tv.column("author", width=110, minwidth=80, stretch=False, anchor="w")
        tv.pack(side="left", fill="x", expand=True)
        def fit_columns(_e=None):
            width=max(3,tv.winfo_width()-4)
            first=round(width*.40);second=round(width*.30)
            for col,size in zip(cols,(first,second,width-first-second)):
                tv.column(col,width=size,stretch=False)
        def fixed_columns(event):
            if tv.identify_region(event.x,event.y)=='separator':return 'break'
        tv.bind('<Configure>',fit_columns)
        for sequence in ('<Button-1>','<B1-Motion>','<ButtonRelease-1>'):
            tv.bind(sequence,fixed_columns)
        for item in LANGUAGE_FILES:
            tv.insert("", "end", iid=item["code"],
                      values=(language_desc(item["code"], self.cfg.get("language")),
                              item["file"], AUTHOR))
        tv.selection_set(self.v["language"].get())
        self.lang_tree = tv

        def _on_lang(_e=None):
            sel = tv.selection()
            if sel:
                self.v["language"].set(sel[0])

        tv.bind("<<TreeviewSelect>>", _on_lang)
        tk.Label(g3, text=T("set_lang_tip"), bg=theme.c("bg"), fg=theme.c("fg_muted"),
                 font=theme.font(delta=-1), anchor="w").pack(fill="x", padx=10, pady=(0, 6))

    def _build_appearance(self):
        T=self.T
        pad=self._page('appearance',T('set_appearance'))
        group=_group(pad,T('set_accent_group'));group.pack(fill='x')
        tk.Label(group,text=T('appearance_choose'),bg=theme.c('bg'),fg=theme.c('fg_dim'),font=theme.font(delta=-1),anchor='w',wraplength=380,justify='left').pack(fill='x',padx=10,pady=(4,4))
        grid=tk.Frame(group,bg=theme.c('bg'));grid.pack(fill='x',padx=8,pady=(0,6))
        self.accent_names={}
        for col in range(4):grid.columnconfigure(col,weight=1,uniform='colors')
        for idx,key in enumerate(ACCENT_ORDER):
            cell=tk.Frame(grid,bg=theme.c('bg'));cell.grid(row=idx//4,column=idx%4,sticky='ew',padx=4,pady=4)
            ring=tk.Frame(cell,bg=theme.c('border'));ring.pack(fill='x')
            sw=tk.Frame(ring,bg=ACCENTS[key],height=24,cursor='hand2');sw.pack(fill='x',padx=2,pady=2)
            ring._theme_fixed=sw._theme_fixed=True
            sw.bind('<Button-1>',lambda e,k=key:self._pick_accent(k))
            name=tk.Label(cell,text=T('accent_'+key),bg=theme.c('bg'),fg=theme.c('fg_dim'),font=theme.font(delta=-1),width=9,cursor='hand2');name.pack(fill='x')
            name.bind('<Button-1>',lambda e,k=key:self._pick_accent(k));self.accent_names[key]=name;self.accent_rings[key]=ring
        preview=_group(pad,T('appearance_preview'));preview.pack(fill='x',pady=(10,0))
        self.preview_box=tk.Frame(preview,highlightthickness=1);self.preview_box.pack(fill='x',padx=10,pady=8)
        self.preview_title=tk.Label(self.preview_box,font=theme.font(bold=True),anchor='w');self.preview_title.pack(fill='x',padx=10,pady=(8,6))
        line=tk.Frame(self.preview_box);line.pack(fill='x',padx=8,pady=(0,8));line.columnconfigure(0,weight=1,uniform='preview');line.columnconfigure(1,weight=1,uniform='preview')
        self.preview_card=tk.Label(line,text=T('appearance_card'),font=theme.font(delta=-1),pady=8,highlightthickness=1);self.preview_card.grid(row=0,column=0,sticky='ew',padx=2)
        self.preview_action=tk.Label(line,text=T('appearance_selected'),font=theme.font(delta=-1),pady=8,highlightthickness=1);self.preview_action.grid(row=0,column=1,sticky='ew',padx=2)
        self.preview_bar=tk.Frame(self.preview_box,height=4);self.preview_bar.pack(fill='x',padx=10,pady=(0,8))
        from ui_transition import walk
        for widget in walk(self.preview_box):widget._theme_fixed=True
        note=_group(pad,T('appearance_about'));note.pack(fill='x',pady=(10,0))
        tk.Label(note,text=T('appearance_note'),bg=theme.c('bg'),fg=theme.c('fg_dim'),font=theme.font(delta=-1),justify='left',anchor='w',wraplength=380).pack(fill='x',padx=10,pady=(4,8))
        self._refresh_accent_rings()

    def _pick_accent(self,key):
        self.v['accent'].set(key);self._refresh_accent_rings()

    def _refresh_accent_rings(self):
        cur=self.v['accent'].get()
        for key,ring in self.accent_rings.items():
            ring.config(bg=ACCENTS[key] if key==cur else theme.c('border'))
            self.accent_names[key].config(text=self.T('accent_'+key)+(' ✓' if key==cur else ''))
        if hasattr(self,'preview_box'):
            p=palette_for(cur);accent=ACCENTS[cur]
            self.preview_box.config(bg=p['bg'],highlightbackground=p['card_border'])
            for w in self.preview_box.winfo_children():w.config(bg=p['bg'])
            self.preview_title.config(text=self.T('appearance_preview_name',name=self.T('accent_'+cur)),fg=accent,bg=p['bg'])
            self.preview_card.config(bg=p['card'],fg=p['fg'],highlightbackground=p['card_border'])
            self.preview_action.config(bg=p['sel_row_bg'],fg=p['sel_row_fg'],highlightbackground=accent)
            self.preview_bar.config(bg=accent)

    def _build_other(self):
        T = self.T
        pad = self._page("other", T("set_other"))

        # ---- v1.3.1：快捷预设自定义（放在最上面，是这一页最常用的设置）
        g0 = _group(pad, T("set_quick_group"))
        g0.pack(fill="x")
        tk.Label(g0, text=T("set_quick_tip"), bg=theme.c("bg"), fg=theme.c("fg_dim"),
                 font=theme.font(delta=-1), anchor="w", justify="left",
                 wraplength=430).pack(fill="x", padx=10, pady=(4, 6))
        row=tk.Frame(g0,bg=theme.c('bg'));row.pack(fill='x',padx=10,pady=4)
        tk.Label(row,text=feature_text(T,'第6个按钮的日期'),bg=theme.c('bg'),fg=theme.c('fg'),font=theme.font()).pack(side='left')
        self.day_box=ttk.Combobox(row,state='readonly',values=[feature_text(T,t) for t in ('今天','明天','后天','3天后','4天后','5天后','6天后','7天后')],width=10,justify='center')
        self.day_box.current(self.v['quick_day_offset'].get());self.day_box.pack(side='left',padx=10)
        self.day_box.bind('<<ComboboxSelected>>',lambda e:self.v['quick_day_offset'].set(self.day_box.current()))
        self._hm_row(g0, "quick_at_tomorrow", T("set_quick_p5"), "08:00")
        tk.Label(g0, text=T("set_quick_note"), bg=theme.c("bg"), fg=theme.c("fg_muted"),
                 font=theme.font(delta=-1), anchor="w", justify="left",
                 wraplength=430).pack(fill="x", padx=10, pady=(4, 2))
        flat_button(g0, T("set_quick_reset"), self._reset_quick_presets,
                    kind="plain", pady=3, padx=10,
                    font=theme.font(delta=-1)).pack(anchor="w", padx=10, pady=(2, 8))

        g1 = _group(pad, T("set_tip_group"))
        g1.pack(fill="x", pady=(12, 0))
        self._check(g1, "popup_at_10s", T("set_popup_10s"), indent=10, wraplength=430)
        # v1.2.0：到点前 10 秒弹「可取消」提示框
        self._check(g1, "cancel_at_10s", T("set_cancel_10s"), indent=10, wraplength=430)

        # v1.2.0：执行日志
        g2 = _group(pad, T("set_log_group"))
        g2.pack(fill="x", pady=(12, 0))
        self._check(g2, "log_enabled", T("set_log_enabled"), indent=10, wraplength=430)

        # v1.2.0：定时器状态持久化
        g3 = _group(pad, T("set_resume_group"))
        g3.pack(fill="x", pady=(12, 0))
        self._check(g3, "resume_timer", T("set_resume_timer"), indent=10, wraplength=430)

        g4 = _group(pad, T("set_autostart_group"))
        g4.pack(fill="x", pady=(12, 0))
        self._check(g4, "autostart", T("set_autostart"), indent=10, wraplength=430)

    def _build_tasks(self):
        from ui_tasks import button, label
        pad = self._page('tasks', self.T('set_tasks'))
        tk.Label(pad,text=self.T('center_hint'),bg=theme.c('bg'),fg=theme.c('fg'),
                 font=theme.font(),justify='left',anchor='w',wraplength=420).pack(fill='x',padx=10,pady=10)
        flat_button(pad,self.T('center_open'),lambda:self.app.open_task_center(parent=self),kind='accent').pack(fill='x',padx=10,pady=(0,10))
        guide=_group(pad,self.T('mode_guide'));guide.pack(fill='x',padx=10,pady=8)
        for key in ('mode_guide_countdown','mode_guide_weekday','mode_guide_interval','mode_guide_calendar'):
            tk.Label(guide,text=self.T(key),bg=theme.c('bg'),fg=theme.c('fg'),font=theme.font(),
                     anchor='w',justify='left',wraplength=400).pack(fill='x',padx=10,pady=5)
        label(pad, '延后当前正在计时的任务：').pack(fill='x', pady=(15,4))
        row = tk.Frame(pad, bg=theme.c('bg'));row.pack(fill='x')
        self.postpone_buttons=[]
        for col,minutes in enumerate((5,10,30)):
            row.columnconfigure(col*2,weight=1,uniform='postpone')
            if col<2:row.columnconfigure(col*2+1,minsize=8)
            b=button(row,f'延后{minutes}分钟',lambda m=minutes:self._postpone(m))
            b.grid(row=0,column=col*2,sticky='ew');self.postpone_buttons.append(b)
        label(pad, '高级任务保存后默认停用；启用后才开始等待。\n工作日按周一至周五计算，不包含法定节假日调整。', wraplength=420, justify='left', font=theme.font(delta=-1)).pack(fill='x', pady=15)

    def _postpone(self, minutes):
        if not self.app.postpone(minutes):
            from tkinter import messagebox
            messagebox.showinfo('没有运行中的定时', '请先开始一个定时任务。', parent=self)

    def _build_backup(self):
        from ui_tasks import button, label, backup_export, backup_import
        from i18n import feature_text
        pad = self._page('backup', feature_text(self.T,'设置与任务模板备份'))
        label(pad, '导出设置、模板和高级任务为JSON文件。\n导入前会显示预览；导入的高级任务全部停用。\n运行中定时、当前队列、自启动项不被替换。', wraplength=420, justify='left').pack(fill='x', pady=12)
        button(pad, '导出设置与模板', lambda:backup_export(self.app,self)).pack(fill='x', pady=8)
        button(pad, '导入设置与模板', lambda:backup_import(self.app,self)).pack(fill='x', pady=8)
        from ui_extras import RecoveryWindow
        g=_group(pad,feature_text(self.T,'备份与恢复'));g.pack(fill='x',padx=10,pady=12)
        label(g,'自动保留最近10份正常配置\n计时状态变化不会反复生成备份',wraplength=390,justify='left',anchor='w').pack(fill='x',padx=10,pady=8)
        label(g,'配置损坏时自动尝试恢复；手动恢复前会显示预览。',wraplength=420,justify='left',font=theme.font(delta=-1)).pack(fill='x',padx=10,pady=6)
        button(g,'查看自动备份',lambda:RecoveryWindow(self.app,self)).pack(fill='x',padx=10,pady=8)
        scope=_group(pad,feature_text(self.T,'备份范围'));scope.pack(fill='x',padx=10,pady=(0,8))
        label(scope,'包含：常用设置、命名模板、高级任务定义',anchor='w',wraplength=390,justify='left',font=theme.font(delta=-1)).pack(fill='x',padx=10,pady=(6,4))
        label(scope,'不包含：运行中的定时、队列、自启动项',anchor='w',wraplength=390,justify='left',font=theme.font(delta=-1)).pack(fill='x',padx=10,pady=(0,6))


    def _build_automation(self):
        from ui_tasks import label,button
        from ui_extras import PreviewWindow
        pad=self._page('automation',feature_text(self.T,'自动化与预览'))
        self.automation_notes=[]
        for title,note,command in [
            ('管理预约、条件与任务链','先观察到网络活动\n再同时满足网络安静与无人操作时长',lambda:self.app.open_advanced(self)),
            ('未来7天任务预览','只显示已启用的预约，含今天共7天\n工作日按周一至周五计算，不调整节假日',lambda:PreviewWindow(self.app,self))]:
            group=_group(pad,feature_text(self.T,title));group.pack(fill='x',padx=10,pady=(8,4))
            note_label=label(group,note,wraplength=420,justify='left',anchor='w')
            note_label.pack(fill='x',padx=10,pady=(6,8));self.automation_notes.append(note_label)
            button(group,title,command).pack(fill='x',padx=10,pady=(0,8))
        guide=_group(pad,feature_text(self.T,'任务链使用说明'));guide.pack(fill='x',padx=10,pady=(8,10))
        for text in ('成功后执行：前置程序退出码为0才继续',
                     '超时或取消：不关闭正在运行的前置程序',
                     '重新打开工具：任务链需手动重新启用'):
            note_label=label(guide,text,wraplength=420,justify='left',anchor='w')
            note_label.pack(fill='x',padx=10,pady=5);self.automation_notes.append(note_label)


    def _build_desktop(self):
        from ui_tasks import label,button
        pad=self._page('desktop',feature_text(self.T,'快捷键与通知'))
        hot=_group(pad,feature_text(self.T,'全局快捷键'));hot.pack(fill='x',padx=10,pady=8)
        self._check(hot,'hotkeys_enabled',feature_text(self.T,'启用全局快捷键'))
        for key,text in [('show','唤出主窗口'),('pause','暂停当前定时'),('resume','继续当前定时')]:
            row=tk.Frame(hot,bg=theme.c('bg'));row.pack(fill='x',padx=10,pady=4)
            label(row,text,anchor='w',wraplength=170).pack(side='left',fill='x',expand=True)
            ttk.Entry(row,textvariable=self.v['hotkey_'+key],width=18).pack(side='right')
        label(hot,'支持Ctrl、Alt、Shift加字母／数字／F1～F12；快捷键冲突会提示，不会覆盖其他程序。',wraplength=420,justify='left',font=theme.font(delta=-1)).pack(fill='x',padx=10,pady=8)
        note=_group(pad,feature_text(self.T,'Windows桌面通知'));note.pack(fill='x',padx=10,pady=8)
        for key,text in [('notifications_enabled','启用桌面通知'),('notify_setup','任务已设置'),('notify_done','任务已完成'),('notify_error','任务失败')]:self._check(note,key,feature_text(self.T,text),indent=10 if key=='notifications_enabled' else 28)
        label(note,'通知跟随Windows通知设置；专注助手或系统禁用通知时可能不弹出。',wraplength=420,justify='left',font=theme.font(delta=-1)).pack(fill='x',padx=10,pady=8)
        button(note,'发送测试通知',self._test_notification).pack(fill='x',padx=10,pady=(0,8))

    def _test_notification(self):
        ok=self.app.desktop.notify('setup',feature_text(self.T,'这是一条测试通知。'),force=True)
        messagebox.showinfo('提示','通知已提交给Windows' if ok else '托盘不可用，无法发送通知',parent=self)

    def _undo(self):
        try:self.app.undo.undo();messagebox.showinfo('已撤销删除','恢复的任务不会自动开始。',parent=self)
        except (ValueError,OSError) as exc:messagebox.showinfo('操作未完成',str(exc),parent=self)

    def sync_vars(self):
        for key,var in self.v.items():var.set(self.cfg.get(key))
        self.day_box.current(self.v['quick_day_offset'].get());self.lang_tree.selection_set(self.v['language'].get())
        self.dirty=False;self._set_apply_enabled(False);self._refresh_accent_rings()

    def _hm_row(self, parent, key, label, default):
        """一行「标签 + 时:分 输入框」（v1.3.1 快捷预设自定义用）。

        用单个文本框装 "22:00" 而不是两个 Spinbox：用户就是要"自己设时间"，
        一个框直接敲 22:30 最直接，也省下一半横向空间（设置窗口是固定宽度）。
        校验交给 app_config.parse_hm（存的是原文，非法值在执行时回落默认）。
        """
        row = tk.Frame(parent, bg=theme.c("bg"))
        row.pack(fill="x", padx=10, pady=(0, 2))
        tk.Label(row, text=label, bg=theme.c("bg"), fg=theme.c("fg"),
                 font=theme.font(), anchor="w").pack(side="left")
        ent = tk.Entry(row, textvariable=self.v[key], width=8, justify="center",
                       bg=theme.c("input_bg"), fg=theme.c("input_fg"),
                       font=theme.font(), bd=0, relief="flat",
                       highlightthickness=1,
                       highlightbackground=theme.c("card_border"),
                       highlightcolor=theme.accent,
                       insertbackground=theme.c("fg"))
        ent.pack(side="left", padx=(10, 0), ipady=3)
        tk.Label(row, text=feature_text(self.T,"(时:分)"), bg=theme.c("bg"), fg=theme.c("fg_muted"),
                 font=theme.font(delta=-1), anchor="w").pack(side="left", padx=(6, 0))
        self._quick_defaults = getattr(self, "_quick_defaults", {})
        self._quick_defaults[key] = default
        return ent

    def _reset_quick_presets(self):
        """把两个自定义预设恢复成默认值（并标记为「已改动」以便点应用）。"""
        self.v["quick_day_offset"].set(1);self.day_box.current(1)
        for key, val in getattr(self, "_quick_defaults", {}).items():
            try:
                self.v[key].set(val)
            except Exception:
                pass

    def _check(self, parent, key, text, indent=10, dep=None, wraplength=0):
        cb = tk.Checkbutton(parent, text=text, variable=self.v[key], bg=theme.c("bg"),
                            fg=theme.c("fg"), font=theme.font(), anchor="w",
                            justify="left", activebackground=theme.c("bg"),
                            activeforeground=theme.c("accent"),
                            selectcolor=theme.c("bg"), bd=0, highlightthickness=0)
        cb.pack(fill="x", padx=indent, anchor="w")
        cb.config(wraplength=wraplength or 420)
        if dep:
            def sync(*_a):
                state = "normal" if self.v[dep].get() else "disabled"
                cb.config(state=state)
                try:
                    cb.config(fg=theme.c("fg") if state == "normal" else theme.c("disabled"))
                except Exception:
                    pass
            self.v[dep].trace_add("write", sync)
            sync()
        return cb

    # ------------------------------------------------------------ 交互
    def _on_nav(self, _e=None):
        sel = self.nav.selection()
        if sel:
            self._show(sel[0])

    def _show(self, key):
        if self._current == key:
            return
        for k, frame in self.pages.items():
            if k == key:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()
        self._current = key
        if hasattr(self,'_scroll_pages'):
            canvas,pad,scroll,item=self._scroll_pages[key];canvas.yview_moveto(0)
        if key == "pc": self.pc_panel.refresh()
        if self.nav.selection() != (key,):
            self.nav.selection_set(key)

    def _collect(self):
        for key, var in self.v.items():
            self.cfg[key] = var.get()
        # v1.2.0：停留时长必须是 3~600 的整数；输入的乱七八糟就回落到默认 15
        try:
            secs = int(float(str(self.v["toast_seconds"].get()).strip()))
        except Exception:
            secs = 15
        self.cfg["toast_seconds"] = max(3, min(600, secs))
        self.v["toast_seconds"].set(str(self.cfg["toast_seconds"]))
        # v1.3.1：两个自定义预设规范成 "HH:MM" 存盘。
        # 解析失败（空、乱填、超范围）就回落到默认值 —— 并且**立刻回写输入框**，
        # 让用户当场看见自己填的值没被采纳（静默丢弃是最招人烦的）。
        for key, (dh, dm) in (("quick_at_today", (22, 0)),
                              ("quick_at_tomorrow", (8, 0))):
            h, m = parse_hm(self.v[key].get(), dh, dm)
            self.cfg[key] = "%02d:%02d" % (h, m)
            self.v[key].set(self.cfg[key])
        self.cfg["quick_at_today"] = "22:00"
        self.cfg["autostart"] = bool(self.v["autostart"].get())

    def on_apply(self, close=False):
        import copy
        previous=copy.deepcopy(self.cfg.data)
        try:
            self._collect()
            self.app.desktop.apply()
            if not self.cfg.save():raise OSError('配置保存失败，原设置已保留。')
        except (ValueError,OSError) as exc:
            self.cfg.data=previous
            try:self.app.desktop.apply()
            except Exception:pass
            messagebox.showerror('操作未完成',str(exc),parent=self);return
        autostart.set_enabled(bool(self.cfg.get('autostart')))
        self.app.apply_settings();self.pc_panel.retheme();self.dirty=False
        if self.cfg.backup_error:messagebox.showwarning(self.T('tip_title'),feature_text(self.T,'设置已保存，但自动备份失败：')+self.cfg.backup_error,parent=self)
        if close:self.destroy();return
        self._set_apply_enabled(False)

    def on_ok(self):
        self.on_apply(close=True)
