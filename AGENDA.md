# Projekt-Agenda: "RaceControl Pro"
**Konzept:** Modulare Veranstaltungssoftware für Kart-Slalom (JKS & KS2000)  
**Zielgruppe:** ADAC Hessen-Thüringen (ca. 10 Klassen / 300 Starter)  
**Stand:** April 2026

---

## Status-Legende
- ✅ Fertig
- ⚠️ Teilweise / Grundversion vorhanden
- ❌ Noch offen

---

## 1. System-Architektur & Infrastruktur
- ✅ **Server-Setup:** Python/FastAPI + SQLite (WAL-Modus, Offline-First)
- ⚠️ **Netzwerk:** CORS für lokales WLAN konfiguriert; Setup-Anleitung in README.md – kein dedizierter AP-Konfigurator
- ✅ **Tech-Stack:** Backend FastAPI, Frontend Vue 3 + Tailwind CSS, Axios
- ❌ **WebSockets:** Aktuell Polling (15 s auf der Landingpage) – kein echter WebSocket-Push

## 2. Benutzer- & Rollenverwaltung
- ✅ **Admin:** Vollzugriff, Veranstaltungen, Klassen, Vereine, Benutzer, Sponsoren, System
- ✅ **Schiedsrichter:** Korrekturberechtigung, Audit-Log, Klassensteuerung, Einspruchfrist
- ✅ **Nennung:** Check-in, Abnahme (Nenngeld + Helm), Nennungsschluss, Drucken
- ✅ **Zeitnahme:** Tastaturoptimierte Eingabe, Strafen, DNS/DNF/DSQ, Undo, Vorziehen
- ✅ **Gast/Viewer:** Landingpage, Livetiming (kein Login erforderlich)

## 3. Dynamische Reglement-Engine
- ✅ **Serien-Verwaltung:** Reglements-Tabelle (JKS, KS2000, freie Meisterschaften)
- ✅ **Regel-Konfigurator:** PenaltyDefinitions pro Reglement (Label, Sekunden, Tastenkürzel)
- ✅ **Wertungslogik:** sum_all, best_of, sum_minus_worst
- ✅ **UI-Adaption:** Zeitnahme lädt Strafbuttons automatisch aus dem Reglement der gewählten Klasse

## 4. Workflow & Zeitnahme (Core)
- ✅ **Speed-Entry Interface:** Zifferneingabe, Enter-Bestätigung, Tastaturkürzel für Strafen
- ✅ **Klassen-Management:** geplant → läuft → unterbrochen → vorläufig → offiziell
- ✅ **Klasse pausieren/fortsetzen:** Unterbrechung und Wiederaufnahme (Schiri + Admin)
- ✅ **Vorziehen:** Fahrer in der Warteschlange an Position 1 setzen (manuelle Queue-Steuerung)
- ✅ **Audit-Log:** Revisionssichere Protokollierung aller Korrekturen
- ✅ **Undo:** Letzten Zeiteintrag rückgängig machen

## 5. Responsive Frontend & Livetiming
- ✅ **Desktop-Ansicht:** Datendichte für Zeitnahme und Admin
- ✅ **Tablet-Ansicht:** Touch-optimiert für Nennbüro und Schiedsrichter
- ✅ **Mobile-First Livetiming:** Dunkles Card-Layout, Sponsorenbereich, Klassenstatus
- ❌ **PWA-Support:** Service Worker, Offline-Indikator – noch nicht implementiert

## 6. Reporting & Export
- ⚠️ **Nennliste drucken:** HTML-Druck mit Unterschriftsfeld, Versicherungshinweis und Einverständniserklärung – fertig
- ❌ **Ergebnisliste PDF:** Export im ADAC Hessen-Thüringen Standardformat – offen
- ❌ **Sprecherliste:** Ausdruck mit Startnummer, Name, Verein, Klasse für den Hallensprecher – offen
- ❌ **Urkunden:** Seriendruckvorlage für Platziertenurkunden – offen
- ⚠️ **Einspruchsfrist-Zeitstempel:** 30-Minuten-Timer vorhanden; „Aushang um: …"-Text für den Ausdruck fehlt noch

## 7. Datenbank-Design & Datenmodell
- ✅ **Reglement-Tabellen:** `Reglements`, `PenaltyDefinitions`
- ✅ **Teilnehmer-Management:** `Participants` mit Jahrgangsmapping, nullable Startnummer
- ✅ **Ergebnis-Architektur:** `RaceResults` + `RunPenalties` (Rohzeit und Strafen getrennt)
- ✅ **Audit-Logging:** `AuditLog` mit Pflichtbegründung
- ✅ **Sponsoren:** `Sponsors` mit Logo-URL, Sortierung, Aktiv-Flag
- ✅ **Systemeinstellungen:** `Settings` (Key-Value für Druckvorlagen-Texte)
- ✅ **Mannschaftswertung:** `Teams`, `TeamMembers` (bis 4 Mitglieder, beste 3 gewertet)
- ✅ **Automatische Migrationen:** Bestehende DBs werden verlustfrei auf den aktuellen Stand gebracht

## 8. Qualitätssicherung & Test
- ❌ **Stresstest:** Simulation mit 300 Datensätzen und 50+ simultanen Clients – noch nicht durchgeführt
- ✅ **Datensicherheit:** Sofortige Persistenz bei jeder Eingabe (kein Datenverlust bei WLAN-Abbruch)
- ❌ **Automatisierte Tests:** Unit-/Integrationstests für Backend und Frontend – noch nicht vorhanden

---

## Offene Punkte – Zusammenfassung

| Priorität | Thema | Aufwand |
|-----------|-------|---------|
| 🔴 Hoch | PDF-Export Ergebnisliste (ADAC-Format) | mittel |
| 🔴 Hoch | Sprecherliste drucken | klein |
| 🟡 Mittel | WebSockets (Echtzeit-Push statt Polling) | groß |
| 🟡 Mittel | Einspruchsfrist-Aushang-Text auf Ausdruck | klein |
| 🟢 Nice-to-have | PWA / Offline-Indikator | mittel |
| 🟢 Nice-to-have | Urkunden-Seriendruck | mittel |
| 🟢 Nice-to-have | Automatisierte Tests | groß |
