"""签名文件校验、内存处理及独立导出；不依赖实验目录。"""
import base64
import io
import os
from pathlib import Path
import tempfile
import threading
from PIL import Image, ImageOps
import numpy as np
from algorithm import extract
from sharpen import sharpen

def preview(image):
    im=image.copy();im.thumbnail((1200,900));stream=io.BytesIO();im.save(stream,format='PNG')
    return 'data:image/png;base64,'+base64.b64encode(stream.getvalue()).decode('ascii')

class Session:
    def __init__(self):
        self.lock=threading.Lock();self.original=None;self.result=None;self.source=None;self.source_name=None

    def load(self, name, data, source=None):
        self.original=None;self.result=None;self.source=None;self.source_name=None
        if Path(name).suffix.lower() not in {'.png','.jpg','.jpeg'}:raise ValueError('仅支持PNG/JPG/JPEG')
        if len(data)>30*1024*1024:raise ValueError('图片超过30MB')
        with Image.open(io.BytesIO(data)) as raw:
            if raw.format not in {'PNG','JPEG'}:raise ValueError('文件内容不是PNG/JPEG')
            if raw.width*raw.height>20_000_000:raise ValueError('图片超过2000万像素')
            im=ImageOps.exif_transpose(raw).convert('RGBA')
            paper=Image.new('RGBA',im.size,'white');paper.alpha_composite(im)
            self.original=paper.convert('RGB')
        self.source=Path(source).resolve() if source else None
        self.source_name=Path(name).name
        return dict(name=name,preview=preview(self.original))

    def process(self, enhance=False):
        self.result=None
        if self.original is None:raise ValueError('请先导入图片')
        result=extract(self.original)
        if not result.getbbox():raise ValueError('未检测到有效签名笔画，请换图检查')
        result,report=sharpen(result,enabled=enhance)
        self.result=result
        return dict(preview=preview(result),sharpen=report)

    def export(self, path, kind):
        if self.result is None:raise ValueError('请先成功处理图片')
        if kind not in {'png','gif'}:raise ValueError('不支持的导出格式')
        path=Path(path).with_suffix('.'+kind)
        if (self.source and path.resolve()==self.source) or (not self.source and path.name.casefold()==str(self.source_name).casefold()):raise ValueError('不能覆盖原始图片；请使用不同文件名')
        box=self.result.getbbox()
        if not box:raise ValueError('没有有效笔画')
        im=self.result.crop(box);h=round(1.1/2.54*96);w=max(1,round(im.width*h/im.height))
        im=im.resize((w,h),Image.Resampling.LANCZOS)
        if kind=='gif':
            a=np.asarray(im)[...,3];mask=a>=128
            if not mask.any():raise ValueError('GIF转换后全透明；请保留PNG，不能导出有效GIF')
            if mask.all():raise ValueError('GIF没有透明背景')
            pal=Image.fromarray(mask.astype('uint8')).convert('P');pal.putpalette([0]*768);im=pal
        fd,temp=tempfile.mkstemp(dir=path.parent,suffix='.'+kind);os.close(fd)
        try:
            if kind=='gif':im.save(temp,format='GIF',transparency=0)
            else:im.save(temp,format='PNG',dpi=(96,96))
            with Image.open(temp) as check:
                a=np.asarray(check.convert('RGBA'))[...,3]
                if check.format!=kind.upper() or check.size!=(w,h) or not (a>0).any() or not (a==0).any():raise ValueError('导出重读检查失败：尺寸、格式、透明或笔画异常')
            # 校验后才替换目标，失败不留下伪成功文件。
            os.replace(temp,path)
        finally:
            if os.path.exists(temp):os.unlink(temp)
        return dict(path=str(path),size=[w,h],format=kind)
