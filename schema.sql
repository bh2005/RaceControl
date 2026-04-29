-- ============================================================
-- RaceControl Pro – SQLite Schema
-- Version: 0.1.0
-- ============================================================

PRAGMA journal_mode = WAL;       -- simultane Lese-/Schreibzugriffe (50+ WS-Clients)
PRAGMA foreign_keys = ON;        -- FK-Constraints erzwingen
PRAGMA encoding = 'UTF-8';

-- ============================================================
-- 1. REGLEMENT-ENGINE
-- ============================================================

CREATE TABLE IF NOT EXISTS Reglements (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL UNIQUE,           -- z.B. "ADAC JKS 2026"
    scoring_type    TEXT    NOT NULL                   -- "sum_all" | "best_of" | "sum_minus_worst"
                    CHECK (scoring_type IN ('sum_all', 'best_of', 'sum_minus_worst')),
    points_formula  TEXT,                              -- JSON-Formel oder Name der Punktetabelle (optional)
    runs_per_class  INTEGER NOT NULL DEFAULT 2,        -- Anzahl Wertungsläufe (ohne Training)
    has_training    INTEGER NOT NULL DEFAULT 1         -- 1 = Trainingslauf vorgesehen
                    CHECK (has_training IN (0, 1)),
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
);

CREATE TABLE IF NOT EXISTS PenaltyDefinitions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    reglement_id    INTEGER NOT NULL REFERENCES Reglements(id) ON DELETE CASCADE,
    label           TEXT    NOT NULL,                  -- z.B. "Pylone", "Torfehler"
    seconds         REAL    NOT NULL CHECK (seconds >= 0),
    shortcut_key    TEXT,                              -- Einzeltaste für Zeitnahme-UI (z.B. 'P')
    sort_order      INTEGER NOT NULL DEFAULT 0,        -- Reihenfolge in der UI
    UNIQUE (reglement_id, shortcut_key)               -- keine doppelten Tasten pro Reglement
);

-- ============================================================
-- 2. VERANSTALTUNGEN & KLASSEN
-- ============================================================

CREATE TABLE IF NOT EXISTS Events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,                  -- z.B. "ADAC Kart-Slalom Kassel 2026-06-01"
    date            TEXT    NOT NULL,                  -- ISO-8601: "2026-06-01"
    location        TEXT,
    reglement_id    INTEGER REFERENCES Reglements(id) ON DELETE SET NULL,
    status          TEXT    NOT NULL DEFAULT 'planned'
                    CHECK (status IN ('planned', 'active', 'finished', 'official')),
    description     TEXT,                              -- Infoseite: Freitext/HTML
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
);

CREATE TABLE IF NOT EXISTS Classes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        INTEGER NOT NULL REFERENCES Events(id) ON DELETE CASCADE,
    reglement_id    INTEGER REFERENCES Reglements(id) ON DELETE SET NULL,
    name            TEXT    NOT NULL,                  -- z.B. "Schüler A", "Junioren"
    short_name      TEXT,                              -- Kürzel für Ausdrucke, z.B. "SA"
    min_birth_year  INTEGER,                           -- Untergrenze Geburtsjahr (inklusiv)
    max_birth_year  INTEGER,                           -- Obergrenze Geburtsjahr (inklusiv)
    run_status              TEXT    NOT NULL DEFAULT 'planned'
                            CHECK (run_status IN ('planned', 'running', 'paused', 'preliminary', 'official')),
    start_order             INTEGER NOT NULL DEFAULT 0, -- Reihenfolge im Tagesablauf
    registration_closed_at  TEXT,                       -- Zeitpunkt Nennungsschluss (ISO-8601)
    start_time              TEXT,                       -- geplante/tatsächliche Startzeit "HH:MM"
    end_time                TEXT,                       -- Zeitpunkt Klassenende → löst Einspruchfrist aus
    is_exhibition           INTEGER NOT NULL DEFAULT 0  -- 1 = Vorstarter/Showklasse, kein run_status-Check
                            CHECK (is_exhibition IN (0, 1)),
    UNIQUE (event_id, name)
);

