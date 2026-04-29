# Bauanleitung – RaceControl All-in-One Server (Raspberry Pi 4)

**Projekt:** RaceControl Pro – Kart-Slalom Zeitmessung  
**Variante:** RPi 4 als vollständiger Server + Lichtschranken-Client  
**Schwierigkeit:** Mittel (Linux-Grundkenntnisse empfohlen)  
**Bauzeit:** ca. 3–4 Stunden

---

## Übersicht und Konzept

Dieses Setup betreibt auf **einem einzigen Raspberry Pi 4** den vollständigen Stack:

```
┌──────────────────────────────────────────────────────────────────┐
│                    Raspberry Pi 4 (4 GB)                         │
│                                                                  │
│   ┌──────────────────────────────────┐                           │
│   │  uvicorn :1980  (FastAPI)        │                           │
│   │   /api/*    → Backend-Logik      │  ←──── WLAN-AP            │
│   │   /ws        → Browser-WS        │        SSID: RaceControl  │
│   │   /ws/timing → Lichtschranke WS  │        IP:   10.42.0.1    │
│   │   /*         → Frontend (Vue)    │                           │
│   └──────────────────────────────────┘                           │
│                    ↑                                             │
│   ┌────────────────┴─────────────────┐                           │
│   │  racecontrol_client.py           │  GPIO 17/27 → IR-Sensoren │
│   │  ws://localhost:1980/ws/timing   │  GPIO 22    → Reset       │
│   │  TM1637 Display lokal            │  GPIO 20/21 → TM1637      │
│   └──────────────────────────────────┘                           │
└──────────────────────────────────────────────────────────────────┘

     Option A: Laptop/Tablet ──→ WLAN "RaceControl" ──→ http://10.42.0.1:1980
     Option B: Laptop/Tablet ──→ Router/AP (DHCP)   ──→ http://racecontrol.local:1980
```

**Vorteile gegenüber dem Zero-2-W-Setup:**
- Kein separater Laptop nötig – der RPi 4 **ist** der Server
- WiFi-Hotspot: alle Geräte (Zeitnehmer-Tablets, Sprecher-Laptop) verbinden sich direkt
- Deutlich mehr Rechenleistung für viele gleichzeitige Verbindungen
- Läuft autonom ohne externe Infrastruktur

**Benötigt trotzdem zwei Einheiten** (Start + Ziel), sofern beide Schranken
nicht am selben Gehäuse montiert werden können. Die zweite Einheit kann ein
günstiger **RPi Zero 2 W** gemäß [BAUANLEITUNG.md](BAUANLEITUNG.md) sein.

---

## 1. Teileliste und Preise

### Pflichtteile

| # | Bauteil | Menge | Preis ca. | Bezugsquelle |
|---|---------|-------|-----------|--------------|
| 1 | Raspberry Pi 4 Model B **4 GB** | 1 | 55 € | Berrybase, Pi-Shop.de, Reichelt |
| 2 | Aktiv-Kühlgehäuse mit Lüfter *(z.B. Argon NEO 5 Fan)* | 1 | 18 € | Berrybase, Amazon |
| 3 | MicroSD 64 GB, **A2** Class (für bessere Datenbank-I/O) | 1 | 12 € | Amazon, Conrad |
| 4 | **Reflexionslichtschranke 5V NPN** *(Retroreflektiv, Sender+Empfänger in einem Gehäuse)* | 1 | 15 € | Amazon, AliExpress |
| 5a | **Retroreflektor** *(Fahrrad-Rückstrahler oder Prismenfolie)* | 1 | 2 € | Fahrradladen, Baumarkt |
| 5 | TM1637 6-stellige 7-Segment-Anzeige | 1 | 6 € | Amazon, AliExpress |
| 6 | Drucktaster (momentary, 12 mm, NO) | 1 | 0,80 € | Reichelt, Conrad |
| 7 | Jumper-Kabel Buchse-Buchse (F-F), 20 cm, 40er-Set | 1 | 4 € | Amazon |
| 8 | USB-C-Netzteil **5 V / 3 A** *(offizielles RPi 4 Netzteil empfohlen)* | 1 | 14 € | Berrybase, Amazon |
| 9 | Powerbank **20.000 mAh**, USB-C PD, min. 15 W | 1 | 28 € | Amazon |

