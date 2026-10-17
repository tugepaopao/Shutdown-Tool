"""Verify an explicitly authorized in-place upgrade with rollback copies."""
import os,sys,json,hashlib,shutil,subprocess,datetime,winreg
from pathlib import Path
import psutil
p=Path(__file__).resolve().parent.parent
key=r'Software\Microsoft\Windows\CurrentVersion\Uninstall\{8F3C1A72-5B4E-4C9D-9E21-7A6B0C5D3F10}_is1'
with winreg.OpenKey(winreg.HKEY_CURRENT_USER,key) as k:
    dest=Path(winreg.QueryValueEx(k,'InstallLocation')[0]).resolve()
    old_version=winreg.QueryValueEx(k,'DisplayVersion')[0]
assert old_version=='2.0.4','Only the inspected 2.0.4 installation may be upgraded'
assert dest.is_dir() and (dest/'定时关机工具.exe').is_file()
for proc in psutil.process_iter(['name']):assert proc.info['name']!='定时关机工具.exe','Close app before upgrading'
proof=p/'核验/package-v205';proof.mkdir(parents=True,exist_ok=True)
backup=proof/('before-upgrade-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'));backup.mkdir()
data=Path(os.environ['APPDATA'])/'HaozaiziShutdownTool'
def digest_tree(folder):return {str(f.relative_to(folder)):hashlib.sha256(f.read_bytes()).hexdigest() for f in folder.rglob('*') if f.is_file()}
before=digest_tree(data) if data.exists() else {}
if data.exists():shutil.copytree(data,backup/'user-data')
shutil.copy2(dest/'定时关机工具.exe',backup/'定时关机工具-v2.0.4.exe')
startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
result=subprocess.run([str(p/'output/Shutdown-Tool-v2.0.5-Setup.exe'),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-','/CURRENTUSER','/NOCLOSEAPPLICATIONS','/NORESTARTAPPLICATIONS','/DIR='+str(dest),'/LOG='+str(proof/'upgrade.log')],startupinfo=startup,timeout=120)
assert result.returncode==0,result.returncode
with winreg.OpenKey(winreg.HKEY_CURRENT_USER,key) as k:assert winreg.QueryValueEx(k,'DisplayVersion')[0]=='2.0.5'
after=digest_tree(data) if data.exists() else {}
assert before==after,'Installer changed user data; backup retained'
assert hashlib.sha256((dest/'定时关机工具.exe').read_bytes()).digest()==hashlib.sha256((p/'dist_v2.0.5/定时关机工具.exe').read_bytes()).digest()
assert (dest/'unins000.exe').exists()
subprocess.run([sys.executable,str(p/'tools/package_smoke.py'),str(dest/'定时关机工具.exe')],check=True,timeout=90)
(proof/'upgrade.json').write_text(json.dumps(dict(from_version='2.0.4',to_version='2.0.5',installer_exit=0,user_data_unchanged=True,installed_binary_matches=True,uninstaller_present=True,uninstall_executed=False),indent=2),encoding='utf-8')
print('PASS in-place upgrade, user data hashes unchanged, installed EXE smoke passed')
