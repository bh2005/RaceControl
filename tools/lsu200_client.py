#!/usr/bin/env python3
"""
RaceControl Pro – ELV LSU200 USB-Zeitmessung-Client

Verbindet sich über USB (virtueller COM-Port) mit der ELV LSU200 und leitet
gemessene Zeiten an das RaceControl-Backend weiter (WebSocket /ws/timing).

Läuft auf demselben Laptop wie RaceControl — kein Raspi erforderlich.

Abhängigkeiten:
    pip install pyserial websocket-client

Starten:
    python lsu200_client.py

COM-Port ermitteln (Windows):
    Gerätemanager → Anschlüsse (COM & LPT) → ELV LSU200 (COMx)
    oder in PowerShell: Get-WmiObject Win32_PnPEntity | Where Name -like "*LSU*"

License: GNU General Public License v2
Author : bh2005
"""

import json
import time
import threading
import serial
import serial.tools.list_ports
import websocket

# ── Konfiguration ─────────────────────────────────────────────────────────────

# COM-Port der LSU200 (Windows: "COM3", Linux: "/dev/ttyUSB0")
# None = automatische Erkennung anhand der USB-VID/PID oder Gerätename
SERIAL_PORT = None          # z.B. "COM3" – None = auto-detect

SERIAL_BAUD = 19200         # fest vorgegeben laut LSU200-Protokoll

BACKEND_WS  = "ws://localhost:1980/ws/timing"

MIN_TIME    = 3.0           # Messungen kürzer als MIN_TIME Sekunden ignorieren
POLL_MS     = 100           # Abfrageintervall in Millisekunden
HEARTBEAT_S = 5             # Heartbeat-Intervall in Sekunden

# ── Interne State-Variablen ───────────────────────────────────────────────────

_ws_conn      = None
_ws_lock      = threading.Lock()
_last_hb_sent = 0.0         # Zeitstempel letzter Heartbeat


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _find_port() -> str | None:
    """Sucht automatisch nach der LSU200 anhand des Gerätenamens."""
    for p in serial.tools.list_ports.comports():
        desc = (p.description or "").upper()
        mfr  = (p.manufacturer or "").upper()
        if "LSU" in desc or "ELV" in desc or "ELV" in mfr:
            return p.device
    return None


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


# ── Serieller Lese-Thread ─────────────────────────────────────────────────────

def _serial_thread():
    global _last_hb_sent
    last_state = -1

    while True:
        # COM-Port bestimmen
        port = SERIAL_PORT or _find_port()
        if port is None:
            print("[LSU200] Kein COM-Port gefunden – retry in 5 s")
            time.sleep(5)
            continue

        try:
            print(f"[LSU200] Verbinde mit {port} ({SERIAL_BAUD} Baud) …")
            with serial.Serial(port, SERIAL_BAUD, timeout=0.5) as ser:
                print(f"[LSU200] Verbunden")
                last_state = -1

                while True:
                    now = time.time()

                    # ── Stoppuhr-Status abfragen ──────────────────────────────
                    ser.reset_input_buffer()
                    ser.write(b"w")
                    raw = ser.readline().decode("ascii", errors="ignore").strip()

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
                                _send_ws({
                                    "type":     "timing_result",
                                    "raw_time": round(elapsed, 3),
                                    "device":   "lsu200-usb",
                                })
                            elif elapsed is not None:
                                print(f"[LSU200] Messung verworfen ({elapsed:.3f} s < {MIN_TIME} s)")

                        last_state = current_state

                    # ── Heartbeat ─────────────────────────────────────────────
                    if now - _last_hb_sent >= HEARTBEAT_S:
                        _send_ws({"type": "timing_device_heartbeat"})
                        _last_hb_sent = now

                    time.sleep(POLL_MS / 1000)

        except serial.SerialException as e:
            print(f"[LSU200] Serial-Fehler: {e} – retry in 5 s")
            last_state = -1

        time.sleep(5)


# ── WebSocket-Thread ──────────────────────────────────────────────────────────

def _ws_on_open(ws):
    global _ws_conn
    with _ws_lock:
        _ws_conn = ws
    print(f"[WS] Verbunden mit {BACKEND_WS}")


def _ws_on_message(ws, message):
    """Backend kann Rückmeldungen schicken (z.B. Startnummer für Display)."""
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
    print("[WS] Getrennt – reconnect in 3 s …")


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
    threading.Thread(target=_ws_thread,    daemon=True, name="ws").start()
    threading.Thread(target=_serial_thread, daemon=True, name="serial").start()

    print("=" * 50)
    print("  RaceControl Pro – ELV LSU200 Client")
    print("=" * 50)
    print(f"  Serial  : {SERIAL_PORT or 'auto-detect'}")
    print(f"  Backend : {BACKEND_WS}")
    print(f"  Min-Zeit: {MIN_TIME} s")
    print("  Ctrl+C zum Beenden")
    print("=" * 50)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[RC] Beende …")
