"""任务校验、模板与可移植备份。导入不启动任务、不修改自启动项。"""
import copy
import datetime as dt
import json
import math
import os
import uuid
from app_config import DEFAULT_SETTINGS

ACTIONS={'lock','hibernate','close_program','shutdown','restart','logoff','sleep','monitor_off','run_program','play_sound','message'}
MODES={'countdown','datetime','interval','calendar','download','network','combined','chain'}
PARAMS=('close_program_path','program_path','sound_file','message_text','force_close_apps')
MAX_TASKS=200

def number(value,low,high,label):
    try:n=float(value)
    except (ValueError,TypeError):raise ValueError(label+'必须是数字')
    if not math.isfinite(n) or not low<=n<=high:raise ValueError(label+f'应在 {low:g}～{high:g} 之间')
    return n

def normalize(task):
    if not isinstance(task,dict):raise ValueError('任务格式错误')
    action=task.get('action','message');mode=task.get('mode','countdown')
    if action not in ACTIONS or mode not in MODES:raise ValueError('未知操作或定时方式')
    result={'action':action,'mode':mode,'name':str(task.get('name','')).strip()[:80]}
    for key in PARAMS:
        if key in task:
            if key=='force_close_apps':
                if not isinstance(task[key],bool):raise ValueError('强制关闭设置必须是布尔值')
                result[key]=task[key]
            else:
                if not isinstance(task[key],str) or len(task[key])>10000:raise ValueError('任务内容过长或格式错误')
                result[key]=task[key]
    if mode in ('countdown','interval'):result['seconds']=number(task.get('seconds',60),1,61*86400-1,'时长秒数')
    elif mode=='datetime':
        for key,high in [('weekday',6),('hour',23),('minute',59),('second',59)]:
            n=number(task.get(key,0),0,high,key)
            if n!=int(n):raise ValueError('时间字段必须是整数')
            result[key]=int(n)
    elif mode=='calendar':
        repeat=task.get('repeat','once')
        if repeat not in ('once','workdays','weekends','daily'):raise ValueError('重复规则错误')
        try:at=dt.datetime.fromisoformat(str(task.get('at','')))
        except ValueError:raise ValueError('日期格式应为 YYYY-MM-DD HH:MM:SS')
        if at.tzinfo is not None:raise ValueError('请使用本机当地时间')
        result.update(at=at.isoformat(timespec='seconds'),repeat=repeat)
    elif mode=='chain':
        path=str(task.get('prepare_path','')).strip()
        args=task.get('prepare_args','')
        if not path or len(path)>4096 or not os.path.isabs(path):raise ValueError('请选择备份程序的绝对路径')
        if not isinstance(args,str) or len(args)>4096:raise ValueError('程序参数过长')
        result.update(prepare_path=path,prepare_args=args,timeout_seconds=number(task.get('timeout_seconds',43200),60,7*86400,'最长等待秒数'))
    else:
        result['idle_seconds']=number(task.get('idle_seconds',60),5,3600,'连续安静秒数')
        result['timeout_seconds']=number(task.get('timeout_seconds',43200),60,7*86400,'最长等待秒数')
        if result['timeout_seconds']<=result['idle_seconds']:raise ValueError('最长等待必须大于安静时长')
        if mode=='download':
            folder=str(task.get('folder','')).strip()
            if not folder or len(folder)>4096:raise ValueError('请选择下载文件夹')
            result['folder']=os.path.abspath(folder)
        else:result['threshold_kib']=number(task.get('threshold_kib',10),0.1,102400,'网络阈值KiB/s')
        if mode=='combined':
            result['user_idle_seconds']=number(task.get('user_idle_seconds',600),60,86400,'无人操作秒数')
            if result['timeout_seconds']<=result['user_idle_seconds']:raise ValueError('最长等待必须大于无人操作时长')
    if task.get('id') is not None:result['id']=task['id']
    if task.get('source_automation'):result['source_automation']=str(task['source_automation'])
    return result

def snapshot(task,cfg):
    result=copy.deepcopy(task)
    for key in PARAMS:result.setdefault(key,cfg.get(key,DEFAULT_SETTINGS.get(key)))
    return normalize(result)

def next_calendar(task,now=None):
    now=now or dt.datetime.now();start=dt.datetime.fromisoformat(task['at'])
    if task.get('repeat','once')=='once':return start if start>now else None
    days={'workdays':set(range(5)),'weekends':{5,6},'daily':set(range(7))}[task['repeat']]
    candidate=start.replace(year=now.year,month=now.month,day=now.day)
    for offset in range(8):
        at=candidate+dt.timedelta(days=offset)
        if at>now and at>=start and at.weekday() in days and at.date().isoformat()!=task.get('skip_date'):return at
    # 开始日期可能还在未来。
    for offset in range(8):
        at=start+dt.timedelta(days=offset)
        if at>now and at.weekday() in days and at.date().isoformat()!=task.get('skip_date'):return at

def save_template(cfg,name,task):
    name=str(name).strip()
    if not name or len(name)>80:raise ValueError('模板名称应为1～80个字符')
    items=copy.deepcopy(cfg.get('templates') or [])
    if any(x.get('name')==name for x in items):raise ValueError('模板名称已存在，请换一个名称或编辑原模板')
    if len(items)>=MAX_TASKS:raise ValueError('模板已达200个上限')
    value=normalize(task);value.pop('id',None);value['name']=name;value['id']=uuid.uuid4().hex
    items.append(value);cfg['templates']=items;return value

