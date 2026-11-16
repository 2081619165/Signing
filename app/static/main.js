'use strict';
const jsStart = performance.now();
const status = document.getElementById('status');
const result = document.getElementById('result');
const ping = document.getElementById('ping');
const marker = document.getElementById('marker');
let ready = false;
async function report(name, data) {
  if (ready) return window.pywebview.api.page_event(name, data);
}
window.addEventListener('error', e => { result.textContent = 'JS 错误：' + e.message; report('js_error', {message:e.message}).catch(console.error); });
window.addEventListener('unhandledrejection', e => { result.textContent = '通信错误：' + String(e.reason); });
window.addEventListener('pywebviewready', async () => {
  ready = true; updateControls();
  status.textContent = 'Python 桥接已就绪'; ping.disabled = false; marker.disabled = false;
  await report('js_ready', {script_start_ms:jsStart, bridge_ready_ms:performance.now(), script_to_bridge_ms:performance.now()-jsStart, user_agent:navigator.userAgent});
  result.textContent = '页面与桥接已初始化；点击按钮测量通信往返。';
});
setTimeout(() => { if (!ready) status.textContent = '桥接等待超过10秒，请查看Python控制台和日志'; }, 10000);
ping.addEventListener('click', async () => {
  ping.disabled = true;
  try {
    const t = performance.now(); const reply = await window.pywebview.api.ping(); const rtt = performance.now()-t;
    result.textContent = `Python 响应成功\nJS→Python→JS 往返：${rtt.toFixed(3)} ms\nPython事件：${reply.event}`;
    await report('bridge_rtt', {rtt_ms:rtt});
  } catch(e) { result.textContent = '通信失败：' + String(e); }
  finally { ping.disabled = false; }
});
marker.addEventListener('click', () => report('manual_marker', {at_ms:performance.now(), note:'用户点击观察点；不是自动视觉通过证明'}).catch(console.error));
document.addEventListener('visibilitychange', () => report('visibility', {state:document.visibilityState, at_ms:performance.now()}).catch(console.error));

const openButton=document.getElementById('open'), processButton=document.getElementById('process');
const exportButton=document.getElementById('export');
const original=document.getElementById('original'),processed=document.getElementById('processed');
const workstatus=document.getElementById('workstatus');
let busy=false,hasInput=false,hasResult=false;
function updateControls(){
  document.getElementById('crop').disabled=!ready||busy||!hasInput;
  openButton.disabled=!ready||busy;processButton.disabled=!ready||busy||!hasInput;
  exportButton.disabled=!ready||busy||!hasResult||!sizeValid;
  document.querySelectorAll('.export-settings input,.export-settings select').forEach(e=>e.disabled=busy);
  document.getElementById('enhance').disabled=busy;
}
function clearResult(){hasResult=false;processed.removeAttribute('src');document.getElementById('exportstatus').textContent='未导出';sizeValid=false;sizeVersion++;document.getElementById('estimated').textContent='处理图片后计算预计输出像素';}
async function task(action){
 if(busy||!ready)return;
 busy=true;updateControls();
 try{await action();}catch(e){workstatus.textContent='失败：'+String(e);}
 finally{busy=false;updateControls();}
}
function check(reply){if(!reply.ok)throw new Error(reply.error);return reply;}
function accept(reply){check(reply);if(reply.cancelled)return;clearResult();hasInput=true;original.src=reply.preview;document.getElementById('filename').textContent=reply.name;document.getElementById('filename').title=reply.name;workstatus.textContent='已导入：'+reply.name;}
openButton.addEventListener('click',()=>task(async()=>{
 clearResult();hasInput=false;original.removeAttribute('src');document.getElementById('filename').textContent='未导入图片';workstatus.textContent='选择图片…';
 const reply=await window.pywebview.api.choose_image();accept(reply);
 if(reply.cancelled)workstatus.textContent='已取消，请重新导入';
}));
processButton.addEventListener('click',()=>task(async()=>{
 clearResult();workstatus.textContent='正在提取，请稍候…';
 const r=check(await window.pywebview.api.process_image(document.getElementById('enhance').checked));
 processed.src=r.preview;hasResult=true;contentRatio=r.content_size[0]/r.content_size[1];if(preset.value.startsWith('signature'))applyPreset();scheduleEstimate();workstatus.textContent='处理完成，可导出。锐化：'+r.sharpen.reason;
}));
exportButton.addEventListener('click',()=>task(async()=>{
 const label=document.getElementById('exportstatus');label.textContent='等待保存…';
 try{const r=check(await window.pywebview.api.export_image(document.getElementById('format').value,settings()));label.textContent=r.cancelled?'已取消':('成功：'+r.size.join('×')+' px；'+(r.format==='gif'?'GIF无可靠DPI元数据，其他软件可能显示72 DPI；不改变像素':('PNG DPI：'+r.dpi[0].toFixed(3))));}
 catch(e){label.textContent='失败：'+String(e);throw e;}
}));
document.getElementById('white').addEventListener('change',e=>document.getElementById('resultbg').classList.toggle('checker',!e.target.checked));
// 用FileReader读取拖入内容，避免依赖浏览器隐藏的本地路径。
for(const name of ['dragover','drop'])document.addEventListener(name,e=>e.preventDefault());
openButton.addEventListener('drop',e=>{
 const files=e.dataTransfer.files;
 task(async()=>{
  clearResult();hasInput=false;original.removeAttribute('src');document.getElementById('filename').textContent='未导入图片';
  if(files.length!==1)throw new Error('请每次拖入一张图片');
  const file=files[0];if(file.size>30*1024*1024)throw new Error('图片超过30MB');
  workstatus.textContent='正在导入…';
  const encoded=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=()=>reject(new Error('读取失败'));reader.readAsDataURL(file);});
  accept(await window.pywebview.api.import_image(file.name,encoded));
 });
});

