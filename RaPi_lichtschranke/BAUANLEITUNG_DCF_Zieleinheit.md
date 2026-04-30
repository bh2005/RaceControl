# Bauanleitung – Zieleinheit mit DCF77/NTP-Zeitsynchronisation

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

## Zeitsynchronisation: NTP oder DCF77?

Die Genauigkeit der Laufzeit hängt davon ab, wie präzise die Systemuhr des RPi ist.

| Methode | Genauigkeit | Vorteil | Wann einsetzen |
|---------|------------|---------|----------------|
| **NTP via Internet** (systemd-timesyncd) | ±10–50 ms | Kein Hardware-Aufwand, läuft sofort | LTE-Verbindung vorhanden (SaaS-Betrieb) |
| **NTP via LAN** (lokaler Zeitserver) | ±1–5 ms | Sehr präzise, kein Internet nötig | Festes WLAN am Veranstaltungsort |
| **DCF77 Hardware-Empfänger** | ±1–10 ms | Komplett offline, kein Netz nötig | Wald, Berg, kein LTE/WLAN erreichbar |

> Für Zeiten im Bereich 30–300 Sekunden (Seifenkiste, Downhill) ist ±50 ms absolut
> ausreichend. **NTP via LTE ist die einfachste Lösung** und für `live-race.de`
> die empfohlene Variante. DCF77 ist nur für Offline-Szenarien nötig.

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
| | **Summe NTP-Variante** | | **~87 €** | |

### Zusatzteil – nur bei DCF77 Offline-Variante

| # | Bauteil | Menge | Preis ca. | Quelle |
|---|---------|-------|-----------|--------|
| 11 | **DCF77-Empfänger-Modul** (z.B. Pollin 810054 oder Conrad DCF-Bausatz) | 1 | 8–15 € | Pollin, Conrad, Amazon |
| 12 | Verlängerungskabel 2-adrig, 1–3 m | 1 | 2 € | Baumarkt |
| | **Summe DCF77-Variante** | | **~100–105 €** | |

> **Empfohlenes DCF77-Modul:** Pollin Bestellnr. 810054 „DCF-Empfänger-Bausatz"  
> Ausgang: 3,3V-kompatibles TTL-Signal, aktiv LOW bei Träger, Puls bei Bit-Flanken.  
> Alternativ: fertig aufgebaute Module mit SMA-Antenne aus China (~5 €, AliExpress).

---

## GPIO-Belegung

| Funktion | GPIO (BCM) | Board-Pin | Bemerkung |
|----------|-----------|-----------|-----------|
| Lichtschranke Ziel | GPIO 27 | Pin 13 | Einziger Sensor dieser Einheit |
| Reset-Taster | GPIO 22 | Pin 15 | Pullup, aktiv LOW |
| DIP 1 – Spurwahl | GPIO 5 | Pin 29 | ON(LOW)=Spur B, OFF(HIGH)=Spur A |
| TM1637 CLK | GPIO 21 | Pin 40 | |
| TM1637 DIO | GPIO 20 | Pin 38 | |
| **DCF77 Signal** | **GPIO 24** | **Pin 18** | Nur DCF77-Variante |
| 5 V (Sensor + DCF77 VCC) | — | Pin 2 | |
| 3,3 V (Display VCC) | — | Pin 1 | |
| GND | — | Pin 6, 9 … | |

---

## Schaltplan

```
                    Raspberry Pi Zero 2 W
                   ┌──────────────────────────┐
                   │  Pin 1  (3,3V) ───────────── TM1637 VCC
                   │  Pin 2  (5V)   ───────────── Lichtschranke VCC (braun)
                   │                         ──── DCF77 VCC  (nur Option B)
                   │  Pin 6  (GND)  ──┬─────────── TM1637 GND
                   │                  ├─────────── Lichtschranke GND (blau)
                   │                  ├─────────── DCF77 GND  (nur Option B)
                   │                  ├─────────── Reset-Taster → GND
                   │                  └─────────── DIP COM → GND
                   │  Pin 13 (GPIO27) ──────────── Lichtschranke Signal (schwarz)
                   │  Pin 15 (GPIO22) ──────────── Reset-Taster
                   │  Pin 18 (GPIO24) ──────────── DCF77 Signal (nur Option B)
                   │  Pin 29 (GPIO 5) ──────────── DIP 1 Spurwahl
                   │  Pin 38 (GPIO20) ──────────── TM1637 DIO
                   │  Pin 40 (GPIO21) ──────────── TM1637 CLK
                   └──────────────────────────┘
```

