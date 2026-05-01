# RaceControl Pro – Handbuch

**MSC Braach e.V. im ADAC**  
Stand: Mai 2026 · Version 0.7.0

---

## Inhaltsverzeichnis

1. [Systemstart](#1-systemstart)
2. [Veranstaltung vorbereiten (Admin)](#2-veranstaltung-vorbereiten-admin)
3. [Nennbüro – Anmeldung und Abnahme](#3-nennbüro--anmeldung-und-abnahme)
4. [Online-Nennung (Teilnehmer)](#4-online-nennung-teilnehmer)
5. [Zeitnahme](#5-zeitnahme)
6. [Trainingsmodus](#6-trainingsmodus)
7. [Auswertung](#7-auswertung)
8. [Schiedsrichter](#8-schiedsrichter)
9. [Nachrichten senden](#9-nachrichten-senden)
10. [Streckenposten](#10-streckenposten)
11. [Livetiming (Gäste)](#11-livetiming-gäste)
12. [Admin – Stammdaten und Einstellungen](#12-admin--stammdaten-und-einstellungen)
13. [Lichtschranken-Clients](#13-lichtschranken-clients)
14. [Downhill- und Seifenkisten-Zeitnahme](#14-downhill--und-seifenkisten-zeitnahme)
15. [Häufige Fragen und Probleme](#15-häufige-fragen-und-probleme)

---

## 1. Systemstart

### Laptop vorbereiten

1. WLAN-Hotspot aktivieren (Laptop als Zugangspunkt) **oder** Verbindung mit dem Veranstaltungs-WLAN.
2. Terminal öffnen und ins Projektverzeichnis wechseln.

---

### Option A – Docker (empfohlen)

Kein Python oder Node.js nötig – nur Docker Desktop muss installiert sein.

```bash
cd RaceControl
docker compose up -d --build
```

Beim ersten Start wird das Image gebaut (ca. 2–3 Minuten). Ab dem zweiten Mal startet es in Sekunden.
Die Datenbank und alle Dokumente bleiben in den Ordnern `data/` und `assets/` erhalten.

System stoppen:
```bash
docker compose down
```

---

### Option B – Direkt (Entwicklung / ohne Docker)

```bash
# Backend
cd RaceControl/backend
uvicorn main:app --host 0.0.0.0 --port 1980
```

Das Backend ist bereit, wenn `Application startup complete.` im Terminal erscheint.

```bash
# Frontend (nur im Entwicklungsmodus nötig)
cd RaceControl/frontend
npm run dev
```

---

### Zugriff vom Tablet / Smartphone

Die IP-Adresse des Laptops im WLAN ermitteln:

```bash
# Windows
ipconfig

# Linux/macOS
ip addr
```

Auf dem Gerät im Browser aufrufen: `http://<IP>:1980`
(im Entwicklungsmodus ohne Docker: `http://<IP>:5173`)

---

## 2. Veranstaltung vorbereiten (Admin)

### Login

1. Browser öffnen → `http://[Server-IP]:5173`
2. Auf **„Anmelden (Personal)"** klicken
3. Mit Benutzername `admin` und Passwort einloggen
4. Weiterleitung zum Admin-Bereich

### Neue Veranstaltung anlegen

1. Admin → **📅 Veranstaltungen** → **+ Neu**
2. Name, Datum, Ort und Beschreibung eingeben
3. **Anlegen** klicken

### Klassen konfigurieren

Nach dem Anlegen der Veranstaltung erscheint der Klassen-Bereich:

1. **+ Klasse** klicken für jede Klasse (z.B. Schüler A, Junioren, Einsteiger)
2. Pro Klasse ausfüllen:
   - **Name** und **Kürzel** (z.B. „SA")
   - **Jg. von / bis** (Jahrgangsgrenzen, z.B. 2015–2018)
   - **Reglement** zuweisen
   - **Reihenfolge** (Startreihenfolge der Klassen im Tagesablauf)
3. **Klassen speichern**

### Veranstaltung aktivieren

Status der Veranstaltung auf **„Aktiv"** setzen, damit sie auf der Landingpage erscheint.

---

## 3. Nennbüro – Anmeldung und Abnahme

**URL:** `/nennung` | **Rolle:** `nennung` oder `admin`

### Workflow für jeden Teilnehmer

```
Online-Voranmeldung  →  Nennbüro Check-in  →  Abnahme  →  Starterliste
     (vor Ort)              (status: checked_in)     (€ + Helm)     (status: technical_ok)
```

### Teilnehmer einchecken

> Die Liste ist sortiert nach: **Status** (Gemeldet zuerst, DSQ zuletzt) → **Klasse** → **Jahrgang** → **Nachname**

1. Teilnehmer in der Liste suchen (Suche nach Name oder Startnummer)
2. In der Zeile auf **Check-in** klicken → Status wechselt zu „Eingecheckt"
3. Nenngeld und Helm abhaken:
   - **€-Button** klicken wenn Nenngeld bezahlt
   - **🪖-Button** klicken wenn Helm kontrolliert und OK
4. Wenn beide Haken gesetzt: **Freigeben ✓** klicken → Teilnehmer ist auf der Starterliste

### Nachnennung

1. **+ Nachnennung** klicken (links unten)
2. Daten eingeben und **Speichern**
3. Startnummer wird nach der Auslosung eingetragen

### Startnummern vergeben (nach der Auslosung)

1. Modus **„🎲 Startnummern vergeben"** wählen
2. Pro Teilnehmer die ausgeloste Startnummer eingeben
3. **Enter** drücken oder außerhalb klicken → wird sofort gespeichert

> **Startnummern pro Klasse:** Jede Klasse zählt ab 1. Startnummer #1 kann in jeder Klasse einmal vergeben werden.

> **Auto-Nummerierung:** Mit **„🎲 Auto ab 1"** werden die Nummern 1, 2, 3 … alphabetisch nach Nachname automatisch vergeben. Bei bereits vorhandenen Nummern erscheint eine Bestätigungsabfrage.

### Nennungsschluss setzen

1. Im linken Panel bei der jeweiligen Klasse auf **„Nennungsschluss setzen"** klicken
2. Startzeit der Klasse eingeben (z.B. `10:30`)
3. **Bestätigen** → Nennungsschluss wird 30 Minuten davor gesetzt
4. Alle verbundenen Clients (Sprecher, Zeitnahme, Livetiming, …) erhalten automatisch
   eine Benachrichtigung: „Klasse X: Auslosung der Startnummern in 5 Minuten an der Nennung!"

> **Ankündigung wiederholen:** Falls nötig, erscheint nach dem Setzen ein Button
> **„📢 Ankündigung wiederholen"** um die Push-Meldung erneut zu senden.

### Nennliste drucken

1. **🖨 Nennliste drucken** klicken (oben rechts in der Mitte)
2. Es öffnet sich ein neues Fenster mit der druckfertigen Liste
3. Druckdialog des Browsers bestätigen

> **Hinweis Elternunterschrift:** Bei minderjährigen Fahrern muss ein Erziehungsberechtigter in der Unterschriftenspalte unterschreiben. Die Liste ist als Veranstaltungsunterlage aufzubewahren.

---

## 4. Online-Nennung (Teilnehmer)

**URL:** `/nennen` (kein Login erforderlich)

Teilnehmer können sich vor Ort selbst über ein bereitgestelltes Tablet anmelden:

1. QR-Code oder Link aufrufen
2. Vorname, Nachname, Jahrgang ausfüllen
3. Verein und Lizenznummer (optional) eintragen
4. Klasse wählen (oder automatisch vom Jahrgang vorgeschlagen)
5. **Jetzt anmelden** klicken

Das System prüft automatisch, ob der Teilnehmer bereits gemeldet ist (Duplikatcheck nach Lizenznummer und Name/Jahrgang).

---

## 5. Zeitnahme

**URL:** `/zeitnahme` | **Rolle:** `zeitnahme` oder `admin`

### Grundablauf

1. **Klasse** wählen (oben links)
2. Der aktuelle Lauf wird **automatisch erkannt** (Training → Lauf 1 → Lauf 2)
3. Der aktuelle Starter wird im blauen Block angezeigt
4. Zeit eingeben → **Enter** oder **✓ Bestätigen**
5. Der nächste Fahrer erscheint automatisch; nach dem letzten Fahrer einer Phase
   wechselt der Lauf automatisch auf den nächsten

> **Hinweis:** Über die Override-Buttons („Tr.", „L1", „L2") kann der Lauf bei Bedarf
> manuell gewechselt werden.

### Zeit eingeben

- Zahl eintippen (z.B. `45.23` oder `45,23` — Komma und Punkt werden akzeptiert)
- Strafen über die Buttons klicken (oder Tastaturkürzel)
- **Enter** bestätigt die Zeit und wechselt automatisch zum nächsten Fahrer

### Sonderstatus

| Kürzel | Bedeutung | Wann verwenden |
|--------|-----------|----------------|
| **DNS** | Nicht gestartet | Fahrer erscheint nicht zur Startlinie |
| **DNF** | Nicht gewertet | Fahrer bricht den Lauf ab oder verlässt den Kurs |
| **DSQ** | Disqualifiziert | Grober Regelverstoß im Lauf |

### Strafen

- Pro definierter Strafe gibt es einen Button (z.B. „Pylone +2.0 s")
- Mehrfachklick erhöht die Anzahl (z.B. 3 Pylonen = +6.0 s)
- Die Gesamtzeit wird sofort berechnet angezeigt
- Tastaturkürzel: Je nach Reglement z.B. `P` für Pylone

### Fahrer vorziehen

Falls ein Fahrer seine Startreihenfolge tauscht (z.B. #4 ist schon im Warmfahrparcour):

1. In der Startliste auf **↑ Vorziehen** bei dem betreffenden Fahrer klicken
2. Dieser Fahrer rückt sofort an Position 1 (nächster Starter)
3. Die restliche Reihenfolge bleibt erhalten
4. Mit **↺ Reihenfolge zurücksetzen** wieder zur Startnummern-Reihenfolge

### Streckenposten-Meldungen

Wenn Streckenposten aktiv sind, erscheinen eingehende Fehlerpunkt-Meldungen
als **gelbes Panel** über den Straf-Buttons:

- Posten-Bezeichnung, Strafname und Sekunden werden angezeigt
- **„Übernehmen"** fügt die Strafe zur aktuellen Zeiteingabe hinzu
- **„✕"** verwirft die Meldung
- Nur Meldungen der aktuell gewählten Klasse sind sichtbar

### Undo

- **↩ Undo** klicken oder **Strg+Z** drücken, um den letzten Eintrag rückgängig zu machen

---

## 6. Trainingsmodus

**URL:** `/training` | **Rolle:** `zeitnahme` oder `admin`

Der Trainingsmodus ermöglicht das Erfassen von Trainingszeiten für Jugendliche **unabhängig von einer Veranstaltung**. Jugendliche (Trainees) werden einmalig im Admin angelegt und stehen dann in jeder Session zur Verfügung.

### Vorbereitung im Admin

1. Admin → **🧒 Jugendliche** → Jugendliche anlegen (Name, Jahrgang, Kart-Nummer, Verein)
2. Admin → **🏋 Training** → Neue Session anlegen (Datum, Name)
3. Session aktivieren: Auf **▶ Aktivieren** klicken — alle anderen Sessions werden automatisch beendet

### Trainingsablauf (/training)

Die Seite besteht aus drei Bereichen:

**Linke Spalte — Fahrerwahl**
1. Gewünschte Session im Dropdown auswählen (aktive Session wird automatisch vorgewählt)
2. Fahrer in der Liste anklicken → erscheint im blauen Fahrer-Block oben
3. Suchfeld zum schnellen Finden (Name oder Kart-Nummer)
4. Laufanzahl und Bestzeit werden direkt angezeigt

**Mittlere Spalte — Zeiteingabe**
1. Fahrer auswählen (links)
2. Zeit eintippen: `45.32` oder `45,32` (Komma und Punkt werden akzeptiert)
3. Bei Bedarf Straf-Schnelltasten klicken: **+3s Pylone**, **+10s Tor**, **+15s Gasse**, **+3s Linie**
4. Sonderstatus: **DNS** / **DNF** / **DSQ** per Button (Zeitfeld wird deaktiviert)
5. **Lauf speichern** klicken oder **Enter** drücken

> **Lichtschranke:** Bei verbundener Lichtschranke wird die Zeit automatisch ins Zeitfeld eingetragen, sobald der Fahrer ausgewählt ist (grünes Blinken + „⚡ Zeit eingetragen").

**Rechte Spalte — Wertung**
- Session-Wertung: aktueller Rang mit Bestzeit und Laufanzahl
- Alle Läufe der Session kompakt gelistet

### Läufe korrigieren / löschen

In der History-Tabelle (Mitte unten) gibt es pro Lauf ein **✕**-Symbol zum Löschen — nach Bestätigungsabfrage wird der Lauf unwiderruflich entfernt.

---

## 7. Auswertung

**URL:** `/auswertung` | **Rolle:** alle angemeldeten Rollen

Die Auswertungsseite zeigt statistische Highlights pro Veranstaltung.

### Seite aufrufen

Im Navigations-Dropdown **„Mehr ▾"** → **📊 Auswertung** klicken.

Oben rechts die gewünschte Veranstaltung auswählen (Standard: aktive Veranstaltung).

### Anzeige

| Bereich | Inhalt |
|---------|--------|
| 🏆 **Schnellste Wertungsläufe pro Klasse** | Tabelle: Klasse · Startnummer · Name · Verein · Lauf-Nr. · Bestzeit |
| 👑 **Schnellste Dame** | Name, Klasse, Verein und Bestzeit der schnellsten Fahrerin |
| 👑 **Schnellster Herr** | Name, Klasse, Verein und Bestzeit des schnellsten Fahrers |

> **Hinweis:** Für die Dame/Herr-Auswertung muss das **Geschlecht** beim Teilnehmer hinterlegt sein (Nennbüro → Teilnehmer bearbeiten → Feld „Geschlecht"). Fehlt das Geschlecht, erscheint ein entsprechender Hinweis in der Kachel.

> Es werden nur **Wertungsläufe** (Lauf 1, 2, …) ausgewertet — keine Trainingsläufe.

---

## 8. Schiedsrichter

**URL:** `/schiedsrichter` | **Rolle:** `schiedsrichter` oder `admin`

### Klasse steuern

| Aktion | Wann |
|--------|------|
| **▶ Klasse starten** | Wenn die Klasse beginnt |
| **⏸ Unterbrechen** | Kurze Unterbrechung (Unfall, Hindernis auf der Strecke) |
| **▶ Fortsetzen** | Nach Behebung der Unterbrechung |
| **⏹ Klasse beenden** | Wenn alle Läufe der Klasse abgeschlossen sind |
| **✓ Klasse offiziell freigeben** | Nach Ablauf der Einspruchfrist |

### Einspruchfrist

- Nach „Klasse beenden" startet automatisch ein **30-Minuten-Countdown**
- Der Timer läuft in Echtzeit sichtbar
- Nach Ablauf wird der „Freigeben"-Button grün → klicken um die Klasse offiziell zu machen
- Frühere Freigabe ist möglich (Button läuft orange mit Hinweis)

### Ergebnis korrigieren

1. In der Mitte das Ergebnis finden, das korrigiert werden soll (Spalte „Lauf" zeigt Training oder Lauf N)
2. **Korrigieren** klicken
3. Neue Rohzeit oder neuen Status eingeben
4. Bei Wertungsläufen (Lauf 1, 2, …): Strafen anpassen — bestehende Strafen entfernen (✕) oder neue hinzufügen (+ Button); die Gesamtzeit wird sofort aktualisiert
5. **Begründung** eingeben (Pflichtfeld, z.B. „Pylone nach Video gestrichen")
6. **Korrektur speichern**

> Alle Korrekturen werden im Audit-Log (rechts) dauerhaft protokolliert.

> **Hinweis Training:** Beim Trainingslauf gibt es keine Straffelder — hier können nur Rohzeit und Status korrigiert werden.

---

## 9. Nachrichten senden

**URL:** `/nachrichten` | **Rolle:** alle außer `viewer`

Über die Nachrichten-Seite können alle angemeldeten Mitarbeiter sofort eine Ankündigung an **alle verbundenen Geräte** senden (Zuschauer-Displays, Sprecher, Zeitnahme, Livetiming).

### Nachricht senden

1. Im Menü auf **„📢 Nachrichten"** klicken
2. Text eingeben oder einen **Schnell-Button** wählen (Bratwurst, JL-Besprechung, Pause, Siegerehrung, …)
3. **„📤 An alle senden"** klicken oder **Strg+Enter** drücken
4. Die Nachricht erscheint sofort auf allen Geräten als cyan Banner

> Die Nachricht wird 30 Sekunden angezeigt und kann durch Klicken geschlossen werden.  
> Am Ende des Banners steht der Absender in Klammern, z.B. `(admin)`.

---

## 10. Streckenposten

**URL:** `/marshal` | **Rolle:** `marshal` (oder `admin`)

Streckenposten melden Fehlerpunkte (Pylonen, Tore usw.) direkt vom Smartphone oder Tablet
an die Zeitnahme. Die Meldungen erscheinen dort als gelbes Panel und können mit einem Klick
übernommen werden.

### Einrichten

1. Im Admin einen Benutzer mit Rolle **`marshal`** anlegen (z.B. „posten1", „posten2", …)
2. Passwort mitteilen; Login-URL: `http://<IP>:1980/login`
3. Nach dem Login landet der Streckenposten automatisch auf `/marshal`

### Posten-Bezeichnung setzen

- Oben links steht die aktuelle Bezeichnung (Standard: „Posten 1")
- Auf den Namen klicken → bearbeiten → **Enter** oder außerhalb klicken zum Speichern
- Die Bezeichnung wird lokal im Browser gespeichert und erscheint bei jeder Meldung

### Fehlerpunkt melden

1. Anzahl der Fehlerpunkte (Sekunden) in das große Zahlenfeld eintippen
2. **„📤 Senden"** tippen oder **Enter** drücken
3. Grünes **„✓ X Punkte gesendet"** erscheint kurz als Bestätigung
4. Das Feld leert sich automatisch — nächste Meldung kann sofort eingegeben werden

> Die Fehlerpunkte werden direkt in Sekunden angegeben (Pylone = 3, Tor = 10 usw.).

### Meldung in der Zeitnahme übernehmen

Eingehende Streckenposten-Meldungen erscheinen in der Zeitnahme als **gelbes Panel**
über den Straf-Buttons:

- **„Übernehmen"** → Strafe wird der aktuellen Zeiteingabe hinzugefügt
- **„✕"** → Meldung verwerfen
- Nach 60 Sekunden werden nicht übernommene Meldungen automatisch ausgeblendet

---

## 11. Livetiming (Gäste)

**URL:** `/livetiming` | Kein Login erforderlich

- Zeigt Ergebnisse aller Klassen in Echtzeit
- Klassen über Tabs wählbar; Gesamtwertung mit Rang, Startnummer, Name, Verein, Gesamtzeit
- Lauf-Detailzeilen unter jedem Fahrer: Rohzeit + Strafzeit pro Lauf (z.B. `Lauf 1  56.13 +12.0s = 68.13`)

---

## 12. Admin – Stammdaten und Einstellungen

### Jugendliche (Trainings-Stammdaten)

Admin → **🧒 Jugendliche**

- Jugendliche anlegen und bearbeiten (Vorname, Nachname, Jahrgang, Kart-Nummer, Verein, Lizenznummer)
- Aktiv/Inaktiv-Schalter: inaktive Jugendliche erscheinen nicht in der Fahrerliste
- Suche nach Name
- Inaktive anzeigen/verbergen per Toggle

### Training-Sessions

Admin → **🏋 Training**

- Trainings-Sessions anlegen: Datum, Name, Status und Notizen
- Status: `geplant` → `aktiv` → `beendet`
- Nur eine Session kann gleichzeitig aktiv sein — beim Aktivieren werden andere automatisch beendet
- Abgeschlossene Sessions bleiben mit allen Läufen erhalten

### Vereine

Admin → **🏁 Vereine**

- Vereine mit Name, Kurzname und Ort anlegen und bearbeiten
- Kurzname erscheint in Listen und auf dem Ausdruck

### Benutzer

Admin → **👥 Benutzer**

- Neue Benutzer mit Rolle anlegen
- Rollen: `admin`, `nennung`, `zeitnahme`, `schiedsrichter`, `marshal`, `viewer`
- `marshal` → Streckenposten-Ansicht (Fehlerpunkte melden)

### Sponsoren

Admin → **🤝 Sponsoren**

- Sponsor anlegen: Name, Logo-URL, Website-URL, Reihenfolge
- Aktiv/Inaktiv-Schalter: nur aktive Sponsoren erscheinen auf der Landingpage
- Logo-Vorschau beim Bearbeiten

### System / Druckvorlage

Admin → **⚙️ System**

Hier werden die Texte konfiguriert, die auf der Nennliste gedruckt werden:

- **Veranstalter:** Name des Veranstalters (z.B. „MSC Braach e.V. im ADAC")
- **Adresse:** Adresse des Veranstalters
- **Versicherungshinweis:** Text über die ADAC-Versicherung
- **Einverständniserklärung:** Text für die Elternunterschrift

**Einstellungen speichern** klicken nach Änderungen.

### Lichtschranken-API-Key

Admin → **⚙️ System** → Karte **„⏱ Lichtschranken-API-Key"**

Der API-Key sichert den `/ws/timing`-WebSocket-Endpunkt ab, damit nur autorisierte Messgeräte Zeiten einspielen können.

**Einmalige Einrichtung:**

1. Auf **📋 Kopieren** klicken — der Schlüssel ist jetzt in der Zwischenablage
2. Auf dem Raspberry Pi die Datei `racecontrol_client.py` öffnen und ganz oben eintragen:
   ```python
   TIMING_API_KEY = "<eingefügter Schlüssel>"
   ```
3. Beim ELV LSU200 entsprechend in `tools/lsu200_client.py` eintragen
4. Client neu starten

**Schlüssel neu generieren (falls Sicherheit kompromittiert):**

1. **🔄 Neu generieren** klicken → Warnmeldung bestätigen
2. Neuen Schlüssel wie oben in alle Client-Scripts eintragen und Clients neu starten

> Der Schlüssel wird beim ersten Start des Backends automatisch erstellt — er muss nur dann eingetragen werden, wenn Lichtschranken-Clients verwendet werden.

---

## 13. Lichtschranken-Clients

### Raspberry Pi (GPIO-Lichtschranke)

Der Raspberry Pi misst Zeiten über zwei GPIO-Lichtschranken und sendet sie per WebSocket an das Backend.

**Starten:**
```bash
cd RaPi_lichtschranke
python3 racecontrol_client.py        # TM1637-Display
# oder
python3 racecontrol_client_max7219.py  # MAX7219-LED-Matrix
```

**Konfiguration** (am Anfang der Datei):
```python
BACKEND_HOST   = "192.168.0.100"   # IP des Laptops mit RaceControl
BACKEND_PORT   = 1980
TIMING_API_KEY = ""                # Admin → System → Lichtschranken-API-Key eintragen
MIN_TIME       = 5.0               # Läufe unter 5 s werden verworfen
```

> Den API-Key im Admin-Bereich (System-Tab → Karte „⏱ Lichtschranken-API-Key") kopieren und hier eintragen.

Detaillierte Verkabelung und Autostart-Anleitung: siehe `RaPi_lichtschranke/notes.md`

---

### ELV LSU200 (USB-Lichtschranke)

Der ELV LSU200 Client läuft auf dem **gleichen Laptop** wie das Backend — kein Raspberry Pi nötig.

**Voraussetzungen:**
```bash
pip install pyserial websocket-client
```

**COM-Port ermitteln (Windows):**
- Gerätemanager → Anschlüsse (COM & LPT) → ELV LSU200 (COMx)
- oder in PowerShell: `Get-WmiObject Win32_PnPEntity | Where Name -like "*LSU*"`

**Starten:**
```bash
cd tools
python lsu200_client.py
```

**Konfiguration** (am Anfang der Datei):
```python
SERIAL_PORT    = None    # None = automatische Erkennung, oder z.B. "COM3"
TIMING_API_KEY = ""      # Admin → System → Lichtschranken-API-Key eintragen
MIN_TIME       = 3.0     # Messungen unter 3 s werden verworfen
```

> Den API-Key im Admin-Bereich (System-Tab → Karte „⏱ Lichtschranken-API-Key") kopieren und hier eintragen.

> Bei erkannter Verbindung erscheint der grüne Lichtschranken-Indikator in der Zeitnahme.

---

## 14. Downhill- und Seifenkisten-Zeitnahme

Downhill MTB, Ski-Abfahrt und Seifenkistenrennen nutzen den **Downhill-Timing-Modus**:
Start und Ziel sind weit voneinander entfernt — die Laufzeit ergibt sich aus
`Ziel-Zeitstempel − geplantem Start`.

### Veranstaltung als Downhill-Event anlegen

1. Admin → Veranstaltungen → Neue Veranstaltung anlegen
2. Feld **Timing-Modus** auf `downhill` setzen
3. Klassen anlegen wie gewohnt (eine Klasse pro Wertungsgruppe)
4. Teilnehmer anmelden (Nennbüro oder Online-Nennung)

### Starterliste (Planstarts) eintragen

1. Admin → Veranstaltung → **Starterliste** (Tab erscheint nur bei `timing_mode = downhill`)
2. Pro Teilnehmer: Planstart-Zeit `HH:MM:SS` eintragen
3. **Spur** (optional): leer lassen für Single-Lane, `A` oder `B` für Zwei-Spur-Betrieb

**Massenimport** (API): `POST /api/events/{id}/schedule/bulk` mit JSON-Array:
```json
[
  { "participant_id": 1, "scheduled_start": "12:00:00" },
  { "participant_id": 2, "scheduled_start": "12:01:00" },
  { "participant_id": 3, "scheduled_start": "12:02:00" }
]
```

### Zieleinheit (Raspberry Pi) einrichten

Für die Ziel-Lichtschranke wird `racecontrol_downhill_finish.py` verwendet — **nicht** der Standard-Client.

**Unterschied zum Standard-Client:**

| Merkmal | Standard | Downhill-Zieleinheit |
|---|---|---|
| GPIO-Sensoren | Start + Ziel | Nur Ziel (GPIO 27) |
| Zeiterfassung | Δt lokal (RPi) | Absoluter Zeitstempel → Backend |
| Spurwahl | — | DIP-Schalter GPIO 5 (A/B) |
| Zeitsync | beliebig | NTP/DCF77/GPS zwingend nötig |

Konfiguration in `racecontrol_downhill_finish.py`:
```python
BACKEND_HOST   = "192.168.0.100"   # IP des Laptops
TIMING_API_KEY = ""                # Admin → System → Lichtschranken-API-Key
MIN_TIME_S     = 10.0              # Kürzeste erlaubte Laufzeit (Fehlauslösung-Schutz)
```

Zeitsynchronisation (Genauigkeit):
- **NTP via LTE/WLAN** (empfohlen): ±10–50 ms — ausreichend für alle Praxis-Szenarien
- **GPS-Maus am Server**: ±1–5 ms für alle RPis via LAN-NTP — optimal bei mehreren Einheiten
- **DCF77-Modul am RPi**: ±1–10 ms offline — für Standorte ohne Mobilfunk
- Bauanleitungen: `RaPi_lichtschranke/BAUANLEITUNG_*.md`

### Zwei-Spur-Betrieb (Seifenkiste)

Für zwei parallele Bahnen werden zwei identische Zieleinheiten aufgebaut:

| DIP 1 (GPIO 5) | Spur | Planstarts |
|---|---|---|
| OFF | **A** | Teilnehmer mit `lane = 'A'` oder `lane = NULL` |
| ON | **B** | Teilnehmer mit `lane = 'B'` |

Beide RPis verbinden sich gleichzeitig mit dem Backend. Jede Auslösung wird
der richtigen Spur-Queue zugeordnet — keine Verwechslungen möglich.

### Ablauf am Veranstaltungstag

1. Veranstaltung auf `active` setzen (Admin → Status ändern)
2. Zieleinheit einschalten — Display zeigt aktuelle Uhrzeit (= Uhr synchronisiert ✓)
3. Starter loslassen — RPi empfängt Lichtschranken-Auslösung
4. Display zeigt berechnete Laufzeit (z.B. `0247 4` = 2:47.4)
5. Zeitnahme-View im Browser zeigt Ergebnis sofort mit Name und Zeit
6. Reset-Taster (GPIO 22) für nächsten Starter drücken

> **Hinweis:** Zeigt das Display `nSYn` nach dem Start, ist die Systemuhr nicht
> synchronisiert. Keine Zeiten messen bis `nSYn` verschwindet und die Uhrzeit angezeigt wird.

---

## 15. Häufige Fragen und Probleme

### Das Backend startet nicht

- Prüfen ob Port 1980 frei ist: `netstat -an | grep 1980`
- Python-Version prüfen: `python --version` (mind. 3.9)
- Abhängigkeiten installiert? `pip install fastapi uvicorn pyjwt bcrypt`

### Ein Teilnehmer hat die falsche Klasse

1. Nennbüro → Teilnehmer anklicken
2. Im Formular rechts die **Klasse** ändern
3. **Speichern**

### Startnummer ist doppelt vergeben

SQLite erzwingt die Eindeutigkeit der Startnummern **pro Klasse**. Die gleiche Startnummer kann in verschiedenen Klassen vergeben werden. Bei Konflikt innerhalb einer Klasse erscheint eine Fehlermeldung.

### Ergebnis wurde falsch eingetragen

Der Schiedsrichter kann jedes Ergebnis unter `/schiedsrichter` korrigieren. Eine Begründung ist Pflicht.

### Die Druckfunktion öffnet kein Fenster

Browser-Popups müssen für diese Seite erlaubt werden:
- Chrome: Adresszeile → Schloss-Symbol → Popups erlauben
- Firefox: Adressleiste → Schild-Symbol → Erlaubnis erteilen

### Datenbank zurücksetzen (Neustart für Tests)

```bash
rm racecontrol.db
# Backend neu starten → Datenbank wird neu angelegt
```

> ⚠️ Achtung: Alle Daten werden gelöscht!
