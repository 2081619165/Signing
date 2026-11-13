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
const pngButton=document.getElementById('png'),gifButton=document.getElementById('gif');
const original=document.getElementById('original'),processed=document.getElementById('processed');
const workstatus=document.getElementById('workstatus');
let busy=false,hasInput=false,hasResult=false;
function updateControls(){
  openButton.disabled=!ready||busy;processButton.disabled=!ready||busy||!hasInput;
  pngButton.disabled=!ready||busy||!hasResult;gifButton.disabled=pngButton.disabled;
  document.getElementById('enhance').disabled=busy;
}
function clearResult(){hasResult=false;processed.removeAttribute('src');document.getElementById('pngstatus').textContent='未导出';document.getElementById('gifstatus').textContent='未导出';}
async function task(action){
 if(busy||!ready)return;
 busy=true;updateControls();
 try{await action();}catch(e){workstatus.textContent='失败：'+String(e);}
 finally{busy=false;updateControls();}
}
function check(reply){if(!reply.ok)throw new Error(reply.error);return reply;}
function accept(reply){check(reply);if(reply.cancelled)return;clearResult();hasInput=true;original.src=reply.preview;workstatus.textContent='已导入：'+reply.name;}
openButton.addEventListener('click',()=>task(async()=>{
 clearResult();hasInput=false;original.removeAttribute('src');workstatus.textContent='选择图片…';
 const reply=await window.pywebview.api.choose_image();accept(reply);
 if(reply.cancelled)workstatus.textContent='已取消，请重新导入';
}));
processButton.addEventListener('click',()=>task(async()=>{
 clearResult();workstatus.textContent='正在提取，请稍候…';
 const r=check(await window.pywebview.api.process_image(document.getElementById('enhance').checked));
 processed.src=r.preview;hasResult=true;workstatus.textContent='处理完成，可导出。锐化：'+r.sharpen.reason;
}));
for(const kind of ['png','gif'])document.getElementById(kind).addEventListener('click',()=>task(async()=>{
 const label=document.getElementById(kind+'status');label.textContent='等待保存…';
 try{const r=check(await window.pywebview.api.export_image(kind));label.textContent=r.cancelled?'已取消':('成功：'+r.size.join('×')+' px');}
 catch(e){label.textContent='失败：'+String(e);throw e;}
}));
document.getElementById('white').addEventListener('change',e=>document.getElementById('resultbg').classList.toggle('checker',!e.target.checked));
// 用FileReader读取拖入内容，避免依赖浏览器隐藏的本地路径。
for(const name of ['dragover','drop'])document.addEventListener(name,e=>e.preventDefault());
document.getElementById('dropzone').addEventListener('drop',e=>{
 const files=e.dataTransfer.files;
 task(async()=>{
  clearResult();hasInput=false;original.removeAttribute('src');
  if(files.length!==1)throw new Error('请每次拖入一张图片');
  const file=files[0];if(file.size>30*1024*1024)throw new Error('图片超过30MB');
  workstatus.textContent='正在导入…';
  const encoded=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=()=>reject(new Error('读取失败'));reader.readAsDataURL(file);});
  accept(await window.pywebview.api.import_image(file.name,encoded));
 });
});
