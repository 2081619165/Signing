"""沿用 show7 平场提取思路；来源和 MIT 声明见 licenses/show7-MIT.txt。
对照版本 f7da5df17bda46a56bf588baa78843baa5b8779a，原实现保留于 .local-tests。
"""
import cv2
import numpy as np
from PIL import Image, ImageOps

def extract(src, out, target_size=(400, 200)):
    img=cv2.imdecode(np.fromfile(str(src),dtype=np.uint8),cv2.IMREAD_COLOR)
    if img is None: raise ValueError('无法读取图片')
    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY).astype(np.float32)
    k=max(31,int(min(gray.shape)*.08)|1)
    # 闭运算仅估计纸张背景，不对笔画做腐蚀或补画。
    padded=cv2.copyMakeBorder(gray,k,k,k,k,cv2.BORDER_REPLICATE)
    background=cv2.morphologyEx(padded,cv2.MORPH_CLOSE,np.ones((k,k),np.uint8))[k:-k,k:-k]
    contrast=np.clip((background-gray)/np.maximum(background,1),0,1)
    med=float(np.median(contrast)); noise=float(np.median(np.abs(contrast-med))*1.4826)
    threshold=max(.012,med+4*noise)
    keep=contrast>threshold
    # 只删孤立单点，保留狭长细线；不连接原本分离的笔画。
    n,labels,stats,_=cv2.connectedComponentsWithStats(keep.astype('uint8'),8)
    valid=np.zeros(n,bool);valid[1:]=stats[1:,cv2.CC_STAT_AREA]>=2
    alpha=np.where(valid[labels],contrast,0)
    rgba=np.zeros((*gray.shape,4),np.uint8);rgba[...,3]=np.round(alpha*255).astype('uint8')
    native=Image.fromarray(rgba);native.save(out.with_name(out.stem+'_native.png'))
    bbox=native.getbbox()
    canvas=Image.new('RGBA',target_size)
    if bbox:
        content=ImageOps.contain(native.crop(bbox),target_size,Image.Resampling.LANCZOS)
        canvas.alpha_composite(content,((target_size[0]-content.width)//2,(target_size[1]-content.height)//2))
    canvas.save(out)
    return dict(threshold=threshold,noise=noise,bbox=bbox,blank=bbox is None)

