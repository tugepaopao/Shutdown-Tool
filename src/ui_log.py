# -*- coding: utf-8 -*-
"""
执行日志窗口 —— 豪崽子の自动关机工具
文件作者：@wenhao

展示 run_log 里的记录：什么时候设定了什么、有没有执行成功。
"""
import tkinter as tk
from ui_window import prepare, show, button_grid, compact_show, wrap_to_width
import tkinter.font as tkfont
from tkinter import ttk, filedialog
from ui_localize import messagebox

from theme import flat_button, theme
from i18n import feature_text

# 事件类型 -> i18n key
KIND_KEYS = {
    "setup": "log_kind_setup",
    "done": "log_kind_done",
    "error": "log_kind_error",
    "cancel": "log_kind_cancel",
    "info": "log_kind_info",
}


class LogWindow(tk.Toplevel):
    """执行日志查看窗口：时间 / 事件 / 内容 / 详情。"""

    def __init__(self, app):
        tk.Toplevel.__init__(self, app.root)
        prepare(self)
        self.app = app
        self.T = app.T
        self.title(self.T("log_title"))
        self.configure(bg=theme.c("bg"))
        self.resizable(True, True)

        wrap_to_width(tk.Label(self, text=self.T("log_hint"), bg=theme.c("bg"),
                 fg=theme.c("fg_dim"), font=theme.font(delta=-1), anchor="w",
                 justify="left", wraplength=480)).pack(fill="x", padx=12,pady=(8,6))

        search=tk.Frame(self,bg=theme.c('bg'));search.pack(fill='x',padx=12,pady=(0,6))
        self.query=tk.StringVar();self.kind=tk.StringVar(value=feature_text(self.T,'全部'))
        self.start_date=tk.StringVar();self.end_date=tk.StringVar()
        self.search_row=search;self.search_entries=[]
        for index,(text,var,width) in enumerate([(feature_text(self.T,'搜索内容／详情'),self.query,20),(feature_text(self.T,'开始日期'),self.start_date,12),(feature_text(self.T,'结束日期'),self.end_date,12)]):
            row=0 if index==0 else 1;col=0 if index<2 else 2
            tk.Label(search,text=text,bg=theme.c('bg'),fg=theme.c('fg'),font=theme.font(delta=-1)).grid(row=row,column=col,sticky='w',padx=(0 if col==0 else 10,6),pady=4)
            entry=ttk.Entry(search,textvariable=var,width=width);entry.grid(row=row,column=col+1,columnspan=3 if index==0 else 1,sticky='ew');entry.bind('<Return>',lambda e:self.refresh())
            search.columnconfigure(col+1,weight=1);self.search_entries.append(entry)
        tk.Label(self,text=feature_text(self.T,'日期格式：YYYY-MM-DD'),bg=theme.c('bg'),fg=theme.c('fg_dim'),font=theme.font(delta=-2),anchor='w').pack(fill='x',padx=12,pady=(0,6))
        filters=tk.Frame(self,bg=theme.c('bg'));filters.pack(fill='x',padx=12,pady=(0,8))
        self.kind_values={feature_text(self.T,'全部'):''};self.kind_values.update({self.T(v):k for k,v in KIND_KEYS.items()})
        box=ttk.Combobox(filters,textvariable=self.kind,values=list(self.kind_values),state='readonly',width=12)
        box.pack(side='left');box.bind('<<ComboboxSelected>>',lambda e:self.refresh())
        flat_button(filters,feature_text(self.T,'搜索／筛选'),self.refresh,kind='accent',font=theme.font(delta=-1)).pack(side='left',padx=6)
        flat_button(filters,feature_text(self.T,'重置'),self._reset,kind='normal',font=theme.font(delta=-1)).pack(side='left')
        self.count_label=tk.Label(filters,bg=theme.c('bg'),fg=theme.c('fg_dim'),font=theme.font(delta=-1))
        self.count_label.pack(side='left',padx=8)
        wrap = tk.Frame(self, bg=theme.c("bg"))
        wrap.pack(fill="both", expand=True, padx=12)
        cols = ("time", "kind", "text", "detail")
        self.tv = ttk.Treeview(wrap, columns=cols, show="headings", height=14,
                               selectmode="browse")
        for col in cols:
            self.tv.heading(col, text=self.T("log_col_" + col), anchor="w")
        font = tkfont.Font(font=theme.font())
        self.tv.column("time", width=font.measure("2026-12-31 23:59:59") + 20, anchor="w", stretch=False)
        from ui_cozy import scale
        for col,width in (('kind',68),('text',170),('detail',130)):
            self.tv.column(col,width=round(width*scale(self)),minwidth=round(width*scale(self)),anchor='w',stretch=False)
        self.tv.grid(row=0,column=0,sticky='nsew');wrap.columnconfigure(0,weight=1);wrap.rowconfigure(0,weight=1)
        sb=ttk.Scrollbar(wrap,orient='vertical',command=self.tv.yview);sb.grid(row=0,column=1,sticky='ns')
        hs=ttk.Scrollbar(wrap,orient='horizontal',command=self.tv.xview);hs.grid(row=1,column=0,sticky='ew')
        self.tv.configure(yscrollcommand=sb.set,xscrollcommand=hs.set)
        # 双击某条记录时，把「详情」原样弹出来（长错误信息在表格里看不全）
        self.tv.bind("<Double-1>", self._show_detail)

        bar = tk.Frame(self, bg=theme.c("bg"))
        bar.pack(side="bottom", before=wrap, fill="x", padx=12, pady=(10, 12))
        button_grid(bar, [
            (self.T("log_clear"),self._clear,"normal"),
            (feature_text(self.T,'导出当前筛选CSV'),self._export,"normal"),
            (self.T("log_close"),self.destroy,"normal")])

        self.bind("<Escape>", lambda e: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.refresh()
        compact_show(self,app)
        self.focus_set()

    # ------------------------------------------------------------ 刷新
    def refresh(self):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        import run_log
        from task_store import filter_logs
        all_rows = run_log.entries(limit=run_log.MAX_ENTRIES)
        try:rows=filter_logs(all_rows,self.query.get(),self.kind_values.get(self.kind.get(),''),self.start_date.get().strip(),self.end_date.get().strip())
        except ValueError as exc:messagebox.showerror('筛选条件有误',str(exc),parent=self);return
        self.filtered_rows=rows
        self.count_label.config(text=f'{len(rows)} / {len(all_rows)}'+(' entries' if self.T.lang=='EN' else ' 條' if self.T.lang=='CHT' else ' 条'))
        for iid in self.tv.get_children():self.tv.delete(iid)
        for idx, rec in enumerate(rows):
            kind = KIND_KEYS.get(rec.get("kind"), "log_kind_info")
            self.tv.insert("", "end", iid=str(idx),
                           values=(rec.get("ts", ""), self.T(kind),
                                   rec.get("text", ""), rec.get("detail", "")))
        kids = self.tv.get_children()
        if kids:
            self.tv.see(kids[-1])          # 滚到最新一条

    def _show_detail(self, _e=None):
        """双击某条：把完整内容 + 详情一起弹出来（表格里长文本会被截断）。"""
        sel = self.tv.selection()
        if not sel:
            return
        vals = self.tv.item(sel[0], "values")
        if len(vals) < 4:
            return
        title, text, detail = vals[1], vals[2], vals[3]
        body = text if not detail else "%s\n\n%s" % (text, detail)
        if not body.strip():
            return
        from ui_localize import messagebox
        messagebox.showinfo(title or self.T("log_title"), body, parent=self)

    def _clear(self):
        import run_log
        run_log.clear()
        self.refresh()

    def _reset(self):
        self.query.set('');self.kind.set(feature_text(self.T,'全部'));self.start_date.set('');self.end_date.set('');self.refresh()

    def _export(self):
        from task_store import export_csv
        path=filedialog.asksaveasfilename(parent=self,defaultextension='.csv',initialfile='执行日志.csv',filetypes=[('CSV','*.csv')])
        if not path:return
        try:export_csv(path,self.filtered_rows);messagebox.showinfo('导出完成',f'已导出 {len(self.filtered_rows)} 条筛选结果。',parent=self)
        except OSError as exc:messagebox.showerror('导出失败',str(exc),parent=self)
