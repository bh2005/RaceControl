# Lichtschranke Setup-Handbuch

**RaceControl Pro – Zeitmessung & Hardware-Clients**

Dieses Handbuch beschreibt alle unterstützten Lichtschranken-Varianten, deren Verkabelung,
Softwareinstallation und Konfiguration.

---

## Variantenvergleich

| Merkmal | **A – ELV LSU200** | **B – ALGE Timy** | **C – ALGE Multi-Timy** | **D – RPi + TM1637** | **E – RPi + MAX7219** |
|---|---|---|---|---|---|
| Hardware | ELV LSU200 (fertig) | ALGE Timy2/3 | 2× ALGE Timy | RPi + 2× Lichtschranke | RPi + 2× Lichtschranke |
| Anschluss | USB am Laptop | RS232 / USB-Adapter am Laptop | 2× RS232 / USB-Adapter | GPIO am Raspberry Pi | GPIO am Raspberry Pi |
| Display | — | — | — | TM1637 7-Segment | MAX7219 LED-Matrix |
| Läuft auf | Laptop (Windows/Linux) | Laptop (Windows/Linux) | Laptop (Windows/Linux) | Raspberry Pi | Raspberry Pi |
| Client-Datei | `tools/lsu200_client.py` | `tools/alge_timy_client.py` | `tools/alge_multi_timy_client.py` | `RaPi_lichtschranke/racecontrol_client.py` | `RaPi_lichtschranke/racecontrol_client_max7219.py` |
| Konfiguration | direkt im Script | direkt im Script | `.env`-Datei oder Script | direkt im Script | direkt im Script |
| Mehrere Geräte | — | — | ✅ beliebig viele | — | — |

### Welche Variante passt?

```
Habt ihr ein fertiges Gerät?
├─ ELV LSU200             →  Variante A
├─ ALGE Timy (1 Gerät)    →  Variante B
└─ ALGE Timy (2 Geräte)   →  Variante C

Baut ihr selbst mit Raspberry Pi?
├─ Kleines kompaktes Display   →  Variante D (TM1637)
└─ Großes LED-Matrix-Display   →  Variante E (MAX7219)
```

---

## Gemeinsame Voraussetzungen (Varianten A–C, Laptop)

### Python-Abhängigkeiten installieren

```bash
cd tools
pip install -r requirements.txt
```

Inhalt `requirements.txt`:
```
pyserial>=3.5
websocket-client>=1.7.0
python-dotenv>=1.0.0
```

### RaceControl Backend muss laufen

Alle Clients verbinden sich per WebSocket mit dem Backend:
```
ws://localhost:1980/ws/timing
```
→ Erst das Backend starten, dann den Client.

---

## Variante A – ELV LSU200 (USB am Laptop)

**Datei:** `tools/lsu200_client.py`

### Hardware

- ELV LSU200 Lichtschranken-Set
- USB-Kabel (Typ A–B, liegt dem Gerät bei)

### Anschluss

USB-Kabel vom LSU200 in einen freien USB-Port des Laptops stecken.  
Windows installiert automatisch einen virtuellen COM-Port (sichtbar im Gerätemanager).

### Konfiguration

In `lsu200_client.py` bei Bedarf anpassen:

```python
SERIAL_PORT = None      # None = automatische Erkennung, oder z.B. "COM3"
SERIAL_BAUD = 19200     # fest vorgegeben laut LSU200-Protokoll
BACKEND_WS  = "ws://localhost:1980/ws/timing"
MIN_TIME    = 3.0       # Messungen kürzer als 3 s werden verworfen
```

### Starten

```bash
python lsu200_client.py
```

### Funktionsweise

Die LSU200 wird im Polling-Modus abgefragt (`w`-Kommando). Der Übergang
`Running(1) → Stopped(0)` signalisiert eine abgeschlossene Messung.

---

## Variante B – ALGE Timy (ein Gerät, Laptop)

**Datei:** `tools/alge_timy_client.py`

### Hardware

- ALGE Timy2 oder Timy3
- RS232-Kabel + USB-Seriell-Adapter (FTDI oder CP210x) **oder** Timy mit USB-Ausgang

### Konfiguration

In `alge_timy_client.py` anpassen:

```python
SERIAL_PORT = None      # None = Auto-Detect, oder z.B. "COM4"
SERIAL_BAUD = 9600      # Standard Timy3; manche nutzen 19200
BACKEND_WS  = "ws://localhost:1980/ws/timing"
MIN_TIME    = 3.0
```

Kanal-Zuordnung (anpassen je nach Timy-Programmierung):

```python
channel_map = {
    "c0": "start",
    "c0m": "start_manual",
    "c1": "finish",
    "c1m": "finish_manual",
}
```

