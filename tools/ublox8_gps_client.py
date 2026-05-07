#!/usr/bin/env python3
"""
RaceControl Pro – u-blox 8 GPS Monitor

Liest NMEA-Daten vom u-blox 8 (USB, CDC ACM) und zeigt
Fix-Status, UTC-Zeit, Position, Höhe und Satelliten live an.

Voraussetzungen:
    sudo apt install python3-serial

udev-Regel / Berechtigungen (einmalig via setup_gps_ntp.sh):
    sudo usermod -aG dialout $USER   (danach neu anmelden)

Starten:
    python3 ublox8_gps_client.py

Gerät manuell vorgeben:
    GPS_DEVICE=/dev/ttyACM1 python3 ublox8_gps_client.py

License: GNU General Public License v2
Author : bh2005
"""

import os
import sys
import time
import serial
import serial.tools.list_ports
from datetime import datetime, timezone

# ── Konfiguration ─────────────────────────────────────────────────────────────

GPS_DEVICE = os.getenv("GPS_DEVICE", "")   # leer = auto-detect
GPS_BAUD   = 9600                           # u-blox 8 NMEA-Default
GPS_TIMEOUT = 2                             # Sekunden

USB_VID = "1546"   # U-Blox AG
USB_PID = "01a8"   # u-blox 8

# ── Gerät automatisch finden ──────────────────────────────────────────────────

def _find_device() -> str | None:
    """Sucht den u-blox 8 anhand VID/PID oder Gerätename."""
    for p in serial.tools.list_ports.comports():
        vid = f"{p.vid:04x}" if p.vid else ""
        pid = f"{p.pid:04x}" if p.pid else ""
        desc = (p.description or "").lower()
        if (vid == USB_VID and pid == USB_PID) or "u-blox" in desc or "ublox" in desc:
            return p.device
    # Fallback: /dev/gps0 (udev-Symlink aus setup_gps_ntp.sh)
    if os.path.exists("/dev/gps0"):
        return "/dev/gps0"
    # Fallback: erstes ttyACM
    if os.path.exists("/dev/ttyACM0"):
        return "/dev/ttyACM0"
    return None


# ── NMEA-Parser ───────────────────────────────────────────────────────────────

def _nmea_checksum(sentence: str) -> bool:
    """Prüft NMEA-Prüfsumme (*XX am Ende)."""
    try:
        data, cksum = sentence[1:].rsplit("*", 1)
        calc = 0
        for c in data:
            calc ^= ord(c)
        return calc == int(cksum.strip(), 16)
    except Exception:
        return False


def _parse_lat(val: str, hemi: str) -> float | None:
    """NMEA ddmm.mmmm → Dezimalgrad."""
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


def _parse_time(t: str, d: str = "") -> str:
    """NMEA-Zeit (HHMMSS.ss) + Datum (DDMMYY) → lesbarer String."""
    try:
        h, m, s = int(t[0:2]), int(t[2:4]), float(t[4:])
        if d and len(d) == 6:
            day, mon, yr = int(d[0:2]), int(d[2:4]), 2000 + int(d[4:6])
            return f"{yr:04d}-{mon:02d}-{day:02d}  {h:02d}:{m:02d}:{s:05.2f} UTC"
        return f"{h:02d}:{m:02d}:{s:05.2f} UTC"
    except Exception:
        return ""


class GpsState:
    def __init__(self):
        self.fix        = 0      # 0=kein Fix, 1=GPS, 2=DGPS, 4=RTK
        self.fix_type   = ""     # "kein Fix" / "2D" / "3D"
        self.utc        = ""
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
        """Verarbeitet eine NMEA-Zeile; aktualisiert State."""
        line = line.strip()
        if not line.startswith("$") or "*" not in line:
            return
        if not _nmea_checksum(line):
            return

        parts = line.split("*")[0].split(",")
        tag = parts[0][1:]   # z.B. "GNGGA", "GNRMC"

        # GGA – Position + Fix-Qualität
        if tag.endswith("GGA") and len(parts) >= 10:
            self.utc       = _parse_time(parts[1])
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

        # RMC – Zeit + Datum + Geschwindigkeit + Kurs
        elif tag.endswith("RMC") and len(parts) >= 9:
            status = parts[2]   # A=valid, V=invalid
            if status == "A":
                self.utc    = _parse_time(parts[1], parts[9])
                self.lat    = _parse_lat(parts[3], parts[4])
                self.lon    = _parse_lat(parts[5], parts[6])
                knots = float(parts[7]) if parts[7] else 0.0
                self.speed_kmh = round(knots * 1.852, 1)
                self.course    = float(parts[8]) if parts[8] else None
            self.updated = True

        # GSV – Satelliten in Sicht
        elif tag.endswith("GSV") and len(parts) >= 4:
            try:
                self.sats_view = int(parts[3])
            except ValueError:
                pass


# ── Anzeige ───────────────────────────────────────────────────────────────────

_FIX_COLOR  = {0: "\033[31m", 1: "\033[33m", 2: "\033[32m"}   # rot / gelb / grün
_RESET      = "\033[0m"
_CLEAR_LINE = "\033[K"
_HOME       = "\033[H"

def _render(state: GpsState, device: str):
    """Gibt den aktuellen GPS-Status im Terminal aus (in-place Update)."""
    fix_col = _FIX_COLOR.get(min(state.fix, 2), "\033[32m")

    lat_str  = f"{state.lat:+.6f}°" if state.lat  is not None else "---"
    lon_str  = f"{state.lon:+.6f}°" if state.lon  is not None else "---"
    alt_str  = f"{state.altitude:.1f} m" if state.altitude is not None else "---"
    hdop_str = f"{state.hdop:.1f}"   if state.hdop     is not None else "---"
    spd_str  = f"{state.speed_kmh:.1f} km/h" if state.speed_kmh is not None else "---"
    crs_str  = f"{state.course:.0f}°"         if state.course    is not None else "---"

    lines = [
        f"\033[1m{'=' * 50}\033[0m{_CLEAR_LINE}",
        f"  RaceControl Pro – u-blox 8 GPS Monitor{_CLEAR_LINE}",
        f"{'=' * 50}{_CLEAR_LINE}",
        f"  Gerät   : {device}{_CLEAR_LINE}",
        f"  Fix     : {fix_col}{state.fix_type or 'warte...'}{_RESET}{_CLEAR_LINE}",
        f"  UTC-Zeit: {state.utc or 'warte...'}{_CLEAR_LINE}",
        f"{'─' * 50}{_CLEAR_LINE}",
        f"  Breite  : {lat_str}{_CLEAR_LINE}",
        f"  Länge   : {lon_str}{_CLEAR_LINE}",
        f"  Höhe    : {alt_str}{_CLEAR_LINE}",
        f"  HDOP    : {hdop_str}{_CLEAR_LINE}",
        f"{'─' * 50}{_CLEAR_LINE}",
        f"  Sats    : {state.sats_used} genutzt / {state.sats_view} sichtbar{_CLEAR_LINE}",
        f"  Geschw. : {spd_str}{_CLEAR_LINE}",
        f"  Kurs    : {crs_str}{_CLEAR_LINE}",
        f"{'=' * 50}{_CLEAR_LINE}",
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

    # Vollbild vorbereiten
    sys.stdout.write("\033[2J")   # Bildschirm löschen
    _render(state, device)

    while True:
        try:
            print(f"\n  Verbinde mit {device} ({GPS_BAUD} Baud) ...")
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
