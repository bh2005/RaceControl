/*
 * Lichtschranken-Zeitmessung mit MAX7219 + WiFi
 * ESP32 (z.B. ESP32 DevKit v1 / WROOM-32)
 *
 * License: GNU General Public License v2
 * Author : BH2005 · MSC Braach e.V. im ADAC
 *
 * Bibliotheken:
 *   - LedControl     (Eberhard Fahle)
 *   - WiFi, HTTPClient (ESP32 built-in)
 *
 * DIP-Schalter (4-fach):
 *   SW1 OFF=Standalone  ON=WiFi-Modus (sendet Ergebnis an RaceControl)
 *   SW2 OFF=Helligkeit niedrig  ON=Helligkeit hoch
 *   SW3 reserviert
 *   SW4 reserviert
 *
 * Pinbelegung:
 *   GPIO4   – Lichtschranke Start   (FALLING, INPUT_PULLUP)
 *   GPIO15  – Lichtschranke Ziel    (FALLING, INPUT_PULLUP)
 *   GPIO16  – Reset-Taster          (INPUT_PULLUP)
 *   GPIO23  – MAX7219 DIN (MOSI)
 *   GPIO18  – MAX7219 CLK (SCK)
 *   GPIO5   – MAX7219 CS  (LOAD)
 *   GPIO32  – SW1  (INPUT_PULLUP)
 *   GPIO33  – SW2  (INPUT_PULLUP)
 *   GPIO25  – SW3  (INPUT_PULLUP)
 *   GPIO26  – SW4  (INPUT_PULLUP)
 *   GPIO2   – Status-LED
 */

#include <LedControl.h>
#include <WiFi.h>
#include <HTTPClient.h>

// ── WiFi / Server Konfiguration ───────────────────────────────────────────────
const char* WIFI_SSID  = "RaceControl";
const char* WIFI_PASS  = "geheim";
const char* SERVER_URL = "http://192.168.1.100:1980";
const char* TIMING_KEY = "HIER_DEN_KEY_EINTRAGEN";

// ── Pins ──────────────────────────────────────────────────────────────────────
#define PIN_LS_START  4
#define PIN_LS_ZIEL   15
#define PIN_RESET     16
#define MAX_DIN       23
#define MAX_CLK       18
#define MAX_CS        5
#define MAX_DEVICES   1
#define PIN_SW1       32
#define PIN_SW2       33
#define PIN_SW3       25
#define PIN_SW4       26
#define PIN_LED       2

#define MIN_ZEIT_MS   3000
#define DEBOUNCE_MS   200

// ── Display ───────────────────────────────────────────────────────────────────
LedControl lc = LedControl(MAX_DIN, MAX_CLK, MAX_CS, MAX_DEVICES);

// ── Zustand ───────────────────────────────────────────────────────────────────
volatile bool          messungAktiv = false;
volatile unsigned long startMs      = 0;
volatile unsigned long stopMs       = 0;
volatile bool          ergebnisNeu  = false;
unsigned long          letzterStart = 0;
unsigned long          letzterStop  = 0;

bool wifiModus     = false;
bool helligkeitHoch = false;

// ── ISR ───────────────────────────────────────────────────────────────────────
void IRAM_ATTR isrStart() {
  unsigned long jetzt = millis();
  if (jetzt - letzterStart < DEBOUNCE_MS) return;
  letzterStart = jetzt;
  if (!messungAktiv) { startMs = jetzt; messungAktiv = true; }
}

void IRAM_ATTR isrZiel() {
  unsigned long jetzt = millis();
  if (jetzt - letzterStop < DEBOUNCE_MS) return;
  letzterStop = jetzt;
  if (messungAktiv) { stopMs = jetzt; messungAktiv = false; ergebnisNeu = true; }
}

// ── Display ───────────────────────────────────────────────────────────────────
void zeigeWarten() {
  for (int i = 0; i < 8; i++) lc.setChar(0, i, '-', false);
}

void zeigeZeit(unsigned long ms) {
  unsigned long hs = ms / 10;
  unsigned int  s  = hs / 100;
  unsigned int  h  = hs % 100;
  unsigned int  m  = s / 60;
  s = s % 60;
  lc.setDigit(0, 7, m / 10,  false);
  lc.setDigit(0, 6, m % 10,  false);
  lc.setDigit(0, 5, s / 10,  false);
  lc.setDigit(0, 4, s % 10,  true);   // Dezimalpunkt als Trenner
  lc.setDigit(0, 3, h / 10,  false);
  lc.setDigit(0, 2, h % 10,  false);
  lc.setChar(0, 1, ' ', false);
  lc.setChar(0, 0, ' ', false);
}

