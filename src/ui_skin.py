"""Opaque, cached skin compositing for the existing native Tk controls.

No layered HWND, transparent-color key or click intercepting overlay is used.
Every original Button/Radiobutton/Entry and callback remains the actual control.
"""
import tkinter as tk
from ui_focus import current_grab, current_focus
import tkinter.font as tkfont
from PIL import Image,ImageDraw,ImageTk,ImageOps
from ui_cozy import CozyButton,CozyFrame,pil_font,scale
from theme import theme
import skins

def renderer_for(widget):
 try:
  renderer=getattr(widget.winfo_toplevel(),'_skin_renderer',None)
  return renderer if renderer and renderer.active else None
 except tk.TclError:return None

def background(widget):
 renderer=renderer_for(widget)
 return renderer.crop(widget) if renderer and renderer.scene is not None else None

def tint(im,color,opacity,radius=0,outline=None):
 layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer)
 from PIL import ImageColor
 fill=ImageColor.getrgb(color)+(int(opacity*255),)
 d.rounded_rectangle((0,0,im.width-1,im.height-1),radius=radius,fill=fill,outline=outline)
 return Image.alpha_composite(im.convert('RGBA'),layer).convert('RGB')

class SkinRenderer:
 def __init__(self,app):
  self.app=app;self.root=app.root;self.root._skin_renderer=self
  self._boxes={};self._root_position=None
  self._hold=False;self.fixed_size=(self.root.winfo_width(),self.root.winfo_height());self.active=False;self.scene=None;self.key=None;self.generation=0;self.job=None;self.tiles={};self.surfaces={};self.canvases={};self.bindings=[]
  self.fade_surface=tk.Label(self.root,bd=0,highlightthickness=0,padx=0,pady=0);self.fade_surface._theme_fixed=True;self.fade_surface._skin_surface_tile=True
  skins.prewarm(self.fixed_size)
  self.root.bind('<Map>',self._mapped,add='+');self.root.bind('<Configure>',self._root_change,add='+');self.root.bind('<Destroy>',self._destroy,add='+')
 def _mapped(self,event):
  if event.widget is self.root:
   if not getattr(self.root,'_main_ready',False):self.root.after_idle(self._restore_size);self.schedule()
 def _restore_size(self):
  if not self.active or not self.root.winfo_exists() or self.root.state()!='normal':return
  # Tk may reintroduce its old non-client height when restored from taskbar.
  # Keep the actual opaque HWND at the already measured fixed client size.
  import ctypes
  from ctypes import wintypes as W
  from ui_titlebar import apply_chrome
  apply_chrome(self.root);u=ctypes.windll.user32;hwnd=u.GetAncestor(self.root.winfo_id(),2);rect=W.RECT();u.GetWindowRect(ctypes.c_void_p(hwnd),ctypes.byref(rect))
  if (rect.right-rect.left,rect.bottom-rect.top)!=self.fixed_size:
   # Hide only a wrapper that actually needs resizing, so intermediate Tk
   # geometry never flashes; ordinary restores keep the opaque cached surface.
   if getattr(self.root,'_main_presented',False):
    from ui_window import _main_opacity
    _main_opacity(self.root,0)
   width,height=self.fixed_size
   request=getattr(self,'_restored_request',None)
   if request is not None:
    # Reuse the measured Tk/non-client offset, checking for wrapper changes.
    # Invalidate Tk's identical-request shortcut without an intermediate layout.
    self.root.geometry('')
    self.root.geometry(f'{request[0]}x{request[1]}')
    self.root.update_idletasks();apply_chrome(self.root)
    u.GetWindowRect(ctypes.c_void_p(hwnd),ctypes.byref(rect))
    if (rect.right-rect.left,rect.bottom-rect.top)==self.fixed_size:
     self.schedule();return
   # Tk can change its cached border offset when recreating the wrapper.
   # Recalibrate only when the cached request no longer fits the actual HWND.
   self.root.minsize(1,1);self.root.maxsize(10000,10000)
   self.root.geometry(f'{width}x{height}');self.root.update_idletasks()
   request_w=width-(self.root.winfo_width()-width);request_h=height-(self.root.winfo_height()-height)
   self.root.geometry(f'{request_w}x{request_h}');self.root.minsize(request_w,request_h);self.root.maxsize(request_w,request_h)
   self.root.update_idletasks();apply_chrome(self.root)
   self._restored_request=(request_w,request_h)
  self.schedule()
 def _destroy(self,event):
  if event.widget is self.root and self.job:
   self.root.after_cancel(self.job);self.job=None
 def _root_change(self,event):
  if event.widget is self.root and self.active:
   if self.scene is None or self.scene.size!=(event.width,event.height):self.schedule()
 def walk(self,widget):
  yield widget
  for child in widget.winfo_children():
   if isinstance(child,tk.Toplevel) or getattr(child,'_skin_surface_tile',False):continue
   yield from self.walk(child)
 def box(self,widget):
  if widget not in self._boxes:
   rx,ry=self._root_position or (self.root.winfo_rootx(),self.root.winfo_rooty())
   x=widget.winfo_rootx()-rx;y=widget.winfo_rooty()-ry
   self._boxes[widget]=(x,y,x+widget.winfo_width(),y+widget.winfo_height())
  return self._boxes[widget]
 def crop(self,widget):
  if self.scene is None:return None
  return self.scene.crop(self.box(widget))
 def schedule(self,event=None):
  if event is not None:
   self._boxes.pop(event.widget,None)
   if event.widget is self.root:self._root_position=(self.root.winfo_rootx(),self.root.winfo_rooty())
  if self.active and not self._hold and self.job is None:self.job=self.root.after(25,self.render)
 def apply(self):
  self._boxes={};self._root_position=(self.root.winfo_rootx(),self.root.winfo_rooty())
  self.key=skins.valid(self.app.cfg.get('skin'));self.active=True
  from ui_compact import refresh_icons
  refresh_icons(self.app)
  if not self.tiles:self.root.update_idletasks();self._install()
  for surface in self.surfaces.values():surface.place(x=0,y=0,relwidth=1,relheight=1);surface.lower()
  self.render(force=True)
 def _install(self):
  for widget in list(self.walk(self.root)):
   if isinstance(widget,(tk.Tk,tk.Frame,tk.LabelFrame)) and widget not in self.surfaces:
    if isinstance(widget,CozyFrame):surface=widget._surface
    else:
     surface=tk.Label(widget,bd=0,highlightthickness=0,padx=0,pady=0);surface._skin_surface_tile=True;surface._theme_fixed=True
     surface.place(x=0,y=0,relwidth=1,relheight=1);surface.lower()
    surface._skin_surface_tile=True;surface.bindtags((str(surface),str(widget),'all'));self.surfaces[widget]=surface
   if isinstance(widget,(tk.Label,tk.Radiobutton)) and widget not in self.tiles and not getattr(widget,'_skin_surface_tile',False):self._wrap(widget)
   if isinstance(widget,tk.Canvas) and widget not in self.canvases:
    self.canvases[widget]=None
   if not getattr(widget,'_skin_bound',False):
    widget._skin_bound=True;widget.bind('<Configure>',self.schedule,add='+')
 def _wrap(self,widget):
  native=widget.configure;get=widget.cget
  virtual={k:get(k) for k in ('text','image','compound','padx','pady','width','height','anchor') if k in widget.keys()}
  record={'config':native,'get':get,'virtual':virtual,'photo':None,'stamp':None,'border':get('borderwidth'),'highlight':get('highlightthickness'),'natural_height':widget.winfo_reqheight(),'natural_width':widget.winfo_reqwidth()};self.tiles[widget]=record
  def configure(cnf=None,**kw):
   if isinstance(cnf,dict):kw={**cnf,**kw};cnf=None
   if isinstance(cnf,str) and cnf in virtual:return (cnf,cnf,cnf,'',virtual[cnf])
   if cnf is None and not kw:
    result=native()
    for k,v in virtual.items():result[k]=(k,k,k,'',v)
    return result
   for k in list(kw):
    if k in virtual:virtual[k]=kw.pop(k)
   result=native(cnf,**kw) if cnf is not None or kw else None
   record['stamp']=None;self.schedule();return result
  def cget(key):return virtual[key] if key in virtual else get(key)
  widget.configure=widget.config=configure;widget.cget=cget
 def suspend(self):
  self.active=False
  if self.job:self.root.after_cancel(self.job);self.job=None
  for widget,record in self.tiles.items():
   if widget.winfo_exists():
    widget.configure=widget.config=record['config'];widget.cget=record['get'];record['config'](**record['virtual'],borderwidth=record['border'],highlightthickness=record['highlight'])
    if isinstance(widget,tk.Radiobutton):record['config'](selectimage='')
  self.tiles.clear()
  for widget,surface in self.surfaces.items():
   if surface.winfo_exists():
    if isinstance(widget,CozyFrame):widget._surface_key=None;widget._round()
    else:surface.place_forget()
  self.scene=None
 def _compose(self):
  size=(max(1,self.root.winfo_width()),max(1,self.root.winfo_height()))
  artwork_stamp=(self.key,size,theme.c('card'))
  if getattr(self,'_artwork_stamp',None)!=artwork_stamp:
   self.has_picture=self.key in skins.PROFILES
   image=skins.background(self.key,size,theme.c('card')) if self.has_picture else Image.new('RGB',size,theme.c('bg'))
   self._art_base=image;self._artwork_stamp=artwork_stamp
  image=self._art_base
  layer=Image.new('RGBA',size);d=ImageDraw.Draw(layer)
  # Transparent controls share one opaque scene. Only the section rules are
  # composited here; no card wash or selected-row plate covers the artwork.
  from PIL import ImageColor
  rule=ImageColor.getrgb(theme.accent)+(145,)
  frames=list(self.app.pages.values())+[self.app.sbar]
  left=self.box(self.app.container)[0]+round(4*scale(self.root))
  right=self.box(self.app.container)[2]-round(4*scale(self.root))
  for frame in frames:
   if frame.winfo_manager():
    y=self.box(frame)[1]
    d.line((left,y,right,y),fill=rule,width=max(1,round(scale(frame))))
  # Light dividers make the secondary action row read as four equal targets.
  buttons=[self.app.btn_enqueue,self.app.btn_pause,self.app.btn_stop,self.app.btn_now]
  for previous,button in zip(buttons,buttons[1:]):
   a,b=self.box(previous),self.box(button);x=(a[2]+b[0])//2
   d.line((x,b[1]+round(8*scale(button)),x,b[3]-round(8*scale(button))),fill=rule,width=1)
  return Image.alpha_composite(image.convert('RGBA'),layer).convert('RGB')
 def render(self,force=False):
  self.job=None
  if not self.active or not self.root.winfo_exists() or self.root.state()!='normal':return
  from ui_native_restore import pending
  if pending(self.root):return
  # Native restore can report normal before Tk receives its full client size.
  # Keep the completed scene through that transient zero/partial layout.
  if (self.root.winfo_width(),self.root.winfo_height())!=self.fixed_size:
   self.schedule();return
  self._boxes={};self._root_position=(self.root.winfo_rootx(),self.root.winfo_rooty())
  # No image work on drag: the positions below are relative to the main client.
  selected=self.app.action_var.get();selected_box=self.box(self.app.action_row_frames[selected][0]) if selected in self.app.action_row_frames else None
  stamp=(self.key,theme.accent,self.root.winfo_width(),self.root.winfo_height(),selected,selected_box,tuple((self.box(f),bool(f.winfo_manager())) for f in list(self.app.pages.values())+[self.app.sbar]))
  if force or getattr(self,'_scene_stamp',None)!=stamp:
   self._scene_stamp=stamp;self.scene=self._compose();self.generation+=1
  if getattr(self,"_defer_paint",False):return
  for widget,surface in list(self.surfaces.items()):
   if not widget.winfo_exists() or widget.winfo_width()<2 or widget.winfo_height()<2:continue
   key=(self.generation,self.box(widget))
   if getattr(surface,'_skin_stamp',None)!=key:
    surface._skin_stamp=key;im=self.crop(widget)
    if getattr(surface,'_skin_photo',None) is not None and (surface._skin_photo.width(),surface._skin_photo.height())==im.size:surface._skin_photo.paste(im)
    else:surface._skin_photo=ImageTk.PhotoImage(im,master=self.root);surface.configure(image=surface._skin_photo)
    surface.configure(bg=theme.c('bg'))
  for widget,record in list(self.tiles.items()):
   if widget.winfo_exists() and widget.winfo_ismapped():self._paint_text(widget,record)
  for widget in self.walk(self.root):
   if isinstance(widget,CozyButton):
    if getattr(widget,'_skin_generation',None)!=(self.generation,self.box(widget)):widget._skin_generation=(self.generation,self.box(widget));widget._last_paint=None;widget._schedule()
  self.canvas_backgrounds()
  if hasattr(self.app,'quick_heading'):self.app.quick_heading.draw()
  for fields in getattr(self.app,'time_inputs',{}).values():
   for field in fields:
    stamp=(self.generation,self.box(field))
    if field.winfo_ismapped() and getattr(field,'_main_surface_stamp',None)!=stamp:
     field._main_surface_stamp=stamp;field.draw()
 def _paint_text(self,widget,record):
  if widget.winfo_width()<2 or widget.winfo_height()<2:return
  v=record['virtual'];get=record['get'];box=self.box(widget)
  disabled=str(get('state'))=='disabled' if 'state' in widget.keys() else False
  color=str(get('disabledforeground' if disabled else 'foreground'))
  stamp=(self.generation,box,tuple((k,str(x)) for k,x in v.items()),str(get('font')),color,disabled,current_focus(widget) is widget)
  if record['stamp']==stamp:return
  record['stamp']=stamp;im=self.crop(widget)
  if isinstance(widget,tk.Radiobutton):im=im.crop((0,0,max(1,im.width-2),max(1,record['natural_height']-2)))
  base=im;ink_stamp=(im.size,stamp[2:])
  if record.get('ink_stamp')!=ink_stamp:
   record['ink_stamp']=ink_stamp;im=Image.new('RGBA',im.size)
   draw=ImageDraw.Draw(im)
   font_spec=str(get('font'))
   if record.get('font_spec')!=font_spec:record['font_spec']=font_spec;record['font']=tkfont.Font(root=widget,font=font_spec)
   font=record['font'];size=font.actual('size');pixels=abs(size) if size<0 else size*float(widget.tk.call('tk','scaling'));pf=pil_font(round(pixels),font.actual('weight')=='bold')
   text=str(v.get('text',''));icon=None
   if v.get('image'):
    try:
     source=v['image']
     if isinstance(source,str):source=getattr(widget,'_theme_photo',None) or getattr(widget,'_nature_photo',None)
     if source:icon=ImageTk.getimage(source).convert('RGBA')
    except (ValueError,AttributeError,tk.TclError):pass
   if icon and v.get('compound')=='none':text=''
   lines=text.split('\n');tw=max((font.measure(line) for line in lines),default=0);th=font.metrics('linespace')*len(lines) if text else 0;iw,ih=icon.size if icon else (0,0);gap=5 if text and icon else 0
   compound=str(v.get('compound'));vertical=compound in ('top','bottom');cw=max(tw,iw) if vertical else tw+iw+gap;ch=th+ih+gap if vertical else max(th,ih)
   anchor=str(v.get('anchor','center'));px=int(float(str(v.get('padx',0))));x=px if 'w' in anchor else im.width-cw-px if 'e' in anchor else (im.width-cw)/2;y=(im.height-ch)/2
   tx=x;ty=y;ix=x;iy=y
   if compound=='left':tx=x+iw+gap;ty=y+(ch-th)/2;iy=y+(ch-ih)/2
   elif compound=='right':ix=x+tw+gap;ty=y+(ch-th)/2;iy=y+(ch-ih)/2
   elif compound=='top':tx=x+(cw-tw)/2;ix=x+(cw-iw)/2;ty=y+ih+gap
   elif compound=='bottom':tx=x+(cw-tw)/2;ix=x+(cw-iw)/2;iy=y+th+gap
   else:tx=(im.width-tw)/2 if anchor=='center' else x;ix=(im.width-iw)/2 if anchor=='center' else x
   if icon:
    if disabled:
     a=icon.getchannel('A');icon=Image.new('RGBA',icon.size,color);icon.putalpha(a)
    im.paste(icon,(round(ix),round(iy)),icon)
   if text:
    for index,line in enumerate(lines):
     b=draw.textbbox((0,0),line,font=pf);draw.text((tx-b[0],ty+index*font.metrics('linespace')+(font.metrics('linespace')-(b[3]-b[1]))/2-b[1]),line,font=pf,fill=color)
   if current_focus(widget) is widget and isinstance(widget,tk.Radiobutton):draw.rounded_rectangle((0,0,im.width-1,im.height-1),radius=8,outline=theme.accent)
   record['ink']=im
  base.paste(record['ink'],(0,0),record['ink']);im=base
  if record['photo'] is not None and (record['photo'].width(),record['photo'].height())==im.size:record['photo'].paste(im)
  else:record['photo']=ImageTk.PhotoImage(im,master=self.root)
  kwargs=dict(image=record['photo'],text='',compound='none',padx=0,pady=0,width=record['natural_width'],height=record['natural_height'],borderwidth=0,highlightthickness=0)
  if isinstance(widget,tk.Radiobutton):kwargs.update(width=0,height=0,selectimage=record['photo'],relief='flat',offrelief='flat',overrelief='flat')
  record['config'](**kwargs)
 def canvas_backgrounds(self):
  if not self.active or self.scene is None:return
  for widget in self.canvases:
   if not widget.winfo_exists() or not widget.winfo_ismapped() or hasattr(widget,'draw'):continue
   key=(self.generation,self.box(widget))
   if getattr(widget,'_skin_canvas_stamp',None)!=key:
    widget._skin_canvas_stamp=key;im=self.crop(widget)
    if getattr(widget,'_skin_canvas_photo',None) is not None and (widget._skin_canvas_photo.width(),widget._skin_canvas_photo.height())==im.size:widget._skin_canvas_photo.paste(im)
    else:widget._skin_canvas_photo=ImageTk.PhotoImage(im,master=self.root)
   if not widget.find_withtag('skin_background'):widget.create_image(0,0,image=widget._skin_canvas_photo,anchor='nw',tags='skin_background')
   else:widget.itemconfigure('skin_background',image=widget._skin_canvas_photo)
   widget.tag_lower('skin_background')

