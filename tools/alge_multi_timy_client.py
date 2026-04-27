#!/usr/bin/env python3
"""
RaceControl Pro – ALGE Timy Multi-Client (Start + Ziel + weitere)

Unterstützt mehrere ALGE Timy Geräte gleichzeitig (z. B. Start-Timy + Finish-Timy).
Jedes Gerät kann über eigenen COM-Port und eigene Kanal-Zuordnung konfiguriert werden.

Abhängigkeiten:
    pip install -r requirements.txt

Konfiguration über .env oder direkt im Code.
"""

import json
import time
import threading
import re
import os
from pathlib import Path
import serial
import serial.tools.list_ports
import websocket
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

# ── Konfiguration ─────────────────────────────────────────────────────────────

BACKEND_WS = os.getenv("BACKEND_WS", "ws://localhost:1980/ws/timing")

# Liste der Timys – hier kannst du beliebig viele hinzufügen
TIMY_DEVICES = [
    {
        "name": "Start-Timy",
        "port": os.getenv("TIMY_START_PORT", None),      # z.B. "COM3" oder None
        "baudrate": int(os.getenv("TIMY_START_BAUD", 9600)),
        "channels": {"c0": "start", "c0m": "start_manual"},
        "color": "🔴"  # nur für schöne Logs
    },
    {
        "name": "Finish-Timy",
        "port": os.getenv("TIMY_FINISH_PORT", None),     # z.B. "COM4"
        "baudrate": int(os.getenv("TIMY_FINISH_BAUD", 9600)),
        "channels": {"c1": "finish", "c1m": "finish_manual"},
        "color": "🏁"
    },
    # Weiteres Timy hinzufügen, z.B. für Intermediate:
    # {
    #     "name": "Intermediate-Timy",
    #     "port": None,
    #     "baudrate": 9600,
    #     "channels": {"c2": "intermediate"},
    #     "color": "📍"
    # },
]

MIN_TIME = 3.0          # Minimale gültige Zeit in Sekunden
HEARTBEAT_S = 5

# ── Globale Variablen ─────────────────────────────────────────────────────────

_ws_conn = None
_ws_lock = threading.Lock()
_last_hb_sent = 0.0
_hb_lock = threading.Lock()


def _find_port(hint: str = "") -> str | None:
    """Sucht nach einem passenden COM-Port."""
    for p in serial.tools.list_ports.comports():
        desc = (p.description or "").upper()
        if hint.upper() in desc or "ALGE" in desc or "TIMY" in desc or "FTDI" in desc:
            return p.device
    return None


def _parse_alge_line(line: str) -> dict | None:
    """Parst ALGE Timy Zeilen."""
    line = line.strip().replace(',', '.')
    if not line:
        return None

    pattern = r'(?i)([a-z]?\s*)(\d{1,4})\s+(c[0-9m]+)\s+([\d:.]+)'
    match = re.search(pattern, line)
    if not match:
        return None

    bib = int(match.group(2))
    channel = match.group(3).lower()
    time_str = match.group(4)

    # Zeit parsen
    try:
        parts = re.split(r'[:.]', time_str)
        h = int(parts[0])
        m = int(parts[1])
        s = int(parts[2])
        ms = int(parts[3].ljust(3, '0')[:3]) if len(parts) > 3 else 0
        seconds = h * 3600 + m * 60 + s + ms / 1000.0
    except Exception:
        return None

    return {
        "bib": bib,
        "channel": channel,
        "time_of_day": time_str,
        "raw_time": round(seconds, 3),
        "raw_line": line
    }


def _send_ws(payload: dict):
    with _ws_lock:
        conn = _ws_conn
    if conn is not None:
        try:
            conn.send(json.dumps(payload))
        except Exception:
            pass


# ── Serieller Thread pro Timy ─────────────────────────────────────────────────

def create_serial_thread(device: dict):
    """Erstellt einen Thread für ein einzelnes Timy-Gerät."""

    def serial_thread():
        global _last_hb_sent
        dev_name = device["name"]
        color = device.get("color", "")

        while True:
            port = device["port"] or _find_port(dev_name)
            if port is None:
                print(f"{color}[{dev_name}] Kein Port gefunden – warte 5s...")
                time.sleep(5)
                continue

            try:
                print(f"{color}[{dev_name}] Verbinde mit {port} @ {device['baudrate']} Baud")
                with serial.Serial(
                    port=port,
                    baudrate=device["baudrate"],
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=0.5
                ) as ser:

                    print(f"{color}[{dev_name}] ✅ Verbunden")

                    while True:
                        now = time.time()

                        raw = ser.readline().decode("ascii", errors="ignore").strip()
                        if raw:
                            print(f"{color}[{dev_name}] Raw: {raw}")
                            parsed = _parse_alge_line(raw)

                            if parsed and parsed["raw_time"] >= MIN_TIME:
                                impulse_type = device["channels"].get(parsed["channel"], parsed["channel"])
                                print(f"{color}[{dev_name}] → Bib {parsed['bib']} | {impulse_type} | {parsed['raw_time']:.3f}s")

                                _send_ws({
                                    "type": "timing_impulse",
                                    "device": "alge_timy",
                                    "device_name": dev_name,
                                    "impulse_type": impulse_type,
                                    **parsed
                                })

                        # Heartbeat — Lock verhindert, dass mehrere Threads gleichzeitig senden
                        with _hb_lock:
                            if now - _last_hb_sent >= HEARTBEAT_S:
                                _last_hb_sent = now
                                _send_ws({"type": "timing_device_heartbeat", "device": "alge_timy"})

                        time.sleep(0.05)

            except serial.SerialException as e:
                print(f"{color}[{dev_name}] Serial-Fehler: {e} – retry in 5s")
            except Exception as e:
                print(f"{color}[{dev_name}] Fehler: {e}")

            time.sleep(5)

    return serial_thread


# ── WebSocket Threads (gleich wie im LSU-Client) ─────────────────────────────

def _ws_on_open(ws):
    global _ws_conn
    with _ws_lock:
        _ws_conn = ws
    print(f"[WS] ✅ Verbunden mit {BACKEND_WS}")


def _ws_on_message(ws, message):
    try:
        data = json.loads(message)
        print(f"[WS] ← {data}")
    except Exception:
        pass


def _ws_on_error(ws, error):
    print(f"[WS] Fehler: {error}")


def _ws_on_close(ws, *args):
    global _ws_conn
    with _ws_lock:
        _ws_conn = None
    print("[WS] Getrennt – reconnect in 3s...")


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
        except Exception:
            pass
        time.sleep(3)


# ── Hauptstart ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("  RaceControl Pro – ALGE Timy Multi-Client")
    print("=" * 70)

    # Starte WebSocket
    threading.Thread(target=_ws_thread, daemon=True, name="websocket").start()

    # Starte einen Thread pro Timy
    for device in TIMY_DEVICES:
        thread = threading.Thread(
            target=create_serial_thread(device),
            daemon=True,
            name=f"serial_{device['name']}"
        )
        thread.start()
        print(f"   → Thread gestartet für: {device['name']}")

    print(f"   Backend: {BACKEND_WS}")
    print("   Ctrl+C zum Beenden")
    print("=" * 70)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[ALGE Multi-Client] Beende alle Threads...")