"""正式版 C：两步同页，保留业务控件和固定底栏。"""
import tkinter as tk
from tkinter import ttk
from theme import theme, flat_button
from ui_cozy import CozyFrame


THEMED_ICONS={'step1','step2','check','clock','sun','moon','enqueue','bolt','message','sliders'}

def icon(app,name,size=20):
    from ui_cozy import cozy_icon,scale
    cache=getattr(app,'_theme_icon_cache',None)
    if cache is None:app._theme_icon_cache={};cache=app._theme_icon_cache
    pixels=round(size*scale(app.root));key=(name,pixels,theme.accent)
    if key not in cache:
        cache[key]=cozy_icon(app.root,name,pixels)
        if len(cache)>192:cache.pop(next(iter(cache)))
    return cache[key]


def set_icon(app,widget,name,size):
    widget._theme_icon=(name,size)
    if getattr(widget,'_title_control',False) and __import__('skins').image_skin(app.cfg):
        from ui_cozy import cozy_icon,scale
        from PIL import Image,ImageTk,ImageFilter
        cache=getattr(app,'_title_icon_cache',None)
        if cache is None:app._title_icon_cache={};cache=app._title_icon_cache
        pixels=round(size*scale(app.root));key=(name,pixels)
        if key not in cache:
            original=ImageTk.getimage(cozy_icon(app.root,name,pixels,ink='#FFFFFF')).convert('RGBA')
            halo=Image.new('RGBA',original.size,'#444066');halo.putalpha(original.getchannel('A').filter(ImageFilter.MaxFilter(3)).point(lambda x:round(x*.6)))
            cache[key]=ImageTk.PhotoImage(Image.alpha_composite(halo,original),master=app.root)
        widget._theme_photo=cache[key]
    elif getattr(widget,'_soft_primary',False):
        from ui_cozy import cozy_icon,scale
        widget._theme_photo=cozy_icon(app.root,name,round(size*scale(app.root)),ink=theme.accent)
    else:widget._theme_photo=icon(app,name,size)
    widget.config(image=widget._theme_photo)

def refresh_icons(app):
    from ui_transition import walk
    for widget in walk(app.root):
        if hasattr(widget,'_theme_icon'):set_icon(app,widget,*widget._theme_icon)
    paint_modes(app)
    for fields in getattr(app,'time_inputs',{}).values():
        for field in fields:field.draw()


def heading(app, parent, step, text, settings=False):
    row = tk.Frame(parent, bg=theme.c('card'))
    row.pack(fill='x',padx=12,pady=(8,5))
    step_label=tk.Label(row,bg=theme.c('card'));set_icon(app,step_label,'step'+str(step),23);step_label.pack(side='left')
    tk.Label(row, text=text, bg=theme.c('card'), fg=theme.accent,
             font=theme.font(bold=True), padx=7).pack(side='left')
    if settings:
        app.header_bar = app.header_inner = row
        app.ver_badge = tk.Label(row, text='v'+str(app.cfg.get('_version', '')), bg=theme.c('bg'))
        app.header_hint = tk.Label(row)
    return row


