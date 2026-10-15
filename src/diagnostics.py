"""Private, path-free diagnostic summary; no automatic transmission."""
import platform,json,datetime as dt

def summary(app):
    from i18n import VERSION
    from ui_main import os_display_name
    hotkeys=getattr(app.desktop,'hotkeys',None)
    return dict(version=VERSION,system=os_display_name(),architecture=platform.machine(),display_scale_percent=round(float(app.root.tk.call('tk','scaling'))/(96/72)*100),language=app.T.lang,
        hotkeys_enabled=bool(app.cfg.get('hotkeys_enabled')),hotkeys_registered=bool(hotkeys and hotkeys.mapping),
        timer=dict(running=app.engine.is_running(),paused=app.engine.paused,mode=app.engine.mode,remaining_seconds=round(app.engine.remaining()),due_at=app.engine.due_at().isoformat(timespec='seconds') if app.engine.due_at() else None),
        queue_count=len(app.task_queue),advanced_count=len(app.automation.jobs),floating=dict(enabled=bool(app.cfg.get('float_enabled')),topmost=bool(app.cfg.get('float_topmost'))),warning_seconds=app.cfg.get('warning_seconds',10))

def text(app):return json.dumps(summary(app),ensure_ascii=False,indent=2)
