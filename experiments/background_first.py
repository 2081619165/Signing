"""背景优先对照；输出仅允许在.local-tests，不替换正式算法。"""
import argparse
import json
import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from algorithm import extract


def background_first(image):
    # 仅把所有通道均接近白色视为背景，软过渡保留深色细笔；不是PS颜色范围复刻。
    rgb=np.asarray(image.convert('RGB'))
    darkness=255-rgb.min(axis=2).astype(float)
    alpha=np.clip((darkness-20)/70,0,1)
    a=Image.fromarray(np.round(alpha*255).astype('uint8')).filter(ImageFilter.GaussianBlur(.3))
    out=image.convert('RGBA');out.putalpha(a)
    return out


def metrics(image,truth=None):
    a=np.asarray(image.convert('RGBA'))[...,3]
    rec={'size':list(image.size),'alpha_histogram':np.bincount(a.ravel(),minlength=256).tolist(),
         'components':{str(t):int(cv2.connectedComponents((a>=t).astype('uint8'),8)[0]-1) for t in (1,32,128)},
         'gif_threshold_removed':int(((a>0)&(a<128)).sum())}
    if truth is not None:
        t=np.asarray(truth)>0
        rec.update(ink_recall=float((a[t]>0).mean()),background_residue=float((a[~t]>0).mean()),
                   ink_recall_128=float((a[t]>=128).mean()))
        # 每条已知独立细线是否保持端到端连续，避免只比较像素总数。
        rec['line_continuity']={str(level):[bool((a[y,20:301]>=level).all()) for y in (30,70,110)] for level in (1,32,128)}
    return rec


def run(image,out,truth=None):
    out.mkdir(parents=True,exist_ok=True);image.save(out/'input.png')
    if truth is not None:truth.save(out/'truth.png')
    rows={}
    # 相同原始视野、相同缩放，避免各自裁剪掩盖算法损失。
    for name,native in [('v1',extract(image)),('background',background_first(image))]:
        rows[name]={}
        for label,im in [('native',native),('small',native.resize((148,74),Image.Resampling.LANCZOS))]:
            path=out/(name+'_'+label+'.png');im.save(path)
            with Image.open(path) as check:rows[name][label]=metrics(check,truth if label=='native' else None)
            for bg in ('white','#333333'):
                back=Image.new('RGBA',im.size,bg);back.alpha_composite(im);back.convert('RGB').save(out/(name+'_'+label+'_'+('white' if bg=='white' else 'dark')+'.png'))
            if label=='small':
                a=np.asarray(im)[...,3];pal=Image.fromarray((a>=128).astype('uint8')).convert('P');pal.putpalette([0]*768)
                target=out/(name+'_small.gif');pal.save(target,transparency=0)
                with Image.open(target) as check:rows[name]['gif']=metrics(check)
    return rows


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path);parser.add_argument('--output',type=Path,default=ROOT/'.local-tests/background-first');args=parser.parse_args()
    out=args.output.resolve();out.relative_to((ROOT/'.local-tests').resolve())
    results={'limitations':'仅合成图有真值；颜色范围不等同PS；连通域数不能独立证明质量；真实笔迹视觉待验','cases':{}}
    if args.input:
        with Image.open(args.input) as raw:
            im=ImageOps.exif_transpose(raw).convert('RGBA');paper=Image.new('RGBA',im.size,'white');paper.alpha_composite(im)
        results['cases']['local_unverified']=run(paper.convert('RGB'),out/'local_unverified')
    else:
        for name,paper,inks in [('white',255,(20,150,230)),('gray',185,(20,150,183))]:
            im=Image.new('RGB',(320,160),(paper,)*3);truth=Image.new('L',im.size)
            for y,ink in zip((30,70,110),inks):
                ImageDraw.Draw(im).line((20,y,300,y),fill=(ink,)*3,width=1);ImageDraw.Draw(truth).line((20,y,300,y),fill=255,width=1)
            im.putpixel((310,140),(20,)*3);truth.putpixel((310,140),255)
            results['cases'][name]=run(im,out/name,truth)
    out.mkdir(parents=True,exist_ok=True);(out/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({name:{alg:{k:v for k,v in data['native'].items() if k!='alpha_histogram'} for alg,data in case.items()} for name,case in results['cases'].items()},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
