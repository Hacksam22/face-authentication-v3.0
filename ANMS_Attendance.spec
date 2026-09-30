# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_all

root = Path(SPECPATH)
ctk_datas, ctk_binaries, ctk_hiddenimports = collect_all("customtkinter")
datas = [
    (str(root / "database" / "schema.sql"), "database"),
    (str(root / "assets" / "app_logo.png"), "assets"),
    (str(root / "assets" / "app_logo.ico"), "assets"),
]
datas.extend(
    (str(cascade), "face_recognition/cascades")
    for cascade in (root / "face_recognition" / "cascades").glob("*.xml")
)
datas.extend(ctk_datas)

a = Analysis(
    [str(root / "main.py")],
    pathex=[str(root)],
    binaries=ctk_binaries,
    datas=datas,
    hiddenimports=["cv2.face", *ctk_hiddenimports],
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
    name="ANMS_Attendance",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon=str(root / "assets" / "app_logo.ico"),
)