# Projekt-Agenda: "RaceControl Pro"
**Konzept:** Modulare Veranstaltungssoftware für Kart-Slalom (JKS & KS2000)
**Zielgruppe:** ADAC Hessen-Thüringen (ca. 10 Klassen / 300 Starter)
**Status:** Konsolidiertes Gesamtkonzept (Inkl. Datenbank-Architektur)

---

## 1. System-Architektur & Infrastruktur
- [ ] **Server-Setup:** Lokaler Python/FastAPI Server auf Basis von SQLite (Offline-First).
- [ ] **Netzwerk:** Konfiguration eines lokalen WLAN-Access-Points ohne Internetzwang.
- [ ] **Tech-Stack:** * Backend: Python (FastAPI).
    * Frontend: Vue.js/React mit Tailwind CSS (Responsive).
    * Kommunikation: WebSockets für Echtzeit-Updates.

## 2. Benutzer- & Rollenverwaltung
- [ ] **Admin:** Vollzugriff auf System, Datenbank-Backups und Reglement-Editor.
- [ ] **Schiedsrichter:** Korrekturberechtigung (Audit-Log), Veto-Recht und offizielle Ergebnis-Freigabe.
- [ ] **Nennung:** Check-in, Stammdatenpflege und technischer Abnahme-Status.
- [ ] **Zeitnahme:** Tastatur-optimierte Schnelleingabe für Zeiten und Strafen.
- [ ] **Gast/Viewer:** Schreibgeschütztes, hoch-responsives Livetiming für mobile Endgeräte.

## 3. Dynamische Reglement-Engine
- [ ] **Serien-Verwaltung:** Profile für JKS, KS2000 und freie Clubmeisterschaften.
- [ ] **Regel-Konfigurator:** Dynamische Definition von Strafwerten (z.B. Pylone +2s vs. +3s).
- [ ] **Wertungslogik:** Einstellbare Modi (Summe der Läufe, Streichergebnisse, Meisterschaftspunkte-Formeln).
- [ ] **UI-Adaption:** Zeitnahme-Interface passt seine Buttons automatisch an das gewählte Reglement an.

## 4. Workflow & Zeitnahme (Core)
- [ ] **Speed-Entry Interface:** Fokus auf Ziffernblock-Bedienung (Eingabe ohne Maus).
- [ ] **Klassen-Management:** Status-Tracker für 10 Klassen (Geplant -> Läuft -> Vorläufig -> Offiziell).
- [ ] **Sicherheits-Features:** * Automatisches Audit-Log für jede manuelle Korrektur.
    * Undo-Funktion für die Zeitnahme bei Fehltriggerung.

## 5. Responsive Frontend & Livetiming
- [ ] **Desktop-Ansicht:** Fokus auf Datendichte für Zeitnahme und Admin (hoher Kontrast).
- [ ] **Tablet-Ansicht:** Touch-optimierte Oberflächen für Schiedsrichter und Vorstart (große Targets).
- [ ] **Mobile-First Livetiming:** Card-basiertes Layout für Zuschauer (optimiert für Smartphones).
- [ ] **PWA-Support:** Offline-Indikator bei WLAN-Abbruch.

## 6. PDF-Reporting & Export (ADAC-Standard)
- [ ] **Ergebnislisten:** Automatischer Export nach ADAC Hessen-Thüringen Standard.
- [ ] **Automatisierung:** Zeitstempel-Logik für Einspruchsfristen ("Aushang um: ...").
- [ ] **Listen-Seriendruck:** Ein-Klick-Druck für Starterlisten, Sprecherlisten und Urkunden.

## 7. Datenbank-Design & Datenmodell
- [ ] **Reglement-Tabellen:** Struktur für `Reglements` und `PenaltyDefinitions` (dynamische Strafen).
- [ ] **Teilnehmer-Management:** `Participants` Tabelle mit automatischem Klassen-Mapping via Geburtsjahr.
- [ ] **Ergebnis-Architektur:** `RaceResults` mit Trennung von Rohzeit und Strafsekunden.
- [ ] **Audit-Logging:** `AuditLog` Tabelle zur revisionssicheren Protokollierung aller Schiedsrichter-Eingriffe.

## 8. Qualitätssicherung & Test
- [ ] **Stresstest:** Simulation von 300 Datensätzen und simultanen Zugriffen (50+ Gast-Clients).
- [ ] **Datensicherheit:** Implementierung automatischer Zwischenspeicherung bei jedem "Enter".