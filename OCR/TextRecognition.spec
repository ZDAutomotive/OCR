# -*- mode: python -*-

block_cipher = None


a = Analysis(['Texterkennung.py'],
             pathex=['C:\\Users\\ZD\\OCR\\OCR'],
             binaries=[],
             datas=[],
             hiddenimports=["'PIL._tkinter_finder'"],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='TextRecognition',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
