#!/usr/bin/env bash
# RaceControl Pro – Pi 2 LSU200 Autostart-Setup
# Dieses Script wird auf dem Raspberry Pi ausgeführt.
# Voraussetzung: alle Dateien liegen bereits in ~/lsu200/
#
# Aufruf:
#   cd ~/lsu200
#   sudo ./install.sh

set -e

INSTALL_DIR="/home/pi/lsu200"
SERVICE_NAME="lsu200"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=================================================="
echo "  RaceControl Pro – Pi 2 LSU200 Setup"
echo "  Verzeichnis: $INSTALL_DIR"
echo "=================================================="

# ── Prüfungen ─────────────────────────────────────────
if [ "$(id -u)" -ne 0 ]; then
    echo "FEHLER: Bitte mit sudo ausführen: sudo ./install.sh"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/lsu200_linux_client.py" ]; then
    echo "FEHLER: lsu200_linux_client.py nicht gefunden in $SCRIPT_DIR"
    echo "        Bitte zuerst deploy.ps1 von Windows aus ausführen."
    exit 1
fi

# ── 1. Pakete installieren ─────────────────────────────
echo ""
echo "[1/5] Installiere Python-Abhängigkeiten ..."
apt-get update -qq
apt-get install -y libusb-1.0-0 python3-usb python3-dotenv python3-websocket

# ── 2. Dateien installieren ───────────────────────────
echo ""
echo "[2/5] Installiere Dateien nach $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR"
cp "$SCRIPT_DIR/lsu200_linux_client.py" "$INSTALL_DIR/"
chmod 755 "$INSTALL_DIR/lsu200_linux_client.py"

# .env nur anlegen wenn noch nicht vorhanden (Konfiguration schützen)
if [ ! -f "$INSTALL_DIR/.env" ]; then
    if [ -f "$SCRIPT_DIR/.env" ]; then
        cp "$SCRIPT_DIR/.env" "$INSTALL_DIR/.env"
    else
        cp "$SCRIPT_DIR/.env.example" "$INSTALL_DIR/.env"
        echo ""
        echo "  ⚠  .env aus Vorlage angelegt – bitte BACKEND_WS und TIMING_API_KEY eintragen:"
        echo "     nano $INSTALL_DIR/.env"
    fi
fi

chown -R pi:pi "$INSTALL_DIR"
chmod 600 "$INSTALL_DIR/.env"

# ── 3. udev-Regel (USB-Zugriff ohne root) ─────────────
echo ""
echo "[3/5] Schreibe udev-Regeln für ELV LSU200 ..."

RULE='SUBSYSTEM=="usb", ATTRS{idVendor}=="18ef", ATTRS{idProduct}=="e02c", MODE="0666", GROUP="plugdev", ENV{ID_MM_DEVICE_IGNORE}="1"'
echo "$RULE" | tee /etc/udev/rules.d/99-lsu200.rules > /dev/null

# cp210x-Kernel-Treiber fernhalten – pyusb spricht direkt mit dem CP2102N
SERIAL_RULE='SUBSYSTEM=="usb-serial", ATTRS{idVendor}=="18ef", ATTRS{idProduct}=="e02c", RUN+="/bin/sh -c '"'"'echo %k > /sys$env{DEVPATH}/../../../driver/unbind 2>/dev/null || true'"'"'"'
echo "$SERIAL_RULE" | tee -a /etc/udev/rules.d/99-lsu200.rules > /dev/null

udevadm control --reload-rules && udevadm trigger
echo "      Regel: /etc/udev/rules.d/99-lsu200.rules"

# ── 4. Benutzer zur Gruppe plugdev hinzufügen ──────────
echo ""
echo "[4/5] Füge Benutzer 'pi' zur Gruppe 'plugdev' hinzu ..."
usermod -aG plugdev pi

# ── 5. Systemd-Dienst registrieren und aktivieren ─────
echo ""
echo "[5/5] Installiere und aktiviere Systemd-Dienst ..."

cp "$SCRIPT_DIR/lsu200.service" /etc/systemd/system/
chmod 644 /etc/systemd/system/lsu200.service

systemctl daemon-reload
systemctl enable lsu200.service
systemctl restart lsu200.service

# ── Ergebnis ──────────────────────────────────────────
echo ""
echo "=================================================="
echo "  Setup abgeschlossen!"
echo ""
echo "  Nächste Schritte:"
echo ""

# .env-Inhalt prüfen
BACKEND=$(grep -E "^BACKEND_WS=" "$INSTALL_DIR/.env" 2>/dev/null | cut -d= -f2- | tr -d '"' || true)
APIKEY=$(grep -E "^TIMING_API_KEY=" "$INSTALL_DIR/.env" 2>/dev/null | cut -d= -f2- | tr -d '"' || true)

if [ -z "$BACKEND" ] || [ "$BACKEND" = "ws://192.168.1.100:1980/ws/timing" ]; then
    echo "  ➤  BACKEND_WS in .env anpassen (IP des Servers eintragen):"
    echo "     nano $INSTALL_DIR/.env"
else
    echo "  ✓  BACKEND_WS : $BACKEND"
fi

if [ -z "$APIKEY" ]; then
    echo "  ➤  TIMING_API_KEY in .env eintragen:"
    echo "     (Quelle: RaceControl Admin → System → Lichtschranken-Schlüssel)"
    echo "     nano $INSTALL_DIR/.env"
    echo "     sudo systemctl restart lsu200"
else
    echo "  ✓  TIMING_API_KEY eingetragen"
fi

echo ""
echo "  Dienst-Befehle:"
echo "    Status : sudo systemctl status lsu200"
echo "    Logs   : sudo journalctl -u lsu200 -f"
echo "    Neustart: sudo systemctl restart lsu200"
echo "=================================================="
