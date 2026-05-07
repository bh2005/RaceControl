/*
 * LoRa-Startlichtschranke – Sender mit DS3231 RTC + Zeitsynchronisation
 * Arduino Nano + RA-02 LoRa-Modul (SX1276/SX1278, 433 MHz) + DS3231 RTC
 *
 * License: GNU General Public License v2
 * Author : BH2005 · MSC Braach e.V. im ADAC
 * URL    : https://github.com/bh2005
 *
 * Bibliotheken (Arduino IDE → Bibliotheken verwalten):
 *   - "LoRa"   von Sandeep Mistry
 *   - "RTClib" von Adafruit
 *
 * Pinbelegung (Arduino Nano):
 *   D2  – Lichtschranke (Start-Trigger)  INT0     FALLING
 *   D9  – RA-02 RST
 *   D10 – RA-02 NSS (CS)                          SPI
 *   D11 – RA-02 MOSI                              SPI
 *   D12 – RA-02 MISO                              SPI
 *   D13 – RA-02 SCK                               SPI
 *   D3  – RA-02 DIO0 (IRQ)
 *   A4  – DS3231 SDA                              I2C
 *   A5  – DS3231 SCL                              I2C
 *
 * Protokoll:
 *   Senden  → {"type":"start","unix":1746612345,"ms":12345678,"lane":"A"}
 *   Empfang ← {"type":"timesync","unix":1746612345}
 */

#include <SPI.h>
#include <LoRa.h>
#include <Wire.h>
#include <RTClib.h>

// ── Konfiguration ─────────────────────────────────────────────────────────────
#define LORA_FREQ   433E6
#define LORA_SF     10       // Spreading Factor 10 (~1,5 km Reichweite)
#define LORA_BW     125E3
#define LORA_CR     5
#define LORA_POWER  17       // dBm Sendeleistung

const char LANE[] = "A";    // "A" oder "B" für Zwei-Spur-Betrieb

// ── Pins ──────────────────────────────────────────────────────────────────────
#define PIN_LS_START  2
#define PIN_LORA_NSS  10
#define PIN_LORA_RST  9
#define PIN_LORA_DIO0 3

#define DEBOUNCE_MS   200

// ── Hardware ──────────────────────────────────────────────────────────────────
RTC_DS3231 rtc;

// ── Zustand ───────────────────────────────────────────────────────────────────
volatile bool          getriggert   = false;
volatile unsigned long triggerMs    = 0;   // millis() beim Trigger (Fallback)
unsigned long          letzterTrigger = 0;

bool rtcOk       = false;   // DS3231 erfolgreich initialisiert
bool rtcSynced   = false;   // mindestens einmal per LoRa synchronisiert

// ── ISR: Lichtschranke ────────────────────────────────────────────────────────
void isrLichtschranke() {
  unsigned long jetzt = millis();
  if (jetzt - letzterTrigger < DEBOUNCE_MS) return;
  letzterTrigger = jetzt;
  triggerMs  = jetzt;
  getriggert = true;
}

// ── Hilfsfunktionen ───────────────────────────────────────────────────────────

// Liefert aktuellen Unix-Timestamp (0 wenn RTC nicht verfügbar)
uint32_t getUnixTime() {
  if (!rtcOk) return 0;
  DateTime now = rtc.now();
  return now.unixtime();
}

// Setzt RTC auf gegebenen Unix-Timestamp
void setRtcTime(uint32_t unix) {
  if (!rtcOk) return;
  DateTime dt(unix);
  rtc.adjust(dt);
  rtcSynced = true;
  Serial.print(F("[RTC]  Zeit gesetzt: "));
  Serial.println(unix);
}