### Starten

```bash
python alge_timy_client.py
```

### ALGE RS232-Protokoll

Typische Ausgabezeilen des Timy:

```
 0005 c1 15:43:51,646
m 0008 c0 15:44:00,2849 00
0043 C0 10:34:13.384
```

Format: `[Prefix] [Startnummer] [Kanal] [Tageszeit]`  
Der Client erkennt alle gängigen Varianten automatisch.

---

## Variante C – ALGE Multi-Timy (mehrere Geräte, Laptop)

**Datei:** `tools/alge_multi_timy_client.py`

Für den Einsatz von Start-Timy und Finish-Timy als getrennte Geräte an zwei COM-Ports.

### Konfiguration über `.env`

`.env`-Datei im `tools/`-Ordner anlegen:

```ini
BACKEND_WS=ws://localhost:1980/ws/timing

# COM-Ports der Timys (Gerätemanager → Anschlüsse)
TIMY_START_PORT=COM3
TIMY_FINISH_PORT=COM4

# Baudrate (Standard: 9600)
TIMY_START_BAUD=9600
TIMY_FINISH_BAUD=9600
```

Ohne `.env` versucht der Client die Ports automatisch zu erkennen.

### Weitere Timys hinzufügen

In `alge_multi_timy_client.py` im `TIMY_DEVICES`-Array ergänzen:

```python
{
    "name": "Intermediate-Timy",
    "port": os.getenv("TIMY_INTER_PORT", None),
    "baudrate": 9600,
    "channels": {"c2": "intermediate"},
    "color": "📍"
},
```

### Starten

```bash
python alge_multi_timy_client.py
```

---

## Variante D – Raspberry Pi mit TM1637-Display

**Datei:** `RaPi_lichtschranke/racecontrol_client.py`

### Hardware

- Raspberry Pi (Zero 2 W, 3B oder 4B)
- 2× Reflexlichtschranke (digitaler Ausgang, 5V oder 3,3V kompatibel)
- 1× TM1637 6-stellige 7-Segment-Anzeige
- 1× Drucktaster (Reset)
- Jumper-Kabel

### GPIO-Verkabelung

| Signal | GPIO (BCM) | Pin | Anmerkung |
|---|---|---|---|
| Lichtschranke 1 – Start | GPIO 17 | Pin 11 | RISING-Flanke startet Messung |
| Lichtschranke 2 – Stop  | GPIO 27 | Pin 13 | RISING-Flanke beendet Messung |
| Reset-Taster            | GPIO 22 | Pin 15 | Pullup, aktiv LOW (FALLING) |

### TM1637-Display

| TM1637 | Raspberry Pi |
|---|---|
| VCC | 3,3V oder 5V (Pin 1 / Pin 2) |
| GND | GND (Pin 6) |
| CLK | GPIO 21 (Pin 40) |
| DIO | GPIO 20 (Pin 38) |

### Abhängigkeiten installieren (auf dem RPi)

```bash
pip install websocket-client RPi.GPIO
pip install git+https://github.com/depklyon/raspberrypi-tm1637
```

### Konfiguration

In `racecontrol_client.py` anpassen:

```python
BACKEND_HOST = "192.168.0.100"  # IP des Laptops mit RaceControl
BACKEND_PORT = 1980
MIN_TIME     = 5.0              # Läufe kürzer als 5 s verwerfen
```

### Starten

```bash
python3 racecontrol_client.py
```

---

## Variante E – Raspberry Pi mit MAX7219-Display

**Datei:** `RaPi_lichtschranke/racecontrol_client_max7219.py`

Gleiche GPIO-Verkabelung wie Variante D (Lichtschranken + Reset).

### SPI aktivieren

```bash
sudo raspi-config
# → Interface Options → SPI → Enable
```

### MAX7219-Display

| MAX7219 | Raspberry Pi |
|---|---|
| VCC | 5V (Pin 2 oder 4) |
| GND | GND (Pin 6) |
| CLK | GPIO 11 / SCLK (Pin 23) |
| DIN | GPIO 10 / MOSI (Pin 19) |
| CS  | GPIO 8 / CE0 (Pin 24) |

### Abhängigkeiten installieren (auf dem RPi)

```bash
pip install websocket-client RPi.GPIO luma.led_matrix Pillow
```

### Konfiguration

In `racecontrol_client_max7219.py` anpassen:

```python
BACKEND_HOST          = "192.168.0.100"
BACKEND_PORT          = 1980
MIN_TIME              = 5.0
MAX7219_CASCADED      = 1     # Anzahl kaskadierter Module
MAX7219_BLOCK_ORIENT  = 90    # 0 oder 90 je nach Modulausrichtung
MAX7219_BRIGHTNESS    = 4     # 0–15
```

