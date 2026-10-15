# -*- coding: utf-8 -*-
"""
定时任务队列窗口 —— 豪崽子の自动关机工具
文件作者：@wenhao

主界面那套时间设置一次只能表达一个定时；这里把多个定时排成队列，
前一个跑完自动接上下一个（见 ui_main 里的 _start_next_task / _handle("finished")）。
"""
import tkinter as tk
from ui_window import prepare, show, button_grid
from tkinter import ttk
from ui_localize import messagebox

from theme import flat_button, theme
from i18n import feature_text


class QueueView:
    """管理「排队等待执行」的定时任务。"""

    def _init_view(self, app, parent=None, embedded=False):
        self.embedded = embedded
        if embedded: tk.Frame.__init__(self, parent, bg=theme.c('bg'))
        else: tk.Toplevel.__init__(self, app.root); prepare(self)
        self.owner = self.winfo_toplevel()
        self.app = app
        self.T = app.T
        if not embedded: self.title(self.T("queue_title"))
        self.configure(bg=theme.c("bg"))
        if not embedded:
            self.resizable(False, False)
            self.transient(app.root)

        if embedded:
            from ui_queue_cards import QueueCards
            self.cards=QueueCards(self);return

        head = tk.Frame(self, bg=theme.c("header_bg"))
        if not embedded: head.pack(fill="x")
        tk.Label(head, text=self.T("queue_title"), bg=theme.c("header_bg"),
                 fg=theme.c("fg"), font=theme.font(delta=2, bold=True),
                 anchor="w").pack(side="left", padx=12, pady=8)

        tk.Label(self, text=self.T("queue_hint"), bg=theme.c("bg"),
                 fg=theme.c("fg_dim"), font=theme.font(delta=-1), anchor="w",
                 justify="left", wraplength=430).pack(fill="x", padx=12,
                                                      pady=(8, 6))

        wrap = tk.Frame(self, bg=theme.c("bg"))
        wrap.pack(fill="both", expand=True, padx=12)
        cols = ("when", "action", "note")
        self.tv = ttk.Treeview(wrap, columns=cols, show="headings", height=7,
                               selectmode="extended")
        for col in cols:
            self.tv.heading(col, text=self.T("queue_col_" + col), anchor="w")
        self.tv.column("when", width=150, anchor="w")
        self.tv.column("action", width=130, anchor="w")
        self.tv.column("note", width=150, anchor="w")
        self.tv.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.tv.yview)
        sb.pack(side="right", fill="y")
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.bind('<Double-1>',lambda e:self._edit())

        editbar=tk.Frame(self,bg=theme.c('bg'));editbar.pack(fill='x',padx=12,pady=(8,0))
        button_grid(editbar, [(feature_text(self.T,text),command,'normal') for text,command in
            [('编辑',self._edit),('复制',self._copy),('上移',lambda:self._move(-1)),('下移',lambda:self._move(1)),('保存为模板',self._template)]])
        tk.Label(self,text=feature_text(self.T,'运行中任务先停止再编辑或排序'),bg=theme.c('bg'),fg=theme.c('fg_dim'),font=theme.font(delta=-2),anchor='w').pack(fill='x',padx=12,pady=(6,0))
        bar = tk.Frame(self, bg=theme.c("bg"))
        bar.pack(fill="x", padx=12, pady=(8,12))
        button_grid(bar, [
            (self.T("queue_add_now"),self._add,"accent"),
            (self.T("queue_remove"),self._remove,"normal"),
            (self.T("queue_clear"),self._clear,"normal"),
            *([] if embedded else [(self.T("queue_close"),self.destroy,"normal")])], columns=3 if embedded else 2)

        undo_bar=tk.Frame(self,bg=theme.c('bg'));undo_bar.pack(fill='x',padx=12,pady=(0,12))
        button_grid(undo_bar,[(feature_text(self.T,'撤销上一次删除'),self._undo,'normal')])
        self.refresh()
        if not embedded:
            self.bind("<Escape>", lambda e: self.destroy())
            self.protocol("WM_DELETE_WINDOW", self.destroy)
            self.update_idletasks()
            self.geometry("+%d+%d" % (app.root.winfo_rootx()+40, app.root.winfo_rooty()+60))
            show(self); self.grab_set(); self.focus_set()

    # ------------------------------------------------------------ 刷新
    def refresh(self):
        """重画表格（外部增删队列后由 App 调用）。"""
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        if hasattr(self,'cards'):self.cards.refresh();return
        keep = set(self.tv.selection())
        for iid in self.tv.get_children():
            self.tv.delete(iid)
        try:
            tasks = self.app.get_queue()
        except Exception:
            tasks = []
        for task in tasks:
            iid = str(task.get("id"))
            self.tv.insert("", "end", iid=iid,
                           values=(self.app.describe_when(task),
                                   self.app.describe_action(task),
                                   self.app.describe_note(task)))
        for iid in keep:
            try:
                if self.tv.exists(iid):
                    self.tv.selection_add(iid)
            except Exception:
                pass

    # ------------------------------------------------------------ 操作
    def _add(self):
        self.app.add_current_to_queue()

    def _remove(self):
        ids = []
        for i in self.tv.selection():
            try:
                ids.append(int(i))
            except Exception:
                pass
        if ids:
            try:self.app.remove_queue_tasks(ids)
            except OSError as exc:messagebox.showerror('操作未完成',str(exc),parent=self)

    def _clear(self):
        try:self.app.clear_queue()
        except OSError as exc:messagebox.showerror('操作未完成',str(exc),parent=self)

    def _undo(self):
        try:self.app.undo.undo();self.refresh()
        except (ValueError,OSError) as exc:messagebox.showinfo('操作未完成',str(exc),parent=self)

    def _ids(self):return [int(i) for i in self.tv.selection()]

    def _edit(self):
        from ui_tasks import TaskEditor
        ids=self._ids()
        if len(ids)!=1:
            messagebox.showinfo('编辑任务','请只选择一个任务。',parent=self);return
        try:
            task=next(t for t in self.app.task_queue if t['id']==ids[0])
            from task_features import editable
            editable(self.app,ids[0])
            dlg=TaskEditor(self.app,task,parent=self.owner,modes=('countdown','datetime','interval'));self.wait_window(dlg)
            if dlg.result:self.app.edit_queue_task(ids[0],dlg.result)
        except (ValueError,OSError) as exc:messagebox.showerror('不能编辑',str(exc),parent=self)

    def _copy(self):
        try:self.app.copy_queue_tasks(self._ids())
        except (ValueError,OSError) as exc:messagebox.showerror('复制失败',str(exc),parent=self)

    def _move(self,direction):
        ids=self._ids()
        try:
            self.app.move_queue_tasks(ids,direction)
            self.tv.selection_set([str(i) for i in ids]);self.tv.see(str(ids[0])) if ids else None
        except (ValueError,OSError) as exc:messagebox.showerror('排序失败',str(exc),parent=self)

    def _template(self):
        import ui_template_name as simpledialog
        from task_store import save_template
        ids=self._ids()
        if len(ids)!=1:messagebox.showinfo('保存模板','请只选择一个任务。',parent=self);return
        task=next(t for t in self.app.task_queue if t['id']==ids[0]);name=simpledialog.askstring('保存模板','模板名称：',parent=self)
        if name:
            import copy
            previous=copy.deepcopy(self.app.cfg.get('templates') or [])
            try:
                save_template(self.app.cfg,name,task)
                if not self.app.cfg.save():raise OSError('模板保存失败')
            except (ValueError,OSError) as exc:
                self.app.cfg['templates']=previous;messagebox.showerror('保存失败',str(exc),parent=self)


class QueueWindow(QueueView, tk.Toplevel):
    def __init__(self, app): self._init_view(app)


class QueuePanel(QueueView, tk.Frame):
    def __init__(self, app, parent): self._init_view(app, parent, embedded=True)
