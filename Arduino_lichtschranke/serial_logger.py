#!/usr/bin/env python3
"""
serial_logger.py  –  Zeitmessungs-Logger für Arduino / ESP32 Lichtschranken
Liest JSON-Zeilen über USB-Serial und loggt sie in eine CSV-Datei.

Verwendung:
  python serial_logger.py                     # Auto-Detect Port, 115200 Baud
  python serial_logger.py COM3                # Windows COM-Port, 115200 Baud
  python serial_logger.py COM3 9600           # Arduino Nano (9600 Baud)
  python serial_logger.py /dev/ttyUSB0        # Linux / Raspberry Pi

JSON-Formate der Geräte:
  TM1637 / MAX7219:
    {"event":"result","device":"arduino_tm1637","time_ms":83456,"time_fmt":"01:23.45"}
  LoRa-Sender / WiFi-Sender:
    {"type":"start","unix":1746612401,"lane":"A","cp":0}

Ausgabe:
  Terminal:  farbige Echtzeit-Anzeige
  CSV:       zeitmessung_DATUM.csv  (wird automatisch erstellt / erweitert)

Abhängigkeiten:
  pip install pyserial
"""

import sys
import json
import csv
import time
import datetime
import os

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("Fehler: 'pyserial' nicht installiert. Bitte ausführen:")
    print("  pip install pyserial")
    sys.exit(1)

# ── Konfiguration ─────────────────────────────────────────────────────────────
LOG_DIR  = "."          # Verzeichnis für CSV-Logs
ENCODING = "utf-8"

# ── Auto-Detect COM-Port ──────────────────────────────────────────────────────
BEKANNTE_CHIPS = ["Arduino", "CH340", "CH341", "CP210", "CP2102", "USB Serial", "FTDI"]

def auto_detect_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        desc = p.description or ""
        if any(chip in desc for chip in BEKANNTE_CHIPS):
            return p.device
    if ports:
        return ports[0].device
    return None

def liste_ports():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("  Keine seriellen Ports gefunden.")
        return
    for p in ports:
        print(f"  {p.device:12s}  {p.description}")

# ── Formatierung Terminal-Ausgabe ─────────────────────────────────────────────
CYAN  = "\033[96m"
GREEN = "\033[92m"
AMBER = "\033[93m"
RESET = "\033[0m"
DIM   = "\033[2m"

def unix_zu_uhrzeit(unix):
    if unix and unix > 1_700_000_000:
        return datetime.datetime.utcfromtimestamp(unix).strftime("%H:%M:%S UTC")
    return "—"

def format_event(data):
    """Gibt eine lesbare Zeile für das Terminal zurück."""
    event = data.get("event", "")
    typ   = data.get("type", "")

    # ── TM1637 / MAX7219 Ergebnis ─────────────────────────────────────────────
    if event == "result":
        device   = data.get("device", "unbekannt")
        time_fmt = data.get("time_fmt", "?")
        time_ms  = data.get("time_ms", 0)
        return (
            f"{GREEN}[ERGEBNIS]{RESET}  "
            f"{device:22s}  "
            f"{GREEN}{time_fmt}{RESET}  "
            f"{DIM}({time_ms} ms){RESET}"
        )

    # ── LoRa / WiFi Trigger ───────────────────────────────────────────────────
    if typ in ("start", "split", "finish"):
        lane  = data.get("lane", "?")
        cp    = data.get("cp", "")
        unix  = data.get("unix", 0)
        uhr   = unix_zu_uhrzeit(unix)
        cp_str = f"  CP={cp}" if cp != "" else ""
        color = GREEN if typ == "start" else (AMBER if typ == "split" else CYAN)
        return (
            f"{color}[{typ.upper():6s}]{RESET}  "
            f"Spur={lane}{cp_str}  "
            f"unix={unix}  "
            f"{DIM}{uhr}{RESET}"
        )

    # ── Unbekanntes JSON ──────────────────────────────────────────────────────
    return f"{DIM}[JSON] {json.dumps(data, ensure_ascii=False)}{RESET}"

# ── CSV-Logging ───────────────────────────────────────────────────────────────
FIELDNAMES = ["timestamp", "event", "device", "lane", "cp",
              "time_ms", "time_fmt", "unix", "raw"]

def log_to_csv(data, writer, csvfile):
    now = datetime.datetime.now().isoformat(timespec="milliseconds")
    writer.writerow({
        "timestamp": now,
        "event":     data.get("event") or data.get("type", ""),
        "device":    data.get("device", ""),
        "lane":      data.get("lane", ""),
        "cp":        data.get("cp", ""),
        "time_ms":   data.get("time_ms", ""),
        "time_fmt":  data.get("time_fmt", ""),
        "unix":      data.get("unix", ""),
        "raw":       json.dumps(data, ensure_ascii=False),
    })
    csvfile.flush()

# ── Haupt-Schleife ────────────────────────────────────────────────────────────
def main():
    # Argumente
    port = sys.argv[1] if len(sys.argv) > 1 else None
    baud = int(sys.argv[2]) if len(sys.argv) > 2 else 115200

    # Port ermitteln
    if not port:
        port = auto_detect_port()
        if port:
            print(f"Auto-Detect: {port}")
        else:
            print("Kein serieller Port gefunden. Verfügbare Ports:")
            liste_ports()
            print("\nVerwendung: python serial_logger.py COM3 [Baudrate]")
            sys.exit(1)

    # CSV-Datei
    datum    = datetime.datetime.now().strftime("%Y-%m-%d")
    csv_path = os.path.join(LOG_DIR, f"zeitmessung_{datum}.csv")
    neu      = not os.path.exists(csv_path)
    csvfile  = open(csv_path, "a", newline="", encoding=ENCODING)
    writer   = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
    if neu:
        writer.writeheader()

    print(f"Verbinde mit {port} @ {baud} Baud ...")
    print(f"Log-Datei:   {csv_path}")
    print("─" * 60)

    try:
        with serial.Serial(port, baud, timeout=1) as ser:
            print(f"Verbunden. Warte auf Zeitmessungen ...  (Ctrl+C zum Beenden)\n")
            while True:
                try:
                    raw = ser.readline()
                except serial.SerialException as e:
                    print(f"\nVerbindung unterbrochen: {e}")
                    break

                line = raw.decode(ENCODING, errors="replace").strip()
                if not line:
                    continue

                ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

                # Debug-Zeilen (mit [xxx]-Prefix) nur anzeigen, nicht loggen
                if line.startswith("["):
                    print(f"{DIM}{ts}  {line}{RESET}")
                    continue

                # JSON parsen
                if line.startswith("{"):
                    try:
                        data = json.loads(line)
                        msg  = format_event(data)
                        print(f"{ts}  {msg}")
                        log_to_csv(data, writer, csvfile)
                        continue
                    except json.JSONDecodeError:
                        pass

                # Sonstige Zeilen (z.B. "Reset.", "Lichtschranke bereit.")
                print(f"{DIM}{ts}  {line}{RESET}")

    except KeyboardInterrupt:
        pass
    except serial.SerialException as e:
        print(f"Serieller Fehler: {e}")
        print(f"\nVerfügbare Ports:")
        liste_ports()
    finally:
        csvfile.close()
        print(f"\nBeendet. Messungen gespeichert in: {csv_path}")

if __name__ == "__main__":
    main()