class QuickHeading(tk.Canvas):
 def __init__(self,parent,app):
  self.app=app;self._draw_job=None
  super().__init__(parent,width=1,height=round(20*scale(parent)),bg=theme.c('card'),highlightthickness=0,bd=0)
  self.bind('<Configure>',lambda e:self.draw())
 def draw(self):
  if self.winfo_width()<2 or self.winfo_height()<5:return
  w=self.winfo_width();h=self.winfo_height();im=background(self) or Image.new('RGB',(w,h),theme.c('card'));d=ImageDraw.Draw(im)
  font=pil_font(round(11*scale(self)));text=self.app.T('quick_group');b=d.textbbox((0,0),text,font=font);tw=b[2]-b[0];left=(w-tw)//2;right=left+tw
  from theme import blend
  rule=blend(theme.accent,theme.c('card'),.45);gap=round(12*scale(self))
  d.line((0,h//2,left-gap,h//2),fill=rule,width=1);d.line((right+gap,h//2,w,h//2),fill=rule,width=1)
  d.text((left-b[0],(h-(b[3]-b[1]))//2-b[1]),text,font=font,fill=theme.accent)
  self._photo=ImageTk.PhotoImage(im,master=self);self.delete('all');self.create_image(0,0,anchor='nw',image=self._photo)