// Sendet Start-Paket per LoRa
void sendeStart() {
  uint32_t unixTs = getUnixTime();
  unsigned long msTs = triggerMs;

  // JSON kompakt: {"type":"start","unix":1746612345,"ms":12345678,"lane":"A"}
  char buf[80];
  if (rtcOk) {
    snprintf(buf, sizeof(buf),
      "{\"type\":\"start\",\"unix\":%lu,\"ms\":%lu,\"lane\":\"%s\"}",
      (unsigned long)unixTs, msTs, LANE);
  } else {
    // Kein RTC: nur millis() — Gateway verwendet dann Empfangszeitpunkt
    snprintf(buf, sizeof(buf),
      "{\"type\":\"start\",\"unix\":0,\"ms\":%lu,\"lane\":\"%s\"}",
      msTs, LANE);
  }

  LoRa.beginPacket();
  LoRa.print(buf);
  LoRa.endPacket();

  Serial.print(F("[SEND] "));
  Serial.println(buf);
  Serial.println(buf);   // clean JSON für serial_logger.py
}

// Verarbeitet eingehende LoRa-Pakete (Zeitsync vom Gateway)
void empfangeLoRa() {
  int pktSize = LoRa.parsePacket();
  if (pktSize == 0) return;

  char buf[128];
  int  i = 0;
  while (LoRa.available() && i < (int)sizeof(buf) - 1) {
    buf[i++] = (char)LoRa.read();
  }
  buf[i] = '\0';

  Serial.print(F("[RECV] "));
  Serial.println(buf);

  // Einfaches Parsen: suche "unix": im String
  // Format erwartet: {"type":"timesync","unix":1746612345}
  char *p = strstr(buf, "\"unix\":");
  if (p) {
    uint32_t unix = (uint32_t)atol(p + 7);
    if (unix > 1700000000UL) {   // Plausibilitätsprüfung (> Jan 2024)
      setRtcTime(unix);
      // Bestätigung zurücksenden
      char ack[48];
      snprintf(ack, sizeof(ack),
        "{\"type\":\"timesync_ack\",\"unix\":%lu}", (unsigned long)unix);
      LoRa.beginPacket();
      LoRa.print(ack);
      LoRa.endPacket();
      Serial.print(F("[SEND] "));
      Serial.println(ack);
    }
  }
}

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(9600);
  while (!Serial);

  // DS3231 initialisieren
  Wire.begin();
  if (rtc.begin()) {
    rtcOk = true;
    if (rtc.lostPower()) {
      Serial.println(F("[RTC]  Strom verloren – Zeit ungültig. Warte auf Zeitsync."));
    } else {
      DateTime now = rtc.now();
      Serial.print(F("[RTC]  Zeit OK: "));
      Serial.println(now.unixtime());
      rtcSynced = true;
    }
  } else {
    Serial.println(F("[RTC]  DS3231 nicht gefunden! Nur millis()-Fallback."));
  }

  // LoRa initialisieren
  LoRa.setPins(PIN_LORA_NSS, PIN_LORA_RST, PIN_LORA_DIO0);
  Serial.print(F("[LoRa] Init... "));
  if (!LoRa.begin(LORA_FREQ)) {
    Serial.println(F("FEHLER! RA-02 nicht gefunden."));
    while (true);
  }
  LoRa.setSpreadingFactor(LORA_SF);
  LoRa.setSignalBandwidth(LORA_BW);
  LoRa.setCodingRate4(LORA_CR);
  LoRa.setTxPower(LORA_POWER);
  Serial.println(F("OK"));

  // Lichtschranke
  pinMode(PIN_LS_START, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_LS_START), isrLichtschranke, FALLING);

  Serial.print(F("[CFG]  Spur: "));
  Serial.println(LANE);
  Serial.print(F("[CFG]  RTC: "));
  Serial.print(rtcOk ? F("vorhanden") : F("fehlt"));
  Serial.print(F("  Sync: "));
  Serial.println(rtcSynced ? F("ja") : F("nein – warte auf Timesync-Paket"));
  Serial.println(F("[OK]   Bereit."));
}

// ── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
  // Eingehende LoRa-Pakete prüfen (Zeitsync)
  empfangeLoRa();

  // Lichtschranke ausgelöst
  if (getriggert) {
    getriggert = false;
    sendeStart();
  }
}
