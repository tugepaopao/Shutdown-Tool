"""Compact settings-only hardware panel. No changes to timer settings or homepage."""
import queue
import threading
import time
import tkinter as tk
from theme import theme, flat_button
from pc_controls import WindowsControls



class PercentSlider(tk.Canvas):
    """Flat, keyboard-accessible slider with a clear thumb and 0..100 range."""
    def __init__(self, parent, variable, command, minimum=0, maximum=100):
        super().__init__(parent, height=26, width=100, bg=parent.cget('background'),
                         highlightthickness=0, takefocus=True, cursor='hand2')
        self.variable, self.command = variable, command
        self.minimum, self.maximum = minimum, maximum
        self.disabled = False
        self.trace = variable.trace_add('write', self.redraw)
        self.bind('<Configure>', self.redraw)
        self.bind('<Button-1>', self._point)
        self.bind('<B1-Motion>', self._point)
        self.bind('<Left>', lambda e: self._step(-1))
        self.bind('<Right>', lambda e: self._step(1))
        self.bind('<Prior>', lambda e: self._step(10))
        self.bind('<Next>', lambda e: self._step(-10))
        self.bind('<Home>', lambda e: self._set(self.minimum))
        self.bind('<End>', lambda e: self._set(self.maximum))
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
        value = max(self.minimum,min(self.maximum,float(self.variable.get())))
        x = margin+(end-margin)*(value-self.minimum)/(self.maximum-self.minimum)
        color = theme.c('disabled') if self.disabled else theme.accent
        self.delete('all')
        self.create_line(margin,center,end,center,fill=theme.c('card_border'),width=4,capstyle='round')
        if not self.disabled: self.create_line(margin,center,x,center,fill=color,width=4,capstyle='round')
        self.create_oval(x-6,center-6,x+6,center+6,fill=theme.c('input_bg'),outline=color,width=2)
        if self.focus_get() is self and getattr(self._root(),'_cozy_keyboard_navigation',False) and not self.disabled:
            self.create_rectangle(1,1,width-2,height-2,outline=theme.accent,dash=(2,2))

    def _set(self, value):
        if self.disabled: return 'break'
        value = max(self.minimum,min(self.maximum,round(value)))
        self.variable.set(value)
        self.command(str(value))
        return 'break'

    def _step(self, amount):
        return self._set(float(self.variable.get())+amount)

    def _point(self, event):
        if self.disabled: return 'break'
        self._root()._cozy_keyboard_navigation=False;self.focus_set()
        return self._set(self.minimum+(event.x-8)*(self.maximum-self.minimum)/max(1,self.winfo_width()-16))


