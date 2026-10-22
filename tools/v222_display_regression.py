"""Native workarea bounds at supplied Tk scale; isolated settings."""
import os,sys,tempfile,time,json,ctypes
from pathlib import Path
from ctypes import wintypes as W
p=Path(__file__).resolve().parents[1];sys.path[:0]=[str(p/'src'),str(p/'tools')]
temp=tempfile.TemporaryDirectory();os.environ['APPDATA']=temp.name
from main import enable_dpi_awareness
enable_dpi_awareness()
import ui_main,autostart
ui_main.App._init_tray=lambda a:None;autostart.set_enabled=lambda *a:True
factor=float(sys.argv[1]);build=ui_main.App.build_ui
def scaled(a):a.root.tk.call('tk','scaling',factor*96/72);return build(a)
ui_main.App.build_ui=scaled
a=ui_main.App({'given':True,'action':'message'});errors=[]
a.root.report_callback_exception=lambda t,v,b:errors.append(str(v))
def pump():
    end=time.monotonic()+.15
    while time.monotonic()<end:a.root.update();time.sleep(.003)
from ui_floating import workareas
areas=workareas(a.root);checks={}
def fits(window,name):
    pump();u=ctypes.windll.user32;u.GetAncestor.argtypes=[W.HWND,W.UINT];u.GetAncestor.restype=W.HWND
    rect=W.RECT();u.GetWindowRect.argtypes=[W.HWND,ctypes.POINTER(W.RECT)]
    u.GetWindowRect(u.GetAncestor(window.winfo_id(),2),ctypes.byref(rect))
    box=(rect.left,rect.top,rect.right,rect.bottom)
    checks[name]=box
    assert any(l<=box[0] and t<=box[1] and box[2]<=r and box[3]<=b for l,t,r,b in areas),(name,box,areas)
try:
    pump();from ui_workspace import keep_visible
    keep_visible(a.root);fits(a.root,'main')
    a.open_settings();fits(a._settings_win,'settings');a._settings_win.destroy()
    a.open_task_center();fits(a._task_center_win,'task-center');a._task_center_win.destroy()
    from ui_date_picker import DatePicker
    d=DatePicker(a.root,a,anchor=a.btn_start);fits(d,'calendar');d.destroy()
    from ui_messagebox import MessageDialog
    d=MessageDialog(a.root,'已有任务正在运行','当前任务继续计时。请选择替换、加入队列或取消。','askyesnocancel',labels={'yes':'替换当前任务','no':'加入队列','cancel':'取消'})
    fits(d,'confirmation');d.destroy()
    a._pick_mode('datetime');pump();a.root.focus_force();a.weekday_box.open();fits(a.weekday_box.popup,'weekday');a.weekday_box.popup.dismiss()
    assert not errors,errors
finally:a.quit_app()
out=p/'核验/v222'/('display-'+str(factor)+'.json');out.write_text(json.dumps(dict(scale=factor,areas=areas,bounds=checks,errors=errors),indent=2),encoding='utf-8');print(out.name,'passed')
