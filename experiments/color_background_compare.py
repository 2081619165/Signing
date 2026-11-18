"""彩章背景新旧对照；仅合成图，tracemalloc非进程总内存。"""
import sys,json,time,tracemalloc
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from algorithm import extract_color,extract_color_baseline
# 可选真实本地输入只输出到.local-tests，不写入日志图像或文件名。
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path);args=parser.parse_args()
if args.input:
    out=ROOT/'.local-tests/color-background/local-diagnostic';out.mkdir(parents=True,exist_ok=True)
    from PIL import ImageOps
    with Image.open(args.input) as raw:
        image=ImageOps.exif_transpose(raw).convert('RGBA')
        paper=Image.new('RGBA',image.size,'white');paper.alpha_composite(image);image=paper.convert('RGB')
    before=extract_color_baseline(image);after,report=extract_color(image,local=True,with_report=True)
    before.save(out/'baseline.png');after.save(out/'local.png')
    # 真实样本仅写入.local-tests，供白/黑/棋盘格人工逐项对照。
    sheet=Image.new('RGB',(image.width*3,(image.height+24)*3),'white');draw=ImageDraw.Draw(sheet)
    for row,background in enumerate(('white','black','checker')):
        for col,(title,foreground) in enumerate((('INPUT',image.convert('RGBA')),('BASELINE',before),('CANDIDATE',after))):
            if background=='checker':
                yy,xx=np.indices((image.height,image.width));v=np.where((xx//10+yy//10)%2,180,235).astype('uint8')
                back=Image.fromarray(np.dstack((v,v,v,np.full_like(v,255))))
            else:back=Image.new('RGBA',image.size,background)
            back.alpha_composite(foreground)
            x=col*image.width;y=row*(image.height+24)
            sheet.paste(back.convert('RGB'),(x,y+24));draw.text((x+4,y+4),title+' '+background,fill='black')
    sheet.save(out/'comparison.png')
    from processing import Session
    stream=__import__('io').BytesIO();image.save(stream,format='PNG')
    session=Session();session.load('local-input.png',stream.getvalue())
    try:
        reply=session.process(kind='color_seal')
        report['pipeline_success']=True
        report['pipeline_method']=reply['color_report']['method']
    except ValueError as exc:
        report['pipeline_success']=False;report['pipeline_error']=str(exc)
    (out/'diagnostics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('本地对照已生成，完整提取流程成功：',report['pipeline_success'],'；视觉质量仍需人工检查')
    raise SystemExit(0)
out=ROOT/'.local-tests/color-background';out.mkdir(parents=True,exist_ok=True)
rows={};sheet=Image.new('RGB',(960,1080),'white')
for row,(name,paper,ink) in enumerate((('red',255,(180,25,35)),('blue',255,(60,90,190)),('pale',210,(206,202,202)),('cast_shadow',220,(190,65,75)),('pink_texture',220,(190,65,75)),('blue_texture',220,(60,90,190)))):
 y,x=np.mgrid[:180,:240];base=np.full((180,240,3),paper,dtype=float)
 if name=='cast_shadow':base-=x[...,None]*.12;base+=np.array((9,0,-5))
 if name in ('pink_texture','blue_texture'):
  base+=np.array((5,-10,-5));base-=x[...,None]*.08
  base+=np.random.default_rng(6).normal(0,1,(180,240,1))
 truth=Image.new('L',(240,180));d=ImageDraw.Draw(truth);d.ellipse((30,20,210,160),outline=255,width=3);d.line((65,90,175,90),fill=255,width=1)
 pixels=np.clip(base,0,255).astype('uint8');mask=np.asarray(truth)>0;pixels[mask]=ink
 im=Image.fromarray(pixels);im.save(out/(name+'_input.png'));rows[name]={}
 for col,mode in enumerate(('baseline','local')):
  tracemalloc.start();t=time.perf_counter()
  result=extract_color_baseline(im) if mode=='baseline' else extract_color(im,local=True)
  ms=(time.perf_counter()-t)*1000;_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
  result.save(out/(name+'_'+mode+'.png'));a=np.asarray(result)[...,3]
  rows[name][mode]=dict(ms=round(ms,2),tracked_peak_bytes=peak,recall=float((a[mask]>0).mean()),background_fraction=float((a[~mask]>0).mean()))
  back=Image.new('RGBA',im.size,'white');back.alpha_composite(result);sheet.paste(back.convert('RGB'),(col*240,row*180))
 sheet.paste(im,(480,row*180));ImageDraw.Draw(sheet).text((725,row*180+20),name,fill='black')
sheet.save(out/'comparison.png');(out/'results.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');print(json.dumps(rows))