-- ============================================================
-- 3. BENUTZER & ROLLEN
-- ============================================================

CREATE TABLE IF NOT EXISTS Users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT    NOT NULL UNIQUE,
    password_hash   TEXT    NOT NULL,                  -- bcrypt-Hash
    role            TEXT    NOT NULL
                    CHECK (role IN ('admin', 'schiedsrichter', 'nennung', 'zeitnahme', 'marshal', 'viewer')),
    display_name    TEXT,                              -- z.B. "Hans Müller (SRI)"
    is_active       INTEGER NOT NULL DEFAULT 1
                    CHECK (is_active IN (0, 1)),
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
);

-- Standard-Admin (Passwort beim ersten Start setzen)
INSERT OR IGNORE INTO Users (username, password_hash, role, display_name)
VALUES ('admin', '__CHANGE_ON_FIRST_LOGIN__', 'admin', 'Administrator');

-- ============================================================
-- 4. SPONSOREN
-- ============================================================

CREATE TABLE IF NOT EXISTS Sponsors (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    logo_url    TEXT,                              -- URL zum Sponsor-Logo
    website_url TEXT,                              -- Klick-Ziel
    sort_order  INTEGER NOT NULL DEFAULT 0,
    is_active   INTEGER NOT NULL DEFAULT 1
                CHECK (is_active IN (0, 1)),
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
);

-- ============================================================
-- 5. VEREINS-STAMMDATEN
-- ============================================================

CREATE TABLE IF NOT EXISTS Clubs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL UNIQUE,           -- z.B. "MSC Braach e.V. im ADAC"
    short_name      TEXT,                              -- Kürzel, z.B. "MSC Braach"
    city            TEXT,                              -- Ort (optional)
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
);

-- ============================================================
-- 5a. TRAININGS-STAMMDATEN (Jugendliche)
-- ============================================================

-- Persistente Jugendlichen-Datenbank, unabhängig von Veranstaltungen
CREATE TABLE IF NOT EXISTS Trainees (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name      TEXT    NOT NULL,
    last_name       TEXT    NOT NULL,
    birth_year      INTEGER,
    license_number  TEXT,                              -- ADAC-Lizenznummer (optional)
    club_id         INTEGER REFERENCES Clubs(id) ON DELETE SET NULL,
    kart_number     TEXT,                              -- Standard-Kart-Nummer (kann je Session überschrieben werden)
    is_active       INTEGER NOT NULL DEFAULT 1
                    CHECK (is_active IN (0, 1)),
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_trainees_club ON Trainees (club_id);
CREATE INDEX IF NOT EXISTS idx_trainees_active ON Trainees (is_active);

-- ============================================================
-- 5b. TRAINING-SESSIONS & LÄUFE
-- ============================================================

CREATE TABLE IF NOT EXISTS TrainingSessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,                  -- z.B. "Donnerstagstraining 29.04.2026"
    date        TEXT    NOT NULL,                  -- ISO-8601 "YYYY-MM-DD"
    status      TEXT    NOT NULL DEFAULT 'planned'
                CHECK (status IN ('planned', 'active', 'finished')),
    notes       TEXT,
    created_by  INTEGER REFERENCES Users(id) ON DELETE SET NULL,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
);

CREATE TABLE IF NOT EXISTS TrainingRuns (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      INTEGER NOT NULL REFERENCES TrainingSessions(id) ON DELETE CASCADE,
    trainee_id      INTEGER NOT NULL REFERENCES Trainees(id) ON DELETE CASCADE,
    kart_number     TEXT,                          -- überschreibt Trainees.kart_number für diesen Lauf
    run_number      INTEGER NOT NULL DEFAULT 1,    -- Laufzähler pro Fahrer/Session
    raw_time        REAL,                          -- gestoppte Zeit in Sekunden; NULL bei DNS/DNF
    penalty_seconds REAL    NOT NULL DEFAULT 0,    -- Summierte Strafzeit (vereinfacht für Training)
    status          TEXT    NOT NULL DEFAULT 'valid'
                    CHECK (status IN ('valid', 'dns', 'dnf', 'dsq')),
    source          TEXT    NOT NULL DEFAULT 'manual'
                    CHECK (source IN ('manual', 'lichtschranke')),
    entered_by      INTEGER REFERENCES Users(id) ON DELETE SET NULL,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now')),
    UNIQUE (session_id, trainee_id, run_number)
);

