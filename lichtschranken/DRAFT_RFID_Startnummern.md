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
| Hobbyist HID-USB | Asyduey ISO18000-6C (Amazon) | ~50 € | 0,2 – 0,5 m | meldet sich als USB-Tastatur — kein Treiber, kein `mercury` |
| Hobbyist Seriell | generisch (AliExpress, CP210x) | 50 – 80 € | 0,5 – 1 m | COM-Port, `mercury`-Bibliothek |
| Semiprofessionell | Impinj R120, Zebra FX7500 | 300 – 700 € | 2 – 5 m | + Antenne 50–150 € |
| Professionell | Impinj R420 | 800 – 1500 € | 5 – 10 m | für Durchfahrt bei Tempo |

> **HID- vs. Serial-Modus:** Budget-Reader von Amazon/AliExpress gibt es in zwei Varianten.
> *HID-USB* (Tastatur-Emulation, z. B. Asyduey): kein Treiber, läuft überall, Client fängt
> Tastatureingaben ab. *Serial/COM-Port*: benötigt `mercury`-Bibliothek + Treiber, dafür
> mehr Konfigurierbarkeit (Sendeleistung, Region, Multi-Tag). Erkennungsmerkmal im Produktnamen:
> "HID" oder "Plug-and-Play" → Tastatur; "RS232/USB", "CP210x", "CH340" → seriell.

**Betrieb:** USB-UHF-Reader laufen auf **Windows-Laptop, Linux oder Raspberry Pi** —
der Client-Prozess (analog zu `lsu200_linux_client.py`) läuft auf dem gleichen Gerät
wie der Reader und sendet per WebSocket ans Backend. Kein dedizierter Pi nötig.

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
- **HID-Budget-Reader** (z. B. Asyduey ISO18000-6C, ~50 €, Amazon) — einfachster Einstieg:
  kein Treiber, kein COM-Port, läuft auf Windows/Linux/Pi ohne Konfiguration
- Reichweite mit mitgelieferter Patch-Antenne: ~20–50 cm (Fahrer hält kurz an oder
  fährt sehr langsam vorbei; für Durchfahrt bei Tempo nicht geeignet)
- UHF-Label am Helm (~0,30 €/Stück)
- **Läuft direkt am Veranstaltungs-Laptop** (Windows oder Linux) — kein extra Pi nötig

**Stufe 3 – semiprofessionell (optional)**
- Impinj R120 + Antenne (~500 € gesamt)
- Zuverlässige Erfassung bei normaler Einfahrgeschwindigkeit
- Lohnt sich wenn Stufe 2 Aussetzer hat

---

## Integration in RaceControl

### Deployment-Optionen für den RFID-Client

Der RFID-Client (analog zu `lsu200_linux_client.py`) ist ein eigenständiger Python-Prozess
der den USB-Reader ausliest und per WebSocket ans Backend sendet.
Er läuft auf **jedem Gerät mit USB-Port und Python**:

| Gerät | Port | Besonderheit |
|---|---|---|
| **Windows-Laptop** (Veranstaltungs-PC) | `COM3`, `COM4` … | Kein extra Hardware nötig, USB direkt einstecken; COM-Port im Gerätemanager prüfen |
| **Linux-Laptop** | `/dev/ttyUSB0` | Benutzer muss in Gruppe `dialout` sein (`sudo usermod -aG dialout $USER`) |
| **Raspberry Pi** (beliebiges Modell) | `/dev/ttyUSB0` | Sinnvoll wenn Reader physisch weit vom Server entfernt ist (langer USB-Kabel vs. Netzwerk) |

**Fazit:** Für den Trainings-Betrieb am einfachsten — Reader per USB direkt in den
Veranstaltungs-Laptop, Client-Script daneben starten, fertig.

### Backend
```
DB: Tabelle RfidTags (uid TEXT PK, trainee_id INT FK)
POST /api/rfid/register   – UID einem Trainee zuordnen (Admin)
```

USB-Reader läuft als eigener Client (ähnlich `lsu200_linux_client.py`)
und sendet per WebSocket ans Backend:
```json
{ "type": "rfid_scan", "uid": "E2003412AB5C", "device": "uhf-usb" }
```

Backend sucht Trainee zur UID und broadcastet:
```json
{ "type": "set_active_trainee", "trainee_id": 4, "trainee_name": "Holzhauer B." }
```

### Client-Gerüst (Windows + Linux, `mercury`-Bibliothek)

