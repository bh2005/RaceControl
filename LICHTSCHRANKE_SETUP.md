# Lichtschranke Setup-Handbuch

**RaceControl Pro – Zeitmessung & Hardware-Clients**

Alle Lichtschranken-Clients und Sketche befinden sich im Ordner `lichtschranken/`.

---

## Variantenvergleich

| Variante | Hardware | Anschluss | Display | Läuft auf | Pfad |
|---|---|---|---|---|---|
| **A** | ELV LSU200 | USB am Laptop | — | Laptop | `lichtschranken/LSU200/` |
| **B** | ALGE Timy2/3 (1 Gerät) | RS232/USB am Laptop | — | Laptop | `lichtschranken/ALGE/` |
| **C** | ALGE Timy (mehrere) | 2× RS232/USB am Laptop | — | Laptop | `lichtschranken/ALGE/` |
| **D** | RPi + 2× Lichtschranke | GPIO | TM1637 | Raspberry Pi | `lichtschranken/RasPi/` |
| **E** | RPi + 2× Lichtschranke | GPIO | MAX7219 | Raspberry Pi | `lichtschranken/RasPi/` |
| **F** | RPi LoRa-Gateway | SX1268 HAT | — | Raspberry Pi | `lichtschranken/RasPi/` |
| **G** | Arduino Nano | USB | TM1637 4-Digit | Standalone | `lichtschranken/Ardoino/` |
| **H** | Arduino Nano | USB | MAX7219 8-Digit | Standalone | `lichtschranken/Ardoino/` |
| **I** | Arduino Nano + RA-02 + DS3231 | LoRa 433 MHz | — | Standalone | `lichtschranken/Ardoino/` |
| **J** | ESP32 | USB / WiFi | TM1637 | Standalone/WiFi | `lichtschranken/ESP32/` |
| **K** | ESP32 | USB / WiFi | MAX7219 | Standalone/WiFi | `lichtschranken/ESP32/` |
| **L** | ESP32 + RA-02 + DS3231 | WiFi primär / LoRa Fallback | — | WiFi/LoRa | `lichtschranken/ESP32/` |
| **M** | u-blox 8 GPS | USB | — | Laptop/RPi | `lichtschranken/GPS/` |
| **N** | ESP32 | Bluetooth SPP | — | direkt am Laptop | `lichtschranken/ESP32/` |

### Entscheidungsbaum

```
Fertiggerät vorhanden?
├─ ELV LSU200              →  Variante A
├─ ALGE Timy (1 Gerät)     →  Variante B
└─ ALGE Timy (2+ Geräte)   →  Variante C

Raspberry Pi vorhanden?
├─ Kabelgebunden, Display   →  Variante D (TM1637) oder E (MAX7219)
└─ Kabellos (Downhill)      →  Variante F (LoRa-Gateway) + I oder L als Sender

Selbst aufbauen (Microcontroller)?
├─ Standalone-Zeitmessung   →  G (TM1637) oder H (MAX7219)
├─ Kabellos, Arduino Nano   →  Variante I (LoRa + RTC)
├─ Kabellos, ESP32          →  Variante L (WiFi → LoRa Fallback)
└─ Kein WLAN, ESP32 ~20 m   →  Variante N (Bluetooth SPP)

Genaue GPS-Zeit als Referenz?
└─ u-blox 8 GPS             →  Variante M (Timesync ans Backend)
```

---

## Setup (alle Laptop-Clients)

### Python-Abhängigkeiten

```bash
cd lichtschranken
bash setup_tools.sh          # installiert alle pip-Pakete + .env anlegen
```

Oder manuell:

```bash
pip install pyserial websocket-client python-dotenv
```

### API-Key konfigurieren

In `lichtschranken/.env`:

```ini
TIMING_API_KEY=xxxx          # Admin → System → Lichtschranken-Schlüssel
BACKEND_WS=ws://localhost:1980/ws/timing
```

### RaceControl Backend muss laufen

Alle Clients verbinden sich per WebSocket mit dem Backend:
```
ws://localhost:1980/ws/timing?key=<API-KEY>
```
→ Erst das Backend starten, dann den Client.

---

## Variante A – ELV LSU200 (USB am Laptop)

**Datei:** `lichtschranken/LSU200/lsu200_client.py`

