from pathlib import Path
import sys,types,ctypes,json,ast
from unittest.mock import patch,Mock
p=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(p/'src'));sys.stdout.reconfigure(encoding='utf-8')
from main import enable_dpi_awareness
from ui_main import os_display_name,is_win10,is_win11
import ui_window
checks=[]
def check(n,v):checks.append([n,bool(v)]);print(('PASS ' if v else 'FAIL ')+n,flush=True);assert v,n
for build,label in [(19045,'Windows 10'),(22000,'Windows 11'),(22631,'Windows 11'),(26100,'Windows 11'),(7601,'Windows 7')]:
 with patch('ui_main.windows_build',return_value=build):
  check(label+' '+str(build)+' detection',os_display_name().startswith(label))
  if build>=22000:check('Win11 not identified as Win10 '+str(build),is_win11() and not is_win10())
api=Mock(return_value=True)
with patch.object(ctypes,'windll',types.SimpleNamespace(user32=types.SimpleNamespace(SetProcessDpiAwarenessContext=api))):
 check('Win10/11 per-monitor-v2 preferred',enable_dpi_awareness()=='per-monitor-v2')
api=Mock(return_value=0)
with patch.object(ctypes,'windll',types.SimpleNamespace(user32=types.SimpleNamespace(),shcore=types.SimpleNamespace(SetProcessDpiAwareness=api))):
 check('missing new DPI API uses per-monitor fallback',enable_dpi_awareness()=='per-monitor')
api=Mock(return_value=True)
with patch.object(ctypes,'windll',types.SimpleNamespace(user32=types.SimpleNamespace(SetProcessDPIAware=api))):
 check('legacy DPI API fallback remains',enable_dpi_awareness()=='system')
with patch.object(ctypes,'windll',types.SimpleNamespace()):check('missing all DPI APIs does not crash',enable_dpi_awareness()=='none')
class Window:
 def update_idletasks(self):pass
 def winfo_id(self):return 1
w=Window()
with patch.object(ctypes,'windll',types.SimpleNamespace()):ui_window.disable_native_animation(w)
check('unsupported DWM decoration degrades safely',w._native_animation_disabled is False)
parsed=0
for f in (p/'src').glob('*.py'):ast.parse(f.read_text(encoding='utf-8-sig'),feature_version=(3,8));parsed+=1
check('source grammar remains Python3.8 parseable',parsed>0)
requirements=(p/'requirements.txt').read_text(encoding='utf-8');check('Win10 dependencies unchanged','Pillow==12.3.0' in requirements and 'PyInstaller==6.22.3' in requirements)
check('unsupported legacy OS still blocked by installer','MinVersion=10.0' in (p/'installer/setup.iss').read_text(encoding='utf-8'))
(p/'tools/v168-platform-results.json').write_text(json.dumps(dict(checks=checks,source_modules=parsed,real_systems_tested=['Windows 10'],win11_simulated=True,win7_binary_supported=False),ensure_ascii=False,indent=2),encoding='utf-8');print('All',len(checks),'passed')
