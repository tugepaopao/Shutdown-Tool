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
        if alpha==255 and getattr(window,'_main_opacity',None)==255 and not style & 0x80000:
            return True
        if alpha==255:
            # Return to an opaque native window after the hidden restore paint.
            # Keeping WS_EX_LAYERED on a fully opaque Tk window breaks GDI
            # move-copy on some multi-monitor drivers.
            # Hide this one DWM surface while switching back to opaque GDI.
            # Native child controls must finish painting before the first frame.
            dwm=ctypes.windll.dwmapi;cloaked=ctypes.c_int(1)
            dwm.DwmSetWindowAttribute.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_void_p,ctypes.c_uint]
            hidden=dwm.DwmSetWindowAttribute(ctypes.c_void_p(hwnd),13,ctypes.byref(cloaked),4)==0
            try:
                if style & 0x80000:u.SetWindowLongW(ctypes.c_void_p(hwnd),-20,style & ~0x80000)
                window._main_opacity=255
                window.update_idletasks();u.RedrawWindow(ctypes.c_void_p(hwnd),None,None,0x185)
                if hidden:dwm.DwmFlush()
            finally:
                if hidden:
                    cloaked.value=0;dwm.DwmSetWindowAttribute(ctypes.c_void_p(hwnd),13,ctypes.byref(cloaked),4)
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
    window._main_ready=False
    window._main_presenting=False
    window._main_present_after=None
    def unmap(event):
        if event.widget is not window:return
        if not getattr(window,'_main_presented',False):_main_opacity(window,0)
        else:
            from ui_native_restore import hold
            hold(window)
    def mapped(event):
        if event.widget is not window:return
        if not getattr(window,'_main_presented',False):_main_opacity(window,0)
        if window._main_present_after is None:
            window._main_present_after=window.after_idle(lambda:present_main(window))
    window.bind('<Unmap>',unmap,add='+')
    window.bind('<Map>',mapped,add='+')
    _main_opacity(window,0)


def present_main(window):
    window._main_present_after=None
    if not getattr(window,'_main_ready',False) or window._main_presenting or not window.winfo_exists() or window.state()!='normal':return
    from ui_native_restore import install,pending
    if pending(window):
        window._main_present_after=window.after(10,lambda:present_main(window))
        return
    install(window)
    window._main_presenting=True
    renderer=getattr(window,'_skin_renderer',None)
    if renderer and renderer.active:
        renderer._hold=True
        if renderer.job:window.after_cancel(renderer.job);renderer.job=None
    try:
        disable_native_animation(window)
        u=ctypes.windll.user32
        renderer=getattr(window,'_skin_renderer',None)
        if renderer and renderer.active:
            renderer._restore_size();window.update_idletasks()
        hwnd=u.GetAncestor(window.winfo_id(),2) or window.winfo_id()
        if getattr(window,'_main_presented',False):
            # Child Map/paint events can arrive after the main Map event.
            # Drain them while presentation is held, guarded against reentry.
            window.update_idletasks();window.update();window.update_idletasks()
            if renderer and renderer.active:renderer.render()
            window.update_idletasks()
            return
        u.RedrawWindow(ctypes.c_void_p(hwnd),None,None,0x185)
        # update_idletasks 不处理所有原生 WM_PAINT；必须排空实际窗口事件。
        # 重入由 _main_presenting 隔离，期间计时与正常事件继续处理。
        window.update()
        window.update_idletasks()
        if renderer and renderer.active:renderer.render();window.update_idletasks()
    except (AttributeError,tk.TclError,OSError):
        pass
    finally:
        window._main_presenting=False
        if renderer and renderer.active:renderer._hold=False;renderer.schedule()
        try:
            if window.winfo_exists() and window.state()=='normal':
                if not _main_opacity(window,255):
                    window.attributes('-alpha',1.0)
                window._main_presented=True
                from ui_native_restore import finish_paint
                finish_paint(window)
        except tk.TclError:
            pass


def prepare(window, caption=True):
    window.withdraw()
    # Every nested dialog restores the previous live modal owner on destruction.
    previous=window.grab_current();focus=window.focus_get()
    status=previous.grab_status() if previous else None
    def restore_modal(event):
        if event.widget is not window:return
        try:
            current=window.grab_current()
            if current is window:window.grab_release()
            if current is None or current is window:
                if previous and previous.winfo_exists() and previous.winfo_viewable():
                    if status=="global":previous.grab_set_global()
                    else:previous.grab_set()
                if focus and focus.winfo_exists() and focus.winfo_viewable():focus.focus_set()
        except tk.TclError:pass
    window.bind("<Destroy>",restore_modal,add="+")
    window._violet_dialog=caption
    window._dialog_ready=False
    window._dialog_presenting=False
    window.configure(bg=theme.c('bg'))
    if caption:
        from ui_dialog_chrome import create
        create(window)
    def mapped(event):
        if event.widget is not window:return
        if caption:
            _main_opacity(window,0)
            window.after_idle(lambda:present_dialog(window))
        owner=getattr(window._root(),'_theme_owner',None)
        if owner:
            # Tk 在父窗口重显时可能重建 transient 外层窗口。
            def reapply():
                if not window.winfo_exists():return
                disable_native_animation(window)
                owner._apply_dark_titlebar(window)
                from ui_dialog_palette import apply
                apply(window)
            window.after_idle(reapply)
    window.bind('<Map>',mapped,add='+')


