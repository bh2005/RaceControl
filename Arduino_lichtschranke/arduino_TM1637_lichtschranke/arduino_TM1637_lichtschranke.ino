/*
 * Lichtschranken-Zeitmessung mit TM1637-Display
 * Arduino Nano / Uno
 *
 * License: GNU General Public License v2
 * Author : BH2005 · MSC Braach e.V. im ADAC
 * URL    : https://github.com/bh2005
 *
 * Bibliothek: TM1637Display by Avishay Orpaz
 *   → Arduino IDE: Sketch → Bibliothek einbinden → TM1637
 *
 * Pinbelegung:
 *   D2  – Lichtschranke 1 (Start)  INT0
 *   D3  – Lichtschranke 2 (Ziel)   INT1
 *   D5  – Reset-Taster (gegen GND)
 *   D6  – TM1637 CLK
 *   D7  – TM1637 DIO
 */

#include <TM1637Display.h>

// ── Pin-Definitionen ──────────────────────────────────────────────────────────
#define PIN_LS_START  2   // INT0 – Lichtschranke Start
#define PIN_LS_ZIEL   3   // INT1 – Lichtschranke Ziel
#define PIN_RESET     5   // Reset-Taster
#define PIN_CLK       6   // TM1637 CLK
#define PIN_DIO       7   // TM1637 DIO

#define MIN_ZEIT_MS   3000  // Mindestzeit 3 s (verhindert Fehlmessungen)
#define DEBOUNCE_MS   200   // Entprellzeit

// ── Display ───────────────────────────────────────────────────────────────────
TM1637Display display(PIN_CLK, PIN_DIO);

// ── Zustand ───────────────────────────────────────────────────────────────────
volatile bool    messungAktiv = false;
volatile unsigned long startMs = 0;
volatile unsigned long stopMs  = 0;
volatile bool    ergebnisNeu  = false;

unsigned long letzterStart = 0;
unsigned long letzterStop  = 0;

// ── ISR: Lichtschranke Start ──────────────────────────────────────────────────
void IRAM_ATTR isrStart() {
  unsigned long jetzt = millis();
  if (jetzt - letzterStart < DEBOUNCE_MS) return;
  letzterStart = jetzt;
  if (!messungAktiv) {
    startMs      = jetzt;
    messungAktiv = true;
  }
}

// ── ISR: Lichtschranke Ziel ───────────────────────────────────────────────────
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
void zeigeWarten() {
  // Zeigt "----" im Wartezustand
  const uint8_t dash = SEG_G;
  display.setSegments((uint8_t[]){dash, dash, dash, dash});
}

void zeigeZeit(unsigned long ms) {
  // Format: SS.hh (Sekunden.Hundertstel) wenn < 100 s
  //         MM:SS              wenn >= 100 s
  unsigned long hs = ms / 10;          // Hundertstel gesamt
  unsigned int  s  = hs / 100;
  unsigned int  h  = hs % 100;

  if (s < 100) {
    // SS.hh – Dezimalpunkt nach Stelle 2
    display.showNumberDecEx(s * 100 + h, 0b01000000, true);
  } else {
    // MM:SS – Doppelpunkt
    unsigned int m = s / 60;
    s = s % 60;
    display.showNumberDecEx(m * 100 + s, 0b01000000, true);
  }
}

void zeigeMessen() {
  // Blinkt "rUn" während Messung läuft (grobe Animation)
  static bool an = false;
  if (an) {
    display.showNumberDec(8888, false);
  } else {
    zeigeWarten();
  }
  an = !an;
}

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(9600);

  pinMode(PIN_LS_START, INPUT_PULLUP);
  pinMode(PIN_LS_ZIEL,  INPUT_PULLUP);
  pinMode(PIN_RESET,    INPUT_PULLUP);

  display.setBrightness(4);
  zeigeWarten();

  attachInterrupt(digitalPinToInterrupt(PIN_LS_START), isrStart, FALLING);
  attachInterrupt(digitalPinToInterrupt(PIN_LS_ZIEL),  isrZiel,  FALLING);

  Serial.println(F("Lichtschranke bereit."));
}

// ── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
  // Reset-Taster
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

  // Messung läuft – Display animieren
  if (messungAktiv) {
    zeigeMessen();
    delay(500);
    return;
  }

  // Neues Ergebnis anzeigen
  if (ergebnisNeu) {
    ergebnisNeu = false;
    unsigned long dauer = stopMs - startMs;

    if (dauer < MIN_ZEIT_MS) {
      Serial.println(F("Messung zu kurz – ignoriert."));
      zeigeWarten();
      return;
    }

    zeigeZeit(dauer);

    // Serielle Ausgabe
    unsigned long hs = dauer / 10;
    unsigned int  s  = hs / 100;
    unsigned int  h  = hs % 100;
    unsigned int  m  = s / 60;
    s = s % 60;
    char buf[16];
    snprintf(buf, sizeof(buf), "Zeit: %02u:%02u.%02u", m, s, h);
    Serial.println(buf);
    // JSON für serial_logger.py
    char json[96];
    snprintf(json, sizeof(json),
      "{\"event\":\"result\",\"device\":\"arduino_tm1637\",\"time_ms\":%lu,\"time_fmt\":\"%02u:%02u.%02u\"}",
      dauer, m, s, h);
    Serial.println(json);
  }

  delay(100);
}
