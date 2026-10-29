# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

APP_DIR = os.path.dirname(os.path.abspath(SPEC))

datas = [
    (os.path.join(APP_DIR, 'index.html'), 'app'),
    (os.path.join(APP_DIR, 'admin.html'), 'app'),
    (os.path.join(APP_DIR, 'favicon.ico'), 'app'),
    (os.path.join(APP_DIR, 'server.py'), 'app'),
    (os.path.join(APP_DIR, 'update_data.py'), 'app'),
    (os.path.join(APP_DIR, 'css'), 'app/css'),
    (os.path.join(APP_DIR, 'js'), 'app/js'),
    (os.path.join(APP_DIR, 'images'), 'app/images'),
    (os.path.join(APP_DIR, 'data'), 'app/data'),
]

hiddenimports = [
    'flask',
    'werkzeug',
    'werkzeug.serving',
    'jinja2',
    'markupsafe',
    'openpyxl',
    'PIL',
    'PIL.Image',
    'webview',
    'clr',
    'pythonnet',
    'clr_loader',
    'proxy_tools',
    'bottle',
]

excludes = [
    'PySide6', 'shiboken6', 'PySide2', 'PyQt5', 'PyQt6',
    'matplotlib', 'scipy', 'numpy', 'unittest', 'test'
]

a = Analysis(
    [os.path.join(APP_DIR, 'desktop_app.py')],
    pathex=[APP_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HoaSenHome',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(APP_DIR, 'favicon.ico'),
)
