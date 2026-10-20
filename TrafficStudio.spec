# -*- mode: python ; coding: utf-8 -*-
# Traffic Studio 2.0 — packaged shell over the V1 traffic engine

a = Analysis(
    ['traffic_studio.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['traffic_test_gui', 'traffic_diag'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Traffic Studio 2.0',
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
    icon='app_icon.ico',
)
