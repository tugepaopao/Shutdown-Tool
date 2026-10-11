"""The eight built-in skins; fixed identifiers keep backups portable."""
import sys
from pathlib import Path
from functools import lru_cache
from PIL import Image
SKIN_ORDER=('violet','plum','blue','pink','green','orange','teal','red')
PROFILES={
 'violet':('#7232D5','purple',('紫樱','紫櫻','Violet bloom')),
 'plum':('#852391','purple',('暮紫','暮紫','Twilight plum')),
 'blue':('#146FDA','blue',('雾蓝','霧藍','Misty blue')),
 'pink':('#C63F6C','pink',('樱粉','櫻粉','Cherry pink')),
 'green':('#2C6033','green',('森绿','森綠','Forest green')),
 'orange':('#DE6416','orange',('蜜橙','蜜橙','Honey orange')),
 'teal':('#008E98','teal',('浅青','淺青','Seafoam')),
 'red':('#BA3445','red',('绯红','緋紅','Crimson rose')),
}
SKIN_CHOICES=('solid',)+SKIN_ORDER

def valid(key):return key if key in SKIN_CHOICES else 'solid'
def name(key,lang='CHS'):
 names={'solid':('默认纯色','預設純色','Solid colors'),'builtin':('内置皮肤','內建皮膚','Built-in skins')}
 return names.get(key,PROFILES.get(key,PROFILES['violet'])[2])[{'CHS':0,'CHT':1,'EN':2}.get(lang,0)]
def path(key,preview=False):
 base=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent.parent))
 return base/'assets'/'skins'/((valid(key)+'-preview.png') if preview else (valid(key)+'.png'))
@lru_cache(maxsize=len(SKIN_ORDER))
def artwork(key):
 with Image.open(path(key)) as im:return im.convert('RGB')
@lru_cache(maxsize=len(SKIN_ORDER))
def preview(key):
 with Image.open(path(key,True)) as im:return im.convert('RGB')
@lru_cache(maxsize=len(SKIN_ORDER))
def palette(key):
 from theme import palette_for,blend
 accent,legacy,_=PROFILES[valid(key)];p=dict(palette_for(legacy))
 p.update(fg='#25212D',input_fg='#25212D',fg_dim='#65596A',fg_muted='#84758B',disabled='#9B8FA2',accent_fg='#FFFFFF')
 for role,t in {'bg':.07,'card':.025,'sel_row_bg':.20,'hover':.13,'card_border':.18,'divider':.18,'header_bg':.07,'status_bg':.08,'input_bg':.015,'nav_active_bg':.15}.items():p[role]=blend('#FFFFFF',accent,t)
 return p


def image_skin(cfg):return valid(cfg.get('skin')) in PROFILES

@lru_cache(maxsize=24)
def background(key,size,card):
 from PIL import ImageOps
 image=ImageOps.fit(artwork(key),size,method=Image.Resampling.LANCZOS,centering=(.5,.5))
 mask=Image.linear_gradient('L').resize(size).point(lambda x:round(6+x*.20))
 return Image.composite(Image.new('RGB',size,card),image,mask)

def prewarm(size):
 # Only Pillow work runs here; no Tk or user config is accessed off-thread.
 import threading
 def warm():
  for key in SKIN_ORDER:
   try:background(key,size,palette(key)['card'])
   except (OSError,ValueError):pass
 threading.Thread(target=warm,name='skin-cache',daemon=True).start()
