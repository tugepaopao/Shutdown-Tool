"""Presentation of real scheduler state; does not alter execution policy."""
import datetime as dt

def status(task,states,now=None):
    if not task:return '已停用','尚未启用'
    now=now or dt.datetime.now();raw=states.get(task['id'],'') or task.get('last_state','')
    if task.get('pending_missed'):return ('待确认' if task.get('missed_policy')=='ask' else '待补执行'),task.get('last_state','错过待确认')
    if raw=='加入队列失败，未执行':return '入队失败',raw
    if raw in ('已错过，未执行','预约保存失败，未执行','监控结果保存失败，未执行'):return ('已错过' if raw=='已错过，未执行' else '保存失败'),raw
    if task.get('end_date') and task['end_date']<now.date().isoformat():return '已结束','已到结束日期'
    if task.get('enabled'):
        if task.get('skip_date')==now.date().isoformat():return '今日跳过','今天已跳过；下次 '+task.get('next_at','').replace('T',' ')
        if task.get('mode')=='calendar':return '已启用','等待 '+task.get('next_at','').replace('T',' ')
        labels={'等待活动':'等待条件','传输中':'传输中','确认安静中':'确认中','等待无人操作':'等待空闲','前置程序运行中':'前置运行'}
        return labels.get(raw,'等待条件'),raw or '等待活动'
    labels={'已过期，未补执行':'已过期','已错过，未执行':'已错过','已加入队列':'已入队','已完成，加入队列':'已入队','等待超时，未执行':'已超时','监控失败，未执行':'监控失败','加入队列失败，未执行':'入队失败','预约保存失败，未执行':'保存失败','监控结果保存失败，未执行':'保存失败','重开后需重新启用任务链':'需重启用'}
    if raw in labels:return labels[raw],raw
    if raw=='已停用':return '已停用',raw
    if task.get('mode')=='calendar' and task.get('repeat','once')=='once':
        try:
            if dt.datetime.fromisoformat(task['at'])<=now:return '已过期','已过期，未补执行'
        except (ValueError,TypeError,KeyError):pass
    return '已停用','尚未启用'

def group(task,states):
    short,_=status(task,states)
    if short in ('待确认','待补执行','已错过','已超时','监控失败','入队失败','保存失败','需重启用'):return 'attention'
    return 'waiting' if task.get('enabled') else 'disabled'

def repeat_label(task,T):
    from i18n import feature_text
    tr=lambda t:feature_text(T,t)
    rule=task.get('repeat','once')
    if rule in ('weekly','custom'):
        names=('Mon','Tue','Wed','Thu','Fri','Sat','Sun') if T.lang=='EN' else ('一','二','三','四','五','六','日')
        return tr('每周')+' '+(' / '.join(names[d] for d in task.get('weekdays',[])))
    return tr({'once':'仅一次','daily':'每天','workdays':'每周一至周五','weekends':'每周六、周日'}.get(rule,'仅一次'))
