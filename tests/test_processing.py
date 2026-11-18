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

    def test_transparent_rotation_before_export(self):
        s=Session();s.load('input.png',self.sample());s.process()
        base=s.result.copy();original=np.asarray(s.original).copy()
        for angle in (-45,-13.2,0,25,45):
            s.rotate_result(angle)
            expected=base.rotate(angle,resample=Image.Resampling.BICUBIC,expand=True,fillcolor=(0,0,0,0)) if angle else base
            self.assertTrue(np.array_equal(np.asarray(s.result),np.asarray(expected)))
            self.assertTrue(np.array_equal(np.asarray(s.original),original))
            self.assertTrue((np.asarray(s.result)[...,3]==0).any())
        with tempfile.TemporaryDirectory(dir=ROOT/'.local-tests') as folder:
            for kind in ('png','gif'):s.export(Path(folder)/('rotated.'+kind),kind,dict(unit='px',width=80,height=60))
        s.rotate_result(0);self.assertTrue(np.array_equal(np.asarray(s.result),np.asarray(base)))
        for angle in (46,float('nan'),True):
            with self.assertRaises(ValueError):s.rotate_result(angle)
        s.process();self.assertEqual(s.rotation,0)
        s.load('new.png',self.sample());self.assertIsNone(s.base_result)
        with self.assertRaises(ValueError):s.rotate_result(10)

    def test_local_color_background_and_fallback(self):
        from algorithm import extract_color,extract_color_baseline
        for color in ((180,25,35),(60,90,190)):
            im=Image.new('RGB',(200,160),'white');ImageDraw.Draw(im).ellipse((25,20,175,140),outline=color,width=3)
            result,report=extract_color(im,local=True,with_report=True)
            self.assertTrue(np.array_equal(np.asarray(result),np.asarray(extract_color_baseline(im))))
        im=Image.new('RGB',(200,160),(210,)*3);ImageDraw.Draw(im).ellipse((25,20,175,140),outline=(206,202,202),width=2)
        result,report=extract_color(im,local=True,with_report=True)
        self.assertEqual(report['method'],'local_background')
        a=np.asarray(result)[...,3];self.assertEqual(a[0,0],0);self.assertGreater(a[20,100],0)
        b=io.BytesIO();im.save(b,format='PNG');session=Session();session.load('input.png',b.getvalue());session.crop([0,0,200,160]);session.process(kind='color_seal')
        noise=Image.fromarray(np.random.default_rng(12).integers(0,256,(100,100,3),dtype=np.uint8))
        result,report=extract_color(noise,local=True,with_report=True)
        self.assertEqual(report['method'],'baseline')

    def test_color_failure_diagnostics(self):
        from algorithm import extract_color
        import json
        image=Image.new('RGB',(80,80),(210,)*3)
        ImageDraw.Draw(image).ellipse((10,10,70,70),outline=(206,202,202),width=2)
        b=io.BytesIO();image.save(b,format='PNG');session=Session();session.load('input.png',b.getvalue())
        logs=[]
        def record(event,**data):logs.append(dict(event=event,**data))
        session.process(kind='color_seal',diagnostic=record)
        validation=next(r for r in logs if r['stage']=='validation')
        self.assertEqual(validation['failed_conditions'],[])
        extraction=next(r for r in logs if r['stage']=='extraction')
        self.assertEqual(extraction['report']['method'],'local_background')
        self.assertNotIn('data:image',json.dumps(logs))
        session.crop([0,0,80,80]);logs.clear();session.process(kind='color_seal',diagnostic=record)
        extraction=next(r for r in logs if r['stage']=='extraction')
        self.assertTrue(extraction['report']['local_requested'])
        self.assertIn('confidence_checks',extraction['report'])
        self.assertEqual(logs[-1]['stage'],'success')

    def test_large_import_preview_and_native_crop(self):
        from processing import LargeSource
        image=Image.new('RGB',(4000,5100),'white')
        ImageDraw.Draw(image).rectangle((100,200,149,249),fill=(180,20,30))
        b=io.BytesIO();image.save(b,format='PNG');data=b.getvalue();image.close()
        session=Session();reply=session.load('large.png',data)
        self.assertIsInstance(session.full,LargeSource)
        self.assertEqual(session.full.size,(4000,5100))
        self.assertLessEqual(max(session.original.size),1600)
        self.assertFalse(session.requires_crop)
        self.assertNotIn('先框选',reply['classification']['reason'])
        self.assertEqual(session.validate_crop([0,0,3000,3000]),(0,0,3000,3000))
        session.crop([100,200,150,250]);self.assertEqual(session.original.size,(50,50))
        self.assertEqual(session.original.getpixel((10,10)),(180,20,30))
        self.assertFalse(session.requires_crop)
        self.assertEqual(session.full.size,(4000,5100))

    def test_large_exif_coordinates_and_decode_guard(self):
        from unittest.mock import patch,MagicMock
        image=Image.new('RGB',(5100,4000),'white')
        ImageDraw.Draw(image).rectangle((0,0,99,99),fill=(20,60,190))
        exif=Image.Exif();exif[274]=6;b=io.BytesIO();image.save(b,format='JPEG',exif=exif,quality=95);image.close()
        session=Session();session.load('rotated.jpg',b.getvalue())
        self.assertEqual(session.full.size,(4000,5100))
        session.crop([3900,0,4000,100])
        r,g,blue=session.original.getpixel((50,50));self.assertGreater(blue,r+100)
        raw=MagicMock();raw.format='PNG';raw.width=10000;raw.height=6000
        with patch('processing.Image.open') as opened:
            opened.return_value.__enter__.return_value=raw
            with self.assertRaisesRegex(ValueError,'预算'):Session().load('huge.png',b'header')
            raw.load.assert_not_called()

    def test_large_crop_bridge_then_extract_and_cancel(self):
        from unittest.mock import patch
        from processing import LargeSource
        image=Image.new('RGB',(4000,5100),'white')
        ImageDraw.Draw(image).ellipse((110,210,290,390),outline=(180,25,35),width=4)
        stream=io.BytesIO();image.save(stream,format='PNG');image.close()
        bridge=Bridge(None);bridge._session=Session();session=bridge._session
        session.load('large.png',stream.getvalue())
        before=session.original
        with patch('crop.activate_existing',return_value=False),patch('crop.select',return_value=None):
            self.assertTrue(bridge.select_region()['cancelled'])
        self.assertFalse(session.requires_crop);self.assertIs(session.original,before)
        def confirm(*args,**kwargs):
            self.assertEqual(kwargs['validate']([0,0,3000,3000]),(0,0,3000,3000))
            self.assertFalse(session.requires_crop);self.assertIs(session.original,before)
            kwargs['validate']([100,200,300,400])
            return [100,200,300,400]
        with patch('crop.activate_existing',return_value=False),patch('crop.select',side_effect=confirm):
            reply=bridge.select_region()
        self.assertTrue(reply['ok']);self.assertFalse(reply['requires_crop'])
        self.assertFalse(session.requires_crop);self.assertEqual(session.original.size,(200,200))
        self.assertTrue(bridge.process_image('off','color_seal')['ok'])
        session.crop([105,205,295,395]);self.assertEqual(session.original.size,(190,190))
        self.assertFalse(session.requires_crop);self.assertIsInstance(session.full,LargeSource)
        session.load('new.png',stream.getvalue())
        self.assertFalse(session.requires_crop);self.assertFalse(session.whole_work_ready);self.assertIsNone(session.crop_box)

    def test_crop_response_failure_does_not_commit(self):
        from unittest.mock import patch
        session=Session();session.load('input.png',self.sample());session.process()
        before=session.original;result=session.result
        with patch('processing.preview',side_effect=RuntimeError('mock preview failure')):
            with self.assertRaises(RuntimeError):session.crop([10,10,100,100])
        self.assertIs(session.original,before);self.assertIs(session.result,result)
        self.assertIsNone(session.crop_box)

    def test_2493mp_full_blue_seal_workflow(self):
        from unittest.mock import patch
        from processing import MAX_WORK_PIXELS,MAX_WORK_SIDE
        size=(5855,4258)
        image=Image.new('RGB',size,'white');draw=ImageDraw.Draw(image)
        draw.ellipse((30,30,size[0]-30,size[1]-30),outline=(35,75,185),width=40)
        draw.line((800,2000,5000,2000),fill=(35,75,185),width=20)
        stream=io.BytesIO();image.save(stream,format='PNG');image.close()
        bridge=Bridge(None);bridge._session=Session();session=bridge._session
        session.load('large-seal.png',stream.getvalue())
        # 不框选直接处理：从完整原图生成工作图，第二次处理复用缓存。
        with patch.object(session.full,'crop',wraps=session.full.crop) as build:
            direct=bridge.process_image('off','color_seal')
            self.assertTrue(direct['ok'],direct)
            self.assertTrue(bridge.process_image('off','color_seal')['ok'])
            self.assertEqual(build.call_count,1)
            self.assertEqual(build.call_args.args[0],(0,0,*size))
            self.assertIsNone(session.crop_box)
            self.assertLessEqual(session.original.width*session.original.height,MAX_WORK_PIXELS)
        def confirm(*args,**kwargs):
            box=[0,0,*size];kwargs['validate'](box);return box
        with patch('crop.activate_existing',return_value=False),patch('crop.select',side_effect=confirm):
            reply=bridge.select_region()
        self.assertTrue(reply['ok'],reply)
        self.assertEqual(reply['source_crop_size'],list(size))
        self.assertEqual(session.crop_box,[0,0,*size])
        self.assertLessEqual(session.original.width*session.original.height,MAX_WORK_PIXELS)
        self.assertLessEqual(max(session.original.size),MAX_WORK_SIDE)
        self.assertFalse(session.requires_crop)
        result=bridge.process_image('off','color_seal');self.assertTrue(result['ok'],result)
        self.assertTrue((np.asarray(session.result)[...,3]==0).any())
        with tempfile.TemporaryDirectory(dir=ROOT/'.local-tests') as folder:
            for kind in ('png','gif'):
                path=Path(folder)/('complete.'+kind)
                session.export(path,kind,dict(unit='px',width=180,height=130,dpi=96))
                with Image.open(path) as exported:self.assertEqual(exported.size,(180,130))
        session.crop([800,1980,1000,2040]);self.assertEqual(session.original.size,(200,60))

    def test_memory_failure_is_reported_without_corrupting_crop(self):
        from unittest.mock import patch
        session=Session();session.load('input.png',self.sample());before=session.original
        with patch.object(session.full,'crop',side_effect=MemoryError):
            with self.assertRaisesRegex(ValueError,'内存不足'):session.crop([0,0,100,100])
        self.assertIs(session.original,before);self.assertIsNone(session.crop_box)
        bridge=Bridge(None);bridge._session=session
        self.assertIn('内存不足',bridge._run(lambda:(_ for _ in ()).throw(MemoryError()))['error'])

    def test_pink_textured_shadow_seals(self):
        from algorithm import extract_color,extract_color_baseline
        h,w=180,240;y,x=np.mgrid[:h,:w]
        texture=np.random.default_rng(6).normal(0,1,(h,w,1))
        paper=np.array((225,210,215))[None,None,:]-x[...,None]*.08+texture
        mask=Image.new('L',(w,h));d=ImageDraw.Draw(mask)
        d.ellipse((25,20,215,160),outline=255,width=3);d.line((60,90,180,90),fill=255,width=1)
        truth=np.asarray(mask)>0
        for color in ((180,30,45),(35,65,185)):
            pixels=paper.copy();pixels[truth]=paper[truth]*.7+np.array(color)*.3
            image=Image.fromarray(np.clip(pixels,0,255).astype('uint8'))
            result,report=extract_color(image,local=True,with_report=True)
            a=np.asarray(result)[...,3]
            self.assertEqual(report['method'],'local_background',report)
            self.assertGreater((a[truth]>0).mean(),.98)
            self.assertLess((a[~truth]>0).mean(),.03)
            b=io.BytesIO();image.save(b,format='PNG');session=Session();session.load('input.png',b.getvalue())
            session.process(kind='color_seal');self.assertIsNotNone(session.result)
        # 有纹理的偏色纸张本身不是印章，不应作为可用结果放行。
        blank=Image.fromarray(np.clip(paper,0,255).astype('uint8'));b=io.BytesIO();blank.save(b,format='PNG')
        session=Session();session.load('input.png',b.getvalue())
        with self.assertRaises(ValueError):session.process(kind='color_seal')

    def test_candidate_review_rejects_tinted_texture_without_subject(self):
        from algorithm import extract_color
        pixels=np.clip(np.array((225,213,216))+np.random.default_rng(52).normal(0,4,(180,240,3)),0,255).astype('uint8')
        image=Image.fromarray(pixels)
        result,report=extract_color(image,local=True,with_report=True)
        self.assertTrue(report['candidate_review_requested'])
        self.assertEqual(report['method'],'baseline')
        if 'candidate_review_checks' in report:
            self.assertFalse(all(report['candidate_review_checks'].values()))
        stream=io.BytesIO();image.save(stream,format='PNG');session=Session();session.load('texture.png',stream.getvalue())
        with self.assertRaises(ValueError):session.process(kind='color_seal')
        mild=Image.fromarray(np.clip(np.array((225,213,216))+np.random.default_rng(52).normal(0,2,(180,240,3)),0,255).astype('uint8'))
        _,report=extract_color(mild,local=True,with_report=True)
        self.assertEqual(report['reason'],'candidate_subject_failed')
        stream=io.BytesIO();mild.save(stream,format='PNG');session.load('mild.png',stream.getvalue())
        with self.assertRaises(ValueError):session.process(kind='color_seal')

    def test_optional_real_seal_candidate_review(self):
        import os
        path=os.environ.get('SEALKIT_REAL_SEAL_INPUT')
        if not path:self.skipTest('真实样本由本地环境变量提供，不提交客户图片')
        session=Session();session.load('private-input.png',Path(path).read_bytes())
        reply=session.process(kind='color_seal');report=reply['color_report']
        self.assertEqual(report['method'],'local_background')
        self.assertTrue(report['candidate_review_requested'])
        self.assertTrue(all(report['candidate_review_checks'].values()))
        self.assertLess(report['selected_alpha']['nonzero_fraction'],.5)
        self.assertLess(report['border_leakage'],.02)
        self.assertGreaterEqual(report['strong_retention'],.98)

    def test_bridge_rejects_duplicate(self):
        bridge=Bridge(None);bridge._session=Session();bridge._session.lock.acquire()
        try:self.assertFalse(bridge.process_image()['ok'])
        finally:bridge._session.lock.release()

if __name__=='__main__':unittest.main()
