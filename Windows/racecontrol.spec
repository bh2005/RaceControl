# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller-Spec für RaceControl Pro (onedir-Build).

Ausgabe:  Windows/dist/racecontrol/
          └── racecontrol.exe  +  _internal/

Ausführen:
    cd Windows
    pyinstaller racecontrol.spec --noconfirm
"""
from pathlib import Path

PROJECT = Path(SPECPATH).parent           # .../RaceControl/
BACKEND = PROJECT / "backend"
FRONTEND_DIST = PROJECT / "frontend" / "dist"
ICON = Path(SPECPATH) / "icon.ico"

a = Analysis(
    [str(Path(SPECPATH) / "launcher.py")],
    pathex=[str(BACKEND)],                # damit PyInstaller `main` findet
    binaries=[],
    datas=[
        # Gebautes Vue-Frontend (muss vor PyInstaller-Lauf vorhanden sein)
        (str(FRONTEND_DIST), "frontend/dist"),
        # Backend-Quellcode (alle .py-Dateien)
        (str(BACKEND), "backend"),
        # schema.sql (wird von database.py beim Start gelesen)
        (str(PROJECT / "schema.sql"), "."),
    ],
    hiddenimports=[
        # uvicorn – lädt viele Teile dynamisch
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.loops.asyncio",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.protocols.websockets.websockets_impl",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "uvicorn.config",
        # starlette
        "starlette.routing",
        "starlette.middleware.cors",
        "starlette.staticfiles",
        "starlette.responses",
        "starlette.background",
        # passlib – bcrypt-Handler wird per String-Name geladen
        "passlib.handlers.bcrypt",
        "passlib.handlers.sha2_crypt",
        # jose / cryptography
        "jose",
        "jose.jwt",
        "jose.exceptions",
        "cryptography.hazmat.primitives.asymmetric.rsa",
        "cryptography.hazmat.backends.openssl",
        # pydantic v2
        "pydantic",
        "pydantic_core",
        "pydantic.deprecated.class_validators",
        # python-multipart
        "multipart",
        # aiosqlite / sqlite3
        "aiosqlite",
        "_sqlite3",
        # email-validator (falls passlib es nutzt)
        "email_validator",
        # pystray + Pillow (optional – System-Tray)
        "pystray",
        "PIL",
        "PIL.Image",
        "PIL.ImageDraw",
        # h11 (HTTP/1.1-Implementierung für uvicorn)
        "h11",
        # anyio / sniffio
        "anyio",
        "anyio.abc",
        "anyio._backends._asyncio",
        "sniffio",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "numpy",
        "scipy",
        "pandas",
        "pytest",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="racecontrol",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,          # True = Konsolenfenster (Logs sichtbar)
                           # False = kein Fenster (nur mit System-Tray sinnvoll)
    icon=str(ICON) if ICON.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="racecontrol",
)
