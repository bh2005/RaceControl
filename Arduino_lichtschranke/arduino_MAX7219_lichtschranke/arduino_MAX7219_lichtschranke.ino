/*
 * Lichtschranken-Zeitmessung mit MAX7219 8-Digit-Display
 * Arduino Nano / Uno
 *
 * License: GNU General Public License v2
 * Author : BH2005 · MSC Braach e.V. im ADAC
 * URL    : https://github.com/bh2005
 *
 * Bibliothek: LedControl by Eberhard Fahle
 *   → Arduino IDE: Sketch → Bibliothek einbinden → LedControl
 *
 * Pinbelegung:
 *   D2  – Lichtschranke 1 (Start)  INT0
 *   D3  – Lichtschranke 2 (Ziel)   INT1
 *   D5  – Reset-Taster (gegen GND)
 *   D10 – MAX7219 CS  (LOAD)
 *   D11 – MAX7219 DIN (MOSI)
 *   D13 – MAX7219 CLK (SCK)
 */

#include <LedControl.h>

// ── Pin-Definitionen ──────────────────────────────────────────────────────────
#define PIN_LS_START  2
#define PIN_LS_ZIEL   3
#define PIN_RESET     5
#define MAX_DIN       11
#define MAX_CLK       13
#define MAX_CS        10
#define MAX_DEVICES   1   // Anzahl verketteter MAX7219-Module

#define MIN_ZEIT_MS   3000
#define DEBOUNCE_MS   200

// ── Display (8-stellig) ───────────────────────────────────────────────────────
LedControl lc = LedControl(MAX_DIN, MAX_CLK, MAX_CS, MAX_DEVICES);

// ── Zustand ───────────────────────────────────────────────────────────────────
volatile bool         messungAktiv = false;
volatile unsigned long startMs     = 0;
volatile unsigned long stopMs      = 0;
volatile bool         ergebnisNeu  = false;

unsigned long letzterStart = 0;
unsigned long letzterStop  = 0;

// ── ISR ───────────────────────────────────────────────────────────────────────
void IRAM_ATTR isrStart() {
  unsigned long jetzt = millis();
  if (jetzt - letzterStart < DEBOUNCE_MS) return;
  letzterStart = jetzt;
  if (!messungAktiv) {
    startMs      = jetzt;
    messungAktiv = true;
  }
}

void IRAM_ATTR isrZiel() {
  unsigned long jetzt = millis();
  if (jetzt - letzterStop < DEBOUNCE_MS) return;
  letzterStop = jetzt;
  if (messungAktiv) {
    stopMs       = jetzt;
    messungAktiv = false;
    ergebnisNeu  = true;
  }
}

// ── Display-Hilfsfunktionen ───────────────────────────────────────────────────
void displayClear() {
  lc.clearDisplay(0);
}

// Zeigt MM:SS.hh auf 8-Digit-Display (Pos 7..0, linksbündig)
// Format: "  MM SS hh" → z.B. "  01 23 45"
void zeigeZeit(unsigned long ms) {
  unsigned long hs = ms / 10;
  unsigned int  s  = hs / 100;
  unsigned int  h  = hs % 100;
  unsigned int  m  = s / 60;
  s = s % 60;

  // Stellen 7-0 von links: M M S S . h h
  lc.setDigit(0, 7, m / 10,       false);
  lc.setDigit(0, 6, m % 10,       false);
  lc.setDigit(0, 5, s / 10,       false);
  lc.setDigit(0, 4, s % 10,       true);  // Dezimalpunkt = Trenner
  lc.setDigit(0, 3, h / 10,       false);
  lc.setDigit(0, 2, h % 10,       false);
  lc.setDigit(0, 1, 0,            false);
  lc.setDigit(0, 0, 0,            false);
}

void zeigeWarten() {
  displayClear();
  // Zeigt "--  --  --" mit Strichen
  for (int i = 0; i < 8; i++) {
    lc.setChar(0, i, '-', false);
  }
}

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(9600);

  lc.shutdown(0, false);
  lc.setIntensity(0, 4);
  lc.clearDisplay(0);
  zeigeWarten();

  pinMode(PIN_LS_START, INPUT_PULLUP);
  pinMode(PIN_LS_ZIEL,  INPUT_PULLUP);
  pinMode(PIN_RESET,    INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(PIN_LS_START), isrStart, FALLING);
  attachInterrupt(digitalPinToInterrupt(PIN_LS_ZIEL),  isrZiel,  FALLING);

  Serial.println(F("Lichtschranke (MAX7219) bereit."));
}

// ── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
  // Reset
  if (digitalRead(PIN_RESET) == LOW) {
    delay(50);
    if (digitalRead(PIN_RESET) == LOW) {
      messungAktiv = false;
      ergebnisNeu  = false;
      zeigeWarten();
      Serial.println(F("Reset."));
      delay(300);
    }
  }

  // Während Messung: laufende Zeit anzeigen
  if (messungAktiv) {
    unsigned long laufend = millis() - startMs;
    zeigeZeit(laufend);
    delay(50);
    return;
  }

  // Ergebnis anzeigen
  if (ergebnisNeu) {
    ergebnisNeu = false;
    unsigned long dauer = stopMs - startMs;

    if (dauer < MIN_ZEIT_MS) {
      Serial.println(F("Messung zu kurz – ignoriert."));
      zeigeWarten();
      return;
    }

    zeigeZeit(dauer);

    unsigned long hs = dauer / 10;
    unsigned int  s  = hs / 100;
    unsigned int  h  = hs % 100;
    unsigned int  m  = s / 60;
    s = s % 60;
    char buf[20];
    snprintf(buf, sizeof(buf), "Zeit: %02u:%02u.%02u", m, s, h);
    Serial.println(buf);
    // JSON für serial_logger.py
    char json[96];
    snprintf(json, sizeof(json),
      "{\"event\":\"result\",\"device\":\"arduino_max7219\",\"time_ms\":%lu,\"time_fmt\":\"%02u:%02u.%02u\"}",
      dauer, m, s, h);
    Serial.println(json);
  }

  delay(50);
}
