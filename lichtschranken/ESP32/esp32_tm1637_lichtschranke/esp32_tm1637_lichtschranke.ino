/*
 * Lichtschranken-Zeitmessung mit TM1637 + WiFi
 * ESP32 (z.B. ESP32 DevKit v1 / WROOM-32)
 *
 * License: GNU General Public License v2
 * Author : BH2005 · MSC Braach e.V. im ADAC
 *
 * Bibliotheken:
 *   - TM1637Display  (Avishay Orpaz)
 *   - WiFi, HTTPClient (ESP32 built-in)
 *
 * DIP-Schalter (4-fach):
 *   SW1 OFF=Standalone  ON=WiFi-Modus (sendet Ergebnis an RaceControl)
 *   SW2 reserviert
 *   SW3 reserviert
 *   SW4 reserviert
 *
 * Pinbelegung:
 *   GPIO4   – Lichtschranke Start   (FALLING, INPUT_PULLUP)
 *   GPIO5   – Lichtschranke Ziel    (FALLING, INPUT_PULLUP)
 *   GPIO15  – Reset-Taster          (FALLING, INPUT_PULLUP)
 *   GPIO18  – TM1637 CLK
 *   GPIO19  – TM1637 DIO
 *   GPIO32  – SW1  (INPUT_PULLUP)
 *   GPIO33  – SW2  (INPUT_PULLUP)
 *   GPIO25  – SW3  (INPUT_PULLUP)
 *   GPIO26  – SW4  (INPUT_PULLUP)
 *   GPIO2   – Status-LED (built-in, blinkt bei WiFi-Aktivität)
 */

#include <TM1637Display.h>
#include <WiFi.h>
#include <HTTPClient.h>

// ── WiFi / Server Konfiguration ───────────────────────────────────────────────
const char* WIFI_SSID   = "RaceControl";          // WLAN-Name anpassen
const char* WIFI_PASS   = "geheim";               // WLAN-Passwort anpassen
const char* SERVER_URL  = "http://192.168.1.100:1980"; // RaceControl-Server IP
const char* TIMING_KEY  = "HIER_DEN_KEY_EINTRAGEN";

// ── Pins ──────────────────────────────────────────────────────────────────────
#define PIN_LS_START  4
#define PIN_LS_ZIEL   5
#define PIN_RESET     15
#define PIN_CLK       18
#define PIN_DIO       19
#define PIN_SW1       32
#define PIN_SW2       33
#define PIN_SW3       25
#define PIN_SW4       26
#define PIN_LED       2

#define MIN_ZEIT_MS   3000
#define DEBOUNCE_MS   200

// ── Display ───────────────────────────────────────────────────────────────────
TM1637Display display(PIN_CLK, PIN_DIO);

// ── Zustand ───────────────────────────────────────────────────────────────────
volatile bool          messungAktiv = false;
volatile unsigned long startMs      = 0;
volatile unsigned long stopMs       = 0;
volatile bool          ergebnisNeu  = false;
unsigned long          letzterStart = 0;
unsigned long          letzterStop  = 0;

bool wifiModus = false;

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
  const uint8_t dash = SEG_G;
  display.setSegments((uint8_t[]){dash, dash, dash, dash});
}

void zeigeZeit(unsigned long ms) {
  unsigned long hs = ms / 10;
  unsigned int  s  = hs / 100;
  unsigned int  h  = hs % 100;
  if (s < 100) {
    display.showNumberDecEx(s * 100 + h, 0b01000000, true);
  } else {
    display.showNumberDecEx((s / 60) * 100 + (s % 60), 0b01000000, true);
  }
}

// ── WiFi ──────────────────────────────────────────────────────────────────────
void verbindeWiFi() {
  Serial.print(F("[WiFi] Verbinde mit "));
  Serial.print(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  int versuche = 0;
  while (WiFi.status() != WL_CONNECTED && versuche < 20) {
    delay(500); Serial.print('.'); versuche++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print(F("\n[WiFi] Verbunden: "));
    Serial.println(WiFi.localIP());
  } else {
    Serial.println(F("\n[WiFi] Nicht erreichbar."));
  }
}

void sendeErgebnis(unsigned long dauerMs) {
  if (WiFi.status() != WL_CONNECTED) {
    verbindeWiFi();
    if (WiFi.status() != WL_CONNECTED) return;
  }

  float sekunden = dauerMs / 1000.0f;
  char  body[80];
  snprintf(body, sizeof(body),
    "{\"raw_time\":%.3f,\"source\":\"arduino_tm1637\"}", sekunden);

  digitalWrite(PIN_LED, HIGH);
  HTTPClient http;
  http.begin(String(SERVER_URL) + "/api/timing/result");
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Timing-Key", TIMING_KEY);
  int code = http.POST(body);
  Serial.print(F("[HTTP] "));
  Serial.print(code);
  Serial.print(F(" – "));
  Serial.println(sekunden, 3);
  http.end();
  digitalWrite(PIN_LED, LOW);
}

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);

  pinMode(PIN_LS_START, INPUT_PULLUP);
  pinMode(PIN_LS_ZIEL,  INPUT_PULLUP);
  pinMode(PIN_RESET,    INPUT_PULLUP);
  pinMode(PIN_SW1, INPUT_PULLUP);
  pinMode(PIN_SW2, INPUT_PULLUP);
  pinMode(PIN_SW3, INPUT_PULLUP);
  pinMode(PIN_SW4, INPUT_PULLUP);
  pinMode(PIN_LED, OUTPUT);

  // DIP-Schalter auslesen (einmalig beim Boot)
  wifiModus = (digitalRead(PIN_SW1) == LOW);

  display.setBrightness(4);
  zeigeWarten();

  attachInterrupt(digitalPinToInterrupt(PIN_LS_START), isrStart, FALLING);
  attachInterrupt(digitalPinToInterrupt(PIN_LS_ZIEL),  isrZiel,  FALLING);

  Serial.print(F("[CFG]  Modus: "));
  Serial.println(wifiModus ? F("WiFi (sendet an RaceControl)") : F("Standalone"));

  if (wifiModus) verbindeWiFi();
  Serial.println(F("[OK]   Bereit."));
}

// ── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
  if (digitalRead(PIN_RESET) == LOW) {
    delay(50);
    if (digitalRead(PIN_RESET) == LOW) {
      messungAktiv = false; ergebnisNeu = false;
      zeigeWarten();
      Serial.println(F("Reset.")); delay(300);
    }
  }

  if (messungAktiv) { zeigeZeit(millis() - startMs); delay(50); return; }

  if (ergebnisNeu) {
    ergebnisNeu = false;
    unsigned long dauer = stopMs - startMs;
    if (dauer < MIN_ZEIT_MS) { zeigeWarten(); return; }
    zeigeZeit(dauer);

    unsigned long hs = dauer / 10;
    unsigned long mm = (hs / 100) / 60;
    unsigned long ss = (hs / 100) % 60;
    unsigned long hh = hs % 100;
    char buf[20];
    snprintf(buf, sizeof(buf), "Zeit: %02lu:%02lu.%02lu", mm, ss, hh);
    Serial.println(buf);
    // JSON für serial_logger.py
    char json[96];
    snprintf(json, sizeof(json),
      "{\"event\":\"result\",\"device\":\"esp32_tm1637\",\"time_ms\":%lu,\"time_fmt\":\"%02lu:%02lu.%02lu\"}",
      dauer, mm, ss, hh);
    Serial.println(json);

    if (wifiModus) sendeErgebnis(dauer);
  }

  delay(50);
}
