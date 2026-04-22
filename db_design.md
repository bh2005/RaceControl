# RaceControl Pro – Datenbankdesign

**Stack:** SQLite (Offline-First) · Python/FastAPI  
**Zielgröße:** ~300 Starter, ~10 Klassen, 50+ simultane WS-Clients

---

## Übersicht: Alle Tabellen

```
Events
  └── Classes ──────────────────────────────┐
        └── RaceResults                      │
              ├── RunPenalties               │
              └── AuditLog                   │
Reglements                                   │
  └── PenaltyDefinitions                     │
Participants ────────────────────────────────┘
Users (für AuditLog & Rollenverwaltung)
```

---

## 1. Reglement-Engine

### Tabelle: `Reglements`

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK | Eindeutige ID |
| `name` | TEXT NOT NULL | z.B. `"ADAC JKS 2026"` oder `"KS2000 Hessen"` |
| `scoring_type` | TEXT NOT NULL | `"sum_all"` (Summe aller Läufe) · `"best_of"` · `"sum_minus_worst"` (Streicher) |
| `points_formula` | TEXT | Name der Punktetabelle oder JSON-Formel (optional, für Meisterschaft) |
| `runs_per_class` | INTEGER DEFAULT 2 | Anzahl Wertungsläufe (ohne Training) |
| `has_training` | BOOLEAN DEFAULT 1 | Ob ein Trainingslauf vorgesehen ist |
| `created_at` | DATETIME DEFAULT CURRENT_TIMESTAMP | |

### Tabelle: `PenaltyDefinitions`

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK | Eindeutige ID |
| `reglement_id` | INTEGER FK → Reglements | Zu welchem Reglement gehört diese Strafe |
| `label` | TEXT NOT NULL | Anzeigename (z.B. `"Pylone"`, `"Torfehler"`) |
| `seconds` | REAL NOT NULL | Strafwert in Sekunden (z.B. `2.0` oder `10.0`) |
| `shortcut_key` | CHAR(1) | Taste für die Zeitnahme (z.B. `'P'` oder `'1'`) |
| `sort_order` | INTEGER DEFAULT 0 | Reihenfolge in der Zeitnahme-UI |

---

## 2. Veranstaltungen & Klassen

### Tabelle: `Events`

Ohne diese Tabelle sind alle Ergebnisse keiner Veranstaltung zugeordnet — bei mehreren Events in der DB wäre nichts trennbar.

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK | Eindeutige ID |
| `name` | TEXT NOT NULL | z.B. `"ADAC Kart-Slalom Kassel 2026-06-01"` |
| `date` | DATE NOT NULL | Veranstaltungsdatum |
| `location` | TEXT | Austragungsort |
| `reglement_id` | INTEGER FK → Reglements | Gilt-für-Reglement (Standardwert, überschreibbar pro Klasse) |
| `status` | TEXT DEFAULT `'planned'` | `"planned"` · `"active"` · `"finished"` · `"official"` |
| `created_at` | DATETIME DEFAULT CURRENT_TIMESTAMP | |

### Tabelle: `Classes`

Ersetzt die fehlende Referenz von `class_id` in `RaceResults`. Definiert auch die automatische Altersklassen-Zuweisung über `birth_year`.

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK | Eindeutige ID |
| `event_id` | INTEGER FK → Events | Zu welcher Veranstaltung |
| `reglement_id` | INTEGER FK → Reglements | Kann vom Event-Standard abweichen |
| `name` | TEXT NOT NULL | z.B. `"Schüler A"`, `"Junioren"`, `"Senioren"` |
| `short_name` | TEXT | Kürzel für Ausdrucke (z.B. `"SA"`) |
| `min_birth_year` | INTEGER | Untergrenze Geburtsjahr (inklusiv) |
| `max_birth_year` | INTEGER | Obergrenze Geburtsjahr (inklusiv) |
| `run_status` | TEXT DEFAULT `'planned'` | `"planned"` · `"running"` · `"preliminary"` · `"official"` |
| `start_order` | INTEGER DEFAULT 0 | Reihenfolge im Tagesablauf |

---

## 3. Teilnehmer

