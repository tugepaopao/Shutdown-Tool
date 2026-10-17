"""Compact settings with a short-label rail and a fixed save region."""
import copy,json,tkinter as tk,tkinter.font as tkfont
from tkinter import ttk,filedialog
from theme import theme,flat_button,enable_button
from ui_cozy import CozyFrame,scale,cozy_icon
from ui_window import prepare,show
from ui_dialog_palette import COLORS as C,apply
from ui_settings_controls import Switch,Expander,label,text
from ui_localize import messagebox
from ui_pc_controls import ControlPanel,PercentSlider
from i18n import Texts,feature_text,LANGUAGE_FILES,AUTHOR
import autostart,quick_presets

PAGES=(('general','通用与启动','gear'),('notifications','提醒与通知','bell'),('floating','界面与悬浮','monitor'),('tasks','任务与预设','document'),('hotkeys','全局快捷键','keyboard'),('pc','电脑快控','monitor'),('backup','备份与诊断','database'))
NAV_LABELS={'CHS':('通用','提醒','界面','任务','快捷键','快控','备份')}
BOOLS=('confirm_before_action','confirm_key_only','confirm_on_exit','confirm_on_exit_only_timer','force_close_apps','esc_to_minimize','minimize_to_tray','autostart','sound_at_10s','popup_at_10s','cancel_at_10s','log_enabled','resume_timer','hotkeys_enabled','notify_setup','notify_done','notify_error','float_enabled','float_topmost')

class SettingsNav(CozyFrame):
    def __init__(self,parent,owner,width):
        super().__init__(parent,bg=C['card'],width=width);self.pack_propagate(False);self.owner=owner;self.buttons={};self.selected=''
        for key,title,icon in PAGES:
            slot=tk.Frame(self,bg=C['card'],height=round(38*owner.s));slot.pack(fill='x',padx=5,pady=(4 if key=='general' else 1,0));slot.pack_propagate(False)
            b=flat_button(slot,owner.nav_label(key),lambda k=key:owner._show(k),font=owner.font(),padx=5,pady=4)
            b._theme_photo=cozy_icon(self,icon,round(20*owner.s));b.config(image=b._theme_photo,compound='left',anchor='w');b.pack(fill='both',expand=True);self.buttons[key]=b
    def get_children(self):return tuple(self.buttons)
    def selection(self):return (self.selected,) if self.selected else ()
    def selection_set(self,key):self.owner._show(key)
    def item(self,key,**kwargs):
        if 'text' in kwargs:self.buttons[key].config(text=kwargs['text'])
        return {'text':self.buttons[key].cget('text')}
    def paint(self,key):
        self.selected=key
        for k,b in self.buttons.items():
            color=C['hover'] if k==key else C['card'];b._bg=color;b._hover=C['hover'];b.config(bg=color,activebackground=C['hover'],fg=theme.accent if k==key else C['fg'])

