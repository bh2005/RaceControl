# Bauanleitung: ESP32-Lichtschranken (WiFi + LoRa + DIP-Schalter)

**Autor:** BH2005 · MSC Braach e.V. im ADAC  
**Gilt für:** alle drei ESP32-Sketche

| Sketch | Einsatz |
|--------|---------|
| `esp32_tm1637_lichtschranke.ino` | Standalone-Messung + optionales WiFi-Reporting |
| `esp32_max7219_lichtschranke.ino` | Wie TM1637, aber mit Live-Anzeige (8-Digit) |
| `esp32_lora_wifi_sender.ino` | Start/Split/Finish-Sender, WiFi primär, LoRa Fallback |

---

## 1. Warum ESP32 statt Arduino Nano?

| Kriterium | Arduino Nano | ESP32 |
|-----------|-------------|-------|
| Preis | ~4 € | ~4 € |
| WiFi | ❌ | ✅ eingebaut |
| Bluetooth | ❌ | ✅ eingebaut |
| CPU-Leistung | 16 MHz, 8-Bit | 240 MHz, 32-Bit (Dual-Core) |
| RAM | 2 KB | 520 KB |
| GPIO-Pins | 22 | 34 |
| 3,3V-tolerant | nein (5V) | ja (3,3V) → RA-02 direkt anschließbar |
| NTP-Zeitsync | ❌ | ✅ (ersetzt DS3231 bei WiFi-Betrieb) |
| Arduino IDE | ✅ | ✅ (Board-Package nötig) |

---

## 2. Entwicklungsumgebung: VS Code + PlatformIO

### Einmalige Installation

