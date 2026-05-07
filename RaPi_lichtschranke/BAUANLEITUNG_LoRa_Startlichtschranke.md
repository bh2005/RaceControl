# Bauanleitung: LoRa-Startlichtschranke für Downhill / Seifenkiste

**Autor:** BH2005 · MSC Braach e.V. im ADAC  
**Zweck:** Kabellose Übertragung des Start-Triggers per LoRa (433 MHz) zum RaceControl-Server am Ziel  
**Reichweite:** bis 5 km (Freifeldtest Waveshare SX1268)

---

## 1. Konzept

```
[Lichtschranke am Start]
        │ GPIO
[Raspberry Pi Zero 2W]
[+ Waveshare LoRa HAT]
        │ 433 MHz LoRa ~
[Waveshare LoRa HAT]
[+ Raspberry Pi am Ziel]
        │ LAN / WLAN
[RaceControl Server]
```

Der Start-Pi erfasst den **Timestamp lokal** beim Auslösen der Lichtschranke und sendet ein kleines LoRa-Paket (< 40 Byte) zum Ziel-Pi. Dieser leitet es per HTTP-POST an das RaceControl-Backend weiter. Die **Timing-Genauigkeit** bleibt erhalten, da der Timestamp vor der Übertragung gestempelt wird.

---

## 2. Benötigte Hardware

### Start-Seite (Sender)

| Artikel | Bezugsquelle | Art.-Nr. | ca. Preis |
|---------|-------------|----------|-----------|
| Raspberry Pi Zero 2W | Reichelt / Berrybase | — | ~18 € |
| **Waveshare LoRa HAT 433 MHz (SX1268)** | Reichelt | RPIZ SHD LORA433 | **19,60 €** |
| 433 MHz Antenne (mitgeliefert) | — | — | enthalten |
| MicroSD-Karte 16 GB | — | — | ~5 € |
| Lichtschranken-Modul (IR, z.B. E18-D80NK) | Amazon / AliExpress | — | ~5 € |
| Gehäuse (wetterfest, IP65) | Baumarkt | — | ~8 € |
| Powerbank 10.000 mAh | — | — | ~15 € |
| **Gesamt Start** | | | **~70 €** |

### Ziel-Seite (Empfänger / Gateway)

| Artikel | Bezugsquelle | Art.-Nr. | ca. Preis |
|---------|-------------|----------|-----------|
| Raspberry Pi 3B+ (oder 4) | Reichelt | — | ~35 € |
| **Waveshare LoRa HAT 433 MHz (SX1268)** | Reichelt | RPIZ SHD LORA433 | **19,60 €** |
| 433 MHz Antenne (mitgeliefert) | — | — | enthalten |
| **Gesamt Ziel** (wenn Pi bereits vorhanden) | | | **~20 €** |

> **Hinweis:** Das HAT passt auf jeden 40-Pin Raspberry Pi (Pi Zero 2W, Pi 3, Pi 4).

---

## 3. Hardware-Aufbau

### 3.1 LoRa HAT aufstecken

Das Waveshare LoRa HAT wird direkt auf den 40-Pin GPIO-Header des Raspberry Pi gesteckt.

```
Pi GPIO 40-Pin
    │
Waveshare SX1268 HAT (direkt aufstecken)
    │
433 MHz Stabantenne (SMA-Buchse, im Lieferumfang)
```

**Wichtig:** Antenne immer **vor** dem Einschalten anschließen — ohne Antenne kann der SX1268 beschädigt werden.

### 3.2 Lichtschranke anschließen (Start-Pi)

Die Lichtschranke wird direkt an GPIO-Pins des Pi angeschlossen (die HAT-Pins GPIO 17/27 bleiben frei):

```
Lichtschranke E18-D80NK:
  Braun  → 5V  (Pin 2)
  Blau   → GND (Pin 6)
  Schwarz → GPIO 17 (Pin 11) — Sensor-Ausgang (LOW wenn unterbrochen)
```

> Das HAT belegt GPIO 8 (CE0), 10 (MOSI), 9 (MISO), 11 (SCLK) für SPI  
> sowie GPIO 18 (M0) und GPIO 23 (M1) für den Betriebsmodus des SX1268.  
> GPIO 17 (Lichtschranke) ist frei.

### 3.3 HAT-Schalterstellung (UART-Modus)

Das Waveshare HAT unterstützt SPI und UART. Für dieses Projekt nutzen wir **UART** (einfacher):

- DIP-Schalter: **A=OFF, B=OFF** → UART über `/dev/ttyS0` (Pi Zero 2W) bzw. `/dev/ttyAMA0` (Pi 3/4)

---

## 4. Raspberry Pi einrichten

### 4.1 Raspberry Pi OS Lite installieren

