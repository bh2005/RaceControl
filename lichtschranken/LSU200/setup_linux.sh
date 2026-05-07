#!/usr/bin/env bash
# RaceControl Pro – Einrichtung ELV LSU200 Linux-Client

set -e

echo "=================================================="
echo "  RaceControl Pro – LSU200 Linux Setup"
echo "=================================================="

# ── Pakete installieren ───────────────────────────────
echo ""
echo "[1/4] Installiere Abhängigkeiten ..."
sudo apt install -y libusb-1.0-0 python3-usb python3-dotenv python3-websocket

# ── udev-Regel einrichten ─────────────────────────────
echo ""
echo "[2/4] Richte udev-Regel ein ..."

# Zugriffsrecht für plugdev ohne root
RULE='SUBSYSTEM=="usb", ATTRS{idVendor}=="18ef", ATTRS{idProduct}=="e02c", MODE="0666", GROUP="plugdev", ENV{ID_MM_DEVICE_IGNORE}="1"'
echo "$RULE" | sudo tee /etc/udev/rules.d/99-lsu200.rules > /dev/null

# USB-Serial-Kernel-Treiber (cp210x, ftdi_sio) vom Gerät fernhalten –
# pyusb kommuniziert direkt mit dem CP2102N-Chip ohne Kernel-Treiber
SERIAL_RULE='SUBSYSTEM=="usb-serial", ATTRS{idVendor}=="18ef", ATTRS{idProduct}=="e02c", RUN+="/bin/sh -c '"'"'echo %k > /sys$env{DEVPATH}/../../../driver/unbind 2>/dev/null || true'"'"'"'
echo "$SERIAL_RULE" | sudo tee -a /etc/udev/rules.d/99-lsu200.rules > /dev/null

sudo udevadm control --reload-rules && sudo udevadm trigger
echo "      udev-Regel geschrieben: /etc/udev/rules.d/99-lsu200.rules"

# ── Benutzer zur Gruppe hinzufügen ────────────────────
echo ""
echo "[3/4] Füge Benutzer '$USER' zur Gruppe 'plugdev' hinzu ..."
sudo usermod -aG plugdev "$USER"

# Gruppe sofort in der aktuellen Shell aktiv machen (kein Neu-Anmelden nötig)
if ! id -nG | grep -qw plugdev; then
    exec newgrp plugdev
fi

# ── .env anlegen (falls noch nicht vorhanden) ─────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LICHTSCHRANKEN_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$LICHTSCHRANKEN_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    cp "$LICHTSCHRANKEN_DIR/.env.example" "$ENV_FILE"
fi

# ── Timing-API-Key vom laufenden Backend abholen ──────
echo ""
echo "[4/4] Suche laufendes RaceControl-Backend ..."
BACKEND_URL="${BACKEND_WS:-http://localhost:1980}"
BACKEND_URL="${BACKEND_URL/ws:\/\//http://}"
BACKEND_URL="${BACKEND_URL/wss:\/\//https://}"
BACKEND_URL="${BACKEND_URL%%/ws*}"   # Pfad-Suffix entfernen

API_KEY=""
if curl -sf --max-time 3 "$BACKEND_URL/api/settings/" -o /tmp/rc_settings.json 2>/dev/null; then
    API_KEY=$(python3 -c "import json,sys; d=json.load(open('/tmp/rc_settings.json')); print(d.get('timing_api_key',''))" 2>/dev/null)
    rm -f /tmp/rc_settings.json
fi

if [ -n "$API_KEY" ]; then
    # Key in .env schreiben (bestehenden Eintrag ersetzen oder anhängen)
    if grep -q "^TIMING_API_KEY=" "$ENV_FILE"; then
        sed -i "s|^TIMING_API_KEY=.*|TIMING_API_KEY=$API_KEY|" "$ENV_FILE"
    else
        echo "TIMING_API_KEY=$API_KEY" >> "$ENV_FILE"
    fi
    echo "      TIMING_API_KEY automatisch eingetragen."
else
    echo "      Backend nicht erreichbar – bitte TIMING_API_KEY manuell eintragen:"
    echo "      $ENV_FILE"
fi

echo ""
echo "=================================================="
echo "  Setup abgeschlossen!"
echo ""
echo "  Nächste Schritte:"
if id -nG | grep -qw plugdev; then
    echo "  1. Gruppe 'plugdev' bereits aktiv – kein Neu-Anmelden nötig"
else
    echo "  1. Gruppe aktivieren (OHNE Neu-Anmelden): newgrp plugdev"
fi
if [ -z "$API_KEY" ]; then
echo "  2. TIMING_API_KEY in lichtschranken/.env eintragen"
echo "     (Quelle: RaceControl Admin → System)"
fi
echo "  3. LSU200 per USB anschließen"
echo "  4. python3 lsu200_linux_client.py"
echo "=================================================="
