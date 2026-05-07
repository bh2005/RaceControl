#!/usr/bin/env python3
"""
RaceControl Pro – u-blox 8 GPS Monitor + Timesync

Liest NMEA-Daten vom u-blox 8 (USB, CDC ACM) und:
  1. Zeigt Fix-Status, UTC-Zeit, Position, Höhe und Satelliten live an.
  2. Sendet bei gültigem Fix alle TIMESYNC_INTERVAL_S Sekunden einen
     GPS-Timesync per WebSocket an das RaceControl-Backend.

Das Backend kann den Timesync an LoRa-Gateways weiterleiten, die ihn
ihrerseits per LoRa-Broadcast an Arduino/ESP32-Sender ausstrahlen.

Voraussetzungen:
    pip install pyserial websocket-client python-dotenv

udev-Regel / Berechtigungen (einmalig via setup_gps_ntp.sh):
    sudo usermod -aG dialout $USER   (danach neu anmelden)

Starten:
    python3 ublox8_gps_client.py
    GPS_DEVICE=/dev/ttyACM1 python3 ublox8_gps_client.py

License: GNU General Public License v2
Author : bh2005
"""

import json
import os
import sys
import time
import threading
from datetime import datetime, timezone

import serial
import serial.tools.list_ports
import websocket
from dotenv import load_dotenv

load_dotenv()

# ── Konfiguration ─────────────────────────────────────────────────────────────

GPS_DEVICE = os.getenv("GPS_DEVICE", "")    # leer = auto-detect
GPS_BAUD   = 9600                            # u-blox 8 NMEA-Default
GPS_TIMEOUT = 2                              # Sekunden

TIMING_API_KEY     = os.getenv("TIMING_API_KEY", "")
BACKEND_WS         = os.getenv("BACKEND_WS", "ws://localhost:1980/ws/timing") + \
                     (f"?key={TIMING_API_KEY}" if TIMING_API_KEY else "")
TIMESYNC_INTERVAL_S = int(os.getenv("GPS_TIMESYNC_INTERVAL", "10"))  # Sekunden zwischen Syncs
MIN_SATS_FOR_SYNC   = 4    # Mindestanzahl Satelliten für Timesync

USB_VID = "1546"   # U-Blox AG
USB_PID = "01a8"   # u-blox 8

# ── Gerät automatisch finden ──────────────────────────────────────────────────

def _find_device() -> str | None:
    for p in serial.tools.list_ports.comports():
        vid = f"{p.vid:04x}" if p.vid else ""
        pid = f"{p.pid:04x}" if p.pid else ""
        desc = (p.description or "").lower()
        if (vid == USB_VID and pid == USB_PID) or "u-blox" in desc or "ublox" in desc:
            return p.device
    if os.path.exists("/dev/gps0"):
        return "/dev/gps0"
    if os.path.exists("/dev/ttyACM0"):
        return "/dev/ttyACM0"
    return None


# ── NMEA-Parser ───────────────────────────────────────────────────────────────

def _nmea_checksum(sentence: str) -> bool:
    try:
        data, cksum = sentence[1:].rsplit("*", 1)
        calc = 0
        for c in data:
            calc ^= ord(c)
        return calc == int(cksum.strip(), 16)
    except Exception:
        return False


def _parse_lat(val: str, hemi: str) -> float | None:
    if not val:
        return None
    try:
        deg = int(float(val) / 100)
        minutes = float(val) - deg * 100
        result = deg + minutes / 60.0
        if hemi in ("S", "W"):
            result = -result
        return result
    except ValueError:
        return None


def _parse_time_str(t: str, d: str = "") -> str:
    """NMEA HHMMSS.ss + DDMMYY → lesbarer UTC-String."""
    try:
        h, m, s = int(t[0:2]), int(t[2:4]), float(t[4:])
        if d and len(d) == 6:
            day, mon, yr = int(d[0:2]), int(d[2:4]), 2000 + int(d[4:6])
            return f"{yr:04d}-{mon:02d}-{day:02d}  {h:02d}:{m:02d}:{s:05.2f} UTC"
        return f"{h:02d}:{m:02d}:{s:05.2f} UTC"
    except Exception:
        return ""


