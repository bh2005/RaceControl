# Bauanleitung: Arduino LoRa-Startlichtschranke (Sender)

**Autor:** BH2005 · MSC Braach e.V. im ADAC  
**Sketch:** `arduino_lora_sender/arduino_lora_sender.ino`  
**Verwendung:** Kabellose Starterfassung für Downhill / Seifenkiste per LoRa 433 MHz  
**Gegenstück:** `RaPi_lichtschranke/lora_ziel_gateway.py` läuft am Ziel-Pi

---

## 1. Konzept

```
[IR-Lichtschranke am Start]
        │ FALLING-Interrupt (D2)
[Arduino Nano]
[+ RA-02 LoRa SX1276, 433 MHz]
[+ DS3231 RTC]
        │ 433 MHz LoRa (bis ~1,5 km mit SF10)
        │ ← Zeitsync-Paket vom Gateway (alle 60 s)
[Raspberry Pi am Ziel]
[+ Waveshare LoRa HAT SX1268]
        │ lora_ziel_gateway.py
[RaceControl Server]
```

**Ablauf:**
1. Gateway sendet beim Start **Zeitsync** per LoRa: `{"type":"timesync","unix":1746612345}`
2. Arduino empfängt Sync, stellt DS3231 auf UTC, bestätigt per `timesync_ack`
3. Lichtschranke löst aus → Arduino liest RTC-Timestamp sofort aus
4. Arduino sendet: `{"type":"start","unix":1746612345,"ms":12345678,"lane":"A"}`
5. Gateway leitet an RaceControl-Backend weiter

> **Timing-Genauigkeit:** RTC-Timestamp wird beim Interrupt gestempelt (< 1 ms Verzögerung).  
> LoRa-Übertragungszeit (~300 ms) ist irrelevant, da der Zeitstempel bereits im Paket steckt.  
> Ohne DS3231 (Fallback): Gateway verwendet seinen eigenen Empfangszeitpunkt.

---

## 2. Benötigte Hardware

### Sender (Start-Seite)

| Artikel | Bezugsquelle | ca. Preis |
|---------|-------------|-----------|
| Arduino Nano (ATmega328P) | AliExpress / Reichelt | ~4 € |
| **RA-02 LoRa-Modul (SX1276, 433 MHz)** | AliExpress / Amazon | ~4 € |
| **DS3231 RTC-Modul (mit CR2032-Knopfzelle)** | AliExpress / Amazon | ~2 € |
| 433 MHz Stabantenne (SMA) | AliExpress | ~2 € |
| IR-Lichtschranken-Modul E18-D80NK | AliExpress | ~3 € |
| Breadboard + Jumper-Kabel | — | ~3 € |
| Gehäuse wetterfest IP65 | Baumarkt | ~6 € |
| Powerbank 5.000 mAh | — | ~10 € |
| **Gesamt Sender** | | **~34 €** |

### Empfänger (Ziel-Seite)
Siehe [RaPi_lichtschranke/BAUANLEITUNG_LoRa_Startlichtschranke.md](../../RaPi_lichtschranke/BAUANLEITUNG_LoRa_Startlichtschranke.md) — Waveshare HAT am Raspberry Pi (19,60 €).

---

## 3. Schaltplan / Pinbelegung

```
Arduino Nano
┌──────────────────────────────────────────┐
│ D2   ── Lichtschranke Signal (INT0)      │  INPUT_PULLUP, FALLING
│ D3   ── RA-02 DIO0 (IRQ)                │
│ D9   ── RA-02 RST                        │
│ D10  ── RA-02 NSS / CS                  │  SPI
│ D11  ── RA-02 MOSI                       │  SPI
│ D12  ── RA-02 MISO                       │  SPI
│ D13  ── RA-02 SCK                        │  SPI
│ A4   ── DS3231 SDA                       │  I²C
│ A5   ── DS3231 SCL                       │  I²C
│ 3.3V ── RA-02 VCC   ⚠️ NICHT 5V!        │
│ 3.3V ── DS3231 VCC  (oder 5V, beide OK) │
│ GND  ── RA-02 GND + DS3231 GND          │
│ 5V   ── Lichtschranke VCC               │
│ GND  ── Lichtschranke GND               │
└──────────────────────────────────────────┘
```

