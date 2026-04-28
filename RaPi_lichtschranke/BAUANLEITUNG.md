# Bauanleitung – Lichtschranke mit Raspberry Pi Zero 2 W

**Projekt:** RaceControl Pro – Zeitmessung Kart-Slalom  
**Variante:** D (TM1637 7-Segment-Anzeige) gemäß LICHTSCHRANKE_SETUP.md  
**Schwierigkeit:** Einsteiger (Löten nur für Stiftleiste nötig)  
**Bauzeit:** ca. 2–3 Stunden pro Einheit

---

## Übersicht

### Sensorprinzip: Reflexionslichtschranke

Sender und Empfänger sitzen im **selben Gehäuse** auf einer Seite der Fahrlinie.
Gegenüber liegt nur ein passiver **Retroreflektor** – kein Strom, kein Kabel.

```
  ┌─────────────────────────────────────────────┐     ┌─────────────┐
  │  Sensor-Einheit (RPi + Schranke)            │     │  Reflektor  │
  │  [Sender] ──→ ──→ ──→ ──→ ──→ ──→ ──→ ──→  │──→  │  (passiv)   │
  │  [Empfänger] ←── ←── ←── ←── ←── ←── ←──  │←──  │  ~2–5 m     │
  │  NPN-Signal → RPi                           │     └─────────────┘
  └─────────────────────────────────────────────┘
           │  1 Kabel (VCC / GND / Signal)
```

### Betriebsmodus A – Zwei Schranken (Start + Ziel getrennt)

Zwei Einheiten, je eine am Start und am Ziel.

### Betriebsmodus B – Eine Schranke (Start UND Ziel)

**Eine einzige Einheit** am Start/Ziel. Kurs ist ein geschlossener Loop.

```
1. Kart durchfährt → START   (Timer läuft)
2. Kart durchfährt → STOP    (Zeit wird angezeigt und gesendet)
```

### Modusauswahl per DIP-Schalter

Modus und Rolle werden über einen **DIP-Schalter am Gehäuse** eingestellt –
kein SSH, kein Code-Edit nötig. Das Display bestätigt den erkannten Modus kurz
beim Einschalten.

| DIP 1 | DIP 2 | Modus | Anzeige beim Start |
|-------|-------|-------|-------------------|
| ON    | ON    | A – zwei Schranken, Rolle **Start** | `A-St` |
| ON    | OFF   | A – zwei Schranken, Rolle **Ziel**  | `A-Zi` |
| OFF   | —     | B – eine Schranke (Start + Ziel)    | `b----` |

---

## 1. Teileliste und Preise

### Pflichtteile (pro Einheit)

| # | Bauteil | Menge | Preis ca. | Bezugsquelle |
|---|---------|-------|-----------|--------------|
| 1 | Raspberry Pi Zero 2 WH *(mit vorgelöteter Stiftleiste)* | 1 | 22 € | Berrybase, Pi-Shop.de, Reichelt |
| 2 | MicroSD-Karte 32 GB, Class 10 / A1 | 1 | 9 € | Amazon, Conrad |
| 3 | **Reflexionslichtschranke 5V NPN** *(Retroreflektiv, 3–5 m)* | 1 | 15 € | Amazon, AliExpress |
| 4 | **Retroreflektor** *(Fahrrad-Rückstrahler oder Prismenfolie)* | 1 | 2 € | Fahrradladen, Baumarkt |
| 5 | TM1637 6-stellige 7-Segment-Anzeige | 1 | 6 € | Amazon, AliExpress |
| 6 | **DIP-Schalter Modul 4-polig** | 1 | 2 € | Amazon, AliExpress |
| 7 | Drucktaster (momentary, 12 mm, NO) | 1 | 0,80 € | Reichelt, Conrad |
| 8 | Jumper-Kabel Buchse-Buchse (F-F), 30 cm, 40er-Set | 1 | 4 € | Amazon |
| 9 | USB-Netzteil 5 V / 2,5 A mit Micro-USB-Kabel | 1 | 11 € | Amazon |
| 10 | Powerbank 10.000 mAh *(für Batteriebetrieb)* | 1 | 18 € | Amazon |

