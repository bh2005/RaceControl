# Projekt-Agenda: "RaceControl Pro"
**Konzept:** Modulare Veranstaltungssoftware für Kart-Slalom (JKS & KS2000)  
**Zielgruppe:** ADAC Hessen-Thüringen (ca. 10 Klassen / 300 Starter)  
**Stand:** April 2026 (v0.6.2)

---

## Status-Legende
- ✅ Fertig
- ⚠️ Teilweise / Grundversion vorhanden
- ❌ Noch offen

---

## 1. System-Architektur & Infrastruktur
- ✅ **Server-Setup:** Python/FastAPI + SQLite (WAL-Modus, Offline-First)
- ✅ **Netzwerk:** CORS für lokales WLAN konfiguriert; alle Geräte erreichbar über `http://<Laptop-IP>:1980`
- ✅ **Tech-Stack:** Backend FastAPI, Frontend Vue 3 + Tailwind CSS, Axios
- ✅ **WebSockets:** Echter Push via BroadcastManager; Livetiming und Landingpage reagieren sofort auf neue Ergebnisse und Statuswechsel
- ✅ **Veranstaltungstag-Deployment:** `npm run build` einmalig → FastAPI liefert gebautes Frontend direkt aus; kein Node.js am Veranstaltungstag erforderlich
- ✅ **API-Routing:** Einheitliches `/api`-Präfix für alle Endpunkte (Dev-Proxy und Produktion konsistent)

## 2. Benutzer- & Rollenverwaltung
- ✅ **Admin:** Vollzugriff, Veranstaltungen, Klassen, Vereine, Benutzer, Sponsoren, System
- ✅ **Schiedsrichter:** Korrekturberechtigung, Audit-Log, Klassensteuerung, Einspruchfrist, Drucken
- ✅ **Nennung:** Check-in, Abnahme (Nenngeld + Helm), Nennungsschluss, Drucken
- ✅ **Zeitnahme:** Tastaturoptimierte Eingabe, Strafen, DNS/DNF/DSQ, Undo, Vorziehen
- ✅ **Streckenposten (marshal):** Mobile-optimierte Meldungserfassung, Storno, History
- ✅ **Sprecher/Viewer:** Sprecher-Dashboard, Nachrichten-Board, Livetiming (kein Login für Livetiming erforderlich)

## 3. Dynamische Reglement-Engine
- ✅ **Serien-Verwaltung:** Reglements-Tabelle (JKS, KS2000, freie Meisterschaften)
- ✅ **Regel-Konfigurator:** PenaltyDefinitions pro Reglement (Label, Sekunden, Tastenkürzel)
- ✅ **Wertungslogik:** sum_all, best_of, sum_minus_worst
- ✅ **UI-Adaption:** Zeitnahme lädt Strafbuttons automatisch aus dem Reglement der gewählten Klasse

## 4. Workflow & Zeitnahme (Core)
- ✅ **Speed-Entry Interface:** Zifferneingabe, Enter-Bestätigung, Tastaturkürzel für Strafen
- ✅ **Klassen-Management:** geplant → läuft → unterbrochen → vorläufig → offiziell
- ✅ **Klasse pausieren/fortsetzen:** Unterbrechung und Wiederaufnahme (Schiri + Admin)
- ✅ **Auto-Klassenabschluss:** Automatisch auf „vorläufig" wenn alle Teilnehmer alle Läufe absolviert haben
- ✅ **Vorziehen:** Fahrer in der Warteschlange an Position 1 setzen (manuelle Queue-Steuerung)
- ✅ **Zufällige Startnummernvergabe:** Fisher-Yates-Shuffle beim Auto-Nummerieren
- ✅ **Audit-Log:** Revisionssichere Protokollierung aller Korrekturen
- ✅ **Undo:** Letzten Zeiteintrag rückgängig machen
- ✅ **Streckenposten-Integration:** Meldungsempfang in Zeitnahme (WS + DB-Fallback), Übernahme in Strafzeit

## 5. Responsive Frontend & Livetiming
- ✅ **Desktop-Ansicht:** Datendichte für Zeitnahme und Admin
- ✅ **Tablet-Ansicht:** Touch-optimiert für Nennbüro und Schiedsrichter
- ✅ **Mobile-First Livetiming:** Dunkles Card-Layout, Sponsorenbereich, Klassenstatus
- ✅ **Trainingszeiten im Livetiming:** Werden angezeigt solange noch keine Wertungsläufe vorhanden
- ✅ **PWA-Support:** Service Worker (Workbox), Offline-Caching für Standings und Public-API, Web App Manifest, "Zum Startbildschirm hinzufügen"
- ✅ **Offline-Indikator:** Amber-Banner erscheint automatisch bei Netzwerkausfall (alle Views)

## 6. Reporting & Export
- ✅ **Nennliste drucken:** HTML-Druck mit Unterschriftsfeld, Versicherungshinweis, Einverständniserklärung
- ✅ **Offizielles Nennungsformular:** 2-seitiger ADAC-Ausdruck pro Teilnehmer (Nennungsformular + Haftungsausschluss); verfügbar sobald Lizenz + Helm + Nenngeld OK
- ✅ **Ergebnisliste drucken:** A4 quer, ADAC-Format mit Fahrzeit / Fehlerpunkte / Lauf-Gesamt pro Lauf, Jahrgang, Summe, Differenz, Einspruchfrist-Zeitstempel, Schiedsrichter-Unterschriftszeile
- ✅ **Sprecherliste drucken:** A4 hoch, alle Teilnehmer nach Klasse sortiert mit Startnummer, Name, Verein, Jahrgang, Notiz-Spalte
- ✅ **Einspruchsfrist-Zeitstempel:** 30-Minuten-Timer ab Klassenende; „bis: HH:MM Uhr" auf der Ergebnisliste
- ❌ **Urkunden:** Seriendruckvorlage für Platziertenurkunden – offen

