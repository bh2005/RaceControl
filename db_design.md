# RaceControl Pro – Datenbankdesign

**Stack:** SQLite (WAL-Modus, Offline-First) · Python 3.9+ / FastAPI  
**Zielgröße:** ~300 Starter, ~10 Klassen, 50+ simultane WS-Clients  
**Schema-Datei:** `schema.sql` (Single Source of Truth)  
*Letzte Aktualisierung: 2026-04-29 · v0.6.0*

---

## Tabellenübersicht

```
Reglements
  └── PenaltyDefinitions

Events
  └── Classes ──────────────────────────────┐
        └── RaceResults                      │
              ├── RunPenalties               │
              └── AuditLog ──── Users        │
Participants ────────────────────────────────┘
  └── Clubs (FK)

Teams
  └── TeamMembers ── Participants

Trainees ── Clubs (FK)
  └── TrainingRuns
        └── TrainingSessions

Sponsors
Settings
```

---

## 1. Reglement-Engine

### `Reglements`

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `name` | TEXT NOT NULL UNIQUE | z.B. `"ADAC JKS 2026"`, `"KS2000 Hessen"` |
| `scoring_type` | TEXT NOT NULL | `"sum_all"` · `"best_of"` · `"sum_minus_worst"` |
| `points_formula` | TEXT | JSON-Formel oder Tabellen-Name (optional) |
| `runs_per_class` | INTEGER DEFAULT 2 | Wertungsläufe ohne Training |
| `has_training` | INTEGER DEFAULT 1 | 1 = Trainingslauf vorgesehen |
| `created_at` | TEXT | ISO-8601-Timestamp |

### `PenaltyDefinitions`

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `reglement_id` | INTEGER FK → Reglements CASCADE | |
| `label` | TEXT NOT NULL | z.B. `"Pylone"`, `"Torfehler"`, `"Ausbruch"` |
| `seconds` | REAL NOT NULL ≥ 0 | Strafwert in Sekunden |
| `shortcut_key` | TEXT | Einzeltaste für Zeitnahme-UI (z.B. `'P'`) |
| `sort_order` | INTEGER DEFAULT 0 | Reihenfolge in der UI |

> UNIQUE: `(reglement_id, shortcut_key)` — keine doppelten Tasten pro Reglement

---

## 2. Veranstaltungen & Klassen

### `Events`

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `name` | TEXT NOT NULL | z.B. `"ADAC Kart-Slalom Kassel 2026-06-01"` |
| `date` | TEXT NOT NULL | ISO-8601: `"2026-06-01"` |
| `location` | TEXT | Austragungsort |
| `reglement_id` | INTEGER FK → Reglements SET NULL | Standard-Reglement (überschreibbar pro Klasse) |
| `status` | TEXT DEFAULT `'planned'` | `"planned"` · `"active"` · `"finished"` · `"official"` |
| `description` | TEXT | Infotext für die Landingpage (HTML/Freitext) |
| `created_at` | TEXT | ISO-8601-Timestamp |

### `Classes`

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `event_id` | INTEGER FK → Events CASCADE | |
| `reglement_id` | INTEGER FK → Reglements SET NULL | Kann vom Event-Standard abweichen |
| `name` | TEXT NOT NULL | z.B. `"Schüler A"`, `"Junioren"`, `"Senioren"` |
| `short_name` | TEXT | Kürzel für Ausdrucke (z.B. `"SA"`) |
| `min_birth_year` | INTEGER | Untergrenze Geburtsjahr (inklusiv) |
| `max_birth_year` | INTEGER | Obergrenze Geburtsjahr (inklusiv) |
| `run_status` | TEXT DEFAULT `'planned'` | Statuswerte siehe unten |
| `start_order` | INTEGER DEFAULT 0 | Reihenfolge im Tagesablauf |
| `registration_closed_at` | TEXT | ISO-8601-Timestamp: Nennungsschluss |
| `start_time` | TEXT | Geplante/tatsächliche Startzeit `"HH:MM"` |
| `end_time` | TEXT | ISO-Timestamp Klassenende → startet 30-min-Einspruchsfrist |

