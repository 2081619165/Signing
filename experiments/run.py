import sys,json,importlib.util,platform
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageOps
root=Path(__file__).resolve().parents[1]; local=root/'.local-tests'; out=local/'results';out.mkdir(exist_ok=True)
sys.path.insert(0,str(local/'signature-extractor'))
import main as sig
import seal_extractor as seal
spec=importlib.util.spec_from_file_location('leo',local/'seal-extractor/scripts/extract_seal.py');leo=importlib.util.module_from_spec(spec);spec.loader.exec_module(leo)
records=[]
# 完全虚构的曲线与 TEST 图案，不使用真实签名印章。
for name,bg,ink,kind in [('white',255,25,'sig'),('gray',185,25,'sig'),('faint',245,190,'sig'),('red',245,(200,35,30),'seal'),('pale_red',245,(240,200,200),'seal'),('blue',245,(30,70,200),'seal'),('shadow',245,35,'sig')]:
 d=out/name;d.mkdir(exist_ok=True); mask=Image.new('L',(640,360));draw=ImageDraw.Draw(mask)
 if kind=='sig':
  draw.line([(65,250),(120,100),(160,240),(225,130),(260,235),(360,150),(445,235),(555,120)],fill=255,width=7);draw.line((80,280,560,270),fill=255,width=1)
 else:
  draw.ellipse((190,50,450,310),outline=255,width=6);draw.text((270,170),'TEST ONLY',fill=255);draw.line((240,220,400,220),fill=255,width=2)
 base=np.full((360,640,3),bg,dtype=np.float32)
 if name=='shadow':base*=np.linspace(.48,1,640)[None,:,None]
 fg=np.full_like(base,ink); a=np.asarray(mask)[...,None]/255; im=Image.fromarray(np.uint8(base*(1-a)+fg*a));src=d/'original.png';im.save(src);mask.save(d/'truth_mask.png')
 for project in ['show7','leopens']:
  rec=dict(sample=name,project=project,visual='待人工确认',parameters='upstream defaults',supported=not(project=='leopens' and kind=='sig') and name!='blue')
  if not rec['supported']:rec['run']='不支持';records.append(rec);continue
  dest=d/(project+'.png')
  try:
   if project=='show7':(sig.extract_and_resize if kind=='sig' else seal.process_seal)(src,dest)
   else:leo.extract(src,dest,quiet=True)
   if not dest.exists():raise ValueError('upstream skipped: no output')
   result=Image.open(dest).convert('RGBA');alpha=np.asarray(result)[...,3];rec.update(run='成功',format=bool((alpha==0).any() and (alpha>0).any()),size=result.size,alpha_zero=int((alpha==0).sum()),alpha_partial=int(((alpha>0)&(alpha<255)).sum()))
   preview=Image.new('RGB',(960,390),'white');p=ImageDraw.Draw(preview);p.text((5,5),name+' | original / white / checker | '+project,fill='black')
   preview.paste(ImageOps.contain(im,(310,350)),(0,30))
   for x,check in [(320,False),(640,True)]:
    panel=Image.new('RGBA',result.size,'white')
    if check:
     ar=np.indices((result.height,result.width)).sum(axis=0) # 下方使用方格而非斜纹
     yy,xx=np.indices((result.height,result.width));v=np.where((xx//12+yy//12)%2,200,245).astype('uint8');panel=Image.fromarray(np.dstack([v,v,v,np.full_like(v,255)]))
    panel=Image.alpha_composite(panel,result);preview.paste(ImageOps.contain(panel.convert('RGB'),(310,350)),(x,30))
   preview.save(d/(project+'_compare.png'))
   # GIF 仅有一位透明；按 alpha>=128 转换，不补画。
   content=result.crop(result.getbbox())
   sizes=[('sign42',None,42),('sign34',None,34)] if kind=='sig' else [('legal',60,60),('builder',151,106),('official',151,151)]
   rec['gif']=[]
   for label,w,h in sizes:
    if w is None:w=max(1,round(content.width*h/content.height))
    small=ImageOps.contain(content,(w,h),Image.Resampling.LANCZOS);canvas=Image.new('RGBA',(w,h));canvas.alpha_composite(small,((w-small.width)//2,(h-small.height)//2))
    pal=canvas.convert('RGB').quantize(colors=255);aa=np.asarray(canvas)[...,3];idx=np.asarray(pal).copy();idx[aa<128]=255;gif=Image.fromarray(idx,'P');palette=pal.getpalette();gif.putpalette(palette+[0]*(768-len(palette)));path=d/(project+'_'+label+'.gif');gif.save(path,transparency=255)
    read=Image.open(path); ga=np.asarray(read.convert('RGBA'))[...,3];rec['gif'].append(dict(file=path.name,size=read.size,expected=[w,h],transparent=bool((ga==0).any()),nonempty=bool((ga>0).any()),visual='待人工确认',dpi_basis=96))
  except (Exception,SystemExit) as e:rec.update(run='失败',error=str(e))
  records.append(rec)
(local/'results.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(records,ensure_ascii=False))
