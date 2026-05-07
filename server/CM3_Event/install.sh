#!/usr/bin/env bash
# RaceControl Pro – CM3 Veranstaltungsserver Setup
# Dieses Script wird auf dem Compute Module 3 ausgeführt.
# Voraussetzung: deploy.ps1 wurde vorher von Windows ausgeführt.
#
# Aufruf:
#   cd ~/racecontrol
#   sudo ./install.sh

set -e

INSTALL_DIR="/home/pi/racecontrol"
VENV_DIR="$INSTALL_DIR/venv"
SERVICE_NAME="racecontrol"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=================================================="
echo "  RaceControl Pro – CM3 Veranstaltungsserver Setup"
echo "  Verzeichnis: $INSTALL_DIR"
echo "=================================================="

# ── Prüfungen ─────────────────────────────────────────
if [ "$(id -u)" -ne 0 ]; then
    echo "FEHLER: Bitte mit sudo ausführen: sudo ./install.sh"
    exit 1
fi

if [ ! -f "$INSTALL_DIR/backend/main.py" ]; then
    echo "FEHLER: $INSTALL_DIR/backend/main.py nicht gefunden."
    echo "        Bitte zuerst deploy.ps1 von Windows ausführen."
    exit 1
fi

if [ ! -d "$INSTALL_DIR/frontend/dist" ]; then
    echo "FEHLER: $INSTALL_DIR/frontend/dist/ nicht gefunden."
    echo "        Bitte in Windows zuerst 'npm run build' ausführen"
    echo "        und dann erneut deploy.ps1 ausführen."
    exit 1
fi

# ── 1. System-Pakete ───────────────────────────────────
echo ""
echo "[1/5] Installiere System-Pakete ..."
apt-get update -qq
apt-get install -y python3-pip python3-venv

# ── 2. Python Virtual Environment ─────────────────────
echo ""
echo "[2/5] Erstelle Python Virtual Environment ..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "      venv erstellt: $VENV_DIR"
else
    echo "      venv bereits vorhanden – überspringe"
fi

echo "      Installiere Python-Abhängigkeiten ..."
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/backend/requirements.txt" --quiet
echo "      Abhängigkeiten installiert"

# ── 3. Dateiberechtigungen ─────────────────────────────
echo ""
echo "[3/5] Setze Dateiberechtigungen ..."
chown -R pi:pi "$INSTALL_DIR"
chmod 750 "$INSTALL_DIR"
chmod 755 "$INSTALL_DIR/backend"
find "$INSTALL_DIR/backend" -name "*.py" -exec chmod 644 {} \;
find "$INSTALL_DIR/backend" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
chmod -R 755 "$INSTALL_DIR/frontend/dist"
if [ -d "$INSTALL_DIR/assets" ]; then
    chmod -R 755 "$INSTALL_DIR/assets"
fi

# ── 4. Systemd-Dienst ──────────────────────────────────
echo ""
echo "[4/5] Installiere Systemd-Dienst ..."
cp "$SCRIPT_DIR/racecontrol.service" /etc/systemd/system/
chmod 644 /etc/systemd/system/racecontrol.service

systemctl daemon-reload
systemctl enable racecontrol.service
systemctl restart racecontrol.service

# ── 5. Datenbank-Initialisierung prüfen ────────────────
echo ""
echo "[5/5] Warte auf Dienst-Start und DB-Initialisierung ..."
sleep 4

if systemctl is-active --quiet racecontrol.service; then
    echo "      Dienst läuft ✓"

    # Erreichbarkeit testen
    if curl -sf --max-time 5 http://localhost:1980/health > /dev/null 2>&1; then
        echo "      API antwortet ✓  →  http://$(hostname -I | awk '{print $1}'):1980"
    else
        echo "      API noch nicht bereit – warte weitere 5 s ..."
        sleep 5
        if curl -sf --max-time 5 http://localhost:1980/health > /dev/null 2>&1; then
            echo "      API antwortet ✓"
        else
            echo "  ⚠  API antwortet nicht – Logs prüfen: sudo journalctl -u racecontrol -f"
        fi
    fi
else
    echo "  ⚠  Dienst läuft nicht – Logs prüfen:"
    echo "     sudo journalctl -u racecontrol --since '1 minute ago'"
fi

# ── Ergebnis ──────────────────────────────────────────
IP=$(hostname -I | awk '{print $1}')
echo ""
echo "=================================================="
echo "  Setup abgeschlossen!"
echo ""
echo "  RaceControl Pro erreichbar unter:"
echo "    http://$IP:1980"
echo ""
echo "  Dienst-Befehle:"
echo "    Status  : sudo systemctl status racecontrol"
echo "    Logs    : sudo journalctl -u racecontrol -f"
echo "    Neustart: sudo systemctl restart racecontrol"
echo ""
echo "  Nach einem Update (deploy.ps1 neu ausführen):"
echo "    sudo systemctl restart racecontrol"
echo "=================================================="