```python
# pip install mercuryapi pyserial websocket-client python-dotenv
import mercury, json, time, websocket
from dotenv import load_dotenv
import os

load_dotenv()
BACKEND_WS   = os.getenv("BACKEND_WS",   "ws://192.168.1.100:1980/ws/timing")
TIMING_KEY   = os.getenv("TIMING_API_KEY", "")
# Windows: "tmr:///COM3"   Linux/Pi: "tmr:///dev/ttyUSB0"
READER_PORT  = os.getenv("RFID_PORT", "tmr:///dev/ttyUSB0")
COOLDOWN_S   = 3.0  # gleiche UID erst nach 3 s erneut senden

reader = mercury.Reader(READER_PORT, baudrate=115200)
reader.set_region("EU3")
reader.set_read_plan([1], "GEN2")

ws_url = BACKEND_WS.replace("/ws/timing", "/ws/rfid")  # eigener WS-Endpoint
# (alternativ: bestehenden /ws/timing-Endpoint nutzen, da rfid_scan dort ignoriert wird
#  bis das Backend den Handler kennt)

last_seen = {}

def on_open(ws):
    print(f"[RFID] Verbunden mit {ws_url}")

ws_app = websocket.WebSocketApp(ws_url + (f"?key={TIMING_KEY}" if TIMING_KEY else ""),
                                 on_open=on_open)
import threading
threading.Thread(target=ws_app.run_forever, daemon=True).start()

print(f"[RFID] Lese von {READER_PORT} …")
while True:
    for tag in reader.read(timeout=500):
        uid = tag.epc.hex().upper()
        now = time.time()
        if now - last_seen.get(uid, 0) > COOLDOWN_S:
            last_seen[uid] = now
            ws_app.send(json.dumps({"type": "rfid_scan", "uid": uid, "device": "uhf-usb"}))
            print(f"[RFID] Tag: {uid}")
```

### Client-Gerüst B – HID-Keyboard-Reader (z. B. Asyduey)

HID-Reader "tippen" den EPC-Code + Enter wie eine Tastatur.
Der Client fängt diese Eingabe ab — kein COM-Port, kein `mercury`.

```python
# pip install pynput websocket-client python-dotenv
# Linux/Pi: evdev ist nativer (kein X11 nötig) — siehe Kommentar unten
import json, time, websocket
from pynput import keyboard as kb
from dotenv import load_dotenv
import os, threading

load_dotenv()
BACKEND_WS  = os.getenv("BACKEND_WS",    "ws://192.168.1.100:1980/ws/timing")
TIMING_KEY  = os.getenv("TIMING_API_KEY", "")
COOLDOWN_S  = 3.0

ws_url = BACKEND_WS.replace("/ws/timing", "/ws/rfid")
ws_app = websocket.WebSocketApp(ws_url + (f"?key={TIMING_KEY}" if TIMING_KEY else ""))
threading.Thread(target=ws_app.run_forever, daemon=True).start()

buffer    = ""
last_seen = {}

def on_press(key):
    global buffer
    try:
        if key == kb.Key.enter:
            uid = buffer.strip().upper()
            buffer = ""
            if uid:
                now = time.time()
                if now - last_seen.get(uid, 0) > COOLDOWN_S:
                    last_seen[uid] = now
                    ws_app.send(json.dumps({"type": "rfid_scan", "uid": uid, "device": "uhf-hid"}))
                    print(f"[RFID-HID] Tag: {uid}")
        elif hasattr(key, 'char') and key.char:
            buffer += key.char
    except Exception:
        pass

print(f"[RFID-HID] Warte auf Tags … (Ctrl+C zum Beenden)")
# suppress=True verhindert, dass der Code in andere Fenster getippt wird
with kb.Listener(on_press=on_press, suppress=True) as listener:
    listener.join()
```

> **Linux/Pi ohne X11** (empfohlen auf Pi im headless-Betrieb):
> `pynput` benötigt dort `$DISPLAY`. Alternativ `evdev` direkt:
> ```python
> from evdev import InputDevice, categorize, ecodes
> # Gerät finden: ls /dev/input/by-id/ | grep -i rfid
> device = InputDevice('/dev/input/event3')
> device.grab()  # exklusiver Zugriff → Eingabe geht nicht in andere Programme
> ```
> `pip install evdev` und Benutzer muss in Gruppe `input` sein (`sudo usermod -aG input pi`).