CREATE INDEX IF NOT EXISTS idx_training_runs_session  ON TrainingRuns (session_id);
CREATE INDEX IF NOT EXISTS idx_training_runs_trainee  ON TrainingRuns (trainee_id);

DROP VIEW IF EXISTS v_training_standings;
CREATE VIEW v_training_standings AS
SELECT
    r.session_id,
    t.id                                            AS trainee_id,
    t.first_name,
    t.last_name,
    t.kart_number                                   AS default_kart,
    COALESCE(cl.short_name, cl.name)                AS club_name,
    COUNT(*)                                        AS run_count,
    MIN(CASE WHEN r.status = 'valid' AND r.raw_time IS NOT NULL
             THEN r.raw_time + r.penalty_seconds END)  AS best_time,
    AVG(CASE WHEN r.status = 'valid' AND r.raw_time IS NOT NULL
             THEN r.raw_time + r.penalty_seconds END)  AS avg_time
FROM   TrainingRuns r
JOIN   Trainees t  ON t.id  = r.trainee_id
LEFT JOIN Clubs cl ON cl.id = t.club_id
GROUP BY r.session_id, r.trainee_id;

-- ============================================================
-- 5. TEILNEHMER
-- ============================================================

CREATE TABLE IF NOT EXISTS Participants (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        INTEGER NOT NULL REFERENCES Events(id) ON DELETE CASCADE,
    class_id        INTEGER REFERENCES Classes(id) ON DELETE SET NULL,
    club_id         INTEGER REFERENCES Clubs(id) ON DELETE SET NULL,  -- NULL = "n.N."
    start_number    INTEGER,                            -- NULL bis zur Auslosung
    first_name      TEXT    NOT NULL,
    last_name       TEXT    NOT NULL,
    birth_year      INTEGER,                           -- für automatisches Klassen-Mapping
    license_number  TEXT,                              -- ADAC-Lizenznummer (optional)
    status          TEXT    NOT NULL DEFAULT 'registered'
                    CHECK (status IN ('registered', 'checked_in', 'technical_ok', 'disqualified')),
    gender          TEXT    CHECK (gender IN ('m', 'w')),  -- m=männlich, w=weiblich
    fee_paid        INTEGER NOT NULL DEFAULT 0
                    CHECK (fee_paid IN (0, 1)),        -- Nenngeld bezahlt
    helmet_ok       INTEGER NOT NULL DEFAULT 0
                    CHECK (helmet_ok IN (0, 1)),       -- Helmkontrolle bestanden
    UNIQUE (class_id, start_number)                    -- Startnummer eindeutig pro Klasse
);

-- ============================================================
-- 5. ERGEBNISSE & STRAFEN
-- ============================================================

CREATE TABLE IF NOT EXISTS RaceResults (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        INTEGER NOT NULL REFERENCES Events(id) ON DELETE CASCADE,
    participant_id  INTEGER NOT NULL REFERENCES Participants(id) ON DELETE CASCADE,
    class_id        INTEGER NOT NULL REFERENCES Classes(id) ON DELETE CASCADE,
    run_number      INTEGER NOT NULL CHECK (run_number >= 0),  -- 0=Training, 1=Lauf1, 2=Lauf2
    raw_time        REAL,                              -- gestoppte Zeit in Sekunden; NULL bei DNS/DNF
    status          TEXT    NOT NULL DEFAULT 'valid'
                    CHECK (status IN ('valid', 'dns', 'dnf', 'dsq')),
    is_official     INTEGER NOT NULL DEFAULT 0
                    CHECK (is_official IN (0, 1)),
    entered_by      INTEGER REFERENCES Users(id) ON DELETE SET NULL,
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now')),
    UNIQUE (participant_id, class_id, run_number)     -- ein Ergebnis pro Fahrer/Lauf
);

