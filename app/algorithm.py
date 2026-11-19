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


def extract_color_baseline(image):
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


def extract_color(image, local=False, with_report=False):
    """仅可信框选纸张启用局部色差；复杂背景保守回退基线。"""
    from time import perf_counter
    started=perf_counter();baseline=extract_color_baseline(image)
    report=dict(method='baseline',reason='not_cropped',local_requested=bool(local),
                timings_ms=dict(baseline=round((perf_counter()-started)*1000,3)))
    def alpha_stats(result):
        a=np.asarray(result)[...,3]
        return dict(nonzero_fraction=float((a>0).mean()),pixels_ge2=int((a>=2).sum()),
                    alpha_max=int(a.max()),alpha_sum=int(a.sum()))
    report['baseline_alpha']=alpha_stats(baseline)
    def finish(result):
        report['selected_alpha']=alpha_stats(result)
        report['timings_ms']['total']=round((perf_counter()-started)*1000,3)
        return (result,report) if with_report else result
    if not local:return finish(baseline)
    rgb=np.asarray(image.convert('RGB')).astype(np.float32)/255
    h,w=rgb.shape[:2]
    if min(h,w)<16:
        report['reason']='region_too_small';return finish(baseline)
    # 有界采样拟合平滑纸张，迭代剔除偏离纸张模型的印泥，不填补笔画。
    step=max(1,int(np.ceil(np.sqrt(h*w/12000))))
    yy,xx=np.mgrid[0:h:step,0:w:step];x=xx.ravel()/max(w-1,1);y=yy.ravel()/max(h-1,1)
    design=np.column_stack((np.ones_like(x),x,y,x*x,x*y,y*y))
    samples=rgb[::step,::step].reshape(-1,3)
    keep=np.ones(len(samples),bool)
    for _ in range(5):
        coef=np.linalg.lstsq(design[keep],samples[keep],rcond=None)[0]
        residual=np.max(np.abs(samples-design@coef),axis=1)
        keep=residual<=max(.006,float(np.percentile(residual,65)))
    noise=float(np.percentile(residual[keep],90))
    # 纸纹的共同亮度起伏不等于彩色噪声，分开估计背景相对彩度。
    fitted=np.maximum(design@coef,.1)
    sample_relative=np.clip(samples/fitted,0,1)
    sample_chroma=sample_relative.max(1)-sample_relative.min(1)
    color_noise=float(np.percentile(sample_chroma[keep],95))
    noise_ok=noise<=.012 or (noise<=.035 and color_noise<=.008)
    # 纸张证据必须覆盖多数样点及各象限，不能把纹理或大片印泥拟合成背景。
    covered=all(np.count_nonzero(keep&(x>=a)&(x<=b)&(y>=c)&(y<=d))>len(samples)*.06
        for a,b,c,d in ((0,.5,0,.5),(.5,1,0,.5),(0,.5,.5,1),(.5,1,.5,1)))
    report.update(background_noise=noise,background_color_noise=color_noise,background_fraction=float(keep.mean()),quadrants_covered=bool(covered),
                  sample_count=len(samples),confidence_checks=dict(noise_ok=bool(noise_ok),fraction_ok=bool(keep.mean()>=.55),coverage_ok=bool(covered)))
    report['timings_ms']['fit']=round((perf_counter()-started)*1000-report['timings_ms']['baseline'],3)
    # 只对中等噪声开启二次复核，不把所有复杂背景直接放行。
    review_needed=not noise_ok
    review_eligible=noise<=.035 and color_noise<=.025
    report['candidate_review_requested']=bool(review_needed)
    if (review_needed and not review_eligible) or keep.mean()<.55 or not covered:
        report['reason']='background_confidence_failed';return finish(baseline)
    xfull=np.linspace(0,1,w,dtype=np.float32)[None,:,None];yfull=np.linspace(0,1,h,dtype=np.float32)[:,None,None]
    paper=(coef[0]+coef[1]*xfull+coef[2]*yfull+coef[3]*xfull*xfull+coef[4]*xfull*yfull+coef[5]*yfull*yfull).astype(np.float32)
    report.update(paper_min=float(paper.min()),paper_max=float(paper.max()),paper_mean_rgb=paper.mean(axis=(0,1)).tolist())
    if paper.min()<.45 or paper.max()>1.05:
        report['reason']='paper_range_failed';return finish(baseline)
    # 干净近白纸沿用既有效果；仅浅到基线漏检时尝试新分离。
    if np.max(np.abs(paper-1))<.025 and np.asarray(baseline)[...,3].max()>8:
        report['reason']='近白背景保留基线';return finish(baseline)
    relative=np.clip(rgb/np.maximum(paper,.1),0,1)
    chroma=relative.max(2)-relative.min(2)
    floor=max(.004,color_noise*1.5)
    weight=np.clip((chroma-floor)/max(.008,color_noise),0,1)
    report.update(chroma_floor=float(floor),chroma_above_floor_fraction=float((chroma>floor).mean()),weight_nonzero_fraction=float((weight>0).mean()))
    alpha=(1-relative.min(2))*weight
    foreground=np.clip((relative-(1-alpha[...,None]))/np.maximum(alpha[...,None],1e-6),0,1)
    candidate=Image.fromarray(np.dstack((np.round(foreground*255),np.round(alpha*255))).astype('uint8'))
    report['candidate_alpha']=alpha_stats(candidate)
    old=np.asarray(baseline)[...,3];new=np.asarray(candidate)[...,3]
    # 旧Alpha也可能来自偏色纸张；仅有显著相对彩差的像素参与强笔保护。
    strong=(old>=64)&(chroma>max(.03,floor*3))
    report['strong_retention']=float((new[strong]>0).mean()) if strong.any() else None
    if strong.any() and (new[strong]>0).mean()<.98:
        report['reason']='强笔迹保护回退';return finish(baseline)
    if (new>0).mean()>.85:
        report['reason']='candidate_density_failed';return finish(baseline)
    sample_alpha=new[::step,::step].ravel()
    leakage=float((sample_alpha[keep]>2).mean())
    report['background_sample_leakage']=leakage
    if leakage>.15:
        report['reason']='background_sample_leakage_failed';return finish(baseline)
    n,labels,stats,_=cv2.connectedComponentsWithStats((new>=2).astype('uint8'),8)
    largest=int(stats[1:,cv2.CC_STAT_AREA].max()) if n>1 else 0
    report['largest_component']=largest
    if largest<12:
        report['reason']='candidate_subject_failed';return finish(baseline)
    if review_needed:
        # 独立纸边证据和主体结构联合验收；不改Alpha生成或最终密度上限。
        border=np.zeros((h,w),bool);margin=max(1,round(min(h,w)*.035))
        border[:margin]=True;border[-margin:]=True;border[:,:margin]=True;border[:,-margin:]=True
        border_leakage=float((new[border]>0).mean())
        border_residue=border_leakage
        if border_leakage>.02 and leakage<=.01:
            # 贴边圆环可占纸边，但必须有足够的内部连通像素和强笔迹作证。
            subject=labels==1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA]))
            interior=subject&~border
            if interior.sum()*2>=largest and (interior&strong).sum()>=max(12,.1*largest):
                border_residue=float(((new>0)&~subject)[border].mean())
        checks=dict(background_leakage_ok=leakage<=.01,border_ok=border_residue<=.02,
                    density_ok=.005<float((new>0).mean())<=.5,subject_ok=largest>=12,
                    strong_retention_ok=bool(strong.any() and report['strong_retention']>=.98))
        report.update(candidate_review_checks=checks,border_leakage=border_leakage,border_residue=border_residue)
        if not all(checks.values()):
            report['reason']='candidate_review_failed';return finish(baseline)
    if leakage>.02:report['quality_warning']='背景可能有少量残留，请人工检查透明预览'
    report.update(method='local_background',reason='受约束候选复核通过' if review_needed else '可信平滑纸张相对色差')
    return finish(candidate)
