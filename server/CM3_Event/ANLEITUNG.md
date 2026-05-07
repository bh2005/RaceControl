# Raspberry Pi Compute Module 3 – RaceControl Veranstaltungsserver

**Ziel:** Der CM3 läuft als vollständiger RaceControl-Server am Veranstaltungstag —
Backend (FastAPI + SQLite) + gebautes Frontend werden automatisch gestartet.
Alle Teilnehmer-Geräte im lokalen Netz rufen `http://192.168.1.100:1980` auf.
Kein Laptop, kein Node.js, kein Internet am Veranstaltungstag nötig.

---

## Architektur-Übersicht

```
[Windows/Linux]   ──(Einrichtung per SCP)──►  [CM3 + CMIO-Board]
                                                    │
                                         Port 1980  │  Ethernet
                                                    │
                          ┌─────────────────────────┴────────────────────────┐
                          │            Switch / Router                        │
                          └──────┬──────────────┬────────────────┬───────────┘
                                 │              │                │
                          [Pi 2 + LSU200]  [Tablet Nennbüro] [Smartphones Livetiming]
```

---

## Hardware-Übersicht

| Gerät | Details |
|-------|---------|
| Raspberry Pi Compute Module 3 | Server-Prozessor (BCM2837, Cortex-A53 1,2 GHz, 1 GB RAM) |
| CM I/O Board v3 (CMIO3) | Trägerplatine mit Ethernet, USB, HDMI |
| microSD oder eMMC | Betriebssystem (CM3 Lite = SD, CM3 = eMMC) |
| Ethernet-Kabel | Verbindung zum Switch/Router |
| Netzteil 5 V / ≥ 2,5 A | Stromversorgung CM3 via CMIO-Board |

---

## Schritt 1 – Raspberry Pi OS flashen

### CM3 Lite (keine eMMC – microSD-Karte)

Identisch zum Pi 2 — microSD-Karte mit Raspberry Pi Imager flashen:
- **OS:** Raspberry Pi OS Lite **64-bit** (CM3 unterstützt 64-bit)
- **Hostname:** `cm3-racecontrol`
- **SSH aktivieren**, Benutzer `pi`, sicheres Passwort
- **WLAN:** leer lassen

### CM3 (mit 4 GB eMMC)

Der CM3 hat keinen SD-Karten-Slot. Die eMMC wird über USB geflasht.

**CMIO-Board vorbereiten (gleich für Windows und Linux):**
- Jumper **J4** auf **Pins 1–2** setzen (USB-Boot aktivieren)
- USB-Kabel von **J2** (USB slave, Micro-USB) zum PC anschließen
- Netzteil anschließen → CM3 startet im Boot-Modus

---

#### Windows

1. **rpiboot** installieren:
   `https://github.com/raspberrypi/usbboot/releases` → `rpiboot_setup.exe`

2. `RPiBoot.exe` ausführen → Warten bis „Found a Raspberry Pi CM3" erscheint

3. CM3 erscheint als Laufwerk (z.B. `D:`) → **Raspberry Pi Imager** starten:
   - **Gerät:** Laufwerk `D:` auswählen (ACHTUNG: nicht die Windows-Festplatte!)
   - **OS:** Raspberry Pi OS Lite 64-bit
   - **Einstellungen:** Hostname `cm3-racecontrol`, SSH aktivieren, User `pi`

---

#### Linux

```bash
# rpiboot installieren (Ubuntu/Debian):
sudo apt install rpiboot

# oder aus Quellcode:
# git clone https://github.com/raspberrypi/usbboot && cd usbboot && make && sudo make install

# rpiboot starten (CM3 muss bereits per USB angeschlossen sein):
sudo rpiboot
# → Warten bis „Found a Raspberry Pi CM3" erscheint
# → CM3 erscheint als Block-Device, z.B. /dev/sdb

# Mit Raspberry Pi Imager flashen (GUI):
rpi-imager
# Oder direkt mit dd (ACHTUNG: /dev/sdX anpassen, falsche Disk = Datenverlust!):
# sudo dd if=raspios-lite-arm64.img of=/dev/sdX bs=4M status=progress && sync
```

---

**Nach dem Flashen (Windows & Linux):**
Jumper **J4 zurück** auf Standard (Open / Pins 2–3), USB-Kabel trennen,
Netzteil kurz trennen und wieder anschließen → CM3 startet normal.