### Frontend (TrainingView)
```javascript
if (msg.type === 'set_active_trainee') {
  const t = trainees.value.find(t => t.id === msg.trainee_id)
  if (t) setCurrentTrainee(t)
}
```

---

## Optische Erkennung (Kamera)

### Ansatz 1 – ArUco-Marker (robusteste Lösung)

ArUco-Marker sind quadratische Binär-Marker aus der OpenCV-Bibliothek.
Sie werden auch bei Unschärfe, schlechtem Licht und extremer Neigung sicher erkannt.
Auf 2 m Entfernung reichen Marker von ca. 5–10 cm Größe aus — am Helm befestigt,
auf Papier gedruckt und laminiert: **~0 €/Stück**.

**Schlüsselvorteil:** Die Marker-ID entspricht direkt der `trainee_id` —
keine `RfidTags`-Tabelle, kein Registrierungsschritt, kein UID-Lookup.

```python
# pip install opencv-python (ArUco ist ab OpenCV 4.7 direkt enthalten)
import cv2
import cv2.aruco as aruco
import websocket, json

cap = cv2.VideoCapture(0)
aruco_dict  = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)   # 50 eindeutige Marker
parameters  = aruco.DetectorParameters()
last_seen   = {}   # trainee_id → timestamp (Debounce)
COOLDOWN_S  = 5.0  # gleiche ID erst nach 5 s erneut senden

ws = websocket.create_connection("ws://192.168.1.100:1980/ws/timing?key=…")

while True:
    ret, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

    if ids is not None:
        aruco.drawDetectedMarkers(frame, corners, ids)
        for marker_id in ids.flatten():
            now = __import__('time').time()
            if now - last_seen.get(marker_id, 0) > COOLDOWN_S:
                last_seen[marker_id] = now
                ws.send(json.dumps({
                    "type":   "rfid_scan",
                    "uid":    f"aruco:{marker_id}",
                    "device": "aruco-cam",
                }))
                print(f"Fahrer-ID erkannt: {marker_id}")

    cv2.imshow('Startnummern-Erkennung', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

**Marker generieren** (einmalig, auf dem Entwicklungsrechner):

```python
import cv2.aruco as aruco, cv2, os

aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
os.makedirs("aruco_marker", exist_ok=True)
for trainee_id in range(1, 51):
    img = aruco.generateImageMarker(aruco_dict, trainee_id, 400)   # 400×400 px
    cv2.imwrite(f"aruco_marker/trainee_{trainee_id:02d}.png", img)
