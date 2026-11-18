"""框选窗口：小预览桥接加载，坐标仍属于完整原图。"""
import base64
import io
import json
import threading
import traceback
import uuid
from time import perf_counter
from pathlib import Path
from PIL import Image

_active=None
_active_lock=threading.Lock()
_opening=threading.Lock()
_requests={}
_shutdown=threading.Event()


def close_native(window,record):
    """不等待shown事件；通过UI消息正常Close，避免隐藏窗destroy等待。"""
    try:
        form=getattr(window,'native',None)
        if form is None:
            record('cleanup_native_pending')
            if not getattr(window,'_crop_cleanup_hook',False):
                window._crop_cleanup_hook=True
                window.events.before_show+=lambda *args:close_native(window,record)
                if getattr(window,'native',None) is not None:close_native(window,record)
            return
        from System import Action
        def close():
            if not form.IsDisposed:form.Close()
            record('cleanup_close_returned')
        record('cleanup_close_requested')
        if form.InvokeRequired:form.BeginInvoke(Action(close))
        else:close()
    except Exception as exc:record('cleanup_error',exception_type=type(exc).__name__,traceback=traceback.format_exc())


def shutdown(diag=None):
    # 关闭主窗必须同时唤醒所有桥接等待，不等待线程join或强杀进程。
    _shutdown.set()
    with _active_lock:requests=list(_requests.values())
    if diag:diag.record('crop_shutdown_begin',pending=len(requests))
    for cancel in requests:cancel()


def activate_existing():
    from .placement import activate
    with _active_lock:window=_active
    if window is not None:
        activate(window);return True
    return _opening.locked()


def preview_payload(image):
    # 不复制整张原图做PNG；只缩放显示副本，原图由Session保留用于裁切。
    scale=min(1,1600/max(image.size))
    size=tuple(max(1,round(n*scale)) for n in image.size)
    small=image.resize(size,Image.Resampling.LANCZOS) if size!=image.size else image
    stream=io.BytesIO();small.save(stream,format='PNG')
    return base64.b64encode(stream.getvalue()).decode('ascii'),size,len(stream.getvalue())


