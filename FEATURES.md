# RaceControl Pro – Funktionsübersicht

Stand: April 2026 · Version 0.6.2

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
- Lauf-Detailzeilen pro Fahrer: Rohzeit + Strafzeit für jeden Lauf (z.B. `Lauf 1  56.13 +12.0s = 68.13`); Strafzeit immer sichtbar (grau bei 0.0 s)

### Dokumente `/dokumente`
- Öffentlich zugängliche Seite für Reglemente, Formulare und Vorlagen
- Dateien werden aus dem `assets/`-Ordner des Servers geladen
- Gruppiert nach Kategorie (Reglemente, Vorlagen & Formulare, Sonstiges)
- Direkter Download bzw. Öffnen im Browser (PDF, Bilder, Dokumente)
- Dateigröße wird angezeigt

### Online-Nennung `/nennen`
- Selbstanmeldung vor Ort über Tablet/Smartphone
- Felder: Vorname, Nachname, Jahrgang, Geschlecht, Verein, Lizenznummer, Klasse
- Automatischer Klassenvorschlag anhand des Jahrgangs
- Duplikatprüfung (nach Lizenznummer oder Name + Jahrgang)
- Bestätigungsscreen mit Startnummer (falls bereits vergeben)

---

## Nennbüro `/nennung`

### Teilnehmerverwaltung
- Vollständige Teilnehmerliste mit Filter (Klasse, Status, Name/Startnummer)
- **Sortierung:** Status (Gemeldet → Eingecheckt → Freigegeben → DSQ), dann Klasse, Jahrgang, Nachname
- Statusworkflow: Gemeldet → Eingecheckt → Freigegeben
- Abnahme: Nenngeld bezahlt (€) und Helmkontrolle (🪖) einzeln abhakbar
- Freigabe (→ Starterliste) nur wenn beide Abnahmen bestätigt
- Nachnennung direkt im Nennbüro
- Inline-Bearbeitung aller Teilnehmerdaten
- **Geschlecht** (m/w/nicht angegeben) — Pflichtfeld für Dame/Herr-Auswertung

### Startnummernvergabe
- Dedizierter Modus „🎲 Startnummern vergeben" nach der Auslosung
- Eingabe der ausgelosten Startnummern direkt in der Tabelle
- Speicherung mit Enter oder Fokusverlust
- **Startnummern pro Klasse**: jede Klasse beginnt bei 1 (nicht mehr eindeutig pro Veranstaltung)
- **„🎲 Auto ab 1"** Button pro Klasse: vergibt 1, 2, 3 … alphabetisch nach Nachname automatisch