-- total_penalties wird NICHT gespeichert — immer berechnet:
-- SELECT SUM(pd.seconds * rp.count)
-- FROM RunPenalties rp
-- JOIN PenaltyDefinitions pd ON pd.id = rp.penalty_definition_id
-- WHERE rp.result_id = <id>

CREATE TABLE IF NOT EXISTS RunPenalties (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id               INTEGER NOT NULL REFERENCES RaceResults(id) ON DELETE CASCADE,
    penalty_definition_id   INTEGER NOT NULL REFERENCES PenaltyDefinitions(id) ON DELETE RESTRICT,
    count                   INTEGER NOT NULL DEFAULT 1 CHECK (count > 0),
    entered_by              INTEGER REFERENCES Users(id) ON DELETE SET NULL,
    created_at              TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
);

-- ============================================================
-- 6. AUDIT-LOG
-- ============================================================

CREATE TABLE IF NOT EXISTS AuditLog (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id       INTEGER REFERENCES RaceResults(id) ON DELETE SET NULL,
    user_id         INTEGER REFERENCES Users(id) ON DELETE SET NULL,
    field_changed   TEXT    NOT NULL,                  -- "raw_time" | "status" | "penalty" | "is_official"
    old_value       TEXT,                              -- JSON-serialisierter Wert vor der Änderung
    new_value       TEXT,                              -- JSON-serialisierter Wert nach der Änderung
    reason          TEXT    NOT NULL,                  -- Pflichtfeld: Begründung der Änderung
    timestamp       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
);

-- AuditLog wird NIE gelöscht (kein CASCADE DELETE von außen)
-- Gelöschte Ergebnisse → result_id wird NULL (SET NULL), Eintrag bleibt erhalten

-- ============================================================
-- 7. MANNSCHAFTSWERTUNG
-- ============================================================

CREATE TABLE IF NOT EXISTS Teams (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        INTEGER NOT NULL REFERENCES Events(id) ON DELETE CASCADE,
    name            TEXT    NOT NULL,                  -- z.B. "MSC Braach I"
    club            TEXT,
    UNIQUE (event_id, name)
);

-- Bis zu 4 Mitglieder pro Mannschaft; beste 3 kommen in die Wertung
CREATE TABLE IF NOT EXISTS TeamMembers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id         INTEGER NOT NULL REFERENCES Teams(id) ON DELETE CASCADE,
    participant_id  INTEGER NOT NULL REFERENCES Participants(id) ON DELETE CASCADE,
    UNIQUE (team_id, participant_id)
);

-- ============================================================
-- 8. SYSTEMEINSTELLUNGEN
-- ============================================================

CREATE TABLE IF NOT EXISTS Settings (
    key     TEXT PRIMARY KEY,
    value   TEXT NOT NULL DEFAULT ''
);

-- Standardwerte (INSERT OR IGNORE: bestehende Werte bleiben erhalten)
INSERT OR IGNORE INTO Settings (key, value) VALUES ('organizer_name',    'MSC Braach e.V. im ADAC');
INSERT OR IGNORE INTO Settings (key, value) VALUES ('organizer_address', '');
INSERT OR IGNORE INTO Settings (key, value) VALUES ('insurance_notice',  'Alle Teilnehmer sind über den ADAC-Motorsport im Rahmen der ADAC-Sportversicherung versichert. Diese Versicherung gilt nur für Unfälle, die in unmittelbarem Zusammenhang mit der Veranstaltung entstehen.');
INSERT OR IGNORE INTO Settings (key, value) VALUES ('parent_consent_text', 'Ich bin mit der Teilnahme meines Kindes an dieser Veranstaltung einverstanden und bestätige die Richtigkeit aller Angaben.');