### Tabelle: `Participants`

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK | Eindeutige ID |
| `event_id` | INTEGER FK → Events | Zugeordnete Veranstaltung |
| `class_id` | INTEGER FK → Classes | Klasse (automatisch via `birth_year` oder manuell) |
| `start_number` | INTEGER NOT NULL | Die feste Nummer am Kart |
| `first_name` | TEXT NOT NULL | Vorname |
| `last_name` | TEXT NOT NULL | Nachname |
| `birth_year` | INTEGER | Für automatisches Klassen-Mapping |
| `club` | TEXT | Ortsclub / Team |
| `license_number` | TEXT | ADAC-Lizenznummer (optional) |
| `status` | TEXT DEFAULT `'registered'` | `"registered"` · `"checked_in"` · `"technical_ok"` · `"disqualified"` |

> **Automatisches Klassen-Mapping:** Beim Check-in prüft das Backend `birth_year` gegen `Classes.min_birth_year` / `max_birth_year` des Events und schlägt die passende Klasse vor.

---

## 4. Ergebnisse & Strafen

### Tabelle: `RaceResults`

Kernprinzip: **Rohdaten unveränderlich, Korrekturen im AuditLog.**  
`total_penalties` wird immer aus `RunPenalties` berechnet, nicht direkt gespeichert.

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK | Eindeutige ID |
| `event_id` | INTEGER FK → Events | Zugeordnete Veranstaltung |
| `participant_id` | INTEGER FK → Participants | Wer ist gefahren? |
| `class_id` | INTEGER FK → Classes | In welcher Klasse? |
| `run_number` | INTEGER NOT NULL | `0` = Training · `1` = Lauf 1 · `2` = Lauf 2 |
| `raw_time` | REAL | Die gestoppte Zeit in Sekunden (z.B. `45.67`) · NULL bei DNS/DNF |
| `status` | TEXT DEFAULT `'valid'` | `"valid"` · `"dns"` · `"dnf"` · `"dsq"` |
| `is_official` | BOOLEAN DEFAULT 0 | Vom Schiedsrichter freigegeben? |
| `entered_by` | INTEGER FK → Users | Wer hat den Eintrag erstellt |
| `created_at` | DATETIME DEFAULT CURRENT_TIMESTAMP | |

> **`total_penalties` wird nicht gespeichert** — sie wird on-the-fly berechnet:  
> `SELECT SUM(pd.seconds * rp.count) FROM RunPenalties rp JOIN PenaltyDefinitions pd ON pd.id = rp.penalty_definition_id WHERE rp.result_id = ?`

### Tabelle: `RunPenalties`

Einzelne Strafeinträge pro Lauf. Ermöglicht vollständige Nachvollziehbarkeit (welche Strafen wurden vergeben?) und korrekte Neuberechnung, wenn sich ein Strafwert ändert.

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK | Eindeutige ID |
| `result_id` | INTEGER FK → RaceResults | Zu welchem Lauf |
| `penalty_definition_id` | INTEGER FK → PenaltyDefinitions | Welche Strafart |
| `count` | INTEGER DEFAULT 1 | Anzahl (z.B. 3× Pylone) |
| `entered_by` | INTEGER FK → Users | Wer hat eingetragen |
| `created_at` | DATETIME DEFAULT CURRENT_TIMESTAMP | |

---

## 5. Benutzer & Rollen

### Tabelle: `Users`

Wird für `AuditLog`, `RaceResults.entered_by` und die Session-Verwaltung benötigt.

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK | Eindeutige ID |
| `username` | TEXT NOT NULL UNIQUE | Anmeldename |
| `password_hash` | TEXT NOT NULL | bcrypt-Hash |
| `role` | TEXT NOT NULL | `"admin"` · `"schiedsrichter"` · `"nennung"` · `"zeitnahme"` · `"viewer"` |
| `display_name` | TEXT | Anzeigename (z.B. `"Hans Müller"`) |
| `is_active` | BOOLEAN DEFAULT 1 | Konto aktiv? |
| `created_at` | DATETIME DEFAULT CURRENT_TIMESTAMP | |

### Rollen & Aufgaben

| Rolle | Aufgaben | Schreiben | Lesen |
|---|---|---|---|
| `admin` | System-Setup, Reglements anlegen, User erstellen, Datenbank-Backups, finale Korrekturen | Alles (inkl. Löschen) | Alles |
| `schiedsrichter` | Zeiten und Strafen korrigieren (mit Audit-Pflicht), Veto-Recht, offizielle Klassen-Freigabe | Korrekturen + Freigabe (kein System-Setup, keine User-Verwaltung) | Alles |
| `nennung` | Fahrer-Check-in, Stammdaten korrigieren, Nachnennungen, Klassen-Zuweisung | Nur Stammdaten (`Participants`, `Classes`) | Stammdaten + Zeiten |
| `zeitnahme` | Eingabe von Laufzeiten und Strafen, Lauf-Status setzen (Start/Ziel) | Nur `RaceResults` + `RunPenalties` | Stammdaten |
| `viewer` | Ergebnisse live verfolgen, Tabellenstand, Urkunden-Vorschau | — (keine Eingabefelder sichtbar) | Alles (read-only) |