**Summe (Modus B, 1 Schranke):** ca. **90 €**  
**Summe (Modus A, 2 Schranken):** ca. **180 €** *(2× alles)*

### Empfohlenes Gehäuse (pro Einheit)

| # | Bauteil | Preis ca. | Bezugsquelle |
|---|---------|-----------|--------------|
| 11 | Kunststoff-Gehäuse IP65, 120 × 80 × 55 mm | 8 € | Reichelt, Conrad |
| 12 | Kabelverschraubung M16 | 0,50 € | Baumarkt |
| 13 | Abstandshalter M2,5 × 10 mm + Schrauben (4 Stk) | 1,50 € | Amazon |

### Werkzeug

| Werkzeug | Bemerkung |
|----------|-----------|
| Lötkolben + Lötzinn | Nur nötig ohne vorgelötete Stiftleiste (kein „WH") |
| Kreuzschraubendreher | Gehäuse, Abstandshalter |
| Bohrer Ø 16 mm | Kabelverschraubung |
| Bohrer Ø 22 mm | Taster-Ausschnitt |
| Bohrer Ø 10–12 mm | DIP-Schalter-Modul (je nach Größe) |
| Multimeter | Spannungsprüfung |

---

## 2. Sensorauswahl und Funktionsprinzip

### Warum Reflexionslichtschranke?

| Merkmal | Reflexions­lichtschranke | Einweg­lichtschranke |
|---------|-------------------------|---------------------|
| Kabel | **Nur eine Seite** | Beide Seiten |
| Gegenseite | Passiver Reflektor (~2 €) | Sender mit Strom |
| Reichweite | 3–8 m | 5–20 m |
| Montageaufwand | **Gering** | Mittel |

### Sensorempfehlung: 5V NPN retroreflektiv

Suchbegriffe: `"retroreflective photoelectric sensor 5V NPN"` /  
`"Reflexionslichtschranke 5V Arduino NPN"` / `"E3Z-R61 5V clone"`

```
Typische Anschlüsse:
  Braun   = VCC (5 V)
  Blau    = GND
  Schwarz = Signal (NPN Open Collector)
            LOW  → Strahl empfangen (Reflektor sichtbar, kein Objekt)
            HIGH → Strahl unterbrochen (Kart fährt durch) = RISING-Flanke ✓
```

### Alternative: 12V-Sensor + Step-Up

Industrielle Sensoren (10–30V, NPN) sind günstiger und in größerer Auswahl
verfügbar. Mit Step-Up-Converter 5V → 12V (~3 €) direkt am RPi betreibbar.
Der NPN-Ausgang bleibt identisch am GPIO anschließbar.

### Retroreflektor

Ein handelsüblicher **Fahrrad-Rückstrahler** (~2 €) funktioniert perfekt.
Am gegenüberliegenden Pfosten per Kabelbinder oder Schraube befestigen.

### NPN-Pegel – kein Pegelwandler nötig

```
RPi GPIO (interner 50 kΩ Pull-Up auf 3,3 V)
    │
    ├── HIGH (3,3 V) wenn Strahl unterbrochen → RISING-Flanke = Auslösung
    │
  [NPN-Kollektor]
    │
   GND (LOW wenn Strahl frei)
```

---

## 3. GPIO-Belegung

| Funktion | GPIO (BCM) | Board-Pin | Kabelfarbe |
|----------|-----------|-----------|------------|
| Sensor S1 (Start / Einzel) | GPIO 17 | Pin 11 | Gelb |
| Sensor S2 (Ziel, nur Modus A) | GPIO 27 | Pin 13 | Orange |
| Reset-Taster | GPIO 22 | Pin 15 | Weiß |
| **DIP 1 – Modus** | **GPIO 5** | **Pin 29** | Lila |
| **DIP 2 – Rolle** | **GPIO 6** | **Pin 31** | Grau |
| TM1637 CLK | GPIO 21 | Pin 40 | Grün |
| TM1637 DIO | GPIO 20 | Pin 38 | Blau |
| 5 V (Sensor VCC) | — | Pin 2 | Rot |
| 3,3 V (Display VCC) | — | Pin 1 | Rot |
| GND | — | Pin 6, 9, 14 … | Schwarz |

---

## 4. Schaltplan

```
                    Raspberry Pi Zero 2 W
                   ┌──────────────────────┐
                   │  Pin 1  (3,3V) ──────────── TM1637 VCC
                   │  Pin 2  (5V)   ──────────── S1 VCC  (braun)
                   │                        ──── S2 VCC  (braun, nur Modus A)
                   │  Pin 6  (GND)  ────┬──────── TM1637 GND
                   │                   ├──────── S1 GND  (blau)
                   │                   ├──────── S2 GND  (blau, nur Modus A)
                   │                   ├──────── Taster  → GND
                   │                   └──────── DIP COM → GND
                   │  Pin 11 (GPIO17) ─────────── S1 Signal   (schwarz)
                   │  Pin 13 (GPIO27) ─────────── S2 Signal   (schwarz, Modus A)
                   │  Pin 15 (GPIO22) ─────────── Taster
                   │  Pin 29 (GPIO 5) ─────────── DIP 1  (Modus)
                   │  Pin 31 (GPIO 6) ─────────── DIP 2  (Rolle)
                   │  Pin 38 (GPIO20) ─────────── TM1637 DIO
                   │  Pin 40 (GPIO21) ─────────── TM1637 CLK
                   └──────────────────────┘

DIP-Schalter-Modul:
  DIP 1 ──── GPIO 5  (Pin 29)  │  ON = nach GND (LOW)  = Modus A
  DIP 2 ──── GPIO 6  (Pin 31)  │  ON = nach GND (LOW)  = Start-Rolle
  COM   ──── GND     (Pin 6)   │  OFF = offen  (HIGH via Pull-Up)
  DIP 3, 4 reserviert
```

---

## 5. Schritt-für-Schritt Aufbau

### Schritt 1: Raspberry Pi vorbereiten

1. **Raspberry Pi OS Lite (64-bit)** im Raspberry Pi Imager auf MicroSD flashen.
2. Vor dem Flashen konfigurieren:
   - Hostname: `racecontrol-01` (beide Einheiten erhalten individuelle Hostnamen)
   - WLAN-SSID und Passwort
   - SSH aktivieren, Benutzer/Passwort setzen
3. Einsetzen, starten, verbinden:
   ```bash
   ssh pi@racecontrol-01.local
   sudo apt update && sudo apt upgrade -y
   ```

### Schritt 2: Software installieren

```bash
pip install websocket-client RPi.GPIO
pip install git+https://github.com/depklyon/raspberrypi-tm1637
mkdir -p ~/RaPi_lichtschranke
# racecontrol_client.py per scp oder git clone übertragen
```

### Schritt 3: DIP-Schalter-Konfiguration im Code

Der Client liest die DIP-Schalter beim Start aus. In `racecontrol_client.py`
die folgenden Konstanten prüfen / anpassen:

```python
# ── DIP-Schalter GPIO-Pins ───────────────────────────────────────────────────
DIP1_PIN = 5    # Modus:  ON (LOW) = Modus A (2 Schranken)
                #         OFF(HIGH) = Modus B (1 Schranke)
DIP2_PIN = 6    # Rolle:  ON (LOW) = Start
                #         OFF(HIGH) = Ziel  (nur relevant in Modus A)

# ── Mindestlaufzeit (Sekunden) ───────────────────────────────────────────────
MIN_TIME_DUAL   = 5.0    # Modus A: Schnellste erlaubte Zeit
MIN_TIME_SINGLE = 15.0   # Modus B: Muss unter kürzester Rundenzeit liegen

# ── Backend ──────────────────────────────────────────────────────────────────
BACKEND_HOST = "192.168.0.100"
BACKEND_PORT = 1980
```

Der Startup-Code liest dann automatisch:

```python
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setup(DIP1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DIP2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# DIP 1: ON (LOW) = Modus A, OFF (HIGH) = Modus B
SINGLE_SENSOR_MODE = (GPIO.input(DIP1_PIN) == GPIO.HIGH)

# DIP 2: ON (LOW) = Start-Rolle, OFF (HIGH) = Ziel-Rolle
role = "start" if GPIO.input(DIP2_PIN) == GPIO.LOW else "ziel"
DEVICE_ID = f"gpio-lichtschranke-{role}"
MIN_TIME   = MIN_TIME_SINGLE if SINGLE_SENSOR_MODE else MIN_TIME_DUAL

# Modus kurz auf dem Display anzeigen
if SINGLE_SENSOR_MODE:
    display.show_string("b----")        # Modus B
elif role == "start":
    display.show_string("A-St ")        # Modus A, Start
else:
    display.show_string("A-Zi ")        # Modus A, Ziel
time.sleep(2)
display.show_string("----")             # Bereit
```

### Schritt 4: Autostart einrichten

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
journalctl -u racecontrol -f
```

### Schritt 5: Verkabelung

**Reflexionslichtschranke (3 Drähte):**

| Sensor-Draht | RPi-Pin | Funktion |
|---|---|---|
| Braun | Pin 2 (5V) | Versorgung |
| Blau | Pin 6 (GND) | Masse |
| Schwarz (S1) | Pin 11 (GPIO 17) | Signal Start / Einzel |
| Schwarz (S2) | Pin 13 (GPIO 27) | Signal Ziel *(nur Modus A)* |

**DIP-Schalter-Modul:**

| DIP-Pin | RPi-Pin | Funktion |
|---|---|---|
| COM | Pin 6 (GND) | Gemeinsame Masse |
| DIP 1 | Pin 29 (GPIO 5) | Modus-Auswahl |
| DIP 2 | Pin 31 (GPIO 6) | Rollen-Auswahl |
| DIP 3, 4 | — | Reserviert |

**TM1637 Display:**

| Display-Pin | RPi-Pin |
|---|---|
| VCC | Pin 1 (3,3 V) |
| GND | Pin 6 (GND) |
| CLK | Pin 40 (GPIO 21) |
| DIO | Pin 38 (GPIO 20) |

**Reset-Taster:** Pin 15 (GPIO 22) ↔ Pin 6 (GND).

> **Kabelprüfung vor Ersteinschalten:** Multimeter zwischen Pin 2 (5V) und
> Pin 6 (GND) → kein Kurzschluss.

### Schritt 6: Sensor ausrichten

1. Retroreflektor gegenüber montieren (Fahrrad-Rückstrahler an Pfosten).
2. Sensor einschalten → LED am Sensor leuchtet bei korrekter Ausrichtung.
3. Höhe: ca. 30–50 cm über Boden (für sichere Kart-Detektion).
4. Probe: Hand in den Strahlengang → LED erlischt, GPIO wechselt auf HIGH ✓

---

## 6. Gehäuse und Montage

### Frontplatten-Layout (Empfehlung)

```
┌─────────────────────────────────────────────────┐
│  [TM1637 Display  ██████████████████████████]   │  ← Fenster ausschneiden
│                                                 │
│  [ DIP 1 2 3 4 ]          [ Reset-Taster ]     │
│   Modus Rolle  __ __                            │
└──────────────────────────────────────────────── ┘
                              │ Kabelverschraubung unten
                              └─── Sensorkabel (nach außen)
```

### Gehäuse vorbereiten

1. **Displayfenster** (70 × 15 mm) ausschneiden, transparente Folie innen kleben.
2. **DIP-Schalter** einbauen: Aussparung passend zur Modulgröße fräsen/feilen
   oder kleinen Deckel ausschneiden (je nach Modultyp auch einfach einklipsen).
3. Bohrungen: Ø 22 mm für Taster, Ø 16 mm für Kabelverschraubung.
4. RPi mit Abstandshaltern M2,5 × 10 mm befestigen.

### Beschriftung

DIP-Schalter beschriften (Klebe-Etikett oder Gravur):

```
  1         2
  │         │
 [▓]  [▓]  [ ]  [ ]
 Mod  Rolle
 ON=A ON=St
 OFF=b OFF=Zi
```

### Montage im Feld

| Option | Kosten | Hinweis |
|--------|--------|---------|
| Kamerastativ (1/4"-Gewinde) | ~15–25 € | Flexibel justierbar |
| Baken-Pfosten + Rohrschelle | ~5 € | Sehr stabil |
| 3D-gedruckter Halter | ~1 € Filament | Maßgeschneidert |

---

## 7. Gesamtkosten

### Modus B – Eine Einheit (häufigste Variante)

| Position | Preis |
|----------|------:|
| Raspberry Pi Zero 2 WH | 22 € |
| MicroSD 32 GB | 9 € |
| Reflexionslichtschranke 5V NPN | 15 € |
| Retroreflektor (Fahrrad-Rückstrahler) | 2 € |
| TM1637 Display | 6 € |
| DIP-Schalter Modul 4-polig | 2 € |
| Taster, Kabel, Kleinteile | 6 € |
| USB-Netzteil / Powerbank | 18 € |
| Gehäuse + Befestigung | 10 € |
| **Gesamt** | **~90 €** |

### Modus A – Zwei Einheiten

| Position | pro Einheit | × 2 |
|----------|:-----------:|:---:|
| Raspberry Pi Zero 2 WH | 22 € | 44 € |
| MicroSD 32 GB | 9 € | 18 € |
| Reflexionslichtschranke | 15 € | 30 € |
| Retroreflektor | 2 € | 4 € |
| TM1637 Display | 6 € | 12 € |
| DIP-Schalter Modul | 2 € | 4 € |
| Taster, Kabel, Kleinteile | 6 € | 12 € |
| USB-Netzteil / Powerbank | 18 € | 36 € |
| Gehäuse + Befestigung | 10 € | 20 € |
| **Gesamt** | **~90 €** | **~180 €** |

---

## 8. Inbetriebnahme und Test

### DIP-Schalter vor dem Start setzen

DIP-Schalter **vor** dem Einschalten einstellen – werden nur beim Start gelesen.

| Szenario | DIP 1 | DIP 2 | Display-Anzeige |
|----------|-------|-------|-----------------|
| Eine Schranke (Slalom-Loop) | OFF | — | `b----` |
| Zwei Schranken – diese ist Start | ON | ON | `A-St ` |
| Zwei Schranken – diese ist Ziel | ON | OFF | `A-Zi ` |

### Funktionstest ohne Backend

```bash
python3 py_code_raspi_TM1637.py
```

Display zeigt gewählten Modus → dann `----`. Strahl unterbrechen → Timer läuft.

### Modus-B-Test (eine Schranke)

1. Strahl unterbrechen → `----` (Timer läuft)
2. Länger als `MIN_TIME` warten
3. Strahl erneut unterbrechen → Zeit erscheint, Ergebnis wird gesendet

### Typische Fehler

| Symptom | Ursache | Lösung |
|---------|---------|--------|
| Display zeigt falschen Modus | DIP-Schalter nach Neustart geändert | Neustart (DIP wird nur beim Boot gelesen) |
| Modus B: stoppt sofort nach Start | `MIN_TIME_SINGLE` zu niedrig | Wert erhöhen (mind. 10 s) |
| Modus B: Ziel nicht erkannt | `MIN_TIME_SINGLE` zu hoch | Wert unter kürzeste Rundenzeit |
| Sensor-LED leuchtet nicht | Reflektor nicht ausgerichtet | Ausrichtung korrigieren |
| Fehlauslösungen bei Sonne | Direktes Sonnenlicht auf Empfänger | Sensor abschirmen / drehen |
| Display zeigt nichts | TM1637 VCC an 5V statt 3,3V | VCC → Pin 1 (3,3V) |
| Zeit wird nicht gesendet | Backend nicht erreichbar | `BACKEND_HOST` und WLAN prüfen |

---

## 9. Weiterführende Dokumentation

| Dokument | Inhalt |
|----------|--------|
| [notes.md](notes.md) | GPIO-Belegung, Abhängigkeiten, WebSocket-Protokoll |
| [LICHTSCHRANKE_SETUP.md](../LICHTSCHRANKE_SETUP.md) | Alle Varianten A–E, Vergleich, Autostart |
| [BAUANLEITUNG_RPi4_Server.md](BAUANLEITUNG_RPi4_Server.md) | RPi 4 All-in-One mit vollem Backend |
| [racecontrol_client.py](racecontrol_client.py) | Produktions-Client TM1637 |
| [py_code_raspi_TM1637.py](py_code_raspi_TM1637.py) | Standalone-Test ohne Backend |
