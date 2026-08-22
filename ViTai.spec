# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/vitai/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[('assets', 'assets')],
    hiddenimports=[
        'pynput.keyboard._darwin',
        'pynput.mouse._darwin',
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
        'pynput.keyboard._xorg',
        'pynput.mouse._xorg',
        'ApplicationServices',
        'HIServices',
        'Quartz',
        'AppKit',
        'Cocoa',
        'objc',
        'certifi',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

import sys
import os

is_darwin = sys.platform == 'darwin'
use_upx = not is_darwin
entitlements_path = 'entitlements.plist' if is_darwin and os.path.exists('entitlements.plist') else None

exe_icon = ['assets/icon.ico'] if sys.platform == 'win32' else None
bundle_icon = 'assets/icon.icns' if os.path.exists('assets/icon.icns') else None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ViTai',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=use_upx,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=entitlements_path,
    icon=exe_icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=use_upx,
    upx_exclude=[],
    name='ViTai',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='ViTai.app',
        icon=bundle_icon,
        bundle_identifier='com.vitai.app',
        info_plist={
            'CFBundleName': 'ViTai',
            'CFBundleDisplayName': 'Vì Người Tài',
            'CFBundleIdentifier': 'com.vitai.app',
            'CFBundleVersion': '3.2.3',
            'CFBundleShortVersionString': '3.2.3',
            'NSHighResolutionCapable': 'True',
            'LSUIElement': '0',
            'NSRequiresAquaSystemAppearance': 'False',
            'NSSupportsAutomaticGraphicsSwitching': 'True',
            'NSAccessibilityUsageDescription': 'Vì Người Tài cần quyền Trợ năng để lắng nghe phím tắt và hiển thị đáp án.',
            'NSInputMonitoringUsageDescription': 'Vì Người Tài cần quyền Giám sát đầu vào để lắng nghe phím tắt giải đề.',
            'NSAppleEventsUsageDescription': 'Vì Người Tài cần quyền AppleEvents để tương tác phím tắt.',
        },
    )