def build_actions(app, parent):
    from ui_main import ACTION_ROWS
    heading(app, parent, 1, app.T('nav_actions'), True)
    body = tk.Frame(parent, bg=theme.c('card'))
    from ui_cozy import scale
    # Let the five actual rows set the height at every DPI; a fixed scaled
    # height left an increasingly large empty band below them.
    body.pack(anchor='w',padx=6,pady=(0,6))
    app.actions_box = app.actions_body = body
    app.hint_label = tk.Label(body)
    app.action_var = tk.StringVar(value=app.cfg.get('action'))
    app.action_widgets = {}; app.action_row_frames = {}; app.detail_rows = {}; app.detail_labels = {}; app.action_more = {}
    app.action_checks = {}
    for i, (action, key, more) in enumerate(ACTION_ROWS):
        grp = CozyFrame(body, bg=theme.c('card'), highlightthickness=0,
                       highlightbackground=theme.c('card_border'))
        grp.grid(row=i//2, column=i%2, sticky='ew', padx=(0, 4) if i%2==0 else (4, 0), pady=1)
        row = tk.Frame(grp, bg=theme.c('card')); row.pack(fill='x',padx=2,pady=3)
        ind = tk.Frame(row, width=0, bg=theme.c('card'))
        rb = flat_button(row, app.T(key),
            lambda a=action:(app.action_var.set(a),app._on_action_pick()),kind='plain',
            font=theme.font(delta=-2),padx=1,pady=1)
        rb.config(image=icon(app,action,19),compound='left',anchor='w',cursor='hand2')
        set_icon(app,rb,action,19)
        rb._row_action=True;rb._fit_text=True
        rb.pack(side='left', fill='x', expand=True)
        check = tk.Label(row, bg=theme.c('card'), width=round(17*scale(row)), image=icon(app, 'check', 17))
        check.pack(side='right', padx=(0, 1)); app.action_checks[action] = check
        check.bind('<Button-1>', lambda e,a=action: (app.action_var.set(a), app._on_action_pick()))
        if more:
            b=flat_button(row, '…', lambda a=action:app.pick_for(a), kind='ghost', padx=round(7*scale(row)),pady=2)
            b._skin_opacity=0;b._skin_border=False
            b.pack(side='right');app.action_more[action]=b
            app.detail_labels[action]=tk.Label(grp)
        # Keep the check beside the text, and parameters at the column edge.
        rb.pack_forget();check.pack_forget()
        rb.pack(side='left');check.pack(side='left',padx=(0,1))
        app.action_widgets[action]=rb; app.detail_rows[action]=row
        app.action_row_frames[action]=(grp,row,ind)
    # Each column reserves its own actual text/control width. A longer label
    # in the right column must not push that whole column farther to the right.
    for col in (0,1):body.columnconfigure(col,weight=0)
    app._bind_action_rows(); app._refresh_action_styles()


def paint_action(app, action, hover=False, selected=False):
    bg=theme.c('card')
    grp,row,ind=app.action_row_frames[action]
    grp.config(bg=bg, highlightbackground=theme.accent if selected else theme.c('card_border'))
    row.config(bg=bg); ind.config(bg=bg)
    for w in row.winfo_children():
        w.config(bg=bg)
        if isinstance(w,(tk.Button,tk.Radiobutton)):w.config(activebackground=bg)
    ink=theme.accent if selected else theme.c('fg')
    app.action_widgets[action].config(fg=ink)
    if action in app.action_more:
        app.action_more[action].config(fg=theme.accent if selected else theme.c('fg_dim'))
    set_icon(app,app.action_checks[action],'check' if selected else 'blank',17)


def refresh_details(app):
    # 参数在「…」弹窗内查看/修改，不挤占操作卡片。
    for action,lab in app.detail_labels.items():
        key={'close_program':'close_program_path','run_program':'program_path','play_sound':'sound_file','message':'message_text'}[action]
        lab.config(text=app.cfg.get(key) or '')
        lab.pack_forget()
    app._refresh_action_styles()


def build_timer(app, parent):
    from ui_main import QUICK_PRESETS
    heading(app,parent,2,app.T('nav_time'))
    # 复用时间输入、预设和按钮的原有构建逻辑，随后收紧展示层。
    app._build_timer_panel_legacy(parent)
    box=app.timer_box
    inner=app.timer_panel.master
    for c in box.winfo_children():
        if c is not inner:c.pack_forget()
    box.config(highlightthickness=0,bg=theme.c('card'))
    inner.pack_configure(padx=6,pady=(0,8))
    inner.config(bg=theme.c('card'))
    panel=app.timer_panel; panel.config(bg=theme.c('card'))
    gp=app.preset_row.master
    gp.config(text='',highlightthickness=0,font=theme.font(bold=True),bg=theme.c('card'),fg=theme.c('fg_dim'))
    gp.pack_configure(pady=(2,8))
    app.time_content_anchor=gp
    app.mode_bar.pack_configure(before=gp)
    from ui_skin import QuickHeading
    app.quick_heading=QuickHeading(gp,app);app.quick_heading.pack(fill='x',padx=4,pady=(2,2),before=app.preset_row)
    app.preset_row.config(bg=theme.c('card'));app.preset_row.pack_configure(padx=0,pady=(3,0))
    names=['clock']*6
    for b in app.preset_btns.values():b.destroy()
    app.preset_btns={}
    for i,(key,spec) in enumerate(QUICK_PRESETS):
        tile=tk.Frame(app.preset_row,bg=theme.c('card'),highlightthickness=0,
                      highlightbackground=theme.c('card_border'))
        tile.grid(row=i//3,column=i%3,sticky='ew',padx=(0 if i%3==0 else 6,0),pady=(0 if i<3 else 5,0))
        b=flat_button(tile,app.T(key),lambda index=i:app.apply_preset(__import__('quick_presets').spec(__import__('quick_presets').get(app.cfg)[index])),kind='normal',font=theme.font(delta=-1),padx=2,pady=5)
        b.config(image=icon(app,names[i],20),compound='left',pady=5,
                 highlightthickness=0,highlightbackground=theme.c('card_border'))
        set_icon(app,b,names[i],17)
        b._skin_opacity=0
        b._skin_border=False
        b.pack(fill='both',expand=True,padx=0,pady=0);app.preset_btns[key]=b
    app._refresh_preset_labels()
    # 隐藏重复的「执行方式」标题，保留三个常显页签。
    for c in app.mode_bar.winfo_children():
        if isinstance(c,tk.Label):c.pack_forget()
    app.mode_bar.pack_configure(pady=(0,0))
    app.mode_btn_row.pack_configure(pady=0)
    app.mode_indicators={}
    for col,(mode,b) in enumerate(app.mode_btns.items()):
        b.config(font=theme.font(delta=-1),pady=6,compound='left')
        set_icon(app,b,'clock',17)
        b._skin_opacity=0
        b.grid_configure(padx=0)
        line=tk.Frame(app.mode_btn_row,height=2,bg=theme.c('card_border'))
        app.mode_indicators[mode]=line
    app.time_inputs={}
    from ui_main_time import NumberInput, WeekdayInput
    for mode,group in app.time_groups.items():
        group.config(highlightthickness=0)
        for c in group.winfo_children():
            if isinstance(c,tk.Label):c.pack_forget()
            else:
                c.pack_configure(padx=4,pady=(6,8))
                cols=max(int(w.grid_info().get('column',0)) for w in c.winfo_children())+1
                for col in range(cols):
                    # The weekday needs three large glyphs; do not multiply its width
                    # across all four columns. Numeric columns share remaining space.
                    c.columnconfigure(col,weight=0 if mode=='datetime' and col==0 else 1,uniform='' if mode=='datetime' and col==0 else 'time_'+mode)
                fields=[]
                for w in list(c.winfo_children()):
                    w.grid_configure(sticky='ew',padx=2)
                    if isinstance(w,tk.Label):
                        labels={'天数':'天','小时数':'时','分钟数':'分','秒数':'秒'}
                        w.configure(anchor='center',text=labels.get(str(w.cget('text')),w.cget('text')))
                    elif w is app.weekday_box:
                        info=w.grid_info();values=list(w.cget('values'));index=w.current();w.destroy()
                        field=WeekdayInput(c,app,values,app.weekday_var);field.current(index)
                        field.grid(**{k:v for k,v in info.items() if k!='in'});app.weekday_box=field;fields.append(field)
                    elif isinstance(w,ttk.Spinbox) or (isinstance(w,ttk.Combobox) and str(w.cget('textvariable'))==str(app.cd_days)):
                        info=w.grid_info();variable=next(v for v in (app.cd_days,app.cd_h,app.cd_m,app.cd_s,app.dt_h,app.dt_m,app.dt_s,app.iv_h,app.iv_m,app.iv_s) if str(v)==str(w.cget('textvariable')))
                        maximum=int(float(w.cget('to'))) if isinstance(w,ttk.Spinbox) else 60
                        w.destroy();field=NumberInput(c,variable,maximum)
                        field.grid(**{k:v for k,v in info.items() if k!='in'});fields.append(field)
                app.time_inputs[mode]=fields
    # Keep all three input surfaces mapped and prepainted in a fixed-height stack.
    # Switching only raises a surface; no pack/unpack or delayed blank background.
    app.root.update_idletasks()
    groups=list(app.time_groups.values())
    height=max(g.winfo_reqheight() for g in groups)
    app.time_stack=tk.Frame(panel,bg=theme.c('card'),height=height)
    app.time_stack.pack(fill='x',before=gp,pady=(0,4))
    app.time_stack.grid_propagate(False)
    app.time_stack.columnconfigure(0,weight=1);app.time_stack.rowconfigure(0,weight=1)
    for group in groups:
        group.pack_forget();group.grid(in_=app.time_stack,row=0,column=0,sticky='nsew')
    app.time_stack.configure(width=max(g.winfo_reqwidth() for g in groups))
    # A full-width primary action, with four equal secondary actions below.
    app.btn_clear.grid_forget()
    app.btn_start.grid_configure(row=0,column=0,columnspan=4,padx=0,pady=(0,5))
    app.btn_start._soft_primary=True
    app.btn_start._kind='outline'
    app.btn_start._skin_opacity=0
    app.btn_start._bg=theme.c('card');app.btn_start._fg=theme.accent
    app.btn_start.config(bg=theme.c('card'),fg=theme.accent,compound='left',font=theme.font(delta=2,bold=True),pady=5)
    set_icon(app,app.btn_start,'play',19)
    app.btn_now=flat_button(app.time_btn_row,app.T('btn_now'),app.perform_now,kind='normal',font=theme.font(delta=-2),padx=2,pady=5)
    for col,(button,name) in enumerate(((app.btn_enqueue,'enqueue'),(app.btn_pause,'pause'),(app.btn_stop,'stop'),(app.btn_now,'bolt'))):
        button.grid(row=1,column=col,columnspan=1,sticky='ew',padx=(0 if col==0 else 5,0),pady=0)
        button._skin_opacity=0
        button.config(image=icon(app,name,16),compound='left',font=theme.font(delta=-2),pady=5,padx=2)
        set_icon(app,button,name,16)
    app.btn_enqueue.config(text='加入队列')
    app.btn_now.config(text='立即执行')
    app.time_btn_row.config(bg=theme.c('card'))
    app.time_spacer.pack_forget()
    app._refresh_mode_btns();app._refresh_time_groups()


def paint_modes(app):
    for mode,b in getattr(app,'mode_btns',{}).items():
        selected=mode==app.mode_var.get()
        bg=theme.c('card'); fg=theme.accent if selected else theme.c('fg')
        b._kind='plain'
        from ui_cozy import cozy_icon,scale
        b._theme_photo=cozy_icon(app.root,'clock',round(17*scale(app.root)),ink=fg)
        b.config(image=b._theme_photo)
        b.config(bg=bg,fg=fg,highlightbackground=theme.c('card_border'))
        b._bg=bg;b._fg=fg;b._border=theme.c('card_border')
        if mode in getattr(app,'mode_indicators',{}):
            app.mode_indicators[mode].config(bg=theme.accent if selected else theme.c('card_border'))


def build_footer(app,parent):
    from ui_summary import build
    build(app,parent)


def measure(app):
    from ui_cozy import scale
    # Time surfaces stay mapped in a fixed stack, so their natural requests
    # already cover all modes. Avoid widest-label * 2 plus arbitrary reserves.
    app.root.update_idletasks()
    width=max(round(426*scale(app.root)),app.root.winfo_reqwidth())
    return width,app.root.winfo_reqheight()


def build_ui(app):
    from ui_titlebar import build
    build(app)
    app.container=tk.Frame(app.root,bg=theme.c('bg'));app.container.pack(fill='both',padx=8,pady=(6,8))
    app.time_stack=None
    app.time_groups={};app.nav_btns={};app.mode_indicators={}
    app.mode_var=tk.StringVar(value=app.cfg.get('mode') or 'countdown')
    app.mid=tk.Frame(app.container,bg=theme.c('bg'));app.mid.pack(fill='x')
    app.content_area=tk.Frame(app.mid,bg=theme.c('bg'));app.content_area.pack(fill='x')
    app.footer=tk.Frame(app.container,bg=theme.c('bg'));app.footer.pack(fill='x')
    app.root.unbind('<MouseWheel>')
    app.pages={key:CozyFrame(app.content_area,bg=theme.c('card')) for key in ('actions','time')}
    for frame in app.pages.values():frame.pack(fill='x',pady=(0,8),ipadx=4)
    app._build_actions(app.pages['actions']);app._build_timer_panel(app.pages['time'])
    app._build_footer(app.footer);app._page_key='time'
    app.root.minsize(1,1);app.root.maxsize(10000,10000)
    w,h=app._measure_window_size();app.root.geometry(f'{w}x{h}')
    app.root.minsize(w,h);app.root.maxsize(w,h);app.root.resizable(False,False);app._lock_window_buttons()
    def settle_size():
        app.root.update();app.root.update_idletasks()
        width=app.root.winfo_width();height=app.root.winfo_reqheight()
        app.root.minsize(1,1);app.root.maxsize(10000,10000)
        app.root.geometry(f'{width}x{height}');app.root.update_idletasks()
        # Tk still budgets the native caption/frame removed by apply_chrome.
        # Measure that offset and compensate so client content ends at the footer.
        request_w=width-(app.root.winfo_width()-width)
        request_h=height-(app.root.winfo_height()-height)
        app.root.geometry(f'{request_w}x{request_h}')
        app.root.minsize(request_w,request_h);app.root.maxsize(request_w,request_h)
        app.root.update_idletasks();app._lock_window_buttons()
    app._settle_fixed_main=settle_size
    if not getattr(app,'_ui_built_once',False):app._ui_built_once=True;app._apply_start_hidden()
    if not app.cli.get('minimized') and not app.cli_help_only:app.show_window()


def show_page(app,key):
    app._page_key=app._prev_page_key=key
    # 两个步骤始终可见，兼容原业务调用。
    if key=='time':app.root.after(30,app._focus_first_time_widget)
