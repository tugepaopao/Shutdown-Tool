"""Six stable quick slots; legacy settings migrate without changing their meaning."""
import copy,datetime as dt

def defaults(cfg=None):
    cfg=cfg or {}
    from app_config import parse_hm
    h,m=parse_hm(cfg.get('quick_at_tomorrow','08:00'),8,0)
    return [dict(kind='duration',seconds=v) for v in (1800,3600,7200)]+[dict(kind='clock',day_offset=0,hour=h,minute=m) for h,m in ((18,0),(22,0))]+[dict(kind='clock',day_offset=int(cfg.get('quick_day_offset',1)),hour=h,minute=m)]

def validate(values):
    if not isinstance(values,list) or len(values)!=6:raise ValueError('快捷预设应包含六项')
    result=[]
    for value in values:
        if not isinstance(value,dict):raise ValueError('快捷预设格式错误')
        if value.get('kind')=='duration':
            seconds=value.get('seconds')
            if type(seconds) is not int or not 1<=seconds<=60*86400:raise ValueError('时长应在1秒至60天之间')
            result.append(dict(kind='duration',seconds=seconds))
        elif value.get('kind')=='clock':
            day,h,m=(value.get(k) for k in ('day_offset','hour','minute'))
            if any(type(v) is not int for v in (day,h,m)) or not(0<=day<=7 and 0<=h<=23 and 0<=m<=59):raise ValueError('快捷预设日期或时间无效')
            result.append(dict(kind='clock',day_offset=day,hour=h,minute=m))
        else:raise ValueError('快捷预设方式无效')
    return result

def get(cfg):return copy.deepcopy(validate(cfg.get('quick_presets')) if cfg.get('quick_presets') else defaults(cfg))

def spec(value):
    if value['kind']=='duration':return ('sec',value['seconds'])
    day=value['day_offset'];h=value['hour'];m=value['minute']
    return ('at',h,m) if day==0 else ('tmr',h,m) if day==1 else ('custom',day,h,m)

def caption(value,T):
    from i18n import feature_text,format_remain
    if value['kind']=='duration':
        seconds=value['seconds']
        if seconds%3600==0:text=f'{seconds//3600}小时后';en=f'{seconds//3600}h later'
        elif seconds%60==0:text=f'{seconds//60}分钟后';en=f'{seconds//60}min later'
        else:text=f'{seconds}秒后';en=f'{seconds}s later'
        return en if T.lang=='EN' else feature_text(T,text)
    day=value['day_offset'];label=('今天','明天','后天')[day] if day<3 else str(day)+'天后'
    if T.lang=='EN':label=('Today','Tomorrow','In 2 days')[day] if day<3 else f'In {day} days'
    else:label=feature_text(T,label)
    return label+f" {value['hour']:02}:{value['minute']:02}"
