"""Direct shortcut recording, draft feedback and non-destructive availability checks."""
import ctypes
import tkinter as tk
from theme import theme,flat_button
from ui_dialog_palette import COLORS as C
from ui_settings_controls import Switch
from desktop_services import parse_hotkey

KINDS=(('show','唤出主窗口'),('pause','暂停当前定时'),('resume','继续当前定时'),('floating','开启／关闭悬浮倒计时'))
DEFAULTS=dict(show='Ctrl+Alt+H',pause='Ctrl+Alt+P',resume='Ctrl+Alt+R',floating='Ctrl+Alt+F')

class Recorder(tk.Canvas):
    def __init__(self,parent,panel,kind):
        self.panel,self.kind=panel,kind;self.variable=panel.owner.v['hotkey_'+kind];self.s=panel.owner.s
        super().__init__(parent,width=round(174*self.s),height=round(32*self.s),bg=C['card'],highlightthickness=0,takefocus=True,cursor='hand2')
        self.bind('<Button-1>',lambda e:self.focus_set());self.bind('<FocusIn>',self.begin)
        self.bind('<FocusOut>',lambda e:panel.end_capture());self.bind('<KeyPress>',self.record)
        self.bind('<Configure>',lambda e:self.draw());self.trace=self.variable.trace_add('write',lambda *a:self.draw())
        self.bind('<Destroy>',lambda e:self.variable.trace_remove('write',self.trace) if e.widget is self else None)
        self.draw()
    def begin(self,e=None):
        self.panel.begin_capture(self);self.draw()
    def draw(self):
        self.delete('all');s=self.s;parts=self.variable.get().split('+');w=max(round(174*s),self.winfo_width());h=round(32*s)
        if self.panel.active is self:self.create_rectangle(1,1,w-2,h-2,outline=theme.accent,width=1)
        widths=[max(28,len(x)*6+12)*s for x in parts];x=max(5*s,(w-sum(widths)-(len(parts)-1)*4*s)/2)
        for part,width in zip(parts,widths):
            self.rounded(x,5*s,x+width,h-5*s,4*s,C['hover'])
            self.create_text(x+width/2,h/2,text=part,font=theme.font(delta=-2),fill=C['fg']);x+=width+4*s
    def rounded(self,x,y,x2,y2,r,color):
        self.create_polygon(x+r,y,x2-r,y,x2,y,x2,y+r,x2,y2-r,x2,y2,x2-r,y2,x+r,y2,x,y2,x,y2-r,x,y+r,x,y,smooth=True,fill=color,outline='')
    def record(self,e):
        if e.keysym in ('Tab','ISO_Left_Tab'):return None
        if e.keysym=='Escape':self.panel.owner.focus_set();return 'break'
        key=e.keysym.upper()
        code=getattr(e,'keycode',0)
        if 48<=code<=57 or 65<=code<=90:key=chr(code)
        elif 112<=code<=123:key='F'+str(code-111)
        if key in ('CONTROL_L','CONTROL_R','ALT_L','ALT_R','SHIFT_L','SHIFT_R'):return 'break'
        if len(key)!=1 and key not in ['F'+str(n) for n in range(1,13)]:return 'break'
        # Tk uses different Alt masks on Windows; async state also handles AltGr.
        u=ctypes.windll.user32
        mods=[name for name,mask,vk in [('Ctrl',4,0x11),('Alt',0x20008,0x12),('Shift',1,0x10)] if e.state&mask or u.GetAsyncKeyState(vk)&0x8000]
        value='+'.join(mods+[key])
        try:parse_hotkey(value)
        except ValueError:
            self.panel.hint.config(text=self.panel.owner.tr('快捷键至少包含Ctrl或Alt'));return 'break'
        self.variable.set(value);self.panel.owner.focus_set();return 'break'

