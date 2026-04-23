# RaceControl Pro – Funktionsübersicht

Stand: April 2026

---

## Öffentliche Bereiche (kein Login erforderlich)

### Landingpage `/`
- Zeigt Veranstaltungsname, Datum und Ort
- Veranstaltungsbeschreibung/Infotexte (vom Admin pflegbar)
- Live-Statusanzeige aller Klassen (geplant / läuft / unterbrochen / vorläufig / offiziell)
- Vorschau der aktuellen Zwischenwertung (laufende oder zuletzt beendete Klasse)
- Teilnehmerstatistik (Gemeldet / Abgenommen)
- Sponsorenbereich mit Logos und Website-Links
- Links zu Livetiming und Online-Nennung
- Automatische Aktualisierung alle 15 Sekunden

### Livetiming `/livetiming`
- Ergebnisse aller Klassen in Echtzeit
- Wechsel zwischen Klassen und Läufen
- Tabellarische Darstellung mit Rang, Startnummer, Name, Verein, Zeit, Strafen

### Online-Nennung `/nennen`
- Selbstanmeldung vor Ort über Tablet/Smartphone
- Felder: Vorname, Nachname, Jahrgang, Verein, Lizenznummer, Klasse
- Automatischer Klassenvorschlag anhand des Jahrgangs
- Duplikatprüfung (nach Lizenznummer oder Name + Jahrgang)
- Bestätigungsscreen mit Startnummer (falls bereits vergeben)

---

## Nennbüro `/nennung`

### Teilnehmerverwaltung
- Vollständige Teilnehmerliste mit Filter (Klasse, Status, Name/Startnummer)
- Statusworkflow: Gemeldet → Eingecheckt → Freigegeben
- Abnahme: Nenngeld bezahlt (€) und Helmkontrolle (🪖) einzeln abhakbar
- Freigabe (→ Starterliste) nur wenn beide Abnahmen bestätigt
- Nachnennung direkt im Nennbüro
- Inline-Bearbeitung aller Teilnehmerdaten

### Startnummernvergabe
- Dedizierter Modus „🎲 Startnummern vergeben" nach der Auslosung
- Eingabe der ausgelosten Startnummern direkt in der Tabelle
- Speicherung mit Enter oder Fokusverlust

### Nennungsschluss
- Pro Klasse: Nennungsschluss setzen (= 30 min vor Startzeit)
- Startzeit der Klasse wird gleichzeitig eingetragen
- Anzeige im Klassen-Status-Panel

### Statistiken
- Übersicht: Gesamt, Ohne Startnummer, Freigegeben, Startklar, Nenngeld offen, Helm ausstehend

### Drucken
- Nennliste drucken (alle Klassen, je eine Seite)
- Spalten: Lfd. Nr. / Startnr. / Name / Verein / Jahrgang / Nenngeld / Helm / Unterschrift
- Enthält Versicherungshinweis und Einverständniserklärung für Erziehungsberechtigte
- Konfigurierbare Texte (Veranstalter, Adresse, Versicherungstext, Einverständniserklärung)

---

## Zeitnahme `/zeitnahme`

### Zeiteingabe
- Klassenwahl und Laufwahl (Training / Lauf 1 / Lauf 2)
- Großes Zeitfeld mit numerischer Eingabe
- Bestätigung mit Enter oder Button
- Sonderstatus: DNS / DNF / DSQ per Button

### Startliste & Vorziehen
- Automatische Queue nach Startnummer (offene Fahrer zuerst)
- Aktueller Fahrer prominent hervorgehoben
- Nächste 6 Starter in der Warteschlange sichtbar
- **Vorziehen**: beliebigen Fahrer per Knopfdruck an die erste Position setzen
- Manuelle Reihenfolge zurücksetzen möglich
- Automatischer Reset bei Klassen- oder Laufwechsel

### Strafen
- Strafbuttons aus dem Reglement (konfigurierbar)
- Tastaturkürzel pro Strafe (z.B. „P" für Pylone)
- Mehrfache Strafen summieren automatisch
- Echtzeit-Anzeige: Strafzeit + Rohzeit = Gesamtzeit

### Ergebnisse
- Laufergebnisse der aktuellen Klasse in der rechten Spalte
- Klassen-Statusanzeige aller Klassen

### Undo
- Letzten Eintrag rückgängig machen (Undo-Stack)

---

## Schiedsrichter `/schiedsrichter`

### Klassen-Steuerung
- Klasse starten (→ läuft)
- Klasse unterbrechen / pausieren (→ unterbrochen)
- Klasse fortsetzen (→ läuft)
- Klasse beenden mit Einspruchfrist-Start (→ vorläufig)
- Klasse offiziell freigeben (→ offiziell)

### Einspruchfrist-Timer
- 30-Minuten-Countdown nach Klassenende
- Visueller Countdown in Echtzeit
- „Freigeben"-Button aktiv nach Ablauf der Frist
- Frühzeitige Freigabe trotzdem möglich (mit Warnanzeige)

### Ergebniskorrekturen
- Zeitkorrektur mit Pflichtfeld „Begründung"
- Statuskorrektur (valid / DNS / DNF / DSQ)
- Audit-Log aller Korrekturen (Feld, Alter Wert, Neuer Wert, Begründung, Zeitstempel)

---

## Admin `/admin`

### Veranstaltungen
- Anlegen, Bearbeiten, Löschen von Veranstaltungen
- Felder: Name, Datum, Ort, Status, Beschreibung/Infotexte
- Klassenverwaltung pro Veranstaltung (Name, Kürzel, Jahrgangsgrenzen, Reglement, Startreihenfolge)
- Status-Steuerung der Klassen (auch Pause/Fortsetzen) direkt im Admin

### Vereine
- Vereinsstammdaten: Name, Kurzname, Ort
- Anlegen, Bearbeiten, Löschen

### Benutzer
- Benutzerverwaltung: Benutzername, Passwort, Rolle, Anzeigename
- Rollen: admin, nennung, zeitnahme, schiedsrichter, viewer

### Sponsoren
- Sponsorenverwaltung: Name, Logo-URL, Website-URL, Reihenfolge, Aktiv/Inaktiv
- Live-Vorschau des Logos beim Bearbeiten
- Aktive Sponsoren erscheinen auf der öffentlichen Landingpage

### System
- Druckvorlage konfigurieren: Veranstalter, Adresse, Versicherungshinweis, Einverständniserklärung
- Hinweise zu Druckereinstellungen und Elternunterschrift

---

## Reglementverwaltung

- Reglemente mit Scoring-Typ (sum_all, best_of, sum_minus_worst)
- Anzahl Läufe, Training ja/nein
- Straf-Definitionen pro Reglement (Label, Sekunden, Tastaturkürzel)

---

## Technisches

- Automatische Datenbank-Migration beim Start (verlustfrei)
- WAL-Modus für gleichzeitige Lese-/Schreibzugriffe
- JWT-Authentifizierung (HS256)
- Rollenbasierte Zugangskontrolle (Frontend + Backend)
- Audit-Log für alle Zeitkorrekturen
- Responsive Design (Tablet-optimiert für Nennbüro und Zeitnahme)
