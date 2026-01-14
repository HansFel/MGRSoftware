# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('c:\\Users\\HTFel\\OneDrive\\Gemeinschaften\\Traktor\\MGRSoftware\\templates', 'templates'), ('c:\\Users\\HTFel\\OneDrive\\Gemeinschaften\\Traktor\\MGRSoftware\\static', 'static'), ('c:\\Users\\HTFel\\OneDrive\\Gemeinschaften\\Traktor\\MGRSoftware\\schema.sql', '.')]
binaries = []
hiddenimports = ['flask', 'sqlite3', 'werkzeug', 'jinja2', 'email_validator']
tmp_ret = collect_all('flask')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('werkzeug')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('jinja2')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['c:\\Users\\HTFel\\OneDrive\\Gemeinschaften\\Traktor\\MGRSoftware\\launcher.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    a.binaries,
    a.datas,
    [],
    name='Maschinengemeinschaft',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
