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
  ready = true;
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