1. [VS Code](https://code.visualstudio.com/) installieren
2. Extension **PlatformIO IDE** installieren (Seitenleiste → Extensions → `PlatformIO IDE`)
3. VS Code neu starten — PlatformIO lädt automatisch alle Toolchains beim ersten Build

### Projekt öffnen

Jeden Sketch-Ordner (z.B. `esp32_lora_wifi_sender/`) direkt in VS Code öffnen — die `platformio.ini` ist bereits vorhanden und konfiguriert Board, Framework und alle Bibliotheken automatisch.

```
VS Code → Datei → Ordner öffnen → esp32_lora_wifi_sender/
```

### Kompilieren & Flashen

| Aktion | PlatformIO-Button | Tastenkürzel |
|--------|------------------|-------------|
| Kompilieren | ✓ (Häkchen) | `Ctrl+Alt+B` |
| Flashen | → (Pfeil) | `Ctrl+Alt+U` |
| Serieller Monitor | Stecker-Symbol | `Ctrl+Alt+S` |

Alle Buttons befinden sich in der **blauen Statusleiste** unten in VS Code.

### platformio.ini (bereits vorhanden, keine Änderung nötig)

ESP32-Beispiel:
```ini
[env:esp32dev]
platform     = espressif32
board        = esp32dev
framework    = arduino
monitor_speed = 115200
lib_deps =
    sandeepmistry/LoRa@^0.8.0
    adafruit/RTClib@^2.1.4
```

PlatformIO lädt alle `lib_deps` beim ersten Build automatisch herunter — kein manuelles Bibliotheken-Installieren nötig.

---

## 3. DIP-Schalter-Belegung

### TM1637 / MAX7219 (Standalone + WiFi)

| Schalter | OFF | ON |
|----------|-----|----|
| **SW1** | Standalone (nur Display) | WiFi-Modus (sendet an RaceControl) |
| **SW2** | Helligkeit niedrig (MAX7219) | Helligkeit hoch |
| SW3 | reserviert | reserviert |
| SW4 | reserviert | reserviert |

### LoRa/WiFi-Sender (Spur + Checkpoint)

| Schalter | OFF | ON |
|----------|-----|----|
| **SW1** | Spur A | Spur B |
| **SW2** | CP Bit 0 = 0 | CP Bit 0 = 1 |
| **SW3** | CP Bit 1 = 0 | CP Bit 1 = 1 |
| **SW4** | Auto (WiFi → LoRa) | Nur LoRa |

**Checkpoint-Tabelle (SW2 + SW3):**

| SW2 | SW3 | CP | Paket-Typ | Bedeutung |
|-----|-----|----|-----------|-----------|
| OFF | OFF | 0 | `start`  | Startlinie |
| ON  | OFF | 1 | `split`  | Zwischenzeit 1 |
| OFF | ON  | 2 | `split`  | Zwischenzeit 2 |
| ON  | ON  | 3 | `finish` | Ziellinie |

> DIP-Schalter werden **einmalig beim Einschalten** gelesen. Änderungen erst nach Neustart aktiv.

---

## 4. Pinbelegung

### TM1637-Variante

```
ESP32 DevKit
┌─────────────────────────────────────┐
│ GPIO4   ── LS Start  (INPUT_PULLUP) │
│ GPIO5   ── LS Ziel   (INPUT_PULLUP) │
│ GPIO15  ── Reset-Taster ── GND      │
│ GPIO18  ── TM1637 CLK               │
│ GPIO19  ── TM1637 DIO               │
│ GPIO32  ── SW1                      │
│ GPIO33  ── SW2                      │
│ GPIO25  ── SW3                      │
│ GPIO26  ── SW4                      │
│ GPIO2   ── Status-LED (built-in)    │
│ 3.3V    ── TM1637 VCC               │
│ GND     ── TM1637 GND               │
│ 5V      ── LS VCC (beide)           │
│ GND     ── LS GND (beide)           │
│ GND     ── DIP-Schalter (alle)      │
└─────────────────────────────────────┘
```

### MAX7219-Variante

```
ESP32 DevKit
┌─────────────────────────────────────┐
│ GPIO4   ── LS Start  (INPUT_PULLUP) │
│ GPIO15  ── LS Ziel   (INPUT_PULLUP) │
│ GPIO16  ── Reset-Taster ── GND      │
│ GPIO23  ── MAX7219 DIN (MOSI)       │
│ GPIO18  ── MAX7219 CLK (SCK)        │
│ GPIO5   ── MAX7219 CS  (LOAD)       │
│ GPIO32–26 ── DIP SW1–SW4            │
│ GPIO2   ── Status-LED               │
│ 3.3V    ── MAX7219 VCC               │  ⚠️ NICHT 5V — ESP32 Logik nur 3,3V!
│ 5V      ── LS VCC                   │
│ GND     ── MAX7219 GND + LS GND     │
└─────────────────────────────────────┘
```

### LoRa/WiFi-Sender (mit DS3231)

```
ESP32 DevKit
┌─────────────────────────────────────┐
│ GPIO4   ── Lichtschranke Signal     │
│ GPIO5   ── RA-02 NSS (CS)    SPI    │
│ GPIO14  ── RA-02 RST                │
│ GPIO2   ── RA-02 DIO0               │
│ GPIO18  ── RA-02 SCK         SPI    │
│ GPIO19  ── RA-02 MISO        SPI    │
│ GPIO23  ── RA-02 MOSI        SPI    │
│ GPIO21  ── DS3231 SDA        I²C    │
│ GPIO22  ── DS3231 SCL        I²C    │
│ GPIO32  ── SW1 (Spur)               │
│ GPIO33  ── SW2 (CP Bit 0)           │
│ GPIO25  ── SW3 (CP Bit 1)           │
│ GPIO26  ── SW4 (Force LoRa)         │
│ 3.3V    ── RA-02 VCC + DS3231 VCC   │  ⚠️ NICHT 5V an RA-02!
│ GND     ── RA-02 GND + DS3231 GND   │
│ 5V      ── Lichtschranke VCC        │
│ GND     ── Lichtschranke GND        │
└─────────────────────────────────────┘
```

> ⚠️ Der ESP32 arbeitet mit **3,3V-Logik** — RA-02 und DS3231 direkt anschließbar, **kein** Levelshifter nötig.

---

## 5. WiFi-Konfiguration im Sketch

In jedem Sketch oben anpassen:

```cpp
const char* WIFI_SSID  = "RaceControl";           // WLAN-Name des Hotspots / Routers
const char* WIFI_PASS  = "geheim";                // Passwort
const char* SERVER_URL = "http://192.168.1.100:1980";  // IP des RaceControl-Servers
const char* TIMING_KEY = "HIER_DEN_KEY_EINTRAGEN";    // Admin → System → API-Key
```

---

## 6. Zeitsynchronisation (LoRa/WiFi-Sender)

### Priorität der Zeitquellen

```
1. WiFi verfügbar → NTP (pool.ntp.org) → DS3231 wird gesetzt  ← beste Genauigkeit
2. WiFi nicht da  → LoRa Timesync vom Gateway → DS3231 wird gesetzt
3. Kein WiFi, kein Sync → unix=0 → Gateway verwendet Empfangszeitpunkt
```

### WiFi + NTP (Normalfall)
Der ESP32 verbindet sich beim Start mit dem WLAN und holt die Zeit von `pool.ntp.org`. Die DS3231 RTC wird automatisch gestellt. Danach liefert der DS3231 genaue Zeitstempel auch ohne WiFi.

### LoRa Fallback
Wenn kein WiFi: Der Gateway-Pi sendet alle 60 s einen Timesync-Broadcast (`lora_ziel_gateway.py`). ESP32 empfängt, stellt DS3231, bestätigt mit `timesync_ack`.

---

## 7. Kommunikationsablauf (LoRa/WiFi-Sender)

```
WiFi verfügbar:
  Lichtschranke → Interrupt → RTC auslesen → HTTP POST an RaceControl
                                                        ↑ direkt, kein Gateway nötig

WiFi nicht verfügbar (SW4=ON oder kein Netz):
  Lichtschranke → Interrupt → RTC auslesen → LoRa-Paket
                                                  → Gateway-Pi → HTTP POST
```

---

## 8. Benötigte Bibliotheken

Arduino IDE → **Bibliotheken verwalten**:

| Bibliothek | Autor | Für |
|-----------|-------|-----|
| TM1637Display | Avishay Orpaz | TM1637-Sketch |
| LedControl | Eberhard Fahle | MAX7219-Sketch |
| LoRa | Sandeep Mistry | LoRa-Sender |
| RTClib | Adafruit | DS3231 (LoRa-Sender) |
| WiFi, HTTPClient | ESP32 built-in | alle |

---

## 9. Einkaufsliste (LoRa/WiFi-Sender komplett)

| Artikel | ca. Preis |
|---------|-----------|
| ESP32 DevKit v1 (WROOM-32) | ~4 € |
| RA-02 LoRa-Modul SX1276 433 MHz | ~4 € |
| DS3231 RTC-Modul | ~2 € |
| 4-fach DIP-Schalter | ~1 € |
| IR-Lichtschranke E18-D80NK | ~3 € |
| 433 MHz Antenne SMA | ~2 € |
| Gehäuse IP65 | ~6 € |
| Powerbank 5.000 mAh | ~10 € |
| **Gesamt** | **~32 €** |

---

## 10. Troubleshooting

| Problem | Lösung |
|---------|--------|
| Kein Board in Arduino IDE | ESP32-Package installiert? Board = "ESP32 Dev Module" |
| WiFi verbindet nicht | SSID/Passwort prüfen; `WIFI_TIMEOUT_MS` erhöhen |
| NTP schlägt fehl | Internet-Zugang am WLAN-Router? Alternativ: lokalen NTP-Server angeben |
| RA-02 nicht gefunden | 3,3V-Pin verwenden; NSS/RST/DIO0-Pins prüfen |
| DS3231 nicht gefunden | SDA=GPIO21, SCL=GPIO22; Modul hat eigene Pullups |
| DIP-Einstellung ignoriert | Neustart nötig — werden nur in `setup()` gelesen |
| Lichtschranke prellt | `DEBOUNCE_MS` auf 500 erhöhen |
