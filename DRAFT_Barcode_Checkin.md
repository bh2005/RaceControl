# DRAFT – Barcode Check-in im Nennbüro

**Status:** Entwurf · noch nicht implementiert  
**Ziel:** Fahrer können sich im Nennbüro mit ihrer digitalen ADAC-Lizenz per QR-/Barcode-Scan einchecken — schneller als manuelle Suche, fehlerlos.

---

## Szenario

1. Fahrer hält Smartphone (ADAC-App, digitale Lizenz) oder Plastikkarte vor den Scanner
2. Scanner liest QR-Code → Lizenznummer wird automatisch ins System übertragen
3. System findet Teilnehmer → zeigt Name, Klasse, Status
4. Nennbüro-Mitarbeiter bestätigt mit einem Klick: Nenngeld ✓ · Helm ✓ · Freigabe ✓
5. Fertig in unter 5 Sekunden

---

## ADAC Digitale Lizenz – Barcode-Format

Die ADAC-App zeigt auf der digitalen Lizenz einen **QR-Code** an.  
Aus Tests bekannte Formate (je nach Jahrgang der Lizenz):

| Format | Beispiel | Wahrscheinlichkeit |
|---|---|---|
| Nur Lizenznummer (numerisch) | `123456789` | häufig |
| Präfix + Nummer | `ADAC-123456789` | möglich |
| URL mit eingebetteter Nummer | `https://meinADAC.de/lizenz/123456789` | selten |

→ **Strategie:** den letzten zusammenhängenden Zahlenblock extrahieren.  
→ Fallback: rohen Scan-String direkt mit `license_number` in der DB vergleichen (LIKE-Suche).

---

## Benutzeroberfläche – Nennbüro

### Neuer „Scan"-Modus in NennungView

```
┌──────────────────────────────────────────────────────────┐
│  📋 Teilnehmer  │  🏁 Mannschaft  │  📷 Scan-Check-in   │
└──────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────┐
  │  🔍  Scanner bereit – QR-Code jetzt einscannen  │
  │  [ ________________________________ ] ↵         │
  └─────────────────────────────────────────────────┘
  (Eingabefeld ist automatisch fokussiert)
  Alternativ: Lizenznummer manuell eintippen + Enter

  ── Letzter Scan: ───────────────────────────────────

  ┌──────────────────────────────────────────────────┐
  │  ✅  Max Mustermann  #7                           │
  │      Klasse: Jugend A · MSC Braach e.V.           │
  │      Status: ⟳ Eingecheckt                        │
  │                                                   │
  │  [✓ Nenngeld €]  [✓ Helm 🪖]  [🚦 Freigeben]     │
  └──────────────────────────────────────────────────┘

  ── Nicht gefunden: ─────────────────────────────────

  ┌──────────────────────────────────────────────────┐
  │  ⚠️  Lizenz 987654 nicht gefunden                 │
  │      Gaststarter? → [+ Jetzt anmelden]            │
  └──────────────────────────────────────────────────┘
```

### Verhalten

- Eingabefeld ist **immer fokussiert** solange der Scan-Tab aktiv ist
- USB-HID-Scanner sendet Barcode + `Enter` → wird wie Tastatureingabe behandelt, kein Treiber nötig
- Nach erfolgreichem Scan: **Akustisches Feedback** (`AudioContext` Beep) + grüner Flash
- Nach Fehlschlag: roter Flash + Fehlerton
- Scan-Historie (letzte 10) bleibt sichtbar für Rückfragen

---

## Backend

### Neuer Endpunkt: Teilnehmer per Lizenznummer suchen

```
GET /api/events/{event_id}/participants/by-license/{license_number}
```

**Logik:**
1. Exakter Treffer: `WHERE license_number = ?`
2. Suffix-Treffer (für URLs/Präfixe): `WHERE license_number LIKE ?` mit dem extrahierten Zahlenblock
3. Kein Treffer → HTTP 404

