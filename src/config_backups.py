"""轮换保留10份正常配置；队列/倒计时变化不产生备份，不恢复执行状态。"""
import copy
import datetime as dt
import hashlib
import json
import os
import shutil
from pathlib import Path

KEEP=10
EXCLUDED={'queue','pending_timer','autostart','templates','automations','float_x','float_y','float_positioned','float_docked'}

def validate_settings(data):
    from app_config import DEFAULT_SETTINGS
    if not isinstance(data,dict):raise ValueError('配置必须是对象')
    for key,value in data.items():
        if key not in DEFAULT_SETTINGS:continue
        default=DEFAULT_SETTINGS[key]
        if type(value) is not type(default):raise ValueError('配置字段类型错误：'+key)
    for key,allowed in {'skin':set(__import__('skins').SKIN_CHOICES)|{'custom'},'language':{'CHS','CHT','EN'},'accent':{'blue','teal','green','orange','red','pink','purple','indigo'}}.items():
        if key in data and data[key] not in allowed:raise ValueError('配置字段值错误：'+key)
    if not 0<=data.get('quick_day_offset',1)<=7:raise ValueError('自定义预设日期越界')
    if not 40<=data.get('float_opacity',90)<=100:raise ValueError('悬浮窗不透明度越界')
    if any(abs(data.get(k,0))>200000 for k in ('float_x','float_y')):raise ValueError('悬浮窗位置越界')
    if any(len(data.get(k,[]))>200 for k in ('queue','templates','automations')):raise ValueError('任务数量超过上限')
    from task_store import normalize
    for key in ('queue','templates','automations'):
        for item in data.get(key,[]):normalize(item)

def portable(data):
    from app_config import DEFAULT_SETTINGS
    data=dict(data)
    if data.get('skin')=='custom':data['skin']='solid'
    settings={k:copy.deepcopy(data.get(k,v)) for k,v in DEFAULT_SETTINGS.items() if k not in EXCLUDED}
    jobs=copy.deepcopy(data.get('automations') or [])
    for j in jobs:
        j['enabled']=False
        for key in ('next_at','skip_date'):j.pop(key,None)
    return {'format':'haozai-backup','schema':1,'settings':settings,'templates':copy.deepcopy(data.get('templates') or []),'automations':jobs}

def folder(path=None):
    if path is None:
        from app_config import config_file
        path=config_file()
    return Path(path).parent/'auto_backups'

def files(path=None):return sorted(folder(path).glob('*.json'),key=lambda x:x.name,reverse=True)

def digest(data):return hashlib.sha256(json.dumps(portable(data),ensure_ascii=False,sort_keys=True).encode('utf-8')).hexdigest()[:16]

def before_save(path,data):
    validate_settings(data)
    p=Path(path);previous=None
    if p.exists():
        try:
            previous=json.loads(p.read_text(encoding='utf-8-sig'));validate_settings(previous)
        except (ValueError,TypeError):return  # load() 已保留损坏原文件。
    if previous is not None and digest(previous)==digest(data):return
    # 保存的是变更前最后一份正常设置；首次保存保存初始基线。
    value=previous if previous is not None else data
    code=digest(value);directory=folder(path);directory.mkdir(exist_ok=True,parents=True)
    if any(x.stem.endswith(code) for x in files(path)):return
    name=dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'-'+code+'.json'
    target=directory/name;tmp=target.with_suffix('.tmp')
    tmp.write_text(json.dumps(portable(value),ensure_ascii=False,indent=2),encoding='utf-8');os.replace(tmp,target)
    for old in files(path)[KEEP:]:old.unlink()

def recover_corrupt(path):
    p=Path(path)
    try:shutil.copy2(p,p.with_name('settings-corrupt-'+dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.json'))
    except OSError:return None,'配置损坏且原文件无法留存，请检查数据目录权限。'
    from task_store import read_backup
    for candidate in files(path):
        try:
            settings,templates,jobs=read_backup(candidate)
            recovered=dict(settings,templates=templates,automations=jobs,queue=[],pending_timer={})
            return recovered,'已恢复上一次正常配置；高级任务保持停用，损坏原文件已留存。'
        except (ValueError,OSError,TypeError):continue
    return None,'配置损坏，已使用默认设置；损坏原文件已留存，尚无可用备份。'
