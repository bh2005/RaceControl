-- ============================================================
-- Migration: KS2000 Fehlerpunkte auf Reglement-Stand
-- Quelle: ADAC-HTH-Jugendkart-Reglement-2026.pdf, Seite 27
-- Ausführen:
--   sudo sqlite3 data/racecontrol.db < backend/migrate_ks2000_penalties.sql
-- ============================================================

PRAGMA foreign_keys = ON;

-- 1. Punkteformel (KS2000-Punkte Platz 1-35, danach je 1 Punkt)
UPDATE Reglements
SET points_formula = '{"1":40,"2":37,"3":35,"4":33,"5":31,"6":30,"7":29,"8":28,"9":27,"10":26,"11":25,"12":24,"13":23,"14":22,"15":21,"16":20,"17":19,"18":18,"19":17,"20":16,"21":15,"22":14,"23":13,"24":12,"25":11,"26":10,"27":9,"28":8,"29":7,"30":6,"31":5,"32":4,"33":3,"34":2,"35":1}'
WHERE name = 'KS2000';

-- 2. Bestehende Labels auf Reglement-Wortlaut anpassen
UPDATE PenaltyDefinitions
SET label = 'Pylone umwerfen/verschieben', shortcut_key = 'P', seconds = 3.0, sort_order = 10
WHERE reglement_id = (SELECT id FROM Reglements WHERE name = 'KS2000')
  AND label IN ('Pylone', 'Pylone umwerfen/verschieben');

UPDATE PenaltyDefinitions
SET label = 'Pylonentor auslassen', shortcut_key = 'T', seconds = 10.0, sort_order = 20
WHERE reglement_id = (SELECT id FROM Reglements WHERE name = 'KS2000')
  AND label IN ('Auslassen Tor', 'Pylonentor', 'Pylonentor auslassen');

UPDATE PenaltyDefinitions
SET label = 'Gasse auslassen', shortcut_key = 'G', seconds = 15.0, sort_order = 40
WHERE reglement_id = (SELECT id FROM Reglements WHERE name = 'KS2000')
  AND label IN ('Auslassen Gasse', 'Gasse – nicht korrekt durchf.', 'Gasse auslassen');

UPDATE PenaltyDefinitions
SET label = 'Unkorrektes Verhalten gegenüber Veranstalter', shortcut_key = 'U', seconds = 20.0, sort_order = 99
WHERE reglement_id = (SELECT id FROM Reglements WHERE name = 'KS2000')
  AND label IN ('Unkorektes Verhalten', 'Unkorrektes Verhalten', 'Unkorrektes Verhalten gegenüber Veranstalter');

-- 3. Fehlende Strafarten ergänzen (INSERT OR IGNORE via UNIQUE-Constraint)
--    Trick: temporär UNIQUE auf (reglement_id, label) durch Unterabfrage prüfen

INSERT INTO PenaltyDefinitions (reglement_id, label, seconds, shortcut_key, sort_order)
SELECT r.id, 'Schweizer Kreuz (Aufgabe) auslassen', 10.0, 'S', 30
FROM Reglements r
WHERE r.name = 'KS2000'
  AND NOT EXISTS (
      SELECT 1 FROM PenaltyDefinitions p
      WHERE p.reglement_id = r.id
        AND p.label = 'Schweizer Kreuz (Aufgabe) auslassen'
  );

INSERT INTO PenaltyDefinitions (reglement_id, label, seconds, shortcut_key, sort_order)
SELECT r.id, 'Begrenzungslinie überschreiten / Klötzchen', 3.0, 'B', 50
FROM Reglements r
WHERE r.name = 'KS2000'
  AND NOT EXISTS (
      SELECT 1 FROM PenaltyDefinitions p
      WHERE p.reglement_id = r.id
        AND p.label = 'Begrenzungslinie überschreiten / Klötzchen'
  );

INSERT INTO PenaltyDefinitions (reglement_id, label, seconds, shortcut_key, sort_order)
SELECT r.id, 'Falsche Fahrtrichtung nach Zieldurchfahrt', 10.0, 'F', 60
FROM Reglements r
WHERE r.name = 'KS2000'
  AND NOT EXISTS (
      SELECT 1 FROM PenaltyDefinitions p
      WHERE p.reglement_id = r.id
        AND p.label = 'Falsche Fahrtrichtung nach Zieldurchfahrt'
  );

-- 4. Veralteten Eintrag entfernen (war in alten Versionen drin, redundant zu "Pylone")
DELETE FROM PenaltyDefinitions
WHERE reglement_id = (SELECT id FROM Reglements WHERE name = 'KS2000')
  AND label IN ('Gasse – Pylone', 'Haltelinie – nicht angehalten', 'Falsches Anfahren / Fahrtrichtung');

-- Ergebnis anzeigen
SELECT 'KS2000 Strafarten nach Migration:' AS info;
SELECT pd.sort_order, pd.shortcut_key, pd.seconds, pd.label
FROM PenaltyDefinitions pd
JOIN Reglements r ON r.id = pd.reglement_id
WHERE r.name = 'KS2000'
ORDER BY pd.sort_order;

SELECT 'points_formula gesetzt: ' || CASE WHEN points_formula IS NOT NULL THEN 'JA' ELSE 'NEIN' END AS pf_status
FROM Reglements WHERE name = 'KS2000';