-- ============================================================
-- 9. STRECKENPOSTEN-LOG
-- ============================================================



CREATE TABLE IF NOT EXISTS MarshalReports (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        INTEGER REFERENCES Events(id) ON DELETE CASCADE,
    ts              TEXT    NOT NULL,
    station         TEXT    NOT NULL,
    marshal_user    TEXT    NOT NULL,
    penalty_seconds REAL    NOT NULL,
    penalty_label   TEXT,
    class_id        INTEGER REFERENCES Classes(id) ON DELETE SET NULL,
    class_name      TEXT,
    cancelled       INTEGER NOT NULL DEFAULT 0 CHECK (cancelled IN (0, 1)),
    cancelled_at    TEXT,
    cancelled_by    TEXT
);

-- ============================================================
-- 10. SYSTEM-LOG
-- ============================================================

CREATE TABLE IF NOT EXISTS SystemLog (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    level       TEXT    NOT NULL DEFAULT 'info'
                CHECK (level IN ('info', 'warn', 'error')),
    event_type  TEXT    NOT NULL,   -- 'login_ok' | 'login_fail' | 'server_start' | 'user_created'
    username    TEXT,               -- betroffener Benutzername (falls bekannt)
    detail      TEXT,               -- Freitext-Detail
    ip          TEXT                -- Client-IP-Adresse
);

-- ============================================================
-- 11. INDIZES
-- ============================================================

-- Schnelle Ergebnisabfragen pro Klasse / Veranstaltung
CREATE INDEX IF NOT EXISTS idx_results_event     ON RaceResults (event_id);
CREATE INDEX IF NOT EXISTS idx_results_class     ON RaceResults (class_id);
CREATE INDEX IF NOT EXISTS idx_results_participant ON RaceResults (participant_id);

-- Schnelle Strafenabfragen pro Ergebnis
CREATE INDEX IF NOT EXISTS idx_penalties_result  ON RunPenalties (result_id);

