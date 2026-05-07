# Bauanleitung: Arduino-Lichtschranke mit TM1637-Display

**Autor:** BH2005 · MSC Braach e.V. im ADAC  
**Sketch:** `arduino_TM1637_lichtschranke/arduino_TM1637_lichtschranke.ino`  
**Verwendung:** Standalone-Zeitmessung (Start + Ziel), Anzeige auf 4-stelligem 7-Segment-Display

---

## 1. Konzept

Zwei IR-Lichtschranken messen die Zeit zwischen Start und Ziel. Das Ergebnis wird auf einem günstigen TM1637-Display angezeigt und zusätzlich per USB-Serial ausgegeben. Kein WLAN, kein Server nötig — komplett autark.

```
[LS Start] → INT0 (D2) ─┐
                          ├─ Arduino Nano ─── TM1637-Display
[LS Ziel ] → INT1 (D3) ─┘
[Reset-Btn] → D5
```

---

## 2. Benötigte Hardware

| Artikel | Bezugsquelle | ca. Preis |
|---------|-------------|-----------|
| Arduino Nano (ATmega328P) | AliExpress / Reichelt | ~4 € |
| TM1637 4-Digit 7-Segment-Display | AliExpress / Amazon | ~2 € |
| IR-Lichtschranken-Modul E18-D80NK (2×) | AliExpress / Amazon | ~5 € |
| Taster (Reset) | Reichelt | ~0,30 € |
| Breadboard + Jumper-Kabel | — | ~3 € |
| USB-Kabel (Typ A auf Mini-B) | — | ~2 € |
| Powerbank (optional, für mobilen Betrieb) | — | ~10 € |
| **Gesamt** | | **~26 €** |

---

## 3. Schaltplan / Pinbelegung

```
Arduino Nano
┌─────────────────────┐
│ D2  ── LS Start (Signal-Ausgang)   │  INPUT_PULLUP, INT0
│ D3  ── LS Ziel  (Signal-Ausgang)   │  INPUT_PULLUP, INT1
│ D5  ── Reset-Taster ── GND         │  INPUT_PULLUP
│ D6  ── TM1637 CLK                  │
│ D7  ── TM1637 DIO                  │
│ 5V  ── LS Start VCC + LS Ziel VCC  │
│ 5V  ── TM1637 VCC                  │
│ GND ── LS Start GND + LS Ziel GND  │
│ GND ── TM1637 GND                  │
│ GND ── Reset-Taster (anderes Ende) │
└─────────────────────┘
```

### Lichtschranke E18-D80NK Anschluss

| Kabel (E18-D80NK) | Arduino |
|-------------------|---------|
| Braun (VCC)       | 5V      |
| Blau  (GND)       | GND     |
| Schwarz (Signal)  | D2 / D3 |

> Der Sensor zieht den Ausgang auf LOW wenn der Strahl unterbrochen ist → `FALLING`-Interrupt.

---

## 4. Entwicklungsumgebung: VS Code + PlatformIO

1. VS Code + Extension **PlatformIO IDE** installieren
2. Ordner `arduino_TM1637_lichtschranke/` in VS Code öffnen
3. Die `platformio.ini` ist bereits vorhanden — PlatformIO lädt die TM1637-Bibliothek beim ersten Build automatisch

```ini
[env:nanoatmega328old]
platform  = atmelavr
board     = nanoatmega328old   ; für China-Nanos mit Old Bootloader
framework = arduino
lib_deps  = avishay/TM1637@^1.2.0
```

## 5. Sketch hochladen

1. Arduino Nano per USB anschließen
2. Ordner in VS Code öffnen
3. PlatformIO-Statusleiste unten: **→ Upload** (oder `Ctrl+Alt+U`)
4. Serieller Monitor: **Stecker-Symbol** (9600 Baud)

---

## 6. Display-Format

| Situation | Anzeige |
|-----------|---------|
| Wartet | `----` |
| Messung läuft | blinkt `8888` |
| Zeit < 100 s | `SS.hh` (Sekunden.Hundertstel) |
| Zeit ≥ 100 s | `MM:SS` (Minuten:Sekunden) |

**Serielle Ausgabe** (9600 Baud):
```
Lichtschranke bereit.
Zeit: 01:23.45
```

---

## 7. Mindestzeit / Fehlmessungen

Auslösungen kürzer als **3 Sekunden** werden ignoriert (Einstellung: `MIN_ZEIT_MS` im Sketch). Für Slalom ggf. auf `500` reduzieren.

---

## 8. Gehäuse-Tipp

Ein wasserdichtes ABS-Gehäuse (IP65, z.B. 120×80×55 mm, ~4 € Baumarkt) schützt das Arduino bei Outdooreinsatz. Display durch Frontplatte mit ausgefrästem Fenster. Powerbank intern für 6–10 h Betriebsdauer.
