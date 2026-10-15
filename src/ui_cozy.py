"""Cream surfaces drawn at screen resolution. Native button semantics stay intact."""
import ctypes
import math
import tkinter as tk
import tkinter.font as tkfont
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageColor

@lru_cache(maxsize=32)
def pil_font(size,bold=False):
    path='C:/Windows/Fonts/msyhbd.ttc' if bold else 'C:/Windows/Fonts/msyh.ttc'
    try:return ImageFont.truetype(path,max(9,int(size)))
    except OSError:return ImageFont.truetype('arial.ttf',max(9,int(size)))

def scale(widget):
    return max(1,min(3,float(widget.tk.call('tk','scaling'))/(96/72)))

@lru_cache(maxsize=48)
def _round_mask(w,h,radius):
    radius=max(1,min(int(radius),w//2,h//2));mask=Image.new('L',(w,h),255)
    # Antialias only the corners; resizing entire large cards blocked theme changes.
    circle=Image.new('L',(radius*6,radius*6));ImageDraw.Draw(circle).ellipse((0,0,radius*6-1,radius*6-1),fill=255)
    circle=circle.resize((radius*2,radius*2),Image.Resampling.LANCZOS)
    for source,dest in [((0,0,radius,radius),(0,0)),((radius,0,radius*2,radius),(w-radius,0)),((0,radius,radius,radius*2),(0,h-radius)),((radius,radius,radius*2,radius*2),(w-radius,h-radius))]:mask.paste(circle.crop(source),dest)
    return mask

def plate(width,height,fill,border,shadow,radius=18,raised=True,base=None):
    w=max(2,int(width));h=max(2,int(height));mask=_round_mask(w,h,int(radius))
    image=Image.composite(Image.new('RGB',(w,h),border or fill),Image.new('RGB',(w,h),base or fill),mask)
    if border and border!=fill and w>4 and h>4:
        inner=Image.new('RGB',(w-2,h-2),fill);image.paste(inner,(1,1),_round_mask(w-2,h-2,max(1,int(radius)-1)))
    else:image=Image.composite(Image.new('RGB',(w,h),fill),Image.new('RGB',(w,h),base or fill),mask)
    return image

class CozyButton(tk.Button):
    """A real Tk Button: native invoke, focus, shortcuts and disabled behavior.

    Its image is a rounded gradient plate with text/icons, never a transparent
    hit-test overlay. cget/configure keep the existing button API for localization.
    """
    virtual={'text','image','compound','anchor','padx','pady','width','height'}
    def __init__(self,parent,**kw):
        self._v={'text':'','image':'','compound':'none','anchor':'center','padx':12,'pady':6,'width':0,'height':0}
        self._v.update({k:kw.pop(k) for k in list(kw) if k in self.virtual})
        self._state=kw.pop('state','normal');self._command=kw.pop('command',None)
        self._keyboard_focus=False;self._ready=False;self._hovering=False;self._pressed=False;self._draw_job=None
        for key in ('bd','borderwidth','relief','highlightthickness'):kw.pop(key,None)
        super().__init__(parent,**kw,command=self._call,bd=0,relief='flat',text='',padx=0,pady=0,highlightthickness=0,default='disabled',overrelief='flat')
        # Native Button mouse bindings shift the image and expose square corners.
        # Keep the real Button API, but own pointer/key feedback and its rounded paint.
        self.bindtags(tuple(tag for tag in self.bindtags() if tag!='Button'))
        top=self.winfo_toplevel();root=self._root()
        if not getattr(top,'_cozy_focus_tracking',False):
            top._cozy_focus_tracking=True
            def keyboard(event):root._cozy_keyboard_navigation=True
            def pointer(event):root._cozy_keyboard_navigation=False
            top.bind('<KeyPress-Tab>',keyboard,add='+');top.bind('<Shift-KeyPress-Tab>',keyboard,add='+');top.bind('<ButtonPress-1>',pointer,add='+')
        self._ready=True;self.bind('<Configure>',self._schedule,add='+')
        self.bind('<Enter>',lambda e:self._interaction(hover=True),add='+');self.bind('<Leave>',lambda e:self._interaction(hover=False,pressed=False),add='+')
        self.bind('<ButtonPress-1>',self._pointer_press);self.bind('<ButtonRelease-1>',self._pointer_release)
        self.bind('<KeyPress-space>',self._space_press);self.bind('<KeyRelease-space>',self._space_release)
        self.bind('<FocusIn>',self._focus_event,add='+');self.bind('<FocusOut>',self._focus_event,add='+')
        self.bind('<Return>',self._enter_key)
        self.bind('<Destroy>',self._dispose,add='+');self._measure();self._paint()
    def _focus_event(self,event):
        self._keyboard_focus=event.type==tk.EventType.FocusIn and bool(getattr(self._root(),'_cozy_keyboard_navigation',False))
        self._schedule()
    def _pointer_press(self,event):
        if self._state!='disabled':self._root()._cozy_keyboard_navigation=False;self._keyboard_focus=False;self.focus_set();self._interaction(pressed=True)
        return 'break'
    def _pointer_release(self,event):
        pressed=self._pressed;self._interaction(pressed=False)
        if pressed and 0<=event.x<self.winfo_width() and 0<=event.y<self.winfo_height():self.invoke()
        return 'break'
    def _space_press(self,event):
        if self._state!='disabled':self._interaction(pressed=True)
        return 'break'
    def _space_release(self,event):
        pressed=self._pressed;self._interaction(pressed=False)
        if pressed:self.invoke()
        return 'break'
    def _enter_key(self,event):
        self.invoke();return 'break'
    def _call(self):
        if self._state!='disabled' and self._command:return self._command()
    def invoke(self):
        return super().invoke() if self._state!='disabled' else ''
    def _dispose(self,e):
        if e.widget is self and self._draw_job:
            self.after_cancel(self._draw_job);self._draw_job=None
    def _interaction(self,hover=None,pressed=None):
        if hover is not None:self._hovering=hover
        if pressed is not None:self._pressed=pressed
        self._schedule()
    def _schedule(self,e=None):
        if not self._ready:return
        if self._draw_job is None:self._draw_job=self.after_idle(self._paint)
    def configure(self,cnf=None,**kw):
        if isinstance(cnf,str):
            if cnf=='state':return ('state','state','State','normal',self._state)
            if cnf in self._v:return (cnf,cnf,cnf,'',self._v[cnf])
            return super().configure(cnf)
        if isinstance(cnf,dict):kw={**cnf,**kw}
        if not kw:
            result=super().configure()
            for k,v in self._v.items():result[k]=(k,k,k,'',v)
            result['state']=('state','state','State','normal',self._state)
            return result
        measure=bool(set(kw)&(self.virtual|{'font'}))
        if 'state' in kw:
            self._state=str(kw.pop('state'));kw['takefocus']=0 if self._state=='disabled' else 1
        if 'command' in kw:self._command=kw.pop('command')
        for k in list(kw):
            if k in self.virtual:self._v[k]=kw.pop(k)
        # The image plate owns its border; keep native border at zero.
        for key in ('highlightthickness','bd','borderwidth','relief','overrelief','default'):kw.pop(key,None)
        result=super().configure(**kw) if kw else None
        if self._ready:
            if measure:self._measure()
            self._schedule()
        return result
    config=configure
    def cget(self,key):return self._state if key=='state' else self._v[key] if key in self._v else super().cget(key)
    __getitem__=cget
    def _content(self):
        specification=str(super().cget('font'))
        if getattr(self,'_font_specification',None)!=specification:
            self._font_specification=specification;self._content_font=tkfont.Font(root=self,font=specification)
        font=self._content_font;text=str(self._v['text']);image=self._v['image']
        try:iw=int(self.tk.call('image','width',str(image))) if image else 0;ih=int(self.tk.call('image','height',str(image))) if image else 0
        except tk.TclError:iw=ih=0
        tw=max((font.measure(line) for line in text.split('\n')),default=0);th=font.metrics('linespace')*max(1,len(text.split('\n'))) if text else 0
        compound=self._v['compound']
        if iw and compound=='none':text='';tw=th=0
        gap=5 if text and iw else 0
        if compound in ('top','bottom'):cw=max(tw,iw);ch=th+ih+gap
        elif compound in ('left','right'):cw=tw+iw+gap;ch=max(th,ih)
        else:cw=max(tw,iw);ch=max(th,ih)
        return font,text,image,iw,ih,tw,th,cw,ch,gap
    def _measure(self):
        # Main controls already reserve room for every supported language.
        # Keep their requests stable instead of redistributing column pixels.
        renderer=getattr(self.winfo_toplevel(),'_skin_renderer',None)
        if getattr(renderer,'_localizing',False) and hasattr(self,'_natural'):return
        font,_,_,_,_,_,_,cw,ch,_=self._content();s=scale(self)
        width=max(cw+2*int(float(self._v['padx']))+12,int(float(self._v['width'] or 0))*font.measure('0'))
        height=max(ch+2*int(float(self._v['pady']))+6,int(float(self._v['height'] or 0))*font.metrics('linespace'))
        self._natural=(max(20,int(width)),max(22,int(height)))
        super().configure(width=self._natural[0],height=self._natural[1])
    def _paint(self):
        self._draw_job=None
        if not self.winfo_exists():return
        focused=self.focus_get() is self and self._keyboard_focus
        from theme import theme,blend
        stamp=(self.winfo_width(),self.winfo_height(),tuple((k,str(v)) for k,v in self._v.items()),self._state,self._hovering,self._pressed,focused,str(super().cget('font')),str(super().cget('background')),str(super().cget('foreground')),str(super().cget('activebackground')),str(super().cget('disabledforeground')),theme.accent,theme.c('shadow'))
        from ui_skin import renderer_for
        renderer=renderer_for(self)
        if renderer:stamp+=(renderer.generation,renderer.box(self))
        if getattr(self,'_last_paint',None)==stamp:return
        self._last_paint=stamp
        w=self.winfo_width() if self.winfo_width()>1 else self._natural[0];h=self.winfo_height() if self.winfo_height()>1 else self._natural[1];disabled=self._state=='disabled'
        bg=str(super().cget('background'));fg=str(super().cget('disabledforeground' if disabled else 'foreground'))
        def rgb(value):
            r,g,b=self.winfo_rgb(value);return '#%02x%02x%02x'%(r//257,g//257,b//257)
        bg=rgb(bg);fg=rgb(fg)
        active=self._hovering and not disabled
        if active:bg=rgb(str(super().cget('activebackground')))
        if self._pressed and not disabled:bg=blend(bg,getattr(self,'_fixed_ink',theme.c('fg')),.08)
        border=theme.accent if focused else (theme.c('card_border') if not active else blend(theme.c('card_border'),theme.accent,.4))
        parent_bg=self.master.cget('background') if 'background' in self.master.keys() else theme.c('bg')
        kind=getattr(self,'_kind','normal')
        border=getattr(self,'_fixed_accent',theme.accent) if focused else getattr(self,'_selection_outline',bg)
        if kind in ('ghost','nav','plain') and not getattr(self,'_nav_active',False) and not active and not self._pressed and not focused:bg=parent_bg;border=bg
        from ui_skin import background,tint
        skin=background(self)
        im=skin if skin is not None else plate(w,h,bg,border,theme.c('shadow'),max(9,int(12*scale(self))),raised=False,base=parent_bg)
        if getattr(self,'_bare_glyph',False):im=skin if skin is not None else Image.new('RGB',(w,h),parent_bg)
        if skin is not None and not getattr(self,'_row_action',False) and not getattr(self,'_bare_glyph',False):
            im=skin
            radius=max(9,int(12*scale(self)))
            if getattr(self,'_kind','normal')=='accent':im=tint(im,bg,1,radius,theme.accent if focused else None)
            elif self._hovering or self._pressed or focused:im=tint(im,bg,.24,radius,theme.accent if focused else None)
            elif bg not in (theme.c('bg'),theme.c('card')):im=tint(im,bg,.20,radius)
        # A restrained vertical highlight, clipped inside the rounded fill.
        base=im
        ink_stamp=(w,h,tuple((k,str(v)) for k,v in self._v.items()),fg,str(super().cget('font')),disabled,self._pressed)
        if getattr(self,'_ink_stamp',None)!=ink_stamp:
            self._ink_stamp=ink_stamp;im=Image.new('RGBA',(w,h))
            d=ImageDraw.Draw(im);font,text,image,iw,ih,tw,th,cw,ch,gap=self._content()
            anchor=str(self._v['anchor']);x=int(float(self._v['padx']))+6 if anchor in ('w','nw','sw') else (w-cw)//2;y=(h-ch)//2+(1 if self._pressed else 0)
            tx,ty=x,y;ix,iy=x,y;compound=self._v['compound']
            if compound=='left':tx=x+iw+gap;iy=y+(ch-ih)//2;ty=y+(ch-th)//2
            elif compound=='right':ix=x+tw+gap;iy=y+(ch-ih)//2;ty=y+(ch-th)//2
            elif compound=='top':tx=x+(cw-tw)//2;ix=x+(cw-iw)//2;ty=y+ih+gap
            elif compound=='bottom':tx=x+(cw-tw)//2;ix=x+(cw-iw)//2;iy=y+th+gap
            else:tx=x+(cw-tw)//2;ix=x+(cw-iw)//2
            if iw:
                try:
                    source=ImageTk.getimage(image).convert('RGBA')
                    if disabled:
                        tint=Image.new('RGBA',source.size,fg);tint.putalpha(source.getchannel('A'));source=tint
                    im.paste(source,(int(ix),int(iy)),source)
                except (ValueError,tk.TclError,AttributeError):pass
            if text:
                pixels=abs(font.actual('size')) if font.actual('size')<0 else font.actual('size')*float(self.tk.call('tk','scaling'))
                pf=pil_font(round(pixels),font.actual('weight')=='bold')
                if getattr(self,'_fit_text',False):
                    available=max(1,w-iw-gap-2*int(float(self._v['padx']))-12)
                    while max((d.textlength(line,font=pf) for line in text.split('\n')),default=0)>available and pf.size>round(9*scale(self)):pf=pil_font(pf.size-1,font.actual('weight')=='bold')
                    tw=max((d.textlength(line,font=pf) for line in text.split('\n')),default=0)
                lineheight=font.metrics('linespace')
                for index,line in enumerate(text.split('\n')):
                    # Center the visible ink within its line box, including punctuation.
                    box=d.textbbox((0,0),line,font=pf)
                    ink_h=box[3]-box[1];ink_w=box[2]-box[0]
                    d.text((tx+(tw-ink_w)/2-box[0],ty+index*lineheight+(lineheight-ink_h)/2-box[1]),line,font=pf,fill=fg)
            self._ink=im
        base.paste(self._ink,(0,0),self._ink);im=base
        if getattr(self,'_plate',None) is not None and (self._plate.width(),self._plate.height())==im.size:self._plate.paste(im)
        else:self._plate=ImageTk.PhotoImage(im,master=self);super().configure(image=self._plate,compound='none',text='')

class CozyFrame(tk.Frame):
    """Rounded real child HWND, with a light surface and inset ambient shadow."""
    def __init__(self,parent,**kw):
        self._plate_job=None;self._radius=kw.pop('radius',18)
        kw.pop('highlightthickness',None)
        super().__init__(parent,**kw,highlightthickness=0)
        self._surface=tk.Label(self,bd=0,bg=self.cget('background'));self._surface._theme_fixed=True;self._surface.place(x=0,y=0,relwidth=1,relheight=1);self._surface.lower();self._surface_key=None
        self.bind('<Configure>',self._round,add='+')
    def configure(self,cnf=None,**kw):
        result=super().configure(cnf,**kw)
        if hasattr(self,'_surface') and kw:self._round()
        return result
    config=configure
    def _round(self,e=None):
        if self.winfo_width()<12 or self.winfo_height()<12:return
        from ui_skin import renderer_for
        renderer=renderer_for(self)
        if renderer or getattr(getattr(self.winfo_toplevel(),'_skin_renderer',None),'_updating',False):
            if renderer:renderer.schedule()
            return
        from theme import theme
        key=(self.winfo_width(),self.winfo_height(),self.cget('background'),theme.c('card_border'),theme.c('shadow'))
        if self._surface_key==key:return
        self._surface_key=key;self._surface_photo=ImageTk.PhotoImage(plate(key[0],key[1],key[2],key[2],key[4],round(self._radius*scale(self)),raised=False,base=self.master.cget('background') if 'background' in self.master.keys() else key[2]),master=self)
        self._surface.configure(image=self._surface_photo,bg=key[2])
        # Rounded edges live in the painted surface. Child HWND regions make
        # Windows' move-copy path leave black strips across layered windows.

class CozyGroup(CozyFrame):
    def __init__(self,parent,text='',**kw):
        from theme import theme
        self._text=text
        super().__init__(parent,bg=theme.c('card'),bd=0,highlightthickness=0)
        self.heading=tk.Label(self,text=text.strip(),bg=theme.c('card'),fg=theme.c('fg'),font=theme.font(bold=True),anchor='w')
        self.heading.pack(fill='x',padx=14,pady=(12,3))
    def cget(self,key):return self.heading.cget('text') if key=='text' else super().cget(key)
    __getitem__=cget
    def configure(self,cnf=None,**kw):
        if isinstance(cnf,dict):kw={**cnf,**kw};cnf=None
        if 'text' in kw:self.heading.configure(text=kw.pop('text'))
        return super().configure(cnf,**kw)
    config=configure

def nature_image(widget,width=116,height=46):
    """Small vector-authored sleeping cat and plant; no external copyrighted art."""
    from theme import theme
    s=3;im=Image.new('RGBA',(116*s,46*s));d=ImageDraw.Draw(im)
    def oval(box,fill):d.ellipse(tuple(int(v*s) for v in box),fill=fill)
    def poly(points,fill):d.polygon([(int(x*s),int(y*s)) for x,y in points],fill=fill)
    def line(points,fill,width=1):d.line([(int(x*s),int(y*s)) for x,y in points],fill=fill,width=width*s)
    oval((18,33,108,44),'#E9E7C8');poly([(85,27),(101,27),(98,40),(88,40)],'#E9BD8F')
    line([(92,28),(92,7)],'#9CAA7D',2);oval((92,1,103,15),'#A8BE91');oval((80,11,93,23),'#B8CA9C')
    oval((38,18,78,41),'#DCA774');oval((49,23,78,40),'#F7E9D8');oval((24,18,48,40),'#F5DCBC')
    poly([(24,24),(27,12),(36,22)],'#DCA774');poly([(38,22),(44,12),(48,28)],'#DCA774')
    d.arc((28*s,26*s,35*s,32*s),0,170,fill='#735845',width=2*s);d.arc((37*s,26*s,44*s,32*s),0,170,fill='#735845',width=2*s)
    line([(35,33),(37,34),(39,33)],'#735845');oval((9,20,19,27),'#B5C89A')
    return ImageTk.PhotoImage(im.resize((width,height),Image.Resampling.LANCZOS),master=widget)


def cozy_icon(widget,name,size,ink=None):
    """One rounded line vocabulary for action, time and utility icons."""
    from theme import theme
    color={'shutdown':'#D87561','restart':'#6EAB85','logoff':'#C7974C','lock':'#C7974C','sleep':'#8C8FCC','hibernate':'#8077A9','play_sound':'#A088BB'}.get(name,theme.accent)
    if name in ('pause','stop','clear','gear','pin','close','minimize'):color=theme.c('fg_dim')
    if name=='play':color=theme.c('accent_fg')
    if ink:color=ink
    unit=4;im=Image.new('RGBA',(96,96));d=ImageDraw.Draw(im);weight=7
    def line(points,c=color,width=weight):
        pts=[(int(x*unit),int(y*unit)) for x,y in points];d.line(pts,fill=c,width=width,joint='curve')
        for x,y in (pts[0],pts[-1]):d.ellipse((x-width/2,y-width/2,x+width/2,y+width/2),fill=c)
    def ellipse(box,c=color,width=weight):d.ellipse(tuple(int(x*unit) for x in box),outline=c,width=width)
    def rect(box,c=color):d.rounded_rectangle(tuple(int(x*unit) for x in box),radius=8,outline=c,width=weight)
    if name.startswith('step'):
        d.ellipse((2,2,94,94),fill=theme.accent);d.text((48,48),name[-1],font=pil_font(58,True),fill=theme.c('accent_fg'),anchor='mm')
    elif name=='blank':pass
    elif name=='check':
        d.ellipse((4,4,92,92),fill=color);line([(6,12),(10,16),(18,8)],theme.c('accent_fg'),8)
    elif name=='shutdown':
        d.arc((12,12,84,84),-65,245,fill=color,width=weight);line([(12,2),(12,11)])
    elif name=='restart':
        d.arc((13,13,83,83),45,345,fill=color,width=weight);line([(21,3),(21,8),(16,8)])
    elif name=='sleep':
        line([(3,9),(3,21)]);line([(3,17),(21,17),(21,21)]);rect((5,10,10,16));line([(11,12),(19,12),(21,15),(21,17)])
        d.text((67,18),'z',font=pil_font(26,True),fill=color,anchor='mm')
    elif name=='hibernate':
        rect((3,3,21,21));line([(6,7),(18,7)],color,5)
        d.arc((29,37,67,75),-60,240,fill=color,width=6);line([(12,9),(12,14)],color,6)
    elif name=='moon':
        d.arc((7,19,67,83),65,290,fill=color,width=weight);d.arc((30,6,73,65),75,225,fill=color,width=weight)
        line([(19,2),(19,8)],color,4);line([(16,5),(22,5)],color,4);d.ellipse((77,42,85,50),fill=color)
    elif name=='gear':
        points=[]
        for step in range(32):
            angle=math.radians(step*360/32);r=10 if step%4 in (1,2) else 8
            points.append((12+r*math.cos(angle),12+r*math.sin(angle)))
        line(points+[points[0]],color,5);ellipse((9,9,15,15),color,5)
    elif name=='pin':
        line([(7,3),(17,3)]);line([(9,3),(9,9),(5,14),(19,14),(15,9),(15,3)]);line([(12,14),(12,22)])
    elif name=='close':line([(6,6),(18,18)]);line([(18,6),(6,18)])
    elif name=='minimize':line([(5,12),(19,12)])
    elif name=='power_badge':
        d.ellipse((2,2,94,94),fill=theme.accent);d.arc((24,24,72,72),-60,240,fill=theme.c('accent_fg'),width=7);line([(12,4),(12,12)],theme.c('accent_fg'),7)
    elif name=='logoff':
        ellipse((8,2,16,10));line([(4,21),(4,18),(7,14),(17,14),(20,18),(20,21),(4,21)])
    elif name=='lock':
        d.arc((26,3,70,54),180,360,fill=color,width=weight);rect((4,10,20,22));line([(12,14),(12,18)])
    elif name in ('run_program','close_program'):
        rect((2,4,22,20));line([(3,8),(21,8)],color,5)
        if name=='run_program':line([(10,11),(16,14),(10,17),(10,11)],color,6)
        else:line([(9,11),(16,17)]);line([(16,11),(9,17)])
    elif name=='play_sound':
        line([(3,9),(7,9),(12,4),(12,20),(7,15),(3,15),(3,9)]);d.arc((38,18,85,78),-65,65,fill=color,width=weight)
    elif name=='message':rect((2,3,22,18));line([(6,18),(6,22),(11,18)]);line([(6,8),(18,8)],color,5);line([(6,13),(15,13)],color,5)
    elif name=='clock':ellipse((3,3,21,21));line([(12,6),(12,12),(16,14)])
    elif name=='sun':
        ellipse((8,8,16,16))
        for a in range(0,360,45):
            r=math.radians(a);line([(12+8*math.cos(r),12+8*math.sin(r)),(12+10*math.cos(r),12+10*math.sin(r))],color,5)
    elif name=='calendar':
        rect((3,5,21,22));line([(3,10),(21,10)],color,5);line([(7,2),(7,7)]);line([(17,2),(17,7)]);line([(8,15),(9,15)],color,5);line([(14,17),(16,14)],color,5)
    elif name=='sunrise':
        d.arc((27,32,69,76),180,360,fill=color,width=weight);line([(2,19),(22,19)],color,5)
        for a in (210,250,290,330):
            r=math.radians(a);line([(12+8*math.cos(r),15+8*math.sin(r)),(12+10*math.cos(r),15+10*math.sin(r))],color,5)
    elif name=='bell':
        line([(5,16),(6,8),(9,4),(15,4),(18,8),(19,16),(5,16)],color,5);line([(9,20),(15,20)],color,5)
    elif name=='monitor':rect((2,3,22,17));line([(12,17),(12,22),(7,22),(17,22)],color,5)
    elif name=='document':rect((5,2,19,22));line([(8,7),(16,7)],color,5);line([(8,12),(16,12)],color,5);line([(8,17),(13,17)],color,5)
    elif name=='keyboard':
        rect((2,5,22,19))
        for y in (9,13):
            for x in (6,10,14,18):line([(x,y),(x+.2,y)],color,5)
        line([(7,16),(17,16)],color,5)
    elif name=='database':
        ellipse((3,2,21,8),color,5);line([(3,5),(3,19)],color,5);line([(21,5),(21,19)],color,5)
        d.arc((12,60,84,88),0,180,fill=color,width=5);d.arc((12,28,84,56),0,180,fill=color,width=5)
    elif name=='parameters':
        rect((2,3,22,21));line([(6,8),(9,11),(6,14)],color,5);line([(12,16),(18,16)],color,5)
    elif name=='sliders':
        for y,x in ((5,16),(12,7),(19,15)):line([(3,y),(21,y)],color,5);d.ellipse(((x-2)*4,(y-2)*4,(x+2)*4,(y+2)*4),fill=theme.c('card'),outline=color,width=5)
    elif name=='enqueue':line([(3,6),(14,6)]);line([(3,12),(14,12)]);line([(3,18),(11,18)]);line([(18,13),(18,21)]);line([(14,17),(22,17)])
    elif name=='bolt':line([(14,2),(5,14),(12,14),(10,22),(20,10),(13,10),(14,2)])
    elif name=='play':d.polygon([(28,12),(80,48),(28,84)],fill=color)
    elif name=='pause':line([(8,5),(8,19)]);line([(16,5),(16,19)])
    elif name=='stop':rect((5,5,19,19))
    elif name=='clear':line([(5,6),(19,6)]);rect((7,8,17,21));line([(10,3),(14,3)])
    else:ellipse((3,3,21,21))
    return ImageTk.PhotoImage(im.resize((int(size),int(size)),Image.Resampling.LANCZOS),master=widget)
