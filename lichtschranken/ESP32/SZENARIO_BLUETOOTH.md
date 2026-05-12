# ESP32 Lichtschranke – Bluetooth SPP (kein WLAN nötig)

**Szenario:** Kein WLAN-Netz am Kurs vorhanden, 1–2 Schranken in Reichweite des Laptops.  
Der ESP32 verbindet sich direkt per **Classic Bluetooth (SPP)** mit dem Laptop — kein Router, kein Access Point.

---

## Architektur

```
[ Lichtschranke ]
       │ GPIO4 (FALLING)
  ┌────▼────┐
  │  ESP32  │  ──── Bluetooth SPP ────▶  [ Laptop ]
  │         │                            serial_logger.py
  │ millis()│                            /dev/rfcomm0
  └─────────┘
```

- Der ESP32 erzeugt den Zeitstempel **lokal** per `millis()` im Moment des Lichtschrankendurchgangs
- Bluetooth überträgt nur das fertige JSON-Ergebnis → Übertragungslatenz irrelevant
- Auf dem Laptop erscheint der ESP32 als virtueller COM-Port (`/dev/rfcomm0`)
- `serial_logger.py` läuft **ohne Änderung** weiter

---

## Vergleich zu den bestehenden Varianten

| Merkmal              | WiFi (bestehend)         | Bluetooth SPP (dieses Szenario) |
|----------------------|--------------------------|----------------------------------|
| Router / AP nötig    | ja                       | **nein**                         |
| Reichweite           | 50–100 m                 | 10–30 m                          |
| Latenz (Übertragung) | 5–20 ms                  | 20–80 ms                         |
| Zeitgenauigkeit      | ESP32 stempelt selbst    | ESP32 stempelt selbst            |
| Mehrere Schranken    | unbegrenzt               | 1–7 gleichzeitig (BT-Limit)      |
| Verkabelung          | nur Stromversorgung      | nur Stromversorgung              |
| Laptop-Setup         | nichts                   | einmalig `rfcomm bind`           |

---

## ESP32-Firmware (Arduino / PlatformIO)

Neue Datei: `esp32_bluetooth_lichtschranke/esp32_bluetooth_lichtschranke.ino`

```cpp
#include <Arduino.h>
#include "BluetoothSerial.h"

// ── Konfiguration ─────────────────────────────────────────────────────────
#define PIN_LICHTSCHRANKE  4      // GPIO mit FALLING-Edge (INPUT_PULLUP)
#define DEVICE_NAME        "RaceControl-BT-A"   // sichtbarer BT-Name
#define LANE               "A"    // Spur: A oder B
#define CHECKPOINT         0      // 0=Start, 1=Split1, 2=Split2, 3=Finish

// ── Globale Objekte ───────────────────────────────────────────────────────
BluetoothSerial SerialBT;

volatile bool triggered = false;
volatile uint32_t triggerMs = 0;

// ── ISR ──────────────────────────────────────────────────────────────────
void IRAM_ATTR onLichtschranke() {
  if (!triggered) {
    triggerMs = millis();
    triggered = true;
  }
}

// ── Setup ─────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  SerialBT.begin(DEVICE_NAME);

  pinMode(PIN_LICHTSCHRANKE, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_LICHTSCHRANKE),
                  onLichtschranke, FALLING);

  Serial.println("Bluetooth gestartet: " DEVICE_NAME);
}

// ── Loop ──────────────────────────────────────────────────────────────────
void loop() {
  if (triggered) {
    uint32_t ms = triggerMs;
    triggered = false;

    // Checkpoint-Typ bestimmen
    const char* type =
      (CHECKPOINT == 0) ? "start" :
      (CHECKPOINT == 3) ? "finish" : "split";

    // JSON senden (gleiche Struktur wie WiFi-Sender)
    char buf[128];
    snprintf(buf, sizeof(buf),
      "{\"type\":\"%s\",\"unix\":%lu,\"lane\":\"%s\",\"cp\":%d,\"ms\":%lu}",
      type, (unsigned long)(ms / 1000), LANE, CHECKPOINT, (unsigned long)ms
    );

    SerialBT.println(buf);
    Serial.println(buf);   // USB-Debug parallel
  }
}
```

### platformio.ini

```ini
[env:esp32dev]
platform  = espressif32
board     = esp32dev
framework = arduino
lib_deps  =
    ; BluetoothSerial ist Teil des ESP32 Arduino Core – keine extra Lib nötig
monitor_speed = 115200
```

---

## Laptop-Setup (einmalig, Linux)

### 1. Bluetooth-MAC des ESP32 herausfinden

```sh
# Bluetooth einschalten und scannen
bluetoothctl
  power on
  scan on
  # warten bis "RaceControl-BT-A" erscheint → MAC notieren
  scan off
  exit
```

### 2. Pairen und virtuellen COM-Port binden

```sh
# Pairen (PIN ist meist leer, einfach bestätigen)
bluetoothctl
  pair AA:BB:CC:DD:EE:FF
  trust AA:BB:CC:DD:EE:FF
  exit

# rfcomm-Gerät anlegen
sudo rfcomm bind 0 AA:BB:CC:DD:EE:FF
# → erzeugt /dev/rfcomm0
```

### 3. serial_logger.py starten

```sh
python lichtschranken/serial_logger.py /dev/rfcomm0
```

Kein weiterer Code-Änderung nötig — der Logger sieht `/dev/rfcomm0` wie einen normalen USB-Serial-Port.

---

## Persistenz: rfcomm automatisch binden (systemd)

Damit `/dev/rfcomm0` nach jedem Neustart automatisch verfügbar ist:

```sh
sudo nano /etc/systemd/system/rfcomm-lichtschranke.service
```

```ini
[Unit]
Description=rfcomm bind RaceControl-BT-A
After=bluetooth.target

[Service]
Type=oneshot
ExecStart=/usr/bin/rfcomm bind 0 AA:BB:CC:DD:EE:FF
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

```sh
sudo systemctl daemon-reload
sudo systemctl enable rfcomm-lichtschranke.service
```

---

## Mehrere Schranken gleichzeitig

Jede Schranke bekommt einen eigenen `DEVICE_NAME` und eine eigene `rfcomm`-Nummer:

| Schranke        | BT-Name              | rfcomm | Port          |
|-----------------|----------------------|--------|---------------|
| Start (Spur A)  | RaceControl-BT-A     | 0      | /dev/rfcomm0  |
| Ziel  (Spur A)  | RaceControl-BT-A-F   | 1      | /dev/rfcomm1  |
| Start (Spur B)  | RaceControl-BT-B     | 2      | /dev/rfcomm2  |

`serial_logger.py` mehrfach starten, jeweils mit eigenem Port.

---

## Wann lieber WiFi verwenden

- Mehr als 2 Schranken gleichzeitig mit zentraler Zeitmessung
- Distanz > 30 m zwischen Schranke und Laptop
- Strecke mit vorhandenem WLAN (OpenWrt-Router bereits aufgebaut)
- Absolute Zeitsynchronisation über NTP nötig (WiFi + DS3231)