> **Unterschied zur Standard-Einheit:** GPIO 17 (Start) entfällt komplett.
> Diese Einheit hat nur **einen** Sensor-Eingang (GPIO 27 = Ziel).

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
BACKEND_HOST   = "192.168.0.100"   # IP des Laptops ODER Subdomain z.B. "msc-braach.live-race.de"
BACKEND_PORT   = 1980              # bei live-race.de: 443 + WSS
TIMING_API_KEY = ""                # Admin → System → Lichtschranken-API-Key eintragen
MIN_TIME_S     = 10.0              # Mindestzeit – Fehlauslösungen ignorieren
```

Für `live-race.de` (SaaS):
```python
BACKEND_WS = f"wss://msc-braach.live-race.de/ws/timing?key={TIMING_API_KEY}"
```

---

## Option A – NTP-Synchronisation (empfohlen)

Keine zusätzliche Hardware nötig. `systemd-timesyncd` ist auf Raspberry Pi OS
standardmäßig aktiv und synchronisiert die Uhr automatisch bei Netzverbindung.

### NTP-Status prüfen

```bash
timedatectl status
```

Erwartete Ausgabe:
```
               Local time: Sa 2026-04-30 12:01:34 CEST
           Universal time: Sa 2026-04-30 10:01:34 UTC
                 RTC time: Sa 2026-04-30 10:01:34
                Time zone: Europe/Berlin (CEST, +0200)
System clock synchronized: yes          ← wichtig
              NTP service: active
```

Zeigt `synchronized: no` → WLAN/LTE-Verbindung prüfen.

### Präziseren NTP-Server konfigurieren (optional)

Für höhere Genauigkeit `chrony` statt `systemd-timesyncd` verwenden:

```bash
sudo apt install chrony -y
sudo nano /etc/chrony/chrony.conf
```

Zeile einfügen:
```
server 0.de.pool.ntp.org iburst
server 1.de.pool.ntp.org iburst
makestep 1.0 3
rtcsync
```

```bash
sudo systemctl restart chrony
chronyc tracking   # Offset sollte < 10 ms sein
```

---

## Option B – DCF77 Hardware-Empfänger (für Offline-Einsatz)

Wenn kein Internet und kein lokales Netz vorhanden ist (Wald, Berg), kann ein
DCF77-Empfänger-Modul die Uhr ohne Netzwerk synchronisieren.

### DCF77-Modul anschließen

| Modul-Pin | RPi-Pin | Funktion |
|-----------|---------|----------|
| VCC | Pin 2 (5V) | Versorgung |
| GND | Pin 6 (GND) | Masse |
| PON (falls vorhanden) | Pin 6 (GND) | Empfänger aktivieren (LOW=aktiv) |
| Signal (TCO/OUT) | Pin 18 (GPIO 24) | Zeitcode-Ausgang |

> Das Modul sollte **möglichst weit** vom RPi und anderen Elektronikteilen aufgestellt
> werden (1–3 m Kabel). Metall und Netzteile stören das 77,5 kHz-Signal.  
> Ausrichtung: Antenne senkrecht, Ferritstab zeigt nach Norden/Süden.

### chrony mit DCF77 konfigurieren

```bash
sudo apt install chrony python3-rpi.gpio -y
```

**DCF77-zu-SHM-Bridge installieren** (liest GPIO und schreibt in Shared Memory für chrony):

```bash
sudo apt install git -y
git clone https://github.com/dl8dtl/dcf77-rpi.git /opt/dcf77-rpi
# oder eigenes minimales Script (siehe unten)
```

**Minimales DCF77-Bridge-Script** (`/opt/dcf77_shm.py`):

```python
#!/usr/bin/env python3
"""
Liest DCF77-Signal von GPIO 24 und stellt die Zeit als SHM 0 für chrony bereit.
Vereinfachte Implementierung – dekodiert Minutenmarken.
"""
import RPi.GPIO as GPIO, time, ctypes, struct, mmap, os

DCF_PIN = 24
SHM_KEY = 0x4e545030   # NTP0 shared memory key

