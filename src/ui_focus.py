"""Resolve Python widgets safely when Tcl owns a native combobox popup."""
import tkinter as tk


def has_grab(widget):
    try:
        return bool(widget.tk.call('grab', 'current', widget._w))
    except AttributeError:  # Small non-Tk controller test doubles.
        return bool(widget.grab_current())
    except tk.TclError:
        return False


def current_grab(widget):
    """Close a native dropdown on navigation, retaining its previous modal grab."""
    try:
        path = str(widget.tk.call('grab', 'current', widget._w))
        if not path:
            return None
        try:
            return widget.nametowidget(path)
        except KeyError:
            # ttk::combobox::Unpost restores the grab saved by ttk::globalGrab.
            owner = path.split('.popdown', 1)[0]
            if owner != path and widget.tk.call('winfo', 'exists', owner):
                widget.tk.call('ttk::combobox::Unpost', owner)
                # On Windows <Unmap> may be delivered later. Restore once now;
                # ttk's subsequent Unmap handler is explicitly idempotent.
                widget.tk.call('ttk::RestoreGrab', path)
                path = str(widget.tk.call('grab', 'current', widget._w))
                return widget.nametowidget(path) if path else None
            return None
    except (KeyError, tk.TclError):
        return None


def current_focus(widget):
    """Paint/focus inspection must neither dismiss nor resolve Tcl-only widgets."""
    try:
        path = str(widget.tk.call('focus', '-displayof', widget._w))
        return widget.nametowidget(path) if path else None
    except (KeyError, tk.TclError):
        return None
