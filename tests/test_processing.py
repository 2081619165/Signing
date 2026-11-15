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

    def test_dimensions_and_fixed_canvas(self):
        s=Session();s.load('input.png',self.sample());s.process()
        with tempfile.TemporaryDirectory() as folder:
            for width,height,dpi,expected in [(1.6,1.6,96,[60,60]),(4,2.8,96,[151,106]),(4,4,96,[151,151]),(4,2.8,300,[472,331])]:
                config=dict(unit='cm',width=width,height=height,dpi=dpi)
                self.assertEqual(s.dimensions(config)['size'],expected)
                for kind in ['png','gif']:
                    r=s.export(Path(folder)/('out.'+kind),kind,config)
                    self.assertEqual(r['size'],expected)
                    with Image.open(Path(folder)/('out.'+kind)) as im:self.assertEqual(list(im.size),expected)
            self.assertEqual(s.dimensions(dict(unit='cm',height=.9,dpi=96))['size'][1],34)
            self.assertEqual(s.dimensions(dict(unit='cm',height=1.1,dpi=96))['size'][1],42)
            self.assertEqual(s.dimensions(dict(unit='px',width=42.5,height=20.5,dpi=96))['size'],[43,21])
            for value in ['NaN',0,-1,'Infinity',100000]:
                with self.assertRaises(ValueError):s.dimensions(dict(unit='px',width=value,height=20,dpi=96))
            before=np.asarray(s.result).copy()
            s.export(Path(folder)/'custom.png','png',dict(unit='px',width=100,height=200,dpi=96))
            self.assertTrue(np.array_equal(before,np.asarray(s.result)))
            with Image.open(Path(folder)/'custom.png') as im:
                box=im.getbbox();self.assertLess(box[3]-box[1],100)

    def test_export_dpi_accuracy(self):
        s=Session()
        s.result=Image.new('RGBA',(180,104))
        s.result.paste((0,0,0,180),(2,2,180,102))
        s.result.paste((0,0,0,0),(30,20,140,80))
        with tempfile.TemporaryDirectory(dir=ROOT/'.local-tests') as folder:
            for dpi in (72,96,300):
                config=dict(unit='cm',height=1.1,dpi=dpi)
                expected=s.dimensions(config)
                if dpi==96:self.assertEqual(expected['size'],[74,42])
                for kind in ('png','gif'):
                    target=Path(folder)/('accuracy.'+kind)
                    r=s.export(target,kind,config)
                    with Image.open(target) as im:
                        self.assertEqual(list(im.size),expected['size'])
                        self.assertEqual(r['size'],list(im.size))
                        alpha=np.asarray(im.convert('RGBA'))[...,3]
                        if kind=='png':
                            self.assertTrue(((alpha>0)&(alpha<255)).any())
                            for value in im.info['dpi']:self.assertAlmostEqual(value,dpi,delta=.0128)
                        else:
                            self.assertEqual(set(np.unique(alpha)),{0,255})
                            self.assertIsNone(r['dpi'])

    def test_bridge_rejects_duplicate(self):
        bridge=Bridge(None);bridge._session=Session();bridge._session.lock.acquire()
        try:self.assertFalse(bridge.process_image()['ok'])
        finally:bridge._session.lock.release()

if __name__=='__main__':unittest.main()