**Summe Pflichtteile:** ca. **150–165 €**

### Gehäuse für Außeneinsatz

| # | Bauteil | Preis ca. | Bezugsquelle |
|---|---------|-----------|--------------|
| 10 | Kunststoff-Gehäuse IP65, 160 × 120 × 60 mm *(größer als beim Zero)* | 12 € | Reichelt, Conrad |
| 11 | Kabelverschraubungen M16 (3 Stk) | 1,50 € | Baumarkt |
| 12 | Abstandshalter M2,5 × 10 mm + Schrauben (4 Stk) | 1,50 € | Amazon |

**Summe Gehäuse:** ca. **15 €**

### Optionales Zubehör

| Bauteil | Preis ca. | Bemerkung |
|---------|-----------|-----------|
| RPi 4 offizielles 7" Touchscreen (DSI) | 70 € | Lokale Bedienung ohne externen Laptop |
| USB-SSD 240 GB (für Datenbank statt SD) | 35 € | Empfohlen für Dauerbetrieb |
| USB-Hub (für Tastatur/Maus bei Ersteinrichtung) | 8 € | Einmalig nötig |

---

## 2. Systemarchitektur

### Software-Stack

| Komponente | Technologie | Port / Pfad |
|------------|-------------|-------------|
| Backend API | FastAPI + uvicorn | `:1980/api/*` |
| WebSocket (Browser) | FastAPI | `:1980/ws` |
| WebSocket (Lichtschranke) | FastAPI | `:1980/ws/timing` |
| Frontend | Vue 3 + Vite (statisch) | `:1980/*` (aus `frontend/dist/`) |
| Datenbank | SQLite (aiosqlite) | `backend/racecontrol.db` |
| Lichtschranken-Client | Python / RPi.GPIO | verbindet auf `localhost:1980` |
| WiFi Access Point | NetworkManager Hotspot | SSID: `RaceControl`, IP: `10.42.0.1` |

### Dateistruktur auf dem RPi

```
/home/pi/RaceControl/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── racecontrol.db          ← Datenbank (automatisch erstellt)
├── frontend/
│   └── dist/                   ← Vorher auf PC gebaut, dann kopiert
│       ├── index.html
│       └── assets/
├── assets/                     ← Reglements, Logos
└── RaPi_lichtschranke/
    └── racecontrol_client.py
```

---

## 3. GPIO-Belegung (identisch mit Zero 2 W)

| Funktion | GPIO (BCM) | Board-Pin | Kabelfarbe |
|----------|-----------|-----------|------------|
| IR-Sensor Start (S1) | GPIO 17 | Pin 11 | Gelb |
| IR-Sensor Ziel (S2) | GPIO 27 | Pin 13 | Orange |
| Reset-Taster | GPIO 22 | Pin 15 | Weiß |
| TM1637 CLK | GPIO 21 | Pin 40 | Grün |
| TM1637 DIO | GPIO 20 | Pin 38 | Blau |
| 5 V (Sensor VCC) | — | Pin 2 | Rot |
| 3,3 V (Display VCC) | — | Pin 1 | Rot |
| GND | — | Pin 6 | Schwarz |

> Detaillierter Schaltplan und Sensortechnik (E18-D80NK, NPN Open-Collector,
> kein Pegelwandler nötig) → [BAUANLEITUNG.md Abschnitt 2–4](BAUANLEITUNG.md)

---

## 4. Installationsanleitung

### Schritt 1: Betriebssystem flashen

1. **Raspberry Pi OS Lite (64-bit)** im Raspberry Pi Imager auswählen.
2. Vor dem Flashen im Imager konfigurieren:
   - Hostname: `racecontrol`
   - WLAN temporär (Heimnetz) für den Download-Schritt
   - SSH aktivieren
   - Benutzer `pi` mit Passwort setzen
3. MicroSD einsetzen, Strom anlegen, per SSH verbinden:
   ```bash
   ssh pi@racecontrol.local
   ```

### Schritt 2: System aktualisieren und Abhängigkeiten installieren