```bash
# Mit Raspberry Pi Imager auf MicroSD flashen:
# OS: Raspberry Pi OS Lite (64-bit)
# Hostname: lora-start  (Sender) / lora-ziel  (Empfänger)
# SSH aktivieren, WLAN konfigurieren (nur Ziel-Pi benötigt WLAN/LAN)
```

### 4.2 UART aktivieren

```bash
sudo raspi-config
# → Interface Options → Serial Port
#   "Login shell over serial?" → No
#   "Serial port hardware enabled?" → Yes
sudo reboot
```

### 4.3 Abhängigkeiten installieren

```bash
sudo apt update && sudo apt install -y python3-pip python3-serial
pip3 install requests RPi.GPIO
```

---

## 5. Software

### 5.1 Sender-Script: `lora_start_sender.py`

Läuft auf dem **Start-Pi**. Wartet auf die Lichtschranke und sendet bei Auslösung ein LoRa-Paket mit Timestamp.

```python
#!/usr/bin/env python3
"""
LoRa-Startlichtschranke – Sender (Start-Pi)
Waveshare SX1268 HAT, UART-Modus
"""
import time
import json
import serial
import RPi.GPIO as GPIO

# ── Konfiguration ──────────────────────────────────────────────────────────────
LICHTSCHRANKE_PIN = 17          # GPIO-Pin der Lichtschranke (BCM)
UART_PORT         = '/dev/ttyS0'  # Pi Zero 2W: ttyS0 | Pi 3/4: ttyAMA0
UART_BAUD         = 9600
DEBOUNCE_MS       = 200         # Entprellzeit in Millisekunden
LANE              = "A"         # Spur: "A" oder "B" (bei Zwei-Spur-Betrieb)

# ── GPIO-Setup ─────────────────────────────────────────────────────────────────
GPIO.setmode(GPIO.BCM)
GPIO.setup(LICHTSCHRANKE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# ── UART zum LoRa HAT ──────────────────────────────────────────────────────────
ser = serial.Serial(UART_PORT, UART_BAUD, timeout=1)
time.sleep(0.1)

last_trigger = 0.0

def on_lichtschranke(channel):
    global last_trigger
    now = time.time()
    # Entprellung
    if (now - last_trigger) < (DEBOUNCE_MS / 1000.0):
        return
    last_trigger = now

    payload = json.dumps({
        "type": "start",
        "ts":   round(now, 4),   # Unix-Timestamp mit 0,1 ms Genauigkeit
        "lane": LANE,
    })

    # LoRa-Paket senden (UART → SX1268 leitet es per LoRa weiter)
    ser.write((payload + "\n").encode())
    print(f"[SEND] {payload}")

# Interrupt: fallende Flanke (Lichtschranke unterbrochen → LOW)
GPIO.add_event_detect(
    LICHTSCHRANKE_PIN,
    GPIO.FALLING,
    callback=on_lichtschranke,
    bouncetime=DEBOUNCE_MS,
)

print("LoRa-Startlichtschranke aktiv. Warte auf Auslösung …")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
    ser.close()
```

---

### 5.2 Gateway-Script: `lora_ziel_gateway.py`

Läuft auf dem **Ziel-Pi** (am Server). Empfängt LoRa-Pakete und leitet sie als HTTP-POST an das RaceControl-Backend weiter.

```python
#!/usr/bin/env python3
"""
LoRa-Gateway – Empfänger (Ziel-Pi)
Waveshare SX1268 HAT, UART-Modus
Leitet Start-Trigger per HTTP an RaceControl-Backend weiter.
"""
import time
import json
import serial
import requests

# ── Konfiguration ──────────────────────────────────────────────────────────────
UART_PORT      = '/dev/ttyAMA0'          # Pi 3/4: ttyAMA0 | Pi Zero: ttyS0
UART_BAUD      = 9600
SERVER_URL     = 'http://localhost:1980' # RaceControl-Backend
TIMING_API_KEY = 'HIER_DEN_KEY_EINTRAGEN'  # Aus Admin → System → API-Key

HEADERS = {
    "X-Timing-Key": TIMING_API_KEY,
    "Content-Type": "application/json",
}

# ── UART ───────────────────────────────────────────────────────────────────────
ser = serial.Serial(UART_PORT, UART_BAUD, timeout=2)
time.sleep(0.1)

print(f"LoRa-Gateway aktiv. Warte auf Pakete von {UART_PORT} …")

while True:
    try:
        raw = ser.readline()
        if not raw:
            continue

        line = raw.decode('utf-8', errors='ignore').strip()
        if not line:
            continue

        print(f"[RECV] {line}")

        data = json.loads(line)

        if data.get("type") == "start":
            # An RaceControl-Backend weiterleiten
            payload = {
                "timestamp": data["ts"],
                "lane":      data.get("lane", "A"),
                "source":    "lora",
            }
            try:
                r = requests.post(
                    f"{SERVER_URL}/api/timing/start",
                    json=payload,
                    headers=HEADERS,
                    timeout=3,
                )
                print(f"[POST] {r.status_code} – {r.text[:80]}")
            except requests.RequestException as e:
                print(f"[ERR]  HTTP-Fehler: {e}")

    except json.JSONDecodeError:
        print(f"[WARN] Kein gültiges JSON: {line!r}")
    except Exception as e:
        print(f"[ERR]  {e}")
        time.sleep(0.5)
```

