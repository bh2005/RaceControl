"""
RaceControl Pro – Windows Launcher

Startet den FastAPI-Backend-Server und öffnet automatisch den Browser.
Optionales System-Tray-Icon (erfordert pystray + Pillow).
"""
import sys
import os
import pathlib
import threading
import time
import webbrowser
import socket


# ── Pfade ──────────────────────────────────────────────────────────────────

def _bundle_root() -> pathlib.Path:
    """Temp-Verzeichnis mit entpackten PyInstaller-Dateien."""
    if getattr(sys, "frozen", False):
        return pathlib.Path(sys._MEIPASS)  # type: ignore[attr-defined]
    # Entwicklung: Projektverzeichnis (eine Ebene über Windows/)
    return pathlib.Path(__file__).resolve().parent.parent


def _persistent_root() -> pathlib.Path:
    """Schreibbares Verzeichnis neben der .exe (Installationsordner)."""
    if getattr(sys, "frozen", False):
        return pathlib.Path(sys.executable).parent
    return pathlib.Path(__file__).resolve().parent.parent


BUNDLE = _bundle_root()
PERSIST = _persistent_root()

# Backend-Quellcode in den Python-Suchpfad aufnehmen
sys.path.insert(0, str(BUNDLE / "backend"))

# Umgebungsvariablen für Backend setzen (vor jedem Import!)
# DATA_DIR: Ordner für racecontrol.db
# ASSETS_DIR: Ordner für hochgeladene Dokumente (Reglements etc.)
os.environ.setdefault("DATA_DIR",   str(PERSIST / "data"))
os.environ.setdefault("ASSETS_DIR", str(PERSIST / "assets"))

# Verzeichnisse anlegen (db + assets)
(PERSIST / "data").mkdir(parents=True, exist_ok=True)
(PERSIST / "assets").mkdir(parents=True, exist_ok=True)

# Jetzt Backend-Module importieren – PyInstaller trackt alle Abhängigkeiten
import main as _app_module  # noqa: E402  (import nach sys.path-Setup)

HOST = "0.0.0.0"
PORT = 1980
URL  = f"http://localhost:{PORT}"


# ── Server ──────────────────────────────────────────────────────────────────

def _run_server() -> None:
    import uvicorn
    uvicorn.run(
        _app_module.app,
        host=HOST,
        port=PORT,
        log_level="warning",
    )


def _wait_and_open_browser() -> None:
    """Wartet bis Port 1980 antwortet, öffnet dann den Browser."""
    for _ in range(60):          # max 30 Sekunden warten
        try:
            with socket.create_connection(("localhost", PORT), timeout=0.5):
                break
        except OSError:
            time.sleep(0.5)
    webbrowser.open(URL)


# ── System-Tray ─────────────────────────────────────────────────────────────

def _make_fallback_icon():
    """Generiert ein einfaches grünes Kreis-Icon (kein .ico nötig)."""
    from PIL import Image, ImageDraw  # type: ignore
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=(34, 197, 94, 255))
    return img


def _run_tray() -> None:
    import pystray  # type: ignore

    icon_path = pathlib.Path(__file__).parent / "icon.ico"
    if icon_path.exists():
        from PIL import Image  # type: ignore
        img = Image.open(str(icon_path))
    else:
        img = _make_fallback_icon()

    def on_open(_icon, _item):
        webbrowser.open(URL)

    def on_quit(icon, _item):
        icon.stop()
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem("RaceControl Pro öffnen", on_open, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Beenden", on_quit),
    )
    tray = pystray.Icon("RaceControl Pro", img, "RaceControl Pro", menu)
    tray.run()


def _blocking_fallback() -> None:
    print(f"\nRaceControl Pro läuft auf {URL}")
    print("Fenster schließen oder Strg+C drücken zum Beenden.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


# ── Hauptprogramm ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()

    threading.Thread(target=_wait_and_open_browser, daemon=True).start()

    try:
        import pystray  # noqa: F401
        _run_tray()
    except ImportError:
        _blocking_fallback()