---

## Schritt 2 – Erster Start und Verbinden

1. Ethernet-Kabel ins CMIO-Board (Buchse **J19**, nahe USB-Ports)
2. Netzteil anschließen → automatischer Start (ca. 60 Sekunden)

**IP-Adresse ermitteln:**

```bash
# Methode A: Hostname (wenn Router mDNS unterstützt) – Windows & Linux
ping cm3-racecontrol.local

# Methode B: Router-Oberfläche → DHCP-Tabelle → "cm3-racecontrol"

# Methode C: Linux – Netzwerk scannen
nmap -sn 192.168.1.0/24 | grep -A1 cm3
```

**SSH verbinden:**

```bash
# Windows (PowerShell) & Linux (Terminal):
ssh pi@cm3-racecontrol.local
# oder mit IP:
ssh pi@192.168.1.XX
```

---

## Schritt 3 – Statische IP einrichten (empfohlen)

Eine feste IP ist wichtig, damit alle Geräte den Server immer unter der gleichen Adresse finden.

**Auf dem CM3 (per SSH):**

```bash
sudo nano /etc/dhcpcd.conf
```

Am Ende anhängen:

```
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1
```

Speichern: `Ctrl+O`, `Enter`, `Ctrl+X`

```bash
sudo reboot
```

Ab jetzt ist der CM3 immer unter `192.168.1.100` erreichbar.

---

## Schritt 4 – Frontend bauen und deployen

Beide Scripts bauen das Frontend automatisch wenn `frontend/dist/` noch nicht existiert
und übertragen danach alle Dateien per SCP/rsync auf den CM3.

---

### Windows (PowerShell)

```powershell
cd "C:\Users\ks84597\OneDrive - K+S Aktiengesellschaft\Documents\Git-Repos\RaceControl\server\CM3_Event"

# Mit Hostname:
.\deploy.ps1 -CmHost cm3-racecontrol.local

# Mit IP-Adresse (zuverlässiger):
.\deploy.ps1 -CmHost 192.168.1.100
```

---

### Linux / macOS (Terminal)

```bash
cd /pfad/zum/repo/server/CM3_Event
chmod +x deploy.sh

# Mit Hostname:
./deploy.sh cm3-racecontrol.local

# Mit IP-Adresse:
./deploy.sh 192.168.1.100

# Mit IP + Benutzer (falls nicht 'pi'):
./deploy.sh 192.168.1.100 pi
```

---

Beide Scripts übertragen automatisch:
- `backend/` (ohne Tests und `__pycache__`)
- `frontend/dist/` (gebautes Vue-Frontend)
- `assets/` (Logos, Reglements, Vorlagen)
- `schema.sql`
- `install.sh` + `racecontrol.service`

SSH-Fingerprint beim ersten Mal mit `yes` bestätigen.

---

## Schritt 5 – Setup auf dem CM3 ausführen

```bash
ssh pi@192.168.1.100
cd ~/racecontrol
sudo ./install.sh
```

Das Script erledigt:
- Python 3 Virtual Environment anlegen
- Alle Abhängigkeiten installieren (`fastapi`, `uvicorn`, `python-jose`, `bcrypt` …)
- Dateiberechtigungen setzen
- `__pycache__`-Verzeichnisse bereinigen
- Systemd-Dienst `racecontrol.service` registrieren
- Dienst starten und beim Boot aktivieren

Ausgabe am Ende zeigt IP und URL.

---

## Schritt 6 – Testen

**Status prüfen:**

```bash
sudo systemctl status racecontrol
```

Erwartete Ausgabe (grünes `active (running)`):
```
● racecontrol.service - RaceControl Pro – Veranstaltungsserver
     Loaded: loaded (/etc/systemd/system/racecontrol.service; enabled)
     Active: active (running) since ...
```

**API-Test:**

```bash
curl http://localhost:1980/health
# → {"status":"ok"}
```

**Im Browser öffnen** (vom Windows-Laptop):

```
http://192.168.1.100:1980
```

Login mit Admin-Passwort (nach DB-Initialisierung: `admin` / `admin123`
→ sofort ändern unter Admin → Benutzer).

---

## Veranstaltungstag – Ablauf

1. CM3 Ethernet-Kabel in den Switch stecken
2. Netzteil anschließen → automatischer Start
3. Pi 2 (LSU200-Client) ebenfalls starten
4. Auf einem Gerät: `http://192.168.1.100:1980` aufrufen → fertig

