"""原创SealKit几何印章图标；同一几何源生成SVG、PNG和ICO。"""
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'app/assets'
# 256单位蓝色圆角底、白色印章柄和底座，小尺寸避免文字细节。
SHAPES=[('round',(8,8,248,248),52,'#245ac2'),('round',(94,48,162,120),24,'white'),('poly',[(104,102),(152,102),(176,164),(80,164)],0,'white'),('round',(48,158,208,202),12,'white')]

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    image=Image.new('RGBA',(1024,1024));draw=ImageDraw.Draw(image)
    svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">']
    for kind,coords,radius,color in SHAPES:
        if kind=='round':
            draw.rounded_rectangle(tuple(v*4 for v in coords),radius=radius*4,fill=color)
            x,y,r,b=coords;svg.append(f'<rect x="{x}" y="{y}" width="{r-x}" height="{b-y}" rx="{radius}" fill="{color}"/>')
        else:
            draw.polygon([(x*4,y*4) for x,y in coords],fill=color)
            points=' '.join(f'{x},{y}' for x,y in coords);svg.append(f'<polygon points="{points}" fill="{color}"/>')
    (OUT/'sealkit.svg').write_text(''.join(svg)+'</svg>',encoding='utf-8')
    image=image.resize((256,256),Image.Resampling.LANCZOS)
    image.save(OUT/'sealkit.png');image.save(OUT/'sealkit.ico',sizes=[(n,n) for n in (16,20,24,32,40,48,64,128,256)])

if __name__=='__main__':main()