> UNIQUE: `(event_id, name)`

**Klassen-Statusübergänge:**

```
planned → running → paused ↔ running
                 ↓
           preliminary → official
```

| Status | Bedeutung |
|---|---|
| `planned` | Noch nicht gestartet |
| `running` | Läuft aktuell |
| `paused` | Unterbrochen (z.B. Regen, Vorfall) |
| `preliminary` | Vorläufig beendet — Einspruchsfrist läuft |
| `official` | Offiziell — freigegeben durch Schiedsrichter |

---

## 3. Vereine

### `Clubs`

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `name` | TEXT NOT NULL UNIQUE | z.B. `"MSC Braach e.V. im ADAC"` |
| `short_name` | TEXT | Kürzel für Listen (z.B. `"MSC Braach"`) |
| `city` | TEXT | Ort (optional) |
| `created_at` | TEXT | ISO-8601-Timestamp |

---

## 4. Teilnehmer

### `Participants`

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `event_id` | INTEGER FK → Events CASCADE | Zugeordnete Veranstaltung |
| `class_id` | INTEGER FK → Classes SET NULL | Klasse (auto via `birth_year` oder manuell) |
| `club_id` | INTEGER FK → Clubs SET NULL | NULL = `"n.N."` (Verein unbekannt) |
| `start_number` | INTEGER | NULL bis zur Auslosung |
| `first_name` | TEXT NOT NULL | Vorname |
| `last_name` | TEXT NOT NULL | Nachname |
| `birth_year` | INTEGER | Für automatisches Klassen-Mapping |
| `license_number` | TEXT | ADAC-Lizenznummer (optional) |
| `gender` | TEXT | `'m'` · `'w'` · NULL — für Auswertung Schnellste Dame/Herr |
| `status` | TEXT DEFAULT `'registered'` | `"registered"` · `"checked_in"` · `"technical_ok"` · `"disqualified"` |
| `fee_paid` | INTEGER DEFAULT 0 | 0/1 — Nenngeld bezahlt |
| `helmet_ok` | INTEGER DEFAULT 0 | 0/1 — Helmkontrolle bestanden |

> UNIQUE: `(class_id, start_number)` — Startnummer eindeutig pro Klasse (jede Klasse beginnt bei 1)  
> Automatisches Klassen-Mapping: Backend prüft `birth_year` gegen `min_birth_year`/`max_birth_year` und schlägt passende Klasse vor.  
> Migration `_migrate_participants_gender()` fügt `gender`-Spalte per `ALTER TABLE` hinzu.

---

## 4b. Trainings-Stammdaten

### `Trainees`

Persistente Jugendlichen-Datenbank — unabhängig von Veranstaltungen.

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `first_name` | TEXT NOT NULL | |
| `last_name` | TEXT NOT NULL | |
| `birth_year` | INTEGER | |
| `license_number` | TEXT | ADAC-Lizenznummer (optional) |
| `club_id` | INTEGER FK → Clubs SET NULL | |
| `kart_number` | TEXT | Standard-Kart-Nummer (überschreibbar pro Run) |
| `is_active` | INTEGER DEFAULT 1 | 0 = inaktiv (erscheint nicht in der Session-Liste) |
| `notes` | TEXT | |
| `created_at` | TEXT | ISO-8601-Timestamp |

### `TrainingSessions`

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `name` | TEXT NOT NULL | z.B. `"Donnerstagstraining 29.04.2026"` |
| `date` | TEXT NOT NULL | ISO-8601 `"YYYY-MM-DD"` |
| `status` | TEXT DEFAULT `'planned'` | `"planned"` · `"active"` · `"finished"` |
| `notes` | TEXT | |
| `created_by` | INTEGER FK → Users SET NULL | |
| `created_at` | TEXT | ISO-8601-Timestamp |

