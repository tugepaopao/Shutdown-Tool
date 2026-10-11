"""先完成布局和原生标题栏，再一次性显示；统一弹窗按钮网格。"""
import ctypes
import tkinter as tk
from theme import theme, flat_button


def _main_opacity(window, alpha):
    """只改变本窗口的呈现，不修改 Windows 全局动画设置。"""
    try:
        u=ctypes.windll.user32
        # Tk 初建时 winfo_id 是客户区子窗口，外层窗口尚未创建。
        # 此时 GetAncestor 会返回自身；给它设 alpha=0 会留下不可点击的
        # 透明客户区，即使随后把外层窗口设为 255 也不能恢复鼠标命中。
        # 只处理已存在的顶层外框；withdraw 阶段不需要透明遮挡。
        u.GetAncestor.argtypes=[ctypes.c_void_p,ctypes.c_uint]
        u.GetAncestor.restype=ctypes.c_void_p
        client=window.winfo_id()
        hwnd=u.GetAncestor(client,2)
        if not hwnd or hwnd==client:
            return False
        u.GetWindowLongW.argtypes=[ctypes.c_void_p,ctypes.c_int]
        u.GetWindowLongW.restype=ctypes.c_long
        u.SetWindowLongW.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_long]
        u.SetWindowLongW.restype=ctypes.c_long
        if u.GetWindowLongW(ctypes.c_void_p(hwnd),-16) & 0x40000000:
            return False  # WS_CHILD 永远不用于主窗口呈现层。
        style=u.GetWindowLongW(ctypes.c_void_p(hwnd),-20)
        if alpha==255:
            # Return to an opaque native window after the hidden restore paint.
            # Keeping WS_EX_LAYERED on a fully opaque Tk window breaks GDI
            # move-copy on some multi-monitor drivers.
            if style & 0x80000:u.SetWindowLongW(ctypes.c_void_p(hwnd),-20,style & ~0x80000)
            window._main_opacity=255
            u.RedrawWindow(ctypes.c_void_p(hwnd),None,None,0x185)
            return True
        if not style & 0x80000:
            u.SetWindowLongW(ctypes.c_void_p(hwnd),-20,style|0x80000)
        ok=u.SetLayeredWindowAttributes(ctypes.c_void_p(hwnd),0,alpha,2)
        window._main_opacity=alpha if ok else None
        return bool(ok)
    except (AttributeError,tk.TclError,OSError):
        return False


def prepare_main(window):
    """主窗口先在不可见合成层完成绘制，再一次显示完整内容。"""
    window._main_presenting=False
    window._main_present_after=None
    def unmap(event):
        if event.widget is window:_main_opacity(window,0)
    def mapped(event):
        if event.widget is not window:return
        _main_opacity(window,0)
        if window._main_present_after is None:
            window._main_present_after=window.after_idle(lambda:present_main(window))
    window.bind('<Unmap>',unmap,add='+')
    window.bind('<Map>',mapped,add='+')
    _main_opacity(window,0)


def present_main(window):
    window._main_present_after=None
    if window._main_presenting or not window.winfo_exists() or window.state()!='normal':return
    window._main_presenting=True
    try:
        disable_native_animation(window)
        u=ctypes.windll.user32
        hwnd=u.GetAncestor(window.winfo_id(),2) or window.winfo_id()
        u.RedrawWindow(ctypes.c_void_p(hwnd),None,None,0x185)
        # update_idletasks 不处理所有原生 WM_PAINT；必须排空实际窗口事件。
        # 重入由 _main_presenting 隔离，期间计时与正常事件继续处理。
        window.update()
        window.update_idletasks()
    except (AttributeError,tk.TclError,OSError):
        pass
    finally:
        window._main_presenting=False
        try:
            if window.winfo_exists() and window.state()=='normal':
                if not _main_opacity(window,255):
                    window.attributes('-alpha',1.0)
        except tk.TclError:
            pass


def prepare(window):
    window.withdraw()
    window.configure(bg=theme.c('bg'))
    def mapped(event):
        if event.widget is not window:return
        owner=getattr(window._root(),'_theme_owner',None)
        if owner:
            # Tk 在父窗口重显时可能重建 transient 外层窗口。
            def reapply():
                if not window.winfo_exists():return
                disable_native_animation(window)
                owner._apply_dark_titlebar(window)
            window.after_idle(reapply)
    window.bind('<Map>',mapped,add='+')


def disable_native_animation(window):
    """仅本程序窗口禁用 DWM 过渡；主窗口另有完整绘制呈现流程。"""
    try:
        window.update_idletasks()
        u=ctypes.windll.user32
        hwnd=u.GetAncestor(window.winfo_id(),2) or window.winfo_id()
        value=ctypes.c_int(1)
        rc=ctypes.windll.dwmapi.DwmSetWindowAttribute(
            ctypes.c_void_p(hwnd),3,ctypes.byref(value),ctypes.sizeof(value))
        window._native_animation_disabled=(rc==0 and value.value==1)
        window._native_animation_configured=(rc==0)
        window._native_animation_hwnd=hwnd
    except (AttributeError,tk.TclError,OSError):
        window._native_animation_disabled=False


def show(window):
    if window is window._root() and window.state()!='normal':
        _main_opacity(window,0)
    window.update_idletasks()
    owner=getattr(window._root(),'_theme_owner',None)
    if owner:
        owner._apply_icon(window)
        window.update_idletasks()
        disable_native_animation(window)
        owner._apply_dark_titlebar(window)
    window.deiconify()


def button_grid(parent,items,columns=None):
    """items: (文字, 回调, 风格)，组内等宽等高；返回按钮以保留业务引用。"""
    columns=columns or len(items)
    buttons=[]
    for col in range(columns):parent.columnconfigure(col,weight=1,uniform='actions')
    for index,(text,command,kind) in enumerate(items):
        row,col=divmod(index,columns)
        parent.rowconfigure(row,weight=1,uniform='actions')
        btn=flat_button(parent,text,command,kind=kind,font=theme.font(delta=-1),padx=8,pady=6)
        btn.grid(row=row,column=col,sticky='nsew',padx=3,pady=3 if len(items)>columns else 0)
        buttons.append(btn)
    parent._action_buttons=buttons
    return buttons