### Nennungsschluss
- Pro Klasse: Nennungsschluss setzen (= 30 min vor Startzeit)
- Startzeit der Klasse wird gleichzeitig eingetragen
- Anzeige im Klassen-Status-Panel
- **Push-Benachrichtigung** beim Setzen: alle verbundenen Clients erhalten sofort eine Ankündigung
  („Klasse X: Auslosung der Startnummern in 5 Minuten an der Nennung!")
- „Ankündigung wiederholen"-Button wenn Nennungsschluss bereits gesetzt

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
- Klassenwahl; Lauf wird automatisch erkannt (Training → Lauf 1 → Lauf 2)
- Großes Zeitfeld mit numerischer Eingabe
- Komma als Dezimaltrennzeichen akzeptiert (56,13 = 56.13 s)
- Bestätigung mit Enter oder Button
- Sonderstatus: DNS / DNF / DSQ per Button

### Automatische Lauf-Erkennung
- System erkennt anhand vorhandener Ergebnisse selbstständig den aktuellen Lauf
- Sequenz: Training → Lauf 1 → Lauf 2 (sobald alle Fahrer einer Phase fertig sind)
- Override-Buttons für manuellen Wechsel weiterhin vorhanden

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
- Lauf-Spalte in der Ergebnistabelle (Training grau, Lauf N blau)
- Zeitkorrektur mit Pflichtfeld „Begründung"
- Statuskorrektur (valid / DNS / DNF / DSQ)
- Strafen-Korrektur für Wertungsläufe: bestehende Strafen ändern, neue hinzufügen; Live-Vorschau der Gesamtzeit
- Training: nur Rohzeit und Status korrigierbar (keine Straffelder)
- Audit-Log aller Korrekturen (Feld, Alter Wert, Neuer Wert, Begründung, Zeitstempel)

### Drucken & Export
- Ergebnisliste drucken: A4 quer, ADAC-Format, Laufdetails, Jahrgang, Summe, Differenz, Einspruchfrist-Zeitstempel, Unterschriftszeile
- Sprecherliste drucken: A4 hoch, alle Teilnehmer mit Startnummer, Name, Verein, Jahrgang, Notiz-Spalte
- **CSV/Excel-Export**: Button „📥 CSV / Excel" im Drucken-Panel; exportiert die gewählte Klasse oder alle Klassen als CSV-Datei (UTF-8 BOM, Semikolon-getrennt); öffnet direkt in Excel ohne Konvertierung

---

## Trainingsmodus `/training`

### Jugendlichen-Datenbank (Trainees)
- Persistente Fahrerdaten unabhängig von Veranstaltungen
- Felder: Vorname, Nachname, Jahrgang, Kart-Nummer, Verein, Lizenznummer, Notizen
- Aktiv/Inaktiv-Schalter (inaktive Fahrer erscheinen nicht in der Session-Liste)
- Verwaltung im Admin-Bereich (Tab „🧒 Jugendliche")

### Training-Sessions
- Sessions anlegen: Datum, Name, Status (geplant / aktiv / beendet), Notizen
- Nur eine Session gleichzeitig aktiv — andere werden automatisch beendet
- Verwaltung im Admin-Bereich (Tab „🏋 Training")

### Zeitnahme im Training
- Fahrer-Auswahl aus der Jugendlichen-Datenbank
- Großes Zeitfeld: `45.32` oder `45,32` (Komma/Punkt akzeptiert)
- Lichtschranke füllt Zeitfeld automatisch (grüner Flash)
- Straf-Schnelltasten: Pylone +3s, Tor +10s, Gasse +15s, Linie +3s
- Sonderstatus: DNS / DNF / DSQ
- Läufe löschen aus der History-Tabelle
- run_number automatisch hochgezählt pro Fahrer/Session

### Wertung & Statistik
- Session-Wertung in Echtzeit (Rang, Bestzeit, Durchschnitt, Laufanzahl)
- WS-Broadcast bei neuem Lauf → alle Clients aktualisieren sofort
- View `v_training_standings` (SQLite)

---

## Auswertung `/auswertung`

- Zugänglich für alle angemeldeten Rollen (im „Mehr"-Dropdown)
- Veranstaltungs-Selektor (Standard: aktive Veranstaltung)
- **Schnellste Wertungsläufe pro Klasse** — Tabelle: Klasse · # · Name · Verein · Lauf · Bestzeit
- **Schnellste Dame** — Kachel mit Zeit, Name, Klasse, Verein (nur wenn Geschlecht = 'w' hinterlegt)
- **Schnellster Herr** — Kachel mit Zeit, Name, Klasse, Verein (nur wenn Geschlecht = 'm' hinterlegt)
- Nur Wertungsläufe (run_number > 0) — keine Trainingsläufe in der Auswertung
- API: `GET /api/events/{id}/statistics` (kein Login erforderlich)
- **CSV/Excel-Export**: Button „📥 CSV / Excel" im Header; exportiert alle Klassen der gewählten Veranstaltung als CSV

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
- Rollen: admin, nennung, zeitnahme, schiedsrichter, marshal, viewer

### Sponsoren
- Sponsorenverwaltung: Name, Logo-URL, Website-URL, Reihenfolge, Aktiv/Inaktiv
- Live-Vorschau des Logos beim Bearbeiten
- Aktive Sponsoren erscheinen auf der öffentlichen Landingpage

### Jugendliche / Training
- Tab „🧒 Jugendliche": Trainings-Stammdaten verwalten (Anlegen, Bearbeiten, Suche, Aktiv-Filter)
- Tab „🏋 Training": Sessions anlegen und aktivieren (Datum, Name, Status, Notizen)

### Reglements-Vorlagen
- **KS 2000 Preset**: Ein-Klick-Anlage des KS-2000-Reglements mit allen offiziellen Strafen
  (Pylone 3 s, Tore 10 s, Gasse 15 s, Linie/Klötzchen 3 s, Fahrtrichtung 10 s, Verhalten 20 s)

### Logs
- Vollständige Log-Ansicht über drei Bereiche in einem Tab:
  - **Streckenposten-Meldungen**: alle `MarshalReports` der Veranstaltung, inkl. Storno-Status
  - **Zeitkorrekturen (Audit-Log)**: jede Korrektur mit Feld, Alter/Neuer Wert, Begründung, Zeitstempel
  - **System-Log**: Server-Start, Login-Ereignisse (OK/Fehlschlag, IP-Adresse), User-Erstellung
- Filter nach Veranstaltung; Echtzeit-Aktualisierung per Button

### Test
- Nur für `admin`-Rolle sichtbar
- **API-Verbindungscheck**: testet ob Backend erreichbar ist
- **Testdaten-Seeder**: legt Reglement, Klassen und Teilnehmer per Klick an; Progress-Log zeigt jeden Schritt

### System
- Druckvorlage konfigurieren: Veranstalter, Adresse, Versicherungshinweis, Einverständniserklärung
- Hinweise zu Druckereinstellungen und Elternunterschrift
- **Spendenhinweis**: PayPal-Links für Bernd und Anke Holzhauer zur Unterstützung der Weiterentwicklung
  und der Jugend-Gruppe des MSC Braach e.V. im ADAC

---

## Reglementverwaltung

- Reglemente mit Scoring-Typ (sum_all, best_of, sum_minus_worst)
- Anzahl Läufe, Training ja/nein
- Straf-Definitionen pro Reglement (Label, Sekunden, Tastaturkürzel)

---

## Lichtschranken-Integration

### Raspberry Pi (`RaPi_lichtschranke/`)

- Zwei GPIO-Lichtschranken (Start GPIO 17, Stop GPIO 27, Reset GPIO 22)
- **Client TM1637**: 7-Segment-Anzeige über I²C (CLK GPIO 21, DIO GPIO 20)
- **Client MAX7219**: LED-Matrix-Anzeige über SPI (CLK GPIO 11, MOSI GPIO 10, CS GPIO 8)
- Standalone-Testskripte ohne Backend (TM1637 und MAX7219)
- Offline-Betrieb: Messung lokal, Zeit auf Display, Senden wenn Backend verfügbar
- Auto-Reconnect nach Verbindungsabbruch (3 s)
- systemd-Autostart-Unit für Produktionsbetrieb
- Konfiguration: `BACKEND_HOST`, `BACKEND_PORT`, `MIN_TIME`

### ELV LSU200 (`tools/lsu200_client.py`)

- USB-Anbindung der ELV LSU200 Lichtschranke (virtueller COM-Port)
- **Läuft auf dem gleichen Laptop wie das Backend** — kein Raspberry Pi nötig
- Automatische COM-Port-Erkennung anhand USB-VID/PID
- Baudrate 19200 Baud (fest nach LSU200-Protokoll)
- Konfiguration: `SERIAL_PORT` (None = auto-detect), `BACKEND_WS`, `MIN_TIME`
- Abhängigkeiten: `pyserial`, `websocket-client`
- COM-Port ermitteln: Gerätemanager → Anschlüsse (COM & LPT)

---

## Streckenposten `/marshal`

- Eigene Rolle `marshal`, Login leitet direkt zur Streckenposten-Ansicht
- Mobile-optimiertes Layout (dunkler Hintergrund, große Buttons – für Smartphone am Posten)
- **Posten-Bezeichnung** einstellbar (z.B. „Posten 2"), wird im localStorage gespeichert
- Klassen-Selector zeigt nur laufende Klassen
- Einfaches Zahlen-Eingabefeld (Fehlerpunkte in Sekunden) + „Senden"-Button
- Grünes „Gesendet ✓"-Flash nach jeder Meldung
- Log der zuletzt gesendeten Meldungen am unteren Rand
- Meldungen werden per WebSocket-Broadcast (`marshal_penalty`) an alle Clients gesendet
- **Zeitnahme** empfängt Meldungen als gelbes Panel über den Straf-Buttons:
  „Übernehmen" → Strafe wird direkt zur aktiven Zeiteingabe hinzugefügt
  „✕" → Meldung verwerfen; Auto-Dismiss nach 60 Sekunden
- Nur Meldungen der aktuell in der Zeitnahme gewählten Klasse werden angezeigt
- Mehrere Streckenposten (4–5) können gleichzeitig verbunden sein

---

## Navigation

- **Live-Uhr** in der TopBar (sekundengenau, tabular-nums Darstellung)
- Rollenbasierte Navigation: nur für die eigene Rolle relevante Menüpunkte sichtbar
- **„Mehr ▾"-Dropdown** in der TopBar: sekundäre Links (Livetiming, Auswertung, Sprecher, Nachrichten,
  Streckenposten, Dokumente, Online-Nennung) ausgeblendet, damit die Bar nicht überfüllt wird;
  Dropdown zeigt fett wenn eine enthaltene Seite aktiv ist
- **Push-Benachrichtigungen** als globales cyan Banner (alle Views, 30 s, schließbar)

## Docker-Deployment

- **Multi-Stage Dockerfile**: Node 22 baut das Frontend, Python 3.12-slim führt das Backend aus
- Ein einziger Container enthält Frontend + Backend + alle API-Endpunkte
- `docker compose up --build` startet das gesamte System ohne Python- oder Node-Installation
- **Volumes**: `./data/` für die SQLite-DB, `./assets/` für Dokumente — beide persistent
- `SECRET_KEY` per Umgebungsvariable (`.env`-Datei)
- Healthcheck auf `/health` eingebaut
- Pfade (DB, Assets) über `DATA_DIR` / `ASSETS_DIR` Env-Vars konfigurierbar

## Windows-Installer

- **Kein Admin-Setup nötig**: Installation in `%LocalAppData%\Programs\RaceControl Pro` ohne Administrator-Rechte
- **PyInstaller-Bundle** (`Windows/racecontrol.spec`): packt Python 3.12, FastAPI, uvicorn und alle Abhängigkeiten
  in ein einziges `racecontrol.exe` — kein Python auf dem Ziel-PC erforderlich
- **Inno Setup Installer** (`Windows/installer.iss`): professioneller Ein-Klick-Installer mit Start-Menü-Eintrag,
  optionaler Desktop-Verknüpfung und Autostart-Option; erzeugt `RaceControl-Pro-Setup-0.6.1.exe`
- **Launcher** (`Windows/launcher.py`): startet den Server im Hintergrund, öffnet Browser automatisch sobald
  Port 1980 antwortet; optionales System-Tray-Icon (pystray + Pillow) mit „Öffnen / Beenden"
- **Build-Skript** (`Windows/build.ps1`): automatisiert den kompletten Build-Ablauf in einem Schritt
  (`npm run build` → PyInstaller → Inno Setup); einzelne Schritte überspringbar
- **Datenpersistenz**: `data\` (SQLite-DB) und `assets\` (Dokumente) liegen neben der `.exe` im Installationsordner

---

## Technisches

- Automatische Datenbank-Migration beim Start (verlustfrei)
- WAL-Modus für gleichzeitige Lese-/Schreibzugriffe
- JWT-Authentifizierung (HS256)
- Rollenbasierte Zugangskontrolle (Frontend + Backend)
- Audit-Log für alle Zeitkorrekturen
- Responsive Design (Tablet-optimiert für Nennbüro und Zeitnahme)
- Docker-ready: Single-Container-Deployment per `docker compose up`