```bash
sudo apt update && sudo apt upgrade -y

# Python + pip
sudo apt install -y python3-pip python3-venv git

# Node.js 20 LTS (für Frontend-Build auf dem RPi – alternativ auf PC builden)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

### Schritt 3: RaceControl Repository kopieren

```bash
# Option A: per git clone (wenn Repo erreichbar)
git clone <repository-url> /home/pi/RaceControl

# Option B: per scp vom Entwicklungs-PC
scp -r ./RaceControl pi@racecontrol.local:/home/pi/
```

### Schritt 4: Python-Umgebung und Backend einrichten

```bash
cd /home/pi/RaceControl/backend

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
pip install websocket-client RPi.GPIO
pip install git+https://github.com/depklyon/raspberrypi-tm1637

# Erste Test-Ausführung (prüfen ob Backend startet)
python3 -m uvicorn main:app --host 0.0.0.0 --port 1980
# Ctrl+C nach erfolgreichem Start
```

### Schritt 5: Frontend bauen

**Option A – auf dem PC bauen (empfohlen, schneller):**

```bash
# Auf dem Entwicklungs-PC:
cd RaceControl/frontend
npm install
npm run build

# dist/-Ordner auf den RPi kopieren:
scp -r dist/ pi@racecontrol.local:/home/pi/RaceControl/frontend/dist
```

**Option B – direkt auf dem RPi bauen:**

```bash
# Auf dem RPi (dauert 5–10 Minuten):
cd /home/pi/RaceControl/frontend
npm install
npm run build
```

> Nach dem Build liegt `frontend/dist/` am richtigen Ort.
> Das Backend serviert diesen Ordner automatisch über `/`.

### Schritt 6: Lichtschranken-Client konfigurieren

```bash
nano /home/pi/RaceControl/RaPi_lichtschranke/racecontrol_client.py
```

Wichtige Einstellungen: Da Backend und Client auf demselben Gerät laufen,
`BACKEND_HOST` auf `localhost` setzen. Außerdem Modus wählen:

```python
BACKEND_HOST       = "localhost"   # ← nicht die WLAN-IP, sondern localhost
BACKEND_PORT       = 1980

# Modus A: zwei separate Sensoren (Start + Ziel)
SINGLE_SENSOR_MODE = False
MIN_TIME           = 5.0

# Modus B: eine Schranke für Start UND Ziel (Kurs = geschlossener Loop)
# SINGLE_SENSOR_MODE = True
# MIN_TIME           = 15.0    # ← kürzeste erwartete Rundenzeit
```

Details zu Modus A/B → [BAUANLEITUNG.md Abschnitt 5](BAUANLEITUNG.md).

### Schritt 7: Systemd-Services einrichten

**7a – Backend-Service:**

```bash
sudo nano /etc/systemd/system/racecontrol-backend.service
```

```ini
[Unit]
Description=RaceControl Pro Backend
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/RaceControl/backend
ExecStart=/home/pi/RaceControl/backend/venv/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 1980
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

**7b – Lichtschranken-Service:**

```bash
sudo nano /etc/systemd/system/racecontrol-lichtschranke.service
```

```ini
[Unit]
Description=RaceControl Lichtschranken-Client (GPIO)
After=racecontrol-backend.service
Wants=racecontrol-backend.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/RaceControl/RaPi_lichtschranke
ExecStart=/home/pi/RaceControl/backend/venv/bin/python3 racecontrol_client.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

**Services aktivieren:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable racecontrol-backend racecontrol-lichtschranke
sudo systemctl start  racecontrol-backend

# Kurz warten bis Backend vollständig gestartet
sleep 3
sudo systemctl start  racecontrol-lichtschranke

# Status prüfen
sudo systemctl status racecontrol-backend
sudo systemctl status racecontrol-lichtschranke

# Live-Logs
journalctl -u racecontrol-backend        -f
journalctl -u racecontrol-lichtschranke  -f
```

### Schritt 8: Netzwerk einrichten

Wähle eine der beiden Varianten je nach Einsatzsituation:

---

#### Option A: Eigener WLAN-Hotspot *(empfohlen für autarken Betrieb)*

Der RPi 4 spannt ein eigenes WLAN auf. Alle Geräte (Zeitnehmer, Sprecher, Admin)
verbinden sich damit. **Keine externe Infrastruktur nötig.**

