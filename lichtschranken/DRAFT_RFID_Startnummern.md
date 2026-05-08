# DRAFT: RFID-Startnummern für RaceControl

## Idee

Fahrer automatisch identifizieren statt manuell im Training auswählen.
Ein RFID-Tag am Kart oder Helm wird beim Pit-Lane-Eingang gescannt →
RaceControl wählt den Fahrer automatisch aus → Lichtschranke misst → Zeit
landet ohne manuelle Auswahl beim richtigen Fahrer.

---

## Technologien im Vergleich

### NFC (13,56 MHz)
- Reichweite: ~3 cm
- Tags: 0,20 – 1 € (Label oder Karte)
- Reader: USB-ACR122U ~25 €, oder jedes Android-Handy
- Python: `nfcpy` (USB) oder kleine Android-App
- **Fazit**: Funktioniert nur als aktiver Scan (Fahrer hält Tag hin).
  Für Training mit Pit-Lane-Check-In ausreichend.

### UHF-RFID (860 – 960 MHz)
- Reichweite: 0,5 – 10 m je nach Hardware
- Tags am Kart-Chassis: On-Metal-Tag nötig (1 – 5 €)
- Tags am Helm: normales UHF-Label reicht (0,10 – 0,50 €)

| Klasse | Beispiel | Preis | Reichweite | Anmerkung |
|---|---|---|---|---|
| Hobbyist USB | generisch (AliExpress) | 40 – 80 € | 0,5 – 1 m | reicht für langsame Durchfahrt |
| Semiprofessionell | Impinj R120, Zebra FX7500 | 300 – 700 € | 2 – 5 m | + Antenne 50–150 € |
| Professionell | Impinj R420 | 800 – 1500 € | 5 – 10 m | für Durchfahrt bei Tempo |

### AMB/MyLaps Transponder (aktiv, dediziert)
- Transponder: 150 – 300 € pro Stück
- Loop im Boden + Decoder: 500 – 2000 €
- Fertiglösung, kein Eigenbau — andere Preisklasse

---

## Empfehlung für Trainings-Betrieb

**Stufe 1 – NFC testen (fast kostenlos)**
- ACR122U USB-Reader (~25 €) am Timing-PC
- NFC-Karte oder -Sticker am Helm (~0,50 €/Stück)
- Fahrer hält Helm kurz an Reader beim Pit-Eingang
- Wenn Workflow im Alltag akzeptiert wird → fertig

**Stufe 2 – UHF wenn NFC zu umständlich**
- Günstiger USB-UHF-Reader (~60 €, AliExpress)
- UHF-Label am Helm (~0,30 €/Stück)
- Antenne am Pit-Lane-Eingang, ~0,5 – 1 m Reichweite
- Fahrer fährt langsam vorbei, kein Anhalten nötig

**Stufe 3 – semiprofessionell (optional)**
- Impinj R120 + Antenne (~500 € gesamt)
- Zuverlässige Erfassung bei normaler Einfahrgeschwindigkeit
- Lohnt sich wenn Stufe 2 Aussetzer hat

---

## Integration in RaceControl

### Backend
```
DB: Tabelle RfidTags (uid TEXT PK, trainee_id INT FK)
POST /api/rfid/register   – UID einem Trainee zuordnen (Admin)
```

USB-Reader läuft als eigener Client (ähnlich lsu200_linux_client.py)
und sendet per WebSocket ans Backend:
```json
{ "type": "rfid_scan", "uid": "E2003412AB5C", "device": "uhf-usb" }
```

Backend sucht Trainee zur UID und broadcastet:
```json
{ "type": "set_active_trainee", "trainee_id": 4, "trainee_name": "Holzhauer B." }
```

### Frontend (TrainingView)
```javascript
if (msg.type === 'set_active_trainee') {
  const t = trainees.value.find(t => t.id === msg.trainee_id)
  if (t) setCurrentTrainee(t)
}
```

---

## Optische Erkennung (Kamera)

