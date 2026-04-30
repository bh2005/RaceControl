# Bauanleitung – Zieleinheit mit GPS/NTP-Zeitsynchronisation

**Projekt:** RaceControl Pro / live-race.de  
**Einsatz:** Downhill MTB · Ski-Abfahrt · Seifenkistenrennen · Rally-Zieleinheit  
**Schwierigkeit:** Einsteiger  
**Bauzeit:** ca. 2–3 Stunden

---

## Warum diese Einheit?

Die Standard-Lichtschranke (`racecontrol_client.py`) misst die Zeit **zwischen zwei Schranken
auf demselben Gerät** — Start und Ziel müssen nebeneinander liegen.

Bei Downhill, Seifenkiste und Rally liegen Start und Ziel **Kilometer auseinander**. Hier gilt:

```
Standard-Einheit:   START-GPIO ──────────────────── STOP-GPIO
                    (ein Gerät, misst Δt direkt)

Diese Einheit:      Planstart 12:01:00  (im Backend hinterlegt)
                    Ziel-GPIO löst aus  (RPi liest Systemuhr)
                    Backend berechnet:  12:03:47.412 − 12:01:00 = 2:47.412
```

Start-Gerät und Ziel-Gerät sprechen **nie direkt miteinander** — beide senden
unabhängig über LTE/WLAN an `live-race.de`. Kein Funkkabel, kein Peer-to-Peer.

---

## Zeitsynchronisation: Welche Methode?

| Methode | Genauigkeit | Vorteil | Wann einsetzen |
|---------|------------|---------|----------------|
| **NTP via Internet** (systemd-timesyncd) | ±10–50 ms | Kein Hardware-Aufwand | LTE-Verbindung vorhanden (SaaS-Betrieb) |
| **NTP via LAN** (lokaler Zeitserver) | ±1–5 ms | Sehr präzise, kein Internet | Festes WLAN am Veranstaltungsort |
| **GPS-Maus (ublox) via USB** | ±100–500 ms | Plug & Play, kein SIM, kein Funkkabel | Kein LTE, aber GPS-Empfang vorhanden |
| **GPS-Modul (ublox) mit PPS** | ±1 µs | Höchste Präzision, offline | Profi-Einsatz, Wald/Berg ohne Mobilfunk |
| **DCF77 Hardware-Empfänger** | ±1–10 ms | Komplett offline, kein GPS nötig | Tunnel, Tieflagen, schlechter GPS-Empfang |

> Für Laufzeiten im Bereich 30–300 Sekunden (Seifenkiste, Downhill) ist ±500 ms absolut
> ausreichend. **NTP via LTE ist die einfachste Lösung** und für `live-race.de`
> die empfohlene Variante.  
> Die **GPS-Maus** bietet sich an, wenn kein LTE verfügbar ist, der Veranstaltungsort
> aber freien Himmel hat (typisch für Downhill-Strecken).

---

## Teileliste

### Pflichtteile (immer)

| # | Bauteil | Menge | Preis ca. | Quelle |
|---|---------|-------|-----------|--------|
| 1 | Raspberry Pi Zero 2 WH | 1 | 22 € | Berrybase, Pi-Shop.de |
| 2 | MicroSD 32 GB, Class 10 / A1 | 1 | 9 € | Amazon |
| 3 | Reflexionslichtschranke 5V NPN | 1 | 15 € | Amazon, AliExpress |
| 4 | Retroreflektor (Fahrrad-Rückstrahler) | 1 | 2 € | Fahrradladen |
| 5 | TM1637 6-stellige 7-Segment-Anzeige | 1 | 6 € | Amazon |
| 6 | DIP-Schalter Modul 4-polig | 1 | 2 € | Amazon |
| 7 | Drucktaster 12 mm NO | 1 | 0,80 € | Reichelt |
| 8 | Jumper-Kabel F-F, 30 cm, 40er-Set | 1 | 4 € | Amazon |
| 9 | Powerbank 10.000 mAh (Micro-USB) | 1 | 18 € | Amazon |
| 10 | Gehäuse IP65, 120 × 80 × 55 mm | 1 | 8 € | Reichelt |
| | **Summe Basis** | | **~87 €** | |

### Zusatzteile – GPS-Variante A: USB-GPS-Maus