```bash
# Hotspot erstellen (NetworkManager)
sudo nmcli device wifi hotspot \
    ifname wlan0 \
    ssid "RaceControl" \
    password "timing1234" \
    con-name "RaceControl-AP"

# Beim Booten automatisch starten
sudo nmcli connection modify RaceControl-AP connection.autoconnect yes
sudo nmcli connection modify RaceControl-AP connection.autoconnect-priority 100

# Sofort aktivieren
sudo nmcli connection up RaceControl-AP
```

> **Passwort anpassen!** Wähle ein eigenes Passwort (mind. 8 Zeichen).

| | |
|---|---|
| **Feste IP des RPi** | `10.42.0.1` |
| **Erreichbarkeit** | `http://10.42.0.1:1980` |
| **Alternativ per mDNS** | `http://racecontrol.local:1980` |

```bash
# mDNS sicherstellen (Avahi) – für racecontrol.local
sudo apt install -y avahi-daemon
sudo systemctl enable --now avahi-daemon
```

---

#### Option B: Externes WLAN mit DHCP *(wenn Router/AP vorhanden)*

Der RPi verbindet sich mit einem vorhandenen WLAN-Router (z. B. in der Veranstaltungshalle
oder einem mobilen LTE-Router). Die IP-Adresse wird per DHCP vergeben.

**Voraussetzung:** Das Heimnetz-WLAN wurde bereits in Schritt 1 im Raspberry Pi Imager
eingetragen. Für ein anderes Netz nachträglich hinzufügen:

```bash
# WLAN-Netz hinzufügen (einmalig)
sudo nmcli device wifi connect "SSID-des-Routers" password "WLAN-Passwort"
```

**mDNS für stabilen Hostnamen einrichten:**

Da DHCP die IP bei jedem Boot ändern kann, ist mDNS die zuverlässigste Zugriffsmethode:

```bash
sudo apt install -y avahi-daemon
sudo systemctl enable --now avahi-daemon
```

RaceControl ist danach erreichbar unter: `http://racecontrol.local:1980`

> `racecontrol.local` funktioniert auf Windows 10+, macOS, iOS und Android
> ohne zusätzliche Konfiguration. Bei älteren Geräten ggf. IP direkt verwenden.

**Aktuelle IP-Adresse ermitteln:**

```bash
# IP anzeigen
hostname -I | awk '{print $1}'

# Oder detaillierter
ip -4 addr show wlan0
```

**DHCP-Reservierung empfohlen:**