-- Audit-Log schnell nach Ergebnis und Zeit durchsuchen
CREATE INDEX IF NOT EXISTS idx_audit_result        ON AuditLog (result_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp     ON AuditLog (timestamp);

-- Streckenposten-Log schnell nach Veranstaltung abfragen
CREATE INDEX IF NOT EXISTS idx_marshal_reports_event ON MarshalReports (event_id);

-- System-Log chronologisch
CREATE INDEX IF NOT EXISTS idx_system_log_ts ON SystemLog (ts);

-- Teilnehmersuche nach Name / Startnummer
CREATE INDEX IF NOT EXISTS idx_participants_event        ON Participants (event_id);
CREATE INDEX IF NOT EXISTS idx_participants_start_number ON Participants (class_id, start_number);

-- Mannschaftswertung
CREATE INDEX IF NOT EXISTS idx_team_members_team        ON TeamMembers (team_id);
CREATE INDEX IF NOT EXISTS idx_team_members_participant ON TeamMembers (participant_id);

-- ============================================================
-- 8. VIEWS (berechnete Ergebnisse)
-- ============================================================

-- Vollständiges Ergebnis pro Lauf inkl. berechneter Strafzeit
DROP VIEW IF EXISTS v_run_results;
CREATE VIEW v_run_results AS
SELECT
    r.id                AS result_id,
    r.event_id,
    r.class_id,
    c.name              AS class_name,
    r.run_number,
    p.id                AS participant_id,
    p.start_number,
    p.first_name,
    p.last_name,
    COALESCE(cl.short_name, cl.name, 'n.N.') AS club,
    r.raw_time,
    r.status,
    r.is_official,
    COALESCE((
        SELECT SUM(pd.seconds * rp.count)
        FROM   RunPenalties rp
        JOIN   PenaltyDefinitions pd ON pd.id = rp.penalty_definition_id
        WHERE  rp.result_id = r.id
    ), 0.0)             AS total_penalties,
    CASE
        WHEN r.status != 'valid' OR r.raw_time IS NULL THEN NULL
        ELSE r.raw_time + COALESCE((
            SELECT SUM(pd.seconds * rp.count)
            FROM   RunPenalties rp
            JOIN   PenaltyDefinitions pd ON pd.id = rp.penalty_definition_id
            WHERE  rp.result_id = r.id
        ), 0.0)
    END                 AS total_time
FROM       RaceResults r
JOIN       Participants p  ON p.id  = r.participant_id
JOIN       Classes      c  ON c.id  = r.class_id
LEFT JOIN  Clubs        cl ON cl.id = p.club_id;

-- Gesamtwertung pro Klasse (scoring_type "sum_all")
DROP VIEW IF EXISTS v_class_standings_sum_all;
CREATE VIEW v_class_standings_sum_all AS
SELECT
    r.event_id,
    r.class_id,
    c.name              AS class_name,
    p.start_number,
    p.first_name,
    p.last_name,
    COALESCE(cl.short_name, cl.name, 'n.N.') AS club,
    COUNT(CASE WHEN r.status = 'valid' AND r.run_number > 0 THEN 1 END) AS valid_runs,
    SUM(CASE WHEN r.status = 'valid' AND r.run_number > 0
             THEN r.raw_time + COALESCE((
                 SELECT SUM(pd.seconds * rp.count)
                 FROM   RunPenalties rp
                 JOIN   PenaltyDefinitions pd ON pd.id = rp.penalty_definition_id
                 WHERE  rp.result_id = r.id
             ), 0.0)
             ELSE NULL END)  AS total_time,
    RANK() OVER (
        PARTITION BY r.class_id
        ORDER BY SUM(CASE WHEN r.status = 'valid' AND r.run_number > 0
                          THEN r.raw_time + COALESCE((
                              SELECT SUM(pd.seconds * rp.count)
                              FROM   RunPenalties rp
                              JOIN   PenaltyDefinitions pd ON pd.id = rp.penalty_definition_id
                              WHERE  rp.result_id = r.id
                          ), 0.0)
                          ELSE 9999 END) NULLS LAST
    )                   AS rank
FROM       RaceResults r
JOIN       Participants p  ON p.id  = r.participant_id
JOIN       Classes      c  ON c.id  = r.class_id
LEFT JOIN  Clubs        cl ON cl.id = p.club_id
WHERE      r.run_number > 0                            -- Training ausschließen
GROUP BY   r.event_id, r.class_id, r.participant_id;

-- Tagesschnellste/r: schnellste Einzellaufzeit je Veranstaltung + Reglement-Gruppe
-- Gibt pro Fahrer die beste Einzellaufzeit zurück (nicht Gesamtsumme).
-- Gefiltert nach event_id + reglement_id in der Applikationsschicht.
DROP VIEW IF EXISTS v_fastest_of_day;
CREATE VIEW v_fastest_of_day AS
SELECT
    r.event_id,
    c.reglement_id,
    reg.name            AS reglement_name,
    p.id                AS participant_id,
    p.start_number,
    p.first_name,
    p.last_name,
    COALESCE(cl.short_name, cl.name, 'n.N.') AS club,
    c.id                AS class_id,
    c.name              AS class_name,
    r.run_number,
    r.raw_time + COALESCE((
        SELECT SUM(pd.seconds * rp.count)
        FROM   RunPenalties rp
        JOIN   PenaltyDefinitions pd ON pd.id = rp.penalty_definition_id
        WHERE  rp.result_id = r.id
    ), 0.0)             AS run_time
FROM       RaceResults r
JOIN       Participants p   ON p.id   = r.participant_id
JOIN       Classes      c   ON c.id   = r.class_id
JOIN       Reglements   reg ON reg.id  = c.reglement_id
LEFT JOIN  Clubs        cl  ON cl.id   = p.club_id
WHERE      r.run_number > 0
  AND      r.status = 'valid'
  AND      r.raw_time IS NOT NULL;
