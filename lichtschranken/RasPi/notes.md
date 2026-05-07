# RaceControl – Raspberry Pi Lichtschranken-Client

## Dateien

| Datei | Beschreibung |
|---|---|
| `racecontrol_client.py` | **Produktions-Client** mit TM1637-7-Segment-Anzeige und WebSocket-Anbindung |
| `racecontrol_client_max7219.py` | **Produktions-Client** mit MAX7219-LED-Matrix und WebSocket-Anbindung |
| `py_code_raspi_TM1637.py` | Standalone-Testskript TM1637 (kein WebSocket, kein Backend nötig) |
| `py_code_raspi_max7219.py` | Standalone-Testskript MAX7219 (kein WebSocket, kein Backend nötig) |

Die Produktions-Clients verbinden sich automatisch per WebSocket mit dem RaceControl-Backend
und senden Messergebnisse direkt ein. Bei fehlender Backend-Verbindung messen sie weiterhin
lokal und zeigen die Zeit auf dem Display an (offline-fähig).

---

## Hardware

### Materialien

- Raspberry Pi (Zero 2 W, 3B oder 4B)
- 2 × Reflexlichtschranke (digitaler Ausgang, 5V oder 3,3V kompatibel)
- 1 × 6-stellige 7-Segment-Anzeige (TM1637 I²C) **oder** 1 × MAX7219 LED-Matrix (SPI)
- 1 × Drucktaster (Reset-Funktion)
- Jumper-Kabel, ggf. Breadboard

---

## Verkabelung

### GPIO-Belegung (BCM-Nummerierung)

| Signal | GPIO-Pin | Anmerkung |
|---|---|---|
| Lichtschranke 1 – Start | GPIO 17 | Eingang, RISING-Flanke löst Startzeit aus |
| Lichtschranke 2 – Stop  | GPIO 27 | Eingang, RISING-Flanke berechnet und sendet Zeit |
| Reset-Taster            | GPIO 22 | Eingang mit internem Pull-Up, aktiv LOW (FALLING-Flanke) |

### Anzeige Option A: TM1637 (I²C-ähnlich, 2 Leitungen)

| TM1637-Pin | Raspberry Pi |
|---|---|
| VCC | 3,3V oder 5V (Pin 1/17 oder Pin 2/4) |
| GND | GND (Pin 6/9/…) |
| CLK | GPIO 21 (Pin 40) |
| DIO | GPIO 20 (Pin 38) |

### Anzeige Option B: MAX7219 LED-Matrix (SPI)

SPI muss aktiviert sein: `sudo raspi-config → Interface Options → SPI → Enable`

| MAX7219-Pin | Raspberry Pi |
|---|---|
| VCC | 5V (Pin 2 oder 4) |
| GND | GND (Pin 6/9/…) |
| CLK | GPIO 11 / SCLK (Pin 23) |
| DIN | GPIO 10 / MOSI (Pin 19) |
| CS  | GPIO 8 / CE0 (Pin 24) |

---

## Software

### Abhängigkeiten installieren

**Für TM1637:**
```bash
pip install websocket-client RPi.GPIO
pip install git+https://github.com/depklyon/raspberrypi-tm1637
```

**Für MAX7219:**
```bash
pip install websocket-client RPi.GPIO luma.led_matrix Pillow
```

### Konfiguration anpassen

In `racecontrol_client.py` bzw. `racecontrol_client_max7219.py`:

```python
BACKEND_HOST = "192.168.0.100"   # IP des Laptops mit RaceControl
BACKEND_PORT = 1980
MIN_TIME     = 5.0               # Läufe kürzer als 5 s werden verworfen
```

### Skript starten

```bash
python3 racecontrol_client.py
# oder
python3 racecontrol_client_max7219.py
```

---

## Autostart (systemd)

Damit der Client beim Hochfahren automatisch startet:

```bash
sudo nano /etc/systemd/system/racecontrol.service
```

Inhalt:
```ini
[Unit]
Description=RaceControl Lichtschranken-Client
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/RaPi_lichtschranke/racecontrol_client.py
WorkingDirectory=/home/pi/RaPi_lichtschranke
Restart=always
RestartSec=5
User=pi

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable racecontrol
sudo systemctl start racecontrol
sudo journalctl -u racecontrol -f   # Live-Log
```

---

## Funktionsweise

```
Lichtschranke 1 (Start)
    │  RISING-Flanke → start_time = time.time(), measuring = True
    │  Display: "----"
    ▼
Lichtschranke 2 (Stop)
    │  RISING-Flanke → elapsed = now - start_time, measuring = False
    │  elapsed < MIN_TIME → Display: "Err ", verwerfen
    │  elapsed ≥ MIN_TIME → Display: Zeit, WebSocket-Nachricht senden
    ▼
Backend (RaceControl)
    │  WS-Nachricht: {"type": "timing_result", "raw_time": 42.317, "device": "…"}
    │  → Zeitnahme-View zeigt Zeit zur Bestätigung, Zeitnehmer wählt Fahrer

Reset-Taster (GPIO 22, aktiv LOW)
    → measuring = False, Display: "----"
```

---

> **Vollständiges Setup-Handbuch für alle Varianten:** [`LICHTSCHRANKE_SETUP.md`](../LICHTSCHRANKE_SETUP.md)

## Alternativer Client: ELV LSU200

Wer keine GPIO-Lichtschranke am Raspberry Pi aufbauen möchte, kann die **ELV LSU200 USB-Lichtschranke** direkt am Laptop betreiben:

| Merkmal | Raspberry Pi (diese Dateien) | ELV LSU200 (`tools/lsu200_client.py`) |
|---|---|---|
| Hardware | RPi + 2 Reflexlichtschranken | ELV LSU200 (fertiges Gerät) |
| Anschluss | GPIO (auf dem RPi) | USB-COM am Laptop |
| Display | TM1637 oder MAX7219 | — (kein eigenes Display) |
| Läuft auf | Raspberry Pi | Laptop (Windows/Linux) |
| Abhängigkeiten | RPi.GPIO, luma / tm1637 | pyserial, websocket-client |

Beide Varianten senden das gleiche WebSocket-Protokoll an `/ws/timing` und erscheinen als Lichtschranken-Indikator in der Zeitnahme.

---

## WebSocket-Protokoll

### Client → Backend

```json
{ "type": "timing_result", "raw_time": 42.317, "device": "gpio-lichtschranke" }
{ "type": "timing_device_heartbeat" }
```

### Reconnect-Verhalten

- Bei Verbindungsabbruch: automatischer Reconnect nach 3 Sekunden
- Heartbeat alle 5 Sekunden zur Verbindungskontrolle
- Display zeigt `CONN` kurz bei Verbindungsaufbau, dann `----`
- Ohne Backend: Messung läuft normal, Zeit wird lokal angezeigt, nicht gesendet