---

### 5.3 Autostart (systemd)

Damit die Scripts nach dem Booten automatisch starten:

**Sender (Start-Pi):** `/etc/systemd/system/lora-sender.service`
```ini
[Unit]
Description=LoRa Startlichtschranke Sender
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/lora_start_sender.py
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

**Gateway (Ziel-Pi):** `/etc/systemd/system/lora-gateway.service`
```ini
[Unit]
Description=LoRa Gateway RaceControl
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/lora_ziel_gateway.py
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

```bash
# Aktivieren:
sudo systemctl enable lora-sender   # bzw. lora-gateway
sudo systemctl start  lora-sender
sudo systemctl status lora-sender
```

---

## 6. HAT konfigurieren (Sendeleistung / Frequenz)

Das Waveshare HAT wird per AT-Befehle über UART konfiguriert. Standardmäßig funktioniert es out-of-the-box mit 433,125 MHz und 9600 Baud. Für optimale Reichweite:

```bash
# Einmalig im Terminal auf dem Pi ausführen:
python3 - <<'EOF'
import serial, time
s = serial.Serial('/dev/ttyS0', 9600, timeout=1)
# Sendeleistung auf Maximum (22 dBm)
s.write(b'AT+POWER=22\r\n'); time.sleep(0.2); print(s.read(100))
# Datenrate auf niedrigste Stufe für max. Reichweite (0.3 kbps)
s.write(b'AT+RATE=1\r\n');  time.sleep(0.2); print(s.read(100))
s.close()
EOF
```

> Niedrigere Datenrate = höhere Reichweite. Bei 0,3 kbps und 22 dBm sind in offenem Gelände 3–5 km realistisch.

---

## 7. EU-Frequenzregelung (433 MHz)

| Parameter | Wert |
|-----------|------|
| Frequenzband | 433,05–434,79 MHz (ISM-Band) |
| Max. Sendeleistung | 10 mW ERP (10 dBm) — SX1268 hat 22 dBm, ggf. reduzieren |
| Duty Cycle | max. **10 %** (deutlich weniger restriktiv als 868 MHz!) |
| Zulassung | CE-zertifiziert, keine Anmeldung erforderlich |

> Bei einer Seifenkistenveranstaltung mit ~100 Starts à 40-Byte-Paket liegt die Sendedauer weit unter 0,1 % — kein Problem.

---

## 8. Zwei-Spur-Betrieb (Spur A + B)

Für Downhill-Rennen mit zwei parallelen Spuren zwei separate Sender aufbauen:

```
[Lichtschranke Spur A] → [Pi + HAT, LANE="A"] ──┐
                                                   │ LoRa 433 MHz
[Lichtschranke Spur B] → [Pi + HAT, LANE="B"] ──┘
                                                   │
                                          [Ziel-Gateway-Pi]
                                                   │
                                          [RaceControl Backend]
```

Das Gateway-Script unterscheidet anhand des `"lane"`-Feldes im JSON-Paket.

---

## 9. Kosten-Zusammenfassung (Gesamtprojekt)

| Komponente | Preis |
|-----------|-------|
| 2× Waveshare LoRa HAT SX1268 | **39,20 €** |
| Raspberry Pi Zero 2W (Sender) | 18,00 € |
| MicroSD + Powerbank + Gehäuse | 28,00 € |
| Lichtschranken-Modul | 5,00 € |
| Raspberry Pi am Ziel (falls nicht vorhanden) | 35,00 € |
| **Gesamt (ohne vorhandenen Ziel-Pi)** | **~125 €** |
| **Gesamt (mit vorhandenem Ziel-Pi)** | **~90 €** |

---

## 10. Troubleshooting

| Problem | Lösung |
|---------|--------|
| Keine Verbindung UART | `ls /dev/tty*` prüfen; raspi-config Serial nochmal kontrollieren |
| Paket kommt nicht an | Antenne prüfen; Sichtlinie zu Hindernissen prüfen; Sendeleistung erhöhen |
| Lichtschranke prellt | `DEBOUNCE_MS` erhöhen (z.B. auf 500) |
| Gateway sendet nicht ans Backend | `TIMING_API_KEY` aus Admin → System kopieren; Server-URL prüfen |
| Pi startet Service nicht | `journalctl -u lora-sender -n 50` für Fehlermeldungen |
