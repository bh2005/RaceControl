#!/usr/bin/env python3
"""
RaceControl Pro – ELV LSU200 Linux USB-Client (pyusb / libusb)

Kommuniziert direkt per USB-Bulk-Transfer mit der LSU200.
Kein virtueller COM-Port, kein ELV-Treiber nötig.
USB-UART-Chip intern: Silicon Labs CP2102N (VID 18ef PID e02c mit ELV-eigener ID).

Voraussetzungen:
    sudo apt install libusb-1.0-0 python3-usb python3-dotenv python3-websocket

udev-Regel (einmalig, damit kein root nötig ist):
    echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="18ef", ATTRS{idProduct}=="e02c", MODE="0666", GROUP="plugdev"' \
         | sudo tee /etc/udev/rules.d/99-lsu200.rules
    sudo udevadm control --reload-rules && sudo udevadm trigger

Benutzer zur Gruppe hinzufügen (einmalig, dann neu anmelden):
    sudo usermod -aG plugdev $USER

Starten:
    python lsu200_linux_client.py

License: GNU General Public License v2
Author : bh2005
"""

import atexit
import json
import os
import signal
import struct
import sys
import time
import threading
import usb.core
import usb.util
import websocket
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()  # liest .env aus dem aktuellen Verzeichnis (optional)

# ── Konfiguration ─────────────────────────────────────────────────────────────
# Reihenfolge: 1. .env-Datei  2. Umgebungsvariable  3. Hardcoded hier

USB_VID = 0x18ef
USB_PID = 0xe02c

EP_OUT = 0x02   # Bulk OUT – Befehle an LSU200
EP_IN  = 0x82   # Bulk IN  – Antworten von LSU200

# CP2102N USB-UART-Chip Initialisierung (Silicon Labs)
_CP210X_IFC_ENABLE   = 0x00
_CP210X_SET_BAUDRATE = 0x1E
_CP210X_SET_LINE_CTL = 0x03
_CP210X_H2I = 0x41   # bmRequestType: Vendor, Host→Interface
_SERIAL_BAUD = 19200

TIMING_API_KEY = os.getenv("TIMING_API_KEY", "")   # Admin → System → Lichtschranken-Schlüssel
BACKEND_WS     = os.getenv("BACKEND_WS", "ws://localhost:1980/ws/timing") + \
                 (f"?key={TIMING_API_KEY}" if TIMING_API_KEY else "")

MIN_TIME    = 3.0    # Messungen kürzer als MIN_TIME Sekunden ignorieren
POLL_MS     = 100    # Abfrageintervall in Millisekunden
HEARTBEAT_S = 5      # Heartbeat-Intervall in Sekunden
USB_TIMEOUT = 2000   # USB read/write Timeout in Millisekunden
LOG_FILE    = Path(__file__).parent / "lsu200.log"
LOG_MAX     = 100    # maximale Anzahl Log-Einträge

# ── Logging ───────────────────────────────────────────────────────────────────

_log_lock = threading.Lock()

def _log(event: str, detail: str = "") -> None:
    ts   = time.strftime("%Y-%m-%dT%H:%M:%S")
    line = f"{ts}\t{event}\t{detail}\n"
    with _log_lock:
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line)
            # Auf die letzten LOG_MAX Zeilen kürzen
            text = LOG_FILE.read_text(encoding="utf-8").splitlines(keepends=True)
            if len(text) > LOG_MAX:
                LOG_FILE.write_text("".join(text[-LOG_MAX:]), encoding="utf-8")
        except Exception:
            pass


# ── Interne State-Variablen ───────────────────────────────────────────────────

_ws_conn      = None
_ws_lock      = threading.Lock()
_last_hb_sent = 0.0
_current_dev  = None   # aktives USB-Device – für sauberes Cleanup
_dev_lock     = threading.Lock()


# ── Cleanup (Signal/atexit) ───────────────────────────────────────────────────

def _cleanup():
    global _current_dev
    with _dev_lock:
        dev = _current_dev
        _current_dev = None
    if dev is not None:
        try:
            usb.util.release_interface(dev, 0)
            usb.util.dispose_resources(dev)
        except Exception:
            pass
    _log("SHUTDOWN")

def _signal_handler(sig, frame):
    print("\n[RC] Beende …")
    _cleanup()
    sys.exit(0)

atexit.register(_cleanup)
signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT,  _signal_handler)


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _open_device():
    """Öffnet die LSU200 per libusb inkl. CP2102N-Initialisierung."""
    dev = usb.core.find(idVendor=USB_VID, idProduct=USB_PID)
    if dev is None:
        return None

    # Kernel-Treiber bedingungslos freigeben (fängt auch usbfs-Reste)
    try:
        dev.detach_kernel_driver(0)
    except usb.core.USBError:
        pass   # kein Treiber gebunden – ok

    try:
        dev.set_configuration()
    except usb.core.USBError as e:
        if e.errno != 16:   # EBUSY = bereits konfiguriert, weitermachen
            print(f"[LSU200] set_configuration Fehler: {e}")
            return None

    usb.util.claim_interface(dev, 0)

    # CP2102N initialisieren: UART enable + Baudrate setzen
    try:
        dev.ctrl_transfer(_CP210X_H2I, _CP210X_IFC_ENABLE,   0x0001, 0, None, 1000)
        dev.ctrl_transfer(_CP210X_H2I, _CP210X_SET_BAUDRATE,  0,      0,
                          struct.pack('<I', _SERIAL_BAUD), 1000)
        dev.ctrl_transfer(_CP210X_H2I, _CP210X_SET_LINE_CTL,  0x0800, 0, None, 1000)
    except usb.core.USBError as e:
        print(f"[LSU200] CP2102N Init-Fehler: {e}")
        _close_device(dev)
        return None

    return dev


