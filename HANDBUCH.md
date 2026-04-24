# RaceControl Pro – Handbuch

**MSC Braach e.V. im ADAC**  
Stand: April 2026

---

## Inhaltsverzeichnis

1. [Systemstart](#1-systemstart)
2. [Veranstaltung vorbereiten (Admin)](#2-veranstaltung-vorbereiten-admin)
3. [Nennbüro – Anmeldung und Abnahme](#3-nennbüro--anmeldung-und-abnahme)
4. [Online-Nennung (Teilnehmer)](#4-online-nennung-teilnehmer)
5. [Zeitnahme](#5-zeitnahme)
6. [Schiedsrichter](#6-schiedsrichter)
7. [Livetiming (Gäste)](#7-livetiming-gäste)
8. [Admin – Stammdaten und Einstellungen](#8-admin--stammdaten-und-einstellungen)
9. [Häufige Fragen und Probleme](#9-häufige-fragen-und-probleme)

---

## 1. Systemstart

### Laptop vorbereiten

1. WLAN-Hotspot aktivieren (Laptop als Zugangspunkt) **oder** Verbindung mit dem Veranstaltungs-WLAN.
2. Terminal öffnen und ins Projektverzeichnis wechseln.

### Backend starten

```bash
cd RaceControl/backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

Das Backend ist bereit, wenn `Application startup complete.` im Terminal erscheint.

### Frontend (falls Entwicklungsmodus)

```bash
cd RaceControl/frontend
npm run dev
```

### Zugriff vom Tablet / Smartphone

Die IP-Adresse des Laptops im WLAN ermitteln (z.B. `192.168.1.100`).  
Auf dem Gerät im Browser aufrufen: `http://192.168.1.100:5173`

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

### Nennungsschluss setzen

1. Im linken Panel bei der jeweiligen Klasse auf **„Nennungsschluss setzen"** klicken
2. Startzeit der Klasse eingeben (z.B. `10:30`)
3. **Bestätigen** → Nennungsschluss wird 30 Minuten davor gesetzt

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
2. **Lauf** wählen: Training / Lauf 1 / Lauf 2
3. Der aktuelle Starter wird im blauen Block angezeigt
4. Zeit eingeben → **Enter** oder **✓ Bestätigen**
5. Der nächste Fahrer erscheint automatisch

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

### Undo

- **↩ Undo** klicken oder **Strg+Z** drücken, um den letzten Eintrag rückgängig zu machen

---

## 6. Schiedsrichter

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

## 7. Livetiming (Gäste)

**URL:** `/livetiming` | Kein Login erforderlich

- Zeigt Ergebnisse aller Klassen in Echtzeit
- Klassen über Tabs wählbar; Gesamtwertung mit Rang, Startnummer, Name, Verein, Gesamtzeit
- Lauf-Detailzeilen unter jedem Fahrer: Rohzeit + Strafzeit pro Lauf (z.B. `Lauf 1  56.13 +12.0s = 68.13`)

---

## 8. Admin – Stammdaten und Einstellungen

### Vereine

Admin → **🏁 Vereine**

- Vereine mit Name, Kurzname und Ort anlegen und bearbeiten
- Kurzname erscheint in Listen und auf dem Ausdruck

### Benutzer

Admin → **👥 Benutzer**

- Neue Benutzer mit Rolle anlegen
- Rollen: `admin`, `nennung`, `zeitnahme`, `schiedsrichter`, `viewer`

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

---

## 9. Häufige Fragen und Probleme

### Das Backend startet nicht

- Prüfen ob Port 8000 frei ist: `netstat -an | grep 8000`
- Python-Version prüfen: `python --version` (mind. 3.9)
- Abhängigkeiten installiert? `pip install fastapi uvicorn pyjwt bcrypt`

### Ein Teilnehmer hat die falsche Klasse

1. Nennbüro → Teilnehmer anklicken
2. Im Formular rechts die **Klasse** ändern
3. **Speichern**

### Startnummer ist doppelt vergeben

SQLite erzwingt die Eindeutigkeit der Startnummern pro Veranstaltung. Bei Konflikt erscheint eine Fehlermeldung. Die Startnummer muss korrigiert werden.

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
