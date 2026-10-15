"""原控件内切换语言：不销毁窗口、不修改引擎、不使用窗口透明动画。"""
import re
import string
import tkinter as tk
from tkinter import ttk
from i18n import _TEXTS,FEATURE_EN,Texts,feature_text,weekday_names,language_desc,LANGUAGE_FILES,AUTHOR
from translations160 import EN

def translate(text,old,new):
    if not isinstance(text,str) or not text:return text
    left=text[:len(text)-len(text.lstrip())];right=text[len(text.rstrip()):];value=text.strip()
    for key,source in _TEXTS[old].items():
        if value==source:return left+_TEXTS[new].get(key,source)+right
    source_T=Texts(old);target_T=Texts(new)
    for source in set(FEATURE_EN)|set(EN):
        if value==feature_text(source_T,source):return left+feature_text(target_T,source)+right
    # 已格式化的状态/标题，变量值继续做静态翻译（例如操作名称）。
    for key,source in _TEXTS[old].items():
        if '{' not in source:continue
        fields=[];pieces=[]
        try:
            for literal,field,fmt,conv in string.Formatter().parse(source):
                pieces.append(re.escape(literal))
                if field:fields.append(field);pieces.append('(.*?)')
            match=re.fullmatch(''.join(pieces),value,flags=re.S)
            if match:
                kw={key:translate(val,old,new) for key,val in zip(fields,match.groups())}
                return left+target_T(key,**kw)+right
        except (ValueError,KeyError):pass
    return text

def walk(widget):
    yield widget
    for child in widget.winfo_children():yield from walk(child)

def update_app(app,old):
    new=app.T.lang
    log_kinds={w:w.kind_values.get(w.kind.get(),'') for w in walk(app.root) if isinstance(w,tk.Toplevel) and hasattr(w,'kind_values')}
    for widget in walk(app.root):
        options=widget.configure()
        if isinstance(widget,(tk.Entry,ttk.Entry,tk.Text)):continue
        if isinstance(widget,(tk.Tk,tk.Toplevel)):widget.title(translate(widget.title(),old,new))
        if 'text' in options and not getattr(widget,'_user_text',False):
            value=str(widget.cget('text'));changed=translate(value,old,new)
            if value!=changed:widget.configure(text=changed)
        if isinstance(widget,ttk.Combobox):
            index=widget.current();values=widget.cget('values');widget.configure(values=[translate(str(x),old,new) for x in values])
            if index>=0:widget.current(index)
        if isinstance(widget,ttk.Treeview):
            for col in widget.cget('columns'):widget.heading(col,text=translate(widget.heading(col,'text'),old,new))
            if widget.cget('show')==('tree',) or str(widget.cget('show'))=='tree':
                for iid in widget.get_children():widget.item(iid,text=translate(widget.item(iid,'text'),old,new))
        if isinstance(widget,ttk.Notebook) and hasattr(widget,'_local_tab_keys'):
            for tab,key in widget._local_tab_keys.items():widget.tab(tab,text=app.T(key))
        if isinstance(widget,tk.Menu):
            end=widget.index('end')
            for idx in range((end+1) if end is not None else 0):
                if widget.type(idx) not in ('separator','tearoff'):widget.entryconfigure(idx,label=translate(widget.entrycget(idx,'label'),old,new))
    app.root.title(app.T('app_name'))
    index=app.weekday_box.current();app.weekday_box.configure(values=weekday_names(new));app.weekday_box.current(max(0,index))
    status_key,status_kw=app._status_key
    status_kw={k:translate(v,old,new) if isinstance(v,str) else v for k,v in status_kw.items()}
    app._refresh_preset_labels();app._set_status(status_key,**status_kw);app._set_running_ui(app.engine.is_running())
    settings=getattr(app,'_settings_win',None)
    if settings and settings.winfo_exists():
        if hasattr(settings,'retranslate'):settings.retranslate(app.T)
        nav_keys={'general':'set_general','display':'set_display','other':'set_other','tasks':'set_tasks','backup':'set_backup','pc':'pc_title','floating':'float_title'}
        for key in settings.nav.get_children() if not hasattr(settings,'retranslate') else ():
            text=app.T(nav_keys[key]) if key in nav_keys else feature_text(app.T,'自动化与预览' if key=='automation' else '快捷键与通知')
            settings.nav.item(key,text='  '+text)
        for item in LANGUAGE_FILES if hasattr(settings,'lang_tree') else ():settings.lang_tree.item(item['code'],values=(language_desc(item['code'],new),item['file'],AUTHOR))
    for log,code in log_kinds.items():
        from ui_log import KIND_KEYS
        log.kind_values={feature_text(app.T,'全部'):''};log.kind_values.update({app.T(v):k for k,v in KIND_KEYS.items()})
        log.kind.set(next(text for text,value in log.kind_values.items() if value==code))
    for widget in list(walk(app.root)):
        if isinstance(widget,tk.Toplevel):
            if hasattr(widget,'refresh_status'):widget.refresh_status()
            elif hasattr(widget,'refresh') and widget is not settings:widget.refresh()

class LocalDialogs:
    def __getattr__(self,name):
        from ui_messagebox import invoke
        def call(title=None,message=None,**kwargs):
            parent=kwargs.get('parent');T=None
            if parent:
                win=parent.winfo_toplevel();T=getattr(win,'T',None) or getattr(getattr(win,'app',None),'T',None) or getattr(getattr(win,'_theme_owner',None),'T',None)
            if T:
                title=translate(str(title or ''),'CHS',T.lang);message=translate(str(message or ''),'CHS',T.lang)
                title=feature_text(T,title);message=feature_text(T,message)
            return invoke(name,title,message,**kwargs)
        return call
messagebox=LocalDialogs()
