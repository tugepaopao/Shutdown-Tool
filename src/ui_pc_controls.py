"""Compact settings-only hardware panel. No changes to timer settings or homepage."""
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk
from theme import theme, flat_button
from pc_controls import WindowsControls
from ui_cozy import CozyFrame



class PercentSlider(tk.Canvas):
    """Flat, keyboard-accessible slider with a clear thumb and 0..100 range."""
    def __init__(self, parent, variable, command):
        super().__init__(parent, height=26, width=100, bg=theme.c('bg'),
                         highlightthickness=0, takefocus=True, cursor='hand2')
        self.variable, self.command = variable, command
        self.disabled = False
        self.trace = variable.trace_add('write', self.redraw)
        self.bind('<Configure>', self.redraw)
        self.bind('<Button-1>', self._point)
        self.bind('<B1-Motion>', self._point)
        self.bind('<Left>', lambda e: self._step(-1))
        self.bind('<Right>', lambda e: self._step(1))
        self.bind('<Prior>', lambda e: self._step(10))
        self.bind('<Next>', lambda e: self._step(-10))
        self.bind('<Home>', lambda e: self._set(0))
        self.bind('<End>', lambda e: self._set(100))
        self.bind('<FocusIn>', self.redraw)
        self.bind('<FocusOut>', self.redraw)
        self.bind('<Destroy>', self._cleanup)

    def _cleanup(self, event):
        if event.widget is self:
            self.variable.trace_remove('write', self.trace)

    def state(self, states=None):
        if states is not None:
            self.disabled = 'disabled' in states
            self.configure(takefocus=not self.disabled, cursor='arrow' if self.disabled else 'hand2')
            self.redraw()
        return ('disabled',) if self.disabled else ()

    def redraw(self, *_):
        if not self.winfo_exists(): return
        width, height = self.winfo_width(), self.winfo_height()
        margin = 8
        center = height/2
        end = max(margin, width-margin)
        x = margin+(end-margin)*max(0,min(100,self.variable.get()))/100
        color = theme.c('disabled') if self.disabled else theme.accent
        self.delete('all')
        self.create_line(margin,center,end,center,fill=theme.c('card_border'),width=4,capstyle='round')
        if not self.disabled: self.create_line(margin,center,x,center,fill=color,width=4,capstyle='round')
        self.create_oval(x-6,center-6,x+6,center+6,fill=theme.c('input_bg'),outline=color,width=2)
        if self.focus_get() is self and not self.disabled:
            self.create_rectangle(1,1,width-2,height-2,outline=theme.accent,dash=(2,2))

    def _set(self, value):
        if self.disabled: return 'break'
        value = max(0,min(100,round(value)))
        self.variable.set(value)
        self.command(str(value))
        return 'break'

    def _step(self, amount):
        return self._set(self.variable.get()+amount)

    def _point(self, event):
        if self.disabled: return 'break'
        self.focus_set()
        return self._set((event.x-8)*100/max(1,self.winfo_width()-16))