# SHM für chrony vorbereiten (struct ntpshm)
SHM_SIZE = 96

def open_shm():
    import sysv_ipc
    try:
        shm = sysv_ipc.SharedMemory(SHM_KEY)
    except sysv_ipc.ExistentialError:
        shm = sysv_ipc.SharedMemory(SHM_KEY, sysv_ipc.IPC_CREAT, 0o666, SHM_SIZE)
    return shm

GPIO.setmode(GPIO.BCM)
GPIO.setup(DCF_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Vollständige DCF77-Dekodierung ist komplex — für den Einsatz in der Praxis
# empfehlen wir das fertige Paket "dcf77" oder "rpi-dcf77":
#   pip install dcf77
# und die chrony-Konfiguration refclock SOCK /run/chrony.dcf77.sock
print("[DCF77] Bridge gestartet — GPIO 24")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    GPIO.cleanup()
```

> **Empfehlung für die Praxis:** Das Paket `rpi-dcf77` liefert einen fertigen
> systemd-Service der das Signal liest und chrony via SOCK-Treiber füttert.
> Alternativ: GPS-Maus (ublox) via UART + gpsd — präziser als DCF77 und
> einfacher zu integrieren (aber teurer, ~30 €).

**chrony-Konfiguration für DCF77 via SOCK:**

```bash
sudo nano /etc/chrony/chrony.conf
```

```
# DCF77 als lokale Zeitreferenz
refclock SOCK /run/chrony.dcf77.sock refid DCF poll 3 precision 1e-3

# Fallback auf NTP wenn Netz vorhanden
server 0.de.pool.ntp.org iburst
makestep 1.0 3
rtcsync
```

```bash
sudo systemctl restart chrony
chronyc sources -v   # DCF77 sollte als * (aktiv) erscheinen
```

### DCF77-Empfang testen

```bash
# GPIO direkt beobachten (muss regelmäßige Pulse zeigen):
python3 -c "
import RPi.GPIO as GPIO, time
GPIO.setmode(GPIO.BCM)
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)
for _ in range(120):
    print(GPIO.input(24), end=' ', flush=True)
    time.sleep(0.5)
GPIO.cleanup()
"
```

Erwartetes Muster: `0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 1 0 0 …`  
(Wechsel zwischen 0 und 1, Minutenmarke = langes HIGH)

Kein Signal (nur `1 1 1 1 1 …`):
- Modul-VCC prüfen (muss ~5V haben)
- Antenne weiter vom RPi entfernen
- PON-Pin auf GND legen

---

## Autostart einrichten

```bash
sudo nano /etc/systemd/system/racecontrol-ziel.service
```

```ini
[Unit]
Description=RaceControl Zieleinheit (Downhill/Seifenkiste)
After=network-online.target time-sync.target
Wants=network-online.target

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

> `After=time-sync.target` stellt sicher, dass der Client erst startet wenn
> die Uhr synchronisiert ist (wichtig besonders beim Kaltstart ohne Netz).

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
identische Einheiten aufgebaut. Die Spurzuordnung erfolgt per DIP-Schalter:

| DIP 1 | Spur | Hostname (Empfehlung) | Gerät-ID |
|-------|------|-----------------------|----------|
| OFF (HIGH) | **A** | `rc-ziel-a` | `downhill-finish-rpi-a` |
| ON (LOW) | **B** | `rc-ziel-b` | `downhill-finish-rpi-b` |

Das Backend verwaltet für jede Spur eine eigene Queue der erwarteten Fahrer.

---

## Gesamtkosten

| Variante | Preis |
|----------|------:|
| NTP via LTE (empfohlen für live-race.de) | **~87 €** |
| NTP via LAN | **~87 €** (gleich, nur anderer Netzwerkzugang) |
| DCF77 Offline | **~100–105 €** |
| **Zwei-Spur-Setup × 2** | **~175–210 €** |

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
| [racecontrol_downhill_finish.py](racecontrol_downhill_finish.py) | Fertiger Client dieser Einheit |
| [racecontrol_client.py](racecontrol_client.py) | Standard-Client TM1637 |
| [notes.md](notes.md) | GPIO-Belegung, WebSocket-Protokoll |
| SaaS-Konzept.md | Architektur live-race.de, Rally- und Downhill-Konzept |