### Hardware
- ELV LSU200 Lichtschranken-Set + USB-Kabel (liegt bei)

### Konfiguration

```python
SERIAL_PORT = None      # None = auto, oder z.B. "COM3"
SERIAL_BAUD = 19200     # fest vorgegeben laut LSU200-Protokoll
MIN_TIME    = 3.0
```

### Starten
```bash
cd lichtschranken/LSU200
python lsu200_client.py
```

> Linux ohne Treiber: `lichtschranken/LSU200/lsu200_linux_client.py` + `bash setup_linux.sh`

---

## Variante B – ALGE Timy (ein Gerät)

**Datei:** `lichtschranken/ALGE/alge_timy_client.py`

### Konfiguration

```python
SERIAL_PORT    = None   # None = auto, oder z.B. "COM4"
SERIAL_BAUD    = 9600   # Standard Timy3; manche: 19200
TIMING_API_KEY = ""     # oder aus .env
MIN_TIME       = 3.0
```

Kanal-Zuordnung (je nach Timy-Programmierung):

```python
channel_map = {
    "c0": "start",   "c0m": "start_manual",
    "c1": "finish",  "c1m": "finish_manual",
}
```

### Starten
```bash
cd lichtschranken/ALGE
python alge_timy_client.py
```

### ALGE RS232-Protokoll
```
 0005 c1 15:43:51,646
m 0008 c0 15:44:00,2849 00
```

---

## Variante C – ALGE Multi-Timy (mehrere Geräte)

**Datei:** `lichtschranken/ALGE/alge_multi_timy_client.py`

### Konfiguration via `.env`

```ini
TIMING_API_KEY=xxxx
BACKEND_WS=ws://localhost:1980/ws/timing
TIMY_START_PORT=COM3
TIMY_FINISH_PORT=COM4
TIMY_START_BAUD=9600
TIMY_FINISH_BAUD=9600
```

### Starten
```bash
cd lichtschranken/ALGE
python alge_multi_timy_client.py
```

---

## Variante D – Raspberry Pi + TM1637

**Datei:** `lichtschranken/RasPi/racecontrol_client.py`

### GPIO-Verkabelung

| Signal | GPIO (BCM) | Pin |
|---|---|---|
| Lichtschranke Start | GPIO 17 | Pin 11 |
| Lichtschranke Stop  | GPIO 27 | Pin 13 |
| Reset-Taster        | GPIO 22 | Pin 15 |

### TM1637-Display

| TM1637 | RPi |
|---|---|
| CLK | GPIO 21 (Pin 40) |
| DIO | GPIO 20 (Pin 38) |
| VCC | 3,3V oder 5V |

### Abhängigkeiten
```bash
pip install websocket-client RPi.GPIO
pip install git+https://github.com/depklyon/raspberrypi-tm1637
```

### Konfiguration
```python
BACKEND_HOST = "192.168.0.100"  # Laptop-IP
BACKEND_PORT = 1980
MIN_TIME     = 5.0
```

### Starten
```bash
python3 lichtschranken/RasPi/racecontrol_client.py
```

---

## Variante E – Raspberry Pi + MAX7219

**Datei:** `lichtschranken/RasPi/racecontrol_client_max7219.py`

Gleiche GPIO-Verkabelung wie Variante D.

### SPI + MAX7219

```bash
sudo raspi-config  # Interface Options → SPI → Enable
pip install websocket-client RPi.GPIO luma.led_matrix Pillow
```

| MAX7219 | RPi |
|---|---|
| CLK | GPIO 11 / SCLK (Pin 23) |
| DIN | GPIO 10 / MOSI (Pin 19) |
| CS  | GPIO 8 / CE0  (Pin 24) |

---

## Variante F – Raspberry Pi LoRa-Gateway (Ziel)

**Datei:** `lichtschranken/RasPi/lora_ziel_gateway.py`  
**Bauanleitung:** `lichtschranken/RasPi/BAUANLEITUNG_LoRa_Startlichtschranke.md`

Empfängt LoRa-Pakete von Arduino/ESP32-Sendern (Variante I / L) und leitet
sie per HTTP an das RaceControl-Backend weiter. Sendet alle 60 s einen
Zeitsync-Broadcast an alle Sender.

### Hardware
- Raspberry Pi (Zero 2W oder 3B/4B)
- Waveshare SX1268 LoRa HAT (433 MHz)

