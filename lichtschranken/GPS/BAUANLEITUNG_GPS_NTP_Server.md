# Bauanleitung – GPS am Server als zentraler NTP-Zeitgeber

**Projekt:** RaceControl Pro / live-race.de  
**Einsatz:** Downhill MTB · Seifenkiste · Rally — alle Ziel-RPis synchronisieren vom Server  
**Schwierigkeit:** Einsteiger  
**Bauzeit:** ca. 1–2 Stunden

---

## Konzept

Statt jede Zieleinheit einzeln mit GPS auszurüsten, bekommt **nur der Server eine GPS-Maus**.
Der Server läuft als lokaler NTP-Zeitgeber im WLAN des Veranstaltungsorts.
Alle Raspberry Pis synchronisieren automatisch von ihm.

```
                     GPS-Maus (u-blox M8, M8030-KT)
                          │
                    [Server / Laptop]
                    chrony + gpsd
                    NTP-Server im WLAN
                    192.168.0.100
                         /|\
                        / | \
               RPi-A    RPi-B    Tablet
            (Spur A)  (Spur B)  (Starter)
            chrony    chrony    Windows NTP
            ←NTP      ←NTP      ←NTP
```

**Für die normale Lichtschranke (Start + Ziel am selben RPi)** bringt GPS am Server
**nichts für die Zeitmessung** — der RPi misst Δt lokal zwischen zwei GPIO-Events,
die Serverzeit ist dabei irrelevant.

**Für die Downhill-Zieleinheit** (`racecontrol_downhill_finish.py`) hingegen ist
diese Architektur die eleganteste Lösung:
- Kein GPS-Hardware auf den RPis nötig
- Alle Ziel-RPis laufen mit derselben Zeitbasis (±1–5 ms LAN-NTP)
- Präziser als GPS-Maus direkt am RPi (±100–500 ms)

---

## Vergleich der Ansätze

| Methode | Genauigkeit RPi | Hardware pro RPi | Hardware Server |
|---------|:--------------:|:----------------:|:---------------:|
| NTP via Internet (LTE) | ±10–50 ms | keine | keine |
| **GPS am Server → LAN-NTP** | **±1–5 ms** | **keine** | **GPS-Maus ~20 €** |
| GPS-Maus pro RPi (USB) | ±100–500 ms | GPS-Maus ~20 €/Stk | keine |
| GPS-Modul + PPS pro RPi | ±1 µs | ~30 €/Stk | keine |
| DCF77 pro RPi | ±1–10 ms | ~12 €/Stk | keine |

> **GPS am Server + LAN-NTP** ist bei zwei oder mehr Ziel-RPis die **günstigste**
> und **genaueste** Offline-Variante: Ein GPS für beliebig viele RPis.

---

## Voraussetzung: Stabiles WLAN am Veranstaltungsort

Diese Architektur funktioniert nur, wenn alle RPis dauerhaft im WLAN-Netz des
Servers erreichbar sind. Faustregel:

- WLAN-Router am Veranstaltungsort aufstellen (kein Internet nötig)
- Alle RPis ins lokale WLAN einbuchen
- Server-Laptop im selben WLAN (oder per LAN-Kabel am Router)
- Maximale Entfernung RPi ↔ Router: ~30 m Sichtlinie (outdoor)

---

## Teileliste

| # | Bauteil | Menge | Preis ca. | Quelle |
|---|---------|-------|-----------|--------|
| 1 | **USB-GPS-Maus mit u-blox M8030-KT** (u-blox 8, Multi-GNSS) | 1 | 10–20 € | Amazon, AliExpress |
| 2 | WLAN-Router (z.B. TP-Link TL-WR841N oder GL.iNet) | 1 | 20–35 € | Amazon |
| | **Summe Server-Seite** | | **~30–55 €** | |

> Der WLAN-Router ist oft bereits vorhanden (FritzBox, altes Gerät).  
> Die GPS-Maus ist eine einmalige Anschaffung für alle zukünftigen Veranstaltungen.

### Welcher u-blox Chip?

