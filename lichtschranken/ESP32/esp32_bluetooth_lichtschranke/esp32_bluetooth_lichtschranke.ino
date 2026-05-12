/*
 * Bluetooth-Lichtschranke – ESP32 Classic BT (SPP)
 *
 * Szenario: Kein WLAN am Kurs – ESP32 verbindet sich direkt per Bluetooth
 * mit dem Laptop. Erscheint dort als /dev/rfcomm0 (Linux) bzw. COM-Port
 * (Windows). serial_logger.py läuft ohne Änderung.
 *
 * License: GNU General Public License v2
 * Author : BH2005 · MSC Braach e.V. im ADAC
 *
 * DIP-Schalter (4-fach):
 *   SW1  OFF=Spur A        ON=Spur B
 *   SW2  ┐ Checkpoint-Nummer (0–3)
 *   SW3  ┘   OFF/OFF=0  ON/OFF=1  OFF/ON=2  ON/ON=3
 *   SW4  (reserviert / nicht belegt)
 *
 * Checkpoint-Bedeutung:
 *   0 = Start           → type "start"
 *   1 = Zwischenzeit 1  → type "split"
 *   2 = Zwischenzeit 2  → type "split"
 *   3 = Ziel / Finish   → type "finish"
 *
 * Pinbelegung:
 *   GPIO4   – Lichtschranke (FALLING, INPUT_PULLUP)
 *   GPIO2   – Status-LED (onboard)
 *   GPIO32  – SW1 (Spur)
 *   GPIO33  – SW2 (CP Bit 0)
 *   GPIO25  – SW3 (CP Bit 1)
 *
 * Bluetooth-Name: "RC-BT-A-0" (Spur + Checkpoint aus DIP-Schaltern)
 *
 * Protokoll (identisch mit WiFi/LoRa-Sender):
 *   {"type":"start","unix":1746612401,"lane":"A","cp":0,"ms":12345}
 *   {"type":"split","unix":1746612445,"lane":"A","cp":1,"ms":56789}
 *   {"type":"finish","unix":1746612489,"lane":"B","cp":3,"ms":99001}
 *
 * Laptop-Setup (einmalig):
 *   bluetoothctl  →  pair / trust <MAC>
 *   sudo rfcomm bind 0 <MAC>
 *   python serial_logger.py /dev/rfcomm0
 */

#include <Arduino.h>
#include "BluetoothSerial.h"

// ── Pins ──────────────────────────────────────────────────────────────────────
#define PIN_LS    4
#define PIN_LED   2
#define PIN_SW1  32
#define PIN_SW2  33
#define PIN_SW3  25

#define DEBOUNCE_MS 200

// ── Globale Objekte ───────────────────────────────────────────────────────────
BluetoothSerial SerialBT;

// ── Konfiguration (wird in setup() aus DIP-Schaltern gelesen) ─────────────────
char        LANE[3]  = "A";
int         CP       = 0;
const char* PKT_TYPE = "start";
char        BT_NAME[16];

// ── Zustand ───────────────────────────────────────────────────────────────────
volatile bool     triggered    = false;
volatile uint32_t triggerMs    = 0;
uint32_t          lastTrigger  = 0;

bool btConnected = false;

// ── ISR ───────────────────────────────────────────────────────────────────────
void IRAM_ATTR onLichtschranke() {
  uint32_t now = millis();
  if (now - lastTrigger < DEBOUNCE_MS) return;
  lastTrigger = now;
  triggerMs   = now;
  triggered   = true;
}

// ── Bluetooth-Callbacks ───────────────────────────────────────────────────────
void onBtConnect(esp_spp_cb_event_t event, esp_spp_cb_param_t* param) {
  if (event == ESP_SPP_SRV_OPEN_EVT) {
    btConnected = true;
    digitalWrite(PIN_LED, HIGH);
    Serial.println(F("[BT]   Client verbunden"));
  } else if (event == ESP_SPP_CLOSE_EVT) {
    btConnected = false;
    digitalWrite(PIN_LED, LOW);
    Serial.println(F("[BT]   Client getrennt"));
  }
}

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);

  // DIP-Schalter lesen
  pinMode(PIN_SW1, INPUT_PULLUP);
  pinMode(PIN_SW2, INPUT_PULLUP);
  pinMode(PIN_SW3, INPUT_PULLUP);

  LANE[0] = (digitalRead(PIN_SW1) == LOW) ? 'B' : 'A';
  int cp0 = (digitalRead(PIN_SW2) == LOW) ? 1 : 0;
  int cp1 = (digitalRead(PIN_SW3) == LOW) ? 2 : 0;
  CP      = cp0 + cp1;

  if      (CP == 0) PKT_TYPE = "start";
  else if (CP == 3) PKT_TYPE = "finish";
  else              PKT_TYPE = "split";

  // BT-Name: z.B. "RC-BT-A-0" oder "RC-BT-B-3"
  snprintf(BT_NAME, sizeof(BT_NAME), "RC-BT-%s-%d", LANE, CP);

  Serial.printf("[CFG]  Spur=%s  CP=%d  Typ=%s  BT-Name=%s\n",
    LANE, CP, PKT_TYPE, BT_NAME);

  // Bluetooth starten
  SerialBT.register_callback(onBtConnect);
  if (!SerialBT.begin(BT_NAME)) {
    Serial.println(F("[BT]   Initialisierung fehlgeschlagen!"));
    // Endlos blinken als Fehlerindikator
    while (true) { digitalWrite(PIN_LED, !digitalRead(PIN_LED)); delay(200); }
  }
  Serial.printf("[BT]   Bereit – warte auf Verbindung mit \"%s\"\n", BT_NAME);

  // Lichtschranke
  pinMode(PIN_LS, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_LS), onLichtschranke, FALLING);

  // LED langsam blinken = wartet auf BT-Client
  Serial.println(F("[OK]   Bereit."));
}

// ── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
  // LED-Heartbeat: langsam = kein Client, schnell = verbunden + trigger
  static uint32_t lastBlink = 0;
  uint32_t blinkInterval = btConnected ? 1000 : 300;
  if (millis() - lastBlink > blinkInterval) {
    lastBlink = millis();
    digitalWrite(PIN_LED, !digitalRead(PIN_LED));
  }

  if (!triggered) return;
  triggered = false;

  uint32_t ms  = triggerMs;
  // unix-Näherung: ESP32-Uptime-Sekunden (kein RTC/NTP nötig)
  // → serial_logger.py nutzt für Zeitmessung ohnehin ms-Delta, nicht unix
  uint32_t sec = ms / 1000;

  char buf[128];
  snprintf(buf, sizeof(buf),
    "{\"type\":\"%s\",\"unix\":%lu,\"lane\":\"%s\",\"cp\":%d,\"ms\":%lu}",
    PKT_TYPE, (unsigned long)sec, LANE, CP, (unsigned long)ms);

  // Bluetooth senden (wenn Client verbunden)
  if (btConnected) {
    SerialBT.println(buf);
  } else {
    Serial.println(F("[WARN] Kein BT-Client – Ereignis lokal gespeichert"));
    // Ereignis nicht verwerfen: nochmals auf USB ausgeben für Debugging
  }

  // USB-Serial immer ausgeben (Debug / Fallback mit USB-Kabel)
  Serial.println(buf);

  // LED kurz aufblitzen als visuelles Feedback
  digitalWrite(PIN_LED, HIGH);
  delay(50);
  digitalWrite(PIN_LED, LOW);
}
