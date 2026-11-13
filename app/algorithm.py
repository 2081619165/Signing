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
