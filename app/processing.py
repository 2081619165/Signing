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
from sharpen import sharpen, enhance_color_ink

# 大图只保留压缩源；解码预算按单次16字节/像素保守估算。
MAX_FILE_BYTES=30*1024*1024
MAX_SOURCE_PIXELS=50_000_000
MAX_WORK_PIXELS=2_000_000
MAX_WORK_SIDE=3200


def working_image(image):
    # 原图坐标和选区不变，只限制送入算法的像素量，不放大小图。
    import math
    scale=min(1,math.sqrt(MAX_WORK_PIXELS/(image.width*image.height)),MAX_WORK_SIDE/max(image.size))
    if scale==1:return image
    size=(max(1,int(image.width*scale)),max(1,int(image.height*scale)))
    return image.resize(size,Image.Resampling.LANCZOS)


def display_image(image,limit=(1600,1600)):
    scale=min(1,limit[0]/image.width,limit[1]/image.height)
    return image.resize((max(1,round(image.width*scale)),max(1,round(image.height*scale))),Image.Resampling.LANCZOS) if scale<1 else image.copy()


def paper_rgb(image):
    if image.mode=='RGB':return image.copy()
    rgba=image.convert('RGBA');paper=Image.new('RGBA',rgba.size,'white');paper.alpha_composite(rgba)
    return paper.convert('RGB')


class LargeSource:
    """原图坐标不变，框选显示只用缓存预览；确认后才解码裁切。"""
    def __init__(self,data,size,display):
        self.data=data;self.size=size;self.width,self.height=size;self.display=display
    def resize(self,size,resample=Image.Resampling.LANCZOS):
        return self.display.resize(size,resample)
    def crop(self,box):
        # PNG/JPEG裁切仍需解码，限制源尺寸和选区以约束峰值。
        with Image.open(io.BytesIO(self.data)) as raw:
            oriented=ImageOps.exif_transpose(raw)
            region=oriented.crop(box)
            work=None
            try:
                work=working_image(region)
                return paper_rgb(work)
            finally:
                if work is not None and work is not region:work.close()
                region.close()
                if oriented is not raw:oriented.close()