## 7. Datenbank-Design & Datenmodell
- ✅ **Reglement-Tabellen:** `Reglements`, `PenaltyDefinitions`
- ✅ **Teilnehmer-Management:** `Participants` mit Jahrgangsmapping, nullable Startnummer, `gender`-Feld (m/w)
- ✅ **Ergebnis-Architektur:** `RaceResults` + `RunPenalties` (Rohzeit und Strafen getrennt)
- ✅ **Audit-Logging:** `AuditLog` mit Pflichtbegründung
- ✅ **Streckenposten-Log:** `MarshalReports` mit Storno-Tracking (cancelled, cancelled_at, cancelled_by)
- ✅ **System-Log:** `SystemLog` (Login-Events, Server-Start, User-Erstellung, Level info/warn/error)
- ✅ **Sponsoren:** `Sponsors` mit Logo-URL, Sortierung, Aktiv-Flag
- ✅ **Systemeinstellungen:** `Settings` (Key-Value für Druckvorlagen-Texte)
- ✅ **Mannschaftswertung:** `Teams`, `TeamMembers` (bis 4 Mitglieder, beste 3 gewertet)
- ✅ **Trainings-Datenmodell:** `Trainees`, `TrainingSessions`, `TrainingRuns`, View `v_training_standings`
- ✅ **Automatische Migrationen:** Bestehende DBs werden verlustfrei auf den aktuellen Stand gebracht

## 8. Sprecher-Dashboard & Ereignis-Log
- ✅ **3-spaltiges Layout:** Aktueller Fahrer | Zeitanalyse + Wertung | Ereignis-Log
- ✅ **Ereignis-Log:** Echtzeit-Protokoll für Streckenposten-Meldungen, Klassen-Statusänderungen, Ankündigungen (📢 Nennungsschluss etc.)
- ✅ **DB-Vorladung:** Letzte Marshal-Meldungen werden beim Öffnen aus der DB geladen
- ✅ **Trainingsanzeige:** Trainingszeiten und -queue werden korrekt angezeigt (manueller Override bleibt erhalten)
- ✅ **Zeitanalyse:** Was braucht der Fahrer für Platz 1 / Top 3 / Top 10? Pylonen-Budget

## 9. Qualitätssicherung & Test
- ❌ **Stresstest:** Simulation mit 300 Datensätzen und 50+ simultanen Clients – noch nicht durchgeführt
- ✅ **Datensicherheit:** Sofortige Persistenz bei jeder Eingabe (kein Datenverlust bei WLAN-Abbruch)
- ✅ **Automatisierte Tests:** pytest-Integrationstests (auth, events, participants, results, public, marshal, auto-close, admin-logs — 105 Tests); Vitest-Tests für useNetworkStatus und useRealtimeUpdate; GitHub Actions CI/CD
- ✅ **Admin Test-Tab:** API Verbindungscheck + Testdaten-Seeder (Reglement, Klassen, Teilnehmer) mit Progress-Log
- ✅ **GPL-2.0 Lizenzseite:** `/lizenz`-Route mit Projektinfo, Bibliotheken-Übersicht, Link auf gnu.org; GPL-Link in StatusBar

---

## 10. Trainingsmodus & Auswertung
- ✅ **Trainees:** Persistente Jugendlichen-Datenbank (CRUD, Verein, Kart-Nummer, Aktiv-Flag)
- ✅ **TrainingSessions:** Anlegen, aktivieren (Single-Active-Lock), beenden
- ✅ **TrainingRuns:** Zeiterfassung mit Auto-Increment run_number, WS-Broadcast, Löschen
- ✅ **TrainingView:** 3-spaltiges Layout (Fahrerliste / Zeitnahme / Wertung)
- ✅ **Lichtschranke im Training:** timing_result auto-befüllt Zeitfeld
- ✅ **Auswertungsseite:** Schnellste pro Klasse + Schnellste Dame + Schnellster Herr
- ✅ **gender-Feld:** Participants.gender (m/w/NULL) inkl. Migration und Formular-UI

---

## Offene Punkte – Zusammenfassung

| Priorität | Thema | Aufwand |
|-----------|-------|---------|
| 🟡 Mittel | Urkunden-Seriendruck | mittel |
| ~~🟡 Mittel~~ | ~~CSV/Excel-Export der Ergebnisse~~ | ~~mittel~~ |
| 🟡 Mittel | pytest-Tests für Trainings-Endpunkte (trainees, training) | mittel |
| ~~🟡 Mittel~~ | ~~pytest-Tests für neue Endpunkte (marshal, admin_logs, auto-close)~~ | ~~mittel~~ |
| 🟢 Nice-to-have | Stresstest (300 Starter, 50 Clients) | groß |
| ~~🟢 Nice-to-have~~ | ~~Automatisierte Tests~~ | ~~groß~~ |
