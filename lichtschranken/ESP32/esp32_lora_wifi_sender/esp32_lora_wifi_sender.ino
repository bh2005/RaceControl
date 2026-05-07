/*
 * LoRa-Startlichtschranke – ESP32 mit WiFi (primär) + LoRa (Fallback)
 * DS3231 RTC + DIP-Schalter für Spur / Checkpoint
 *
 * License: GNU General Public License v2
 * Author : BH2005 · MSC Braach e.V. im ADAC
 *
 * Bibliotheken:
 *   - LoRa    (Sandeep Mistry)
 *   - RTClib  (Adafruit)
 *   - WiFi, HTTPClient, time (ESP32 built-in)
 *
 * DIP-Schalter (4-fach):
 *   SW1  OFF=Spur A        ON=Spur B
 *   SW2  ┐ Checkpoint-Nummer (0–3)
 *   SW3  ┘   OFF/OFF=0  ON/OFF=1  OFF/ON=2  ON/ON=3
 *   SW4  OFF=Auto        ON=Nur LoRa (kein WiFi)
 *
 * Checkpoint-Bedeutung:
 *   0 = Start           → type "start"
 *   1 = Zwischenzeit 1  → type "split"
 *   2 = Zwischenzeit 2  → type "split"
 *   3 = Ziel / Finish   → type "finish"
 *
 * Pinbelegung:
 *   GPIO4   – Lichtschranke (FALLING, INPUT_PULLUP)
 *   GPIO18  – LoRa SCK   (SPI VSPI)
 *   GPIO19  – LoRa MISO  (SPI VSPI)
 *   GPIO23  – LoRa MOSI  (SPI VSPI)
 *   GPIO5   – LoRa NSS
 *   GPIO14  – LoRa RST
 *   GPIO2   – LoRa DIO0  / Status-LED
 *   GPIO21  – DS3231 SDA (I²C)
 *   GPIO22  – DS3231 SCL (I²C)
 *   GPIO32  – SW1 (Spur)
 *   GPIO33  – SW2 (CP Bit 0)
 *   GPIO25  – SW3 (CP Bit 1)
 *   GPIO26  – SW4 (Force LoRa)
 *
 * Protokoll (WiFi / LoRa identisch):
 *   {"type":"start","unix":1746612401,"lane":"A","cp":0}
 *   {"type":"split","unix":1746612445,"lane":"A","cp":1}
 *   {"type":"finish","unix":1746612489,"lane":"A","cp":3}
 */

#include <SPI.h>
#include <LoRa.h>
#include <Wire.h>
#include <RTClib.h>
#include <WiFi.h>
#include <HTTPClient.h>

// ── WiFi / Server Konfiguration ───────────────────────────────────────────────
const char* WIFI_SSID  = "RaceControl";
const char* WIFI_PASS  = "geheim";
const char* SERVER_URL = "http://192.168.1.100:1980";
const char* TIMING_KEY = "HIER_DEN_KEY_EINTRAGEN";

// ── LoRa Konfiguration ────────────────────────────────────────────────────────
#define LORA_FREQ   433E6
#define LORA_SF     10
#define LORA_BW     125E3
#define LORA_CR     5
#define LORA_POWER  17

// ── Pins ──────────────────────────────────────────────────────────────────────
#define PIN_LS      4
#define PIN_LORA_NSS  5
#define PIN_LORA_RST  14
#define PIN_LORA_DIO0 2
#define PIN_SW1     32
#define PIN_SW2     33
#define PIN_SW3     25
#define PIN_SW4     26

#define DEBOUNCE_MS 200
#define WIFI_TIMEOUT_MS 8000   // max. Wartezeit für WiFi-Reconnect

// ── Hardware ──────────────────────────────────────────────────────────────────
RTC_DS3231 rtc;

// ── Konfiguration (aus DIP-Schaltern) ────────────────────────────────────────
char        LANE[2]    = "A";
int         CP         = 0;
bool        FORCE_LORA = false;
const char* PKT_TYPE   = "start";

// ── Zustand ───────────────────────────────────────────────────────────────────
volatile bool          getriggert    = false;
volatile unsigned long triggerMs     = 0;
unsigned long          letzterTrigger = 0;

bool rtcOk     = false;
bool rtcSynced = false;
bool loraOk    = false;

// ── ISR ───────────────────────────────────────────────────────────────────────
void IRAM_ATTR isrLichtschranke() {
  unsigned long jetzt = millis();
  if (jetzt - letzterTrigger < DEBOUNCE_MS) return;
  letzterTrigger = jetzt;
  triggerMs  = jetzt;
  getriggert = true;
}

// ── Zeithilfen ────────────────────────────────────────────────────────────────
uint32_t getUnixTime() {
  if (rtcOk) return rtc.now().unixtime();
  // Fallback: ESP32 Systemzeit (nach NTP-Sync gültig)
  return (uint32_t)(esp_timer_get_time() / 1000000ULL + 1700000000UL);
}

void setRtcVonNTP() {
  struct tm ti;
  if (!getLocalTime(&ti, 2000)) return;
  time_t t = mktime(&ti);
  if (rtcOk) { rtc.adjust(DateTime((uint32_t)t)); rtcSynced = true; }
  Serial.printf("[NTP]  Sync OK: %lu\n", (unsigned long)t);
}

void setRtcVonLoRa(uint32_t unix) {
  if (rtcOk) { rtc.adjust(DateTime(unix)); rtcSynced = true; }
  Serial.printf("[SYNC] LoRa-Zeit gesetzt: %lu\n", (unsigned long)unix);
}