def disable_native_animation(window):
    """仅本程序窗口禁用 DWM 过渡；主窗口另有完整绘制呈现流程。"""
    try:
        u=ctypes.windll.user32
        hwnd=u.GetAncestor(window.winfo_id(),2) or window.winfo_id()
        if getattr(window,'_native_animation_configured',False) and getattr(window,'_native_animation_hwnd',None)==hwnd:return
        value=ctypes.c_int(1)
        rc=ctypes.windll.dwmapi.DwmSetWindowAttribute(
            ctypes.c_void_p(hwnd),3,ctypes.byref(value),ctypes.sizeof(value))
        window._native_animation_disabled=(rc==0 and value.value==1)
        window._native_animation_configured=(rc==0)
        window._native_animation_hwnd=hwnd
    except (AttributeError,tk.TclError,OSError):
        window._native_animation_disabled=False


def show(window):
    # Already-mapped dialogs will not emit Map again. Never leave them at alpha 0.
    if getattr(window,'_dialog_ready',False) and getattr(window,'_violet_dialog',False) and window.winfo_viewable():
        present_dialog(window)
        return
    if window is window._root() and getattr(window,'_main_presented',False):
        window.deiconify();return
    if window is window._root() and window.state()!='normal':
        _main_opacity(window,0)
    window.update_idletasks()
    owner=getattr(window._root(),'_theme_owner',None)
    if owner:
        owner._apply_icon(window)
        window.update_idletasks()
        disable_native_animation(window)
        owner._apply_dark_titlebar(window)
    from ui_dialog_palette import apply
    apply(window)
    window._dialog_ready=True
    # Hide the already-created native wrapper before ShowWindow's first frame.
    # Map also repeats this when Tk recreates a transient wrapper.
    if getattr(window,'_violet_dialog',False):_main_opacity(window,0)
    window.deiconify()


def present_dialog(window):
    if not window.winfo_exists() or not window._dialog_ready or window._dialog_presenting:return
    window._dialog_presenting=True
    try:
        # Paint without dispatching another user command during construction.
        window.update_idletasks()
        _main_opacity(window,255)
    finally:window._dialog_presenting=False


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


def compact_show(window, app, height=520):
    """Opt-in auxiliary window bounds, matching settings without changing main UI."""
    from ui_cozy import scale
    from ui_floating import workareas, clamp_position
    from ctypes import wintypes as W
    s=scale(window);areas=workareas(window)
    cx,cy=app.root.winfo_rootx(),app.root.winfo_rooty()
    area=next((a for a in areas if a[0]<=cx<a[2] and a[1]<=cy<a[3]),areas[0])
    width=640 if app.T.lang=='EN' else 560
    size=(min(round(width*s),area[2]-area[0]-20),min(round(height*s),area[3]-area[1]-20))
    window._compact_size=size
    x,y=clamp_position(cx+25,cy+25,*size,areas)
    window.geometry(f'{size[0]}x{size[1]}+{x}+{y}')
    window.minsize(*size)
    show(window);window.update_idletasks()
    # Custom caption removes native borders after mapping; use final outer bounds.
    try:
        u=ctypes.windll.user32
        u.GetAncestor.argtypes=[W.HWND,W.UINT];u.GetAncestor.restype=W.HWND
        u.SetWindowPos.argtypes=[W.HWND,W.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,W.UINT]
        u.SetWindowPos(u.GetAncestor(window.winfo_id(),2),None,x,y,*size,0x14)
    except (AttributeError,OSError):pass


def wrap_to_width(label):
    """Keep auxiliary-window prose within its actual allocated width."""
    label.bind('<Configure>',lambda e:label.configure(wraplength=max(1,e.width-4)),add='+')
    return label


def activate_dialog(window):
    """Reuse an existing dialog and respect any currently active modal editor."""
    modal=window.grab_current()
    target=modal.winfo_toplevel() if modal is not None and modal.winfo_exists() else window
    show(target)
    target.update_idletasks()
    if getattr(target,'_violet_dialog',False):present_dialog(target)
    from ui_workspace import keep_visible
    keep_visible(target)
    target.lift()
    target.focus_set()
    return target
