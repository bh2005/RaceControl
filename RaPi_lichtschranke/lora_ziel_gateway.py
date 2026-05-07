#!/usr/bin/env python3
"""
LoRa-Gateway – Empfänger (Ziel-Pi)
Waveshare SX1268 HAT, UART-Modus

Funktionen:
  - Empfängt Start-Pakete vom Arduino LoRa-Sender
  - Leitet sie per HTTP an das RaceControl-Backend weiter
  - Sendet regelmäßig einen Zeitsync an alle Arduino-Sender (UTC)
  - Bestätigt timesync_ack vom Arduino

Konfiguration in den Konstanten unten anpassen.
"""
import time
import json
import serial
import requests
import threading

# ── Konfiguration ──────────────────────────────────────────────────────────────
UART_PORT      = '/dev/ttyAMA0'           # Pi 3/4: ttyAMA0 | Pi Zero: ttyS0
UART_BAUD      = 9600
SERVER_URL     = 'http://localhost:1980'  # RaceControl-Backend
TIMING_API_KEY = 'HIER_DEN_KEY_EINTRAGEN'

# Zeitsync: alle N Sekunden UTC-Zeit an Arduino senden
TIMESYNC_INTERVAL = 60   # Sekunden

HEADERS = {
    'X-Timing-Key': TIMING_API_KEY,
    'Content-Type': 'application/json',
}

# ── UART ───────────────────────────────────────────────────────────────────────
ser = serial.Serial(UART_PORT, UART_BAUD, timeout=2)
time.sleep(0.2)

# ── Zeitsync senden ───────────────────────────────────────────────────────────
def sende_timesync():
    """Sendet aktuellen Unix-Timestamp per LoRa an alle Arduinos."""
    unix = int(time.time())
    payload = json.dumps({'type': 'timesync', 'unix': unix})
    ser.write((payload + '\n').encode())
    print(f'[SYNC] Zeitsync gesendet: unix={unix}')

def timesync_loop():
    """Hintergrund-Thread: sendet regelmäßig Zeitsync."""
    # Erster Sync sofort beim Start
    time.sleep(2)
    while True:
        try:
            sende_timesync()
        except Exception as e:
            print(f'[ERR]  Zeitsync fehlgeschlagen: {e}')
        time.sleep(TIMESYNC_INTERVAL)

# ── Start-Paket verarbeiten ───────────────────────────────────────────────────
def verarbeite_start(data: dict, rohzeile: str):
    """Leitet ein Start-Paket an das RaceControl-Backend weiter."""
    unix_ts = data.get('unix', 0)
    lane    = data.get('lane', 'A')

    # Wenn Arduino keinen RTC hat (unix=0): Gateway-Timestamp verwenden
    if unix_ts == 0:
        unix_ts = int(time.time())
        print(f'[WARN] Kein RTC-Timestamp vom Arduino – verwende Gateway-Zeit: {unix_ts}')

    payload = {
        'timestamp': unix_ts,
        'lane':      lane,
        'source':    'lora',
        'raw':       rohzeile,
    }

    try:
        r = requests.post(
            f'{SERVER_URL}/api/timing/start',
            json=payload,
            headers=HEADERS,
            timeout=3,
        )
        print(f'[POST] {r.status_code} lane={lane} unix={unix_ts} – {r.text[:80]}')
    except requests.RequestException as e:
        print(f'[ERR]  HTTP-Fehler: {e}')

# ── Hauptschleife ─────────────────────────────────────────────────────────────
def main():
    print(f'[OK]   LoRa-Gateway aktiv. UART={UART_PORT}, Server={SERVER_URL}')

    # Zeitsync im Hintergrund starten
    t = threading.Thread(target=timesync_loop, daemon=True)
    t.start()

    while True:
        try:
            raw = ser.readline()
            if not raw:
                continue

            line = raw.decode('utf-8', errors='ignore').strip()
            if not line:
                continue

            print(f'[RECV] {line}')

            data = json.loads(line)
            pkt_type = data.get('type')

            if pkt_type == 'start':
                verarbeite_start(data, line)

            elif pkt_type == 'timesync_ack':
                print(f'[ACK]  Arduino hat Zeitsync bestätigt: unix={data.get("unix")}')

            else:
                print(f'[WARN] Unbekannter Pakettyp: {pkt_type!r}')

        except json.JSONDecodeError:
            print(f'[WARN] Kein gültiges JSON: {line!r}')
        except Exception as e:
            print(f'[ERR]  {e}')
            time.sleep(0.5)

if __name__ == '__main__':
    main()