class ControlPanel(tk.Frame):
    def __init__(self, parent, settings, backend=None):
        super().__init__(parent, bg=parent.cget('bg'))
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
        self._poll_id = self._periodic_id = self._retry_id = None
        self.bind('<Destroy>', self._destroyed, add='+')
        self.pack(fill='both', expand=True, padx=0, pady=4)
        bar = tk.Frame(self, bg=self.cget('bg')); bar.pack(fill='x', pady=(0, 8))
        self.count_label = self._label(bar, 'pc_detecting', anchor='w')
        self.count_label.pack(side='left', fill='x', expand=True)
        self.refresh_button = flat_button(bar, self.T('pc_refresh'), self.refresh, padx=10)
        self.refresh_button.pack(side='right')
        bright = self._group('pc_brightness')
        self.monitors_frame = tk.Frame(bright, bg=bright.cget('bg'))
        self.monitors_frame.pack(fill='x', padx=10, pady=6)
        self.link_check = tk.Checkbutton(bright, text=self.T('pc_link'), variable=self.link,
            bg=bright.cget('bg'), fg=theme.c('fg'), selectcolor=theme.c('input_bg'),
            activebackground=bright.cget('bg'), font=getattr(self.winfo_toplevel(),'font',theme.font)(), anchor='w')
        self.link_check.pack(fill='x', padx=6, pady=(0, 8))
        self.link_check.bind('<Configure>',lambda e:self.link_check.configure(wraplength=max(50,e.width-24)))
        self.labels.append((self.link_check, 'pc_link'))
        sound = self._group('pc_volume')
        sound_row = tk.Frame(sound, bg=sound.cget('bg')); sound_row.pack(fill='x', padx=10, pady=(6, 0))
        self._label(sound_row, 'pc_volume', anchor='w').pack(side='left')
        self.volume_value = tk.Label(sound_row, text='—', bg=sound_row.cget('bg'), fg=theme.accent,
                                     font=getattr(self.winfo_toplevel(),'font',theme.font)(bold=True), anchor='e')
        self.volume_value.pack(side='right')
        controls = tk.Frame(sound, bg=sound.cget('bg')); controls.pack(fill='x', padx=10, pady=(4, 6))
        controls.columnconfigure(0, weight=1)
        self.volume = tk.DoubleVar(self, 0)
        self.volume_scale = self._scale(controls, self.volume, self._volume_changed)
        self.volume_scale.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        self.volume_scale.state(['disabled'])
        self.mute_button = flat_button(controls, self.T('pc_mute'), self.toggle_mute, padx=10)
        self.mute_button.grid(row=0, column=1, sticky='ew')
        self.mute_button.configure(state='disabled')
        self.audio_note = tk.Label(sound, text='', bg=sound.cget('bg'), fg=theme.c('fg_muted'),
                                   font=getattr(self.winfo_toplevel(),'font',theme.font)(), anchor='w', justify='left', wraplength=400)
        self.audio_note.pack(fill='x', padx=10, pady=(0, 5))
        awake=self._group('pc_awake_title')
        self.awake_var=tk.BooleanVar(self, bool(settings.app.cfg.get('keep_display_on')))
        from ui_settings_controls import Switch
        row=tk.Frame(awake,bg=awake.cget('bg'));row.pack(fill='x',padx=12,pady=(8,12))
        self.awake_check=Switch(row,self.awake_var,command=self._awake_changed);self.awake_check.pack(side='right')
        self._label(row,'pc_awake_toggle',anchor='w',wraplength=240,justify='left').pack(side='left',fill='x',expand=True)
        self.status = tk.Label(self, text='', bg=theme.c('bg'), fg=theme.c('fg_muted'),
                              font=getattr(self.winfo_toplevel(),'font',theme.font)(), anchor='w', justify='left', wraplength=400)
        self.status.pack(fill='x', pady=(0, 6))
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
        label = tk.Label(parent, text=self.T(key), bg=parent.cget('bg'), fg=theme.c('fg'), font=getattr(self.winfo_toplevel(),'font',theme.font)(), **kwargs)
        self.labels.append((label, key))
        if kwargs.get('wraplength'):
            label.bind('<Configure>',lambda e:label.configure(wraplength=max(50,e.width-2)) if abs(int(label.cget('wraplength'))-e.width)>3 else None)
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
        for task in [self._poll_id, self._periodic_id, self._retry_id, *self.pending.values()]:
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
                row['slider'].state(['disabled'] if monitor.value is None else ['!disabled'])
                if not any(key.startswith('brightness:') for key in self.pending):
                    row['variable'].set(monitor.value or 0)
                    row['value_label'].configure(text='—' if monitor.value is None else f'{monitor.value}%')
            self.link_check.configure(state='normal' if sum(m.value is not None for m in result) > 1 else 'disabled')
            self.status.configure(text=self.T('pc_ready'))
            return
        for widget in self.monitors_frame.winfo_children(): widget.destroy()
        self.rows = {}
        self.monitor_list = result
        self.count_label.configure(text=self.T('pc_count', n=len(result)))
        surface = self.monitors_frame.cget("background")
        secondary = 0
        for monitor in result:
            if not monitor.primary: secondary += 1
            name = self.T('pc_primary') if monitor.primary else self.T('pc_secondary', n=secondary)
            frame = tk.Frame(self.monitors_frame, bg=surface); frame.pack(fill='x', pady=(0, 8))
            head = tk.Frame(frame, bg=surface); head.pack(fill='x')
            title = tk.Label(head, text=name, bg=surface, fg=theme.c('fg'), font=getattr(self.winfo_toplevel(),'font',theme.font)(), anchor='w')
            title.pack(side='left', fill='x', expand=True)
            value = tk.Label(head, text='—' if monitor.value is None else f'{monitor.value}%',
                             bg=surface, fg=theme.accent, font=getattr(self.winfo_toplevel(),'font',theme.font)(bold=True))
            value.pack(side='right')
            var = tk.DoubleVar(self, monitor.value or 0)
            slider = self._scale(frame, var, lambda number, key=monitor.key: self._brightness_changed(key, number))
            slider.pack(fill='x', pady=(4, 0))
            if monitor.value is None:
                slider.state(['disabled'])
                tk.Label(frame, text=self.T('pc_unavailable'), bg=surface, fg=theme.c('fg_muted'),
                         font=getattr(self.winfo_toplevel(),'font',theme.font)(), anchor='w', justify='left', wraplength=400).pack(fill='x', pady=(3, 0))
            self.rows[monitor.key] = dict(monitor=monitor, variable=var, slider=slider, value_label=value)
        if not result:
            missing=self._label(self.monitors_frame, 'pc_missing', anchor='w', wraplength=400)
            missing.configure(bg=surface);missing.pack(fill='x', pady=4)
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
            if self._retry_id:self.after_cancel(self._retry_id)
            self._retry_id=self.after(350,self._retry_refresh)

    def _retry_refresh(self):
        self._retry_id=None
        self.refresh()

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
