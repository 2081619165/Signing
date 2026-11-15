"""同尺寸GIF阈值比较，仅生成合成材料。"""
import sys,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from processing import gif_image
out=ROOT/'.local-tests/gif-alpha';out.mkdir(parents=True,exist_ok=True)
im=Image.new('RGBA',(36,42));d=ImageDraw.Draw(im)
for y,a in ((5,24),(15,50),(25,100)):
    d.line((3,y,32,y),fill=(0,0,0,a),width=1)
im.putpixel((1,40),(0,0,0,2));im.save(out/'before.png');a=np.asarray(im)[...,3]
rows={}
for t in (1,8,16,32,64,128):
    mask=a>=t;rows[str(t)]={'pixels':int(mask.sum()),'continuous_lines':[bool(mask[y,3:33].all()) for y in (5,15,25)],'noise_retained':bool(mask[40,1])}
pal,report=gif_image(im);pal.save(out/'after.gif',transparency=0)
with Image.open(out/'after.gif') as check:
    mask=np.asarray(check.convert('RGBA'))[...,3]>0
    rows['adaptive']={**report,'pixels':int(mask.sum()),'size':list(check.size),'continuous_lines':[bool(mask[y,3:33].all()) for y in (5,15,25)],'noise_retained':bool(mask[40,1])}
(out/'results.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');print(json.dumps(rows))