def preview(image):
    im=display_image(image,(1200,900));stream=io.BytesIO();im.save(stream,format='PNG')
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
        self.color_base=None;self.color_edited=False
        self.requires_crop=False;self.input_bytes=None;self.base_result=None;self.rotation=0;self.full=None;self.crop_box=None;self.lock=threading.Lock();self.original=None;self.result=None;self.source=None;self.source_name=None

    def load(self, name, data, source=None):
        self.color_base=None;self.color_edited=False
        self.requires_crop=False;self.input_bytes=None;self.base_result=None;self.rotation=0;self.full=None;self.crop_box=None;self.original=None;self.result=None;self.source=None;self.source_name=None
        if Path(name).suffix.lower() not in {'.png','.jpg','.jpeg'}:raise ValueError('仅支持PNG/JPG/JPEG')
        if len(data)>MAX_FILE_BYTES:raise ValueError('图片超过30MB')
        with Image.open(io.BytesIO(data)) as raw:
            if raw.format not in {'PNG','JPEG'}:raise ValueError('文件内容不是PNG/JPEG')
            pixels=raw.width*raw.height
            if pixels>MAX_SOURCE_PIXELS or pixels*16>800*1024*1024:
                raise ValueError('图片超出安全解码预算（最多5000万像素），请先在本地缩小原图')
            large=pixels>20_000_000
            orientation=raw.getexif().get(274,1)
            logical_size=(raw.height,raw.width) if orientation in (5,6,7,8) else raw.size
            if large:
                # JPEG可先draft减少预览解码量；PNG仍需解码，但不保留全尺寸副本。
                raw.draft('RGB',(1600,1600))
                small=display_image(raw)
                oriented=ImageOps.exif_transpose(small)
                display=paper_rgb(oriented)
            else:
                display=paper_rgb(ImageOps.exif_transpose(raw))
        self.input_bytes=len(data)
        self.requires_crop=False
        self.whole_work_ready=not large
        self.original=working_image(display)
        self.full=LargeSource(data,logical_size,display) if large else display.copy()
        self.source=Path(source).resolve() if source else None
        self.source_name=Path(name).name
        identification=classify(display_image(self.original))
        return dict(name=name,preview=preview(self.original),classification=identification)

    def commit_erasure(self, packed):
        if self.result is None:raise ValueError('请先成功提取')
        width,height=self.result.size
        if len(packed)!=(width*height+7)//8:raise ValueError('擦除数据尺寸不符')
        mask=np.unpackbits(np.frombuffer(packed,dtype=np.uint8),count=width*height,bitorder='little').reshape(height,width)
        pixels=np.array(self.result)
        pixels[...,3][mask!=0]=0
        edited=Image.fromarray(pixels)
        box=edited.getbbox()
        if box is None:raise ValueError('结果已全部擦除，请保留有效笔迹')
        response=dict(preview=preview(edited),canvas_size=edited.size,content_size=[box[2]-box[0],box[3]-box[1]])
        # 当前方向成为新的旋转起点，原图与原提取对象均未就地修改。
        self.base_result=self.result=edited
        self.color_edited=self.color_base is not None
        self.rotation=0
        return response

    def rotate_result(self, angle):
        # 只从提取后的透明母版旋转，避免累计重采样和白底污染。
        import math
        if self.base_result is None or self.result is None:raise ValueError('请先成功提取')
        if isinstance(angle,bool) or not isinstance(angle,(int,float)) or not -180<=angle<=180:raise ValueError('旋转角度需在-180至180度')
        rotated,response=self._rotation(self.base_result,angle)
        self.result=rotated;self.rotation=angle
        return response

    @staticmethod
    def _rotation(base,angle):
        rotated=base.rotate(angle,resample=Image.Resampling.BICUBIC,expand=True,fillcolor=(0,0,0,0)) if angle else base
        box=rotated.getbbox()
        return rotated,dict(preview=preview(rotated),canvas_size=rotated.size,content_size=[box[2]-box[0],box[3]-box[1]],angle=angle)

    def set_color_enhancement(self, enabled, discard_edits=False):
        if type(enabled) is not bool or type(discard_edits) is not bool:raise ValueError('无效的色彩增强设置')
        if self.color_base is None or self.result is None:raise ValueError('请先提取彩色印章')
        if self.color_edited and not discard_edits:raise ValueError('请确认覆盖已完成的橡皮擦编辑')
        base,report=enhance_color_ink(self.color_base,enabled)
        angle=0 if self.color_edited else self.rotation
        result,response=self._rotation(base,angle)
        self.base_result,self.result,self.rotation=base,result,angle
        self.color_edited=False
        return dict(response,base_canvas_size=base.size,sharpen=report)

    def validate_crop(self, box):
        # 坐标属于EXIF归正后的原图；验证完成后才修改会话。
        import math
        if self.full is None:raise ValueError('请先导入图片')
        if not isinstance(box,list) or len(box)!=4 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in box):raise ValueError('无效选区')
        x,y,r,b=box
        if not (0<=x<r<=self.full.width and 0<=y<b<=self.full.height):raise ValueError('选区越界或为空')
        coords=(math.floor(x),math.floor(y),math.ceil(r),math.ceil(b))
        if r-x<4 or b-y<4:raise ValueError('选区宽高至少4个原图像素')
        return coords

    def crop(self, box):
        coords=self.validate_crop(box)
        try:
            cropped=working_image(self.full.crop(coords))
        except MemoryError as exc:
            raise ValueError('原图解码或裁切内存不足，请关闭其他程序或先缩小原图') from exc
        # 预览和分类成功后一次提交，失败不留下半更新的状态。
        image_preview=preview(cropped)
        identification=classify(cropped)
        self.color_base=None;self.color_edited=False
        self.base_result=None;self.rotation=0;self.requires_crop=False;self.original=cropped;self.crop_box=list(coords);self.result=None
        return dict(preview=image_preview,box=self.crop_box,classification=identification,requires_crop=False,
                    source_crop_size=[coords[2]-coords[0],coords[3]-coords[1]],work_size=list(cropped.size))

    def process(self, enhance='standard', kind='auto', diagnostic=None, color_enhance=False):
        self.color_base=None;self.color_edited=False
        self.base_result=None;self.rotation=0;self.result=None
        if self.original is None:raise ValueError('请先导入图片')
        from time import perf_counter
        import uuid
        started=perf_counter();request=uuid.uuid4().hex[:12]
        def log(stage,**data):
            if diagnostic:diagnostic('color_diagnostic',request=request,stage=stage,elapsed_ms=round((perf_counter()-started)*1000,3),**data)
        # 未框选的大图以完整原图为区域，缓存受控工作图，重复提取不反复解码。
        if isinstance(self.full,LargeSource) and self.crop_box is None and not self.whole_work_ready:
            log('whole_work_begin',source_size=list(self.full.size))
            try:
                work=self.full.crop((0,0,self.full.width,self.full.height))
            except MemoryError as exc:
                log('whole_work_failed',exception_type='MemoryError')
                raise ValueError('原图解码内存不足，请关闭其他程序或先缩小原图') from exc
            self.original=work
            self.whole_work_ready=True
            log('whole_work_ready',work_size=list(work.size))
        work=working_image(self.original)
        identification=classify(display_image(work))
        log('classification',requested=kind,cropped=self.crop_box is not None,width=self.original.width,height=self.original.height,classification=identification)
        if kind not in {'auto','black_signature','color_seal'}:raise ValueError('无效处理类型')
        chosen=identification['type'] if kind=='auto' else kind
        if chosen=='uncertain':
            log('rejected',conditions=['classification_uncertain']);raise ValueError(identification['reason'])
        log('route',chosen=chosen,local_enabled=self.crop_box is not None,work_size=list(work.size),source_crop_size=[self.crop_box[2]-self.crop_box[0],self.crop_box[3]-self.crop_box[1]] if self.crop_box else list(self.full.size))
        # 手动类型只改变路由，空白与随机噪声仍拒绝。
        import cv2
        probe=np.asarray(work.convert('L'))
        edges=cv2.Laplacian(probe,cv2.CV_32F)
        if probe.std()<.5 or (float(np.std(edges))>110 and identification['diagnostics']['density']>.4):
            log('rejected',conditions=['blank_or_noise'],gray_std=float(probe.std()),laplacian_std=float(np.std(edges)))
            raise ValueError('图片为空白或噪声过多，无法可靠提取')
        color=chosen=='color_seal'
        color_report=None
        if color:result,color_report=extract_color(work,local=True,with_report=True)
        else:result=extract(work)
        if color:
            log('extraction',report=color_report)
            validation_started=perf_counter()
            alpha=np.asarray(result)[...,3]
            n,labels,stats,_=cv2.connectedComponentsWithStats((alpha>=2).astype('uint8'),8)
            areas=stats[1:,cv2.CC_STAT_AREA]
            supported=int(areas[areas>=2].sum())
            density=float((alpha>0).mean())
            # 浅笔允许多个短组件共同举证；密集区域仅可信背景可放宽。
            density_limit=.85 if color_report['method']=='local_background' else .65
            failed_conditions=[]
            if n<=1:failed_conditions.append('no_component_alpha_ge2')
            if supported<12:failed_conditions.append('supported_pixels_lt12')
            if density>density_limit:failed_conditions.append('nonzero_density_over_limit')
            log('validation',nonzero_fraction=density,density_limit=density_limit,
                largest_component=int(areas.max()) if areas.size else 0,component_count=n-1,
                supported_pixels=supported,background_residue_rejected=density>density_limit,
                failed_conditions=failed_conditions,validation_ms=round((perf_counter()-validation_started)*1000,3))
            if n<=1 or supported<12 or density>density_limit:
                raise ValueError('未检测到有效彩色主体或背景残留过多，请重新框选')
        if not result.getbbox():raise ValueError('未检测到有效签名笔画，请换图检查')
        if color:
            self.color_base=result
            result,report=enhance_color_ink(result,enabled=color_enhance)
        else:
            result,report=sharpen(result,enabled=enhance)
        if color and color_report.get('quality_warning'):
            report['reason']+='；'+color_report['quality_warning']
        self.result=result;self.base_result=result if color else result.copy()
        log('success',chosen=chosen)
        box=result.getbbox()
        return dict(preview=preview(result),canvas_size=result.size,sharpen=report,content_size=[box[2]-box[0],box[3]-box[1]],color_report=color_report,result_type=chosen)

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
