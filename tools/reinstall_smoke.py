"""Authorized uninstall/reinstall check; preserves user data and startup value."""
import os,sys,json,subprocess,winreg,hashlib,shutil,datetime
from pathlib import Path
import psutil
p=Path(__file__).resolve().parent.parent;proof=p/'核验/package-v205'
key=r'Software\Microsoft\Windows\CurrentVersion\Uninstall\{8F3C1A72-5B4E-4C9D-9E21-7A6B0C5D3F10}_is1'
with winreg.OpenKey(winreg.HKEY_CURRENT_USER,key) as k:
 assert winreg.QueryValueEx(k,'DisplayVersion')[0]=='2.0.5'
 dest=Path(winreg.QueryValueEx(k,'InstallLocation')[0]).resolve()
 try:tasks=winreg.QueryValueEx(k,'Inno Setup: Selected Tasks')[0]
 except FileNotFoundError:tasks=''
assert dest.name=='HaozaiziShutdownTool' and (dest/'unins000.exe').is_file()
for proc in psutil.process_iter(['name']):assert proc.info['name']!='定时关机工具.exe','App must be closed'
run=r'Software\Microsoft\Windows\CurrentVersion\Run';value='豪崽子の自动关机工具'
with winreg.OpenKey(winreg.HKEY_CURRENT_USER,run) as k:
 try:startup_value=winreg.QueryValueEx(k,value)
 except FileNotFoundError:startup_value=None
data=Path(os.environ['APPDATA'])/'HaozaiziShutdownTool'
def hashes():return {str(f.relative_to(data)):hashlib.sha256(f.read_bytes()).hexdigest() for f in data.rglob('*') if f.is_file()}
before=hashes();backup=proof/('before-reinstall-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
if data.exists():shutil.copytree(data,backup/'user-data')
si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
uninstalled=False
try:
 result=subprocess.run([str(dest/'unins000.exe'),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/LOG='+str(proof/'uninstall.log')],startupinfo=si,timeout=120)
 assert result.returncode==0 and not (dest/'定时关机工具.exe').exists()
 assert hashes()==before
 uninstalled=True
finally:
 # Reinstall even if an uninstall assertion fails; never intentionally leave it removed.
 result=subprocess.run([str(p/'output/Shutdown-Tool-v2.0.5-Setup.exe'),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-','/CURRENTUSER','/NOCLOSEAPPLICATIONS','/NORESTARTAPPLICATIONS','/DIR='+str(dest),'/TASKS='+tasks,'/LOG='+str(proof/'reinstall.log')],startupinfo=si,timeout=120)
 with winreg.OpenKey(winreg.HKEY_CURRENT_USER,run,0,winreg.KEY_SET_VALUE) as k:
  if startup_value is not None:winreg.SetValueEx(k,value,0,startup_value[1],startup_value[0])
  else:
   try:winreg.DeleteValue(k,value)
   except FileNotFoundError:pass
 assert result.returncode==0
assert uninstalled and hashes()==before
with winreg.OpenKey(winreg.HKEY_CURRENT_USER,key) as k:assert winreg.QueryValueEx(k,'DisplayVersion')[0]=='2.0.5'
assert hashlib.sha256((dest/'定时关机工具.exe').read_bytes()).digest()==hashlib.sha256((p/'dist_v2.0.5/定时关机工具.exe').read_bytes()).digest()
subprocess.run([sys.executable,str(p/'tools/package_smoke.py'),str(dest/'定时关机工具.exe')],check=True,timeout=90)
(proof/'reinstall.json').write_text(json.dumps(dict(uninstall_passed=True,reinstall_passed=True,user_data_unchanged=True,startup_value_restored=True,installed_version='2.0.5'),indent=2),encoding='utf-8')
print('PASS uninstall and reinstall; user data unchanged; startup setting restored')
