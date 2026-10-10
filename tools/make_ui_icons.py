"""绘制紧凑同页界面的图标；透明底、抗锯齿，不依赖字体符号。"""
import math
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
OUT=Path(__file__).resolve().parents[1]/'assets/ui'
OUT.mkdir(exist_ok=True)
BLUE='#3284ff'
COLORS={'shutdown':'#ff493c','restart':'#22bb73','logoff':'#ed910b','sleep':'#3284ff',
        'monitor_off':'#708396','run_program':'#3284ff','play_sound':'#7058ec','message':'#3284ff'}
def generate(name):
    im=Image.new('RGBA',(256,256))
    d=ImageDraw.Draw(im)
    def box(b):return tuple(int(v*4) for v in b)
    def line(points,fill,width=3):d.line([(int(x*4),int(y*4)) for x,y in points],fill=fill,width=width*4,joint='curve')
    def ellipse(b,fill=None,outline=None,width=3):d.ellipse(box(b),fill=fill,outline=outline,width=width*4)
    def arc(b,start,end,fill,width=3):d.arc(box(b),start,end,fill=fill,width=width*4)
    def poly(points,fill):d.polygon([(int(x*4),int(y*4)) for x,y in points],fill=fill)
    def rounded(b,color):d.rounded_rectangle(box(b),radius=5*4,fill=color)
    color=COLORS.get(name,BLUE)
    if name=='shutdown':
        arc((10,12,54,56),-52,232,color,5);line([(32,6),(32,32)],color,5)
    elif name=='restart':
        arc((10,10,54,54),35,316,color,5);poly([(53,8),(54,27),(36,23)],color)
    elif name=='logoff':
        ellipse((22,6,42,27),fill=color);rounded((10,33,54,58),color)
    elif name in ('sleep','moon'):
        ellipse((10,9,54,55),fill=color);ellipse((29,2,62,40),fill=(0,0,0,0))
    elif name=='monitor_off':
        d.rounded_rectangle(box((8,12,56,46)),radius=3*4,outline=color,width=4*4)
        line([(32,46),(32,56)],color,4);line([(20,56),(44,56)],color,4)
    elif name=='run_program':
        rounded((6,13,58,51),color);poly([(26,21),(43,32),(26,43)],'white')
    elif name=='play_sound':
        poly([(7,25),(20,25),(35,12),(35,52),(20,39),(7,39)],color)
        arc((30,17,56,47),-65,65,color,4);arc((37,8,63,56),-65,65,color,3)
    elif name=='message':
        rounded((6,10,58,51),color);poly([(16,48),(16,60),(29,49)],color)
        line([(16,23),(47,23)],'white',3);line([(16,33),(42,33)],'white',3)
    elif name=='clock':
        ellipse((12,12,52,52),outline=BLUE,width=3);line([(32,19),(32,33),(42,39)],BLUE,3)
    elif name=='sun':
        ellipse((22,22,42,42),outline=BLUE,width=3)
        for i in range(8):
            angle=i*math.pi/4
            line([(32+math.cos(angle)*17,32+math.sin(angle)*17),(32+math.cos(angle)*24,32+math.sin(angle)*24)],BLUE,3)
    elif name=='sunrise':
        arc((17,22,47,54),180,360,BLUE,3);line([(8,40),(56,40)],BLUE,3);line([(14,49),(50,49)],BLUE,3)
        for a in (0,45,90,135,180):
            theta=math.radians(a)
            line([(32+math.cos(theta)*21,39-math.sin(theta)*21),(32+math.cos(theta)*27,39-math.sin(theta)*27)],BLUE,3)
    elif name in ('check','step1','step2'):
        ellipse((4,4,60,60),fill=BLUE)
        if name=='check':line([(17,32),(27,42),(47,22)],'white',5)
        else:
            font=ImageFont.truetype(str(Path(os.environ.get('SystemRoot','C:/Windows'))/'Fonts/segoeuib.ttf'),size=37*4)
            d.text((128,121),name[-1],font=font,fill='white',anchor='mm')
    elif name=='play':poly([(18,9),(53,32),(18,55)],'white')
    elif name=='pause':
        rounded((16,13,27,51),'#93a3b8');rounded((37,13,48,51),'#93a3b8')
    elif name=='stop':rounded((15,15,49,49),'#93a3b8')
    elif name=='clear':
        line([(13,18),(51,18)],'#73849a',4);line([(24,10),(40,10)],'#73849a',4)
        line([(18,23),(21,54),(43,54),(46,23)],'#73849a',4)
        line([(28,26),(28,46)],'#73849a',3);line([(36,26),(36,46)],'#73849a',3)
    elif name=='enqueue':
        for y in (16,27,38):line([(10,y),(39,y)],'#73849a',3)
        line([(47,33),(47,55)],'#73849a',3);line([(36,44),(58,44)],'#73849a',3)
    elif name=='bolt':poly([(38,5),(14,36),(30,36),(24,59),(53,26),(36,26)],'#6b82ab')
    im.resize((64,64),Image.Resampling.LANCZOS).save(OUT/(name+'.png'))
for name in list(COLORS)+['clock','sun','moon','sunrise','check','step1','step2','play','pause','stop','clear','enqueue','bolt']:
    generate(name)
print('UI icons generated:',len(list(OUT.glob('*.png'))))
Image.new('RGBA',(64,64)).save(OUT/'blank.png')
