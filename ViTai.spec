# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

root_dir = os.path.abspath(SPECPATH)
icon_file = os.path.join(root_dir, 'assets', 'icon.ico')
icon_path = icon_file if os.path.exists(icon_file) else None

hidden_imports = ['certifi']
excludes = []

if sys.platform.startswith('win'):
    hidden_imports.extend([
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
    ])
    excludes.extend(['Xlib', 'evdev'])
else:
    hidden_imports.extend([
        'pynput.keyboard._xorg',
        'pynput.mouse._xorg',
    ])
    excludes.extend(['win32api', 'win32con', 'win32gui'])

a = Analysis(
    [os.path.join(root_dir, 'src', 'vitai', 'main.py')],
    pathex=[os.path.join(root_dir, 'src')],
    binaries=[],
    datas=[(os.path.join(root_dir, 'assets'), 'assets')],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ViTai',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ViTai',
)
