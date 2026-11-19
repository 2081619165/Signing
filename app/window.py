"""窗口、诊断及异步业务桥接。"""
import argparse
import base64
import os
import importlib.metadata
import io
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
        self.path = folder / (datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.jsonl')
        self.lock = threading.Lock()
        self.write_failures=0
        self.last_error_type=None
        try:folder.mkdir(parents=True, exist_ok=True)
        except Exception as exc:self._failed(exc)

    def _failed(self,exc):
        # 日志失败不得阻断业务；只留内存计数，禁止递归写日志。
        self.write_failures+=1;self.last_error_type=type(exc).__name__

    def record(self, event, **data):
        # 堆栈仅保留代码位置，不落盘异常文本、源代码行或客户文件路径。
        if 'traceback' in data:
            data['traceback']=[dict(file=Path(f.filename).name,line=f.lineno,function=f.name)
                               for f in traceback.extract_tb(sys.exc_info()[2])]
        if 'error' in data:data['error']='details_omitted'
        item = dict(event=event, pid=os.getpid(), thread=dict(name=threading.current_thread().name,ident=threading.get_ident(),daemon=threading.current_thread().daemon), since_entry_ms=round((perf_counter()-self.entry)*1000, 3), **data)
        try:
            with self.lock:
                self.path.parent.mkdir(parents=True,exist_ok=True)
                with self.path.open('a', encoding='utf8') as f:
                    f.write(json.dumps(item, ensure_ascii=False)+'\n')
        except Exception as exc:self._failed(exc)
        return item

class Bridge:
    def __init__(self, diag):
        self._diag = diag
        self._window = None
        self._session = None
        self._eraser = None

    def ping(self):
        return self._diag.record('python_ping')

    def page_event(self, name, metrics):
        # 仅收集固定诊断事件，不开放文件访问或命令执行。
        allowed = {'js_ready', 'bridge_rtt', 'visibility', 'js_error', 'manual_marker','crop_frontend'}
        if name not in allowed or not isinstance(metrics, dict):
            raise ValueError('无效诊断事件')
        if name=='js_error':metrics={'reported':True}  # 浏览器错误文本可能夹带客户路径。
        if name=='crop_frontend':
            metrics={k:v for k,v in metrics.items() if k in {'request','stage','ready','busy','has_input','ok','cancelled','elapsed_ms'} and isinstance(v,(str,bool,int,float))}
            if any(isinstance(v,str) and len(v)>80 for v in metrics.values()):raise ValueError('无效框选诊断')
        return self._diag.record(name, browser=metrics)

    def _run(self, action, operation='unspecified'):
        started=perf_counter()
        def record(stage,**data):
            if self._diag:self._diag.record('bridge_operation',operation=operation,stage=stage,elapsed_ms=round((perf_counter()-started)*1000,3),**data)
        record('received')
        if self._session is None:
            record('rejected',reason='session_unavailable')
            return {'ok':False,'error':'业务模块尚未就绪'}
        if not self._session.lock.acquire(blocking=False):
            record('rejected',reason='session_busy')
            return {'ok':False,'error':'正在处理，请稍候'}
        try:
            record('started')
            response={'ok':True, **action()}
            record('cancelled' if response.get('cancelled') else 'completed')
            return response
        except MemoryError:
            record('failed',exception_type='MemoryError')
            if self._diag:self._diag.record('bridge_memory_error',exception_type='MemoryError')
            return {'ok':False,'error':'图片解码或处理内存不足，请关闭其他程序或先缩小原图'}
        except Exception as exc:
            record('failed',exception_type=type(exc).__name__)
            if self._diag:self._diag.record('bridge_action_exception',exception_type=type(exc).__name__,traceback=traceback.format_exc())
            return {'ok':False,'error':str(exc)}
        finally:
            self._session.lock.release()
            record('released')

    def choose_image(self):
        def action():
            import webview
            self._session.color_base=None;self._session.color_edited=False
            self._session.base_result=None;self._session.rotation=0;self._session.full=None;self._session.crop_box=None;self._session.original=None;self._session.result=None
            selected=self._window.create_file_dialog(webview.FileDialog.OPEN,allow_multiple=False,file_types=('Images (*.png;*.jpg;*.jpeg)',))
            if not selected:return {'cancelled':True}
            p=Path(selected[0])
            if p.stat().st_size>30*1024*1024:raise ValueError('图片超过30MB')
            return self._session.load(p.name,p.read_bytes(),str(p))
        return self._run(action,'choose_image')

    def import_image(self, name, encoded):
        def action():
            import base64
            self._session.color_base=None;self._session.color_edited=False
            self._session.base_result=None;self._session.rotation=0;self._session.full=None;self._session.crop_box=None;self._session.original=None;self._session.result=None
            if len(encoded)>42*1024*1024:raise ValueError('图片超过大小限制')
            return self._session.load(name,base64.b64decode(encoded,validate=True))
        return self._run(action,'import_image')

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
            response=self._run(action,'select_region')
            record('returned',ok=response.get('ok'),cancelled=response.get('cancelled',False))
            return response
        except Exception as exc:
            record('exception',exception_type=type(exc).__name__,traceback=traceback.format_exc())
            return dict(ok=False,error=str(exc))

    def process_image(self, enhance='standard', kind='auto', color_enhance=False):
        return self._run(lambda:self._session.process(enhance,kind,diagnostic=self._diag.record if self._diag else None,
                                                     color_enhance=color_enhance),'process_image')

    def set_color_enhancement(self, enabled, discard_edits=False):
        return self._run(lambda:self._session.set_color_enhancement(enabled,discard_edits),'set_color_enhancement')

    def begin_erasure(self):
        def action():
            image=self._session.result
            if image is None:raise ValueError('请先成功提取')
            self._eraser=None
            with io.BytesIO() as stream:
                image.save(stream,format='PNG')
                encoded=base64.b64encode(stream.getbuffer()).decode('ascii')
            token=uuid.uuid4().hex
            self._eraser=(token,image,encoded,bytearray())
            if self._diag:self._diag.record('eraser_ready',width=image.width,height=image.height)
            return dict(token=token,width=image.width,height=image.height,total=len(encoded))
        return self._run(action,'begin_erasure')

    def _erasure(self,token):
        state=self._eraser
        if state is None or token!=state[0] or state[1] is not self._session.result:
            raise ValueError('当前结果已变化，请重新打开橡皮擦')
        return state

    def eraser_image_chunk(self,token,offset):
        def action():
            _,image,encoded,mask=self._erasure(token)
            if type(offset) is not int or not 0<=offset<len(encoded):raise ValueError('无效图像分块')
            chunk=encoded[offset:offset+128*1024]
            if offset+len(chunk)==len(encoded):
                self._eraser=(token,image,'',mask)
            return dict(chunk=chunk)
        return self._run(action,'eraser_image_chunk')

    def eraser_mask_chunk(self,token,offset,chunk):
        def action():
            _,image,_,mask=self._erasure(token)
            if type(offset) is not int or not isinstance(chunk,str) or not 0<len(chunk)<=128*1024:
                raise ValueError('无效擦除数据分块')
            block=base64.b64decode(chunk,validate=True)
            if offset==0:mask.clear()
            if offset!=len(mask) or len(mask)+len(block)>(image.width*image.height+7)//8:
                raise ValueError('无效擦除数据范围')
            mask.extend(block)
            return {}
        return self._run(action,'eraser_mask_chunk')

    def finish_erasure(self,token):
        def action():
            _,image,_,mask=self._erasure(token)
            result=self._session.commit_erasure(mask)
            self._eraser=None
            if self._diag:self._diag.record('eraser_completed',width=image.width,height=image.height)
            return result
        return self._run(action,'finish_erasure')

    def cancel_erasure(self,token):
        def action():
            if self._eraser and token==self._eraser[0]:
                self._eraser=None
                if self._diag:self._diag.record('eraser_cancelled')
            return {}
        return self._run(action,'cancel_erasure')

    def rotate_result(self, angle):
        return self._run(lambda:self._session.rotate_result(angle),'rotate_result')

    def estimate_size(self, settings):
        return self._run(lambda:self._session.dimensions(settings),'estimate_size')

    def export_image(self, kind, settings=None):
        def action():
            import webview
            if kind not in {'png','gif'}:raise ValueError('不支持的格式')
            if self._session.result is None:raise ValueError('请先处理图片')
            selected=self._window.create_file_dialog(webview.FileDialog.SAVE,save_filename='signature.'+kind,file_types=(kind.upper()+' (*.'+kind+')',))
            if not selected:return {'cancelled':True}
            target=selected if isinstance(selected,str) else selected[0]
            return self._session.export(target,kind,settings)
        return self._run(action,'export_image')

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
    exit_code=1
    print('诊断日志:', diag.path, flush=True)
    try:
        diag.record('entry_environment', crop_diagnostics_version='2026-11-18-hardening-v1',frozen=bool(getattr(sys,'frozen',False)),python=platform.python_version(), os=platform.platform())
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
            exit_code=0
            return 0
        assets = Path(__file__).parent / 'static'
        html = (assets/'index.html').read_text(encoding='utf8')
        html = html.replace('/* BRAND_ICON */','data:image/png;base64,'+base64.b64encode((assets.parent/'assets/sealkit.png').read_bytes()).decode('ascii'))
        html = html.replace('/* INLINE_STYLE */', (assets/'style.css').read_text(encoding='utf8'))
        html = html.replace('/* INLINE_SCRIPT */', (assets/'main.js').read_text(encoding='utf8')+'\n'+
                            (assets/'eraser.js').read_text(encoding='utf8'))
        t = perf_counter()
        bridge=Bridge(diag)
        from processing import Session
        bridge._session=Session()
        window = webview.create_window('SealKit', html=html, js_api=bridge,
                                      width=960, height=680, min_size=(680,480),
                                      resizable=True, background_color='#F4F6F8')
        bridge._window=window
        def cleanup_crop(*unused):
            diag.record('main_close_cleanup_begin')
            from crop import shutdown
            shutdown(diag)
            diag.record('main_close_cleanup_returned')
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
        exit_code=0
        return 0
    except Exception as exc:
        diag.record('fatal_error', exception_type=type(exc).__name__,traceback=traceback.format_exc())
        logging.error('SealKit启动失败：%s；请检查诊断日志',type(exc).__name__)
        return 1
    finally:
        diag.record('application_return',exit_code=exit_code,log_write_failures=diag.write_failures,
                    log_last_error_type=diag.last_error_type,
                    non_daemon_threads=[t.name for t in threading.enumerate() if not t.daemon and t is not threading.current_thread()])
