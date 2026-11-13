"""正式处理回归，不使用真实客户材料。"""
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from processing import Session
from window import Bridge

class ProcessingTests(unittest.TestCase):
    def sample(self,ink=25):
        im=Image.new('RGB',(320,160),(185,185,185));d=ImageDraw.Draw(im);d.line((20,130,90,25,140,125,290,40),fill=(ink,ink,ink),width=5)
        b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()

    def test_export_and_source_protection(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'中文原图.png';p.write_bytes(self.sample());before=p.read_bytes()
            s=Session();s.load(p.name,p.read_bytes(),p);s.process()
            with self.assertRaises(ValueError):s.export(p,'png')
            for kind in ['png','gif']:
                target=Path(folder)/('签名.'+kind);r=s.export(target,kind)
                self.assertEqual(r['size'][1],42)
                with Image.open(target) as im:
                    a=np.asarray(im.convert('RGBA'))[...,3];self.assertTrue((a==0).any() and (a>0).any())
            self.assertEqual(before,p.read_bytes())

    def test_faint_failure_preserves_target_and_png_success(self):
        s=Session();s.load('faint.png',self.sample(170));s.process()
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'existing.gif';p.write_bytes(b'existing')
            with self.assertRaisesRegex(ValueError,'全透明'):s.export(p,'gif')
            self.assertEqual(p.read_bytes(),b'existing')
            s.export(Path(folder)/'valid.png','png')

    def test_empty_and_bad_import_clear_result(self):
        s=Session();s.load('good.png',self.sample());s.process()
        with self.assertRaises(Exception):s.load('bad.png',b'not image')
        self.assertIsNone(s.result);self.assertIsNone(s.original)
        b=io.BytesIO();Image.new('RGB',(100,100),'white').save(b,format='PNG');s.load('blank.png',b.getvalue())
        with self.assertRaises(ValueError):s.process()
        self.assertIsNone(s.result)

    def test_v1_pixel_equivalence(self):
        spec=importlib.util.spec_from_file_location('v1',ROOT/'experiments/gray_signature.py');v1=importlib.util.module_from_spec(spec);spec.loader.exec_module(v1)
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'input.png';p.write_bytes(self.sample());out=Path(folder)/'baseline.png';v1.extract(p,out)
            s=Session();s.load(p.name,p.read_bytes());s.process(False)
            with Image.open(Path(folder)/'baseline_native.png') as im:self.assertTrue(np.array_equal(np.asarray(im),np.asarray(s.result)))

    def test_bridge_rejects_duplicate(self):
        bridge=Bridge(None);bridge._session=Session();bridge._session.lock.acquire()
        try:self.assertFalse(bridge.process_image()['ok'])
        finally:bridge._session.lock.release()

if __name__=='__main__':unittest.main()
