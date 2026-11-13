import sys,json,hashlib,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps,ImageDraw
from gray_signature import extract
from signature_sharpen import sharpen, export_gif
import argparse
parser=argparse.ArgumentParser();parser.add_argument("--no-sharpen",action="store_true");args=parser.parse_args()
root=Path(__file__).resolve().parents[1];local=root/'.local-tests';out=local/('gray-v2-off' if args.no_sharpen else 'gray-v2');out.mkdir(exist_ok=True)
sys.path.insert(0,str(local/'signature-extractor'));import main as baseline
sources=[(p.parent.name,p,'synthetic') for p in (local/'results').glob('*/original.png') if p.parent.name in ['white','gray','faint','shadow']]
sources += [('local_'+str(i),p,'local_unconfirmed') for i,p in enumerate(Path('D:/code/signature-extractor/input').glob('*')) if p.suffix.lower() in ['.png','.jpg','.jpeg']]
# 空白灰纸是背景误判的负例。
blank=out/'blank_gray.png';Image.new('RGB',(640,360),(180,180,180)).save(blank);sources.append(('blank',blank,'synthetic'))
rows=[]
for name,src,kind in sources:
 d=out/name;d.mkdir(exist_ok=True);shutil.copyfile(src,d/'original.png');rec=dict(name=name,kind=kind,sha256=hashlib.sha256(src.read_bytes()).hexdigest(),visual='待人工确认')
 try:
  baseline.extract_and_resize(src,d/'baseline.png');rec['baseline_output']=(d/'baseline.png').exists()
  rec['optimized']=extract(src,d/'optimized.png')
  native=Image.open(d/'optimized_native.png').convert('RGBA')
  enhanced,rec['sharpen']=sharpen(native,enabled=not args.no_sharpen)
  enhanced.save(d/'sharpened_native.png')
  rec['gif']=export_gif(enhanced,d/'signature.gif')
  panels=[]
  for file in ['baseline.png','optimized_native.png','sharpened_native.png']:
   if not (d/file).exists():continue
   im=Image.open(d/file).convert('RGBA');a=np.asarray(im)[...,3];rec[file]=dict(size=im.size,alpha_zero=int((a==0).sum()),alpha_nonzero=int((a>0).sum()),alpha_max=int(a.max()))
   for bg in ['white','dark','checker']:
    yy,xx=np.indices((im.height,im.width));v=np.where((xx//12+yy//12)%2,180,235).astype('uint8');back=Image.fromarray(np.dstack([v,v,v,np.full_like(v,255)])) if bg=='checker' else Image.new('RGBA',im.size,'white' if bg=='white' else (45,45,45,255))
    panel=Image.alpha_composite(back,im).convert('RGB');panel=ImageOps.contain(panel,(400,200));panel.save(d/(file[:-4]+'_'+bg+'.png'));panels.append((file+' '+bg,panel))
  sheet=Image.new('RGB',(1200,900),'#eeeeee');draw=ImageDraw.Draw(sheet);original=ImageOps.contain(Image.open(src).convert('RGB'),(390,200));sheet.paste(original,(0,20));draw.text((0,0),name+' ORIGINAL ('+kind+')',fill='black')
  for i,(label,panel) in enumerate(panels):x=i%3*400;y=230+i//3*220;sheet.paste(panel,(x,y+20));draw.text((x,y),label,fill='black')
  sheet.save(d/'comparison.jpg');rec['run']='success'
  truth=local/'results'/name/'truth_mask.png'
  if truth.exists():
   t=np.asarray(Image.open(truth))>0;a=np.asarray(Image.open(d/'optimized_native.png'))[...,3]>0;rec['native_metrics']=dict(ink_recall=float(a[t].mean()),background_false_positive=float(a[~t].mean()),thin_line_recall=float(a[270:281,80:561][t[270:281,80:561]].mean()))
 except Exception as e:rec['error']=str(e)
 rows.append(rec)
(out/'results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(rows,ensure_ascii=False))
