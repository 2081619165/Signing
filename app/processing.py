"""签名文件校验、内存处理及独立导出；不依赖实验目录。"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import base64
import io
import os
from pathlib import Path
import tempfile
import threading
from PIL import Image, ImageOps
import numpy as np
from algorithm import extract, classify, extract_color
from sharpen import sharpen

def preview(image):
    im=image.copy();im.thumbnail((1200,900));stream=io.BytesIO();im.save(stream,format='PNG')
    return 'data:image/png;base64,'+base64.b64encode(stream.getvalue()).decode('ascii')

def gif_image(image):
    """单级透明配灰度调色板；不补画、不改变尺寸。"""
    a=np.asarray(image.convert('RGBA'))[...,3]
    active=a[a>=4]
    if not active.size:raise ValueError('GIF有效笔画过淡，请保留PNG')
    threshold=max(4,min(32,int(np.ceil(np.percentile(active,95)*.2))))
    # 若主要笔迹覆盖不足，降低阈值，但不纳入1至3级微弱噪点。
    reference=a>=8
    while threshold>4 and ((reference.any() and (a[reference]>=threshold).mean()<.95) or float(a[a>=threshold].sum())/max(float(a.sum()),1)<.95):
        threshold-=1
    mask=a>=threshold
    # 灰色不透明像素近似白底上的原Alpha外观，避免浅笔全部变黑。
    indices=np.where(mask,np.maximum(a,1),0).astype('uint8')
    pal=Image.fromarray(indices).convert('P')
    pal.putpalette([channel for i in range(256) for channel in (255-i,)*3])
    rgb=np.asarray(image.convert('RGB'))
    if np.any((rgb.max(2).astype(int)-rgb.min(2))[mask]>8):
        # 彩色分支使用255色量化，索引0专供透明；黑签原调色板保持不变。
        white=Image.new('RGBA',image.size,'white');white.alpha_composite(image.convert('RGBA'))
        quant=white.convert('RGB').quantize(colors=255,dither=Image.Dither.NONE)
        indices=np.where(mask,np.asarray(quant).astype('uint16')+1,0).astype('uint8')
        pal=Image.fromarray(indices).convert('P')
        palette=quant.getpalette()[:765]
        pal.putpalette([0,0,0]+palette+[0]*(765-len(palette)))
    report=gif_quality(a,mask)
    report['threshold']=threshold
    return pal,report


def gif_quality(alpha,mask):
    # 同尺寸比较；8级Alpha以上视为参考笔迹，墨量同时纳入更浅边缘。
    reference=alpha>=8
    coverage=float(mask[reference].mean()) if reference.any() else 0
    mass=float(alpha[mask].sum())/max(float(alpha.sum()),1)
    if coverage<.9 or mass<.9:
        raise ValueError('GIF相对PNG丢失大量有效笔画，请保留PNG（覆盖率%.1f%%，墨量%.1f%%）'%(coverage*100,mass*100))
    return dict(coverage=coverage,alpha_mass_retained=mass)


class Session:
    def __init__(self):
        self.full=None;self.crop_box=None;self.lock=threading.Lock();self.original=None;self.result=None;self.source=None;self.source_name=None

    def load(self, name, data, source=None):
        self.full=None;self.crop_box=None;self.original=None;self.result=None;self.source=None;self.source_name=None
        if Path(name).suffix.lower() not in {'.png','.jpg','.jpeg'}:raise ValueError('仅支持PNG/JPG/JPEG')
        if len(data)>30*1024*1024:raise ValueError('图片超过30MB')
        with Image.open(io.BytesIO(data)) as raw:
            if raw.format not in {'PNG','JPEG'}:raise ValueError('文件内容不是PNG/JPEG')
            if raw.width*raw.height>20_000_000:raise ValueError('图片超过2000万像素')
            im=ImageOps.exif_transpose(raw).convert('RGBA')
            paper=Image.new('RGBA',im.size,'white');paper.alpha_composite(im)
            self.original=paper.convert('RGB')
        self.full=self.original.copy()
        self.source=Path(source).resolve() if source else None
        self.source_name=Path(name).name
        return dict(name=name,preview=preview(self.original),classification=classify(self.original))

    def crop(self, box):
        # 坐标属于EXIF归正后的原图；验证完成后才修改会话。
        import math
        if self.full is None:raise ValueError('请先导入图片')
        if not isinstance(box,list) or len(box)!=4 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in box):raise ValueError('无效选区')
        x,y,r,b=box
        if not (0<=x<r<=self.full.width and 0<=y<b<=self.full.height):raise ValueError('选区越界或为空')
        coords=(math.floor(x),math.floor(y),math.ceil(r),math.ceil(b))
        if r-x<4 or b-y<4:raise ValueError('选区宽高至少4个原图像素')
        cropped=self.full.crop(coords)
        self.original=cropped;self.crop_box=list(coords);self.result=None
        return dict(preview=preview(cropped),box=self.crop_box,classification=classify(cropped))

    def process(self, enhance='standard', kind='auto'):
        self.result=None
        if self.original is None:raise ValueError('请先导入图片')
        identification=classify(self.original)
        if kind not in {'auto','black_signature','color_seal'}:raise ValueError('无效处理类型')
        chosen=identification['type'] if kind=='auto' else kind
        if chosen=='uncertain':raise ValueError(identification['reason'])
        # 手动类型只改变路由，空白与随机噪声仍拒绝。
        import cv2
        probe=np.asarray(self.original.convert('L'))
        edges=cv2.Laplacian(probe,cv2.CV_32F)
        if probe.std()<.5 or (float(np.std(edges))>110 and identification['diagnostics']['density']>.4):
            raise ValueError('图片为空白或噪声过多，无法可靠提取')
        color=chosen=='color_seal'
        result=extract_color(self.original) if color else extract(self.original)
        if color:
            alpha=np.asarray(result)[...,3]
            n,labels,stats,_=cv2.connectedComponentsWithStats((alpha>=8).astype('uint8'),8)
            if n<=1 or stats[1:,cv2.CC_STAT_AREA].max()<8 or (alpha>0).mean()>.65:
                raise ValueError('未检测到有效彩色主体或背景残留过多，请重新框选')
        if not result.getbbox():raise ValueError('未检测到有效签名笔画，请换图检查')
        result,report=(result,dict(reason='彩色保色处理，不应用黑签增强')) if color else sharpen(result,enabled=enhance)
        self.result=result
        box=result.getbbox()
        return dict(preview=preview(result),sharpen=report,content_size=[box[2]-box[0],box[3]-box[1]])

    def dimensions(self, settings=None):
        if self.result is None:raise ValueError('请先成功处理图片')
        box=self.result.getbbox()
        if not box:raise ValueError('没有有效笔画')
        settings=settings or {'unit':'cm','height':1.1,'dpi':96}
        if not isinstance(settings,dict):raise ValueError('无效尺寸设置')
        def number(value):
            try:n=Decimal(str(value))
            except InvalidOperation:raise ValueError('尺寸和DPI必须为数字')
            if not n.is_finite() or n<=0:raise ValueError('尺寸和DPI必须为正数')
            return n
        dpi=number(settings.get('dpi',96))
        if not 1<=dpi<=2400:raise ValueError('DPI范围为1至2400')
        unit=settings.get('unit','cm')
        if unit not in {'cm','px'}:raise ValueError('无效单位')
        width=settings.get('width')
        height=settings.get('height')
        ratio=Decimal(box[2]-box[0])/Decimal(box[3]-box[1])
        if width is None:
            height=number(height if height is not None else 1.1)
            width=height*ratio
        else:
            width=number(width)
            height=number(height) if height is not None else width/ratio
        factor=dpi/Decimal('2.54') if unit=='cm' else Decimal(1)
        w=int((width*factor).quantize(Decimal(1),rounding=ROUND_HALF_UP))
        h=int((height*factor).quantize(Decimal(1),rounding=ROUND_HALF_UP))
        if min(w,h)<1 or max(w,h)>10000 or w*h>20_000_000:raise ValueError('输出需至少1px，单边不超过10000px，总量不超过2000万像素')
        return dict(size=[w,h],dpi=float(dpi),cm=[float(Decimal(n)*Decimal('2.54')/dpi) for n in (w,h)])

    def export(self, path, kind, settings=None):
        if self.result is None:raise ValueError('请先成功处理图片')
        if kind not in {'png','gif'}:raise ValueError('不支持的导出格式')
        path=Path(path).with_suffix('.'+kind)
        if (self.source and path.resolve()==self.source) or (not self.source and path.name.casefold()==str(self.source_name).casefold()):raise ValueError('不能覆盖原始图片；请使用不同文件名')
        box=self.result.getbbox()
        if not box:raise ValueError('没有有效笔画')
        spec=self.dimensions(settings);w,h=spec['size']
        content=ImageOps.contain(self.result.crop(box),(w,h),Image.Resampling.LANCZOS)
        im=Image.new('RGBA',(w,h));im.alpha_composite(content,((w-content.width)//2,(h-content.height)//2))
        if kind=='gif':
            gif_alpha=np.asarray(im)[...,3].copy()
            im,quality=gif_image(im)
            if not (np.asarray(im)==0).any():raise ValueError('GIF没有透明背景')
        fd,temp=tempfile.mkstemp(dir=path.parent,suffix='.'+kind);os.close(fd)
        try:
            if kind=='gif':im.save(temp,format='GIF',transparency=0)
            else:im.save(temp,format='PNG',dpi=(spec['dpi'],spec['dpi']))
            with Image.open(temp) as check:
                actual_size=list(check.size)
                actual_dpi=check.info.get('dpi') if kind=='png' else None
                # PNG pHYs以整数像素/米存储，允许半个单位的量化误差。
                if kind=='png' and (not actual_dpi or any(abs(d-spec['dpi'])>0.0128 for d in actual_dpi)):
                    raise ValueError('导出重读检查失败：PNG DPI异常')
                a=np.asarray(check.convert('RGBA'))[...,3]
                if kind=='gif':quality.update(gif_quality(gif_alpha,a>0))
                if check.format!=kind.upper() or check.size!=(w,h) or not (a>0).any() or not (a==0).any():raise ValueError('导出重读检查失败：尺寸、格式、透明或笔画异常')
            # 校验后才替换目标，失败不留下伪成功文件。
            os.replace(temp,path)
        finally:
            if os.path.exists(temp):os.unlink(temp)
        return dict(path=str(path),size=actual_size,format=kind,dpi=actual_dpi,cm=spec['cm'],quality=quality if kind=='gif' else None)