print("Marker gespeichert in aruco_marker/")
```

Auf DIN A6 drucken (Drucker auf 8 × 8 cm skalieren), laminieren, Klettband am Helm.

**Hardware-Empfehlung:**
- Raspberry Pi Cam v2 oder USB-Webcam mit Autofokus (~20 €)
- Für bewegte Durchfahrten: Webcam mit hoher Framerate (60 fps) oder Globalshutter
- Raspberry Pi Zero 2 W reicht für die Erkennung (ca. 10–15 fps mit 640×480)

**Wann DICT_4X4_50 nicht reicht:**
Bei mehr als 50 Fahrern → `DICT_5X5_100` (100 Marker) oder `DICT_6X6_250` verwenden.
Die Marker werden etwas weniger robust, bleiben aber deutlich besser als QR-Codes.

---

### Ansatz 2 – QR-Code / Barcode am Kart
- Code auf Papier drucken, laminieren, am Helm oder Kart kleben: **~0 €**
- Kamera: Raspberry Pi Cam (~15 €) oder USB-Webcam (~20 €)
- Python: `opencv-python` + `pyzbar` oder `cv2.QRCodeDetector`
- Reichweite: 0,2 – 1,5 m (abhängig von Code-Größe und Kamera)
- **Vorteil gegenüber NFC**: kein Handkontakt nötig, etwas mehr Abstand
- **Nachteil**: Licht- und Winkelempfindlich, bei Bewegung Unschärfe

### Ansatz 3 – OCR (Kart-Nummer direkt lesen)
- Kamera erkennt die aufgemalte Startnummer
- Python: `pytesseract` + OpenCV Vorverarbeitung
- Funktioniert gut bei hellem Licht, statischer Kamera, kontrastreicher Schrift
- Versagt bei: schlechtem Licht, Schmutz, Motion Blur, ähnlichen Schriftarten
- Aufwand: deutlich höher als QR, Zuverlässigkeit deutlich geringer
- **Fazit**: für Produktion nicht empfohlen

### Ansatz 4 – KI-basierte Erkennung (YOLO + OCR)
- YOLO erkennt den Kart/Fahrer, OCR liest die Nummer aus dem Crop
- Robust gegen Winkel und Licht wenn gut trainiert
- Trainingsaufwand: eigene Bilder nötig, GPU hilfreich
- Python: `ultralytics` (YOLOv8) + `pytesseract` / `easyocr`
- **Fazit**: interessant für vollautomatische Durchfahrtserkennung bei Tempo,
  aber erheblicher Einrichtungsaufwand — Overkill für Trainings-Betrieb

### Vergleich Kamera vs. RFID

| Kriterium | ArUco (Kamera) | QR-Code (Kamera) | NFC | UHF-RFID |
|---|---|---|---|---|
| Hardware-Kosten | ~20 € | ~20 € | ~25 € | 40 – 700 € |
| Tag/Sticker-Kosten | ~0 € (Ausdruck) | ~0 € (Ausdruck) | 0,20 – 1 € | 0,30 – 5 € |
| Reichweite | 0,5 – 2 m | 0,2 – 1,5 m | ~3 cm | 0,5 – 10 m |
| Lichtabhängig | gering | ja | nein | nein |
| Bewegungsrobust | gut (Unschärfe OK) | nein (bei Tempo) | nein | ja |
| Winkelrobust | sehr gut | mittel | – | ja |
| Kein UID-Lookup nötig | **ja** (ID = trainee_id) | nein | nein | nein |
| Softwareaufwand | gering (nur OpenCV) | mittel | gering | gering–mittel |
| **Empfehlung** | **Pit-Lane (langsam/halt)** | Pit-Lane (Halt) | Pit-Lane (Halt) | Durchfahrt |

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
| Pit-Lane, Fahrer hält an oder fährt langsam | **ArUco-Marker** (Ausdruck + Webcam, ~20 €) — robusteste Kamera-Lösung |
| Pit-Lane alternativ (kein Kamera-Setup gewünscht) | NFC (~25 €) oder QR-Code (~20 €) |
| Pit-Lane, Fahrer hält kurz an, schneller Einstieg | **Asyduey HID-UHF (~50 €, Amazon)** — Plug-and-Play, ~20–50 cm Reichweite |
| Pit-Lane, Fahrer fährt zügig durch | UHF-Seriell-Reader (~60–80 €) + Helm-Label, `mercury`-Client |
| Durchfahrt bei normalem Tempo | Impinj R120 + Antenne (~500 €) |
| Vollautomatisch ohne Tags | YOLO + OCR – erheblicher Aufwand, nicht für Produktion empfohlen |

Einstieg: **ArUco-Marker testen** — kostet fast nichts, kein UID-Registrierungsschritt,
gleiche Backend-Integration wie RFID. Die Marker-ID entspricht direkt der `trainee_id`,
d.h. Marker 4 drucken → Trainee 4 in RaceControl wird automatisch gewählt.
Wenn der Workflow im Alltag akzeptiert wird, ist die Sache erledigt.
Wenn nicht (zu wenig Reichweite bei Durchfahrt), auf UHF upgraden ohne Backend-Änderungen.

---

## Offene Fragen
- [ ] HID-Reader (Asyduey o.ä.): `pynput` (Windows/Linux mit X11) oder `evdev` (Linux/Pi headless)?
- [ ] Wenn HID: `suppress=True` in `pynput` erfordert auf manchen Linux-Systemen Root — testen!
- [ ] On-Metal-Tag oder Helm-Montage? (Helm einfacher, kein Metallproblem)
- [ ] Einzeln oder mehrere Reader (Start + Ziel)?
- [ ] Registrierung der Tags: Admin-UI oder Kommandozeile?
- [ ] QR-Code-Format: einfache ID (`RC:4`) oder URL (`https://racecontrol.local/trainee/4`)?
- [ ] Kamera-Platzierung: fest montiert am Pit-Eingang oder mobil?
- [ ] ArUco: DICT_4X4_50 (robust, 50 Marker) oder DICT_5X5_100 (100 Marker, etwas weniger robust)?
- [ ] ArUco: Marker-Größe am Helm — 8 × 8 cm ausreichend oder 10 × 10 cm für mehr Reichweite?

---

*Stand: 2026-05-08 – Draft, noch nicht implementiert*