### Starten
```bash
python3 lichtschranken/RasPi/lora_ziel_gateway.py
```

---

## Variante G – Arduino Nano + TM1637 (Standalone)

**Sketch:** `lichtschranken/Ardoino/arduino_TM1637_lichtschranke/`  
**Bauanleitung:** `lichtschranken/Ardoino/BAUANLEITUNG_Arduino_TM1637_Lichtschranke.md`

Autarke Zeitmessung ohne Server. Ergebnis auf 4-stelligem Display + USB-Serial JSON.

### Pinbelegung
| Signal | Pin |
|---|---|
| Lichtschranke Start | D2 (INT0) |
| Lichtschranke Ziel  | D3 (INT1) |
| Reset-Taster        | D5 |
| TM1637 CLK          | D6 |
| TM1637 DIO          | D7 |

### Flash (PlatformIO)
```bash
cd lichtschranken/Ardoino/arduino_TM1637_lichtschranke
# VS Code → PlatformIO → Upload  (Ctrl+Alt+U)
```

---

## Variante H – Arduino Nano + MAX7219 (Standalone, Live-Anzeige)

**Sketch:** `lichtschranken/Ardoino/arduino_MAX7219_lichtschranke/`  
**Bauanleitung:** `lichtschranken/Ardoino/BAUANLEITUNG_Arduino_MAX7219_Lichtschranke.md`

Wie Variante G, aber 8-stelliges Display zeigt die Zeit **live während der Fahrt** (50 ms-Refresh).

| Signal | Pin |
|---|---|
| MAX7219 DIN | D11 (MOSI) |
| MAX7219 CLK | D13 (SCK)  |
| MAX7219 CS  | D10        |

---

## Variante I – Arduino Nano + LoRa + DS3231 (Sender)

**Sketch:** `lichtschranken/Ardoino/arduino_lora_sender/`  
**Bauanleitung:** `lichtschranken/Ardoino/BAUANLEITUNG_Arduino_LoRa_Sender.md`

Sendet Startzeitpunkt per LoRa 433 MHz an Variante F (Gateway am Ziel).
DS3231 RTC liefert genauen UTC-Timestamp; Zeitsync vom Gateway alle 60 s.

### Konfiguration im Sketch
```cpp
const char LANE[] = "A";    // "A" oder "B"
#define LORA_SF   10        // Spreading Factor (10 ≈ 1,5 km)
#define LORA_POWER 17       // dBm (10 = EU-konform 10 mW ERP)
```

### Paket-Format
```json
{"type":"start","unix":1746612401,"ms":54321,"lane":"A"}
```

---

## Variante J – ESP32 + TM1637 (Standalone / WiFi)

**Sketch:** `lichtschranken/ESP32/esp32_tm1637_lichtschranke/`

DIP-Schalter SW1: `OFF` = Standalone, `ON` = WiFi (sendet Ergebnis an RaceControl).

### WiFi-Konfiguration im Sketch
```cpp
const char* WIFI_SSID  = "RaceControl";
const char* WIFI_PASS  = "geheim";
const char* SERVER_URL = "http://192.168.1.100:1980";
const char* TIMING_KEY = "HIER_DEN_KEY_EINTRAGEN";
```

---

## Variante K – ESP32 + MAX7219 (Standalone / WiFi, Live-Anzeige)

**Sketch:** `lichtschranken/ESP32/esp32_max7219_lichtschranke/`

Wie Variante J + 8-stelliges Live-Display.  
SW2: `OFF` = Helligkeit niedrig, `ON` = Helligkeit hoch.

---

## Variante L – ESP32 + LoRa + WiFi (Start/Split/Finish)

**Sketch:** `lichtschranken/ESP32/esp32_lora_wifi_sender/`  
**Bauanleitung:** `lichtschranken/ESP32/BAUANLEITUNG_ESP32_Lichtschranke.md`

WiFi primär (NTP-Sync, HTTP direkt ans Backend) – LoRa automatischer Fallback.
DIP-Schalter konfigurieren Spur und Checkpoint-Typ.

### DIP-Schalter

