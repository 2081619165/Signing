"""四档笔迹增强对比，仅使用合成折线；输出留供人工验收。"""
import sys,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from processing import Session
from algorithm import extract
from sharpen import sharpen,legacy_sharpen
out=ROOT/'.local-tests/ink-enhancement';out.mkdir(parents=True,exist_ok=True)
rows={};sheet=Image.new('RGB',(640,480),'white')
for row,ink in enumerate((170,110,25)):
    src=Image.new('RGB',(320,160),(185,)*3);d=ImageDraw.Draw(src)
    d.line((20,130,90,25,140,125,290,40),fill=(ink,)*3,width=2)
    src.save(out/f'input_{ink}.png');base=extract(src);old,report=legacy_sharpen(base)
    rows[str(ink)]={'legacy':report,'legacy_changed':int(np.any(np.asarray(base)!=np.asarray(old),axis=2).sum())}
    for col,level in enumerate(('off','light','standard','strong')):
        im,report=sharpen(base,level);im.save(out/f'{ink}_{level}_native.png')
        s=Session();s.result=im
        config=dict(unit='px',width=160,height=80,dpi=96)
        exports={}
        for kind in ('png','gif'):
            target=out/f'{ink}_{level}.{kind}';exports[kind]=s.export(target,kind,config)
        with Image.open(out/f'{ink}_{level}.png') as check:
            bg=Image.new('RGBA',check.size,'white');bg.alpha_composite(check.convert('RGBA'))
            sheet.paste(bg.convert('RGB'),(col*160,row*160+25))
            ImageDraw.Draw(sheet).text((col*160,row*160),f'{ink} {level}',fill='black')
        rows[str(ink)][level]={'report':report,'exports':exports}
sheet.save(out/'comparison.png');(out/'results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print({k:(v['legacy']['reason'],v['legacy_changed']) for k,v in rows.items()})