const preset=document.getElementById('preset'),unit=document.getElementById('unit');
const widthInput=document.getElementById('width'),heightInput=document.getElementById('height'),dpiInput=document.getElementById('dpi');
let contentRatio=1,sizeValid=false,sizeVersion=0,estimateTimer;
// 显示保留三位小数；真实数值独立保存，避免单位切换损失精度。
const exact=new Map();
const numeric=el=>exact.has(el)?exact.get(el):Number(el.value);
const setNumber=(el,n)=>{exact.set(el,n);el.value=Number(n.toFixed(3));};
function settings(){return {unit:unit.value,width:numeric(widthInput),height:numeric(heightInput),dpi:dpiInput.value};}
function applyPreset(){
 const sizes={signature:[1.1*contentRatio,1.1],signature09:[.9*contentRatio,.9],legal:[1.6,1.6],builder:[4,2.8],official:[4,4]};
 if(!sizes[preset.value])return;
 const f=unit.value==='cm'?1:Number(dpiInput.value)/2.54;
 setNumber(widthInput,sizes[preset.value][0]*f);setNumber(heightInput,sizes[preset.value][1]*f);
 document.getElementById('ratio').checked=true;
}
function scheduleEstimate(){
 sizeValid=false;const version=++sizeVersion;clearTimeout(estimateTimer);
 if(!hasResult)return;
 document.getElementById('estimated').textContent='正在计算…';updateControls();
 estimateTimer=setTimeout(async()=>{
  try{const r=check(await window.pywebview.api.estimate_size(settings()));if(version!==sizeVersion)return;sizeValid=true;document.getElementById('estimated').textContent='预计输出：'+r.size.join(' × ')+' px；按所选DPI折算 '+r.cm.map(n=>n.toFixed(4)).join(' × ')+' cm（像素取整有微小误差）'+(document.getElementById('format').value==='gif'?'；GIF无可靠DPI元数据，以像素为准':'');}
  catch(e){if(version!==sizeVersion)return;document.getElementById('estimated').textContent='尺寸无效：'+String(e);}
  updateControls();
 },180);
}
preset.addEventListener('change',()=>{applyPreset();scheduleEstimate();});
unit.addEventListener('change',()=>{
 const f=unit.value==='px'?Number(dpiInput.value)/2.54:2.54/Number(dpiInput.value);
 for(const el of [widthInput,heightInput])if(numeric(el)>0)setNumber(el,numeric(el)*f);
 scheduleEstimate();
});
for(const el of [widthInput,heightInput])el.addEventListener('input',()=>{
 exact.delete(el);preset.value='custom';
 if(document.getElementById('ratio').checked&&Number(el.value)>0){
  if(el===widthInput)setNumber(heightInput,Number(el.value)/contentRatio);
  else setNumber(widthInput,Number(el.value)*contentRatio);
 }
 scheduleEstimate();
});
document.getElementById('ratio').addEventListener('change',e=>{if(e.target.checked){preset.value='custom';setNumber(heightInput,numeric(widthInput)/contentRatio);}scheduleEstimate();});
dpiInput.addEventListener('input',()=>{scheduleEstimate();});
document.getElementById('format').addEventListener('change',()=>{document.getElementById('exportstatus').textContent='未导出';scheduleEstimate();});

// 取消弹窗不触碰现有结果；确认后清空旧导出状态。
document.getElementById('crop').addEventListener('click',()=>task(async()=>{const r=check(await window.pywebview.api.select_region());if(r.cancelled)return;original.src=r.preview;clearResult();workstatus.textContent='已框选，请点击提取黑色签名';}));
