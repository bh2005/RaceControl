#!/usr/bin/env python3
#
# RaceControl Pro – Zieleinheit für Downhill / Seifenkiste / Rally
#
# Einsatz:  Ziel-Raspberry Pi mit EINER Lichtschranke.
#           Sendet beim Auslösen einen absoluten Zeitstempel ans Backend.
#           Das Backend berechnet: Ziel-Zeit − Planstart = Laufzeit.
#
# Zeitsync: Option A (empfohlen): systemd-timesyncd / chrony via NTP (Internet/LAN)
#           Option B (offline):   DCF77-Empfänger-Modul + chrony refclock
#
# Abhängigkeiten:
#   pip install websocket-client RPi.GPIO
#   pip install git+https://github.com/depklyon/raspberrypi-tm1637
#
# Verkabelung:
#   Lichtschranke Signal → GPIO 27 (Stop/Ziel)
#   Reset-Taster         → GPIO 22 (Pullup, aktiv LOW)
#   TM1637 CLK           → GPIO 21
#   TM1637 DIO           → GPIO 20
#   DIP 1 (Spur A/B)     → GPIO 5  (ON=LOW=Spur B, OFF=HIGH=Spur A)
#
# License: GNU General Public License v2
# Author : bh2005
#

import json
import time
import threading
import subprocess
from datetime import datetime, timezone

import RPi.GPIO as GPIO
from tm1637 import TM1637
import websocket

# ── Konfiguration ─────────────────────────────────────────────────────────────

BACKEND_HOST   = "192.168.0.100"   # IP des Laptops / live-race.de Subdomain
BACKEND_PORT   = 1980
TIMING_API_KEY = ""                # Admin → System → Lichtschranken-API-Key

BACKEND_WS = f"ws://{BACKEND_HOST}:{BACKEND_PORT}/ws/timing" + \
             (f"?key={TIMING_API_KEY}" if TIMING_API_KEY else "")

# GPIO-Pins (BCM)
LS_FINISH_PIN = 27    # Lichtschranke Ziel
RESET_PIN     = 22    # Reset-Taster (Pullup, aktiv LOW)
DIP1_PIN      = 5     # Spurwahl: ON (LOW) = Spur B, OFF (HIGH) = Spur A

# TM1637-Display
CLK = 21
DIO = 20

# Mindest-Laufzeit – kürzere Auslösungen sind Fehlauslösungen
MIN_TIME_S    = 10.0   # Sekunden

# Debounce der Lichtschranke
BOUNCE_MS = 200

# Heartbeat
HEARTBEAT_S = 5

# ── Spurkennung ───────────────────────────────────────────────────────────────