| Schalter | OFF | ON |
|---|---|---|
| SW1 | Spur A | Spur B |
| SW2 | CP-Bit 0 = 0 | CP-Bit 0 = 1 |
| SW3 | CP-Bit 1 = 0 | CP-Bit 1 = 1 |
| SW4 | Auto (WiFi→LoRa) | Nur LoRa |

**Checkpoint-Tabelle (SW2+SW3):**

| SW2 | SW3 | Typ |
|---|---|---|
| OFF | OFF | `start` |
| ON  | OFF | `split` (Zwischenzeit 1) |
| OFF | ON  | `split` (Zwischenzeit 2) |
| ON  | ON  | `finish` |

### Zeitsync-Priorität
```
1. WiFi verfügbar → NTP (pool.ntp.org) → DS3231 setzen
2. Kein WiFi      → LoRa-Timesync vom Gateway → DS3231 setzen
3. Kein Sync      → unix=0 → Gateway verwendet Empfangszeitpunkt
```

---

## Variante N – ESP32 Bluetooth SPP (kein WLAN)

**Sketch:** `lichtschranken/ESP32/esp32_bluetooth_lichtschranke/`  
**Szenario-Doku:** `lichtschranken/ESP32/SZENARIO_BLUETOOTH.md`

Kein Router, kein Access Point — der ESP32 verbindet sich direkt per Classic Bluetooth (SPP) mit dem Laptop.
Auf dem Laptop erscheint er als `/dev/rfcomm0` (Linux) oder COM-Port (Windows).
`serial_logger.py` läuft **ohne Änderung** weiter.

### DIP-Schalter (identisch mit Variante L)

| Schalter | OFF | ON |
|---|---|---|
| SW1 | Spur A | Spur B |
| SW2 | CP-Bit 0 = 0 | CP-Bit 0 = 1 |
| SW3 | CP-Bit 1 = 0 | CP-Bit 1 = 1 |

**BT-Name** wird automatisch aus Spur + Checkpoint gesetzt: `RC-BT-A-0`, `RC-BT-B-3` etc.

### Laptop-Setup (einmalig, Linux)

```bash
# 1. Pairen
bluetoothctl
  power on
  scan on          # MAC von "RC-BT-A-0" notieren
  pair AA:BB:CC:DD:EE:FF
  trust AA:BB:CC:DD:EE:FF
  exit

# 2. Virtuellen COM-Port anlegen
sudo rfcomm bind 0 AA:BB:CC:DD:EE:FF

# 3. Logger starten
python lichtschranken/serial_logger.py /dev/rfcomm0
```

### Autostart (systemd)

```ini
# /etc/systemd/system/rfcomm-lichtschranke.service
[Unit]
Description=rfcomm bind RaceControl-BT
After=bluetooth.target

[Service]
Type=oneshot
ExecStart=/usr/bin/rfcomm bind 0 AA:BB:CC:DD:EE:FF
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload && sudo systemctl enable rfcomm-lichtschranke.service
```

### Mehrere Schranken

| Schranke | BT-Name | rfcomm | Port |
|---|---|---|---|
| Start Spur A | RC-BT-A-0 | 0 | /dev/rfcomm0 |
| Ziel Spur A | RC-BT-A-3 | 1 | /dev/rfcomm1 |
| Start Spur B | RC-BT-B-0 | 2 | /dev/rfcomm2 |

`serial_logger.py` je einmal pro Port starten.

---

## Variante M – u-blox 8 GPS (Timesync)

**Datei:** `lichtschranken/GPS/ublox8_gps_client.py`  
**Bauanleitung:** `lichtschranken/GPS/BAUANLEITUNG_GPS_NTP_Server.md`

Live-Monitor + sendet alle 10 s GPS-UTC-Zeit ans Backend (`gps_timesync`).
Das Backend kann den Sync an LoRa-Gateways weiterleiten.

### Konfiguration
```ini
# lichtschranken/.env
TIMING_API_KEY=xxxx
GPS_TIMESYNC_INTERVAL=10     # Sekunden zwischen Syncs
```

### Starten
```bash
python lichtschranken/GPS/ublox8_gps_client.py
# oder: GPS_DEVICE=/dev/ttyACM0 python ublox8_gps_client.py
```

### Timesync-Paket (WebSocket)
```json
{"type":"gps_timesync","unix":1746612345,"utc":"2026-05-07  14:32:01.00 UTC","fix":1,"sats":8,"hdop":1.2,"source":"ublox8"}
```

