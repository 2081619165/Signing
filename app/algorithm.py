"""复用Signing V1核心；上游show7来源及许可见licenses/show7-MIT.txt。"""
import cv2
import numpy as np
from PIL import Image

def extract(image):
    # 与实验版一致，输入为内存RGB，输出原尺寸连续Alpha。
    img=cv2.cvtColor(np.asarray(image.convert('RGB')),cv2.COLOR_RGB2BGR)
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
    return Image.fromarray(rgba)


def classify(image):
    """只统计有效局部墨迹；启发式无法区分所有文字/签名。"""
    rgb=np.asarray(image.convert('RGB'));gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
    k=max(31,int(min(gray.shape)*.08)|1)
    bg=cv2.morphologyEx(gray,cv2.MORPH_CLOSE,np.ones((k,k),np.uint8))
    hsv=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV)
    colored=(hsv[...,1]>=32)&((rgb.max(2).astype(float)-rgb.min(2))>=10)
    ink=((bg.astype(float)-gray)>3)|colored
    count=int(ink.sum());reason='颜色或内容不足，请先框选签名或印章区域'
    kind='uncertain';fraction=float(colored[ink].mean()) if count else 0
    n,_,stats,_=cv2.connectedComponentsWithStats(ink.astype('uint8'),8)
    parts=int((stats[1:,cv2.CC_STAT_AREA]>=4).sum())
    # 整页纵向分布、多块文字、彩色与黑色混合均保守拒绝。
    ys,xs=np.where(ink)
    page=count and image.height>image.width*1.15 and (ys.max()-ys.min())>image.height*.55
    rows=ink.sum(1)>max(2,image.width*.005)
    bands=int(np.count_nonzero(np.diff(np.pad(rows.astype(int),(1,1)))==1))
    if count>=8 and count/ink.size<.55 and not page and parts<30 and bands<=5:
        if fraction>=.9:kind='color_seal';reason='检测到以彩色墨迹为主的区域'
        elif fraction<=.03:kind='black_signature';reason='检测到以中性墨迹为主的区域'
        else:reason='检测到混合内容，请先框选'
    # 彩色主体独立判断，不让中性灰底或少量长横线稀释全部证据。
    cn,_,cs,_=cv2.connectedComponentsWithStats(colored.astype('uint8'),8)
    color_count=int(colored.sum());largest=int(cs[1:,cv2.CC_STAT_AREA].max()) if cn>1 else 0
    cy,cx=np.where(colored)
    compact=color_count>=16 and largest>=12 and color_count/ink.size<.5
    color_page=bool(color_count and image.height>image.width*1.15 and cy.max()-cy.min()>image.height*.8)
    neutral=ink&~colored
    nn,_,ns,_=cv2.connectedComponentsWithStats(neutral.astype('uint8'),8)
    neutral_parts=ns[1:]
    # 允许最多两条水平辅助线；大量黑字仍要求框选。
    meaningful=neutral_parts[neutral_parts[:,cv2.CC_STAT_AREA]>=8]
    lines=sum(1 for part in meaningful if part[cv2.CC_STAT_WIDTH]>=part[cv2.CC_STAT_HEIGHT]*8)
    mostly_lines=len(meaningful)<=2 and lines==len(meaningful)
    color_rows=colored.sum(1)>max(1,image.width*.002)
    color_bands=int(np.count_nonzero(np.diff(np.pad(color_rows.astype(int),(1,1)))==1))
    if compact and not color_page and color_bands<=12 and (fraction>=.5 or mostly_lines):
        kind='color_seal';reason='检测到连贯彩色主体（允许有限灰黑横线）'
    if kind=='uncertain' and reason.startswith('颜色或内容不足'):
        reason='有效区域不足或结构复杂，请框选或手动指定类型'
    return dict(type=kind,reason=reason,color_fraction=fraction,components=parts,
                diagnostics=dict(ink_pixels=count,color_pixels=color_count,largest_color_component=largest,
                    density=count/ink.size,bands=bands,page=bool(page),color_bands=color_bands,
                    compact=bool(compact),color_page=color_page,neutral_components=len(meaningful),
                    mostly_lines=mostly_lines,color_fraction_pass=fraction>=.5))


def extract_color(image):
    """白纸模型分离彩墨，反算前景色以避免白边；不调用黑签提取。"""
    rgb=np.asarray(image.convert('RGB')).astype(np.float32)/255
    chroma=rgb.max(2)-rgb.min(2)
    # 按局部像素最大通道归一化中性灰底，彩度决定透明度。
    normalized=rgb/np.maximum(rgb.max(2)[...,None],1e-6)
    # 蓝色主导像素保留原亮度，避免逐像素白化使蓝色内文变淡；红色路径保持。
    blue=(rgb[...,2]>rgb[...,0]+.03)&(rgb[...,2]>rgb[...,1]+.03)
    normalized=np.where(blue[...,None],rgb,normalized)
    alpha=np.where(chroma>.025,1-normalized.min(2),0)
    rgb=normalized
    foreground=np.clip((rgb-(1-alpha[...,None]))/np.maximum(alpha[...,None],1e-6),0,1)
    return Image.fromarray(np.dstack((np.round(foreground*255),np.round(alpha*255))).astype('uint8'))
