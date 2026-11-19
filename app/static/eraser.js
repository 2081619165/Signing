'use strict';
(()=>{
const resultBox=document.getElementById('resultbg');
const toolbar=document.createElement('div');
toolbar.className='toolbar eraser-tools';
toolbar.hidden=true;
toolbar.innerHTML=`
  <label>笔刷 <input id="eraserSize" type="range" min="1" max="200" value="18"><output id="eraserDiameter">18 px</output></label>
  <button id="eraserUndo" disabled>撤销</button><button id="eraserRedo" disabled>重做</button>
  <button id="eraserMinus" aria-label="缩小">−</button><button id="eraserPlus" aria-label="放大">＋</button>
  <button id="eraserFit">适应</button><button id="eraserFinish" disabled>完成编辑</button><button id="eraserCancel">取消</button>
  <span id="eraserMessage" role="status"></span>`;
resultBox.after(toolbar);
const $=id=>document.getElementById('eraser'+id[0].toUpperCase()+id.slice(1));
const view=document.createElement('div'),canvas=document.createElement('canvas');
const cursor=document.createElement('div');
view.className='eraser-view';view.hidden=true;view.append(canvas);
cursor.className='eraser-cursor';cursor.hidden=true;cursor.setAttribute('aria-hidden','true');
resultBox.append(view,cursor);
const context=canvas.getContext('2d',{willReadFrequently:true});
const baseMask=document.createElement('canvas'),mask=document.createElement('canvas');
const base=baseMask.getContext('2d'),paint=mask.getContext('2d',{willReadFrequently:true});
const source=new Image();
let scale=1,loaded=false,saving=false,stroke=null,history=[],redo=[];
let data=null,pan=null,spaceHeld=false,lastPointer=null;
const api=()=>window.pywebview.api;
const message=text=>{$('message').textContent=text;};

function controls(){
  $('undo').disabled=!loaded||saving||!!stroke||!history.length;
  $('redo').disabled=!loaded||saving||!!stroke||!redo.length;
  $('finish').disabled=!loaded||saving||!!stroke||(!history.length&&!baseMask.hasMarks);
  $('cancel').disabled=saving;
}
function zoom(value){
  scale=Math.max(Math.min(.01,8000/Math.max(data.width,data.height)),Math.min(8,8000/Math.max(data.width,data.height),value));
  canvas.style.width=data.width*scale+'px';canvas.style.height=data.height*scale+'px';
}
function fit(){
  zoom(Math.min(1,(view.clientWidth-28)/data.width,(view.clientHeight-28)/data.height));
  view.scrollLeft=view.scrollTop=0;
}
function overCanvas(event){
  return document.elementFromPoint(event.clientX,event.clientY)===canvas;
}
function showCursor(event){
  lastPointer=event;
  const rect=canvas.getBoundingClientRect(),box=resultBox.getBoundingClientRect();
  cursor.hidden=!loaded||saving||!!pan||spaceHeld||!overCanvas(event);
  const diameter=Number($('size').value)*rect.width/canvas.width;
  Object.assign(cursor.style,{width:diameter+'px',height:diameter+'px',
    left:event.clientX-box.left-resultBox.clientLeft+'px',top:event.clientY-box.top-resultBox.clientTop+'px'});
}
function segment(ctx,a,b,radius){
  ctx.fillStyle='#000';ctx.strokeStyle='#000';ctx.lineWidth=2*radius;ctx.lineCap='round';
  ctx.beginPath();ctx.arc(b[0],b[1],radius,0,2*Math.PI);ctx.fill();
  if(a!==b){ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke();}
}
function replay(ctx,item){
  item.points.forEach((point,index)=>segment(ctx,item.points[Math.max(0,index-1)],point,item.radius));
}
function render(){
  const binary=paint.getImageData(0,0,data.width,data.height);
  for(let i=3;i<binary.data.length;i+=4)binary.data[i]=binary.data[i]>=128?255:0;
  context.globalCompositeOperation='source-over';
  context.putImageData(binary,0,0);
  context.globalCompositeOperation='source-out';
  context.drawImage(source,0,0);
  context.globalCompositeOperation='destination-out';
}
function rebuild(){
  paint.clearRect(0,0,data.width,data.height);paint.drawImage(baseMask,0,0);
  history.forEach(item=>replay(paint,item));render();controls();
}
// 边界框使用浏览器 CSS 坐标，滚动和显示缩放由浏览器统一换算。
function point(event){
  const rect=canvas.getBoundingClientRect();
  return [(event.clientX-rect.left)*canvas.width/rect.width,(event.clientY-rect.top)*canvas.height/rect.height];
}
function extend(event){
  const next=point(event),previous=stroke.points.at(-1)||next;
  stroke.points.push(next);
  segment(paint,previous,next,stroke.radius);
  segment(context,previous,next,stroke.radius);
}
function alphaSum(){
  const rgba=context.getImageData(0,0,data.width,data.height).data;
  let sum=0;
  for(let i=3;i<rgba.length;i+=4)sum+=rgba[i];
  return sum;
}
function stopPan(){
  if(!pan)return;
  const {id}=pan;
  pan=null;canvas.classList.remove('panning');
  if(canvas.hasPointerCapture(id))canvas.releasePointerCapture(id);
}
function setHand(enabled){
  spaceHeld=enabled;
  view.classList.toggle('grab',enabled);
  if(lastPointer)showCursor(lastPointer);
}
const textControl=target=>target instanceof HTMLElement&&
  (target.isContentEditable||!!target.closest('input,textarea,select,[role="textbox"]'));
window.addEventListener('keydown',event=>{
  if(event.code!=='Space'||!loaded||saving||textControl(event.target))return;
  event.preventDefault();
  if(event.repeat)return;
  setHand(true);
  // 正在擦除时按空格，只结算已画笔划，下一次按下才能拖动。
  if(stroke){
    const {id}=stroke;
    end({pointerId:id});
    if(canvas.hasPointerCapture(id))canvas.releasePointerCapture(id);
  }
});
window.addEventListener('keyup',event=>{
  if(event.code!=='Space'||!spaceHeld)return;
  if(pan?.space)stopPan();
  setHand(false);
});
function resetHand(){
  stopPan();lastPointer=null;setHand(false);cursor.hidden=true;
}
window.addEventListener('blur',resetHand);
window.addEventListener('focusin',event=>{if(textControl(event.target)&&spaceHeld)resetHand();});
canvas.onpointerdown=event=>{
  if(!loaded||saving||stroke||pan)return;
  if(event.button===1||(spaceHeld&&event.button===0)){
    event.preventDefault();canvas.setPointerCapture(event.pointerId);
    pan={id:event.pointerId,space:event.button===0,x:event.clientX,y:event.clientY,left:view.scrollLeft,top:view.scrollTop};
    cursor.hidden=true;canvas.classList.add('panning');return;
  }
  if(event.button!==0||spaceHeld)return;
  canvas.setPointerCapture(event.pointerId);
  stroke={id:event.pointerId,radius:Number($('size').value)/2,points:[],before:alphaSum()};
  extend(event);controls();
};
canvas.onpointermove=event=>{
  if(pan?.id===event.pointerId){
    if(!overCanvas(event)){stopPan();showCursor(event);return;}
    view.scrollLeft=pan.left+pan.x-event.clientX;view.scrollTop=pan.top+pan.y-event.clientY;
  }else if(stroke?.id===event.pointerId)extend(event);
  showCursor(event);
};
canvas.onpointerenter=showCursor;
canvas.onpointerleave=()=>{stopPan();lastPointer=null;cursor.hidden=true;};
function end(event){
  if(pan?.id===event.pointerId){
    stopPan();
    if(event.type==='pointerup')showCursor(event);
    else cursor.hidden=true;
  }
  if(stroke?.id!==event.pointerId)return;
  if(event.type==='pointerup')extend(event);
  if(alphaSum()<stroke.before){
    history.push(stroke);redo=[];
    if(history.length>10){replay(base,history.shift());baseMask.hasMarks=true;}
  }
  stroke=null;rebuild();
}
canvas.onpointerup=canvas.onpointercancel=canvas.onlostpointercapture=end;
$('undo').onclick=()=>{if(history.length){redo.push(history.pop());rebuild();}};
$('redo').onclick=()=>{if(redo.length){history.push(redo.pop());rebuild();}};
$('plus').onclick=()=>{if(loaded&&!stroke&&!saving)zoom(scale*1.25);};
$('minus').onclick=()=>{if(loaded&&!stroke&&!saving)zoom(scale/1.25);};
$('fit').onclick=()=>{if(loaded&&!stroke&&!saving)fit();};
$('size').oninput=()=>{$('diameter').value=$('size').value+' px';};
view.addEventListener('wheel',event=>{
  if(!loaded)return;
  event.preventDefault();
  if(stroke||saving||pan)return;
  if(spaceHeld||event.shiftKey){
    // Chromium 可能把 Shift 滚轮转换成 deltaX；统一换算为 CSS 像素。
    const horizontal=!spaceHeld;
    const delta=horizontal?(event.deltaX||event.deltaY):(event.deltaY||event.deltaX);
    const unit=event.deltaMode===1?16:event.deltaMode===2?(horizontal?view.clientWidth:view.clientHeight):1;
    if(horizontal)view.scrollLeft+=delta*unit;
    else view.scrollTop+=delta*unit;
    showCursor(event);
    return;
  }
  const [x,y]=point(event);
  zoom(scale*(event.deltaY<0?1.15:1/1.15));
  const rect=canvas.getBoundingClientRect();
  view.scrollLeft+=rect.left+x*rect.width/canvas.width-event.clientX;
  view.scrollTop+=rect.top+y*rect.height/canvas.height-event.clientY;
  showCursor(event);
},{passive:false});

function leave(){
  resetHand();
  loaded=false;saving=false;stroke=null;data=null;history=[];redo=[];
  baseMask.hasMarks=false;
  for(const layer of [canvas,baseMask,mask]){layer.width=0;layer.height=0;}
  source.removeAttribute('src');
  toolbar.hidden=view.hidden=cursor.hidden=true;
  processed.hidden=false;editingResult=false;busy=false;updateControls();
}
async function cancel(){
  if(!editingResult||saving)return;
  const token=data?.token;
  saving=true;controls();
  try{
    if(token)check(await api().cancel_erasure(token));
  }finally{leave();}
}
$('cancel').onclick=()=>cancel().catch(e=>{workstatus.textContent='橡皮擦取消失败：'+String(e);});

$('finish').onclick=async()=>{
  if($('finish').disabled)return;
  saving=true;controls();message('正在提交…');
  try{
    const alpha=paint.getImageData(0,0,data.width,data.height).data;
    const remaining=context.getImageData(0,0,data.width,data.height).data;
    const packed=new Uint8Array(Math.ceil(data.width*data.height/8));
    let hasInk=false;
    for(let i=0;i<data.width*data.height;i++){
      if(alpha[i*4+3]>=128)packed[i>>3]|=1<<(i&7);
      else if(remaining[i*4+3])hasInk=true;
    }
    if(!hasInk)throw new Error('请保留有效笔迹，可撤销后再完成编辑。');
    for(let offset=0;offset<packed.length;offset+=48*1024){
      const chunk=packed.subarray(offset,offset+48*1024);
      check(await api().eraser_mask_chunk(data.token,offset,btoa(String.fromCharCode(...chunk))));
    }
    const reply=check(await api().finish_erasure(data.token));
    leave();applyEditedResult(reply);
  }catch(e){message(String(e));saving=false;controls();}
};

eraserButton.onclick=async()=>{
  if(!ready||busy||!hasResult)return;
  editingResult=true;busy=true;saving=true;updateControls();controls();
  toolbar.hidden=false;message('正在载入透明图像…');
  try{
    data=check(await api().begin_erasure());
    const parts=[];
    for(let offset=0;offset<data.total;){
      const part=check(await api().eraser_image_chunk(data.token,offset));
      if(!part.chunk||data.total<offset+part.chunk.length)throw new Error('无效图像分块');
      parts.push(part.chunk);offset+=part.chunk.length;
    }
    source.src='data:image/png;base64,'+parts.join('');
    await source.decode();
    if(source.naturalWidth!==data.width||source.naturalHeight!==data.height)throw new Error('图像尺寸不符');
    for(const layer of [canvas,baseMask,mask]){layer.width=data.width;layer.height=data.height;}
    loaded=true;saving=false;processed.hidden=true;view.hidden=false;fit();rebuild();
    message('空格＋拖动或滚轮：平移 · Shift＋滚轮：横移 · Ctrl＋滚轮：缩放');
  }catch(e){
    saving=false;
    try{await cancel();}
    finally{workstatus.textContent='橡皮擦载入失败：'+String(e);}
  }
};
})();
