"""黑色签名 Alpha 自然增强；不改变灰底提取器。"""
import cv2
import numpy as np
from PIL import Image

def _structure(a):
    masks=[a>=t for t in (16,32,64,128,192)]
    return masks

def sharpen(image, enabled=True):
    rgba=np.asarray(image.convert('RGBA')).copy();a=rgba[...,3].astype(np.float32)/255
    report={'enabled':enabled,'applied':False,'fallback':False}
    if not enabled or not np.any(a):
        report['reason']='disabled_or_empty';return image.copy(),report
    peak=float(np.percentile(a[a>0],95));mask=(a>peak*.5).astype('uint8')
    dist=cv2.distanceTransform(mask,cv2.DIST_L2,3)
    width=float(2*np.median(dist[mask>0])) if mask.any() else 0
    gx=cv2.Sobel(a,cv2.CV_32F,1,0,ksize=3)/8;gy=cv2.Sobel(a,cv2.CV_32F,0,1,ksize=3)/8
    edge=np.hypot(gx,gy);active=edge>peak*.05
    sharpness=float(np.median(edge[active])/max(peak,.001)) if active.any() else 0
    n,labels,stats,_=cv2.connectedComponentsWithStats((a>0).astype('uint8'),8)
    tiny=np.isin(labels,np.where(stats[:,cv2.CC_STAT_AREA]<=3)[0]);noise=float(a[tiny].sum()/max(a.sum(),.001))
    report.update(width_px=width,edge_score=sharpness,noise_fraction=noise)
    # 经验筛选只决定是否尝试；最终以结构不变量验收，不宣称能恢复细节。
    if sharpness>=.22 or sharpness<.045 or noise>.02:
        report['reason']='clear_severe_blur_or_noise';return image.copy(),report
    strength=.08 if width<3 else .16
    blurred=cv2.GaussianBlur(a,(0,0),.65)
    candidate=np.clip(a+strength*(a-blurred),0,1)
    candidate[(a==0)|tiny]=a[(a==0)|tiny]
    b=np.round(candidate*255).astype('uint8');old=rgba[...,3].copy()
    # 将增强限制在原Alpha等值区间内，候选越界仍由后续检查回退。
    # 多级等值线像素集合严格相同：防止增粗、断裂、粘连及新连通噪点。
    invariant=all(np.array_equal(x,y) for x,y in zip(_structure(old),_structure(b)))
    mass_change=abs(float(b.sum())-float(old.sum()))/max(float(old.sum()),1)
    report.update(strength=strength,structure_equal=invariant,mass_change=mass_change)
    if not invariant or mass_change>.01:
        report.update(fallback=True,reason='structure_or_ink_mass_changed');return image.copy(),report
    rgba[...,3]=b;report.update(applied=bool(np.any(b!=old)),reason='accepted')
    return Image.fromarray(rgba),report
