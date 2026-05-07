# Bauanleitung: Arduino-Lichtschranke mit MAX7219-Display

**Autor:** BH2005 · MSC Braach e.V. im ADAC  
**Sketch:** `arduino_MAX7219_lichtschranke/arduino_MAX7219_lichtschranke.ino`  
**Verwendung:** Standalone-Zeitmessung mit 8-stelligem Display — zeigt laufende Zeit während der Fahrt

---

## 1. Konzept

Wie die TM1637-Variante, aber mit einem **MAX7219 8-stelligen 7-Segment-Display**. Vorteil: Das Display zeigt während der Messung die **laufende Zeit live** an (Stoppuhr-Modus). Format `MM:SS.hh` auf 8 Stellen — gut lesbar auf Distanz.

```
[LS Start] → INT0 (D2) ─┐
                          ├─ Arduino Nano ─── MAX7219 (8-Digit)
[LS Ziel ] → INT1 (D3) ─┘
[Reset-Btn] → D5
```

---

## 2. Benötigte Hardware

| Artikel | Bezugsquelle | ca. Preis |
|---------|-------------|-----------|
| Arduino Nano (ATmega328P) | AliExpress / Reichelt | ~4 € |
| MAX7219 8-Digit 7-Segment-Modul | AliExpress / Amazon | ~3 € |
| IR-Lichtschranken-Modul E18-D80NK (2×) | AliExpress / Amazon | ~5 € |
| Taster (Reset) | Reichelt | ~0,30 € |
| Breadboard + Jumper-Kabel | — | ~3 € |
| **Gesamt** | | **~15 €** |

---

## 3. Schaltplan / Pinbelegung

```
Arduino Nano
┌──────────────────────────────────┐
│ D2  ── LS Start (Signal)         │  INPUT_PULLUP, INT0
│ D3  ── LS Ziel  (Signal)         │  INPUT_PULLUP, INT1
│ D5  ── Reset-Taster ── GND       │  INPUT_PULLUP
│ D10 ── MAX7219 CS  (LOAD)        │  SPI
│ D11 ── MAX7219 DIN (MOSI)        │  SPI
│ D13 ── MAX7219 CLK (SCK)         │  SPI
│ 5V  ── MAX7219 VCC               │
│ GND ── MAX7219 GND               │
│ 5V  ── LS VCC (beide)            │
│ GND ── LS GND (beide)            │
└──────────────────────────────────┘
```

### MAX7219-Modul Anschluss

| MAX7219-Pin | Arduino Nano |
|-------------|-------------|
| VCC         | 5V          |
| GND         | GND         |
| DIN         | D11 (MOSI)  |
| CS          | D10         |
| CLK         | D13 (SCK)   |

> Bei mehreren verketteten Modulen: DOUT des ersten Moduls → DIN des zweiten. `MAX_DEVICES` im Sketch anpassen.

---

## 4. Entwicklungsumgebung: VS Code + PlatformIO

1. VS Code + Extension **PlatformIO IDE** installieren
2. Ordner `arduino_MAX7219_lichtschranke/` in VS Code öffnen
3. Die `platformio.ini` ist bereits vorhanden — LedControl-Bibliothek wird automatisch geladen

```ini
[env:nanoatmega328old]
platform  = atmelavr
board     = nanoatmega328old
framework = arduino
lib_deps  = wayoda/LedControl@^1.0.6
```

## 5. Sketch hochladen

1. Arduino Nano per USB anschließen
2. Ordner in VS Code öffnen
3. PlatformIO-Statusleiste: **→ Upload** (`Ctrl+Alt+U`)
4. Serieller Monitor: **Stecker-Symbol** (9600 Baud)

---

## 6. Display-Format

Das 8-stellige Display zeigt:

| Situation | Anzeige (Beispiel) |
|-----------|--------------------|
| Wartet    | `--------` (Striche) |
| Messung läuft (live) | `00:04.23` (läuft mit) |
| Ergebnis  | `01:23.45` (eingefroren) |

Format: **`MM:SS.hh`** — Minuten : Sekunden . Hundertstel

---

## 7. Helligkeit anpassen

Im Sketch `setup()`:
```cpp
lc.setIntensity(0, 4);  // 0 = dunkel, 15 = max. hell
```

---

## 8. Vorteil gegenüber TM1637

Das MAX7219-Display zeigt die Zeit **während der Fahrt live** mit 50ms-Aktualisierung. Damit können Zuschauer die laufende Zeit mitverfolgen. Die TM1637-Variante blinkt nur während der Messung.
