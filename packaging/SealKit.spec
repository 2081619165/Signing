# 手动运行：python -m PyInstaller --clean --noconfirm packaging/SealKit.spec
from pathlib import Path
from PyInstaller.utils.hooks import collect_all
root=Path(SPECPATH).parent
assets=[(str(root/'app/static'),'static'),(str(root/'app/crop/index.html'),'crop'),(str(root/'app/crop/main.js'),'crop'),(str(root/'app/assets'),'assets'),(str(root/'app/licenses'),'licenses')]
binaries=[];hidden=['webview.platforms.winforms','webview.platforms.edgechromium','clr','bottle']
for package in ('webview','pythonnet','clr_loader'):
    data,libs,imports=collect_all(package)
    assets+=data;binaries+=libs;hidden+=imports
analysis=Analysis([str(root/'app/main.py')],pathex=[str(root/'app')],binaries=binaries,datas=assets,hiddenimports=hidden,excludes=['tkinter','PyQt5','PyQt6','PySide2','PySide6'])
pyz=PYZ(analysis.pure)
exe=EXE(pyz,analysis.scripts,analysis.binaries,analysis.datas,[],name='SealKit',console=False,debug=False,strip=False,upx=False,icon=str(root/'app/assets/sealkit.ico'))