def filter_logs(rows,query='',kind='',start='',end=''):
    for value in (start,end):
        if value:dt.date.fromisoformat(value)
    if start and end and start>end:raise ValueError('开始日期不能晚于结束日期')
    query=query.casefold().strip()
    return [r for r in rows if (not kind or r.get('kind')==kind)
            and (not start or str(r.get('ts',''))[:10]>=start)
            and (not end or str(r.get('ts',''))[:10]<=end)
            and (not query or query in ' '.join(str(r.get(k,'')) for k in ('ts','kind','text','detail')).casefold())]

def export_csv(path,rows):
    import csv
    with open(path,'w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['时间','事件','内容','详情','是否成功'])
        for row in rows:
            values=[str(row.get(k,'')) for k in ('ts','kind','text','detail','ok')]
            # 在 Excel 中按文本处理，防止日志文本被当作公式。
            writer.writerow(["'"+v if v.lstrip().startswith(('=','+','-','@')) else v for v in values])

def export_backup(cfg,path):
    settings={k:copy.deepcopy(cfg.get(k)) for k in DEFAULT_SETTINGS if k not in ('queue','pending_timer','templates','automations','autostart')}
    data={'format':'haozai-backup','schema':1,'settings':settings,'templates':copy.deepcopy(cfg.get('templates') or []),
          'automations':copy.deepcopy(cfg.get('automations') or [])}
    for job in data['automations']:job['enabled']=False;job.pop('next_at',None)
    tmp=str(path)+'.tmp'
    with open(tmp,'w',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2)
    os.replace(tmp,path)

def read_backup(path):
    if os.path.getsize(path)>2*1024*1024:raise ValueError('备份文件不能超过2MB')
    with open(path,encoding='utf-8-sig') as f:data=json.load(f)
    if not isinstance(data,dict) or data.get('format')!='haozai-backup' or data.get('schema')!=1:raise ValueError('不支持的备份格式或版本')
    source=data.get('settings',{});settings={}
    if not isinstance(source,dict):raise ValueError('设置格式错误')
    excluded={'queue','pending_timer','templates','automations','autostart'}
    for key,value in source.items():
        if key not in DEFAULT_SETTINGS or key in excluded:continue
        default=DEFAULT_SETTINGS[key]
        if isinstance(default,bool) and not isinstance(value,bool):raise ValueError(key+'类型错误')
        if type(default) is int:
            high={'cd_days':60,'cd_hours':23,'cd_minutes':59,'cd_seconds':59,'dt_weekday':6,'dt_hour':23,'dt_minute':59,'dt_second':59,'iv_hours':23,'iv_minutes':59,'iv_seconds':59,'toast_seconds':600,'quick_day_offset':7,'float_opacity':100,'float_x':200000,'float_y':200000}.get(key,86400)
            low=-200000 if key in ('float_x','float_y') else 40 if key=='float_opacity' else 3 if key=='toast_seconds' else 0
            if type(value) is not int or not low<=value<=high:raise ValueError(key+'范围错误')
        if isinstance(default,str) and (not isinstance(value,str) or len(value)>10000):raise ValueError(key+'类型错误')
        settings[key]=value
    enums={'language':{'CHS','CHT','EN'},'theme_mode':{'light','dark','system'},'font_size':{'small','normal','large','huge'},'accent':{'blue','teal','green','orange','red','pink','purple','indigo'},'action':ACTIONS,'mode':{'countdown','datetime','interval'}}
    for key,values in enums.items():
        if key in settings and settings[key] not in values:raise ValueError(key+'值不受支持')
    templates=[];jobs=[]
    for key,target in [('templates',templates),('automations',jobs)]:
        raw=data.get(key,[])
        if not isinstance(raw,list) or len(raw)>MAX_TASKS:raise ValueError('任务清单格式错误或超过200个')
        names=set()
        for task in raw:
            task=normalize(task)
            if not task['name'] or task['name'] in names:raise ValueError('任务名称为空或重复')
            names.add(task['name']);task['id']=uuid.uuid4().hex
            if key=='automations':
                if task['mode'] not in ('calendar','download','network','combined','chain'):raise ValueError('高级任务方式错误')
                task['enabled']=False
            target.append(task)
    from desktop_services import parse_hotkey
    for key in ('hotkey_show','hotkey_pause','hotkey_resume'):
        if key in settings:parse_hotkey(settings[key])
    settings['float_positioned']=False
    settings['float_enabled']=False
    settings['hotkeys_enabled']=False
    settings['keep_display_on']=False
    settings['quick_at_today']='22:00'
    settings['theme_mode']='light'
    settings['font_size']='normal'
    return settings,templates,jobs

def import_backup(cfg,path):
    settings,templates,jobs=read_backup(path)
    old=copy.deepcopy(cfg.data)
    cfg.update(settings);cfg['templates']=templates;cfg['automations']=jobs
    if not cfg.save():cfg.data=old;raise OSError('保存失败，原设置已保留')
    return len(templates),len(jobs)