def _nmea_to_unix(t: str, d: str) -> int | None:
    """NMEA HHMMSS.ss + DDMMYY → Unix-Timestamp (UTC)."""
    try:
        h, m, s = int(t[0:2]), int(t[2:4]), int(float(t[4:]))
        day, mon, yr = int(d[0:2]), int(d[2:4]), 2000 + int(d[4:6])
        dt = datetime(yr, mon, day, h, m, s, tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        return None


class GpsState:
    def __init__(self):
        self.fix        = 0
        self.fix_type   = ""
        self.utc        = ""
        self.unix_time  = None   # GPS-Unix-Timestamp aus RMC (mit Datum)
        self.lat        = None
        self.lon        = None
        self.altitude   = None
        self.sats_used  = 0
        self.sats_view  = 0
        self.hdop       = None
        self.speed_kmh  = None
        self.course     = None
        self.updated    = False

    def feed(self, line: str):
        line = line.strip()
        if not line.startswith("$") or "*" not in line:
            return
        if not _nmea_checksum(line):
            return

        parts = line.split("*")[0].split(",")
        tag = parts[0][1:]

        if tag.endswith("GGA") and len(parts) >= 10:
            self.utc       = _parse_time_str(parts[1])
            self.lat       = _parse_lat(parts[2], parts[3])
            self.lon       = _parse_lat(parts[4], parts[5])
            self.fix       = int(parts[6]) if parts[6] else 0
            self.sats_used = int(parts[7]) if parts[7] else 0
            self.hdop      = float(parts[8]) if parts[8] else None
            self.altitude  = float(parts[9]) if parts[9] else None
            self.fix_type  = {0: "kein Fix", 1: "GPS-Fix", 2: "DGPS-Fix"}.get(
                self.fix, f"Fix-{self.fix}"
            )
            self.updated = True

        elif tag.endswith("RMC") and len(parts) >= 10:
            status = parts[2]
            if status == "A":
                self.utc       = _parse_time_str(parts[1], parts[9])
                self.unix_time = _nmea_to_unix(parts[1], parts[9])
                self.lat       = _parse_lat(parts[3], parts[4])
                self.lon       = _parse_lat(parts[5], parts[6])
                knots = float(parts[7]) if parts[7] else 0.0
                self.speed_kmh = round(knots * 1.852, 1)
                self.course    = float(parts[8]) if parts[8] else None
            self.updated = True

        elif tag.endswith("GSV") and len(parts) >= 4:
            try:
                self.sats_view = int(parts[3])
            except ValueError:
                pass

    @property
    def sync_ready(self) -> bool:
        """True wenn Fix vorhanden und genug Satelliten für zuverlässigen Timesync."""
        return self.fix > 0 and self.sats_used >= MIN_SATS_FOR_SYNC and self.unix_time is not None


# ── WebSocket ─────────────────────────────────────────────────────────────────

_ws_conn      = None
_ws_lock      = threading.Lock()
_last_sync_sent = 0.0
_ws_connected = False


def _send_ws(payload: dict):
    with _ws_lock:
        conn = _ws_conn
    if conn is not None:
        try:
            conn.send(json.dumps(payload))
        except Exception:
            pass


def _ws_on_open(ws):
    global _ws_conn, _ws_connected
    with _ws_lock:
        _ws_conn = ws
    _ws_connected = True


def _ws_on_message(ws, message):
    pass   # Backend-Antworten werden für GPS-Client nicht benötigt


def _ws_on_error(ws, error):
    pass


def _ws_on_close(ws, *args):
    global _ws_conn, _ws_connected
    with _ws_lock:
        _ws_conn = None
    _ws_connected = False


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


# ── Timesync-Thread ───────────────────────────────────────────────────────────

def _timesync_loop(state: GpsState):
    """Sendet alle TIMESYNC_INTERVAL_S Sekunden einen GPS-Timesync ans Backend."""
    global _last_sync_sent
    while True:
        time.sleep(1)
        if not state.sync_ready:
            continue
        now = time.time()
        if now - _last_sync_sent < TIMESYNC_INTERVAL_S:
            continue
        _last_sync_sent = now
        _send_ws({
            "type":   "gps_timesync",
            "unix":   state.unix_time,
            "utc":    state.utc,
            "fix":    state.fix,
            "sats":   state.sats_used,
            "hdop":   state.hdop,
            "source": "ublox8",
        })


# ── Anzeige ───────────────────────────────────────────────────────────────────

_FIX_COLOR  = {0: "\033[31m", 1: "\033[33m", 2: "\033[32m"}
_RESET      = "\033[0m"
_CLEAR_LINE = "\033[K"
_HOME       = "\033[H"


def _render(state: GpsState, device: str):
    fix_col = _FIX_COLOR.get(min(state.fix, 2), "\033[32m")

    lat_str  = f"{state.lat:+.6f}°"       if state.lat       is not None else "---"
    lon_str  = f"{state.lon:+.6f}°"       if state.lon       is not None else "---"
    alt_str  = f"{state.altitude:.1f} m"  if state.altitude  is not None else "---"
    hdop_str = f"{state.hdop:.1f}"        if state.hdop      is not None else "---"
    spd_str  = f"{state.speed_kmh:.1f} km/h" if state.speed_kmh is not None else "---"
    crs_str  = f"{state.course:.0f}°"     if state.course    is not None else "---"

    # Timesync-Status
    if not _ws_connected:
        sync_str = "\033[31mkein Backend\033[0m"
    elif not state.sync_ready:
        reason = "warte auf Fix..." if state.fix == 0 else f"Sats {state.sats_used}/{MIN_SATS_FOR_SYNC}"
        sync_str = f"\033[33m{reason}\033[0m"
    else:
        last = int(time.time() - _last_sync_sent) if _last_sync_sent else 0
        sync_str = f"\033[32maktiv  (letzter Sync vor {last} s)\033[0m"

    lines = [
        f"\033[1m{'=' * 52}\033[0m{_CLEAR_LINE}",
        f"  RaceControl Pro – u-blox 8 GPS + Timesync{_CLEAR_LINE}",
        f"{'=' * 52}{_CLEAR_LINE}",
        f"  Gerät   : {device}{_CLEAR_LINE}",
        f"  Fix     : {fix_col}{state.fix_type or 'warte...'}{_RESET}{_CLEAR_LINE}",
        f"  UTC-Zeit: {state.utc or 'warte...'}{_CLEAR_LINE}",
        f"{'─' * 52}{_CLEAR_LINE}",
        f"  Breite  : {lat_str}{_CLEAR_LINE}",
        f"  Länge   : {lon_str}{_CLEAR_LINE}",
        f"  Höhe    : {alt_str}{_CLEAR_LINE}",
        f"  HDOP    : {hdop_str}{_CLEAR_LINE}",
        f"{'─' * 52}{_CLEAR_LINE}",
        f"  Sats    : {state.sats_used} genutzt / {state.sats_view} sichtbar{_CLEAR_LINE}",
        f"  Geschw. : {spd_str}{_CLEAR_LINE}",
        f"  Kurs    : {crs_str}{_CLEAR_LINE}",
        f"{'─' * 52}{_CLEAR_LINE}",
        f"  Timesync: {sync_str}{_CLEAR_LINE}",
        f"  Interval: alle {TIMESYNC_INTERVAL_S} s  |  Mindest-Sats: {MIN_SATS_FOR_SYNC}{_CLEAR_LINE}",
        f"{'=' * 52}{_CLEAR_LINE}",
        f"  Ctrl+C zum Beenden{_CLEAR_LINE}",
    ]

    sys.stdout.write(_HOME)
    sys.stdout.write("\n".join(lines) + "\n")
    sys.stdout.flush()


# ── Hauptschleife ─────────────────────────────────────────────────────────────

def main():
    device = GPS_DEVICE or _find_device()

    if not device:
        print("FEHLER: u-blox 8 nicht gefunden.")
        print("  Tipp: GPS-Maus anschließen, oder Gerät manuell vorgeben:")
        print("  GPS_DEVICE=/dev/ttyACM0 python3 ublox8_gps_client.py")
        sys.exit(1)

    state = GpsState()

    # WebSocket + Timesync-Thread starten
    threading.Thread(target=_ws_thread, daemon=True, name="ws").start()
    threading.Thread(target=_timesync_loop, args=(state,), daemon=True, name="timesync").start()

    sys.stdout.write("\033[2J")
    _render(state, device)

    while True:
        try:
            with serial.Serial(device, GPS_BAUD, timeout=GPS_TIMEOUT) as ser:
                sys.stdout.write("\033[2J")
                while True:
                    raw = ser.readline()
                    try:
                        line = raw.decode("ascii", errors="ignore")
                    except Exception:
                        continue
                    state.feed(line)
                    if state.updated:
                        _render(state, device)
                        state.updated = False

        except serial.SerialException as e:
            sys.stdout.write(_HOME)
            print(f"  Fehler: {e}")
            print(f"  Retry in 5 s ...")
            time.sleep(5)
        except PermissionError:
            print(f"\nFEHLER: Kein Zugriff auf {device}.")
            print("  Tipp: sudo usermod -aG dialout $USER  (dann neu anmelden)")
            sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Beende.")
