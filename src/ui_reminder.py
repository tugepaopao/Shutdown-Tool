"""Live violet reminder drawn over the approved purple portrait artwork."""
import math,time,sys,tkinter as tk
from pathlib import Path
from PIL import Image,ImageDraw,ImageColor
from ui_cozy import pil_font,scale,_round_mask
from ui_floating import workareas
from ui_float_surface import present

class FadeMessageBox(tk.Toplevel):
    def __init__(self,master,title,text,seconds=15,on_close=None,button_text=None,on_button=None,extra_buttons=None):
        super().__init__(master);self.withdraw();self.overrideredirect(True);self.attributes('-toolwindow',True);self.attributes('-topmost',True)
        self._theme_fixed=True;self.configure(bg='#332079');self.on_close=on_close;self.on_button=on_button;self._closed=False;self._closing=False;self._button_clicked=False;self._jobs=set();self._pressed=None;self._hover=None;self._focus=None;self._scroll=0;self._alpha=0
        self.title_text=str(title);self.message=str(text);self.dpi_scale=scale(self);self.s=self.dpi_scale*.85
        self.items=list(extra_buttons or [])
        if button_text:self.items.append((button_text,on_button))
        self._btn=tk.Button(self,command=self._fire_button) if button_text else None
        self._tick_label=tk.Label(self);self._tick_label._theme_fixed=True
        self.canvas=tk.Canvas(self,bg='#332079',bd=0,highlightthickness=0,takefocus=1);self.canvas._theme_fixed=True;self.canvas.pack(fill='both',expand=True)
        cx=master.winfo_rootx()+master.winfo_width()//2;cy=master.winfo_rooty()+master.winfo_height()//2
        area=min(workareas(master),key=lambda a:max(a[0]-cx,0,cx-a[2])**2+max(a[1]-cy,0,cy-a[3])**2)
        left,top,right,bottom=area;self.panel_width=min(round(560*self.s),right-left-round(32*self.dpi_scale));self.panel_height=round(self.panel_width/2.14)
        self.position=(right-self.panel_width-round(20*self.dpi_scale),bottom-self.panel_height-round(20*self.dpi_scale));self.geometry(f'{self.panel_width}x{self.panel_height}+{self.position[0]}+{self.position[1]}')
        asset=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent.parent))/'assets/ui/violet_reminder.png'
        with Image.open(asset) as artwork:self.art=artwork.convert('RGBA').resize((self.panel_width,self.panel_height),Image.Resampling.LANCZOS)
        try:self._countdown=max(1,int(seconds))
        except (ValueError,TypeError):self._countdown=15
        self._deadline=time.monotonic()+self._countdown;self._shown_seconds=self._countdown
        self._layout();self._render();self.update_idletasks()
        self.bind('<Map>',lambda e:self._present() if e.widget is self else None,add='+')
        self.bind('<ButtonPress-1>',self._press);self.bind('<ButtonRelease-1>',self._release);self.bind('<Motion>',self._motion);self.bind('<Leave>',self._leave)
        self.bind('<MouseWheel>',self._wheel);self.bind('<Escape>',lambda e:self.close())
        self.canvas.bind('<Tab>',self._tab);self.canvas.bind('<Shift-Tab>',lambda e:self._tab(e,-1));self.canvas.bind('<Return>',self._key_activate);self.canvas.bind('<space>',self._key_activate)
        self.bind('<Destroy>',self._destroyed,add='+');self.deiconify();self._present();self._fade_in();self._auto_close()
    def _later(self,ms,fn):
        def run():
            self._jobs.discard(job)
            if not self._closed:fn()
        job=self.after(ms,run);self._jobs.add(job)
    def _layout(self):
        w,h=self.panel_width,self.panel_height;self.button_boxes=[];count=len(self.items)
        columns=2 if count>1 else 1;rows=math.ceil(count/columns) if count else 0
        start=.565 if rows>1 else .735
        for i in range(count):
            col=i%columns;row=i//columns;x1=.070+col*.255;x2=x1+(.232 if columns>1 else .488)
            self.button_boxes.append((x1*w,(start+row*.185)*h,x2*w,(start+.148+row*.185)*h))
        self.message_box=(.072*w,.300*h,.553*w,(.505 if rows>1 else .670 if rows else .875)*h)
        self.message_font=pil_font(round(13*self.s));d=ImageDraw.Draw(self.art);self._lines=[]
        for paragraph in self.message.split('\n'):
            line=''
            for char in paragraph:
                if line and d.textlength(line+char,font=self.message_font)>self.message_box[2]-self.message_box[0]:self._lines.append(line);line=char
                else:line+=char
            self._lines.append(line)
        self._line_height=round(19*self.s);self._visible_lines=max(1,int((self.message_box[3]-self.message_box[1])/self._line_height))
    def _render(self):
        if self._closed:return
        w,h=self.panel_width,self.panel_height;im=self.art.copy();d=ImageDraw.Draw(im)
        titlefont=pil_font(round(18*self.s),True)
        while d.textlength(self.title_text,font=titlefont)>w*.55 and titlefont.size>11:titlefont=pil_font(titlefont.size-1,True)
        d.text((w*.118,h*.133),self.title_text,font=titlefont,fill='white',anchor='lm')
        d.text((w*.867,h*.133),f'{self._shown_seconds}s',font=pil_font(round(16*self.s),True),fill='white',anchor='mm')
        d.line([(w*.900,h*.080),(w*.900,h*.183)],fill=(255,255,255,160),width=1)
        cx,cy=w*.941,h*.133;r=round(7*self.s)
        if self._focus==len(self.items):d.rounded_rectangle((cx-r*1.7,cy-r*1.7,cx+r*1.7,cy+r*1.7),radius=r,outline='white',width=1)
        d.line([(cx-r,cy-r),(cx+r,cy+r)],fill='white',width=max(2,round(2*self.s)));d.line([(cx-r,cy+r),(cx+r,cy-r)],fill='white',width=max(2,round(2*self.s)))
        x1,y1,x2,y2=self.message_box;region=Image.new('RGBA',(round(x2-x1),round(y2-y1)));rd=ImageDraw.Draw(region)
        for i,line in enumerate(self._lines[self._scroll:self._scroll+self._visible_lines]):rd.text((0,i*self._line_height),line,font=self.message_font,fill='#33255F')
        im.alpha_composite(region,(round(x1),round(y1)))
        if len(self._lines)>self._visible_lines:
            d=ImageDraw.Draw(im);x=x2+5;d.line((x,y1,x,y2),fill='#DED5EE',width=2);length=(y2-y1)*self._visible_lines/len(self._lines);y=y1+(y2-y1-length)*self._scroll/max(1,len(self._lines)-self._visible_lines);d.line((x,y,x,y+length),fill='#8E65C9',width=3)
        for i,(box,(label,_)) in enumerate(zip(self.button_boxes,self.items)):
            x1,y1,x2,y2=map(round,box);bw,bh=x2-x1,y2-y1;primary=i==len(self.items)-1 and self.on_button is not None
            active=i==self._hover or i==self._focus;layer=Image.new('RGBA',(bw,bh));ld=ImageDraw.Draw(layer)
            for y in range(bh):
                t=y/max(1,bh-1);c=tuple(round(a+(b-a)*t) for a,b in zip((139,69,244),(80,42,185)))+(245,) if primary else (255,255,255,185 if active else 140)
                ld.line((0,y,bw,y),fill=c)
            layer.putalpha(Image.composite(layer.getchannel('A'),Image.new('L',(bw,bh)),_round_mask(bw,bh,round(9*self.s))));im.alpha_composite(layer,(x1,y1));d=ImageDraw.Draw(im)
            d.rounded_rectangle((x1,y1,x2-1,y2-1),radius=round(9*self.s),outline='white' if active else '#EEE6FF',width=max(1,round(self.s)))
            font=pil_font(round(13*self.s),True)
            while d.textlength(str(label),font=font)>bw-12 and font.size>9:font=pil_font(font.size-1,True)
            d.text(((x1+x2)/2,(y1+y2)/2),str(label),font=font,fill='white' if primary else '#3C2B71',anchor='mm')
        self._image=im;self._tick_label.configure(text=f'{self._shown_seconds}s');self._present()
    def _present(self):
        if self.winfo_exists() and self.state()!='withdrawn' and hasattr(self,'_image'):present(self,self._image,round(255*self._alpha))
    def _hit(self,event):
        x,y=event.x_root-self.position[0],event.y_root-self.position[1];w,h=self.panel_width,self.panel_height
        if .912*w<=x<=.976*w and .060*h<=y<=.207*h:return 'close'
        for i,(x1,y1,x2,y2) in enumerate(self.button_boxes):
            if x1<=x<=x2 and y1<=y<=y2:return i
        return None
    def _press(self,event):self._pressed=self._hit(event)
    def _release(self,event):
        pressed=self._pressed;self._pressed=None
        if pressed is not None and pressed==self._hit(event):self.close() if pressed=='close' else self._activate(pressed)
    def _motion(self,event):
        hit=self._hit(event)
        if hit!=self._hover:self._hover=hit;self.canvas.configure(cursor='hand2' if hit is not None else '');self._render()
    def _leave(self,event):
        if self._hover is not None:self._hover=None;self._render()
    def _wheel(self,event):
        limit=max(0,len(self._lines)-self._visible_lines);self._scroll=max(0,min(limit,self._scroll+(-1 if event.delta>0 else 1)));self._render()
    def _tab(self,event,direction=1):
        self._focus=((self._focus if isinstance(self._focus,int) else -1)+direction)%(len(self.items)+1);self._render();return 'break'
    def _key_activate(self,event):
        if self._focus==len(self.items):self.close()
        elif isinstance(self._focus,int):self._activate(self._focus)
        return 'break'
    def _activate(self,index):
        if self._closed or self._closing or self._button_clicked:return
        self._button_clicked=True;callback=self.items[index][1];self.close()
        if callback:callback()
    def _fire_button(self):
        if self.items:self._activate(len(self.items)-1)
    def _fade_in(self,step=0,steps=10):
        if self._closing or self._closed:return
        self._alpha=min(1,(step+1)/steps);self._present()
        if step+1<steps:self._later(20,lambda:self._fade_in(step+1,steps))
    def _fade_out(self,step=0,steps=10):
        if self._closed:return
        self._alpha=max(0,self._fade_start*(1-(step+1)/steps));self._present()
        if step+1<steps:self._later(20,lambda:self._fade_out(step+1,steps))
        else:self._finish()
    def _auto_close(self):
        if self._closed or self._closing:return
        remain=max(0,math.ceil(self._deadline-time.monotonic()));self._countdown=remain
        if remain!=self._shown_seconds:self._shown_seconds=remain;self._render()
        if remain:self._later(100,self._auto_close)
        else:self.close()
    def close(self):
        if self._closed or self._closing:return
        self._closing=True;self._fade_start=self._alpha
        for job in list(self._jobs):self.after_cancel(job)
        self._jobs.clear();self._fade_out()
    def _destroyed(self,event):
        if event.widget is not self:return
        for job in list(self._jobs):
            try:self.after_cancel(job)
            except tk.TclError:pass
        self._jobs.clear();self._closed=True
    def _finish(self):
        if self._closed:return
        callback=self.on_close;self.destroy()
        if callback:callback()
