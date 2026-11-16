'use strict';
// 选框始终保存原图坐标，显示比例只参与鼠标映射。
const $=id=>document.getElementById(id),stage=$('stage'),box=$('box');
let scale=1,selection=data.box,drag=null;
// 平移以画布CSS像素保存，绝不修改选区原图坐标。
const view=$('view');let offsetX=0,offsetY=0,space=false,pan=null;
$('image').src=data.src;
function draw(){stage.style.left=offsetX+'px';stage.style.top=offsetY+'px';stage.style.width=data.width*scale+'px';stage.style.height=data.height*scale+'px';box.hidden=!selection;if(selection){const [x,y,r,b]=selection;Object.assign(box.style,{left:x*scale+'px',top:y*scale+'px',width:(r-x)*scale+'px',height:(b-y)*scale+'px'});$('info').textContent=`${Math.ceil(r)-Math.floor(x)} × ${Math.ceil(b)-Math.floor(y)} px`;}$('confirm').disabled=!selection||selection[2]-selection[0]<4||selection[3]-selection[1]<4;}
function fit(){stop();scale=Math.max(.0001,Math.min((view.clientWidth-24)/data.width,(view.clientHeight-24)/data.height));offsetX=(view.clientWidth-data.width*scale)/2;offsetY=(view.clientHeight-data.height*scale)/2;draw();}
function point(e){const r=stage.getBoundingClientRect();return [Math.max(0,Math.min(data.width,(e.clientX-r.left)/scale)),Math.max(0,Math.min(data.height,(e.clientY-r.top)/scale))];}
stage.onpointerdown=e=>{if(e.button!==0||space)return;e.preventDefault();stage.setPointerCapture(e.pointerId);drag={start:point(e),old:selection&&selection.slice(),mode:e.target.dataset.corner!==undefined?Number(e.target.dataset.corner):(e.target===box?'move':'new')};if(drag.mode==='new')selection=[...drag.start,...drag.start];draw();};
stage.onpointermove=e=>{if(!drag)return;const p=point(e),o=drag.old;let a,b;if(drag.mode==='move'){const dx=Math.max(-o[0],Math.min(data.width-o[2],p[0]-drag.start[0])),dy=Math.max(-o[1],Math.min(data.height-o[3],p[1]-drag.start[1]));selection=[o[0]+dx,o[1]+dy,o[2]+dx,o[3]+dy];}else{a=drag.mode==='new'?drag.start:[[o[2],o[3]],[o[0],o[3]],[o[0],o[1]],[o[2],o[1]]][drag.mode];b=p;selection=[Math.min(a[0],b[0]),Math.min(a[1],b[1]),Math.max(a[0],b[0]),Math.max(a[1],b[1])];}draw();};
stage.onpointerup=stage.onpointercancel=()=>{drag=null;};
// 以鼠标锚点反算新的平移量，缩放前后锚点对应同一原图像素。
function zoom(factor,x=view.clientWidth/2,y=view.clientHeight/2){
 if(drag||pan)return;
 const next=Math.max(.0001,Math.min(8,scale*factor)),ratio=next/scale;
 offsetX=x-(x-offsetX)*ratio;offsetY=y-(y-offsetY)*ratio;scale=next;draw();
}
function stop(){drag=null;pan=null;view.classList.remove('panning');}
function clearHand(){space=false;stop();view.classList.remove('hand');}
window.addEventListener('keydown',e=>{if(e.code==='Space'){e.preventDefault();space=true;view.classList.add('hand');}});
window.addEventListener('keyup',e=>{if(e.code==='Space'){e.preventDefault();clearHand();}});
window.addEventListener('blur',clearHand);
document.addEventListener('visibilitychange',()=>{if(document.hidden)clearHand();});
view.addEventListener('pointerdown',e=>{
 if(!space||e.button!==0)return;e.preventDefault();drag=null;
 view.setPointerCapture(e.pointerId);pan={x:e.clientX,y:e.clientY,ox:offsetX,oy:offsetY};view.classList.add('panning');
},true);
view.addEventListener('pointermove',e=>{if(!pan)return;offsetX=pan.ox+e.clientX-pan.x;offsetY=pan.oy+e.clientY-pan.y;draw();});
view.addEventListener('pointerup',stop);view.addEventListener('pointercancel',clearHand);view.addEventListener('lostpointercapture',stop);
view.addEventListener('pointerleave',clearHand);
// 必须非passive，阻止WebView页面缩放，仅缩放图片。
document.addEventListener('wheel',e=>{if(!e.ctrlKey)return;e.preventDefault();if(!view.contains(e.target))return;const r=view.getBoundingClientRect();zoom(Math.exp(-e.deltaY*.002),e.clientX-r.left,e.clientY-r.top);},{passive:false});
$('fit').onclick=fit;$('plus').onclick=()=>zoom(1.25);$('minus').onclick=()=>zoom(1/1.25);$('reset').onclick=()=>{selection=null;draw();};
$('cancel').onclick=()=>window.pywebview.api.cancel();
$('confirm').onclick=async()=>{if($('confirm').disabled)return;$('confirm').disabled=true;try{await window.pywebview.api.confirm(selection);}catch(e){$('message').textContent=String(e);draw();}};
window.addEventListener('resize',draw);requestAnimationFrame(fit);