---

## USB-Serial JSON-Logger (Arduino / ESP32)

**Datei:** `lichtschranken/serial_logger.py`

Liest JSON-Zeitmessungen direkt vom USB-Anschluss (parallel zu WiFi/LoRa).
Alle Arduino/ESP32-Sketche geben beim Auslösen eine JSON-Zeile aus.

```bash
pip install pyserial

python lichtschranken/serial_logger.py          # auto-detect, 115200 Baud
python lichtschranken/serial_logger.py COM3 9600  # Arduino Nano
```

**Beispiel-Ausgabe:**
```
14:32:01.234  [ERGEBNIS]  arduino_tm1637        01:23.45  (83456 ms)
14:32:05.891  [START  ]   Spur=A  CP=0  unix=1746612401  14:32:05 UTC
```

Log-Datei: `zeitmessung_DATUM.csv` (automatisch).

---

## Autostart am Raspberry Pi (systemd)

Gilt für alle RPi-Clients (Varianten D, E, F).

```bash
sudo nano /etc/systemd/system/racecontrol.service
```

```ini
[Unit]
Description=RaceControl Lichtschranken-Client
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/lichtschranken/RasPi/racecontrol_client.py
WorkingDirectory=/home/pi/lichtschranken/RasPi
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
sudo journalctl -u racecontrol -f
```

---

## COM-Port ermitteln

### Windows
```powershell
Get-WmiObject Win32_PnPEntity | Where-Object { $_.Name -like "*COM*" } | Select-Object Name
Get-WmiObject Win32_PnPEntity | Where-Object { $_.Name -like "*FTDI*" -or $_.Name -like "*CP210*" -or $_.Name -like "*CH34*" } | Select-Object Name
```

### Linux
```bash
ls /dev/ttyUSB*   # USB-Seriell (FTDI, CP210x, CH340)
ls /dev/ttyACM*   # CDC-ACM (Arduino, u-blox GPS)
ls /dev/serial/by-id/    # stabile Namen
```

---

## WebSocket-Protokoll

Alle Clients senden an `ws://<backend>:1980/ws/timing?key=<API-KEY>`.

### Timing-Ergebnis (LSU200, RPi)
```json
{"type":"timing_result","raw_time":42.317,"device":"lsu200-usb"}
```

### Timing-Impuls (ALGE Timy)
```json
{"type":"timing_impulse","device":"alge_timy","bib":5,"channel":"c1","impulse_type":"finish","time_of_day":"15:43:51.646","raw_time":56791.646}
```

### Trigger (Arduino/ESP32 LoRa/WiFi)
```json
{"type":"start","unix":1746612401,"lane":"A","cp":0}
{"type":"split","unix":1746612445,"lane":"A","cp":1}
{"type":"finish","unix":1746612489,"lane":"A","cp":3}
```

### GPS-Timesync
```json
{"type":"gps_timesync","unix":1746612345,"fix":1,"sats":8,"hdop":1.2,"source":"ublox8"}
```

### Heartbeat (alle Clients)
```json
{"type":"timing_device_heartbeat","device":"lsu200-usb"}
```

---

## Troubleshooting

| Problem | Lösung |
|---|---|
| Client findet keinen COM-Port | `SERIAL_PORT` explizit setzen; Treiber prüfen (CH340, FTDI, CP210x) |
| Verbindung zum Backend schlägt fehl | Port 1980 offen? `http://localhost:1980/health` prüfen; Firewall? |
| LoRa Init FEHLER | RA-02 mit **3,3V** betreiben; NSS/RST/DIO0-Pins prüfen |
| Kein Zeitsync empfangen | Gateway läuft? SF auf beiden Seiten gleich? UART-Port korrekt? |
| Lichtschranke prellt | `DEBOUNCE_MS` auf 500 erhöhen |
| `unix=0` im LoRa-Paket | DS3231 nicht gefunden oder kein Sync – Gateway übernimmt Timestamp |
| GPS kein Fix | Freie Himmelssicht; `cgps -s` prüfen; innen: bis 10 min warten |
| API-Key fehlt | `lichtschranken/.env` prüfen: `TIMING_API_KEY=xxx` |
| ALGE Baudrate falsch | Timy: `MENU → RS232 → Baudrate`; Standard 9600, ältere 19200 |
