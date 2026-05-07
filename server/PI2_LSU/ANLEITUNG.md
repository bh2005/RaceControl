# Raspberry Pi 2 Model B + ELV LSU200 – Einrichtungsanleitung

**Ziel:** Der Pi 2 startet automatisch, verbindet sich per Ethernet mit dem lokalen
Netzwerk, öffnet die LSU200 per USB und sendet Zeitnahme-Daten per WebSocket
an den RaceControl-Server. Kein Eingriff am Veranstaltungstag nötig.

---

## Hardware-Übersicht

| Gerät | Rolle |
|-------|-------|
| Raspberry Pi 2 Model B v1.1 | LSU200-Client (Timing-Sender) |
| ELV LSU200 (USB) | Lichtschranken-Stoppuhr |
| Ethernet-Kabel | Verbindung zum Switch/Router |
| microSD-Karte (≥ 8 GB) | Betriebssystem |
| Micro-USB-Netzteil (≥ 2 A) | Stromversorgung Pi |
| USB-Netzteil oder PowerBank | Stromversorgung LSU200 |

---

## Schritt 1 – Raspberry Pi OS flashen

1. **Raspberry Pi Imager** herunterladen:
   `https://www.raspberrypi.com/software/`

2. Imager starten, dann:
   - **Gerät:** Raspberry Pi 2
   - **OS:** Raspberry Pi OS Lite (32-bit) — kein Desktop nötig
   - **Speicher:** microSD-Karte auswählen

3. Vor dem Schreiben das **Zahnrad-Symbol** (Erweiterte Einstellungen) öffnen:
   - **Hostname:** `pi2-lsu200`
   - **SSH aktivieren:** ja, Passwort-Authentifizierung
   - **Benutzername:** `pi` | **Passwort:** sicheres Passwort vergeben
   - **WLAN:** leer lassen (nicht benötigt)
   - **Locale:** Zeitzone `Europe/Berlin`, Tastatur `de`

4. Schreiben → Karte in den Pi einlegen.

---

## Schritt 2 – Pi starten und verbinden

1. Ethernet-Kabel vom Pi in den Router/Switch stecken.
2. Netzteil anschließen — Pi startet automatisch (kein Powerknopf).
3. Ca. 60 Sekunden warten bis der Boot abgeschlossen ist.

**IP-Adresse ermitteln** (eine der drei Methoden):

```powershell
# Methode A: Hostname (funktioniert wenn Router mDNS unterstützt)
ping pi2-lsu200.local

# Methode B: Router-Weboberfläche → DHCP-Tabelle → "pi2-lsu200"

# Methode C: IP-Scanner (z.B. Advanced IP Scanner, kostenlos)
```

**SSH-Verbindung aufbauen** (PowerShell auf Windows):

```powershell
ssh pi@pi2-lsu200.local
# oder mit IP:
ssh pi@192.168.1.XX
```

---

## Schritt 3 – Statische IP einrichten (empfohlen)

Eine feste IP verhindert, dass sich die Adresse nach einem Neustart ändert.
Die `.env`-Datei muss dann nicht angepasst werden.

**Auf dem Pi (per SSH):**

```bash
sudo nano /etc/dhcpcd.conf
```

Am Ende der Datei anhängen (IP-Adressen an euer Netzwerk anpassen):

```
interface eth0
static ip_address=192.168.1.50/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1
```

Speichern (`Ctrl+O`, `Enter`, `Ctrl+X`), dann neu starten:

```bash
sudo reboot
```

Nach dem Neustart ist der Pi immer unter `192.168.1.50` erreichbar.

---

## Schritt 4 – Dateien von Windows auf den Pi übertragen

Im Ordner `server/PI2_LSU/` liegt das PowerShell-Script `deploy.ps1`.
Es überträgt alle benötigten Dateien automatisch per SCP.

**PowerShell auf Windows öffnen, ins Repo-Verzeichnis wechseln:**

```powershell
cd "C:\Users\ks84597\OneDrive - K+S Aktiengesellschaft\Documents\Git-Repos\RaceControl\server\PI2_LSU"
```

**Deploy ausführen:**

```powershell
# Mit Hostname (wenn mDNS funktioniert):
.\deploy.ps1 -PiHost pi2-lsu200.local

# Mit IP-Adresse (immer zuverlässig):
.\deploy.ps1 -PiHost 192.168.1.50
```

SSH-Fingerprint-Warnung beim ersten Mal mit `yes` bestätigen.
Passwort eingeben wenn danach gefragt wird.

---

## Schritt 5 – .env konfigurieren (IP des RaceControl-Servers)

**Auf dem Pi:**

```bash
nano ~/lsu200/.env
```

Folgende Werte eintragen:

```ini
# IP-Adresse des RaceControl-Servers (CM3 oder Laptop am Veranstaltungstag)
BACKEND_WS=ws://192.168.1.100:1980/ws/timing

# API-Key: RaceControl Admin → System → Lichtschranken-Schlüssel
TIMING_API_KEY=abc123...
```

Speichern: `Ctrl+O`, `Enter`, `Ctrl+X`