**Response** (gleiche Struktur wie `ParticipantResponse`):
```json
{
  "id": 42,
  "first_name": "Max",
  "last_name": "Mustermann",
  "start_number": 7,
  "class_id": 3,
  "class_name": "Jugend A",
  "club": "MSC Braach e.V.",
  "status": "checked_in",
  "fee_paid": true,
  "helmet_ok": false,
  "license_number": "123456789"
}
```

### Check-in-Schnellaktion (bestehender Endpunkt, keine Änderung nötig)

```
PATCH /api/events/{event_id}/participants/{id}
{ "status": "checked_in" }
{ "fee_paid": true }
{ "helmet_ok": true }
{ "status": "technical_ok" }
```

---

## Hardware-Optionen

### Option A – USB HID Barcode-/QR-Scanner (empfohlen)

- **Plug & Play** — wird als USB-Tastatur erkannt, kein Treiber, kein Python-Code nötig
- Funktioniert mit jedem Browser (Desktop + Tablet)
- Scannt QR-Codes auf Smartphone-Display zuverlässig auch bei Schräglage und schlechtem Licht
- Empfohlene Geräte: Netum C890, Inateck BCST-70, Honeywell Voyager 1202g
- Preis: ~25–60 €

```
[ADAC-App QR] → [USB-Scanner] → USB → [Laptop] → Browser → Eingabefeld → Enter
```

### Option B – Smartphone-Kamera im Browser (WebRTC)

- Kein extra Hardware nötig
- `jsQR`-Bibliothek liest Kamera-Stream und erkennt QR-Code automatisch
- Nachteil: braucht HTTPS oder localhost (kein HTTP über WLAN), etwas langsamer
- Sinnvoll für mobilen Einsatz am Posten (z.B. Fahrerwaage)

### Option C – Kombination

USB-Scanner am festen Nennbüro-Laptop (A) +  
Kamera-Scan auf Tablet am Fahrerwaage-Posten (B)

---

## Ablaufdiagramm

```
Scan-Eingabe (USB-Scanner oder Tipp)
        │
        ▼
  Lizenznummer extrahieren
  (Zahlenblock aus rohem String)
        │
        ├─── GET /participants/by-license/{nr}
        │
        ├── 200 ──► Fahrerkarte anzeigen
        │           ├─ Aktionen: Nenngeld / Helm / Status
        │           └─ PATCH participant → Update
        │
        └── 404 ──► "Nicht gefunden"
                    ├─ [+ Anmelden] → Nennformular (Lizenz vorausgefüllt)
                    └─ Gaststarter-Hinweis
```

---

## Zu klärende Fragen

- [ ] Welches genaue Format hat der ADAC-App-QR-Code 2026? (Scan testen und loggen)
- [ ] Soll beim Scan automatisch `status → checked_in` gesetzt werden (One-Click-Flow) oder immer manuell bestätigen?
- [ ] Scan auch am Fahrerwaage-Posten (eigene Rolle `marshal`?) oder nur Nennbüro?
- [ ] Soll die Scan-Historie exportierbar sein (CSV, für Anwesenheitsliste)?
- [ ] Mehrfachscan desselben Fahrers: Warnung oder stumm ignorieren?

---

## Implementierungsaufwand (Schätzung)

| Komponente | Aufwand |
|---|---|
| Backend-Endpunkt `by-license` | ~1 h |
| Frontend Scan-Tab + Eingabefeld | ~2 h |
| Fahrerkarte + Quick-Actions | ~1 h (großteils aus NennungView wiederverwendbar) |
| Beep / visuelles Feedback | ~0,5 h |
| Option B (jsQR Kamera) | ~3 h zusätzlich |
| Tests | ~1 h |
| **Gesamt** | **~5,5 h** (ohne Kamera) |

---

## Nächste Schritte

1. ADAC-App-QR-Code mit einem USB-Scanner testen und Format loggen
2. Fragen oben klären
3. Backend-Endpunkt implementieren (klein, isoliert testbar)
4. Frontend-Tab in NennungView als separater Branch
