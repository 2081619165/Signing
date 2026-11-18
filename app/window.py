"""窗口、诊断及异步业务桥接。"""
import argparse
import base64
import os
import importlib.metadata
import json
import logging
from pathlib import Path
import platform
import threading
import traceback
import uuid
from time import perf_counter
from datetime import datetime
import sys

ROOT = Path(__file__).resolve().parents[1]

class Diagnostics:
    def __init__(self, entry):
        self.entry = entry
        folder = (Path(os.environ.get('LOCALAPPDATA',str(Path.home()))) / 'SealKit' / 'logs') if getattr(sys,'frozen',False) else ROOT / '.local-tests' / 'webview-logs'
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / (datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.jsonl')
        self.lock = threading.Lock()

    def record(self, event, **data):
        item = dict(event=event, pid=os.getpid(), thread=dict(name=threading.current_thread().name,ident=threading.get_ident(),daemon=threading.current_thread().daemon), since_entry_ms=round((perf_counter()-self.entry)*1000, 3), **data)
        with self.lock:
            with self.path.open('a', encoding='utf8') as f:
                f.write(json.dumps(item, ensure_ascii=False)+'\n')
        return item

class Bridge:
    def __init__(self, diag):
        self._diag = diag
        self._window = None
        self._session = None

    def ping(self):
        return self._diag.record('python_ping')

    def page_event(self, name, metrics):
        # 仅收集固定诊断事件，不开放文件访问或命令执行。
        allowed = {'js_ready', 'bridge_rtt', 'visibility', 'js_error', 'manual_marker','crop_frontend'}
        if name not in allowed or not isinstance(metrics, dict):
            raise ValueError('无效诊断事件')
        if name=='crop_frontend':
            metrics={k:v for k,v in metrics.items() if k in {'request','stage','ready','busy','has_input','ok','cancelled','elapsed_ms'} and isinstance(v,(str,bool,int,float))}
            if any(isinstance(v,str) and len(v)>80 for v in metrics.values()):raise ValueError('无效框选诊断')
        return self._diag.record(name, browser=metrics)

    def _run(self, action):
        if self._session is None:
            return {'ok':False,'error':'业务模块尚未就绪'}
        if not self._session.lock.acquire(blocking=False):
            return {'ok':False,'error':'正在处理，请稍候'}
        try:
            return {'ok':True, **action()}
        except MemoryError:
            if self._diag:self._diag.record('bridge_memory_error',exception_type='MemoryError')
            return {'ok':False,'error':'图片解码或处理内存不足，请关闭其他程序或先缩小原图'}
        except Exception as exc:
            if self._diag:self._diag.record('bridge_action_exception',exception_type=type(exc).__name__,traceback=traceback.format_exc())
            return {'ok':False,'error':str(exc)}
        finally:
            self._session.lock.release()

    def choose_image(self):
        def action():
            import webview
            self._session.base_result=None;self._session.rotation=0;self._session.full=None;self._session.crop_box=None;self._session.original=None;self._session.result=None
            selected=self._window.create_file_dialog(webview.FileDialog.OPEN,allow_multiple=False,file_types=('Images (*.png;*.jpg;*.jpeg)',))
            if not selected:return {'cancelled':True}
            p=Path(selected[0])
            if p.stat().st_size>30*1024*1024:raise ValueError('图片超过30MB')
            return self._session.load(p.name,p.read_bytes(),str(p))
        return self._run(action)

    def import_image(self, name, encoded):
        def action():
            import base64
            self._session.base_result=None;self._session.rotation=0;self._session.full=None;self._session.crop_box=None;self._session.original=None;self._session.result=None
            if len(encoded)>42*1024*1024:raise ValueError('图片超过大小限制')
            return self._session.load(name,base64.b64decode(encoded,validate=True))
        return self._run(action)

    def select_region(self, request=None):
        started=perf_counter()
        request=request if isinstance(request,str) and len(request)<=64 and request.replace('-','').isalnum() else uuid.uuid4().hex[:12]
        def record(stage,**data):
            if self._diag:self._diag.record('crop_bridge',request=request,stage=stage,elapsed_ms=round((perf_counter()-started)*1000,3),**data)
        record('received')  # 必须早于模块导入、窗口激活及会话锁。
        try:
            from crop import activate_existing
            record('activation_check')
            if activate_existing():
                record('existing_or_opening');return dict(ok=True,cancelled=True)
            def action():
                from crop import select
                if self._session.full is None:raise ValueError('请先导入图片')
                record('session_acquired',width=self._session.full.width,height=self._session.full.height,file_bytes=getattr(self._session,'input_bytes',None))
                box=select(self._session.full,self._session.crop_box,self._window,self._diag,request_id=request,validate=self._session.validate_crop)
                if box is None:
                    record('cancelled');return dict(cancelled=True)
                record('crop_commit_begin')
                result=self._session.crop(box)
                record('crop_commit_end',width=self._session.original.width,height=self._session.original.height,requires_crop=self._session.requires_crop,source_crop_size=result['source_crop_size'],work_size=result['work_size']);return result
            response=self._run(action)
            record('returned',ok=response.get('ok'),cancelled=response.get('cancelled',False))
            return response
        except Exception as exc:
            record('exception',exception_type=type(exc).__name__,traceback=traceback.format_exc())
            return dict(ok=False,error=str(exc))

    def process_image(self, enhance='standard', kind='auto'):
        return self._run(lambda:self._session.process(enhance,kind,diagnostic=self._diag.record if self._diag else None))

    def rotate_result(self, angle):
        return self._run(lambda:self._session.rotate_result(angle))

    def estimate_size(self, settings):
        return self._run(lambda:self._session.dimensions(settings))

    def export_image(self, kind, settings=None):
        def action():
            import webview
            if kind not in {'png','gif'}:raise ValueError('不支持的格式')
            if self._session.result is None:raise ValueError('请先处理图片')
            selected=self._window.create_file_dialog(webview.FileDialog.SAVE,save_filename='signature.'+kind,file_types=(kind.upper()+' (*.'+kind+')',))
            if not selected:return {'cancelled':True}
            target=selected if isinstance(selected,str) else selected[0]
            return self._session.export(target,kind,settings)
        return self._run(action)

def runtime_versions():
    if sys.platform != 'win32':
        return []
    import winreg
    found = []
    sub = r'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}'
    for hive, label in [(winreg.HKEY_LOCAL_MACHINE, 'machine'), (winreg.HKEY_CURRENT_USER, 'user')]:
        for view in [winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY]:
            try:
                with winreg.OpenKey(hive, sub, 0, winreg.KEY_READ | view) as key:
                    version = winreg.QueryValueEx(key, 'pv')[0]
                    if version and version != '0.0.0.0':
                        item = dict(scope=label, version=version)
                        if item not in found: found.append(item)
            except FileNotFoundError:
                pass
    return found

def main(entry):
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='仅检查依赖，不创建窗口')
    args = parser.parse_args()
    diag = Diagnostics(entry)
    print('诊断日志:', diag.path, flush=True)
    try:
        diag.record('entry_environment', crop_diagnostics_version='2026-11-17-entry-v2',frozen=bool(getattr(sys,'frozen',False)),python=platform.python_version(), os=platform.platform())
        t = perf_counter()
        import webview
        if sys.platform=='win32':
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('SealKit.Desktop')
        diag.record('webview_imported', duration_ms=(perf_counter()-t)*1000,
                    version=importlib.metadata.version('pywebview'))
        versions = runtime_versions()
        diag.record('runtime_registry', versions=versions)
        if sys.platform != 'win32': raise RuntimeError('此原型仅支持Windows')
        if not versions: raise RuntimeError('未检测到WebView2 Runtime，请安装Evergreen Runtime；不自动回退MSHTML')
        # 检查 .NET / pythonnet 加载；最终渲染能力仍以实际窗口启动为准。
        import clr
        diag.record('pythonnet_imported')
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full') as key:
            release = winreg.QueryValueEx(key, 'Release')[0]
        diag.record('dotnet_release', release=release)
        if release < 394802: raise RuntimeError('需要.NET Framework 4.6.2或更高版本')
        if args.check:
            import cv2, numpy, PIL
            diag.record('image_dependencies', opencv=cv2.__version__, numpy=numpy.__version__, pillow=PIL.__version__)
            print('依赖检查完成；未创建窗口，渲染和黑屏尚未验证。')
            return 0
        assets = Path(__file__).parent / 'static'
        html = (assets/'index.html').read_text(encoding='utf8')
        html = html.replace('/* BRAND_ICON */','data:image/png;base64,'+base64.b64encode((assets.parent/'assets/sealkit.png').read_bytes()).decode('ascii'))
        html = html.replace('/* INLINE_STYLE */', (assets/'style.css').read_text(encoding='utf8'))
        html = html.replace('/* INLINE_SCRIPT */', (assets/'main.js').read_text(encoding='utf8'))
        t = perf_counter()
        bridge=Bridge(diag)
        from processing import Session
        bridge._session=Session()
        window = webview.create_window('SealKit', html=html, js_api=bridge,
                                      width=960, height=680, min_size=(680,480),
                                      resizable=True, background_color='#F4F6F8')
        bridge._window=window
        def cleanup_crop(*unused):
            from crop import shutdown
            shutdown(diag)
        window.events.closing+=cleanup_crop
        diag.record('window_object_created', duration_ms=(perf_counter()-t)*1000)
        for name in ['shown','loaded','minimized','maximized','restored','closed']:
            def event_handler(*unused, event=name):
                diag.record('window_'+event, actual_renderer=getattr(window.gui, 'renderer', 'unknown'))
                if event == 'shown' and getattr(window.gui, 'renderer', None) != 'edgechromium':
                    diag.record('fatal_error', error='实际后端非edgechromium，关闭原型')
                    window.destroy()
            getattr(window.events, name).__iadd__(event_handler)
        diag.record('gui_loop_requested', backend='edgechromium')
        # HTML直接注入，资源内联，不触发本地HTTP服务。
        webview.start(gui='edgechromium', http_server=False, debug=False, icon=str(assets.parent/'assets/sealkit.ico'))
        cleanup_crop()
        diag.record('gui_loop_returned',live_threads=[dict(name=t.name,daemon=t.daemon) for t in threading.enumerate()])
        return 0
    except Exception as exc:
        diag.record('fatal_error', error=repr(exc))
        logging.exception('SealKit启动失败；请检查日志与WebView2/.NET依赖')
        return 1
