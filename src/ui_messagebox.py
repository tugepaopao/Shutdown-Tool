"""Violet message prompts with Tk-compatible results and nested modal ownership."""
import tkinter as tk
from theme import theme
from ui_window import prepare,show,button_grid,text_rows,content_show
from ui_dialog_palette import COLORS

_CHOICES={
    'showinfo':(('ok',), 'ok'), 'showwarning':(('ok',),'ok'), 'showerror':(('ok',),'ok'),
    'askyesno':(('yes','no'),'no'), 'askquestion':(('yes','no'),'no'),
    'askokcancel':(('ok','cancel'),'cancel'), 'askretrycancel':(('retry','cancel'),'cancel'),
    'askyesnocancel':(('yes','no','cancel'),'cancel'),
}
_LABELS={
    'CHS':dict(ok='确定',cancel='取消',yes='是',no='否',retry='重试'),
    'CHT':dict(ok='確定',cancel='取消',yes='是',no='否',retry='重試'),
    'EN':dict(ok='OK',cancel='Cancel',yes='Yes',no='No',retry='Retry'),
}

class MessageDialog(tk.Toplevel):
    def __init__(self,parent,title,message,kind,default=None,detail=None,labels=None):
        owner=parent.winfo_toplevel()
        super().__init__(owner);prepare(self)
        self.T=getattr(owner,'T',None) or getattr(getattr(owner,'app',None),'T',None) or getattr(getattr(owner._root(),'_theme_owner',None),'T',None)
        self.choices,self.result=_CHOICES[kind]
        self.title(str(title or ''));self.transient(owner);self.resizable(False,False)
        self.configure(bg=COLORS['bg'],highlightthickness=1,highlightbackground=COLORS['border'])
        from ui_cozy import scale
        s=scale(self)
        body=tk.Frame(self,bg=COLORS['bg']);body.pack(fill='both',expand=True,padx=round(18*s),pady=(round(12*s),round(14*s)))
        text=str(message or '')+ ('\n\n'+str(detail) if detail else '')
        rows=text_rows(self,text,round(310*s),theme.font(),maximum=11)
        if rows>=11:
            from tkinter import ttk
            box=tk.Frame(body,bg=COLORS['bg']);box.pack(side='left',fill='both',expand=True)
            content=tk.Text(box,wrap='word',width=1,height=10,font=theme.font(),bg=COLORS['bg'],fg=COLORS['fg'],bd=0,highlightthickness=0)
            scroll=ttk.Scrollbar(box,command=content.yview);scroll.pack(side='right',fill='y');content.config(yscrollcommand=scroll.set);content.pack(fill='both',expand=True)
            content.insert('1.0',text);content.config(state='disabled')
        else:
            headline,separator,description=text.partition('\n')
            tk.Label(body,text=headline,bg=COLORS['bg'],fg=COLORS['fg'],font=theme.font(bold=bool(separator)),justify='left',anchor='w',wraplength=round(330*s)).pack(fill='x',pady=(0,round(6*s)) if separator else 0)
            if separator:
                tk.Label(body,text=description.strip(),bg=COLORS['bg'],fg=COLORS['muted'],font=theme.font(delta=-1),justify='left',anchor='w',wraplength=round(330*s)).pack(fill='x')
        bar=tk.Frame(self,bg=COLORS['bg']);bar.pack(fill='x',padx=12,pady=(0,12))
        supplied=labels
        labels=dict(_LABELS.get(getattr(self.T,'lang','CHS'),_LABELS['CHS']))
        if supplied:
            from i18n import feature_text
            labels.update({k:feature_text(self.T,v) for k,v in supplied.items()})
        actions=tk.Frame(bar,bg=COLORS['bg']);actions.pack(side='right')
        self.buttons=button_grid(actions,[(labels[key],lambda value=key:self.choose(value),'accent' if key in ('ok','yes','retry') else 'normal') for key in self.choices])
        self.protocol('WM_DELETE_WINDOW',self.destroy)
        self.bind('<Escape>',lambda e:self.dismiss())
        chosen=default if default in self.choices else self.choices[0]
        self.bind('<Return>',lambda e:self.choose(chosen))
        self.update_idletasks()
        width=max(self.winfo_reqwidth(),round((370 if rows>=11 else 280)*s));height=self.winfo_reqheight()
        app=getattr(owner._root(),'_theme_owner',None)
        if app:
            content_show(self,app,width=width/s,min_height=110,max_height=380)
        else:
            from ui_floating import workareas,clamp_position
            x,y=clamp_position(owner.winfo_rootx(),owner.winfo_rooty(),width,height,workareas(owner))
            self.geometry(f'{width}x{height}{x:+d}{y:+d}');show(self)
        self.grab_set();self.buttons[self.choices.index(chosen)].focus_set();self._message_ready=True
    def choose(self,value):
        self.result=value;self.destroy();return 'break'
    def dismiss(self):
        self.destroy();return 'break'

def invoke(kind,title=None,message=None,**kwargs):
    if kind not in _CHOICES:raise AttributeError(kind)
    parent=kwargs.pop('parent',None) or tk._default_root
    temporary=None
    if parent is None:
        temporary=tk.Tk();temporary.withdraw();parent=temporary
    dialog=None
    try:
        dialog=MessageDialog(parent,title,message,kind,default=kwargs.get('default'),detail=kwargs.get('detail'),labels=kwargs.get('labels'))
        parent.wait_window(dialog);result=dialog.result
        if kind=='askyesnocancel':return None if result=='cancel' else result=='yes'
        if kind in ('askyesno','askokcancel','askretrycancel'):return result in ('yes','ok','retry')
        return result
    finally:
        if dialog is not None and dialog.winfo_exists():dialog.destroy()
        if temporary:temporary.destroy()