Für zuverlässigen Betrieb empfiehlt es sich, im Router eine **statische DHCP-Lease**
(auch „DHCP-Reservierung") für den RPi einzurichten. Dazu im Router-Webinterface:

1. Gerät `racecontrol` in der DHCP-Tabelle suchen
2. MAC-Adresse des RPi fixieren → feste IP zuweisen (z. B. `192.168.1.100`)
3. Browser-URL dann dauerhaft: `http://192.168.1.100:1980`

**MAC-Adresse des RPi ermitteln:**

```bash
ip link show wlan0 | grep ether | awk '{print $2}'
```

| | |
|---|---|
| **IP** | dynamisch per DHCP (oder per Reservierung fest) |
| **Erreichbarkeit** | `http://racecontrol.local:1980` *(mDNS)* |
| **Fallback** | `http://<IP>:1980` *(IP via `hostname -I`)* |

---

> **Vergleich der Optionen:**
>
> | | Option A (Hotspot) | Option B (externer AP) |
> |---|---|---|
> | Infrastruktur | keine | Router/AP vorhanden |
> | IP | immer `10.42.0.1` | per DHCP (oder Reservierung) |
> | Zugriffsname | `10.42.0.1` oder `racecontrol.local` | `racecontrol.local` oder feste IP |
> | Internet-Zugang | kein | ja (über Router) |
> | Ideal für | Wettkampf ohne Infra | Training, feste Anlage |

### Schritt 9: Firewall (optional, empfohlen)

```bash
sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment "SSH"
sudo ufw allow 1980/tcp comment "RaceControl"
sudo ufw --force enable
```

---

## 5. Inbetriebnahme

### Checkliste vor dem ersten Start

- [ ] Sensoren verkabelt und Poti eingestellt
- [ ] TM1637 zeigt `----` nach Start
- [ ] `sudo systemctl status racecontrol-backend` → **active (running)**
- [ ] `sudo systemctl status racecontrol-lichtschranke` → **active (running)**
- [ ] Netzwerk-Option gewählt (A = Hotspot / B = externer AP)
- [ ] **Option A:** WLAN-Hotspot "RaceControl" sichtbar auf Handy/Laptop → `http://10.42.0.1:1980`
- [ ] **Option B:** RPi im Heimnetz erreichbar → `http://racecontrol.local:1980`
- [ ] Login-Seite erscheint

### Funktionstest

```bash
# Backend-Gesundheit
curl http://localhost:1980/health
# Erwartete Antwort: {"status":"ok"}

# WebSocket-Verbindung vom Lichtschranken-Client prüfen
journalctl -u racecontrol-lichtschranke -n 20
# Sollte zeigen: "[CONN] Verbunden mit ws://localhost:1980/ws/timing"
```

### Ablauf im Betrieb

**Option A (eigener Hotspot):**
1. RPi 4 einschalten → Backend startet automatisch (~15 s Bootzeit)
2. WLAN "RaceControl" erscheint
3. Zeitnehmer-Laptop/Tablet verbindet sich mit WLAN "RaceControl"
4. Browser auf `http://10.42.0.1:1980` → RaceControl-Oberfläche
5. TM1637 zeigt Lichtschranken-Status direkt am Gerät

**Option B (externer AP):**
1. RPi 4 einschalten → verbindet sich automatisch mit dem konfigurierten WLAN
2. Zeitnehmer-Geräte verbinden sich mit demselben WLAN-Router
3. Browser auf `http://racecontrol.local:1980` → RaceControl-Oberfläche  
   *(Fallback: IP per `hostname -I` auf dem RPi ermitteln)*
4. TM1637 zeigt Lichtschranken-Status direkt am Gerät

---

## 6. Gesamtkosten im Vergleich

| Variante | Preis | Besonderheit |
|----------|-------|--------------|
| Zero 2 W (nur Client) | ~79 € | Braucht externen Laptop als Server |
| RPi 4 All-in-One | ~160 € | Vollständiger Server + Client, eigenes WLAN |
| RPi 4 + Zero 2 W (empfohlen) | ~240 € | RPi 4 = Server+Start, Zero = Ziel |

---

## 7. Optionen und Erweiterungen

### Option A: USB-SSD statt MicroSD (empfohlen für Dauerbetrieb)

MicroSD-Karten verschleißen durch häufige Datenbank-Schreibzugriffe.
Eine USB-3-SSD verlängert die Lebensdauer erheblich:

```bash
# SSD als Boot-Medium einrichten (im Raspberry Pi Imager):
# → Storage → USB-SSD auswählen statt SD-Karte
# → Gleiche Konfiguration wie für SD
```

### Option B: Offizieller RPi 7" Touchscreen

Ermöglicht lokale Bedienung ohne externen Laptop (Admin-Ansicht direkt am Gerät):

```bash
# Chromium im Kiosk-Modus nach Boot automatisch starten
sudo apt install -y chromium-browser

# Autostart-Datei anlegen
mkdir -p /home/pi/.config/autostart
cat > /home/pi/.config/autostart/racecontrol-kiosk.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=RaceControl Kiosk
Exec=chromium-browser --kiosk --app=http://localhost:1980
EOF
```

> Benötigt Raspberry Pi OS **mit Desktop** (nicht Lite).

### Option D: Werkzeug-Akku als mobile Stromversorgung (12 V / 18 V)

Wer keinen USB-C-PD-fähigen Powerbank zur Hand hat oder eine längere Laufzeit
benötigt, kann handelsübliche **Akkuschrauber-Akkus (12 V oder 18 V)** nutzen.
Dafür wird nur ein kleines DC-DC-Wandlermodul (Buck-Converter) benötigt.

#### Schaltungskonzept

```
 Akku (12 V / 18 V)
  [B+] ──────────────────────────┐
                                  ▼
                      ┌──────────────────────┐
                      │  DC-DC Buck-Converter │
                      │  IN:  8–32 V         │
                      │  OUT: 5 V / 3 A      │
                      └──────────┬───────────┘
                                  │ USB-C (5 V, 3 A)
                                  ▼
                      ┌──────────────────────┐
                      │  Raspberry Pi 4      │
                      │  USB-C Power Input   │
                      └──────────────────────┘
  [B-] ──────────────────────────┘ (GND durchverbinden)
```

#### Benötigte Teile

| Bauteil | Preis ca. | Bezugsquelle |
|---------|-----------|--------------|
| **DC-DC Buck-Converter** 8–32 V → 5 V, 3 A *(z.B. XL4016, LM2596 oder Pololu D24V22F5)* | 5–12 € | Amazon, AliExpress, Reichelt |
| **Akku-Adapter** passend zur eigenen Marke *(Makita, Bosch, DeWalt …)* | 8–18 € | Amazon, AliExpress |
| USB-C-Kabel (A/barrel → USB-C) oder USB-C-Buchse am Converter-Ausgang | 3–5 € | Amazon |
| Schraubklemmen oder Lüsterklemmen (für Verdrahtung) | 1 € | Baumarkt |

**Summe Zusatzteile:** ca. **17–36 €**

> **Akku-Adapter:** Für jede Marke gibt es auf AliExpress günstige
> Kunststoff-Adapter, die auf die Akku-Schiene gesteckt werden und
> Schraubklemmen für B+ / B- herausführen.  
> Suchbegriff: "Makita 18V battery holder adapter", "Bosch 18V battery adapter"

#### Laufzeiten (Richtwert)

| Akku | Kapazität | RPi 4 (Ø 8 W inkl. Sensor+Display) | Laufzeit |
|------|-----------|--------------------------------------|---------|
| 12 V / 2 Ah | 24 Wh | ~8 W | **~2,5 h** |
| 18 V / 2 Ah | 36 Wh | ~8 W | **~4 h** |
| 18 V / 4 Ah | 72 Wh | ~8 W | **~8 h** |
| 18 V / 5 Ah | 90 Wh | ~8 W | **~10 h** |

> **Wirkungsgrad des Wandlers (~85 %)** ist bereits eingerechnet.
> Ein halber Wettkampftag ist realistisch mit einem Standard-4-Ah-Akku.

#### Hinweise

- Den Wandler **nicht auf den maximalen Ausgangsstrom (3 A) dauerhaft belasten** —
  ein Wandler für 5 A ist langlebiger und läuft kühler.
- Den eingestellten Ausgangsstrom mit einem Multimeter prüfen, **bevor** der RPi
  angeschlossen wird. Zu hohe Spannung (> 5,25 V) beschädigt den RPi 4 sofort.
- **Alternative ohne Lötarbeit:** Einige Marken-Akkus (Bosch Professional,
  Makita 18 V XGT) bieten Akkus mit eingebautem **USB-A-/USB-C-Ausgang** (5 V / 2–3 A).
  Diese können direkt ohne Wandler verwendet werden — Preis der Akkus mit USB-Ausgang
  liegt bei 40–80 €.

### Option C: Datenbank-Backup auf USB-Stick

```bash
# /etc/cron.d/racecontrol-backup
sudo bash -c 'cat > /etc/cron.d/racecontrol-backup << EOF
# Täglich um 23:00 Uhr Datenbank sichern
0 23 * * * pi cp /home/pi/RaceControl/backend/racecontrol.db /media/usb-backup/racecontrol-\$(date +\%Y\%m\%d).db
EOF'
```

---

## 8. Weiterführende Dokumentation

| Dokument | Inhalt |
|----------|--------|
| [BAUANLEITUNG.md](BAUANLEITUNG.md) | RPi Zero 2 W – Schaltplan, Sensortechnik, Gehäusebau |
| [notes.md](notes.md) | GPIO-Pinout, WebSocket-Protokoll, Abhängigkeiten |
| [LICHTSCHRANKE_SETUP.md](../LICHTSCHRANKE_SETUP.md) | Alle Varianten A–E im Vergleich |
| [racecontrol_client.py](racecontrol_client.py) | Lichtschranken-Client (TM1637) |