class ControlPanel(tk.Frame):
    def __init__(self, parent, settings, backend=None):
        super().__init__(parent, bg=theme.c('bg'))
        self.settings = settings
        self.T = settings.T
        self.backend = backend or WindowsControls()
        self.requests, self.results = queue.Queue(), queue.Queue()
        self.closed = threading.Event()
        self.pending = {}
        self.revisions = {}
        self.refreshing = False
        self.last_detection = 0
        self.rows = {}
        self.monitor_list = []
        self.link = tk.BooleanVar(self, False)
        self.muted = False
        self.labels = []
        self._poll_id = self._periodic_id = None
        self.bind('<Destroy>', self._destroyed, add='+')
        self.pack(fill='both', expand=True, padx=10, pady=8)
        bar = tk.Frame(self, bg=theme.c('bg')); bar.pack(fill='x', pady=(0, 8))
        self.count_label = self._label(bar, 'pc_detecting', anchor='w')
        self.count_label.pack(side='left', fill='x', expand=True)
        self.refresh_button = flat_button(bar, self.T('pc_refresh'), self.refresh, padx=10)
        self.refresh_button.pack(side='right')
        bright = self._group('pc_brightness')
        self.monitors_frame = tk.Frame(bright, bg=theme.c('bg'))
        self.monitors_frame.pack(fill='x', padx=10, pady=6)
        self.link_check = tk.Checkbutton(bright, text=self.T('pc_link'), variable=self.link,
            bg=theme.c('bg'), fg=theme.c('fg'), selectcolor=theme.c('input_bg'),
            activebackground=theme.c('bg'), font=theme.font(), anchor='w')
        self.link_check.pack(fill='x', padx=6, pady=(0, 8))
        self.labels.append((self.link_check, 'pc_link'))
        sound = self._group('pc_volume')
        sound_row = tk.Frame(sound, bg=theme.c('bg')); sound_row.pack(fill='x', padx=10, pady=(6, 0))
        self._label(sound_row, 'pc_volume', anchor='w').pack(side='left')
        self.volume_value = tk.Label(sound_row, text='—', bg=theme.c('bg'), fg=theme.accent,
                                     font=theme.font(bold=True), anchor='e')
        self.volume_value.pack(side='right')
        controls = tk.Frame(sound, bg=theme.c('bg')); controls.pack(fill='x', padx=10, pady=(4, 6))
        controls.columnconfigure(0, weight=1)
        self.volume = tk.DoubleVar(self, 0)
        self.volume_scale = self._scale(controls, self.volume, self._volume_changed)
        self.volume_scale.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        self.volume_scale.state(['disabled'])
        self.mute_button = flat_button(controls, self.T('pc_mute'), self.toggle_mute, padx=10)
        self.mute_button.grid(row=0, column=1, sticky='ew')
        self.mute_button.configure(state='disabled')
        self.audio_note = tk.Label(sound, text='', bg=theme.c('bg'), fg=theme.c('fg_muted'),
                                   font=theme.font(), anchor='w', justify='left', wraplength=400)
        self.audio_note.pack(fill='x', padx=10, pady=(0, 5))
        awake=self._group('pc_awake_title')
        self.awake_var=tk.BooleanVar(self, bool(settings.app.cfg.get('keep_display_on')))
        self.awake_check=tk.Checkbutton(awake,text=self.T('pc_awake_toggle'),variable=self.awake_var,command=self._awake_changed,bg=theme.c('bg'),fg=theme.c('fg'),selectcolor=theme.c('input_bg'),activebackground=theme.c('bg'),font=theme.font(),anchor='w')
        self.awake_check.pack(fill='x',padx=6,pady=(5,3));self.labels.append((self.awake_check,'pc_awake_toggle'))
        self._label(awake,'pc_awake_hint',anchor='w',wraplength=400,justify='left').pack(fill='x',padx=10,pady=(0,8))
        self._label(self, 'pc_live', anchor='w', wraplength=400, justify='left').pack(fill='x', pady=(0, 6))
        self.status = tk.Label(self, text='', bg=theme.c('bg'), fg=theme.c('fg_muted'),
                              font=theme.font(), anchor='w', justify='left', wraplength=400)
        self.status.pack(fill='x', pady=(0, 6))
        guide = self._group('pc_guide')
        for key in ('pc_guide_display', 'pc_guide_ddc', 'pc_guide_audio', 'pc_guide_cancel'):
            self._label(guide, key, anchor='w', justify='left', wraplength=400).pack(fill='x', padx=10, pady=5)
        self.retheme()
        threading.Thread(target=self._worker, name='PC controls', daemon=True).start()
        self._poll_id = self.after(50, self._poll)
        self._periodic_id = self.after(4000, self._periodic)

    def _awake_changed(self):
        from ui_localize import messagebox
        app=self.settings.app;previous=bool(app.cfg.get("keep_display_on"));wanted=bool(self.awake_var.get())
        try:
            app.display_awake.set_enabled(wanted)
            app.cfg["keep_display_on"]=wanted
            if not app.cfg.save():raise OSError(self.T("pc_awake_save_error"))
        except OSError as exc:
            app.display_awake.set_enabled(previous);app.cfg["keep_display_on"]=previous;self.awake_var.set(previous)
            messagebox.showerror(self.T("tip_title"),str(exc),parent=self.settings)

    def _label(self, parent, key, **kwargs):
        label = tk.Label(parent, text=self.T(key), bg=theme.c('bg'), fg=theme.c('fg'), font=theme.font(), **kwargs)
        self.labels.append((label, key))
        return label

    def _group(self, key):
        from ui_cozy import CozyGroup
        group = CozyGroup(self,text=self.T(key))
        group.pack(fill='x', pady=(0, 10))
        self.labels.append((group, key))
        return group

    def _scale(self, parent, var, command):
        return PercentSlider(parent, var, command)

    def retheme(self):
        self.volume_scale.redraw()
        self.volume_value.configure(fg=theme.accent)
        for row in self.rows.values():
            row['value_label'].configure(fg=theme.accent)
            row['slider'].redraw()

    def _worker(self):
        while not self.closed.is_set():
            request = self.requests.get()
            if request is None or self.closed.is_set():
                return
            fn, callback = request
            try:
                result, error = fn(), None
            except Exception as exc:
                result, error = None, str(exc)
            if not self.closed.is_set():
                self.results.put((callback, result, error))

    def _submit(self, fn, callback):
        if not self.closed.is_set():
            self.requests.put((fn, callback))

    def _poll(self):
        if self.closed.is_set(): return
        for _ in range(20):
            try: callback, result, error = self.results.get_nowait()
            except queue.Empty: break
            callback(result, error)
        self._poll_id = self.after(50, self._poll)

    def _destroyed(self, event):
        if event.widget is not self: return
        self.closed.set()
        for task in [self._poll_id, self._periodic_id, *self.pending.values()]:
            if task:
                try: self.after_cancel(task)
                except tk.TclError: pass
        self.requests.put(None)

    def _periodic(self):
        if self.settings._current == 'pc' and not self.refreshing and not self.pending:
            if time.monotonic()-self.last_detection > 20: self.refresh()
            else: self._submit(self.backend.audio, self._show_audio)
        self._periodic_id = self.after(4000, self._periodic)

    def refresh(self):
        if self.refreshing or self.pending: return
        self.refreshing = True
        self.last_detection = time.monotonic()
        self.refresh_button.configure(state='disabled')
        self.status.configure(text=self.T('pc_detecting'))
        self._submit(self.backend.audio, self._show_audio)
        self._submit(self.backend.monitors, self._show_monitors)

    def _show_monitors(self, result, error):
        self.refreshing = False
        self.refresh_button.configure(state='normal')
        if error:
            self.status.configure(text=self.T('pc_detection_failed'))
            return
        if self.rows and [(m.key,m.method) for m in result] == [(m.key,m.method) for m in self.monitor_list]:
            self.monitor_list = result
            for monitor in result:
                row = self.rows[monitor.key]
                row['monitor'] = monitor
                row['variable'].set(monitor.value or 0)
                row['value_label'].configure(text='—' if monitor.value is None else f'{monitor.value}%')
            self.status.configure(text=self.T('pc_ready'))
            return
        for widget in self.monitors_frame.winfo_children(): widget.destroy()
        self.rows = {}
        self.monitor_list = result
        self.count_label.configure(text=self.T('pc_count', n=len(result)))
        secondary = 0
        for monitor in result:
            if not monitor.primary: secondary += 1
            name = self.T('pc_primary') if monitor.primary else self.T('pc_secondary', n=secondary)
            frame = tk.Frame(self.monitors_frame, bg=theme.c('bg')); frame.pack(fill='x', pady=(0, 8))
            head = tk.Frame(frame, bg=theme.c('bg')); head.pack(fill='x')
            title = tk.Label(head, text=name, bg=theme.c('bg'), fg=theme.c('fg'), font=theme.font(), anchor='w')
            title.pack(side='left', fill='x', expand=True)
            value = tk.Label(head, text='—' if monitor.value is None else f'{monitor.value}%',
                             bg=theme.c('bg'), fg=theme.accent, font=theme.font(bold=True))
            value.pack(side='right')
            var = tk.DoubleVar(self, monitor.value or 0)
            slider = self._scale(frame, var, lambda number, key=monitor.key: self._brightness_changed(key, number))
            slider.pack(fill='x', pady=(4, 0))
            if monitor.value is None:
                slider.state(['disabled'])
                tk.Label(frame, text=self.T('pc_unavailable'), bg=theme.c('bg'), fg=theme.c('fg_muted'),
                         font=theme.font(), anchor='w', justify='left', wraplength=400).pack(fill='x', pady=(3, 0))
            self.rows[monitor.key] = dict(monitor=monitor, variable=var, slider=slider, value_label=value)
        if not result:
            self._label(self.monitors_frame, 'pc_missing', anchor='w', wraplength=400).pack(fill='x', pady=4)
        self.link_check.configure(state='normal' if sum(m.value is not None for m in result) > 1 else 'disabled')
        self.status.configure(text=self.T('pc_ready'))

    def _show_audio(self, result, error):
        if error:
            self.volume_scale.state(['disabled']); self.mute_button.configure(state='disabled')
            self.volume_value.configure(text='—'); self.audio_note.configure(text=self.T('pc_audio_unavailable'))
            return
        if 'volume' in self.pending or 'mute' in self.pending: return
        self.volume.set(result['value'])
        self.volume_value.configure(text=f"{result['value']}%")
        self.muted = result['muted']
        self.volume_scale.state(['!disabled']); self.mute_button.configure(state='normal', text=self.T('pc_unmute' if self.muted else 'pc_mute'))
        self.audio_note.configure(text='')

    def _debounce(self, key, fn, callback):
        revision = self.revisions[key] = self.revisions.get(key, 0)+1
        previous = self.pending.get(key)
        if previous:
            self.after_cancel(previous)
        def send():
            self.pending[key] = None
            def finished(result, error):
                # A newer slider request may already be waiting; do not clear it.
                if self.revisions.get(key) != revision: return
                self.pending.pop(key, None)
                callback(result, error)
            def latest():
                if self.revisions.get(key) == revision: return fn()
            self._submit(latest, finished)
        self.pending[key] = self.after(250, send)

    def _brightness_changed(self, key, number):
        if key not in self.rows or self.rows[key]['monitor'].value is None: return
        level = max(0, min(100, round(float(number))))
        targets = [row for row in self.rows.values() if row['monitor'].value is not None] if self.link.get() else [self.rows[key]]
        for row in targets:
            row['variable'].set(level)
            row['value_label'].configure(text=f'{level}%')
        if self.link.get():
            def set_linked():
                failures = []
                for row in targets:
                    try: self.backend.set_brightness(row['monitor'], level)
                    except Exception: failures.append(row['monitor'].key)
                if failures: raise RuntimeError('partial_brightness')
            self._debounce('brightness:linked', set_linked, self._brightness_done)
        else:
            row = targets[0]
            self._debounce('brightness:'+row['monitor'].key,
                           lambda: self.backend.set_brightness(row['monitor'], level), self._brightness_done)

    def _brightness_done(self, result, error):
        self.status.configure(text=self.T('pc_partial' if error and self.link.get() else 'pc_failed' if error else 'pc_applied'))
        if error:
            self.after(350, self.refresh)

    def _volume_changed(self, number):
        if 'disabled' in self.volume_scale.state(): return
        level = max(0, min(100, round(float(number))))
        self.volume_value.configure(text=f'{level}%')
        self._debounce('volume', lambda: self.backend.set_volume(level), self._audio_done)

    def toggle_mute(self):
        if 'mute' in self.pending: return
        value = not self.muted
        self._debounce('mute', lambda: self.backend.set_mute(value), self._audio_done)

    def _audio_done(self, result, error):
        self.status.configure(text=self.T('pc_failed' if error else 'pc_applied'))
        self._submit(self.backend.audio, self._show_audio)