// ── WiFi ──────────────────────────────────────────────────────────────────────
void verbindeWiFi() {
  Serial.print(F("[WiFi] Verbinde…"));
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  int v = 0;
  while (WiFi.status() != WL_CONNECTED && v < 20) { delay(500); Serial.print('.'); v++; }
  Serial.println(WiFi.status() == WL_CONNECTED
    ? "\n[WiFi] OK: " + WiFi.localIP().toString()
    : F("\n[WiFi] Nicht erreichbar."));
}

void sendeErgebnis(unsigned long dauerMs) {
  if (WiFi.status() != WL_CONNECTED) { verbindeWiFi(); if (WiFi.status() != WL_CONNECTED) return; }

  float sekunden = dauerMs / 1000.0f;
  char  body[80];
  snprintf(body, sizeof(body),
    "{\"raw_time\":%.3f,\"source\":\"esp32_max7219\"}", sekunden);

  digitalWrite(PIN_LED, HIGH);
  HTTPClient http;
  http.begin(String(SERVER_URL) + "/api/timing/result");
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Timing-Key", TIMING_KEY);
  int code = http.POST(body);
  Serial.printf("[HTTP] %d – %.3f s\n", code, sekunden);
  http.end();
  digitalWrite(PIN_LED, LOW);
}

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);

  pinMode(PIN_LS_START, INPUT_PULLUP);
  pinMode(PIN_LS_ZIEL,  INPUT_PULLUP);
  pinMode(PIN_RESET,    INPUT_PULLUP);
  pinMode(PIN_SW1, INPUT_PULLUP); pinMode(PIN_SW2, INPUT_PULLUP);
  pinMode(PIN_SW3, INPUT_PULLUP); pinMode(PIN_SW4, INPUT_PULLUP);
  pinMode(PIN_LED, OUTPUT);

  wifiModus      = (digitalRead(PIN_SW1) == LOW);
  helligkeitHoch = (digitalRead(PIN_SW2) == LOW);

  lc.shutdown(0, false);
  lc.setIntensity(0, helligkeitHoch ? 12 : 4);
  lc.clearDisplay(0);
  zeigeWarten();

  attachInterrupt(digitalPinToInterrupt(PIN_LS_START), isrStart, FALLING);
  attachInterrupt(digitalPinToInterrupt(PIN_LS_ZIEL),  isrZiel,  FALLING);

  Serial.printf("[CFG]  Modus: %s  Helligkeit: %s\n",
    wifiModus ? "WiFi" : "Standalone",
    helligkeitHoch ? "hoch" : "niedrig");

  if (wifiModus) verbindeWiFi();
  Serial.println(F("[OK]   Bereit."));
}

// ── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
  if (digitalRead(PIN_RESET) == LOW) {
    delay(50);
    if (digitalRead(PIN_RESET) == LOW) {
      messungAktiv = false; ergebnisNeu = false;
      zeigeWarten(); Serial.println(F("Reset.")); delay(300);
    }
  }

  if (messungAktiv) { zeigeZeit(millis() - startMs); delay(30); return; }

  if (ergebnisNeu) {
    ergebnisNeu = false;
    unsigned long dauer = stopMs - startMs;
    if (dauer < MIN_ZEIT_MS) { zeigeWarten(); return; }
    zeigeZeit(dauer);
    unsigned long hs = dauer / 10;
    unsigned long mm = (hs / 100) / 60;
    unsigned long ss = (hs / 100) % 60;
    unsigned long hh = hs % 100;
    Serial.printf("Zeit: %02lu:%02lu.%02lu\n", mm, ss, hh);
    // JSON für serial_logger.py
    char json[96];
    snprintf(json, sizeof(json),
      "{\"event\":\"result\",\"device\":\"esp32_max7219\",\"time_ms\":%lu,\"time_fmt\":\"%02lu:%02lu.%02lu\"}",
      dauer, mm, ss, hh);
    Serial.println(json);
    if (wifiModus) sendeErgebnis(dauer);
  }

  delay(30);
}
