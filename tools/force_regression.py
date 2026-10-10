import os,sys,tempfile,subprocess,time,json,shutil
from pathlib import Path
from unittest.mock import patch
p=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(p/'src'));sys.stdout.reconfigure(encoding='utf-8')
import psutil,program_control as pc
checks=[]
def check(n,v):checks.append([n,bool(v)]);print(('PASS ' if v else 'FAIL ')+n,flush=True);assert v,n
with tempfile.TemporaryDirectory(prefix='v168-force-') as folder:
 folder=Path(folder);code=folder/'fixture.cs';code.write_text('''using System;using System.IO;using System.Diagnostics;using System.Threading;class T{static void Main(string[] a){if(a.Length>0){Thread.Sleep(Timeout.Infinite);return;}Process.Start(Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"Worker.exe"),"child");Thread.Sleep(Timeout.Infinite);}}''')
 target=folder/'Target.exe';other=folder/'Other.exe';worker=folder/'Worker.exe';compiler=Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
 subprocess.run([str(compiler),'/nologo','/target:winexe',f'/out:{target}',str(code)],capture_output=True,check=True);shutil.copy2(target,other);shutil.copy2(target,worker)
 children=[psutil.Popen([str(target)]),psutil.Popen([str(target)]),psutil.Popen([str(other)])];owned=[]
 try:
  deadline=time.monotonic()+10
  while time.monotonic()<deadline:
   owned=[x for parent in children for x in parent.children(recursive=True)]
   if len(owned)==3:break
   time.sleep(.05)
  check('background fixtures have children',len(owned)==3)
  other_child=children[2].children()[0]
  target_children=[x for x in owned if x.pid!=other_child.pid]
  check('target works with no visible windows',not any(w['path']==pc.canonical(target) for w in pc.running_programs()))
  ok,err=pc.close_program(str(target));check('force closes hidden/tray-style roots',ok)
  check('all selected instances exited',all(not c.is_running() for c in children[:2]))
  check('different-exe child processes exited',all(not c.is_running() for c in target_children))
  check('unrelated root still alive',children[2].is_running())
  check('unrelated same-name child still alive',other_child.is_running())
  check('missing target reports failure',not pc.close_program(str(target))[0])
 finally:
  for child in [*owned,*children]:
   try:
    if child.is_running():child.kill()
   except psutil.NoSuchProcess:pass
  psutil.wait_procs([*owned,*children],timeout=5)
 class Fake:
  pid=987654
  def exe(self):return str(target)
  def create_time(self):return 1
  def children(self,recursive=False):return []
  def kill(self):raise psutil.AccessDenied(self.pid)
  def is_running(self):return True
 with patch('program_control.matching_processes',return_value=[Fake()]),patch('program_control.psutil.wait_procs',return_value=([],[Fake()])):
  check('permission failure never reported as success','管理员' in pc.close_program(str(target))[1])
 class Reused(Fake):
  calls=0
  def create_time(self):self.calls+=1;return self.calls
  def kill(self):raise AssertionError('Reused pid must never be killed')
 reused=Reused()
 with patch('program_control.matching_processes',side_effect=[[reused],[]]),patch('program_control.psutil.wait_procs',return_value=([],[])):
  check('PID identity rechecked before force end',pc.close_program(str(target))[0])
(p/'tools/v168-force-results.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8');print('All',len(checks),'passed')
