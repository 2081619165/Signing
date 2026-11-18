"""窗口定位纯坐标回归，不启动原生窗口。"""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from crop.placement import choose_bounds

class PlacementTests(unittest.TestCase):
    def test_diagnostics_write_failure_never_breaks_bridge(self):
        from window import Diagnostics,Bridge
        from processing import Session
        from time import perf_counter
        from unittest.mock import patch
        with patch('pathlib.Path.mkdir',side_effect=PermissionError):
            diag=Diagnostics(perf_counter())
            self.assertEqual(diag.record('test')['event'],'test')
            bridge=Bridge(diag);bridge._session=Session()
            self.assertTrue(bridge._run(lambda:{'cancelled':True},'choose_image')['ok'])
            self.assertFalse(bridge._run(lambda:(_ for _ in ()).throw(ValueError('private')),'export_image')['ok'])
            self.assertFalse(bridge._session.lock.locked())
        self.assertGreater(diag.write_failures,1)
        self.assertEqual(diag.last_error_type,'PermissionError')

    def test_diagnostics_operation_and_private_exception(self):
        from window import Diagnostics,Bridge
        from processing import Session
        from unittest.mock import patch
        from time import perf_counter
        import tempfile,json
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'.local-tests') as folder:
            with patch('window.ROOT',Path(folder)):diag=Diagnostics(perf_counter())
            bridge=Bridge(diag);bridge._session=Session()
            bridge._run(lambda:{'cancelled':True},'choose_image')
            bridge._run(lambda:(_ for _ in ()).throw(OSError('SECRET_CUSTOMER_PATH')),'export_image')
            diag.record('application_return',exit_code=0)
            text=diag.path.read_text(encoding='utf-8');rows=[json.loads(line) for line in text.splitlines()]
            self.assertNotIn('SECRET_CUSTOMER_PATH',text)
            self.assertTrue(any(r.get('operation')=='choose_image' and r.get('stage')=='cancelled' for r in rows))
            self.assertTrue(any(r.get('operation')=='export_image' and r.get('exception_type')=='OSError' for r in rows))
            self.assertEqual(rows[-1]['exit_code'],0)

    def test_closed_state_without_callback_releases_waiter(self):
        import crop,threading,time
        from unittest.mock import patch
        from types import SimpleNamespace
        from PIL import Image
        class Event:
            def __init__(self,value=False):self.value=value
            def __iadd__(self,handler):return self
            def is_set(self):return self.value
        window=SimpleNamespace(uid='missed-close',native=None,events=SimpleNamespace(closed=Event(),loaded=Event(True),shown=Event(),before_show=Event()))
        results=[];rows=[]
        class Log:
            def record(self,event,**data):rows.append(event)
        def create(*args,**kwargs):kwargs['js_api'].page_event('image_decoded');return window
        with patch('webview.create_window',side_effect=create),patch('crop.placement.show_positioned'):
            worker=threading.Thread(target=lambda:results.append(crop.select(Image.new('RGB',(40,40)),None,None,Log(),timeout=2)),daemon=True)
            worker.start();deadline=time.monotonic()+2
            while crop._active is None and time.monotonic()<deadline:time.sleep(.01)
            window.events.closed.value=True  # 不发出closed回调。
            worker.join(2)
        self.assertFalse(worker.is_alive());self.assertEqual(results,[None])
        self.assertIn('crop_closed_state_recovered',rows)

    def test_center_tracks_main_position(self):
        self.assertEqual(choose_bounds((0,100,960,680),(0,0,2400,1040),(900,650)),(30,115,900,650))
        self.assertEqual(choose_bounds((1200,100,960,680),(0,0,2400,1040),(900,650)),(1230,115,900,650))
        self.assertEqual(choose_bounds((200,0,960,680),(0,0,1600,860),(900,650)),(230,15,900,650))
    def test_negative_monitor_and_small_workarea(self):
        for area,size in [((-1920,0,1920,1040),(900,650)),((0,0,800,560),(900,650)),((1920,0,2560,1400),(1350,975))]:
            x,y,w,h=choose_bounds((area[0]+100,200,1000,700),area,size)
            self.assertGreaterEqual(x,area[0]);self.assertGreaterEqual(y,area[1])
            self.assertLessEqual(x+w,area[0]+area[2]);self.assertLessEqual(y+h,area[1]+area[3])

    def test_crop_preview_preserves_original_geometry(self):
        from crop import preview_payload
        from PIL import Image
        import io,base64
        from processing import Session
        for size in ((120,60),(2480,3508),(4000,3000)):
            image=Image.new('RGB',size,'white')
            encoded,preview_size,_=preview_payload(image)
            self.assertLessEqual(max(preview_size),1600)
            with Image.open(io.BytesIO(base64.b64decode(encoded))) as decoded:self.assertEqual(decoded.size,preview_size)
            session=Session();session.full=image
            session.crop([10,10,110,50]);self.assertEqual(session.original.size,(100,40))
            self.assertEqual(session.full.size,size)

    def test_crop_timeout_then_creation_failure_releases_guard(self):
        from crop import select,_opening
        from unittest.mock import patch
        from PIL import Image
        import time
        logs=[]
        class Log:
            def record(self,event,**data):logs.append(event)
        class Event:
            def __iadd__(self,handler):return self
            def is_set(self):return False
        class Window:
            uid='fake'
            class events:
                closed=Event();loaded=Event();shown=Event();before_show=Event()
            def destroy(self):pass
        with patch('webview.create_window',return_value=Window()):
            with self.assertRaises(TimeoutError):select(Image.new('RGB',(40,40)),None,None,Log(),timeout=.1)
        self.assertFalse(_opening.locked());self.assertIn('crop_timeout',logs)
        with patch('webview.create_window',side_effect=RuntimeError('mock')):
            with self.assertRaises(RuntimeError):select(Image.new('RGB',(40,40)),None,None,Log(),timeout=2)
        self.assertFalse(_opening.locked());self.assertIn('crop_exception',logs)

    def test_main_close_wakes_active_crop_and_cleans_registry(self):
        import crop,threading,time
        from unittest.mock import patch
        from types import SimpleNamespace
        from PIL import Image
        class Event:
            def __init__(self,value=False):self.value=value
            def __iadd__(self,handler):return self
            def is_set(self):return self.value
        def create(*args,**kwargs):
            kwargs['js_api'].page_event('image_decoded')
            return SimpleNamespace(uid='test',native=None,events=SimpleNamespace(closed=Event(),loaded=Event(True),shown=Event(),before_show=Event()))
        outputs=[];errors=[]
        def run():
            try:outputs.append(crop.select(Image.new('RGB',(40,40)),None,None,timeout=2))
            except Exception as exc:errors.append(str(exc))
        with patch('webview.create_window',side_effect=create),patch('crop.placement.show_positioned'),patch('crop.close_native') as close:
            worker=threading.Thread(target=run,daemon=True);worker.start()
            deadline=time.monotonic()+2
            while crop._active is None and time.monotonic()<deadline:time.sleep(.01)
            crop.shutdown();worker.join(2)
            self.assertFalse(worker.is_alive());self.assertEqual(errors,[]);self.assertEqual(outputs,[None])
            self.assertFalse(crop._opening.locked());self.assertIsNone(crop._active);self.assertFalse(crop._requests)
            self.assertTrue(close.called)
        crop._shutdown.clear()  # 测试隔离；实际退出状态不恢复。

    def test_crop_bridge_logs_before_activation_and_rejected_lock(self):
        from window import Bridge
        from processing import Session
        from unittest.mock import patch
        rows=[]
        class Log:
            def record(self,event,**data):rows.append((event,data))
        bridge=Bridge(Log());bridge._session=Session()
        with patch('crop.activate_existing',side_effect=RuntimeError('activation mock')):
            self.assertFalse(bridge.select_region('crop-test')['ok'])
        self.assertEqual(rows[0][1]['stage'],'received')
        self.assertEqual(rows[-1][1]['exception_type'],'RuntimeError')
        rows.clear();bridge._session.lock.acquire()
        try:
            with patch('crop.activate_existing',return_value=False):self.assertFalse(bridge.select_region('crop-lock')['ok'])
        finally:bridge._session.lock.release()
        self.assertEqual(rows[-1][1]['stage'],'returned');self.assertFalse(rows[-1][1]['ok'])
