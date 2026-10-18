"""Isolated log/calendar behavior, bounded rendering and transition checks."""
import os,sys,tempfile,time,json,datetime as dt,csv,tkinter as tk
from pathlib import Path
from unittest.mock import patch
p=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(p/'src'));sys.stdout.reconfigure(encoding='utf-8')
temp=tempfile.TemporaryDirectory(prefix='shutdown-v208-');os.environ['APPDATA']=temp.name
from main import enable_dpi_awareness
enable_dpi_awareness()
import actions,autostart,run_log
from ui_main import App
from ui_date_picker import DatePicker,pick_date
from ui_localize import messagebox
from capture_window import capture
if len(sys.argv)>1:
 OriginalTk=tk.Tk
 class ScaledTk(OriginalTk):
  def __init__(self,*args,**kwargs):
   super().__init__(*args,**kwargs);self.tk.call('tk','scaling',float(sys.argv[1])*96/72)
 tk.Tk=ScaledTk
App._init_tray=lambda a:None;autostart.set_enabled=lambda *a:True;actions.perform=lambda *a,**k:(_ for _ in ()).throw(AssertionError('Real action forbidden'))
a=App({'given':True,'action':'message'});a.cfg.update(dict(confirm_on_exit=False,autostart=False));checks=[];errors=[];a.root.report_callback_exception=lambda t,v,b:errors.append(str(v))
out=p/'核验/v208';out.mkdir(parents=True,exist_ok=True)
if len(sys.argv)>1:out=out/('scale-'+sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
def pump(seconds=.1):
 end=time.perf_counter()+seconds
 while time.perf_counter()<end:a.root.update();time.sleep(.002)
def check(name,ok):checks.append((name,bool(ok)));print(('PASS ' if ok else 'FAIL ')+name,flush=True);assert ok,name
def seed():
 return [dict(ts=f'2026-10-{i//20+1:02d} 08:{i%60:02d}:00',kind='error' if i%10==0 else 'done',text=('资料备份' if i%2 else '休息提醒')+str(i),detail='完整错误详情\n'+('测试内容 '*500) if i%10==0 else '执行完成',ok=i%10!=0) for i in range(500)]
try:
 pump();rows=seed();path=Path(run_log.log_file());path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
 w=a.open_log();pump()
 check('500 records retained',len(w.filtered_rows)==500)
 check('rendering bounded by visible rows',len(w.canvas.find_all())<100)
 check('date fields are read only',str(w.start_input.entry.cget('state'))=='readonly')
 before=w.start_date.get();w.start_input.entry.insert(0,'bad');check('manual typing cannot alter date',w.start_date.get()==before)
 w.select_index(250);pump();pos=w.canvas.yview();selected=w.selected;paints=w.render_count
 with patch.object(run_log,'entries',wraps=run_log.entries) as reads:
  for _ in range(10):w.refresh()
  pump();check('unchanged refresh avoids file read and painting',reads.call_count==0 and w.render_count==paints)
 check('refresh preserves scroll and selection',pos==w.canvas.yview() and selected==w.selected)
 with patch.object(w,'refresh',wraps=w.refresh) as refresh:
  for value in ('资','资料','资料备份'):w.query.set(value)
  pump(.22);check('rapid search merges into one filter',refresh.call_count==1)
 check('content search correct',len(w.filtered_rows)==250)
 w.query.set('完整错误详情');w.refresh();check('details searchable',len(w.filtered_rows)==50)
 w._reset();w.start_date.set('2026-10-02');w.end_date.set('2026-10-03');w.refresh();check('date boundaries inclusive',len(w.filtered_rows)==40)
 w.kind.set(a.T('log_kind_error'));w.refresh();check('date and event filters combine',len(w.filtered_rows)==4)
 export=Path(temp.name)/'filtered.csv'
 with patch('ui_log.filedialog.asksaveasfilename',return_value=str(export)),patch.object(messagebox,'showinfo'):w._export()
 with export.open(encoding='utf-8-sig',newline='') as f:exported=list(csv.reader(f))
 check('CSV exports all filtered data',len(exported)==5 and exported[1][3].startswith('完整错误详情'))
 w._reset();w.select_index(490);pump();w._show_detail();pump();detail=next(x for x in w.winfo_children() if isinstance(x,tk.Toplevel));check('detail modal owns focus',w.grab_current() is detail)
 def walk(x):
  for c in x.winfo_children():
   yield c;yield from walk(c)
 text=next(x for x in walk(detail) if isinstance(x,tk.Text));check('full long detail preserved',rows[490]['detail'] in text.get('1.0','end'));detail.destroy();pump();check('closing detail releases modal',w.grab_current() is None)
 w.start_date.set('2026-10-01');w.end_date.set('2026-10-17');w.refresh();w.canvas.yview_moveto(0);w.select_index(0);pump();capture(w).save(out/'execution-log.png')
 picker=DatePicker(w,a,'2026-10-17',title='选择结束日期',allow_clear=True,minimum='2026-10-01',range_start='2026-10-01',range_end='2026-10-17',endpoint='end');pump();capture(picker).save(out/'date-range.png')
 check('calendar range prevents reversed dates',not picker.valid(dt.date(2026,9,30)))
 check('calendar footer visible and inside window',picker.footer.winfo_viewable() and picker.footer.winfo_y()+picker.footer.winfo_height()<=picker.winfo_height())
 picker.minimum=None;picker.year,picker.month=2024,2;picker.render();pump()
 box=next(box for box,value in picker.hits if value==dt.date(2024,2,29));picker.calendar.event_generate('<Button-1>',x=int((box[0]+box[2])/2),y=int((box[1]+box[3])/2));pump();check('leap day selected by click',picker.selected==dt.date(2024,2,29))
 picker.navigate(-1);check('month navigation works',picker.month==1)
 picker.year,picker.month=2026,1;picker.navigate(-1);check('year rollover works',(picker.year,picker.month)==(2025,12))
 picker.choose_month();picker.choose_month();pump();check('year selection available',picker.mode=='years' and len(picker.hits)==12)
 picker.destroy();pump();check('cancel keeps source date',w.end_date.get()=='2026-10-17')
 v=tk.StringVar(w,value='2026-10-01')
 def accept_day():
  pick=next(x for x in w.winfo_children() if isinstance(x,DatePicker));pick.selected=dt.date(2026,10,8);pick.accept()
 w.after(80,accept_day);pick_date(w,a,v);check('confirmation commits selected date',v.get()=='2026-10-08')
 def clear_day():next(x for x in w.winfo_children() if isinstance(x,DatePicker)).finish('')
 w.after(80,clear_day);pick_date(w,a,v,allow_clear=True);check('unlimited clears date',v.get()=='')
 w._reset();w.canvas.yview_moveto(.3);pump();pos=w.canvas.yview();run_log.add('info','新日志');w.refresh();pump();check('new log detected without resetting reading position',w.filtered_rows[-1]['text']=='新日志' and abs(w.canvas.yview()[0]-pos[0])<.01)
 with patch.object(messagebox,'askyesno',return_value=False):w._clear()
 check('clear cancellation preserves records',len(run_log.entries(500))==500)
 with patch.object(messagebox,'askyesno',return_value=True):w._clear()
 pump();check('clear updates empty state',not w.filtered_rows)
 w.query.set('pending');w.destroy();pump(.22);check('close cancels pending filter',not errors)
 center=a.open_task_center();pump();panel=center.panels['queue']
 with patch.object(panel,'refresh',wraps=panel.refresh) as refresh:
  center.select_tab('templates');center.select_tab('queue');pump();check('tab event does not refresh selected page twice',refresh.call_count==1)
 from ui_window import activate_dialog
 import ui_window
 with patch.object(ui_window,'_main_opacity',wraps=ui_window._main_opacity) as opacity:
  for _ in range(10):activate_dialog(center)
  pump();check('visible window reuse never toggles opacity',opacity.call_count==0)
 center.iconify();pump();a.open_task_center();pump();check('minimized window fully restored',center.state()=='normal' and center._main_opacity==255)
 a.cfg['templates']=[dict(id=str(i),name='模板'+str(i),action='message',message_text='test',mode='countdown',seconds=60,favorite=False) for i in range(200)]
 center.select_tab('templates');pump();cards=center.panels['templates'].cards;view=center.panels['templates']
 check('large library preserves all model rows',len(cards.rows)==len(cards.tv.get_children())==200)
 check('large library builds only initial visible controls',sum('name' in row for row in cards.rows.values())<20)
 cards.canvas.yview_moveto(1);pump();check('scroll materializes last row','name' in cards.rows['199'])
 with patch.object(view,'edit') as edit:
  cards.rows['199']['edit'].invoke();pump();check('lazy edit targets correct item',edit.call_count==1 and view.selected()['id']=='199')
 view.favorite();pump();check('lazy favorite updates actual task',next(t for t in a.cfg['templates'] if t['id']=='199')['favorite'])
 cards.query.set('模板199');pump(.22);check('lazy search retains selected task',list(cards.rows)==['199'] and view.selected()['id']=='199')
 cards.query.set('');pump(.22);cards.canvas.yview_moveto(0);pump();check('return to first row restores controls','name' in cards.rows['0'])
 capture(center).save(out/'large-templates.png')
 check('no callback exceptions',not errors or print(errors))
 (out/'results.json').write_text(json.dumps(dict(checks=checks,errors=errors),ensure_ascii=False,indent=2),encoding='utf-8')
finally:
 a.engine.stop();a.automation.close();a.floating.close();a.desktop.close();a.display_awake.close();a.root.destroy();temp.cleanup()
