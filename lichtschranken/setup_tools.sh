#!/usr/bin/env bash
# RaceControl Pro – Tools Setup
#
# Richtet alle Timing-Clients ein:
#   - ALGE Timy (alge_timy_client.py, alge_multi_timy_client.py)
#   - ELV LSU200 serial (lsu200_client.py)
#   - ELV LSU200 Linux/USB (lsu200_linux_client.py) — inkl. udev
#   - u-blox 8 GPS Monitor (ublox8_gps_client.py)
#
# Plattform: Linux / macOS / Windows (Git Bash)
#
# Verwendung:
#   bash setup_tools.sh
#   bash setup_tools.sh --backend http://192.168.1.100:1980

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"
BACKEND_URL="${1:-}"

echo "=================================================="
echo "  RaceControl Pro – Tools Setup"
echo "=================================================="
echo ""

# ── [1/4] Python-Version prüfen ───────────────────────
echo "[1/4] Prüfe Python-Version ..."

PY=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        MAJOR=$(echo "$VER" | cut -d. -f1)
        MINOR=$(echo "$VER" | cut -d. -f2)
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 10 ]; then
            PY="$cmd"
            break
        fi
    fi
done

if [ -z "$PY" ]; then
    echo ""
    echo "  FEHLER: Python 3.10 oder neuer wird benötigt."
    echo "  Aktuell installiert: $(python3 --version 2>/dev/null || echo 'nicht gefunden')"
    echo "  → https://www.python.org/downloads/"
    exit 1
fi

echo "      Python $VER gefunden: $(command -v $PY)"

# ── [2/4] pip-Abhängigkeiten installieren ─────────────
echo ""
echo "[2/4] Installiere Python-Abhängigkeiten ..."

# pip bevorzugen, Fallback auf pip3
PIP=""
for cmd in pip pip3; do
    if command -v "$cmd" &>/dev/null; then
        PIP="$cmd"
        break
    fi
done

if [ -z "$PIP" ]; then
    echo "  FEHLER: pip nicht gefunden."
    exit 1
fi

# Basis-Pakete (alle Clients)
"$PIP" install --quiet pyserial websocket-client python-dotenv

echo "      pyserial, websocket-client, python-dotenv installiert"

# pyusb nur auf Linux (für lsu200_linux_client.py)
if [[ "$(uname -s)" == "Linux" ]]; then
    if "$PIP" install --quiet pyusb 2>/dev/null; then
        echo "      pyusb installiert (Linux-USB-Client)"
    else
        echo "      pyusb übersprungen (libusb nicht gefunden – bei Bedarf: sudo apt install libusb-1.0-0)"
    fi
fi

# ── [3/4] .env anlegen / ergänzen ─────────────────────
echo ""
echo "[3/4] Richte .env-Konfiguration ein ..."

if [ ! -f "$ENV_FILE" ]; then
    cp "$SCRIPT_DIR/.env.example" "$ENV_FILE"
    echo "      .env angelegt aus .env.example"
else
    echo "      .env bereits vorhanden – wird nur ergänzt falls nötig"
fi

# Pflichtfelder sicherstellen (anhängen falls noch nicht vorhanden)
for key in TIMING_API_KEY BACKEND_WS TIMY_START_PORT TIMY_FINISH_PORT; do
    if ! grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
        case "$key" in
            TIMING_API_KEY)  echo "TIMING_API_KEY="                             >> "$ENV_FILE" ;;
            BACKEND_WS)      echo "BACKEND_WS=ws://localhost:1980/ws/timing"    >> "$ENV_FILE" ;;
            TIMY_START_PORT) echo "# TIMY_START_PORT=COM3"                      >> "$ENV_FILE" ;;
            TIMY_FINISH_PORT)echo "# TIMY_FINISH_PORT=COM4"                     >> "$ENV_FILE" ;;
        esac
    fi
done

# ── [4/4] API-Key automatisch vom Backend holen ───────
echo ""
echo "[4/4] Suche laufendes RaceControl-Backend ..."

# Backend-URL aus Argument, .env oder Standard ermitteln
if [ -z "$BACKEND_URL" ]; then
    BACKEND_URL=$(grep "^BACKEND_WS=" "$ENV_FILE" 2>/dev/null | cut -d= -f2- | \
        sed 's|ws://|http://|; s|wss://|https://|; s|/ws/timing.*||')
    BACKEND_URL="${BACKEND_URL:-http://localhost:1980}"
fi

API_KEY=""
if command -v curl &>/dev/null; then
    if curl -sf --max-time 3 "$BACKEND_URL/api/settings/" -o /tmp/rc_settings.json 2>/dev/null; then
        API_KEY=$("$PY" -c \
            "import json,sys; d=json.load(open('/tmp/rc_settings.json')); print(d.get('timing_api_key',''))" \
            2>/dev/null || true)
        rm -f /tmp/rc_settings.json
    fi
fi

if [ -n "$API_KEY" ]; then
    if grep -q "^TIMING_API_KEY=" "$ENV_FILE"; then
        sed -i "s|^TIMING_API_KEY=.*|TIMING_API_KEY=$API_KEY|" "$ENV_FILE"
    else
        echo "TIMING_API_KEY=$API_KEY" >> "$ENV_FILE"
    fi
    echo "      TIMING_API_KEY automatisch eingetragen."
else
    echo "      Backend nicht erreichbar – TIMING_API_KEY manuell eintragen:"
    echo "      $ENV_FILE"
    echo "      (Quelle: RaceControl Admin → System → Lichtschranken-Schlüssel)"
fi

# ── Linux-Extras: udev für LSU200 ─────────────────────
if [[ "$(uname -s)" == "Linux" ]]; then
    echo ""
    echo "  Linux erkannt – udev-Regel für ELV LSU200 einrichten?"
    read -r -p "  (für lsu200_linux_client.py) [j/N] " REPLY
    if [[ "$REPLY" =~ ^[jJyY]$ ]]; then
        bash "$SCRIPT_DIR/setup_linux.sh"
    fi
fi

# ── Zusammenfassung ───────────────────────────────────
echo ""
echo "=================================================="
echo "  Setup abgeschlossen!"
echo ""
echo "  Konfiguration:"
echo "    $ENV_FILE"
echo ""
echo "  Verfügbare Clients:"
echo ""
echo "  ALGE Timy (1 Gerät):"
echo "    → COM-Port in alge_timy_client.py: SERIAL_PORT"
echo "    → python alge_timy_client.py"
echo ""
echo "  ALGE Timy (mehrere Geräte):"
echo "    → COM-Ports in .env: TIMY_START_PORT, TIMY_FINISH_PORT"
echo "    → python alge_multi_timy_client.py"
echo ""
echo "  ELV LSU200 (Windows/seriell):"
echo "    → COM-Port in lsu200_client.py: SERIAL_PORT"
echo "    → python lsu200_client.py"
echo ""
if [[ "$(uname -s)" == "Linux" ]]; then
echo "  ELV LSU200 (Linux/USB direkt):"
echo "    → python lsu200_linux_client.py"
echo ""
fi
echo "  u-blox 8 GPS Monitor:"
echo "    → python ublox8_gps_client.py"
echo ""
if ! grep -q "^TIMING_API_KEY=.\+" "$ENV_FILE" 2>/dev/null; then
echo "  WICHTIG: TIMING_API_KEY noch nicht gesetzt!"
echo "    Admin → System → Lichtschranken-Schlüssel → in .env eintragen"
echo ""
fi
echo "=================================================="