GPIO.setmode(GPIO.BCM)
GPIO.setup(DIP1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
LANE = "B" if GPIO.input(DIP1_PIN) == GPIO.LOW else "A"

# ── State ─────────────────────────────────────────────────────────────────────

_ws_lock      = threading.Lock()
_ws_conn      = None
_last_hb      = 0.0
_ready        = True      # True = wartet auf nächsten Fahrer

# ── Display ───────────────────────────────────────────────────────────────────

display = TM1637(CLK, DIO)
display.brightness(3)


def _show(text: str):
    display.show(text)


def _show_time(seconds: float):
    """Zeigt MM:SS.h auf dem TM1637 (6-stellig)."""
    m  = int(seconds // 60)
    s  = int(seconds % 60)
    h  = int((seconds * 10) % 10)
    if m > 0:
        _show(f"{m:02}{s:02}{h:1} ")
    else:
        _show(f"  {s:02}{h:1} ")


def _show_clock(ts: str):
    """Zeigt HH:MM auf dem Display (während Warten)."""
    try:
        _show(ts[3:8].replace(":", ""))   # "12:03:47" → "0347"
    except Exception:
        pass


# ── Zeitsync-Prüfung ─────────────────────────────────────────────────────────

def _clock_synced() -> bool:
    """
    Prüft ob die Systemzeit synchronisiert ist.
    Akzeptiert: NTP (systemd-timesyncd / chrony) oder DCF77 via chrony.
    """
    try:
        out = subprocess.check_output(
            ["timedatectl", "show", "--property=NTPSynchronized"],
            timeout=2, text=True
        )
        return "yes" in out.lower()
    except Exception:
        return False


# ── WebSocket ─────────────────────────────────────────────────────────────────

def _send(payload: dict):
    with _ws_lock:
        conn = _ws_conn
    if conn is not None:
        try:
            conn.send(json.dumps(payload))
        except Exception:
            pass


def _ws_on_open(ws):
    global _ws_conn
    with _ws_lock:
        _ws_conn = ws
    print(f"[WS] Verbunden  Spur {LANE}")
    _show("ConA" if LANE == "A" else "ConB")
    time.sleep(0.8)
    _show("----")


def _ws_on_message(ws, message):
    """
    Backend antwortet auf timing_finish mit berechneter Laufzeit:
    {"type": "timing_result_display", "raw_time": 167.412, "rank": 3}
    """
    global _ready
    try:
        data = json.loads(message)
        if data.get("type") == "timing_result_display":
            t = data.get("raw_time")
            if isinstance(t, (int, float)):
                _show_time(t)
                print(f"[ZIEL] Laufzeit: {t:.3f} s")
        _ready = True
    except Exception:
        pass


def _ws_on_error(ws, error):
    print(f"[WS] Fehler: {error}")


def _ws_on_close(ws, *args):
    global _ws_conn
    with _ws_lock:
        _ws_conn = None
    print("[WS] Getrennt – reconnect in 3 s …")
    _show("dISC")


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
            print(f"[WS] Fehler: {e}")
        time.sleep(3)


def _heartbeat_thread():
    global _last_hb
    while True:
        time.sleep(HEARTBEAT_S)
        now = time.time()
        if now - _last_hb >= HEARTBEAT_S:
            _send({"type": "timing_device_heartbeat"})
            _last_hb = now


# ── GPIO-Callbacks ────────────────────────────────────────────────────────────

_last_trigger = 0.0


def _on_finish(channel):
    global _last_trigger, _ready

    now_ts   = time.time()
    now_wall = datetime.now(timezone.utc)

    # Debounce (zusätzlich zu bouncetime)
    if now_ts - _last_trigger < MIN_TIME_S:
        print(f"[ZIEL] Fehlauslösung ignoriert (< {MIN_TIME_S} s)")
        return
    _last_trigger = now_ts

    # Uhrzeitstring mit Millisekunden: "12:03:47.412"
    clock_str = now_wall.strftime("%H:%M:%S.") + f"{now_wall.microsecond // 1000:03d}"

    # Zeitsync-Warnung
    if not _clock_synced():
        print("[ZIEL] WARNUNG: Uhr nicht synchronisiert!")
        _show("nSYn")
        time.sleep(1)

    _ready = False
    _show("----")
    print(f"[ZIEL] Auslösung Spur {LANE}: {clock_str}")

    _send({
        "type":   "timing_finish",
        "clock":  clock_str,
        "lane":   LANE,
        "device": f"downhill-finish-rpi-{LANE.lower()}",
    })


def _on_reset(channel):
    global _ready, _last_trigger
    _ready       = True
    _last_trigger = 0.0
    _show("----")
    print("[ZIEL] Reset")


# ── GPIO-Setup ────────────────────────────────────────────────────────────────

GPIO.setup(LS_FINISH_PIN, GPIO.IN)
GPIO.setup(RESET_PIN,     GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.add_event_detect(LS_FINISH_PIN, GPIO.RISING,  callback=_on_finish, bouncetime=BOUNCE_MS)
GPIO.add_event_detect(RESET_PIN,     GPIO.FALLING, callback=_on_reset,  bouncetime=200)

# ── Uhrzeitanzeige (Leerlauf) ─────────────────────────────────────────────────

def _clock_display_thread():
    """Zeigt im Leerlauf die aktuelle Uhrzeit auf dem Display."""
    while True:
        if _ready:
            _show_clock(datetime.now().strftime("%H:%M:%S"))
        time.sleep(1)


# ── Start ─────────────────────────────────────────────────────────────────────

threading.Thread(target=_ws_thread,           daemon=True, name="ws").start()
threading.Thread(target=_heartbeat_thread,    daemon=True, name="hb").start()
threading.Thread(target=_clock_display_thread, daemon=True, name="clk").start()

synced = _clock_synced()

print("=" * 52)
print("  RaceControl Pro – Zieleinheit Downhill/Seifenkiste")
print("=" * 52)
print(f"  Spur    : {LANE}")
print(f"  Backend : {BACKEND_WS}")
print(f"  Min-Zeit: {MIN_TIME_S} s")
print(f"  Zeitsync: {'✓ synchronisiert' if synced else '⚠ NICHT synchronisiert!'}")
print("  Ctrl+C zum Beenden")
print("=" * 52)

if not synced:
    _show("nSYn")
    time.sleep(2)

_show("----")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n[RC] Beende …")
    _show("    ")
    GPIO.cleanup()