> Nur eine Session kann gleichzeitig `status = 'active'` haben. Der PATCH-Endpoint setzt andere Sessions automatisch auf `'finished'`.

### `TrainingRuns`

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `session_id` | INTEGER FK → TrainingSessions CASCADE | |
| `trainee_id` | INTEGER FK → Trainees CASCADE | |
| `kart_number` | TEXT | Überschreibt `Trainees.kart_number` für diesen Lauf |
| `run_number` | INTEGER DEFAULT 1 | Auto-Increment via `MAX(run_number)+1` pro Fahrer/Session |
| `raw_time` | REAL | NULL bei DNS/DNF/DSQ |
| `penalty_seconds` | REAL DEFAULT 0 | Summierte Strafzeit |
| `status` | TEXT DEFAULT `'valid'` | `"valid"` · `"dns"` · `"dnf"` · `"dsq"` |
| `source` | TEXT DEFAULT `'manual'` | `"manual"` · `"lichtschranke"` |
| `entered_by` | INTEGER FK → Users SET NULL | |
| `created_at` | TEXT | ISO-8601-Timestamp |

> UNIQUE: `(session_id, trainee_id, run_number)`

**View `v_training_standings`:**
```sql
-- Rang, Bestzeit, Durchschnitt pro Fahrer je Session
SELECT r.session_id, t.id AS trainee_id, t.first_name, t.last_name,
       COUNT(*) AS run_count,
       MIN(CASE WHEN r.status='valid' THEN r.raw_time + r.penalty_seconds END) AS best_time,
       AVG(CASE WHEN r.status='valid' THEN r.raw_time + r.penalty_seconds END) AS avg_time
FROM TrainingRuns r JOIN Trainees t ON t.id = r.trainee_id
GROUP BY r.session_id, r.trainee_id;
```

---

## 5. Ergebnisse & Strafen

### `RaceResults`

Kernprinzip: **Rohdaten unveränderlich — Korrekturen über AuditLog.**  
`total_penalties` wird nie gespeichert, immer live aus `RunPenalties` berechnet.

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `event_id` | INTEGER FK → Events CASCADE | |
| `participant_id` | INTEGER FK → Participants CASCADE | |
| `class_id` | INTEGER FK → Classes CASCADE | |
| `run_number` | INTEGER ≥ 0 | `0` = Training · `1` = Lauf 1 · `2` = Lauf 2 … |
| `raw_time` | REAL | Gestoppte Zeit in Sekunden · NULL bei DNS/DNF |
| `status` | TEXT DEFAULT `'valid'` | `"valid"` · `"dns"` · `"dnf"` · `"dsq"` |
| `is_official` | INTEGER DEFAULT 0 | 1 = Schiedsrichter hat freigegeben |
| `entered_by` | INTEGER FK → Users SET NULL | Wer hat eingetragen |
| `created_at` | TEXT | ISO-8601-Timestamp |

> UNIQUE: `(participant_id, class_id, run_number)` — ein Ergebnis pro Fahrer/Lauf

**Strafberechnung (immer on-the-fly):**
```sql
SELECT COALESCE(SUM(pd.seconds * rp.count), 0)
FROM   RunPenalties rp
JOIN   PenaltyDefinitions pd ON pd.id = rp.penalty_definition_id
WHERE  rp.result_id = ?
```

### `RunPenalties`

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `result_id` | INTEGER FK → RaceResults CASCADE | |
| `penalty_definition_id` | INTEGER FK → PenaltyDefinitions RESTRICT | |
| `count` | INTEGER DEFAULT 1 > 0 | Anzahl (z.B. 3× Pylone) |
| `entered_by` | INTEGER FK → Users SET NULL | |
| `created_at` | TEXT | ISO-8601-Timestamp |

---

## 6. Benutzer & Rollen