class HotkeyPanel:
    def __init__(self,owner,pad):
        self.owner=owner;self.active=None;self.recorders={};self.states={};self.checked={}
        g=owner._card(pad,'全局快捷键');owner._check(g,'hotkeys_enabled','启用全局快捷键')
        self.hint=owner._lab(g,'点击组合键框后，直接按下新的快捷键',fg=C['muted'],font=theme.font(delta=-2),wraplength=400);self.hint.pack(fill='x',pady=(0,8))
        for kind,name in KINDS:
            row=tk.Frame(g,bg=C['card']);row.pack(fill='x',pady=4)
            row.columnconfigure(0,weight=1)
            owner._lab(row,name,width=1,wraplength=round(140*owner.s),font=theme.font(delta=-1)).grid(row=0,column=0,sticky='ew')
            recorder=Recorder(row,self,kind);recorder.grid(row=0,column=1,padx=round(4*owner.s));self.recorders[kind]=recorder
            state=owner._lab(row,'',font=theme.font(delta=-2),width=8,anchor='center');state.grid(row=0,column=2);self.states[kind]=state
        owner._lab(g,'支持 Ctrl、Alt、Shift + 字母／数字／F1～F12',wraplength=480,fg=C['muted'],font=theme.font(delta=-2)).pack(fill='x',pady=(9,3))
        flat_button(g,owner.tr('恢复默认快捷键'),self.reset,padx=8,pady=4).pack(anchor='e')
        self.details=owner._card(pad,'修改明细');self.detail_label=owner._lab(self.details,'',wraplength=500,font=theme.font(delta=-1));self.detail_label.pack(fill='x',pady=5)
        self.refresh()
    def begin_capture(self,recorder):
        self.end_capture()
        service=self.owner.app.desktop
        try:
            if service.hotkeys:service.hotkeys.configure({})
            service.capturing=True;self.active=recorder
        except (ValueError,OSError):
            self.hint.config(text=self.owner.tr('快捷键注册线程无响应'))
    def end_capture(self):
        if self.active is None:return
        old=self.active;self.active=None;service=self.owner.app.desktop;service.capturing=False
        try:service.apply()
        except (ValueError,OSError) as exc:service.error=str(exc)
        if old.winfo_exists():old.draw()
        self.checked.clear();self.refresh()
    def available(self,combo):
        if combo in self.checked:return self.checked[combo]
        service=self.owner.app.desktop
        if service.hotkeys and combo in service.hotkeys.mapping.values():return True
        u=ctypes.windll.user32
        ok=bool(u.RegisterHotKey(None,0x4B12,*combo))
        if ok:u.UnregisterHotKey(None,0x4B12)
        self.checked[combo]=ok;return ok
    def refresh(self):
        self.checked.clear()
        o=self.owner;values={k:o.v['hotkey_'+k].get() for k,_ in KINDS};parsed={}
        for k,v in values.items():
            try:parsed[k]=parse_hotkey(v)
            except ValueError:parsed[k]=None
        lines=[];enabled=o.v['hotkeys_enabled'].get();manager=o.app.desktop.hotkeys
        for kind,name in KINDS:
            changed=values[kind]!=o._baseline.get('hotkey_'+kind,values[kind]) if hasattr(o,'_baseline') else False
            combo=parsed[kind]
            duplicate=combo is not None and list(parsed.values()).count(combo)>1
            occupied=combo is not None and not duplicate and not self.available(combo)
            registered=enabled and not changed and bool(manager and manager.mapping.get(kind)==combo)
            state='格式无效' if combo is None else '重复快捷键' if duplicate else '被占用' if occupied else '已注册' if registered else '待保存' if changed or enabled!=o.cfg.get('hotkeys_enabled') else '未启用'
            self.states[kind].config(text=o.tr(state),fg='#AD4061' if duplicate or occupied or combo is None else C['muted'] if registered or not enabled else theme.accent)
            if changed:lines.append(o.tr(name)+'\n'+o._baseline['hotkey_'+kind]+'   →   '+values[kind])
        self.detail_label.config(text='\n\n'.join(lines) if lines else o.tr('暂无快捷键修改'))
    def reset(self):
        self.end_capture();self.checked.clear()
        for kind,value in DEFAULTS.items():self.owner.v['hotkey_'+kind].set(value)
