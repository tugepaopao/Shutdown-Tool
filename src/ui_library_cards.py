"""Template and advanced-task cards sharing the queue's visual language."""
import datetime as dt
import math
import tkinter as tk
from tkinter import ttk, font as tkfont
from PIL import Image, ImageDraw, ImageTk
from theme import theme, flat_button, enable_button
from ui_cozy import CozyFrame, scale, cozy_icon
from ui_dialog_palette import COLORS as C
from ui_runtime_context import blossom
from ui_queue_cards import CircleButton
from i18n import feature_text


class StatusBadge(tk.Canvas):
    def __init__(self,parent,text):
        super().__init__(parent,bg=parent.cget('bg'),highlightthickness=0,bd=0)
        self.text=text;self.fill=C['hover'];self.ink=C['fg'];self._stamp=None
        self.bind('<Configure>',lambda e:self.redraw())

    def redraw(self):
        w,h=self.winfo_width(),self.winfo_height();bg=self.master.cget('bg')
        stamp=(w,h,bg,self.text,self.fill,self.ink)
        if w<2 or h<2 or stamp==self._stamp:return
        self._stamp=stamp;self.configure(bg=bg);self.delete('all')
        im=Image.new('RGB',(w*4,h*4),bg);draw=ImageDraw.Draw(im)
        draw.rounded_rectangle((0,0,w*4-1,h*4-1),radius=h*2,fill=self.fill)
        self._photo=ImageTk.PhotoImage(im.resize((w,h),Image.Resampling.LANCZOS),master=self)
        self.create_image(0,0,image=self._photo,anchor='nw')
        self.create_text(w/2,h/2,text=self.text,fill=self.ink,font=theme.font(delta=-2))


class FavoriteButton(CircleButton):
    def _paint(self):
        self._draw_job=None
        if not self.winfo_exists():return
        w=max(1,self.winfo_width());h=max(1,self.winfo_height());on=self.cget('text')=='★'
        if min(w,h)<5:return
        bg=self.master.cget('bg');key=(w,h,on,self._state,self._hovering,self._pressed,self._keyboard_focus,bg)
        if key==self._circle_stamp:return
        self._circle_stamp=key;q=4;size=min(w,h)*q;cx=w*q/2;cy=h*q/2
        im=Image.new('RGB',(w*q,h*q),bg);draw=ImageDraw.Draw(im)
        color=C['hover'] if self._hovering else C['selected'] if on else '#ECE7FC'
        r=size/2-2*q;draw.ellipse((cx-r,cy-r,cx+r,cy+r),fill=color,outline=theme.accent if self._keyboard_focus else color,width=q)
        points=[]
        for i in range(10):
            angle=-math.pi/2+i*math.pi/5;radius=size*(.25 if i%2==0 else .11)
            points.append((cx+radius*math.cos(angle),cy+radius*math.sin(angle)))
        ink='white' if on else C['muted'];draw.polygon(points,fill=ink if on else None,outline=ink,width=2*q)
        self._circle_photo=ImageTk.PhotoImage(im.resize((w,h),Image.Resampling.LANCZOS),master=self)
        tk.Button.configure(self,image=self._circle_photo,bg=bg,activebackground=bg)