// ── WiFi ──────────────────────────────────────────────────────────────────────
bool verbindeWiFi() {
  if (WiFi.status() == WL_CONNECTED) return true;
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < WIFI_TIMEOUT_MS) delay(200);
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print(F("[WiFi] OK: ")); Serial.println(WiFi.localIP());
    configTime(0, 0, "pool.ntp.org", "time.nist.gov");
    delay(1000);
    setRtcVonNTP();
    return true;
  }
  Serial.println(F("[WiFi] Nicht erreichbar → LoRa-Fallback"));
  return false;
}

// ── Senden per WiFi ───────────────────────────────────────────────────────────
bool sendeWiFi(uint32_t unix) {
  char body[100];
  snprintf(body, sizeof(body),
    "{\"type\":\"%s\",\"unix\":%lu,\"lane\":\"%s\",\"cp\":%d}",
    PKT_TYPE, (unsigned long)unix, LANE, CP);

  HTTPClient http;
  http.begin(String(SERVER_URL) + "/api/timing/trigger");
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Timing-Key", TIMING_KEY);
  int code = http.POST(body);
  http.end();
  Serial.printf("[HTTP] %d %s\n", code, body);
  Serial.println(body);   // clean JSON für serial_logger.py
  return (code >= 200 && code < 300);
}

// ── Senden per LoRa ───────────────────────────────────────────────────────────
void sendeLoRa(uint32_t unix) {
  if (!loraOk) return;
  char buf[100];
  snprintf(buf, sizeof(buf),
    "{\"type\":\"%s\",\"unix\":%lu,\"lane\":\"%s\",\"cp\":%d}",
    PKT_TYPE, (unsigned long)unix, LANE, CP);
  LoRa.beginPacket();
  LoRa.print(buf);
  LoRa.endPacket();
  Serial.printf("[LoRa] %s\n", buf);
  Serial.println(buf);   // clean JSON für serial_logger.py
}

// ── Eingehende LoRa-Pakete (Zeitsync) ────────────────────────────────────────
void empfangeLoRa() {
  if (!loraOk) return;
  int pktSize = LoRa.parsePacket();
  if (!pktSize) return;

  char buf[128]; int i = 0;
  while (LoRa.available() && i < (int)sizeof(buf) - 1) buf[i++] = (char)LoRa.read();
  buf[i] = '\0';
  Serial.printf("[RECV] %s\n", buf);

  char* p = strstr(buf, "\"unix\":");
  if (p && strstr(buf, "timesync")) {
    uint32_t unix = (uint32_t)atol(p + 7);
    if (unix > 1700000000UL) {
      setRtcVonLoRa(unix);
      char ack[64];
      snprintf(ack, sizeof(ack),
        "{\"type\":\"timesync_ack\",\"unix\":%lu}", (unsigned long)unix);
      LoRa.beginPacket(); LoRa.print(ack); LoRa.endPacket();
    }
  }
}

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);

  // DIP-Schalter lesen
  pinMode(PIN_SW1, INPUT_PULLUP); pinMode(PIN_SW2, INPUT_PULLUP);
  pinMode(PIN_SW3, INPUT_PULLUP); pinMode(PIN_SW4, INPUT_PULLUP);

  LANE[0]    = (digitalRead(PIN_SW1) == LOW) ? 'B' : 'A';
  int cp_b0  = (digitalRead(PIN_SW2) == LOW) ? 1 : 0;
  int cp_b1  = (digitalRead(PIN_SW3) == LOW) ? 2 : 0;
  CP         = cp_b0 + cp_b1;
  FORCE_LORA = (digitalRead(PIN_SW4) == LOW);

  if      (CP == 0) PKT_TYPE = "start";
  else if (CP == 3) PKT_TYPE = "finish";
  else              PKT_TYPE = "split";

  Serial.printf("[CFG]  Spur=%s  CP=%d  Typ=%s  LoRa-only=%s\n",
    LANE, CP, PKT_TYPE, FORCE_LORA ? "ja" : "nein");

  // DS3231
  Wire.begin();
  rtcOk = rtc.begin();
  if (rtcOk) {
    if (rtc.lostPower()) Serial.println(F("[RTC]  lostPower – warte auf Sync"));
    else { Serial.printf("[RTC]  OK: %lu\n", (unsigned long)rtc.now().unixtime()); rtcSynced = true; }
  } else {
    Serial.println(F("[RTC]  DS3231 nicht gefunden"));
  }

  // LoRa
  LoRa.setPins(PIN_LORA_NSS, PIN_LORA_RST, PIN_LORA_DIO0);
  if (LoRa.begin(LORA_FREQ)) {
    LoRa.setSpreadingFactor(LORA_SF);
    LoRa.setSignalBandwidth(LORA_BW);
    LoRa.setCodingRate4(LORA_CR);
    LoRa.setTxPower(LORA_POWER);
    loraOk = true;
    Serial.println(F("[LoRa] OK"));
  } else {
    Serial.println(F("[LoRa] Modul nicht gefunden"));
  }

  // WiFi (wenn nicht Force-LoRa)
  if (!FORCE_LORA) verbindeWiFi();

  // Lichtschranke
  pinMode(PIN_LS, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_LS), isrLichtschranke, FALLING);

  Serial.println(F("[OK]   Bereit."));
}

// ── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
  empfangeLoRa();

  if (getriggert) {
    getriggert = false;
    uint32_t unix = getUnixTime();

    bool gesendet = false;

    // Primär: WiFi (wenn nicht Force-LoRa)
    if (!FORCE_LORA) {
      if (WiFi.status() == WL_CONNECTED || verbindeWiFi()) {
        gesendet = sendeWiFi(unix);
      }
    }

    // Fallback: LoRa
    if (!gesendet) sendeLoRa(unix);
  }
}