### QR-Code / Barcode am Kart
- Code auf Papier drucken, laminieren, am Helm oder Kart kleben: **~0 €**
- Kamera: Raspberry Pi Cam (~15 €) oder USB-Webcam (~20 €)
- Python: `opencv-python` + `pyzbar` oder `cv2.QRCodeDetector`
- Reichweite: 0,2 – 1,5 m (abhängig von Code-Größe und Kamera)
- **Vorteil gegenüber NFC**: kein Handkontakt nötig, etwas mehr Abstand
- **Nachteil**: Licht- und Winkelempfindlich, bei Bewegung Unschärfe

### OCR (Kart-Nummer direkt lesen)
- Kamera erkennt die aufgemalte Startnummer
- Python: `pytesseract` + OpenCV Vorverarbeitung
- Funktioniert gut bei hellem Licht, statischer Kamera, kontrastreicher Schrift
- Versagt bei: schlechtem Licht, Schmutz, Motion Blur, ähnlichen Schriftarten
- Aufwand: deutlich höher als QR, Zuverlässigkeit deutlich geringer
- **Fazit**: für Produktion nicht empfohlen

### KI-basierte Erkennung (YOLO + OCR)
- YOLO erkennt den Kart/Fahrer, OCR liest die Nummer aus dem Crop
- Robust gegen Winkel und Licht wenn gut trainiert
- Trainingsaufwand: eigene Bilder nötig, GPU hilfreich
- Python: `ultralytics` (YOLOv8) + `pytesseract` / `easyocr`
- **Fazit**: interessant für vollautomatische Durchfahrtserkennung bei Tempo,
  aber erheblicher Einrichtungsaufwand — Overkill für Trainings-Betrieb

### Vergleich Kamera vs. RFID

| Kriterium | QR-Code (Kamera) | NFC | UHF-RFID |
|---|---|---|---|
| Hardware-Kosten | ~20 € | ~25 € | 40 – 700 € |
| Tag/Sticker-Kosten | ~0 € (Ausdruck) | 0,20 – 1 € | 0,30 – 5 € |
| Reichweite | 0,2 – 1,5 m | ~3 cm | 0,5 – 10 m |
| Lichtabhängig | ja | nein | nein |
| Bewegungsrobust | nein (bei Tempo) | nein | ja |
| Softwareaufwand | mittel | gering | gering–mittel |
| **Empfehlung** | Pit-Lane-Scan (Halt) | Pit-Lane-Scan (Halt) | Durchfahrt |

### Integration (QR-Code)
Kleiner Kamera-Client analog zu `lsu200_linux_client.py`:
```python
# pip install opencv-python pyzbar
import cv2
from pyzbar.pyzbar import decode

cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    for obj in decode(frame):
        uid = obj.data.decode('utf-8')   # z.B. "RC:trainee:4"
        # → WebSocket: {"type": "rfid_scan", "uid": uid, "device": "qr-cam"}
```

---

## Gesamtempfehlung

| Szenario | Empfehlung |
|---|---|
| Pit-Lane, Fahrer hält an | QR-Code (Ausdruck + Webcam, ~20 €) oder NFC (~25 €) |
| Pit-Lane, Fahrer fährt langsam durch | UHF-Budget-Reader (~60 €) + Helm-Label |
| Durchfahrt bei normalem Tempo | Impinj R120 + Antenne (~500 €) |
| Vollautomatisch ohne Tags | YOLO + OCR – erheblicher Aufwand, nicht für Produktion empfohlen |

Einstieg: **QR-Code testen** — kostet fast nichts, gleiche Backend-Integration
wie RFID. Wenn der Workflow im Alltag akzeptiert wird, ist die Sache erledigt.
Wenn nicht, auf UHF upgraden ohne Backend-Änderungen.

---

## Offene Fragen
- [ ] Welche Python-Bibliothek für günstigen USB-UHF-Reader? (`mercury`, herstellerspezifisch, oder generisch über seriell)
- [ ] On-Metal-Tag oder Helm-Montage? (Helm einfacher, kein Metallproblem)
- [ ] Einzeln oder mehrere Reader (Start + Ziel)?
- [ ] Registrierung der Tags: Admin-UI oder Kommandozeile?
- [ ] QR-Code-Format: einfache ID (`RC:4`) oder URL (`https://racecontrol.local/trainee/4`)?
- [ ] Kamera-Platzierung: fest montiert am Pit-Eingang oder mobil?

---

*Stand: 2026-05-07 – Draft, noch nicht implementiert*