class LibraryCards:
    def __init__(self, view):
        self.view=view;self.app=view.app;self.advanced=view.advanced;self.s=scale(view)
        self.rows={};self.signature=None;self._painting=False;self._selected_key=None
        # Keep the existing task selection API without displaying a second table.
        self.tv=view.tv=ttk.Treeview(view,columns=('name','action','when','state'),show='headings',selectmode='browse')
        self.tv.bind('<<TreeviewSelect>>',lambda e:self.selection_changed())
        self.summary=CozyFrame(view,bg=C['card']);self.summary.pack(fill='x',padx=4,pady=(3,8))
        inner=tk.Frame(self.summary,bg=C['card']);inner.pack(fill='x',padx=12,pady=10)
        self.flower=tk.Label(inner,bg=C['card'])
        self.flower._photo=ImageTk.PhotoImage(blossom(round(48*self.s),0,False),master=view)
        self.flower.config(image=self.flower._photo);self.flower.pack(side='left',padx=(0,12))
        right=tk.Frame(inner,bg=C['card'],width=round((118 if self.advanced else 92)*self.s))
        right.pack(side='right',fill='y');right.pack_propagate(False)
        self.summary_more=CircleButton(right,lambda:self.menu(self.summary_more))
        self.summary_more.place(relx=1,x=-round(38*self.s),y=round(12*self.s),width=round(38*self.s),height=round(38*self.s))
        if self.advanced:
            self.summary_status=self.badge(right,'');self.summary_status.place(x=0,y=round(18*self.s),width=round(72*self.s),height=round(27*self.s))
        else:
            self.favorite_button=FavoriteButton(right,lambda:view.safe(view.favorite))
            self.favorite_button.place(x=0,y=round(12*self.s),width=round(38*self.s),height=round(38*self.s))
        texts=tk.Frame(inner,bg=C['card']);texts.pack(side='left',fill='both',expand=True)
        self.eyebrow=self.label(texts,'下次执行' if self.advanced else '我的模板',small=True);self.eyebrow.pack(fill='x')
        self.title=self.label(texts,'',bold=True);self.title.config(font=theme.font(delta=1,bold=True));self.title.pack(fill='x',pady=(4,3))
        self.subtitle=self.label(texts,'',small=True);self.subtitle.pack(fill='x')
        self.title.bind('<Configure>',lambda e:self.fit(self.title,getattr(self,'_title',''),e.width))
        self.subtitle.bind('<Configure>',lambda e:self.fit(self.subtitle,getattr(self,'_subtitle',''),e.width))
        self.card=CozyFrame(view,bg=C['card']);self.card.pack(fill='both',expand=True,padx=4)
        self.bottom=tk.Frame(view,bg=C['bg']);self.bottom.pack(side='bottom',before=self.card,fill='x',padx=4,pady=(8,4))
        actions=[('新建任务',view.add,'accent'),('启用／停用',view.toggle,'normal')] if self.advanced else [('加入队列',view.use,'accent'),('保存主页面当前设定',view.capture,'normal')]
        self.buttons=[]
        for i,(title,fn,kind) in enumerate(actions+[('更多操作',lambda:self.menu(self.buttons[2]),'normal')]):
            self.bottom.columnconfigure(i,weight=1,uniform='libraryactions')
            b=flat_button(self.bottom,self.tr(title),lambda fn=fn:view.safe(fn),kind=kind,font=theme.font(delta=-1),padx=4,pady=7)
            b.grid(row=0,column=i,sticky='ew',padx=(0,5) if i<2 else 0)
            if i>0:b._selection_outline='#D8CDEF'
            self.buttons.append(b)
        arrow=Image.new('RGBA',(48,48));draw=ImageDraw.Draw(arrow)
        draw.line([(10,17),(24,31),(38,17)],fill=C['fg'],width=5,joint='curve')
        self.buttons[-1]._theme_photo=ImageTk.PhotoImage(arrow.resize((round(11*self.s),round(11*self.s)),Image.Resampling.LANCZOS),master=view)
        self.buttons[-1].config(image=self.buttons[-1]._theme_photo,compound='right')
        self.details=CozyFrame(self.card,bg=C['input'],radius=10) if self.advanced else tk.Frame(self.card,bg=C['card'])
        self.details.pack(side='bottom',fill='x',padx=14,pady=10)
        if self.advanced:
            self.next_label=self.label(self.details,'',small=True);self.next_label.pack(fill='x',padx=10,pady=(8,4))
            self.repeat_label=self.label(self.details,'',small=True);self.repeat_label.pack(fill='x',padx=10,pady=(0,8))
            for label in (self.next_label,self.repeat_label):
                label.config(bg=C['input']);label.bind('<Configure>',lambda e,w=label:self.fit(w,getattr(w,'_full_text',''),e.width))
        else:
            self.selection_label=self.label(self.details,'',small=True);self.selection_label.pack(side='left')
        wrap=tk.Frame(self.card,bg=C['card']);wrap.pack(fill='both',expand=True,padx=10,pady=(10,0))
        wrap.columnconfigure(0,weight=1);wrap.rowconfigure(1,weight=1)
        self.header=tk.Frame(wrap,bg=C['card'],height=round(26*self.s));self.header.grid(row=0,column=0,sticky='ew');self.header.pack_propagate(False)
        self.headings=[self.label(self.header,t,small=True) for t in ('名称','操作','执行方式','状态')]
        self.canvas=tk.Canvas(wrap,bg=C['card'],highlightthickness=0,height=round(120*self.s),takefocus=True)
        self.canvas.grid(row=1,column=0,sticky='nsew')
        self.scroll=ttk.Scrollbar(wrap,command=self.canvas.yview);self.scroll.grid(row=1,column=1,sticky='ns')
        self.canvas.config(yscrollcommand=self.scroll.set)
        self.body=tk.Frame(self.canvas,bg=C['card']);self.body_item=self.canvas.create_window(0,0,window=self.body,anchor='nw')
        self.body.bind('<Configure>',lambda e:self.canvas.config(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>',lambda e:self.layout(e.width))
        self._wheel_id=view.owner.bind('<MouseWheel>',self.wheel,add='+')
        view.bind('<Destroy>',self.cleanup,add='+')
        for key,step in (('<Up>',-1),('<Down>',1)):
            self.canvas.bind(key,lambda e,step=step:self.move_selection(step))
        self.canvas.bind('<Return>',lambda e:view.safe(view.edit))
        self.empty=self.label(self.body,'暂无高级任务，点击“新建任务”开始' if self.advanced else '暂无模板，可保存主页面当前设定',small=True)

    def tr(self,text):return feature_text(self.app.T,text)

    def wheel(self,event):
        widget=event.widget
        while widget is not None and widget is not self.view:
            widget=getattr(widget,'master',None)
        if widget is self.view and self.view.winfo_viewable():
            if self.canvas.bbox('all') and self.body.winfo_height()>self.canvas.winfo_height():
                self.canvas.yview_scroll(-int(event.delta/120),'units')
            return 'break'

    def cleanup(self,event):
        if event.widget is self.view and self._wheel_id:
            self.view.owner.unbind('<MouseWheel>',self._wheel_id);self._wheel_id=None

    def label(self,parent,text,small=False,bold=False):
        return tk.Label(parent,text=self.tr(text),bg=C['card'],fg=C['muted'] if small else C['fg'],font=theme.font(delta=-2 if small else 0,bold=bold),anchor='w',bd=0,padx=0)

    def badge(self,parent,text):
        return StatusBadge(parent,self.tr(text))

    def paint_badge(self,badge,text,enabled=None):
        bg,fg=('#C8E8D2','#285F40') if enabled is True else ('#E3DFEC',C['muted']) if enabled is False else (C['hover'],C['fg'])
        badge.text=self.tr(text);badge.fill=bg;badge.ink=fg;badge.redraw()

    def fit(self,label,text,width):
        font=tkfont.Font(root=self.view,font=label.cget('font'));width=max(0,width-4)
        result=text
        if font.measure(text)>width:
            lo,hi=0,len(text)
            while lo<hi:
                mid=(lo+hi+1)//2
                if font.measure(text[:mid]+'…')<=width:lo=mid
                else:hi=mid-1
            result=text[:lo]+'…' if width else ''
        if label.cget('text')!=result:label.config(text=result)

    def schedule(self,task):
        if task.get('mode') in ('countdown','interval'):
            seconds=int(task['seconds'])
            if seconds%60==0:value=self.tr('{n} 分钟').format(n=seconds//60)
            else:value=self.tr('{n} 秒').format(n=seconds)
            return self.tr('倒计时 {t}' if task['mode']=='countdown' else '每 {t} 循环').format(t=value)
        if task.get('mode')!='calendar':return self.app.describe_when(task)
        repeat={'once':'仅一次','daily':'每天','workdays':'每周一至周五','weekends':'每周六、周日'}.get(task.get('repeat','once'),'仅一次')
        at=dt.datetime.fromisoformat(task['at'])
        return (at.strftime('%Y-%m-%d %H:%M') if task.get('repeat','once')=='once' else self.tr(repeat)+' '+at.strftime('%H:%M'))

    def next_text(self,task):
        if not task:return self.tr('暂无已启用任务')
        if not task.get('enabled'):return self.tr('尚未启用')
        if task.get('mode')!='calendar':return self.tr('条件满足后执行')
        value=task.get('next_at')
        if not value:return self.tr('暂无预约')
        try:at=dt.datetime.fromisoformat(value)
        except (TypeError,ValueError):return self.tr('暂无预约')
        day=(at.date()-dt.date.today()).days
        return (self.tr('今天') if day==0 else self.tr('明天') if day==1 else at.strftime('%Y-%m-%d'))+' '+at.strftime('%H:%M')

    def next_task(self):
        enabled=[t for t in self.view.items() if t.get('enabled')]
        scheduled=[t for t in enabled if t.get('mode')=='calendar' and t.get('next_at')]
        return min(scheduled,key=lambda t:t['next_at']) if scheduled else next(iter(enabled),None)

    def select(self,iid):
        self.tv.selection_set(iid);self.canvas.focus_set();self.selection_changed()

    def edit_row(self,iid):
        self.select(iid);self.view.safe(self.view.edit)

    def move_selection(self,step):
        ids=list(self.rows)
        if ids:
            selected=self.tv.selection();index=ids.index(selected[0]) if selected and selected[0] in ids else -1
            index=max(0,min(len(ids)-1,index+step));self.select(ids[index])
            row=self.rows[ids[index]]['frame'];height=max(1,self.body.winfo_height())
            self.canvas.yview_moveto(row.winfo_y()/height)
        return 'break'

    def refresh(self):
        items=self.view.items();signature=(repr(items),repr(self.app.automation.states) if self.advanced else '',self.app.T.lang)
        if signature!=self.signature:
            self.signature=signature;selected=self.tv.selection();position=self.canvas.yview()[0]
            self._painting=True
            old_order=list(self.rows);new_order=[str(t['id']) for t in items]
            for iid in set(old_order)-set(new_order):
                self.rows.pop(iid)['frame'].destroy();self.tv.delete(iid)
            self.empty.pack_forget()
            for task in items:
                iid=str(task['id']);schedule=self.schedule(task)
                state=('已启用' if task.get('enabled') else '已停用') if self.advanced else ('常用' if task.get('favorite') else '普通')
                values=(task['name'],self.app.describe_action(task),schedule,self.tr(state))
                enabled=bool(task.get('enabled')) if self.advanced else None if task.get('favorite') else False
                if iid in self.rows:
                    row=self.rows[iid];row['task']=task
                    if tuple(self.tv.item(iid,'values'))!=values:self.tv.item(iid,values=values)
                    if row['action']!=task['action']:
                        row['action']=task['action'];icon=row['icon']
                        icon._photo=cozy_icon(icon,'bell' if task['action']=='message' else task['action'],round(22*self.s),ink=theme.accent);icon.config(image=icon._photo)
                    self.paint_badge(row['badge'],state,enabled)
                    continue
                self.tv.insert('','end',iid=iid,values=values)
                row=CozyFrame(self.body,bg=C['card'],height=round(49*self.s),radius=10);row.pack(fill='x',pady=2);row.pack_propagate(False)
                name=self.label(row,task['name'],bold=True);icon=self.label(row,'')
                icon._photo=cozy_icon(row,'bell' if task['action']=='message' else task['action'],round(22*self.s),ink=theme.accent);icon.config(image=icon._photo)
                edit=flat_button(row,self.tr('编辑'),lambda iid=iid:self.edit_row(iid),font=theme.font(delta=-2),padx=2,pady=3)
                edit._selection_outline='#D8CDEF'
                condition=self.label(row,schedule,small=True);badge=self.badge(row,state)
                self.paint_badge(badge,state,enabled)
                self.rows[iid]=dict(frame=row,name=name,icon=icon,edit=edit,condition=condition,badge=badge,task=task,action=task['action'])
                for widget in (row,row._surface,name,icon,condition,badge):
                    widget.bind('<Button-1>',lambda e,iid=iid:self.select(iid))
                    widget.bind('<Double-Button-1>',lambda e,iid=iid:self.edit_row(iid))
                from ui_settings_controls import Tooltip
                Tooltip(name,lambda iid=iid:self.rows[iid]['task']['name']+'\n'+self.app.describe_action(self.rows[iid]['task']))
                Tooltip(condition,lambda iid=iid:self.schedule(self.rows[iid]['task']))
            self.rows={iid:self.rows[iid] for iid in new_order}
            if old_order!=new_order:
                for index,(iid,row) in enumerate(self.rows.items()):
                    row['frame'].pack_forget();row['frame'].pack(fill='x',pady=2);self.tv.move(iid,'',index)
            if not items:self.empty.pack(fill='x',padx=12,pady=32)
            if selected and selected[0] in self.rows:self.tv.selection_set(selected[0])
            elif items:self.tv.selection_set(str(items[0]['id']))
            self._painting=False;self.layout();self.canvas.update_idletasks();self.canvas.yview_moveto(position)
            key='advanced' if self.advanced else 'templates'
            if hasattr(self.view.owner,'tab_buttons'):
                self.view.owner.tab_buttons[key].config(text=self.app.T('center_'+key)+'  '+str(len(items)))
        self.selection_changed()

    def layout(self,width=None):
        width=max(1,width or self.canvas.winfo_width());self.canvas.itemconfigure(self.body_item,width=width)
        # Shared header/row boundaries never grow with the text.
        widths=(round(width*.31),round(width*.17),round(width*.34));widths+= (width-sum(widths),)
        self.column_widths=widths;gap=round(7*self.s);x=0
        name_inset=0 if self.advanced else round(25*self.s)+4
        for i,(heading,w) in enumerate(zip(self.headings,widths)):
            inset=name_inset if i==0 else 0
            heading.config(anchor='center' if i in (1,3) else 'w')
            heading.place(x=x+gap+inset,y=0,width=max(1,w-2*gap-inset),relheight=1)
            self.fit(heading,self.tr(('名称','操作','执行方式','状态')[i]),w-2*gap-inset);x+=w
        for row in self.rows.values():
            task=row['task'];w0,w1,w2,w3=widths;icon_width=0 if self.advanced else round(25*self.s)
            if not self.advanced:row['icon'].place(x=gap,y=round(13*self.s),width=icon_width,height=round(22*self.s))
            row['name'].place(x=gap+name_inset,y=0,width=max(1,w0-2*gap-name_inset),relheight=1)
            self.fit(row['name'],task['name'],max(1,w0-2*gap-name_inset))
            row['edit'].place(x=w0+gap,y=round(10*self.s),width=max(1,w1-2*gap),height=round(28*self.s))
            row['condition'].place(x=w0+w1+gap,y=0,width=max(1,w2-2*gap),relheight=1)
            self.fit(row['condition'],self.schedule(task),w2-2*gap)
            row['badge'].place(x=w0+w1+w2+gap,y=round(11*self.s),width=max(1,w3-2*gap),height=round(27*self.s))

    def selection_changed(self):
        if self._painting:return
        selected=self.view.selected();iid=str(selected['id']) if selected else None
        if iid!=self._selected_key:
            self._selected_key=iid
        for key,row in self.rows.items():
            bg=C['hover'] if key==iid else C['card']
            if row['frame'].cget('bg')!=bg:
                row['frame'].config(bg=bg)
                for name in ('name','icon','condition'):row[name].config(bg=bg)
                row['edit']._last_paint=None;row['edit']._schedule()
                row['badge'].redraw()
        task=self.next_task() if self.advanced else selected
        self._title=(task['name']+' · '+self.app.describe_action(task) if self.advanced else task['name']) if task else self.tr('暂无已启用任务' if self.advanced else '我的模板')
        self._subtitle=(self.next_text(task)+' · '+self.repeat(task) if self.advanced else self.app.describe_action(task)+' · '+self.schedule(task)) if task else self.tr('新建任务后手动启用' if self.advanced else '保存常用设定，一键加入队列')
        self.fit(self.title,self._title,self.title.winfo_width());self.fit(self.subtitle,self._subtitle,self.subtitle.winfo_width())
        if self.advanced:
            self.paint_badge(self.summary_status,'已启用' if task else '已停用',bool(task))
            for label,text in ((self.next_label,self.tr('下次执行')+'：  '+self.next_text(selected)),(self.repeat_label,self.tr('重复')+'：  '+self.repeat(selected))):
                label._full_text=text;self.fit(label,text,label.winfo_width())
            enable_button(self.buttons[1],selected is not None)
        else:
            self.favorite_button.config(text='★' if selected and selected.get('favorite') else '☆')
            enable_button(self.favorite_button,selected is not None);enable_button(self.buttons[0],selected is not None)
            self.selection_label.config(text=self.tr('选中 {n} 项').format(n=int(selected is not None)))

    def repeat(self,task):
        if not task:return '—'
        if task.get('mode')!='calendar':return self.tr('条件任务（单次）')
        return self.tr({'once':'仅一次','daily':'每天','workdays':'每周一至周五','weekends':'每周六、周日'}[task.get('repeat','once')])

    def menu(self,anchor):
        from ui_popup_menu import VioletMenu
        from ui_extras import PreviewWindow
        selected=self.view.selected();has=selected is not None
        items=[('新建任务',self.view.add,True,'enqueue'),('编辑',self.view.edit,has,'parameters'),('复制',self.view.duplicate,has,'copy'),('删除',self.view.remove,has,'clear')]
        if self.advanced:
            items += [('今天跳过一次',self.view.skip_today,has and selected.get('mode')=='calendar' and selected.get('enabled',False),'clock'),('未来7天任务预览',lambda:PreviewWindow(self.app,self.view.owner),True,'calendar')]
        else:items += [('撤销上一次删除',self.view.undo_delete,self.app.undo.available(),'restart')]
        menu=tk.Menu(self.view,tearoff=0)
        for text,fn,enabled,icon in items:menu.add_command(label=self.tr(text),command=lambda fn=fn:self.view.safe(fn),state='normal' if enabled else 'disabled')
        self.popup=VioletMenu(self.app,menu,anchor=anchor,icons=tuple(i[3] for i in items),title=self.tr('更多操作'))