def _close_device(dev):
    """Gibt Interface und Gerät sauber frei."""
    try:
        usb.util.release_interface(dev, 0)
        usb.util.dispose_resources(dev)
    except Exception:
        pass


def _parse_time(time_str: str) -> float | None:
    """
    Wandelt 'HH:MM:SS:mmm' in Dezimal-Sekunden um.
    Beispiel: '00:01:23:456' → 83.456
    """
    try:
        parts = time_str.strip().replace(",", ":").split(":")
        if len(parts) < 3:
            return None
        h  = int(parts[0])
        m  = int(parts[1])
        s  = int(parts[2])
        ms = int(parts[3]) if len(parts) > 3 else 0
        return h * 3600 + m * 60 + s + ms / 1000.0
    except (ValueError, IndexError):
        return None


def _send_ws(payload: dict):
    """Sendet JSON ans Backend; schweigt wenn nicht verbunden."""
    with _ws_lock:
        conn = _ws_conn
    if conn is not None:
        try:
            conn.send(json.dumps(payload))
        except Exception:
            pass


# ── USB Lese-Thread ───────────────────────────────────────────────────────────

def _usb_thread():
    global _last_hb_sent, _current_dev
    last_state = -1

    while True:
        print("[LSU200] Suche Gerät (VID=18ef PID=e02c) …")
        dev = _open_device()

        if dev is None:
            print("[LSU200] Gerät nicht gefunden – retry in 5 s")
            print("         Tipp: udev-Regel prüfen oder als root starten")
            time.sleep(5)
            continue

        with _dev_lock:
            _current_dev = dev
        print("[LSU200] Gerät gefunden und geöffnet")
        _log("USB_CONNECTED", "LSU200 geöffnet")
        last_state = -1

        try:
            while True:
                now = time.time()

                # ── Status abfragen ───────────────────────────────────────────
                dev.write(EP_OUT, b"w", timeout=USB_TIMEOUT)
                raw_bytes = dev.read(EP_IN, 64, timeout=USB_TIMEOUT)
                raw = bytes(raw_bytes).decode("ascii", errors="ignore").strip()

                if ";" in raw:
                    state_str, time_str = raw.split(";", 1)
                    try:
                        current_state = int(state_str.strip())
                    except ValueError:
                        current_state = -1

                    # Übergang Running(1) → Stopped(0) = Messung abgeschlossen
                    if last_state == 1 and current_state == 0:
                        elapsed = _parse_time(time_str)
                        if elapsed is not None and elapsed >= MIN_TIME:
                            print(f"[LSU200] Neue Zeit: {elapsed:.3f} s")
                            _log("MESSUNG", f"{elapsed:.3f}")
                            _send_ws({
                                "type":     "timing_result",
                                "raw_time": round(elapsed, 3),
                                "device":   "lsu200-usb",
                            })
                        elif elapsed is not None:
                            print(f"[LSU200] Messung verworfen ({elapsed:.3f} s < {MIN_TIME} s)")
                            _log("VERWORFEN", f"{elapsed:.3f} (< {MIN_TIME} s)")

                    last_state = current_state

                # ── Heartbeat ─────────────────────────────────────────────────
                if now - _last_hb_sent >= HEARTBEAT_S:
                    _send_ws({"type": "timing_device_heartbeat"})
                    _last_hb_sent = now

                time.sleep(POLL_MS / 1000)

        except usb.core.USBError as e:
            print(f"[LSU200] USB-Fehler: {e} – retry in 5 s")
            _log("USB_ERROR", str(e))
            last_state = -1
        finally:
            with _dev_lock:
                _current_dev = None
            _close_device(dev)
            _log("USB_DISCONNECTED")

        time.sleep(5)


# ── WebSocket-Thread ──────────────────────────────────────────────────────────

def _ws_on_open(ws):
    global _ws_conn
    with _ws_lock:
        _ws_conn = ws
    print(f"[WS] Verbunden mit {BACKEND_WS}")
    _log("WS_CONNECTED", BACKEND_WS)


def _ws_on_message(ws, message):
    try:
        data = json.loads(message)
        print(f"[WS] ← {data}")
    except Exception:
        pass


def _ws_on_error(ws, error):
    print(f"[WS] Fehler: {error}")
    _log("WS_ERROR", str(error))


def _ws_on_close(ws, *args):
    global _ws_conn
    with _ws_lock:
        _ws_conn = None
    print("[WS] Getrennt – reconnect in 3 s …")
    _log("WS_DISCONNECTED")


def _ws_thread():
    while True:
        try:
            ws = websocket.WebSocketApp(
                BACKEND_WS,
                on_open=_ws_on_open,
                on_message=_ws_on_message,
                on_error=_ws_on_error,
                on_close=_ws_on_close,
            )
            ws.run_forever(ping_interval=10, ping_timeout=5)
        except Exception as e:
            print(f"[WS] run_forever Fehler: {e}")
        time.sleep(3)


# ── Start ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    threading.Thread(target=_ws_thread, daemon=True, name="ws").start()
    threading.Thread(target=_usb_thread, daemon=True, name="usb").start()

    print("=" * 50)
    print("  RaceControl Pro – ELV LSU200 Linux-Client")
    print("=" * 50)
    print(f"  USB     : {USB_VID:04x}:{USB_PID:04x}")
    print(f"  Backend : {BACKEND_WS}")
    print(f"  Min-Zeit: {MIN_TIME} s")
    print("  Ctrl+C zum Beenden")
    print("=" * 50)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[RC] Beende …")
