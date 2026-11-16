"""独立框选窗口，仅暴露读取快照与提交选区。"""
import base64
import io
import json
import threading
from pathlib import Path


_active=None
_active_lock=threading.Lock()

def activate_existing():
    from .placement import activate
    with _active_lock:
        window=_active
    if window is None:return False
    activate(window)
    return True


def select(image,box,parent):
    import webview
    stream=io.BytesIO();image.save(stream,format='PNG')
    data=dict(src='data:image/png;base64,'+base64.b64encode(stream.getvalue()).decode('ascii'),width=image.width,height=image.height,box=box)
    done=threading.Event()
    class API:
        def cancel(self):
            window.destroy()

        def confirm(self,coords):
            self.result=coords
            window.destroy()
    api=API();api.result=None
    assets=Path(__file__).parent
    html=(assets/'index.html').read_text(encoding='utf-8').replace('/* DATA */',json.dumps(data)).replace('/* SCRIPT */',(assets/'main.js').read_text(encoding='utf-8'))
    global _active
    from .placement import show_positioned
    window=webview.create_window('框选签名区域',html=html,js_api=api,
        width=900,height=650,min_size=(640,400),hidden=True,
        resizable=True,maximized=False,on_top=False,background_color='#F4F6F8')
    with _active_lock:_active=window
    def closed(*args):
        global _active
        with _active_lock:
            if _active is window:_active=None
        done.set()
    window.events.closed+=closed
    window.events.loaded+=lambda *args:show_positioned(window,parent)
    done.wait()
    return api.result
