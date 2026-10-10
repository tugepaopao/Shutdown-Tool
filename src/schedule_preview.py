"""未来7个自然日（含今天）的预约；条件/程序链没有可预知时刻。"""
import copy
import datetime as dt
from collections import Counter
from task_store import next_calendar

def schedule_preview(jobs,now=None,days=7):
    now=now or dt.datetime.now();end=dt.datetime.combine(now.date()+dt.timedelta(days=days),dt.time())
    rows=[]
    for job in jobs:
        if not job.get('enabled') or job.get('mode')!='calendar':continue
        cursor=now
        for _ in range(days+1):
            at=next_calendar(job,cursor)
            if at is None or at>=end:break
            rows.append({'at':at,'id':job['id'],'name':job['name'],'action':job['action'],'task':copy.deepcopy(job)})
            if job.get('repeat','once')=='once':break
            cursor=at
    rows.sort(key=lambda r:(r['at'],r['name']))
    counts=Counter(r['at'].replace(second=0,microsecond=0) for r in rows)
    for row in rows:row['overlap']=counts[row['at'].replace(second=0,microsecond=0)]>1
    return rows
