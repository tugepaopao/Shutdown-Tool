"""Theme-matched dialog captions, including Windows 10 without caption colors."""
import ctypes
import tkinter as tk
from ctypes import wintypes as W
from theme import theme, flat_button
from ui_cozy import cozy_icon, scale


def create(window):
    if getattr(window, '_dialog_caption', None) is not None: return
    bar = tk.Frame(window, bg=theme.c('bg'), bd=0)
    bar._theme_roles = {'background': 'bg'}
    bar.pack(side='top', fill='x')
    window._dialog_caption = bar
    icon = tk.Label(bar, bg=theme.c('bg'), bd=0)
    icon._theme_roles = {'background': 'bg'}
    icon.pack(side='left', padx=(12, 7), pady=7)
    title = tk.Label(bar, bg=theme.c('bg'), fg=theme.c('fg'), font=theme.font(bold=True), anchor='w')
    title._theme_roles = {'background': 'bg', 'foreground': 'fg'}
    title.pack(side='left', fill='x', expand=True)
    def close():
        command = window.protocol('WM_DELETE_WINDOW')
        if command: window.tk.call('eval', command)
        else: window.destroy()
    button = flat_button(bar, '', close, kind='ghost', padx=7, pady=5)
    button._theme_roles = {'background': 'bg', 'activebackground': 'hover', 'foreground': 'fg_dim', 'disabledforeground': 'disabled'}
    button.pack(side='right', padx=(7, 10), pady=3)
    window._dialog_icon = icon; window._dialog_title = title; window._dialog_close = button
    _bind_move_resize(window, (bar, icon, title))


def update(window):
    if getattr(window, '_dialog_caption', None) is None: return False
    if not window.winfo_exists(): return True
    window._dialog_caption.configure(bg=theme.c('bg'))
    window._dialog_title.configure(text=window.title(), bg=theme.c('bg'), fg=theme.c('fg'))
    stamp = (theme.accent, theme.c('bg'), theme.c('fg_dim'), round(22 * scale(window)))
    if getattr(window, '_dialog_icon_stamp', None) != stamp:
        window._dialog_icon_stamp = stamp
        icon = window._dialog_icon
        icon._theme_photo = cozy_icon(window, 'power_badge', stamp[3])
        icon.configure(image=icon._theme_photo, bg=theme.c('bg'))
        button = window._dialog_close
        button._theme_photo = cozy_icon(window, 'close', round(16 * scale(window)))
        button.configure(image=button._theme_photo, bg=theme.c('bg'), activebackground=theme.c('hover'), fg=theme.c('fg_dim'))
    _strip_caption(window)
    return True


def _strip_caption(window):
    try:
        u = ctypes.windll.user32
        u.GetAncestor.argtypes = [W.HWND, W.UINT]; u.GetAncestor.restype = W.HWND
        hwnd = u.GetAncestor(window.winfo_id(), 2)
        if not hwnd or hwnd == window.winfo_id(): return
        u.GetWindowLongW.argtypes = [W.HWND, ctypes.c_int]; u.GetWindowLongW.restype = ctypes.c_long
        u.SetWindowLongW.argtypes = [W.HWND, ctypes.c_int, ctypes.c_long]
        u.SetWindowPos.argtypes = [W.HWND, W.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, W.UINT]
        style = u.GetWindowLongW(hwnd, -16)
        # Preserve native ownership, keyboard close and taskbar rules.
        # Client resize edges match the existing main window's implementation.
        wanted = (style & ~0xC00000 & ~0x40000) | 0x80000
        if wanted != style:
            u.SetWindowLongW(hwnd, -16, wanted)
            u.SetWindowPos(hwnd, None, 0, 0, 0, 0, 0x37)
        window._dialog_chrome_hwnd = hwnd
    except (AttributeError, OSError, tk.TclError): pass


def _bind_move_resize(window, widgets):
    state = {'origin': None, 'pending': None, 'job': None, 'edge': ''}
    def rect():
        u = ctypes.windll.user32
        u.GetAncestor.argtypes = [W.HWND, W.UINT]; u.GetAncestor.restype = W.HWND
        hwnd = u.GetAncestor(window.winfo_id(), 2); r = W.RECT()
        u.GetWindowRect(W.HWND(hwnd), ctypes.byref(r))
        return hwnd, r.left, r.top, r.right-r.left, r.bottom-r.top
    def flush():
        state['job'] = None
        pending, state['pending'] = state['pending'], None
        if pending is None or not window.winfo_exists(): return
        hwnd, x, y, w, h = pending
        u = ctypes.windll.user32
        u.SetWindowPos.argtypes = [W.HWND, W.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, W.UINT]
        u.SetWindowPos(hwnd, None, x, y, w, h, 0x14 | (0x1 if not state['edge'] else 0))
    def begin(e, edge=''):
        state['origin'] = (e.x_root, e.y_root, *rect()); state['edge'] = edge
    def move(e):
        if state['origin'] is None: return
        mx, my, hwnd, x, y, w, h = state['origin']
        dx, dy, edge = e.x_root-mx, e.y_root-my, state['edge']
        if edge:
            minw, minh = window.minsize()
            if 'e' in edge: w = max(minw+2, w+dx)
            if 's' in edge: h = max(minh+2, h+dy)
            if 'w' in edge:
                nw = max(minw+2, w-dx); x += w-nw; w = nw
            if 'n' in edge:
                nh = max(minh+2, h-dy); y += h-nh; h = nh
        else: x += dx; y += dy
        state['pending'] = (hwnd, x, y, w, h)
        if state['job'] is None: state['job'] = window.after(16, flush)
    def end(e=None):
        # Commit the release position when Windows coalesces the last motion.
        if e is not None and state['origin'] is not None: move(e)
        if state['job'] is not None: window.after_cancel(state['job']); state['job'] = None
        if state['pending'] is not None: flush()
        state['origin'] = None; state['edge'] = ''
    for widget in widgets:
        widget.bind('<ButtonPress-1>', begin); widget.bind('<B1-Motion>', move); widget.bind('<ButtonRelease-1>', end)
    def edge_press(e):
        if not any(window.resizable()) or state['origin'] is not None: return
        x, y = e.x_root-window.winfo_rootx(), e.y_root-window.winfo_rooty(); margin = round(5*scale(window))
        horizontal,vertical=window.resizable()
        edge = ('n' if y<margin else 's' if y>=window.winfo_height()-margin else '') if vertical else ''
        edge += ('w' if x<margin else 'e' if x>=window.winfo_width()-margin else '') if horizontal else ''
        if edge: begin(e, edge)
    window.bind('<ButtonPress-1>', edge_press, add='+')
    window.bind('<B1-Motion>', lambda e: move(e) if state['edge'] else None, add='+')
    window.bind('<ButtonRelease-1>', end, add='+')
    def dispose(e):
        if e.widget is window and state['job'] is not None: window.after_cancel(state['job']); state['job'] = None
    window.bind('<Destroy>', dispose, add='+')