### `Users`

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `username` | TEXT NOT NULL UNIQUE | |
| `password_hash` | TEXT NOT NULL | bcrypt-Hash |
| `role` | TEXT NOT NULL | Werte siehe unten |
| `display_name` | TEXT | z.B. `"Hans Müller (SRI)"` |
| `is_active` | INTEGER DEFAULT 1 | 0 = gesperrt |
| `created_at` | TEXT | ISO-8601-Timestamp |

**Rollen & API-Berechtigungen:**

| Ressource / Aktion | admin | schiedsrichter | nennung | zeitnahme | viewer |
|---|:---:|:---:|:---:|:---:|:---:|
| Reglements, Events, Klassen, User | ✅ | — | — | — | — |
| Teilnehmer anlegen / ändern | ✅ | — | ✅ | — | — |
| Check-in, Abnahme (Nenngeld, Helm) | ✅ | — | ✅ | — | — |
| Zeiten & Strafen eingeben | ✅ | — | — | ✅ | — |
| Klassen-Status setzen (start/pause) | ✅ | ✅ | — | — | — |
| Zeiten / Strafen korrigieren | ✅ | ✅ (Audit-Pflicht) | — | — | — |
| Klasse freigeben (`official`) | ✅ | ✅ | — | — | — |
| Ergebnisse, Livetiming lesen | ✅ | ✅ | ✅ | ✅ | ✅ |

> **Audit-Pflicht:** Jede Schiedsrichter-Korrektur erfordert eine `reason`-Begründung. Ohne diese lehnt die API die Änderung mit HTTP 422 ab.

---

## 7. Audit-Log

### `AuditLog`

Revisionssichere Protokollierung aller Korrekturen. Wird **nie gelöscht** — auch wenn das zugehörige Ergebnis entfernt wird (`result_id → NULL`).

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `result_id` | INTEGER FK → RaceResults SET NULL | NULL wenn Ergebnis gelöscht |
| `user_id` | INTEGER FK → Users SET NULL | |
| `field_changed` | TEXT NOT NULL | `"raw_time"` · `"status"` · `"penalty"` · `"is_official"` |
| `old_value` | TEXT | Wert vor der Änderung |
| `new_value` | TEXT | Wert nach der Änderung |
| `reason` | TEXT NOT NULL | Pflichtbegründung |
| `timestamp` | TEXT | ISO-8601-Timestamp |

---

## 8. Mannschaftswertung

### `Teams`

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `event_id` | INTEGER FK → Events CASCADE | |
| `name` | TEXT NOT NULL | z.B. `"MSC Braach I"` |
| `club` | TEXT | Vereinsname (Freitext) |

> UNIQUE: `(event_id, name)`

### `TeamMembers`

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `team_id` | INTEGER FK → Teams CASCADE | |
| `participant_id` | INTEGER FK → Participants CASCADE | |

> Bis zu 4 Mitglieder pro Team, beste 3 kommen in die Wertung.  
> UNIQUE: `(team_id, participant_id)`

---

## 9. Sponsoren & Einstellungen

### `Sponsors`

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `name` | TEXT NOT NULL | Firmenname |
| `logo_url` | TEXT | URL zum Logo-Bild |
| `website_url` | TEXT | Klick-Ziel auf der Landingpage |
| `sort_order` | INTEGER DEFAULT 0 | Anzeigereihenfolge |
| `is_active` | INTEGER DEFAULT 1 | 0 = ausgeblendet |
| `created_at` | TEXT | ISO-8601-Timestamp |

### `Settings`

Key-Value-Tabelle für Systemkonfiguration (Druckvorlagen-Texte etc.).

| Spalte | Typ | Beschreibung |
|---|---|---|
| `key` | TEXT PRIMARY KEY | Einstellungsname |
| `value` | TEXT NOT NULL DEFAULT `''` | Wert |

**Vordefinierte Keys:**

