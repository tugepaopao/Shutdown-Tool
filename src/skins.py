"""Fixed violet artwork for the public violet edition."""
import sys
from pathlib import Path
from functools import lru_cache
from PIL import Image
SKIN_ORDER=('violet',)
PROFILES={'violet':('#7232D5','purple',('紫樱','紫櫻','Violet bloom'))}
SKIN_CHOICES=SKIN_ORDER
# Accept old public settings/backups before Config normalizes their appearance.
ACCEPTED_SKINS={'solid','violet','plum','blue','pink','green','orange','teal','red','custom'}
def valid(key):return 'violet'

def path(key,preview=False):
 base=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent.parent))
 return base/'assets'/'skins'/(valid(key)+'.png')
@lru_cache(maxsize=len(SKIN_ORDER))
def artwork(key):
 with Image.open(path(key)) as im:return im.convert('RGB')
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
 mask=Image.linear_gradient('L').resize(size).point(lambda x:round(4+x*.11))
 return Image.composite(Image.new('RGB',size,card),image,mask)

def prewarm(size):
 # Only Pillow work runs here; no Tk or user config is accessed off-thread.
 import threading
 def warm():
  for key in SKIN_ORDER:
   try:background(key,size,palette(key)['card'])
   except (OSError,ValueError):pass
 threading.Thread(target=warm,name='skin-cache',daemon=True).start()