> ⚠️ **RA-02 arbeitet mit 3,3V** — niemals 5V anlegen, das zerstört das Modul.  
> ⚠️ **Antenne** immer vor dem Einschalten anschließen.  
> DS3231 akzeptiert 3,3V und 5V — beide funktionieren.

### DS3231-Modul Anschluss

| DS3231-Pin | Arduino Nano |
|------------|-------------|
| VCC        | 3.3V oder 5V |
| GND        | GND         |
| SDA        | A4          |
| SCL        | A5          |
| SQW        | nicht belegt |
| 32K        | nicht belegt |

---

## 4. Entwicklungsumgebung: VS Code + PlatformIO

1. VS Code + Extension **PlatformIO IDE** installieren
2. Ordner `arduino_lora_sender/` in VS Code öffnen
3. Die `platformio.ini` ist bereits vorhanden — alle Bibliotheken werden automatisch geladen

```ini
[env:nanoatmega328old]
platform  = atmelavr
board     = nanoatmega328old
framework = arduino
lib_deps  =
    sandeepmistry/LoRa@^0.8.0
    adafruit/RTClib@^2.1.4
```

| Bibliothek | Funktion |
|-----------|---------|
| **LoRa** (Sandeep Mistry) | LoRa-Kommunikation über RA-02 |
| **RTClib** (Adafruit) | DS3231 Echtzeituhr |

---

## 5. Zeitsynchronisation

### Ablauf

```
Gateway-Pi                          Arduino
    │                                   │
    │── {"type":"timesync",             │
    │    "unix":1746612345} ──────────►│
    │                                   │  DS3231 wird auf UTC gesetzt
    │◄─ {"type":"timesync_ack",         │
    │    "unix":1746612345} ────────────│
    │                                   │
    │    [Lichtschranke auslöst]        │
    │                                   │  RTC auslesen → unix=1746612401
    │◄─ {"type":"start",                │
    │    "unix":1746612401,             │
    │    "ms":54321,"lane":"A"} ────────│
    │                                   │
    │── HTTP POST /api/timing/start ──► RaceControl
```

- Das Gateway sendet **automatisch alle 60 Sekunden** einen Zeitsync
- Zusätzlich einmal sofort beim Gateway-Start (nach 2 s)
- Arduino bestätigt jeden Sync mit `timesync_ack`
- Bei der ersten erfolgreichen Synchronisation zeigt die serielle Ausgabe `[RTC] Zeit gesetzt: ...`

### Serielle Ausgabe Arduino (9600 Baud)

Beim Start ohne vorherige Sync (RTC hat Strom verloren):
```
[RTC]  Strom verloren – Zeit ungültig. Warte auf Zeitsync.
[LoRa] Init... OK
[CFG]  Spur: A
[CFG]  RTC: vorhanden  Sync: nein – warte auf Timesync-Paket
[OK]   Bereit.
```

Nach Empfang des Zeitsync vom Gateway:
```
[RECV] {"type":"timesync","unix":1746612345}
[RTC]  Zeit gesetzt: 1746612345
[SEND] {"type":"timesync_ack","unix":1746612345}
```

Beim Auslösen der Lichtschranke:
```
[SEND] {"type":"start","unix":1746612401,"ms":54321,"lane":"A"}
```

### Fallback ohne DS3231

Wenn kein DS3231 verbaut ist oder dieser fehlt, sendet der Arduino `"unix":0`. Das Gateway erkennt dies und verwendet **seinen eigenen Empfangszeitpunkt** als Timestamp. Genauigkeit dann: ±LoRa-Delay (~300 ms) — für die meisten Anwendungen ausreichend.

---

## 6. Sketch konfigurieren

In `arduino_lora_sender.ino` vor dem Hochladen anpassen:

```cpp
const char LANE[] = "A";   // "A" oder "B"

#define LORA_SF   10        // Spreading Factor (Reichweite vs. Geschwindigkeit)
#define LORA_POWER 17       // dBm — auf 10 reduzieren für EU-konforme 10 mW ERP
```

**Spreading Factor:**

| SF | Reichweite (Freifeld) | Paketdauer | Empfehlung |
|----|----------------------|------------|------------|
| 7  | ~500 m  | ~50 ms   | Kurzstrecke / Slalom |
| 9  | ~1 km   | ~150 ms  | Mittlere Distanz |
| 10 | ~1,5 km | ~300 ms  | Downhill Standard |
| 12 | ~3 km   | ~1,5 s   | Große Distanz |

---

## 7. Sketch hochladen

1. Arduino Nano per USB anschließen
2. Board: **Arduino Nano**, Prozessor: **ATmega328P (Old Bootloader)**
3. `arduino_lora_sender.ino` öffnen → **Hochladen**

---

## 8. Gateway starten (Ziel-Pi)

```bash
# Einmalig: Abhängigkeiten installieren
pip3 install pyserial requests

# Gateway starten
python3 lora_ziel_gateway.py
```

Ausgabe beim Start:
```
[OK]   LoRa-Gateway aktiv. UART=/dev/ttyAMA0, Server=http://localhost:1980
[SYNC] Zeitsync gesendet: unix=1746612345
[RECV] {"type":"timesync_ack","unix":1746612345}
[ACK]  Arduino hat Zeitsync bestätigt: unix=1746612345
```

---

## 9. Zwei-Spur-Betrieb (Spur A + B)

Zwei baugleiche Sender aufbauen — im Sketch jeweils `LANE = "A"` und `LANE = "B"`.
Der Zeitsync vom Gateway erreicht beide Sender gleichzeitig (Broadcast).

```
[Arduino Spur A, LANE="A"] ──┐
                               │ 433 MHz LoRa
[Arduino Spur B, LANE="B"] ──┤
                               │ ← Zeitsync (beide empfangen)
                     [Ziel-Pi Gateway]
```

---

## 10. Vergleich Arduino vs. Raspberry Pi (Sender)

| Kriterium | Arduino Nano + RA-02 + DS3231 | Raspberry Pi Zero 2W + HAT |
|-----------|-------------------------------|---------------------------|
| Kosten | ~10 € | ~38 € |
| Stromverbrauch | ~30 mA | ~150 mA |
| Akkulaufzeit (5.000 mAh) | ~160 h | ~33 h |
| Bootzeit | Sofort | ~25 s |
| Echtzeit-Uhr | DS3231 (±2 ppm) | Systemzeit (NTP) |
| Zeitsync | Per LoRa vom Gateway | — |
| **Empfehlung** | **✅ Sender am Start** | Gateway am Ziel |

---

## 11. EU-Frequenzregelung (433 MHz)

| Parameter | Wert |
|-----------|------|
| Frequenzband | 433,05–434,79 MHz |
| Max. ERP | 10 mW (10 dBm) — Sketch auf `LORA_POWER 10` setzen für Konformität |
| Duty Cycle | max. 10 % |
| 100 Starts + 60 Syncs/Tag bei SF10 | < 0,1 % Duty Cycle ✅ |

---

## 12. Troubleshooting

| Problem | Lösung |
|---------|--------|
| `LoRa init... FEHLER!` | RA-02 Verkabelung; **3,3V** statt 5V; NSS/RST/DIO0 korrekt? |
| `DS3231 nicht gefunden` | SDA=A4, SCL=A5; Modul hat eigene Pullups — kein externer Widerstand nötig |
| Kein Zeitsync empfangen | Gateway läuft? UART-Port korrekt? SF auf beiden Seiten gleich? |
| Lichtschranke prellt | `DEBOUNCE_MS` auf 500 erhöhen |
| `unix=0` im Paket | DS3231 nicht gefunden oder lostPower — Gateway übernimmt Timestamp |
| RTC verliert Zeit nach Stromverlust | CR2032-Knopfzelle leer — ersetzen (~0,50 €) |
