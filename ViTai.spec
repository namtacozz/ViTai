# -*- mode: python ; coding: utf-8 -*-
import sys

a = Analysis(
    ['src/vitai/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[('assets', 'assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ViTai',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ViTai',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='ViTai.app',
        icon='assets/icon.ico',
        bundle_identifier='com.namtaco.vitai',
        info_plist={
            'CFBundleName': 'ViTai',
            'CFBundleDisplayName': 'Vì Người Tài',
            'CFBundleIdentifier': 'com.namtaco.vitai',
            'CFBundleVersion': '3.0.0',
            'CFBundleShortVersionString': '3.0.0',
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'NSAppleEventsUsageDescription': 'ViTai cần quyền AppleEvents để bắt phím tắt và đọc văn bản bôi đen.',
            'NSAccessibilityUsageDescription': 'ViTai cần quyền Accessibility (Trợ năng) để nhận diện phím tắt toàn cục và sự kiện chuột.',
        },
    )