def select(image,box,parent,diag=None,timeout=45,request_id=None,validate=None):
    import webview
    global _active
    if _shutdown.is_set():raise ValueError('程序正在退出')
    if not _opening.acquire(blocking=False):raise ValueError('框选窗口正在打开，请稍候')
    request=request_id or uuid.uuid4().hex[:12];started=perf_counter()
    done=threading.Event();ready=threading.Event();aborted=threading.Event()
    state={'window':None,'error':None,'stage':'request','result':None,'displayed':False,'decoded':False}
    def record(event,**data):
        if diag:diag.record('crop_'+event,request=request,elapsed_ms=round((perf_counter()-started)*1000,3),**data)
    def stage(name,**data):state['stage']=name;record(name,**data)
    def cleanup(window):close_native(window,record)
    def cancel_request():
        aborted.set();state['result']=None;done.set();ready.set()
        record('parent_shutdown',stage=state['stage'])
        window=state['window']
        if window is not None:cleanup(window)
        # create_window可能尚未返回，但已加入PyWebView窗口表。
        for pending in list(webview.windows):
            if getattr(pending,'js_api',None) is state.get('api') and pending is not window:cleanup(pending)
    with _active_lock:_requests[request]=cancel_request
    if _shutdown.is_set():cancel_request()
    def fail(message):state['error']=message;ready.set()
    def prepare():
        global _active
        try:
            stage('preview_begin',width=image.width,height=image.height)
            encoded,size,png_bytes=preview_payload(image)
            stage('preview_encoded',preview_width=size[0],preview_height=size[1],png_bytes=png_bytes,base64_chars=len(encoded))
            if aborted.is_set():return
            class API:
                def cancel(self):
                    record('cancel_requested');state['window'].destroy()
                def confirm(self,coords):
                    if not ready.is_set() or state['error']:raise ValueError('图片尚未加载')
                    # 先验证再关闭；被拒的选区允许在原窗口继续调整。
                    if validate:
                        try:validate(coords)
                        except Exception as exc:
                            record('selection_rejected',exception_type=type(exc).__name__,reason=str(exc))
                            raise
                    record('selection_validated')
                    record('confirm_requested')
                    state['result']=coords;state['window'].destroy()
                def image_chunk(self,offset):
                    if aborted.is_set():raise ValueError('加载已取消')
                    if isinstance(offset,bool) or not isinstance(offset,int) or not 0<=offset<len(encoded):raise ValueError('无效分块位置')
                    if offset==0:stage('transfer_begin')
                    chunk=encoded[offset:offset+128*1024]
                    if offset+len(chunk)==len(encoded):stage('transfer_end')
                    return dict(chunk=chunk,total=len(encoded))
                def page_event(self,event):
                    if event not in {'ready','image_decoded','image_error','js_error'}:return
                    record('page_'+event)
                    if event=='image_decoded':
                        state['decoded']=True
                        if state['displayed']:ready.set()
                    elif event in {'image_error','js_error'}:fail('框选图片加载失败，请查看日志')
            assets=Path(__file__).parent
            data=dict(width=image.width,height=image.height,box=box)
            html=(assets/'index.html').read_text(encoding='utf-8').replace('/* DATA */',json.dumps(data)).replace('/* SCRIPT */',(assets/'main.js').read_text(encoding='utf-8'))
            stage('html_ready',html_bytes=len(html.encode('utf-8')))
            state['api']=API()
            if aborted.is_set():return
            stage('create_begin')
            window=webview.create_window('框选签名区域',html=html,js_api=state['api'],width=900,height=650,min_size=(640,400),hidden=True,resizable=True,maximized=False,on_top=False,background_color='#F4F6F8')
            state['window']=window;stage('created',uid=window.uid)
            if aborted.is_set():cleanup(window);return
            with _active_lock:_active=window
            def closed(*args):
                nonlocal encoded
                # 窗口关闭即释放预览传输串，不等待跨语言引用回收。
                encoded=''
                record('closed');done.set();ready.set()
            load_lock=threading.Lock()
            def loaded(*args):
                if not load_lock.acquire(blocking=False):return
                if state.get('load_handled'):load_lock.release();return
                state['load_handled']=True
                try:
                    stage('page_loaded')
                    if aborted.is_set():cleanup(window);return
                    from .placement import show_positioned
                    stage('show_begin');show_positioned(window,parent,record);stage('show_returned');state['displayed']=True
                    if state['decoded']:ready.set()
                except Exception as exc:
                    record('exception',stage=state['stage'],exception_type=type(exc).__name__,traceback=traceback.format_exc());fail('框选窗口显示失败，请查看日志')
                finally:load_lock.release()
            window.events.before_show+=lambda *args:record('native_before_show')
            record('native_state_after_create',native_exists=getattr(window,'native',None) is not None,shown=window.events.shown.is_set(),loaded=window.events.loaded.is_set())
            window.events.closed+=closed
            window.events.loaded+=loaded
            window.events.shown+=lambda *args:record('shown')
            # 创建同步完成期间loaded/closed可能早于处理器绑定。
            if window.events.closed.is_set():closed()
            elif window.events.loaded.is_set():
                record('loaded_before_subscription');loaded()
        except Exception as exc:
            record('exception',stage=state['stage'],exception_type=type(exc).__name__,traceback=traceback.format_exc());fail('框选窗口准备失败，请查看日志')
    record('request_received')
    threading.Thread(target=prepare,daemon=True).start()
    try:
        if not ready.wait(timeout):
            record('timeout',stage=state['stage'],timeout_seconds=timeout)
            raise TimeoutError('框选窗口加载超过45秒，请重试并查看日志')
        if aborted.is_set():return None
        if state['error']:raise RuntimeError(state['error'])
        if not done.is_set():done.wait()  # 正常用户框选不限时。
        return state['result']
    except Exception as exc:
        record('request_exception',stage=state['stage'],exception_type=type(exc).__name__,traceback=traceback.format_exc())
        raise
    finally:
        aborted.set()
        window=state['window']
        with _active_lock:
            if _active is window:_active=None
            _requests.pop(request,None)
        if window is not None and not done.is_set():cleanup(window)
        _opening.release()
        record('request_finished',aborted=aborted.is_set(),prepare_threads_daemon=True)
