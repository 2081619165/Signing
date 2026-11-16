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
from processing import Session, gif_image, gif_quality
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

    def test_faint_gif_and_png_success(self):
        s=Session();s.load('faint.png',self.sample(170));s.process()
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'existing.gif';p.write_bytes(b'existing')
            s.export(p,'gif')
            self.assertNotEqual(p.read_bytes(),b'existing')
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

    def test_gif_faint_lines_and_quality_guard(self):
        im=Image.new('RGBA',(36,42));d=ImageDraw.Draw(im)
        for y,a in ((5,24),(15,50),(25,100)):
            d.line((3,y,32,y),fill=(0,0,0,a),width=1)
        im.putpixel((1,40),(0,0,0,2))
        pal,report=gif_image(im)
        a=np.asarray(im)[...,3];mask=np.asarray(pal)>0
        self.assertTrue(mask[5,3:33].all())
        self.assertFalse(mask[40,1])
        self.assertEqual(pal.size,(36,42))
        self.assertLess(int((a>=128).sum()),int(mask.sum()))
        with self.assertRaisesRegex(ValueError,'丢失大量'):gif_quality(a,a>=128)
        with tempfile.TemporaryDirectory(dir=ROOT/'.local-tests') as folder:
            target=Path(folder)/'faint.gif';pal.save(target,transparency=0)
            with Image.open(target) as read:
                self.assertTrue(np.array_equal(np.asarray(read.convert('RGBA'))[...,3]>0,mask))
        s=Session();s.result=im.copy();s.result.putpixel((0,0),(0,0,0,255))
        with tempfile.TemporaryDirectory(dir=ROOT/'.local-tests') as folder:
            p=Path(folder)/'keep.gif';p.write_bytes(b'existing')
            from unittest.mock import patch
            with patch('processing.gif_image',return_value=(Image.new('P',im.size),{})):
                with self.assertRaises(ValueError):s.export(p,'gif',dict(unit='px',width=36,height=42))
            self.assertEqual(p.read_bytes(),b'existing')

    def test_crop_uses_imported_original(self):
        s=Session();s.load('input.png',self.sample());full=np.asarray(s.full).copy()
        s.process();s.crop([10.2,20.3,100.1,90.1])
        self.assertEqual(s.original.size,(91,71));self.assertIsNone(s.result)
        s.crop([200,0,300,100])
        self.assertTrue(np.array_equal(np.asarray(s.original),full[0:100,200:300]))
        before=s.original.copy()
        for box in ([0,0,1,1],[-1,0,20,20],[0,0,500,20],[0,0,float('nan'),20]):
            with self.assertRaises(ValueError):s.crop(box)
            self.assertTrue(np.array_equal(np.asarray(before),np.asarray(s.original)))
        s.load('new.png',self.sample());self.assertIsNone(s.crop_box)

    def test_ink_enhancement_levels(self):
        from sharpen import sharpen
        base=Image.new('RGBA',(100,40));d=ImageDraw.Draw(base)
        d.line((5,10,90,10),fill=(0,0,0,24),width=1)
        d.line((5,20,90,20),fill=(0,0,0,100),width=1)
        base.putpixel((1,1),(0,0,0,8));old=np.asarray(base)
        previous=old[...,3]
        for level in ('off','light','standard','strong'):
            result,report=sharpen(base,level);a=np.asarray(result)[...,3]
            self.assertTrue(np.array_equal(a>0,old[...,3]>0))
            self.assertTrue((a>=previous).all());self.assertEqual(a[1,1],8)
            if level=='off':self.assertTrue(np.array_equal(np.asarray(result),old))
            else:self.assertGreater(a[10,10],previous[10,10])
            previous=a
        self.assertTrue(np.array_equal(np.asarray(base),old))

    def test_classification_and_color_exports(self):
        from algorithm import classify
        for color in ((210,30,40),(30,60,210)):
            image=Image.new('RGB',(200,160),'white');d=ImageDraw.Draw(image)
            d.ellipse((30,20,170,140),outline=color,width=5)
            self.assertEqual(classify(image)['type'],'color_seal')
            b=io.BytesIO();image.save(b,format='PNG');s=Session()
            self.assertEqual(s.load('seal.png',b.getvalue())['classification']['type'],'color_seal')
            s.process();a=np.asarray(s.result)
            self.assertTrue(((a[...,3]>0)&(a[...,3]<255)).any())
            with tempfile.TemporaryDirectory(dir=ROOT/'.local-tests') as folder:
                for kind in ('png','gif'):
                    p=Path(folder)/('exported_seal.'+kind);s.export(p,kind,dict(unit='px',width=100,height=100))
                    with Image.open(p) as read:
                        pixels=np.asarray(read.convert('RGBA'));ink=pixels[pixels[...,3]>0,:3]
                        self.assertGreater(float(np.abs(ink[:,0].astype(float)-ink[:,2]).mean()),30)
                        self.assertEqual(read.size,(100,100))
            d.line((20,150,180,150),fill='black',width=5)
            self.assertEqual(classify(image)['type'],'color_seal')
        page=Image.new('RGB',(400,560),'white');d=ImageDraw.Draw(page)
        for y in range(30,530,40):d.line((20,y,370,y),fill='black',width=2)
        self.assertEqual(classify(page)['type'],'uncertain')
        b=io.BytesIO();page.save(b,format='PNG');s=Session();s.load('page.png',b.getvalue())
        with self.assertRaises(ValueError):s.process()
        self.assertEqual(s.crop([0,20,390,40])['classification']['type'],'black_signature')

    def test_gray_seal_and_manual_safety(self):
        from algorithm import classify
        for bg,color in ((180,(160,20,30)),(255,(25,60,190))):
            im=Image.new('RGB',(200,160),(bg,)*3);d=ImageDraw.Draw(im)
            d.rectangle((25,25,175,135),outline=color,width=5)
            d.line((0,150,199,150),fill=(60,)*3,width=2)
            self.assertEqual(classify(im)['type'],'color_seal')
            b=io.BytesIO();im.save(b,format='PNG');s=Session();s.load('input.png',b.getvalue());s.process()
            a=np.asarray(s.result)
            self.assertEqual(a[0,0,3],0);self.assertEqual(a[150,10,3],0)
            self.assertGreater(a[25,50,3],0)
        for im in (Image.new('RGB',(100,100),'white'),Image.fromarray(np.random.default_rng(42).integers(0,256,(100,100,3),dtype=np.uint8))):
            b=io.BytesIO();im.save(b,format='PNG');s=Session();s.load('input.png',b.getvalue())
            for kind in ('black_signature','color_seal'):
                with self.assertRaises(ValueError):s.process(kind=kind)
        im=Image.new('RGB',(200,160),'white');d=ImageDraw.Draw(im)
        d.ellipse((30,20,170,120),outline=(200,20,30),width=4)
        d.rectangle((10,130,190,150),fill='black')
        b=io.BytesIO();im.save(b,format='PNG');s=Session();s.load('input.png',b.getvalue());s.process(kind='color_seal')
        self.assertIsNotNone(s.result)

    def test_pale_seal_and_blue_composite(self):
        from algorithm import classify,extract_color
        for color in ((180,190,220),(220,185,185)):
            im=Image.new('RGB',(220,180),(190,)*3)
            ImageDraw.Draw(im).ellipse((30,20,190,160),outline=color,width=4)
            self.assertEqual(classify(im)['type'],'color_seal')
        im=Image.new('RGB',(120,80),'white')
        ImageDraw.Draw(im).line((10,40,110,40),fill=(100,130,200),width=3)
        im.putpixel((20,20),(220,230,250))
        result=extract_color(im);a=np.asarray(result)
        back=Image.new('RGBA',im.size,'white');back.alpha_composite(result)
        for x,y in ((40,40),(20,20)):
            self.assertTrue(np.all(np.abs(np.array(back.getpixel((x,y))[:3])-np.array(im.getpixel((x,y))))<=1))
        self.assertEqual(a[0,0,3],0)
        red=Image.new('RGB',(10,10),(160,20,30));r=np.asarray(extract_color(red))[0,0]
        normalized=np.array((160,20,30))/160
        alpha=1-normalized.min()
        expected=np.rint(np.r_[np.clip((normalized-(1-alpha))/alpha,0,1)*255,alpha*255]).astype('uint8')
        self.assertTrue(np.array_equal(r,expected))

    def test_bridge_rejects_duplicate(self):
        bridge=Bridge(None);bridge._session=Session();bridge._session.lock.acquire()
        try:self.assertFalse(bridge.process_image()['ok'])
        finally:bridge._session.lock.release()

if __name__=='__main__':unittest.main()
