#!/bin/bash
# =============================================================================
#  RaceControl Pro – Port-Weiterleitung auf dem Laptop (Linux)
#
#  Was dieses Script macht:
#    - iptables: Port 80 → 1980 auf dem LAN-Interface (PREROUTING)
#      damit http://racecontrol (Port 80) zu RaceControl weiterleitet
#    - Regel persistent machen (überlebt Neustart)
#
#  Voraussetzung: set_infra_openwrt.sh wurde auf dem Router ausgeführt
#                 (DNS: racecontrol → 192.168.1.239)
#
#  Aufruf:
#    sudo bash server/set_infra_laptop.sh
# =============================================================================

set -e

# ── Konfiguration ─────────────────────────────────────────────────────────────
RC_PORT="1980"
LAN_IF="${LAN_IF:-}"          # leer = automatisch erkennen

# ── Farben ────────────────────────────────────────────────────────────────────
G='\033[0;32m'; Y='\033[1;33m'; B='\033[0;34m'; R='\033[0;31m'; N='\033[0m'
info() { printf "${B}[INFO]${N}  %s\n" "$*"; }
ok()   { printf "${G}[ OK ]${N}  %s\n" "$*"; }
warn() { printf "${Y}[WARN]${N}  %s\n" "$*"; }
fail() { printf "${R}[FAIL]${N}  %s\n" "$*"; exit 1; }

if [ "$(id -u)" -ne 0 ]; then
    fail "Bitte mit sudo ausführen: sudo bash $0"
fi

printf "\n${G}╔══════════════════════════════════════════════════════╗${N}\n"
printf "${G}║  RaceControl – Port-Setup auf dem Laptop             ║${N}\n"
printf "${G}║  Port 80 → ${RC_PORT}  (iptables PREROUTING)          ║${N}\n"
printf "${G}╚══════════════════════════════════════════════════════╝${N}\n\n"

# ══════════════════════════════════════════════════════════════════════════════
#  SCHRITT 1 – LAN-Interface ermitteln
# ══════════════════════════════════════════════════════════════════════════════
info "Schritt 1/3 – LAN-Interface ermitteln..."

if [ -z "${LAN_IF}" ]; then
    # Interface das auf 192.168.1.x liegt
    LAN_IF=$(ip -4 addr show | awk '/inet 192\.168\.1\./{print $NF}' | head -1)
fi

if [ -z "${LAN_IF}" ]; then
    fail "Kein Interface mit 192.168.1.x gefunden. Manuell setzen: LAN_IF=eth0 sudo bash $0"
fi

LAN_IP=$(ip -4 addr show dev "${LAN_IF}" | awk '/inet /{gsub(/\/.*/, ""); print $2}' | head -1)
ok "Interface: ${LAN_IF}  IP: ${LAN_IP}"

# ══════════════════════════════════════════════════════════════════════════════
#  SCHRITT 2 – iptables REDIRECT 80 → RC_PORT
# ══════════════════════════════════════════════════════════════════════════════
info "Schritt 2/3 – iptables REDIRECT Port 80 → ${RC_PORT}..."

# Idempotent: Regel nur setzen wenn noch nicht vorhanden
if iptables -t nat -C PREROUTING -i "${LAN_IF}" -p tcp --dport 80 \
       -j REDIRECT --to-ports "${RC_PORT}" 2>/dev/null; then
    ok "Regel bereits vorhanden – kein Eingriff nötig."
else
    iptables -t nat -A PREROUTING -i "${LAN_IF}" -p tcp --dport 80 \
        -j REDIRECT --to-ports "${RC_PORT}"
    ok "iptables: Port 80 → ${RC_PORT} auf ${LAN_IF} gesetzt."
fi

# ══════════════════════════════════════════════════════════════════════════════
#  SCHRITT 3 – Regel persistent machen
# ══════════════════════════════════════════════════════════════════════════════
info "Schritt 3/3 – Persistenz (überlebt Neustart)..."

RULES_DIR="/etc/iptables"
RULES_FILE="${RULES_DIR}/rules.v4"
SYSTEMD_UNIT="/etc/systemd/system/racecontrol-nat.service"

mkdir -p "${RULES_DIR}"

if command -v iptables-save >/dev/null 2>&1; then
    # Variante A: iptables-persistent (apt install iptables-persistent)
    if dpkg -l iptables-persistent >/dev/null 2>&1; then
        iptables-save > "${RULES_FILE}"
        ok "Regeln in ${RULES_FILE} gespeichert (iptables-persistent)."
    else
        # Variante B: Systemd-Unit die die Regel beim Boot setzt
        cat > "${SYSTEMD_UNIT}" << UNIT
[Unit]
Description=RaceControl Port-80 → ${RC_PORT} NAT
After=network.target

[Service]
Type=oneshot
ExecStart=/sbin/iptables -t nat -C PREROUTING -i ${LAN_IF} -p tcp --dport 80 -j REDIRECT --to-ports ${RC_PORT} || /sbin/iptables -t nat -A PREROUTING -i ${LAN_IF} -p tcp --dport 80 -j REDIRECT --to-ports ${RC_PORT}
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
UNIT
        systemctl daemon-reload
        systemctl enable racecontrol-nat.service
        ok "Systemd-Unit angelegt und aktiviert: racecontrol-nat.service"
    fi
else
    warn "iptables-save nicht gefunden – Regel geht nach Neustart verloren."
    warn "Installieren: sudo apt install iptables-persistent"
fi

# ══════════════════════════════════════════════════════════════════════════════
#  ZUSAMMENFASSUNG & SCHNELLTEST
# ══════════════════════════════════════════════════════════════════════════════
printf "\n${G}══════════════════════════════════════════════════════${N}\n"
printf "${G}  Laptop-Setup abgeschlossen!${N}\n"
printf "${G}══════════════════════════════════════════════════════${N}\n\n"

printf "  Aktive Regel:\n"
iptables -t nat -L PREROUTING -n --line-numbers 2>/dev/null | grep -E "REDIRECT|num" || true
printf "\n"

printf "  Erreichbar für alle Geräte im WLAN/LAN:\n\n"
printf "    ${G}http://racecontrol${N}          ← empfohlen\n"
printf "    ${G}http://racecontrol.lan${N}\n"
printf "    ${G}http://${LAN_IP}:${RC_PORT}${N}     ← direkter Zugriff\n\n"

printf "  WebSocket (Livetiming / PWA-Push):\n"
printf "    ${G}✓${N}  TCP-Redirect transparent – WS funktioniert ohne Proxy\n\n"

printf "  Diagnose:\n"
printf "    Regel prüfen:   sudo iptables -t nat -L PREROUTING -n -v\n"
printf "    Regel entfernen: sudo iptables -t nat -D PREROUTING -i ${LAN_IF} -p tcp --dport 80 -j REDIRECT --to-ports ${RC_PORT}\n\n"

# Funktionstest: RaceControl über Port 80 erreichbar?
if curl -s -o /dev/null -w "%{http_code}" --max-time 3 "http://127.0.0.1:${RC_PORT}/" 2>/dev/null | grep -q "200"; then
    ok "RaceControl läuft auf Port ${RC_PORT} – http://racecontrol ist bereit."
else
    warn "RaceControl antwortet noch nicht auf Port ${RC_PORT}."
    warn "Backend starten: cd backend && uvicorn main:app --host 0.0.0.0 --port ${RC_PORT}"
fi
