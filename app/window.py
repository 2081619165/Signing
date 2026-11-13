"""窗口和诊断桥接，不导入印签算法。"""
import argparse
import importlib.metadata
import json
import logging
from pathlib import Path
import platform
import threading
from time import perf_counter
from datetime import datetime
import sys

ROOT = Path(__file__).resolve().parents[1]

class Diagnostics:
    def __init__(self, entry):
        self.entry = entry
        folder = ROOT / '.local-tests' / 'webview-logs'
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / (datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.jsonl')
        self.lock = threading.Lock()

    def record(self, event, **data):
        item = dict(event=event, since_entry_ms=round((perf_counter()-self.entry)*1000, 3), **data)
        with self.lock:
            with self.path.open('a', encoding='utf8') as f:
                f.write(json.dumps(item, ensure_ascii=False)+'\n')
        return item

class Bridge:
    def __init__(self, diag):
        self._diag = diag

    def ping(self):
        return self._diag.record('python_ping')

    def page_event(self, name, metrics):
        # 仅收集固定诊断事件，不开放文件访问或命令执行。
        allowed = {'js_ready', 'bridge_rtt', 'visibility', 'js_error', 'manual_marker'}
        if name not in allowed or not isinstance(metrics, dict):
            raise ValueError('无效诊断事件')
        return self._diag.record(name, browser=metrics)

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
        diag.record('entry_environment', python=platform.python_version(), os=platform.platform())
        t = perf_counter()
        import webview
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
            print('依赖检查完成；未创建窗口，渲染和黑屏尚未验证。')
            return 0
        assets = Path(__file__).parent / 'static'
        html = (assets/'index.html').read_text(encoding='utf8')
        html = html.replace('/* INLINE_STYLE */', (assets/'style.css').read_text(encoding='utf8'))
        html = html.replace('/* INLINE_SCRIPT */', (assets/'main.js').read_text(encoding='utf8'))
        t = perf_counter()
        window = webview.create_window('Signing', html=html, js_api=Bridge(diag),
                                      width=960, height=680, min_size=(680,480),
                                      resizable=True, background_color='#F4F6F8')
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
        webview.start(gui='edgechromium', http_server=False, debug=False)
        diag.record('gui_loop_returned')
        return 0
    except Exception as exc:
        diag.record('fatal_error', error=repr(exc))
        logging.exception('Signing启动失败；请检查日志与WebView2/.NET依赖')
        return 1
