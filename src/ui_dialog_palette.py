"""Cool violet surfaces shared by ordinary dialogs and the gear menu."""
import tkinter as tk
from tkinter import ttk
from theme import theme
from ui_cozy import CozyGroup,scale

COLORS={'bg':'#E3DFF7','card':'#F2F0FC','input':'#F8F7FF','fg':'#302454','muted':'#736C92','hover':'#DAD2F7','selected':'#CDC0EF','border':'#B9ABE1','menu':'#EBE6FC'}

def apply(window, subtree=None):
    if window is window._root() or not getattr(window,'_violet_dialog',False):return
    source=theme.p
    roles={'bg':'bg','header_bg':'bg','card':'card','nav_bg':'card','sel_row_bg':'selected','hover':'hover','nav_active_bg':'selected','nav_hover_bg':'hover','input_bg':'input','fg':'fg','input_fg':'fg','fg_dim':'muted','fg_muted':'muted','nav_fg':'muted','head_fg':'muted','border':'border','card_border':'border','divider':'border','head_bg':'card'}
    mapping={source[k]:COLORS[v] for k,v in roles.items() if k in source}
    style=ttk.Style(window);prefix='Violet'+str(window.winfo_id())+'.';window.configure(bg=COLORS['bg'],bd=0,highlightthickness=0)
    def walk(w):
        yield w
        for child in w.winfo_children():
            if not isinstance(child,tk.Toplevel):yield from walk(child)
    for widget in walk(subtree if subtree is not None else window):
        if isinstance(widget,CozyGroup):
            packed=widget.pack_slaves()
            if len(packed)>1:
                last=packed[-1];value=last.pack_info().get('pady',0);pads=tuple(value) if isinstance(value,(tuple,list)) else last.tk.splitlist(str(value))
                top=int(pads[0]);bottom=int(pads[-1]);inset=round(8*scale(widget))
                if bottom<inset:last.pack_configure(pady=(top,inset))
        if isinstance(widget,ttk.Widget):
            base=str(widget.cget('style')) or widget.winfo_class()
            if prefix in base:continue
            orientation=str(widget.cget('orient')).capitalize() if 'orient' in widget.keys() else ''
            if orientation and not base.startswith(orientation+'.'):base=orientation+'.'+base
            scoped=(orientation+'.'+prefix+base[len(orientation)+1:]) if orientation else prefix+base
            try:style.layout(scoped,style.layout(base))
            except tk.TclError:pass
            opts=dict(background=COLORS['bg'],foreground=COLORS['fg'],fieldbackground=COLORS['input'],bordercolor=COLORS['border'],lightcolor=COLORS['bg'],darkcolor=COLORS['bg'],troughcolor=COLORS['bg'],arrowcolor=COLORS['muted'])
            if isinstance(widget,ttk.Combobox):
                opts.update(selectbackground=COLORS['input'],selectforeground=COLORS['fg'])
                style.map(scoped,selectbackground=[('readonly',COLORS['input'])],selectforeground=[('readonly',COLORS['fg'])])
            if isinstance(widget,ttk.Scrollbar):
                # Retain native drag/page/keyboard behavior with a flat violet thumb.
                opts.update(background=COLORS['selected'],troughcolor=COLORS['card'],
                            bordercolor=COLORS['card'],lightcolor=COLORS['selected'],
                            darkcolor=COLORS['selected'],relief='flat',borderwidth=0)
                style.map(scoped,background=[('pressed',theme.accent),('active',COLORS['border'])],
                          lightcolor=[('pressed',theme.accent),('active',COLORS['border'])],
                          darkcolor=[('pressed',theme.accent),('active',COLORS['border'])])
            if isinstance(widget,ttk.Treeview):
                opts.update(background=COLORS['card'],fieldbackground=COLORS['card']);style.map(scoped,background=[('selected',COLORS['selected'])],foreground=[('selected',COLORS['fg'])]);style.configure(scoped+'.Heading',background=COLORS['card'],foreground=COLORS['muted'],bordercolor=COLORS['bg'],lightcolor=COLORS['card'],darkcolor=COLORS['card'],relief='flat')
            style.configure(scoped,**opts);widget.configure(style=scoped);continue
        options=widget.keys();kw={}
        for key in ('background','activebackground','selectcolor','foreground','insertbackground'):
            if key in options:
                value=str(widget.cget(key))
                if value in mapping and mapping[value]!=value:kw[key]=mapping[value]
        if 'highlightbackground' in options and int(str(widget.cget('highlightthickness'))) and str(widget.cget('highlightbackground'))!=COLORS['border']:kw['highlightbackground']=COLORS['border']
        if kw:widget.configure(**kw)
        if hasattr(widget,'_bg'):
            widget._bg=mapping.get(widget._bg,widget._bg);widget._hover=COLORS['hover']
        # Keep the existing painted surface when its size and colors match.
        if hasattr(widget,'_surface_key'):widget._round()