### Berechtigungs-Matrix (API-Ebene)

| Ressource / Aktion | admin | schiedsrichter | nennung | zeitnahme | viewer |
|---|---|---|---|---|---|
| Reglements anlegen / ändern | ✅ | — | — | — | — |
| Events anlegen / ändern | ✅ | — | — | — | — |
| Klassen konfigurieren | ✅ | — | — | — | — |
| User anlegen | ✅ | — | — | — | — |
| Datenbank-Backup | ✅ | — | — | — | — |
| Teilnehmer anlegen / ändern | ✅ | — | ✅ | — | — |
| Klassen-Zuweisung setzen | ✅ | — | ✅ | — | — |
| Check-in / techn. Abnahme | ✅ | — | ✅ | — | — |
| Zeiten eingeben | ✅ | — | — | ✅ | — |
| Strafen eingeben | ✅ | — | — | ✅ | — |
| Lauf-Status setzen | ✅ | — | — | ✅ | — |
| Zeiten / Strafen korrigieren | ✅ | ✅ (Audit-Pflicht) | — | — | — |
| Klasse freigeben (`run_status = official`) | ✅ | ✅ | — | — | — |
| Ergebnisse lesen | ✅ | ✅ | ✅ | ✅ | ✅ |
| Livetiming / Urkunden-Vorschau | ✅ | ✅ | ✅ | ✅ | ✅ |

> **Audit-Pflicht für `schiedsrichter`:** Jede Korrektur durch einen Schiedsrichter erfordert
> eine Begründung (`reason`) und wird im `AuditLog` mit `user_id` und Timestamp festgehalten.
> Ohne ausgefüllte Begründung lehnt die API die Änderung ab (`HTTP 422`).

---

## 6. Audit-Log

### Tabelle: `AuditLog`

Jede manuelle Änderung an `RaceResults` oder `RunPenalties` wird hier revisionssicher protokolliert.

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK | Eindeutige ID |
| `result_id` | INTEGER FK → RaceResults | Welches Ergebnis wurde geändert |
| `user_id` | INTEGER FK → Users | Wer hat geändert |
| `field_changed` | TEXT NOT NULL | Welches Feld: `"raw_time"` · `"status"` · `"penalty"` · `"is_official"` |
| `old_value` | TEXT | Wert vor der Änderung (JSON-serialisiert) |
| `new_value` | TEXT | Wert nach der Änderung (JSON-serialisiert) |
| `reason` | TEXT | Begründung (z.B. `"Pylone nach Videobeweis gestrichen"`) |
| `timestamp` | DATETIME DEFAULT CURRENT_TIMESTAMP | Wann passierte die Änderung |

---

## 7. Beziehungsdiagramm (vereinfacht)

```
Events ──────────────────────────┐
  │                              │
  ├── Classes ───────────────────┤
  │     └── Participants ────────┤
  │                              │
  └── RaceResults ───────────────┘
        ├── RunPenalties
        │     └── PenaltyDefinitions ── Reglements
        └── AuditLog
              └── Users
```

---

## 8. SQLite-Besonderheiten

- **`REAL` für Zeiten:** SQLite hat keinen `DECIMAL`-Typ — `REAL` (64-bit float) ist präzise genug für Slalomzeiten (±0.001s Genauigkeit bei Werten bis ~999s)
- **`BOOLEAN`:** SQLite speichert als `0`/`1` — in FastAPI/Pydantic als `bool` abbilden
- **`DATETIME`:** Als ISO-8601-String speichern (`"2026-06-01T09:30:00"`)
- **Kein `CASCADE DELETE`** für AuditLog — gelöschte Ergebnisse sollen im Log erhalten bleiben
- **WAL-Modus aktivieren:** `PRAGMA journal_mode=WAL;` — ermöglicht simultane Lese-/Schreibzugriffe (wichtig für 50+ WS-Clients)

---

*Letzte Änderung: 2026-04-22 · RaceControl Pro*