class SettingsWindow(tk.Toplevel):
    def __init__(self,app):
        super().__init__(app.root);prepare(self);self.app=app;self.T=app.T;self.cfg=app.cfg;self.s=scale(self);self.dirty=False;self._closing=False;self._syncing=True;self._pc_panel=None;self.preview_window=None
        self.title(self.T('set_title'));self.resizable(False,False);self.configure(bg=C['bg'])
        self.v={};self._load_vars()
        body=tk.Frame(self,bg=C['bg']);body.pack(fill='both',expand=True,padx=round(10*self.s),pady=round(8*self.s))
        nav_width=self._nav_width()
        self.nav=SettingsNav(body,self,nav_width);self.nav.pack(side='left',fill='y')
        self.right=tk.Frame(body,bg=C['bg']);self.right.pack(side='left',fill='both',expand=True,padx=(round(10*self.s),0))
        self.pages={};self._scroll_pages={};self._built_pages=set();self._current=None
        for key,title,_ in PAGES:self._page(key,title)
        self.footer=CozyFrame(self.right,bg=C['card'],height=round(60*self.s));self.footer.pack_propagate(False);self.footer.pack(side='bottom',fill='x',pady=(round(6*self.s),0),padx=(0,round(12*self.s)))
        foot=tk.Frame(self.footer,bg=C['card']);foot.pack(fill='both',expand=True,padx=round(10*self.s),pady=round(5*self.s))
        actions=tk.Frame(foot,bg=C['card']);actions.pack(side='right',padx=(round(6*self.s),0))
        self.save_btn=flat_button(actions,self.tr('保存设置'),self.on_apply,kind='accent',font=self.font(),padx=10,pady=5);self.save_btn.pack(side='right',padx=(8,0))
        self.discard_btn=flat_button(actions,self.tr('放弃更改'),self.discard,font=self.font(),padx=10,pady=5);self.discard_btn.pack(side='right')
        tk.Frame(foot,bg='#DDD5F1',width=1).pack(side='right',fill='y',padx=(round(6*self.s),0))
        self.save_state=tk.Label(foot,bg=C['card'],fg=C['muted'],font=self.font(bold=True),anchor='w');self.save_state.pack(fill='x')
        self.save_note=tk.Label(foot,bg=C['card'],fg=C['muted'],font=self.font(delta=-2),anchor='w',justify='left',wraplength=round(230*self.s));self.save_note.pack(fill='x',pady=(3,0))
        self.save_note.bind('<Configure>',lambda e:self.save_note.config(wraplength=max(30,e.width-2)) if abs(int(self.save_note.cget('wraplength'))-e.width)>3 else None)
        self.apply_btn=self.save_btn
        self._size_for_language()
        self._show('general');self.bind('<Escape>',lambda e:self.request_close());self.protocol('WM_DELETE_WINDOW',self.request_close)
        self._syncing=False;self._baseline=self._values();self._mark_dirty()
        self.update_idletasks();self.geometry(f'+{max(0,app.root.winfo_rootx()+25)}+{max(0,app.root.winfo_rooty()+25)}');show(self)
        # Keep the footer above the taskbar, including larger display scaling.
        from ui_floating import workareas,clamp_position
        import ctypes
        from ctypes import wintypes as W
        x,y=clamp_position(app.root.winfo_rootx()+25,app.root.winfo_rooty()+25,*self._compact_size,workareas(self))
        u=ctypes.windll.user32;u.GetAncestor.argtypes=[W.HWND,W.UINT];u.GetAncestor.restype=W.HWND
        u.SetWindowPos.argtypes=[W.HWND,W.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,W.UINT]
        u.SetWindowPos(u.GetAncestor(self.winfo_id(),2),None,x,y,*self._compact_size,0x14)
        self.focus_set()
    def font(self,delta=0,bold=False):
        return theme.font(delta=max(-2,delta-1),bold=bold)
    def nav_label(self,key):
        return NAV_LABELS.get(self.T.lang,NAV_LABELS['CHS'])[[k for k,_,_ in PAGES].index(key)]
    def _nav_width(self):
        font=tkfont.Font(root=self,font=self.font())
        return max(round((96 if self.T.lang!='EN' else 116)*self.s),
                   max(font.measure(self.nav_label(k)) for k,_,_ in PAGES)+round(44*self.s))
    def _size_for_language(self):
        # Explicit geometry prevents lazy pages and translations changing the window size.
        from ui_floating import workareas
        areas=workareas(self);cx=self.app.root.winfo_rootx();cy=self.app.root.winfo_rooty()
        area=min(areas,key=lambda a:max(a[0]-cx,0,cx-a[2])**2+max(a[1]-cy,0,cy-a[3])**2)
        width=round((640 if self.T.lang=='EN' else 560)*self.s)
        height=round(520*self.s)
        self._compact_size=(min(width,area[2]-area[0]-20),min(height,area[3]-area[1]-20))
        self.geometry(f'{self._compact_size[0]}x{self._compact_size[1]}')
        if getattr(self,'_dialog_ready',False):
            # The custom caption removes native frame pixels; size the real wrapper too.
            self.update_idletasks()
            import ctypes
            from ctypes import wintypes as W
            from ui_floating import clamp_position
            x,y=clamp_position(self.winfo_rootx(),self.winfo_rooty(),*self._compact_size,areas)
            u=ctypes.windll.user32;u.GetAncestor.argtypes=[W.HWND,W.UINT];u.GetAncestor.restype=W.HWND
            u.SetWindowPos.argtypes=[W.HWND,W.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,W.UINT]
            u.SetWindowPos(u.GetAncestor(self.winfo_id(),2),None,x,y,*self._compact_size,0x14)
        if hasattr(self,'nav'):self.nav.config(width=self._nav_width())
    def tr(self,value):return feature_text(self.T,value)
    def _load_vars(self):
        for key in BOOLS:self.v[key]=tk.BooleanVar(self,value=bool(self.cfg.get(key)))
        for key in ('language','hotkey_show','hotkey_pause','hotkey_resume','hotkey_floating','resume_strategy'):self.v[key]=tk.StringVar(self,value=self.cfg.get(key))
        for key in ('toast_seconds','float_opacity','warning_seconds'):self.v[key]=tk.StringVar(self,value=str(self.cfg.get(key)))
        if not self.cfg.get('notifications_enabled'):
            for key in ('notify_setup','notify_done','notify_error'):self.v[key].set(False)
        self.v['quick_presets']=tk.StringVar(self,value=json.dumps(quick_presets.get(self.cfg),sort_keys=True))
        for var in self.v.values():var.trace_add('write',self._mark_dirty)
    def _values(self):return {k:v.get() for k,v in self.v.items()}
    def _mark_dirty(self,*args):
        if self._syncing:return
        count=sum(value!=self._baseline.get(k) for k,value in self._values().items())+int(getattr(self,'_preset_draft_dirty',False));self.dirty=bool(count)
        if hasattr(self,'save_state'):
            self._dirty_count=count
            self._paint_save_state()
            enable_button(self.save_btn,self.dirty);enable_button(self.discard_btn,self.dirty)
            self.save_btn.config(bg=theme.accent,disabledforeground='#E6D9FB')
            if hasattr(self,'hotkey_panel'):self.hotkey_panel.refresh()
            self.discard_btn.config(bg=C['input'],disabledforeground=C['muted'])
    def _paint_save_state(self):
        count=getattr(self,'_dirty_count',0);instant=self._current=='pc'
        state='已修改' if count else '立即生效' if instant else '未修改'
        note='修改后需保存才会生效' if count or not instant else '亮度与音量调整立即生效'
        if count and instant:note='其他设置已修改，需保存生效'
        self.save_state.config(text=self.tr('已修改 {n} 项').format(n=count) if count else self.tr(state),fg=theme.accent if count else C['muted'])
        self.save_state._state_photo=cozy_icon(self,'check',round(17*self.s),ink=theme.accent if count else C['muted'])
        self.save_state.config(image=self.save_state._state_photo,compound='left',padx=3)
        self.save_note.config(text=self.tr(note))
    def sync_external(self,key,value):
        """An immediate main-window action updates one field, preserving other drafts."""
        if key not in self.v:return
        self._syncing=True
        try:self.v[key].set(value);self._baseline[key]=self.v[key].get()
        finally:self._syncing=False
        self._mark_dirty()
    def _set_apply_enabled(self,value):self._mark_dirty()
    def _page(self,key,title):
        if key in self.pages:return self._scroll_pages[key][1]
        frame=tk.Frame(self.right,bg=C['bg']);self.pages[key]=frame
        head=tk.Frame(frame,bg=C['bg']);head.pack(fill='x',pady=(2,8))
        self._lab(head,title,font=self.font(delta=3,bold=True)).pack(side='left')
        canvas=tk.Canvas(frame,bg=C['bg'],highlightthickness=0,width=round(400*self.s),height=round(300*self.s));canvas.pack(side='left',fill='both',expand=True)
        gutter=tk.Frame(frame,bg=C['bg'],width=round(12*self.s));gutter.pack(side='right',fill='y');gutter.pack_propagate(False)
        scroll=ttk.Scrollbar(gutter,command=canvas.yview);canvas.config(yscrollcommand=scroll.set)
        pad=tk.Frame(canvas,bg=C['bg']);item=canvas.create_window(0,0,window=pad,anchor='nw')
        def layout(e=None):
            canvas.configure(scrollregion=(0,0,canvas.winfo_width(),max(canvas.winfo_height(),pad.winfo_reqheight())))
            if pad.winfo_reqheight()>canvas.winfo_height():scroll.pack(fill='y',expand=True)
            else:scroll.pack_forget()
        pad.bind('<Configure>',layout);canvas.bind('<Configure>',lambda e:(canvas.itemconfigure(item,width=e.width),layout()))
        self.bind('<MouseWheel>',lambda e,k=key:canvas.yview_scroll(-int(e.delta/120),'units') if self._current==k and pad.winfo_reqheight()>canvas.winfo_height() and e.widget.winfo_class() not in ('TCombobox','TSpinbox') else None,add='+')
        self._scroll_pages[key]=(canvas,pad,scroll,item);return pad
    def _show(self,key):
        key={'display':'general','other':'tasks','automation':'tasks','desktop':'notifications'}.get(key,key)
        if key==self._current:return
        if hasattr(self,'hotkey_panel'):self.hotkey_panel.end_capture()
        new_page=key not in self._built_pages
        self._ensure_page(key)
        for k,f in self.pages.items():
            if k==key:f.pack(fill='both',expand=True)
            else:f.pack_forget()
        self._current=key;self.nav.paint(key)
        if new_page:
            apply(self,self.pages[key]);self._compact_control_fonts(self.pages[key])
        if self._pc_panel:self._pc_panel.set_active(key=='pc')
        if hasattr(self,'save_state'):self._paint_save_state()
        if key=='pc':self.pc_panel.refresh()
        if key=='tasks':self._task_counts()
        if key=='backup':self.diagnostics_panel.refresh()
    def _compact_control_fonts(self, subtree=None):
        from ui_localize import walk
        for widget in walk(subtree if subtree is not None else self):
            if isinstance(widget,(ttk.Entry,ttk.Combobox,ttk.Spinbox)):
                widget.configure(font=self.font())
    def _ensure_page(self,key):
        if key not in self._built_pages:getattr(self,'_build_'+key)();self._built_pages.add(key)
    def _lab(self,parent,value,**kwargs):
        kw=dict(text=self.tr(value),bg=parent.cget('bg'),fg=C['fg'],font=self.font(),anchor='w',justify='left');kw.update(kwargs)
        w=tk.Label(parent,**kw);w._source_text=value
        from i18n import _TEXTS
        w._settings_text_key=next((k for k,v in _TEXTS[self.T.lang].items() if value and v==value),None)
        if kw.get('wraplength',0):
            w.bind('<Configure>',lambda e:w.config(wraplength=max(50,e.width-2)) if abs(int(w.cget('wraplength'))-e.width)>3 else None)
        return w
    def _card(self,pad,title,note=None):
        card=CozyFrame(pad,bg=C['card'],bd=0,highlightthickness=0);card.pack(fill='x',pady=(0,round(7*self.s)))
        h=tk.Frame(card,bg=C['card']);h.pack(fill='x',padx=round(12*self.s),pady=(round(10*self.s),round(5*self.s)))
        self._lab(h,title,font=self.font(delta=1,bold=True)).pack(side='left')
        if note:self._lab(card,note,fg=C['muted'],font=self.font(delta=-2),wraplength=400).pack(fill='x',padx=round(12*self.s),pady=(0,round(4*self.s)))
        inner=tk.Frame(card,bg=C['card']);inner.pack(fill='x',padx=round(12*self.s),pady=(0,round(10*self.s)))
        return inner
    def _actions(self,parent,items):
        from ui_window import button_grid
        row=tk.Frame(parent,bg=parent.cget("bg"));row.pack(fill="x",pady=4)
        buttons=button_grid(row,items)
        for b in buttons:
            if b._kind!='accent':b._bg=C["hover"];b._hover=C["selected"];b.config(bg=C["hover"],fg=theme.accent,activebackground=C["selected"])
        return buttons
    def _row(self,parent,name,widget=None):
        row=tk.Frame(parent,bg=parent.cget('bg'));row.pack(fill='x',pady=round(4*self.s))
        lab=self._lab(row,name,wraplength=round(365*self.s));row._row_label=lab
        if widget:widget(row).pack(side='right')
        lab.pack(side='left',fill='x',expand=True)
        return row
    def _check(self,parent,key,name,indent=0,dep=None,wraplength=0,checkbox=False):
        row=self._row(parent,name);control=Switch(row,self.v[key],checkbox);control.pack(side='right');row._row_label.pack_forget();row._row_label.pack(side='left',fill='x',expand=True)
        if dep:
            def sync(*a):control.set_disabled(not self.v[dep].get())
            self.v[dep].trace_add('write',sync);sync()
        return control
    def _enum(self,parent,key,values,width=18):
        box=ttk.Combobox(parent,state='readonly',values=[self.tr(label) for _,label in values],width=width,justify='center');box._source_values=[label for _,label in values];box._setting_key=key;box._codes=[v for v,_ in values]
        box.current(next((i for i,(value,_) in enumerate(values) if value==self.v[key].get()),0))
        box.bind('<<ComboboxSelected>>',lambda e:self.v[key].set(values[box.current()][0]));return box
    def _expander(self,parent,title,notes):
        e=Expander(parent,title);e.pack(fill='x',pady=5)
        for note in notes:self._lab(e.body,note,wraplength=480,font=self.font(delta=-1),fg=C['muted']).pack(fill='x',pady=3)
        return e
    def _build_general(self):
        pad=self._page('general','通用与启动')
        g=self._card(pad,'窗口行为')
        self._row(g,'最小化：回到任务栏')
        self._check(g,'minimize_to_tray','关闭主窗口时隐藏到托盘')
        self._check(g,'esc_to_minimize','按 Esc 最小化到任务栏')
        g=self._card(pad,'启动与恢复')
        self._check(g,'autostart',self.T('set_autostart'))
        self._row(g,'重开后的定时恢复',lambda r:self._enum(r,'resume_strategy',[('ask','询问恢复'),('paused','恢复为暂停'),('continue','直接继续'),('off','不恢复')]))
        g=self._card(pad,'操作确认')
        for key,name,dep in [('confirm_before_action',self.T('set_confirm_before'),None),('confirm_key_only',self.T('set_confirm_key'),'confirm_before_action'),('confirm_on_exit',self.T('set_confirm_on_exit'),None),('confirm_on_exit_only_timer',self.T('set_confirm_exit_timer'),'confirm_on_exit'),('force_close_apps',self.T('set_force_close'),None)]:self._check(g,key,name,dep=dep)
    def _build_hotkeys(self):
        from ui_hotkey_settings import HotkeyPanel
        pad=self._page('hotkeys','全局快捷键');self.hotkey_panel=HotkeyPanel(self,pad)
    def _build_notifications(self):
        pad=self._page('notifications','提醒与通知');g=self._card(pad,'执行前提醒','提前提醒不改变任务执行时刻。')
        self._row(g,'提前提醒',lambda r:self._enum(r,'warning_seconds',[(str(v),str(v)+' 秒') for v in (10,30,60)],width=12))
        for key,name in [('cancel_at_10s','可取消提醒'),('sound_at_10s','提示音'),('popup_at_10s','显示主窗口')]:self._check(g,key,name)
        g=self._card(pad,'Windows 通知','按 Windows 通知设置显示。')
        for key,name in [('notify_setup','任务已设置'),('notify_done','任务已完成'),('notify_error','任务失败')]:
            row=tk.Frame(g,bg=C['card']);row.pack(fill='x',pady=5);Switch(row,self.v[key],checkbox=True).pack(side='left');self._lab(row,name).pack(side='left',padx=6)
        g=self._card(pad,'消息与预览');self._row(g,'消息停留时长',lambda r:ttk.Spinbox(r,from_=3,to=600,textvariable=self.v['toast_seconds'],width=8,justify='center'))
        from ui_window import button_grid
        self._actions(g,[(self.tr('预览提醒'),self.preview,'normal'),(self.tr('测试通知'),self._test_notification,'normal')])
    def _build_floating(self):
        pad=self._page('floating','界面与悬浮');g=self._card(pad,self.T('float_title'))
        self._check(g,'float_enabled',self.T('float_enabled'));self._check(g,'float_topmost',self.T('float_topmost'),dep='float_enabled')
        row=self._row(g,self.T('float_opacity'))
        self.opacity_value=tk.Label(row,bg=C['card'],fg=theme.accent,font=self.font(),anchor='e')
        self.opacity_value.pack(side='right')
        def percent(*args):self.opacity_value.config(text=f"{int(float(self.v['float_opacity'].get()))}%")
        trace=self.v['float_opacity'].trace_add('write',percent);percent()
        self.opacity_value.bind('<Destroy>',lambda e:self.v['float_opacity'].trace_remove('write',trace) if e.widget is self.opacity_value else None)
        self.opacity_slider=PercentSlider(g,self.v['float_opacity'],lambda value:None,minimum=40,maximum=100)
        self.opacity_slider.pack(fill='x',pady=(2,7))
        self.float_reset_button=flat_button(g,self.T('float_reset'),self._reset_float,kind='accent',padx=12,pady=5)
        self.float_reset_button.pack(fill='x',pady=6)
    def _reset_float(self):
        self.cfg['float_positioned']=False;self.cfg['float_docked']=False;self.cfg.save();f=self.app.floating
        if f.window:f.window.destroy();f.window=None;f.apply()
    def _build_pc(self):
        pad=self._page('pc','电脑快控');self._lab(pad,'拖动滑块立即生效；放弃更改不会撤销硬件调整。',wraplength=540,fg=C['muted'],font=self.font(delta=-1)).pack(fill='x',pady=(0,8))
        self._pc_panel=ControlPanel(pad,self)
    @property
    def pc_panel(self):self._ensure_page('pc');return self._pc_panel
    def _build_tasks(self):
        pad=self._page('tasks','任务与预设');g=self._card(pad,'快捷预设');self._lab(g,'六个位置，可按习惯设置',fg=C['muted'],font=self.font(delta=-1)).pack(fill='x',pady=(0,8))
        self.preset_items=json.loads(self.v['quick_presets'].get());self.preset_index=5;grid=tk.Frame(g,bg=C['card']);grid.pack(fill='x');self.preset_tiles=[]
        for i in range(6):
            grid.columnconfigure(i%3,weight=1,uniform='preset');slot=tk.Frame(grid,bg=C['card'],height=round(46*self.s));slot.grid(row=i//3,column=i%3,sticky='ew',padx=round(3*self.s),pady=round(3*self.s));slot.pack_propagate(False)
            b=flat_button(slot,'',lambda index=i:self.select_preset(index),padx=5,pady=5,font=self.font(delta=-1));b._fit_text=True;b.pack(fill='both',expand=True);b.bind('<Button-3>',lambda e,index=i:self.preset_menu(index),add='+');self.preset_tiles.append(b)
        form=tk.Frame(g,bg=C['card']);form.pack(fill='x',pady=(10,2));self.preset_label=self._lab(form,'第1项');self.preset_label.pack(side='left',padx=(0,8))
        self.preset_kind=ttk.Combobox(form,state='readonly',values=[self.tr('倒计时'),self.tr('定点执行')],width=10);self.preset_kind.bind('<<ComboboxSelected>>',self.preset_kind_changed)
        self.preset_day=ttk.Combobox(form,state='readonly',values=self._preset_days(),width=10);self.preset_day.pack(side='left',padx=5);self.preset_day.bind('<<ComboboxSelected>>',self.preset_edited)
        self._preset_draft_dirty=False;self._preset_loading=False
        self.preset_value=tk.StringVar(self);self.preset_value.trace_add('write',self._preset_text_changed);self.preset_entry=ttk.Entry(form,textvariable=self.preset_value,width=10,justify='center');self.preset_entry.pack(side='left',padx=5,fill='x',expand=True);self.preset_entry.bind('<FocusOut>',self.preset_edited);self.preset_entry.bind('<Return>',self.preset_edited)
        self.preset_unit=self._lab(form,'分钟');self.preset_unit.pack(side='left');self.preset_error=self._lab(g,'',fg='#A84967',font=self.font(delta=-1));self.preset_error.pack(fill='x')
        self._lab(g,'修改后只影响快捷入口；右键可更改方式、排序或恢复默认。',fg=C['muted'],wraplength=510,font=self.font(delta=-1)).pack(fill='x',pady=(3,0))
        self.select_preset(5,commit=False)
        g=self._card(pad,'任务中心');self.task_counts=self._lab(g,'',wraplength=400);self.task_counts.pack(fill='x',pady=(0,8));self._task_counts()
        flat_button(g,self.tr('打开任务中心'),lambda:self.app.open_task_center(parent=self),kind='accent',padx=16,pady=8).pack(fill='x')
    def _preset_days(self):
        if self.T.lang=='EN':return ('Today','Tomorrow')+tuple(f'In {n} days' for n in range(2,8))
        return tuple(self.tr(v) for v in ('今天','明天','后天','3天后','4天后','5天后','6天后','7天后'))
    def _task_counts(self):
        if hasattr(self,'task_counts'):self.task_counts.config(text=self.tr('队列 {q} 项 · 模板 {t} 个 · 高级任务 {a} 项').format(q=len(self.app.task_queue),t=len(self.cfg.get('templates') or []),a=len(self.app.automation.jobs)))
    def _preset_text_changed(self,*args):
        if self._preset_loading:return
        self._preset_draft_dirty=self.preset_value.get()!=getattr(self,'_preset_display','');self._mark_dirty()
    def preset_edited(self,e=None):
        if not hasattr(self,'preset_entry'):return True
        try:
            if self.preset_kind.current()==0:
                number=float(self.preset_value.get());seconds=round(number*60)
                if seconds!=number*60 and abs(seconds-number*60)>1e-6:raise ValueError('时长最多精确到秒')
                value=dict(kind='duration',seconds=seconds)
            else:
                raw=self.preset_value.get().strip().replace('：',':');h,m=map(int,raw.split(':'));value=dict(kind='clock',day_offset=self.preset_day.current(),hour=h,minute=m)
            items=copy.deepcopy(self.preset_items);items[self.preset_index]=value;self.preset_items=quick_presets.validate(items)
            self._preset_draft_dirty=False;self._preset_display=self.preset_value.get()
            self.v['quick_presets'].set(json.dumps(self.preset_items,sort_keys=True));self.preset_error.config(text='');self.paint_presets();return True
        except (ValueError,OverflowError):self.preset_error.config(text=self.tr('请输入有效时长或 HH:MM 时间'));return False
    def select_preset(self,index,commit=True):
        if commit and not self.preset_edited():return
        self.preset_index=index;v=self.preset_items[index];self.preset_kind.current(0 if v['kind']=='duration' else 1)
        self._preset_loading=True
        self.preset_label.config(text=self.tr('第{n}项').format(n=index+1));self.preset_value.set(str(v['seconds']/60).rstrip('0').rstrip('.') if v['kind']=='duration' else f"{v['hour']:02}:{v['minute']:02}")
        if v['kind']=='clock':self.preset_day.pack(side='left',after=self.preset_label,padx=5);self.preset_day.current(v['day_offset']);self.preset_unit.config(text='')
        else:self.preset_day.pack_forget();self.preset_unit.config(text=self.tr('分钟'))
        self._preset_loading=False;self._preset_display=self.preset_value.get();self._preset_draft_dirty=False;self.paint_presets()
    def paint_presets(self):
        for i,b in enumerate(self.preset_tiles):
            v=self.preset_items[i];selected=i==self.preset_index;b._theme_photo=cozy_icon(self,'clock',round(20*self.s));b._selection_outline=theme.accent if selected else '#E4DEF5';b._last_paint=None;b.config(text=quick_presets.caption(v,self.T),image=b._theme_photo,compound='left',bg=C['input']);b._bg=C['input'];b._hover=C['hover']
    def preset_kind_changed(self,e=None):
        self.preset_value.set('30' if self.preset_kind.current()==0 else '08:00');self.preset_day.current(1);self.preset_edited();self.select_preset(self.preset_index,commit=False)
    def preset_menu(self,index):
        if not self.preset_edited():return
        self.select_preset(index,False)
        from ui_popup_menu import VioletMenu
        menu=tk.Menu(self,tearoff=0)
        for title,command in [('倒计时',lambda:(self.preset_kind.current(0),self.preset_kind_changed())),('定点执行',lambda:(self.preset_kind.current(1),self.preset_kind_changed())),('前移',lambda:self.move_preset(index,-1)),('后移',lambda:self.move_preset(index,1)),('恢复默认',self.reset_presets)]:menu.add_command(label=self.tr(title),command=command)
        self._preset_popup=VioletMenu(self.app,menu,anchor=self.preset_tiles[index],icons=('clock','sun','enqueue','enqueue','clear'))
    def move_preset(self,index,delta):
        other=index+delta
        if not 0<=other<6:return
        self.preset_items[index],self.preset_items[other]=self.preset_items[other],self.preset_items[index];self.v['quick_presets'].set(json.dumps(self.preset_items,sort_keys=True));self.select_preset(other,False)
    def reset_presets(self):self.preset_items=quick_presets.defaults();self.v['quick_presets'].set(json.dumps(self.preset_items,sort_keys=True));self.preset_error.config(text='');self.select_preset(0,False)
    def _build_backup(self):
        from ui_diagnostics import DiagnosticsPanel
        self.diagnostics_panel=DiagnosticsPanel(self,self._page('backup','备份与诊断'))
    def copy_diagnostics(self):
        import diagnostics
        self.clipboard_clear();self.clipboard_append(diagnostics.text(self.app));self.update_idletasks();messagebox.showinfo('诊断概要已复制','默认不包含消息内容和个人文件路径。',parent=self)
    def preview(self):
        from ui_reminder import FadeMessageBox
        if self.preview_window and self.preview_window.winfo_exists():self.preview_window.close()
        seconds=int(self.v['warning_seconds'].get());self.preview_window=FadeMessageBox(self.app.root,self.tr('提醒预览'),self.tr('这是预览，不会执行操作或改变当前计时。'),seconds=seconds,button_text=self.T('btn_cancel_action'),on_button=lambda:self.preview_window.close(),extra_buttons=[(self.tr('延后'+str(m)+'分钟'),lambda:self.preview_window.close()) for m in (5,10,30)])
        if self.app.cancel_toast and self.app.cancel_toast.winfo_exists():
            x,y=self.preview_window.position;self.preview_window.position=(x,max(0,y-self.preview_window.panel_height-15));self.preview_window._present()
    def _test_notification(self):
        ok=self.app.desktop.notify('setup',self.tr('这是一条测试通知。'),force=True);messagebox.showinfo('提示','通知已提交给Windows' if ok else '托盘不可用，无法发送通知',parent=self)
    def _collect(self):
        if 'tasks' in self._built_pages and not self.preset_edited():raise ValueError('请输入有效时长或 HH:MM 时间')
        values=self._values();changed={k:v for k,v in values.items() if v!=self._baseline.get(k)}
        for key,low,high in [('toast_seconds',3,600),('float_opacity',40,100),('warning_seconds',10,60)]:
            if key in changed:
                changed[key]=int(changed[key]);
                if not low<=changed[key]<=high:raise ValueError('数值超出允许范围')
        if 'warning_seconds' in changed and changed['warning_seconds'] not in (10,30,60):raise ValueError('提醒提前量无效')
        if 'quick_presets' in changed:changed['quick_presets']=quick_presets.validate(json.loads(changed['quick_presets']))
        if 'resume_strategy' in changed:changed['resume_timer']=changed['resume_strategy']!='off'
        if any(k in changed for k in ('notify_setup','notify_done','notify_error')):changed['notifications_enabled']=any(values[k] for k in ('notify_setup','notify_done','notify_error'))
        if any(k.startswith('hotkey_') for k in changed):
            from desktop_services import parse_hotkey
            parsed=[parse_hotkey(values['hotkey_'+k]) for k in ('show','pause','resume','floating')]
            if len(set(parsed))!=len(parsed):raise ValueError('不同操作不能使用相同快捷键')
        return changed
    def on_apply(self,close=False):
        if hasattr(self,'hotkey_panel'):self.hotkey_panel.end_capture()
        previous=copy.deepcopy(self.cfg.data);startup_changed=False
        try:
            changed=self._collect();self.cfg.update(changed);self.app.desktop.apply()
            if 'autostart' in changed:
                if not autostart.set_enabled(changed['autostart']):raise OSError('开机启动设置失败，原设置已保留。')
                startup_changed=True
            if not self.cfg.save():raise OSError('配置保存失败，原设置已保留。')
        except (ValueError,OSError,TypeError) as exc:
            self.cfg.data=previous
            try:self.app.desktop.apply()
            except Exception:pass
            if startup_changed:autostart.set_enabled(previous.get('autostart',False))
            messagebox.showerror('操作未完成',str(exc),parent=self);return False
        self.app.engine.warning_seconds=int(self.cfg.get('warning_seconds',10));self.app.apply_settings();self._baseline=self._values();self._mark_dirty()
        if self._pc_panel:self._pc_panel.retheme()
        if close:self.destroy()
        return True
    def discard(self):
        self._syncing=True
        for key,value in self._baseline.items():self.v[key].set(value)
        self._syncing=False
        if hasattr(self,'preset_items'):self.preset_items=json.loads(self.v['quick_presets'].get());self.select_preset(self.preset_index,False)
        self._sync_enums();self._mark_dirty()
    def _sync_enums(self):
        # Keep the visible combo choices in sync after a draft is discarded.
        from ui_localize import walk
        for w in walk(self):
            if hasattr(w,'_source_values'):
                vals=w.cget('values')
                for key,var in self.v.items():
                    # Enum controls remember their configuration key below.
                    if getattr(w,'_setting_key',None)==key:w.current(next((i for i,v in enumerate(w._codes) if v==var.get()),0))
    def request_close(self):
        if self._closing:return 'break'
        if self.dirty:
            result=messagebox.askyesnocancel('保存更改？','是：保存；否：放弃；取消：继续编辑。',parent=self,default='cancel',labels={'yes':'保存','no':'放弃','cancel':'继续编辑'})
            if result is None:return 'break'
            if result and not self.on_apply():return 'break'
        self.destroy();return 'break'
    def on_ok(self):return self.on_apply(close=True)
    def sync_vars(self):
        self._syncing=True
        for key,var in self.v.items():
            value=json.dumps(quick_presets.get(self.cfg),sort_keys=True) if key=='quick_presets' else self.cfg.get(key)
            if value is not None:var.set(value)
        if not self.cfg.get('notifications_enabled'):
            for key in ('notify_setup','notify_done','notify_error'):self.v[key].set(False)
        self._syncing=False;self._baseline=self._values()
        if hasattr(self,'preset_items'):self.preset_items=json.loads(self.v['quick_presets'].get());self.select_preset(self.preset_index,False)
        self._sync_enums();self._mark_dirty()
    def retranslate(self,T):
        self.T=T
        from ui_localize import walk
        for w in walk(self):
            if hasattr(w,'_source_text'):w.config(text=self.T(w._settings_text_key) if getattr(w,'_settings_text_key',None) else self.tr(w._source_text))
            if hasattr(w,'_source_values'):
                i=w.current();w.config(values=[self.tr(v) for v in w._source_values]);w.current(i)
            if isinstance(w,Switch):w.draw()
            if isinstance(w,Expander):w.button.config(text=('− ' if w.opened else '+ ')+self.tr(w.title))
        for key,title,_ in PAGES:self.nav.buttons[key].config(text=self.nav_label(key))
        self._size_for_language()
        self.nav.paint(self._current);self._paint_save_state();
        if hasattr(self,'hotkey_panel'):self.hotkey_panel.refresh()
        self.save_btn.config(text=self.tr('保存设置'));self.discard_btn.config(text=self.tr('放弃更改'))
        if hasattr(self,'preset_items'):
            self.preset_day.config(values=self._preset_days());self.preset_kind.config(values=[self.tr('倒计时'),self.tr('定点执行')]);self.select_preset(self.preset_index,False);self._task_counts()
    def destroy(self):
        self._closing=True
        if hasattr(self,'hotkey_panel'):self.hotkey_panel.end_capture()
        if self.preview_window:
            try:self.preview_window.close()
            except tk.TclError:pass
        super().destroy()