### Starten

```bash
python3 racecontrol_client_max7219.py
```

---

## Autostart beim RPi-Hochfahren (systemd)

Gilt für Varianten D und E.

```bash
sudo nano /etc/systemd/system/racecontrol.service
```

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

## COM-Port ermitteln

### Windows

**Gerätemanager:**  
`Win + X` → Gerätemanager → Anschlüsse (COM & LPT) → Gerät notieren (z.B. `COM4`)

**PowerShell:**
```powershell
# Alle seriellen Ports auflisten
Get-WmiObject Win32_PnPEntity | Where-Object { $_.Name -like "*COM*" } | Select-Object Name

# Gezielt nach LSU200 suchen
Get-WmiObject Win32_PnPEntity | Where-Object { $_.Name -like "*LSU*" } | Select-Object Name

# Gezielt nach FTDI-Adapter suchen (häufig für ALGE)
Get-WmiObject Win32_PnPEntity | Where-Object { $_.Name -like "*FTDI*" -or $_.Name -like "*CP210*" } | Select-Object Name
```

**Prüfen ob Port frei ist:**
```powershell
netstat -an | findstr :1980   # RaceControl-Port prüfen
```

### Linux / Raspberry Pi

```bash
ls /dev/ttyUSB*     # USB-Seriell-Adapter
ls /dev/ttyACM*     # CDC-ACM (manche USB-Geräte)
ls /dev/serial/by-id/   # stabile Namen unabhängig vom Einsteckreihenfolge

# Detailinfo zu einem Port
udevadm info --name=/dev/ttyUSB0 --attribute-walk | grep -E "idVendor|idProduct|ATTRS"
```

---

## WebSocket-Protokoll

Alle Clients senden an `ws://<backend>:1980/ws/timing`.

### Timing-Ergebnis (LSU200, RPi)

```json
{ "type": "timing_result", "raw_time": 42.317, "device": "lsu200-usb" }
```

### Timing-Impuls (ALGE Timy)

```json
{
  "type": "timing_impulse",
  "device": "alge_timy",
  "bib": 5,
  "channel": "c1",
  "impulse_type": "finish",
  "time_of_day": "15:43:51.646",
  "raw_time": 56791.646,
  "source": "alge_timy"
}
```

### Heartbeat (alle Clients)

```json
{ "type": "timing_device_heartbeat", "device": "lsu200-usb" }
```

### Reconnect-Verhalten

- Verbindungsverlust → automatischer Reconnect nach **3 Sekunden**
- Heartbeat alle **5 Sekunden** zur Verbindungskontrolle
- RPi-Display zeigt `CONN` bei Verbindungsaufbau, dann `----`
- Ohne Backend: Messung läuft normal, Zeit wird lokal angezeigt, nicht gesendet

---

## Troubleshooting

### Client findet keinen COM-Port

- Treiber prüfen (FTDI: `ftdi_sio`, CP210x: `cp210x`)
- Unter Windows: Gerätemanager → Unbekannte Geräte prüfen
- `SERIAL_PORT` im Script explizit setzen (z.B. `"COM4"`)
- USB-Kabel wechseln (Datenkabel, nicht nur Ladekabel)

### Verbindung zum Backend schlägt fehl

- Läuft RaceControl auf Port 1980? → `http://localhost:1980/health` im Browser prüfen
- Firewall-Ausnahme für Port 1980 vorhanden?
- Beim RPi: `BACKEND_HOST` auf die tatsächliche Laptop-IP setzen (per `ipconfig` ermitteln)
- Beide Geräte im selben WLAN?

### Falsche Baudrate (ALGE Timy)

- Timy3 Standard: `9600 Baud`; ältere Modelle / andere Konfiguration: `19200 Baud`
- In der Timy-Konfiguration nachschauen: `MENU → RS232 → Baudrate`
- `SERIAL_BAUD` im Script entsprechend anpassen

### Zeiten werden verworfen (`MIN_TIME`)

- `MIN_TIME` zu hoch eingestellt → im Script reduzieren
- Standard: 3,0 s (Laptop-Clients) / 5,0 s (RPi)

### RPi: SPI-Fehler (MAX7219)

```bash
# SPI-Modul prüfen
lsmod | grep spi
# SPI aktivieren falls nicht vorhanden
sudo raspi-config → Interface Options → SPI → Enable
sudo reboot
```

### ALGE Multi-Timy: Ein Timy wird nicht erkannt

- COM-Ports in `.env` explizit eintragen (nicht auf Auto-Detect verlassen wenn mehrere Adapter)
- Adapter-Reihenfolge: beim Neustart können sich `COM`-Nummern ändern → stabile Namen per `by-id` nutzen (Linux)
