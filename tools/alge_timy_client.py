#!/usr/bin/env python3
"""
RaceControl Pro – ALGE Timy (Timy2 / Timy3) Client

Verbindet sich über RS232 (USB-Adapter) mit einem ALGE Timy und leitet
Start- und Stopp-Impulse per WebSocket an das RaceControl-Backend weiter.

Läuft auf demselben Laptop wie RaceControl — kein Raspberry Pi nötig.

Abhängigkeiten:
    pip install pyserial websocket-client

Starten:
    python alge_timy_client.py

COM-Port ermitteln (Windows):
    Gerätemanager → Anschlüsse (COM & LPT)

License: GNU General Public License v2
Author : bh2005 (angepasst für ALGE)
"""

import json
import time
import threading
import re
import serial
import serial.tools.list_ports
import websocket

# ── Konfiguration ─────────────────────────────────────────────────────────────

# COM-Port des ALGE Timy (Windows: "COM4", Linux: "/dev/ttyUSB0")
# None = automatische Suche (weniger zuverlässig als bei LSU)
SERIAL_PORT = None          # z.B. "COM4" oder None für Auto-Suche

SERIAL_BAUD = 9600          # Standard bei den meisten ALGE Timy3-Einstellungen
                            # Manche nutzen 19200 – bei Bedarf anpassen!

BACKEND_WS  = "ws://localhost:1980/ws/timing"

MIN_TIME    = 3.0           # Impulse mit kürzerer Zeit ignorieren (Anti-Bounce)
HEARTBEAT_S = 5             # Heartbeat-Intervall

# ── Interne State-Variablen ───────────────────────────────────────────────────

_ws_conn      = None
_ws_lock      = threading.Lock()
_last_hb_sent = 0.0


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _find_alge_port() -> str | None:
    """Sucht automatisch nach einem ALGE Timy anhand typischer Hinweise."""
    for p in serial.tools.list_ports.comports():
        desc = (p.description or "").upper()
        mfr  = (p.manufacturer or "").upper()
        if any(x in desc or x in mfr for x in ["ALGE", "TIMY", "RS232", "FTDI", "CP210"]):
            print(f"[ALGE] Potentieller Port gefunden: {p.device} → {p.description}")
            return p.device
    return None


def _parse_alge_line(line: str) -> dict | None:
    """
    Parst typische ALGE Timy RS232-Ausgaben.
    Beispiele:
      " 0005 c1 15:43:51,646" 
      "m 0008 c0 15:44:00,2849 00"
      "0043 C0 10:34:13.384"
    """
    line = line.strip()
    if not line:
        return None

    # Komma durch Punkt ersetzen für float-Parsing
    line = line.replace(',', '.')

    # Regex: optionales Präfix + Startnummer + Kanal + Zeit
    pattern = r'(?i)([a-z]?\s*)(\d{1,4})\s+(c[0-9m]+)\s+([\d:.]+)'
    match = re.search(pattern, line)
    if not match:
        return None

    bib    = int(match.group(2))
    channel = match.group(3).lower()
    time_str = match.group(4)

    # Zeit in Sekunden umrechnen (HH:MM:SS.mmm)
    try:
        parts = re.split(r'[:.]', time_str)
        h = int(parts[0])
        m = int(parts[1])
        s = int(parts[2])
        ms = int(parts[3].ljust(3, '0')[:3]) if len(parts) > 3 else 0
        seconds = h * 3600 + m * 60 + s + ms / 1000.0
    except Exception:
        return None

    # Kanal → impulse_type Mapping (anpassen je nach Timy-Programmierung!)
    channel_map = {
        "c0": "start",
        "c0m": "start_manual",
        "c1": "finish",
        "c1m": "finish_manual",
        # Weitere Intermediate-Kanäle bei Bedarf hinzufügen:
        # "c2": "intermediate1",
    }

    impulse_type = channel_map.get(channel, channel)

    return {
        "bib": bib,
        "channel": channel,
        "impulse_type": impulse_type,
        "time_of_day": time_str,
        "raw_time": round(seconds, 3),
        "source": "alge_timy",
        "raw_line": line
    }


def _send_ws(payload: dict):
    """Sendet JSON ans Backend."""
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

    while True:
        port = SERIAL_PORT or _find_alge_port()
        if port is None:
            print("[ALGE] Kein COM-Port gefunden – suche erneut in 5 s...")
            time.sleep(5)
            continue

        try:
            print(f"[ALGE] Verbinde mit {port} @ {SERIAL_BAUD} Baud …")
            with serial.Serial(
                port=port,
                baudrate=SERIAL_BAUD,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.5,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            ) as ser:

                print(f"[ALGE] ✅ Erfolgreich verbunden mit {port}")

                while True:
                    now = time.time()

                    # Zeile lesen
                    raw = ser.readline().decode("ascii", errors="ignore").strip()

                    if raw:
                        print(f"[ALGE] Raw: {raw}")
                        parsed = _parse_alge_line(raw)

                        if parsed and parsed["raw_time"] >= MIN_TIME:
                            print(f"[ALGE] → Impuls erkannt: Bib {parsed['bib']} | {parsed['impulse_type']} | {parsed['raw_time']:.3f}s")
                            _send_ws({
                                "type": "timing_impulse",
                                "device": "alge_timy",
                                **parsed
                            })

                    # Heartbeat
                    if now - _last_hb_sent >= HEARTBEAT_S:
                        _send_ws({"type": "timing_device_heartbeat", "device": "alge_timy"})
                        _last_hb_sent = now

                    time.sleep(0.05)   # schnelle Polling-Rate für ALGE

        except serial.SerialException as e:
            print(f"[ALGE] Serial-Fehler: {e} – retry in 5 s")
        except Exception as e:
            print(f"[ALGE] Unerwarteter Fehler: {e}")

        time.sleep(5)


# ── WebSocket-Thread (fast identisch zum LSU-Client) ─────────────────────────

def _ws_on_open(ws):
    global _ws_conn
    with _ws_lock:
        _ws_conn = ws
    print(f"[WS] ✅ Verbunden mit RaceControl Backend ({BACKEND_WS})")


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
    print("[WS] Verbindung geschlossen – reconnect in 3 s …")


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

    print("=" * 60)
    print("  RaceControl Pro – ALGE Timy Client")
    print("=" * 60)
    print(f"  Serial Port : {SERIAL_PORT or 'Auto-Detect'}")
    print(f"  Baudrate    : {SERIAL_BAUD}")
    print(f"  Backend WS  : {BACKEND_WS}")
    print(f"  Min. Zeit   : {MIN_TIME} s")
    print("  Ctrl+C zum Beenden")
    print("=" * 60)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[ALGE Client] Beende …")