| # | Bauteil | Menge | Preis ca. | Quelle |
|---|---------|-------|-----------|--------|
| 11 | **USB-GPS-Maus mit ublox-Chip** (z.B. GlobalSat BU-353S4, oder generisch „ublox 7/8 USB") | 1 | 15–25 € | Amazon |
| 12 | Micro-USB OTG-Adapter (für Pi Zero) | 1 | 2 € | Amazon |
| | **Summe GPS-Maus-Variante** | | **~104–115 €** | |

> **Empfohlene Geräte:**  
> - GlobalSat BU-353S4 (SiRF Star IV, NMEA, sehr zuverlässig, ~20 €)  
> - Geräte mit ublox 7 oder ublox 8 Chip (NMEA-kompatibel, ~15–20 €)  
> - Jede GPS-Maus die unter Linux als `/dev/ttyUSB0` oder `/dev/ttyACM0` erscheint

### Zusatzteile – GPS-Variante B: ublox-Modul mit PPS (Profi)

| # | Bauteil | Menge | Preis ca. | Quelle |
|---|---------|-------|-----------|--------|
| 11b | **ublox NEO-M8N Breakout Board** (mit PPS-Pin) | 1 | 20–30 € | Amazon, AliExpress |
| 12b | Level-Shifter 3,3V↔5V (für UART+PPS) | 1 | 3 € | Amazon |
| 13b | Verlängerungskabel 4-adrig, 1–2 m | 1 | 3 € | Baumarkt |
| | **Summe PPS-Variante** | | **~115–125 €** | |

> Der PPS-Ausgang (Pulse Per Second) liefert ein GPIO-Signal exakt bei Sekundenübergang —
> chrony nutzt das für Präzision im Mikrosekundenbereich. Für Kart-Slalom/Seifenkiste
> weit überdimensioniert, aber für professionelle Rally-Zeitnahme sinnvoll.

---

## GPIO-Belegung

| Funktion | GPIO (BCM) | Board-Pin | Bemerkung |
|----------|-----------|-----------|-----------|
| Lichtschranke Ziel | GPIO 27 | Pin 13 | Einziger Sensor dieser Einheit |
| Reset-Taster | GPIO 22 | Pin 15 | Pullup, aktiv LOW |
| DIP 1 – Spurwahl | GPIO 5 | Pin 29 | ON(LOW)=Spur B, OFF(HIGH)=Spur A |
| TM1637 CLK | GPIO 21 | Pin 40 | |
| TM1637 DIO | GPIO 20 | Pin 38 | |
| **GPS PPS-Signal** | **GPIO 18** | **Pin 12** | Nur Variante B (ublox-Modul mit PPS) |
| **GPS TX → RPi RX** | **GPIO 15 (RXD)** | **Pin 10** | Nur Variante B (UART) |
| 5 V (Sensor VCC) | — | Pin 2 | |
| 3,3 V (Display + GPS-Modul VCC) | — | Pin 1 | |
| GND | — | Pin 6, 9 … | |

> **Variante A (GPS-Maus):** Nur USB, kein zusätzliches GPIO nötig.  
> **Variante B (ublox-Modul):** UART-TX des Moduls → RPi RXD (Pin 10), PPS → GPIO 18.

---

## Schaltplan

### Variante A – USB-GPS-Maus

```
                    Raspberry Pi Zero 2 W
                   ┌──────────────────────────┐
                   │  Pin 1  (3,3V) ───────────── TM1637 VCC
                   │  Pin 2  (5V)   ───────────── Lichtschranke VCC (braun)
                   │  Pin 6  (GND)  ──┬─────────── TM1637 GND
                   │                  ├─────────── Lichtschranke GND (blau)
                   │                  ├─────────── Reset-Taster → GND
                   │                  └─────────── DIP COM → GND
                   │  Pin 13 (GPIO27) ──────────── Lichtschranke Signal (schwarz)
                   │  Pin 15 (GPIO22) ──────────── Reset-Taster
                   │  Pin 29 (GPIO 5) ──────────── DIP 1 Spurwahl
                   │  Pin 38 (GPIO20) ──────────── TM1637 DIO
                   │  Pin 40 (GPIO21) ──────────── TM1637 CLK
                   │  USB (OTG)       ──────────── GPS-Maus (ublox)
                   └──────────────────────────┘
```

### Variante B – ublox NEO-M8N mit PPS

```
                    Raspberry Pi Zero 2 W
                   ┌──────────────────────────┐
                   │  Pin 1  (3,3V) ─────────────────────────── TM1637 VCC
                   │                ─────────────────────────── ublox VCC (3,3V)
                   │  Pin 2  (5V)   ───────────── Lichtschranke VCC (braun)
                   │  Pin 6  (GND)  ──┬─────────── TM1637 GND
                   │                  ├─────────── Lichtschranke GND
                   │                  ├─────────── ublox GND
                   │                  ├─────────── Reset-Taster → GND
                   │                  └─────────── DIP COM → GND
                   │  Pin 10 (RXD)  ──────────── ublox TX
                   │  Pin 12 (GPIO18)─────────── ublox PPS
                   │  Pin 13 (GPIO27) ──────────── Lichtschranke Signal
                   │  Pin 15 (GPIO22) ──────────── Reset-Taster
                   │  Pin 29 (GPIO 5) ──────────── DIP 1 Spurwahl
                   │  Pin 38 (GPIO20) ──────────── TM1637 DIO
                   │  Pin 40 (GPIO21) ──────────── TM1637 CLK
                   └──────────────────────────┘
```

> Bei Variante B: Zwischen ublox-TX und RPi-RX einen **Level-Shifter** schalten,
> wenn das Modul mit 5V arbeitet. NEO-M8N Breakout Boards laufen meist mit 3,3V —
> dann direkt verbinden.

---

## Software-Installation

### Schritt 1 – Raspberry Pi OS Lite flashen

Raspberry Pi Imager → „Raspberry Pi OS Lite (64-bit)"  
Vor dem Flashen konfigurieren:
- Hostname: `rc-ziel-a` (Spur A) / `rc-ziel-b` (Spur B)
- WLAN + SSH aktivieren

```bash
ssh pi@rc-ziel-a.local
sudo apt update && sudo apt upgrade -y
```

### Schritt 2 – Python-Abhängigkeiten

```bash
pip install websocket-client RPi.GPIO
pip install git+https://github.com/depklyon/raspberrypi-tm1637

mkdir -p ~/RaPi_lichtschranke
# racecontrol_downhill_finish.py übertragen (scp oder git clone)
```

### Schritt 3 – Client konfigurieren

Am Anfang von `racecontrol_downhill_finish.py` anpassen:

```python
BACKEND_HOST   = "192.168.0.100"   # IP des Laptops ODER z.B. "msc-braach.live-race.de"
BACKEND_PORT   = 1980              # bei live-race.de: 443 + WSS
TIMING_API_KEY = ""                # Admin → System → Lichtschranken-API-Key eintragen
MIN_TIME_S     = 10.0              # Mindestzeit – Fehlauslösungen ignorieren
```

Für `live-race.de` (SaaS):
```python
BACKEND_WS = f"wss://msc-braach.live-race.de/ws/timing?key={TIMING_API_KEY}"
```

---

## Option A – NTP-Synchronisation (empfohlen bei Netzverbindung)

Keine zusätzliche Hardware nötig. `systemd-timesyncd` ist auf Raspberry Pi OS
standardmäßig aktiv und synchronisiert die Uhr automatisch bei Netzverbindung.

```bash
timedatectl status
```

Erwartete Ausgabe:
```
System clock synchronized: yes          ← wichtig
              NTP service: active
```

Zeigt `synchronized: no` → WLAN/LTE-Verbindung prüfen.

---

## Option B – USB-GPS-Maus (Variante A, einfach)

### gpsd installieren und konfigurieren

```bash
sudo apt install gpsd gpsd-clients chrony -y
```

GPS-Maus einstecken und Gerät ermitteln:

```bash
ls /dev/ttyUSB* /dev/ttyACM*
# typisch: /dev/ttyUSB0 oder /dev/ttyACM0
```

**gpsd konfigurieren** (`/etc/default/gpsd`):

```bash
sudo nano /etc/default/gpsd
```

```ini
START_DAEMON="true"
USBAUTO="true"
DEVICES="/dev/ttyUSB0"
GPSD_OPTIONS="-n"
```

```bash
sudo systemctl enable gpsd
sudo systemctl start gpsd
```

### GPS-Empfang testen

```bash
cgps -s
# oder:
gpsmon
```

Erwartete Ausgabe (nach 1–2 Minuten freier Himmel):
```
Time:     2026-04-30T10:01:34.000Z
Latitude: 50.xxxx N
Fix:      3D
Sats:     8
```

Kein Fix (`No Fix`):
- Antenne mit freier Sicht zum Himmel ausrichten
- 1–3 Minuten warten (Kaltstart)
- Gerät an einem anderen USB-Port probieren

### chrony mit GPS-Zeit konfigurieren

```bash
sudo nano /etc/chrony/chrony.conf
```

```
# GPS via gpsd Shared Memory
refclock SHM 0 refid GPS precision 1e-1 offset 0.9999 delay 0.2

# Fallback auf NTP wenn Netz vorhanden
server 0.de.pool.ntp.org iburst
makestep 1.0 3
rtcsync
```

```bash
sudo systemctl restart chrony
chronyc sources -v
```

Erwartete Ausgabe:
```
MS Name/IP address    Stratum  Poll  Reach  LastRx  Last sample
=================================================================
#? GPS                      0     4    377      7    +0.245s[  +0.245s] +/-  0.200s
^* 0.de.pool.ntp.org        2     6    377     49    -2.3ms[  -2.3ms] +/-   10ms
```

> Das `*` kennzeichnet die aktive Quelle. GPS allein (ohne PPS) hat typisch ±100–500 ms
> Offset — ausreichend für Laufzeiten ab ~10 Sekunden. Bei vorhandenem Internet wird
> NTP bevorzugt (viel präziser), GPS dient als Fallback.

---

## Option C – ublox NEO-M8N mit PPS (Variante B, Profi)

### UART auf dem RPi freischalten

```bash
sudo raspi-config
# → Interface Options → Serial Port
# Login shell over serial: No
# Serial port hardware: Yes
sudo reboot
```

### gpsd mit UART konfigurieren

```bash
sudo nano /etc/default/gpsd
```

```ini
START_DAEMON="true"
USBAUTO="false"
DEVICES="/dev/ttyAMA0"
GPSD_OPTIONS="-n"
```

### PPS-Kernel-Modul laden

```bash
sudo nano /boot/config.txt
```

Zeile hinzufügen:
```
dtoverlay=pps-gpio,gpiopin=18
```

```bash
sudo reboot
# Nach Neustart:
sudo modprobe pps_gpio
ls /dev/pps*   # → /dev/pps0
```

### chrony mit UART-GPS + PPS konfigurieren

```bash
sudo nano /etc/chrony/chrony.conf
```

```
# GPS NMEA via UART (SHM 0) – grobe Zeit
refclock SHM 0 refid GPS precision 1e-1 offset 0.9999 delay 0.2

# PPS via GPIO 18 (SHM 1 oder direkt /dev/pps0) – Präzision im µs-Bereich
refclock PPS /dev/pps0 refid PPS lock GPS precision 1e-9

# Fallback NTP
server 0.de.pool.ntp.org iburst
makestep 1.0 3
rtcsync
```

```bash
sudo systemctl restart chrony
chronyc sources -v
```

Erwartete Ausgabe mit aktivem PPS:
```
MS Name/IP address    Stratum  Poll  Reach  LastRx  Last sample
=================================================================
#? GPS                      0     4    377      7    +0.245s[  +0.245s] +/-  0.200s
#* PPS                      0     4    377      7    +14ns[  +14ns] +/-   22ns
```

> `PPS` mit `*` und Offset im Nanosekundenbereich = perfekte Synchronisation.
> Besser als DCF77, kein Empfangsproblem in Gebäuden oder bei Interferenzen.

### PPS-Signal testen

```bash
sudo apt install pps-tools -y
sudo ppstest /dev/pps0
```

Erwartete Ausgabe:
```
trying PPS source "/dev/pps0"
ok, found 1 source(s), now start fetching data
source 0 - assert 1746000001.000000001, sequence: 42 - clear ...
```

Ein Puls pro Sekunde, `sequence` zählt hoch = korrekt.

---

## Autostart einrichten

```bash
sudo nano /etc/systemd/system/racecontrol-ziel.service
```

```ini
[Unit]
Description=RaceControl Zieleinheit (Downhill/Seifenkiste)
After=network-online.target time-sync.target gpsd.service
Wants=network-online.target gpsd.service

[Service]
ExecStart=/usr/bin/python3 /home/pi/RaPi_lichtschranke/racecontrol_downhill_finish.py
WorkingDirectory=/home/pi/RaPi_lichtschranke
Restart=always
RestartSec=5
User=pi

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable racecontrol-ziel
sudo systemctl start racecontrol-ziel
journalctl -u racecontrol-ziel -f
```

> `After=gpsd.service` stellt sicher, dass gpsd bereits läuft und die Uhr durch
> chrony bereits auf GPS-Zeit gestellt wurde, bevor der Client startet.

---

## Displayanzeige

| Situation | Anzeige |
|-----------|---------|
| Bootet, Uhr nicht synchronisiert | `nSYn` (2 s), dann `----` |
| Bereit, wartet auf Fahrer | aktuelle Uhrzeit `1203` (wechselt jede Sekunde) |
| Verbunden mit Backend, Spur A | `ConA` (1 s), dann Uhrzeit |
| Verbunden mit Backend, Spur B | `ConB` (1 s), dann Uhrzeit |
| Backend getrennt | `dISC` |
| Auslösung – wartet auf Backend-Antwort | `----` |
| Laufzeit vom Backend empfangen (z.B. 2:47.4) | `0247 4` |
| Reset-Taster gedrückt | `----` → Uhrzeit |

---

## DIP-Schalter Spurwahl

Für **Zwei-Spur-Betrieb** (Seifenkiste mit zwei parallelen Bahnen) werden zwei
identische Einheiten aufgebaut:

| DIP 1 | Spur | Hostname (Empfehlung) | Gerät-ID |
|-------|------|-----------------------|----------|
| OFF (HIGH) | **A** | `rc-ziel-a` | `downhill-finish-rpi-a` |
| ON (LOW) | **B** | `rc-ziel-b` | `downhill-finish-rpi-b` |

---

## Gesamtkosten

| Variante | Preis |
|----------|------:|
| NTP via LTE (empfohlen für live-race.de) | **~87 €** |
| GPS-Maus USB (Variante A) | **~104–115 €** |
| ublox NEO-M8N + PPS (Variante B, Profi) | **~115–125 €** |
| **Zwei-Spur-Setup × 2 (GPS-Maus)** | **~208–230 €** |

---

## Vergleich der Zeitsync-Methoden

| Methode | Genauigkeit | Offline? | Hardware-Aufwand | Kosten extra |
|---------|:-----------:|:--------:|:----------------:|:------------:|
| NTP via LTE | ±10–50 ms | Nein | Keine | 0 € |
| GPS-Maus USB | ±100–500 ms | Ja | Plug & Play | ~17–27 € |
| GPS + PPS GPIO | ±1 µs | Ja | UART + Level-Shifter | ~26–36 € |
| DCF77 Modul | ±1–10 ms | Ja | GPIO + Antenne | ~10–17 € |

> **Empfehlung:** Für `live-race.de` SaaS-Betrieb immer NTP nutzen. GPS-Maus
> ist die unkomplizierteste Offline-Lösung (einstecken, läuft). DCF77 ist präziser
> aber empfindlicher (Interferenzen, Ausrichtung der Antenne). GPS + PPS ist
> für professionelle Rally-Zeitnahme geeignet.

---

## Unterschiede zur Standard-Einheit

| Merkmal | Standard (`racecontrol_client.py`) | Diese Einheit |
|---------|-----------------------------------|---------------|
| Sensoren | 1–2 (Start + Ziel am selben Gerät) | 1 (nur Ziel) |
| Zeitmessung | Δt zwischen zwei GPIO-Events | Absoluter Zeitstempel (Systemuhr) |
| Gesendet wird | `timing_result` mit `raw_time` (Sekunden) | `timing_finish` mit `clock` (HH:MM:SS.mmm) |
| Laufzeit-Berechnung | Im RPi | Im Backend (Ziel − Planstart) |
| Start-Gerät | Am selben RPi | Separates Starter-Tablet oder 2. RPi |
| Mehrere Geräte parallel | Nein | Ja (Spur A + Spur B unabhängig) |
| Einsatz | Kart-Slalom, Loop-Kurse | Downhill, Seifenkiste, Rally-Ziel |

---

## Weiterführende Dokumentation

| Dokument | Inhalt |
|----------|--------|
| [BAUANLEITUNG.md](BAUANLEITUNG.md) | Standard-Einheit (Start + Ziel, Kart-Slalom) |
| [BAUANLEITUNG_DCF_Zieleinheit.md](BAUANLEITUNG_DCF_Zieleinheit.md) | Zieleinheit mit DCF77-Offline-Sync |
| [racecontrol_downhill_finish.py](racecontrol_downhill_finish.py) | Fertiger Client dieser Einheit |
| [racecontrol_client.py](racecontrol_client.py) | Standard-Client TM1637 |
| [notes.md](notes.md) | GPIO-Belegung, WebSocket-Protokoll |
| SaaS-Konzept.md | Architektur live-race.de, Rally- und Downhill-Konzept |