| Key | Standardwert |
|---|---|
| `organizer_name` | `"MSC Braach e.V. im ADAC"` |
| `organizer_address` | `""` |
| `insurance_notice` | Versicherungstext ADAC |
| `parent_consent_text` | Einverständnistext für Minderjährige |

---

## 10. Views (berechnete Ergebnisse)

### `v_run_results`

Vollständiges Laufergebnis inkl. berechneter Strafzeit.

| Spalte | Beschreibung |
|---|---|
| `result_id`, `event_id`, `class_id`, `class_name` | Identifikation |
| `run_number` | Laufnummer |
| `participant_id` | ID des Teilnehmers (für Queue-Logik in der Zeitnahme) |
| `start_number`, `first_name`, `last_name`, `club` | Fahrer-Info |
| `raw_time`, `status`, `is_official` | Rohzeitwerte |
| `total_penalties` | Summe aller Strafsekunden (COALESCE → 0.0) |
| `total_time` | `raw_time + total_penalties` · NULL bei DNS/DNF/DSQ |

> **Hinweis:** Alle drei Views (`v_run_results`, `v_class_standings_sum_all`, `v_fastest_of_day`) werden in `schema.sql` mit `DROP VIEW IF EXISTS` + `CREATE VIEW` erzeugt (nicht `CREATE VIEW IF NOT EXISTS`), damit Schema-Änderungen beim Neustart des Backends immer wirksam werden.

### `v_class_standings_sum_all`

Gesamtwertung pro Klasse (Scoring-Typ `sum_all`).

| Spalte | Beschreibung |
|---|---|
| `event_id`, `class_id`, `class_name` | |
| `start_number`, `first_name`, `last_name`, `club` | |
| `valid_runs` | Anzahl gültiger Wertungsläufe (run_number > 0) |
| `total_time` | Summe aller `total_time` gültiger Läufe |
| `rank` | RANK() OVER (PARTITION BY class_id ORDER BY total_time NULLS LAST) |

> Training (run_number = 0) wird in beiden Views aus der Wertung ausgeschlossen.

### `v_fastest_of_day`

Schnellste Einzellaufzeit je Fahrer pro Veranstaltung (für Tagesschnellsten-Auswertung).

### `v_training_standings`

Wertung pro Trainings-Session: Rang, Bestzeit, Durchschnitt, Laufanzahl — GROUP BY `(session_id, trainee_id)`.

### Statistics-Endpoint (`GET /api/events/{id}/statistics`)

Kein dedizierter View — die Abfrage läuft direkt gegen `v_run_results` JOIN `Participants`:
- `fastest_per_class` — MIN(`total_time`) pro `class_id`, nur `run_number > 0`
- `fastest_dame` — MIN(`total_time`) über alle Klassen für Teilnehmer mit `gender = 'w'`
- `fastest_herr` — MIN(`total_time`) über alle Klassen für Teilnehmer mit `gender = 'm'`

---

## 11. SQLite-Besonderheiten

| Thema | Detail |
|---|---|
| WAL-Modus | `PRAGMA journal_mode=WAL` — parallele Lese-/Schreibzugriffe (50+ WS-Clients) |
| Foreign Keys | `PRAGMA foreign_keys=ON` — muss bei jeder Verbindung gesetzt werden |
| `REAL` für Zeiten | 64-bit IEEE 754 Float — ausreichend für Slalomzeiten (±0,001 s bis ~999 s) |
| `BOOLEAN` | SQLite speichert als `0`/`1` — in FastAPI/Pydantic als `bool` abgebildet |
| `DATETIME` | Als ISO-8601-String `"2026-06-01T09:30:00"` gespeichert |
| AuditLog | Kein CASCADE DELETE — gelöschte Ergebnisse bleiben im Log erhalten (`result_id → NULL`) |
| Migrationen | `database.py` wendet `ALTER TABLE`-Statements automatisch beim Start an (verlustfrei) |