| Chip | Generation | Konstellationen | NMEA-Genauigkeit | USB-ID |
|------|-----------|-----------------|-----------------|--------|
| G7020-KT | u-blox 7 | GPS only | ±200–500 ms | `1546:01a7` |
| **M8030-KT** | **u-blox 8** | **GPS + GLONASS + Galileo + BeiDou** | **±50–150 ms** | `1546:01a8` |

**Empfehlung: M8030-KT (u-blox 8)** — mehr Satelliten sichtbar = stabilerer Fix,
besonders unter Zelten oder bei bewölktem Himmel. Preis-Unterschied: ~2–5 €.

Chip nach dem Einstecken prüfen:
```bash
lsusb | grep -i u-blox
# 1546:01a8 = u-blox 8 (M8030-KT) ✓
# 1546:01a7 = u-blox 7 (G7020-KT)
```

Typische Produkte mit M8030-KT: „VK-162G-2", „GlobalSat BU-353-S4 (neu)", viele
generische „u-blox 8 USB GPS" auf Amazon/AliExpress (~8–15 €).

### Ziel-RPis (normal, ohne GPS)

Jede Zieleinheit wird wie die **NTP-Variante** aus `BAUANLEITUNG_DCF_Zieleinheit.md`
aufgebaut — **ohne** DCF77-Modul oder GPS:

| # | Bauteil | Menge | Preis ca. |
|---|---------|-------|-----------|
| Standard-Teileliste (Nr. 1–10) | Raspberry Pi + Lichtschranke + Display | 1 Set | ~87 € |

---

## Server einrichten (Linux / Raspberry Pi als Server)

> **Windows-Laptop als Server?** Windows unterstützt gpsd und chrony nativ nicht.
> Empfehlung: Einen kleinen Raspberry Pi 4 als dedizierten Server + GPS-NTP nutzen,
> oder RaceControl Pro im Docker-Container betreiben (dann läuft chrony im Container).
> Anleitung für den Raspberry Pi als Server siehe unten.

### gpsd und chrony installieren

```bash
sudo apt install gpsd gpsd-clients chrony -y
```

### GPS-Maus konfigurieren

GPS-Maus per USB anschließen, Gerät ermitteln:

```bash
ls /dev/ttyUSB* /dev/ttyACM*
# typisch: /dev/ttyUSB0
```

**`/etc/default/gpsd` bearbeiten:**

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
sudo systemctl restart gpsd
```

**GPS-Empfang testen** (nach 1–2 Minuten mit freier Himmelssicht):

```bash
cgps -s
# Zeigt: Fix, Satelliten, Zeit — warten bis "3D Fix" erscheint
```

### chrony als NTP-Server mit GPS-Quelle

```bash
sudo nano /etc/chrony/chrony.conf
```

```
# GPS via gpsd (USB-Maus, NMEA)
# u-blox 8 (M8030-KT): ±50-150ms / u-blox 7 (G7020-KT): ±200-500ms
refclock SHM 0 refid GPS precision 1e-1 offset 0.9999 delay 0.2

# Fallback: Internet-NTP wenn verfügbar
server 0.de.pool.ntp.org iburst

# Als NTP-Server für alle Geräte im lokalen WLAN-Netz bereitstellen
allow 192.168.0.0/24

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
================================================================
#* GPS                      0     4    377      6   +0.212s[+0.212s] +/-  0.200s
```

**NTP-Bereitstellung prüfen:**

```bash
chronyc clients
# zeigt alle RPis die sich synchronisieren
```

---

## Raspberry Pis auf Server-NTP umstellen

Auf **jedem** Ziel-RPi (`rc-ziel-a`, `rc-ziel-b`):

```bash
sudo apt install chrony -y
sudo nano /etc/chrony/chrony.conf
```

```
# Primär: lokaler GPS-NTP-Server
server 192.168.0.100 iburst prefer

# Fallback: Internet (falls verfügbar)
server 0.de.pool.ntp.org iburst

