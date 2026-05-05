// Protestfrist in Minuten (Reglementvorschrift)
export const PROTEST_WINDOW_MIN = 30

// Zeitmessung
export const AUTO_CLOSE_DELAY_MS  = 6_000   // ms bis Lauf automatisch geschlossen wird
export const FLASH_DURATION_MS    =  1_800   // ms für Highlight-Effekt nach neuem Ergebnis
export const MARSHAL_TIMEOUT_MS   = 60_000   // ms bis Marshal-Meldung abläuft (Zeitnahme)
export const MARSHAL_TIMEOUT_SPEAKER_MS = 30_000  // ms bis Marshal-Meldung im Speaker abläuft
export const DEBOUNCE_SAVE_MS     =   400    // ms Debounce beim Speichern von Formularen

// Livetiming / Polling
export const POLL_INTERVAL_MS  = 30_000  // ms zwischen Polling-Anfragen wenn WS getrennt
export const DEFAULT_RUNS      = 2       // Anzahl Läufe wenn kein Wert bekannt
export const RECENT_RUNS_LIMIT = 8       // max. angezeigte Einzel-Läufe

// Speaker
export const SPEAKER_LOG_LIMIT    = 50      // max. Einträge im Event-Log
export const SPEAKER_RANK_TARGETS = [1, 3, 10]  // Plätze für Zeitrückstand-Anzeige