**Kein Login, kein SSH, kein manueller Start nötig.**

---

## Update – neues Release einspielen

Änderungen im Code werden so auf den CM3 übertragen:

**Windows:**
```powershell
# Rebuild + Transfer:
.\deploy.ps1 -CmHost 192.168.1.100

# Danach Dienst neu starten:
ssh pi@192.168.1.100 'sudo systemctl restart racecontrol'

# Nur Code, kein Frontend-Rebuild:
.\deploy.ps1 -CmHost 192.168.1.100 -SkipBuild
ssh pi@192.168.1.100 'sudo systemctl restart racecontrol'
```

**Linux:**
```bash
# Rebuild + Transfer:
./deploy.sh 192.168.1.100

# Danach Dienst neu starten:
ssh pi@192.168.1.100 'sudo systemctl restart racecontrol'

# Nur Code, kein Frontend-Rebuild:
./deploy.sh 192.168.1.100 pi --skip-build
ssh pi@192.168.1.100 'sudo systemctl restart racecontrol'
```

Die Datenbank (`racecontrol.db`) wird beim Deploy **nicht überschrieben** —
alle Veranstaltungsdaten bleiben erhalten.

---

## Nützliche Befehle (SSH)

```bash
# Status anzeigen
sudo systemctl status racecontrol

# Live-Logs verfolgen
sudo journalctl -u racecontrol -f

# Dienst neu starten
sudo systemctl restart racecontrol

# Dienst stoppen
sudo systemctl stop racecontrol

# IP-Adresse anzeigen
hostname -I

# Datenbank-Backup manuell erstellen
python3 ~/racecontrol/backend/backup_db.py

# Datenbank-Integrität prüfen
python3 ~/racecontrol/backend/db_health.py

# Admin-Passwort zurücksetzen
python3 ~/racecontrol/backend/reset_admin_password.py

# Freien Speicherplatz prüfen
df -h /
```

---

## Troubleshooting

### Dienst startet nicht

```bash
sudo journalctl -u racecontrol --since "5 minutes ago"
```

Häufige Ursachen:
- **`ModuleNotFoundError`**: `sudo /home/pi/racecontrol/venv/bin/pip install -r /home/pi/racecontrol/backend/requirements.txt`
- **`frontend/dist nicht gefunden`**: `deploy.ps1` (Windows) oder `deploy.sh` (Linux) erneut ausführen
- **`schema.sql not found`**: schema.sql fehlt → Deploy-Script erneut ausführen

### Port 1980 nicht erreichbar

```bash
# Lauscht uvicorn?
ss -tlnp | grep 1980

# Firewall (Raspberry Pi OS hat standardmäßig keine)
sudo iptables -L INPUT
```

### Falsches Frontend (alte Version)

```powershell
# Windows: rebuild erzwingen
Remove-Item "..\..\frontend\dist" -Recurse -Force
.\deploy.ps1 -CmHost 192.168.1.100
```

```bash
# Linux: rebuild erzwingen
rm -rf ../../frontend/dist
./deploy.sh 192.168.1.100
```

### Datenbank beschädigt

```bash
python3 ~/racecontrol/backend/db_health.py --vacuum
```

Bei schwerem Schaden:
```bash
sudo systemctl stop racecontrol
cp ~/racecontrol/racecontrol.db ~/racecontrol/racecontrol.db.bak
rm ~/racecontrol/racecontrol.db
sudo systemctl start racecontrol   # legt neue, leere DB an
```

---

## Verzeichnisstruktur auf dem CM3

```
/home/pi/racecontrol/
├── backend/               # FastAPI Python-Backend
│   ├── main.py
│   ├── database.py
│   ├── requirements.txt
│   └── routers/
├── frontend/
│   └── dist/              # Gebautes Vue-Frontend (von npm run build)
├── assets/                # Logos, Reglements, Druckvorlagen
├── schema.sql             # Datenbank-Schema (automatische Migration)
├── racecontrol.db         # SQLite-Datenbank (WAL-Modus, auto-erstellt)
├── venv/                  # Python Virtual Environment
├── install.sh             # Setup-Script
└── racecontrol.service    # Systemd-Kopie (Referenz)

/etc/systemd/system/
└── racecontrol.service    # Aktive Autostart-Definition
```