makestep 1.0 3
rtcsync
```

```bash
sudo systemctl enable chrony
sudo systemctl restart chrony
```

Synchronisation prüfen:

```bash
chronyc tracking
```

Erwartete Ausgabe:
```
Reference ID    : C0A80064 (192.168.0.100)
Stratum         : 2
Ref time (UTC)  : Wed Apr 30 10:01:34 2026
System time     : 0.000003265 seconds fast of NTP time
Last offset     : +0.000003412 seconds
RMS offset      : 0.000004821 seconds    ← ~5 µs!
Frequency       : 3.456 ppm fast
Residual freq   : +0.002 ppm
Skew            : 0.124 ppm
Root delay      : 0.000892 seconds
Root dispersion : 0.000109 seconds
```

> `RMS offset` im Mikrosekundenbereich = perfekte Synchronisation im LAN.
> Die GPS-Ungenauigkeit (±100–500 ms der USB-Maus) mittelt chrony über viele
> Messungen heraus — die RPis erreichen tatsächlich ±1–5 ms Genauigkeit.

---

## Autostart auf dem Server

Damit gpsd und chrony nach Neustart automatisch laufen:

```bash
sudo systemctl enable gpsd chrony
```

Falls der Server gleichzeitig RaceControl Pro ausführt, startreihenfolge sicherstellen:

```bash
sudo nano /etc/systemd/system/racecontrol.service
```

```ini
[Unit]
Description=RaceControl Pro Backend
After=network-online.target time-sync.target gpsd.service
Wants=gpsd.service
```

---

## Autostart auf den Ziel-RPis

Auf jedem Ziel-RPi:

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
```

> `After=time-sync.target` stellt sicher, dass chrony die Uhr bereits vom Server
> empfangen hat, bevor der Client startet.

---

## Checkliste Veranstaltungstag

```
[ ] WLAN-Router einschalten, Netz "RaceControl" prüfen
[ ] Server starten → warten bis GPS-Fix (cgps zeigt 3D Fix, ~2 min)
[ ] chronyc sources → GPS mit * markiert
[ ] Ziel-RPi-A einschalten → 90 s warten → chronyc tracking (RMS offset < 10ms?)
[ ] Ziel-RPi-B einschalten → gleich prüfen
[ ] racecontrol_downhill_finish.py: Display zeigt Uhrzeit (kein "nSYn") = OK
[ ] Backend: Admin → System → Zieleinheiten-Heartbeat für A und B sichtbar
[ ] Testlauf: Planstart 1 Minute in Zukunft eintragen, Lichtschranke auslösen
    → Backend zeigt berechnete Laufzeit = korrekt
```

---

## Wann welche Variante wählen?

| Situation | Empfehlung |
|-----------|-----------|
| Internet/LTE am Veranstaltungsort vorhanden | **NTP via Internet** — kein Extraaufwand |
| Kein Internet, aber festes WLAN, mehrere RPis | **GPS am Server + LAN-NTP** ← diese Anleitung |
| Kein Internet, kein WLAN, einzelner RPi | **GPS-Maus oder DCF77 direkt am RPi** |
| Maximale Präzision (Profi-Rally) | **GPS-Modul + PPS** pro RPi oder am Server |
| Normale Lichtschranke (Start+Ziel selber RPi) | **GPS irrelevant** — RPi misst Δt lokal |

---

## Weiterführende Dokumentation

| Dokument | Inhalt |
|----------|--------|
| [BAUANLEITUNG.md](BAUANLEITUNG.md) | Standard-Einheit (Start + Ziel, Kart-Slalom) |
| [BAUANLEITUNG_DCF_Zieleinheit.md](BAUANLEITUNG_DCF_Zieleinheit.md) | Zieleinheit mit DCF77 (kein WLAN nötig) |
| [BAUANLEITUNG_GPS_Zieleinheit.md](BAUANLEITUNG_GPS_Zieleinheit.md) | Zieleinheit mit GPS direkt am RPi |
| [racecontrol_downhill_finish.py](racecontrol_downhill_finish.py) | Fertiger Client Zieleinheit |
| SaaS-Konzept.md | Architektur live-race.de, Rally- und Downhill-Konzept |
