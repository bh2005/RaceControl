#!/usr/bin/env bash
# deploy.sh
# Überträgt das RaceControl-Backend, das gebaute Frontend und Assets
# per rsync/scp auf den Raspberry Pi Compute Module 3 (Veranstaltungsserver).
#
# Aufruf:
#   ./deploy.sh                              # Standard: cm3-racecontrol.local / pi
#   ./deploy.sh 192.168.1.100               # mit IP-Adresse
#   ./deploy.sh 192.168.1.100 pi            # mit IP + Benutzer
#   ./deploy.sh 192.168.1.100 pi --skip-build

set -e

CM_HOST="${1:-cm3-racecontrol.local}"
CM_USER="${2:-pi}"
SKIP_BUILD="${3:-}"
TARGET="${CM_USER}@${CM_HOST}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

BACKEND_DIR="$REPO_ROOT/backend"
FRONTEND_DIST="$REPO_ROOT/frontend/dist"
ASSETS_DIR="$REPO_ROOT/assets"
SCHEMA_FILE="$REPO_ROOT/schema.sql"

echo ""
echo "=================================================="
echo "  RaceControl Pro – CM3 Deploy (Linux/macOS)"
echo "=================================================="
echo "  Ziel   : $TARGET:/home/pi/racecontrol/"
echo "  Backend: $BACKEND_DIR"
echo "  Dist   : $FRONTEND_DIST"
echo ""

# ── Abhängigkeiten prüfen ─────────────────────────────
for cmd in rsync scp ssh; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "FEHLER: '$cmd' nicht gefunden."
        echo "        Installieren: sudo apt install openssh-client rsync"
        exit 1
    fi
done

# ── Frontend bauen wenn nötig ─────────────────────────
if [ -z "$SKIP_BUILD" ]; then
    if [ ! -d "$FRONTEND_DIST" ]; then
        echo "[BUILD] frontend/dist nicht gefunden – starte npm run build ..."
        FRONTEND_DIR="$REPO_ROOT/frontend"
        if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
            echo "        Installiere Node-Abhängigkeiten (npm install) ..."
            (cd "$FRONTEND_DIR" && npm install)
        fi
        (cd "$FRONTEND_DIR" && npm run build)
        echo "        Build abgeschlossen."
    else
        echo "[BUILD] frontend/dist vorhanden – kein Rebuild nötig."
        echo "        (Neu bauen: rm -rf ../../frontend/dist && ./deploy.sh)"
    fi
else
    echo "[BUILD] übersprungen (--skip-build)."
fi

echo ""

# ── Zielverzeichnisse anlegen ─────────────────────────
echo "[1/5] Bereite Verzeichnisse auf CM3 vor ..."
ssh "$TARGET" "mkdir -p ~/racecontrol/backend ~/racecontrol/frontend ~/racecontrol/assets"

# ── Backend übertragen (ohne Tests und Cache) ─────────
echo "[2/5] Übertrage Backend ..."
rsync -a --delete \
    --exclude='__pycache__/' \
    --exclude='tests/' \
    --exclude='*.pyc' \
    --exclude='*.db' \
    --exclude='.pytest_cache/' \
    --exclude='conftest.py' \
    "$BACKEND_DIR/" "${TARGET}:~/racecontrol/backend/"
echo "      Backend übertragen ✓"

# ── schema.sql übertragen ─────────────────────────────
echo "[3/5] Übertrage schema.sql ..."
scp "$SCHEMA_FILE" "${TARGET}:~/racecontrol/"
echo "      schema.sql übertragen ✓"

# ── Frontend-Dist übertragen ──────────────────────────
echo "[4/5] Übertrage frontend/dist ..."
rsync -a --delete "$FRONTEND_DIST/" "${TARGET}:~/racecontrol/frontend/dist/"
echo "      frontend/dist übertragen ✓"

# ── Assets übertragen ─────────────────────────────────
if [ -d "$ASSETS_DIR" ]; then
    echo "[5/5] Übertrage assets ..."
    rsync -a "$ASSETS_DIR/" "${TARGET}:~/racecontrol/assets/"
    echo "      assets übertragen ✓"
else
    echo "[5/5] assets-Verzeichnis nicht gefunden – übersprungen."
fi

# ── Setup-Dateien übertragen ──────────────────────────
echo ""
echo "[+]  Übertrage Setup-Dateien ..."
scp "$SCRIPT_DIR/install.sh" "$SCRIPT_DIR/racecontrol.service" "${TARGET}:~/racecontrol/"
ssh "$TARGET" "chmod +x ~/racecontrol/install.sh"
echo "     Setup-Dateien übertragen ✓"

# ── Ergebnis ──────────────────────────────────────────
echo ""
echo "=================================================="
echo "  Alle Dateien erfolgreich übertragen!"
echo ""
echo "  Weiter auf dem CM3 (SSH):"
echo "    ssh $TARGET"
echo "    cd ~/racecontrol"
echo "    sudo ./install.sh"
echo ""
echo "  Oder direkt von hier (Erstinstallation):"
echo "    ssh $TARGET 'cd ~/racecontrol && sudo ./install.sh'"
echo ""
echo "  Nach einem Update (Re-Deploy + Neustart):"
echo "    ./deploy.sh $CM_HOST $CM_USER"
echo "    ssh $TARGET 'sudo systemctl restart racecontrol'"
echo "=================================================="
