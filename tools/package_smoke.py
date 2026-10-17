"""Run a packaged EXE with isolated data and close only its own window."""
import os,sys,time,json,tempfile,subprocess,ctypes,hashlib
from pathlib import Path
from ctypes import wintypes as W
import psutil
p=Path(__file__).resolve().parent.parent
exe=Path(sys.argv[1]).resolve();assert exe.is_file()
sys.path.insert(0,str(p/'src'))
u=ctypes.windll.user32
u.GetWindowThreadProcessId.argtypes=[W.HWND,ctypes.POINTER(W.DWORD)]
u.GetWindowTextW.argtypes=[W.HWND,W.LPWSTR,ctypes.c_int]
u.IsWindowVisible.argtypes=[W.HWND];u.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
u.ShowWindow.argtypes=[W.HWND,ctypes.c_int];u.IsIconic.argtypes=[W.HWND]
callback=ctypes.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
def window(proc):
    ids={proc.pid}
    try:ids.update(c.pid for c in psutil.Process(proc.pid).children(recursive=True))
    except psutil.Error:pass
    found=[]
    def visit(hwnd,data):
        pid=W.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        title=ctypes.create_unicode_buffer(256);u.GetWindowTextW(hwnd,title,256)
        if pid.value in ids and u.IsWindowVisible(hwnd) and '定时关机工具' in title.value:found.append(hwnd)
        return True
    u.EnumWindows(callback(visit),0)
    return found[0] if found else None
with tempfile.TemporaryDirectory(prefix='shutdown-package-') as tmp:
    folder=Path(tmp)/'HaozaiziShutdownTool';folder.mkdir()
    seed=dict(minimize_to_tray=False,confirm_on_exit=False,autostart=False,language='CHS',hotkeys_enabled=False,hotkey_show='Ctrl+Alt+J',templates=[dict(id='preserved',name='升级验证模板',favorite=True,action='message',mode='countdown',seconds=600)],automations=[],pending_timer={},task_queue=[],float_enabled=False)
    cfg=folder/'settings.json';cfg.write_text(json.dumps(seed,ensure_ascii=False),encoding='utf-8')
    env=dict(os.environ,APPDATA=tmp);start=time.monotonic();proc=subprocess.Popen([str(exe),'/w'],env=env)
    hwnd=None
    while time.monotonic()-start<35 and proc.poll() is None:
        hwnd=window(proc)
        if hwnd:break
        time.sleep(.1)
    assert hwnd,'Packaged window did not appear'
    seconds=round(time.monotonic()-start,2)
    u.ShowWindow(hwnd,6);time.sleep(.4)
    second=subprocess.Popen([str(exe),'/w'],env=env);assert second.wait(timeout=25)==0
    deadline=time.monotonic()+5
    while u.IsIconic(hwnd) and time.monotonic()<deadline:time.sleep(.1)
    assert not u.IsIconic(hwnd),'Second launch did not restore main window'
    u.PostMessageW(hwnd,0x10,0,0);assert proc.wait(timeout=20)==0
    result=json.loads(cfg.read_text(encoding='utf-8'))
    assert result['templates'][0]['favorite'] and result['templates'][0]['name']==seed['templates'][0]['name']
    assert result['hotkey_show']=='Ctrl+Alt+J'
    proof=dict(exe_name=exe.name,sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),startup_seconds=seconds,window_visible=True,second_launch_restored=True,clean_exit=True,template_favorite_and_shortcut_preserved=True)
    from i18n import VERSION
    out=p/('核验/package-v'+VERSION.replace('.',''));out.mkdir(parents=True,exist_ok=True)
    (out/('portable.json' if exe.parent.name.startswith('dist') else 'installed.json')).write_text(json.dumps(proof,indent=2),encoding='utf-8')
    print(json.dumps(proof),flush=True)