> **Tipp:** Den TIMING_API_KEY findest du in RaceControl unter
> Admin → System → Lichtschranken-Schlüssel (oder per API: `/api/settings/`).

---

## Schritt 6 – Setup-Script ausführen

**Auf dem Pi:**

```bash
cd ~/lsu200
sudo ./install.sh
```

Das Script erledigt automatisch:
- Python-Abhängigkeiten installieren (`libusb`, `python3-usb`, `python3-dotenv`, `python3-websocket`)
- Dateien nach `/home/pi/lsu200/` installieren
- udev-Regel für USB-Zugriff ohne root schreiben
- Benutzer `pi` zur Gruppe `plugdev` hinzufügen
- Systemd-Dienst registrieren und beim Start aktivieren
- Dienst sofort starten

Ausgabe am Ende zeigt ob `.env` noch angepasst werden muss.

---

## Schritt 7 – Testen

**Dienst-Status prüfen:**

```bash
sudo systemctl status lsu200
```

Erwartete Ausgabe (grünes `active (running)`):
```
● lsu200.service - RaceControl Pro – ELV LSU200 Timing Client
     Loaded: loaded (/etc/systemd/system/lsu200.service; enabled)
     Active: active (running) since ...
```

**Live-Logs anzeigen:**

```bash
sudo journalctl -u lsu200 -f
```

Erwartete Log-Zeilen:
```
[WS] Verbunden mit ws://192.168.1.100:1980/ws/timing?key=...
[LSU200] Suche Gerät (VID=18ef PID=e02c) …
[LSU200] Gerät gefunden und geöffnet
```

**LSU200 per USB anschließen** → sofort erkannt ohne Neustart.

**Testmessung:** Lichtschranke starten und stoppen → Log zeigt:
```
[LSU200] Neue Zeit: 12.456 s
```

In RaceControl erscheint die Zeit automatisch im Zeitfeld.

---

## Veranstaltungstag – Ablauf

1. Pi mit Ethernet-Kabel in den Switch/Router stecken
2. Netzteil anschließen → Pi startet automatisch
3. LSU200 per USB anschließen (jederzeit, auch nach dem Start)
4. **Fertig** — kein SSH, kein Login, kein manueller Start nötig

Der Dienst startet automatisch nach dem Booten und stellt die
Verbindung zum Backend her sobald das Netzwerk verfügbar ist.
Bei Verbindungsabbruch verbindet er sich automatisch neu.

---

## Nützliche Befehle (SSH bei Bedarf)

```bash
# Status anzeigen
sudo systemctl status lsu200

# Live-Logs verfolgen
sudo journalctl -u lsu200 -f

# Dienst neu starten (nach .env-Änderung)
sudo systemctl restart lsu200

# Dienst stoppen
sudo systemctl stop lsu200

# Dienst deaktivieren (kein Autostart mehr)
sudo systemctl disable lsu200

# Log-Datei des Clients
cat ~/lsu200/lsu200.log

# USB-Gerät prüfen
lsusb | grep ELV
```

---

## Troubleshooting

### "Gerät nicht gefunden – retry in 5 s"

```bash
# USB-Gerät erkannt?
lsusb | grep -i "18ef"

# udev-Regel aktiv?
cat /etc/udev/rules.d/99-lsu200.rules

# Berechtigungen prüfen
ls -la /dev/bus/usb/$(lsusb | grep 18ef | awk '{print $2}')/ 2>/dev/null || echo "Gerät nicht gefunden"
```

→ LSU200 ab- und neu anschließen, 5 Sekunden warten.

### WebSocket verbindet nicht

```bash
# Ist das Backend erreichbar?
curl -s http://192.168.1.100:1980/api/settings/ | python3 -m json.tool

# IP in .env korrekt?
cat ~/lsu200/.env
```

→ IP des RaceControl-Servers in `.env` prüfen, dann `sudo systemctl restart lsu200`.

### TIMING_API_KEY falsch / abgelaufen

```bash
nano ~/lsu200/.env   # neuen Key eintragen
sudo systemctl restart lsu200
```

### Pi bekommt keine IP (kein Netzwerk)

```bash
ip addr show eth0
ip route
```

→ Ethernet-Kabel prüfen, Router/Switch prüfen.
→ Statische IP konfigurieren (Schritt 3).

### Dienst startet nicht nach Reboot

```bash
sudo systemctl is-enabled lsu200   # muss "enabled" ausgeben
sudo journalctl -u lsu200 --since "10 minutes ago"
```

---

## Dateiübersicht (auf dem Pi nach Installation)

```
/home/pi/lsu200/
├── lsu200_linux_client.py   # Hauptprogramm (USB → WebSocket)
├── .env                     # Konfiguration (BACKEND_WS, TIMING_API_KEY)
└── lsu200.log               # Letzte 100 Ereignisse (automatisch rotiert)

/etc/systemd/system/
└── lsu200.service           # Autostart-Definition

/etc/udev/rules.d/
└── 99-lsu200.rules          # USB-Zugriffsrechte ohne root
```
