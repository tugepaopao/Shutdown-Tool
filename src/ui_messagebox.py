"""Violet message prompts with Tk-compatible results and nested modal ownership."""
import tkinter as tk
from theme import theme
from ui_window import prepare,show,button_grid
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
        body=tk.Frame(self,bg=COLORS['card']);body.pack(fill='both',expand=True,padx=12,pady=(7,12))
        mark='?' if kind.startswith('ask') else '!' if kind in ('showerror','showwarning') else 'i'
        tk.Label(body,text=mark,bg=COLORS['card'],fg=theme.accent,font=theme.font(delta=9,bold=True),width=2).pack(side='left',anchor='n',padx=(10,4),pady=12)
        text=str(message or '')+ ('\n\n'+str(detail) if detail else '')
        tk.Label(body,text=text,bg=COLORS['card'],fg=COLORS['fg'],font=theme.font(),justify='left',anchor='w',wraplength=round(380*self.tk.call('tk','scaling')/(96/72))).pack(side='left',fill='both',expand=True,padx=(0,16),pady=16)
        bar=tk.Frame(self,bg=COLORS['bg']);bar.pack(fill='x',padx=12,pady=(0,12))
        supplied=labels
        labels=dict(_LABELS.get(getattr(self.T,'lang','CHS'),_LABELS['CHS']))
        if supplied:
            from i18n import feature_text
            labels.update({k:feature_text(self.T,v) for k,v in supplied.items()})
        self.buttons=button_grid(bar,[(labels[key],lambda value=key:self.choose(value),'accent' if key in ('ok','yes','retry') else 'normal') for key in self.choices])
        self.protocol('WM_DELETE_WINDOW',self.destroy)
        self.bind('<Escape>',lambda e:self.dismiss())
        chosen=default if default in self.choices else self.choices[0]
        self.bind('<Return>',lambda e:self.choose(chosen))
        self.update_idletasks()
        width=max(self.winfo_reqwidth(),round(320*self.tk.call('tk','scaling')/(96/72)));height=self.winfo_reqheight()
        x=max(0,owner.winfo_rootx()+(owner.winfo_width()-width)//2)
        y=max(0,owner.winfo_rooty()+(owner.winfo_height()-height)//2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        show(self);self.grab_set();self.buttons[self.choices.index(chosen)].focus_set();self._message_ready=True
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
