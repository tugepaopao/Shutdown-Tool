"""非阻塞颜色过渡：保留控件、输入、焦点和运行中计时。"""
import tkinter as tk
import time
from theme import theme, blend, shade, PALETTES, ACCENTS

OPTIONS=('background','foreground','activebackground','activeforeground',
         'disabledforeground','highlightbackground','highlightcolor','selectcolor',
         'selectbackground','selectforeground','insertbackground')

def walk(root):
    yield root
    for child in root.winfo_children():yield from walk(child)

def finish(app):
    transition=getattr(app,'_color_transition',None)
    if transition:
        app.root.after_cancel(transition['after'])
        transition['paint'](1.0)
        app._color_transition=None

def animate(app,old_palette,old_accent,old_dark,duration=360):
    target=dict(theme.p);target_accent=theme.accent;new_dark=theme.is_dark
    old=dict(old_palette);old['accent']=old_accent
    new=dict(target);new['accent']=target_accent
    old['accent_hover']=shade(old_accent,1.12 if old_dark else .90)
    new['accent_hover']=shade(target_accent,1.12 if new_dark else .90)
    entries=[]
    for widget in walk(app.root):
        if getattr(widget,'_theme_fixed',False):continue
        roles=getattr(widget,'_theme_roles',{})
        fields=getattr(widget,'_theme_options',None)
        if fields is None:
            fields=tuple(option for option in OPTIONS if option in widget.keys());widget._theme_options=fields
        changes={}
        for option in fields:
            current=str(widget.cget(option))
            role=roles.get(option)
            if role is None:
                matches=[key for key,value in old.items() if value.lower()==current.lower()]
                if not matches:continue
                # 白色文字和白色输入框分别保留语义，避免深色中错配。
                preferred='accent_fg' if option in ('foreground','activeforeground','selectforeground') and current.lower()=='#ffffff' else ('input_bg' if widget.winfo_class() in ('Entry','Spinbox','Text') and option=='background' else 'card')
                role=preferred if preferred in matches else matches[0]
                roles[option]=role
            changes[option]=(current,new.get(role,current))
        if changes:entries.append((widget,changes))
        widget._theme_roles=roles
        for attr in ('_bg','_fg','_hover','_border'):
            if hasattr(widget,attr):
                current=str(getattr(widget,attr));matches=[key for key,value in old.items() if value.lower()==current.lower()]
                if matches:
                    key='accent_fg' if attr=='_fg' and 'accent_fg' in matches else matches[0]
                    setattr(widget,attr,new[key])
    start=time.monotonic()
    def paint(t):
        eased=t*t*(3-2*t)
        theme._transition_palette={key:blend(old_palette[key],value,eased) for key,value in target.items()}
        theme._transition_accent=blend(old_accent,target_accent,eased)
        theme.apply_ttk(app.root)
        settings=getattr(app,'_settings_win',None)
        if settings and settings.winfo_exists() and getattr(settings,'_pc_panel',None) is not None:settings.pc_panel.retheme()
        from ui_compact import refresh_icons
        if duration>0 or not hasattr(app,"skin_renderer"):refresh_icons(app)
        app._last_transition_samples.append(blend(old_palette['bg'],target['bg'],eased))
        for widget,changes in entries:
            try:widget.configure(**{option:blend(before,after,eased) for option,(before,after) in changes.items()})
            except tk.TclError:pass
        if t>=1:
            theme._transition_palette=None;theme._transition_accent=None
            theme.apply_ttk(app.root)
            app._refresh_action_styles();app._refresh_mode_btns();app._set_running_ui(app.engine.is_running())
            settings=getattr(app,'_settings_win',None)
            if settings and settings.winfo_exists():settings._refresh_accent_rings();settings._set_apply_enabled(settings.dirty)
            from ui_dialog_chrome import update
            for widget in walk(app.root):
                if isinstance(widget,tk.Toplevel):update(widget)
    def frame():
        t=1.0 if duration<=0 else min(1,(time.monotonic()-start)*1000/duration);paint(t)
        if t<1:
            app._color_transition={'after':app.root.after(20,frame),'paint':paint}
        else:
            app._color_transition=None
            if old_dark!=new_dark:
                for window in [app.root]+[w for w in app.root.winfo_children() if isinstance(w,tk.Toplevel)]:
                    app._apply_window_chrome(window)
    app._last_transition_samples=[]
    frame()
