#!/bin/sh
# =============================================================================
#  RaceControl Pro – Netzwerk-Infrastruktur für OpenWRT
#  http://racecontrol  →  http://192.168.1.239:1980  (inkl. WebSocket!)
#
#  Aufruf auf dem Router:
#    scp setup_racecontrol_network.sh root@192.168.1.1:/tmp/
#    ssh root@192.168.1.1 "sh /tmp/setup_racecontrol_network.sh"
# =============================================================================

set -e

# ── Konfiguration ─────────────────────────────────────────────────────────────
RC_IP="192.168.1.239"
RC_PORT="1980"
RC_HOST="racecontrol"

# ── Farben ────────────────────────────────────────────────────────────────────
G='\033[0;32m'; Y='\033[1;33m'; B='\033[0;34m'; R='\033[0;31m'; N='\033[0m'
info() { printf "${B}[INFO]${N}  %s\n" "$*"; }
ok()   { printf "${G}[ OK ]${N}  %s\n" "$*"; }
warn() { printf "${Y}[WARN]${N}  %s\n" "$*"; }
fail() { printf "${R}[FAIL]${N}  %s\n" "$*"; exit 1; }

printf "\n${G}╔══════════════════════════════════════════════════════╗${N}\n"
printf "${G}║  RaceControl – Netzwerk-Setup für OpenWRT            ║${N}\n"
printf "${G}║  http://racecontrol  →  ${RC_IP}:${RC_PORT}         ║${N}\n"
printf "${G}╚══════════════════════════════════════════════════════╝${N}\n\n"

# ══════════════════════════════════════════════════════════════════════════════
#  SCHRITT 1 – DNS via dnsmasq
#  "racecontrol" löst für ALLE Geräte im LAN zur Laptop-IP auf
# ══════════════════════════════════════════════════════════════════════════════
info "Schritt 1/3 – DNS-Eintrag (dnsmasq)..."

DNS_CONF="/etc/dnsmasq.d/racecontrol.conf"
mkdir -p /etc/dnsmasq.d

cat > "${DNS_CONF}" << EOF
# RaceControl Pro – DNS
# Erstellt von setup_racecontrol_network.sh
address=/${RC_HOST}/${RC_IP}
address=/${RC_HOST}.lan/${RC_IP}
address=/${RC_HOST}.local/${RC_IP}
EOF

/etc/init.d/dnsmasq reload 2>/dev/null || /etc/init.d/dnsmasq restart
ok "DNS: '${RC_HOST}' → ${RC_IP}"

# ══════════════════════════════════════════════════════════════════════════════
#  SCHRITT 2 – Reverse Proxy mit WebSocket-Support
#
#  OpenWRT nutzt UCI zur nginx-Konfiguration – direkte .conf-Dateien werden
#  von /etc/init.d/nginx bei jedem Start ÜBERSCHRIEBEN.
#  Lösung: include-Datei in /etc/nginx/conf.d/ die UCI nicht anfasst,
#  PLUS die UCI-Hauptkonfiguration so anpassen dass conf.d eingebunden wird.
# ══════════════════════════════════════════════════════════════════════════════
info "Schritt 2/3 – Reverse Proxy (nginx + WebSocket)..."

# nginx installieren falls nicht vorhanden
if ! which nginx >/dev/null 2>&1; then
    info "  Installiere nginx..."
    opkg update -q 2>/dev/null || true
    opkg install nginx 2>/dev/null || fail "nginx konnte nicht installiert werden. Manuell: opkg install nginx"
fi
ok "nginx verfügbar."

# ── Haupt-nginx.conf prüfen und ggf. anpassen ─────────────────────────────────
# OpenWRT generiert /var/lib/nginx/uci.conf aus UCI.
# Wir hängen eine eigene include-Direktive an die nginx.conf an,
# damit unsere WebSocket-Proxy-Config nicht überschrieben wird.

NGINX_MAIN="/etc/nginx/nginx.conf"
NGINX_PROXY_CONF="/etc/nginx/conf.d/racecontrol_proxy.conf"

mkdir -p /etc/nginx/conf.d

# ── Proxy-Konfiguration schreiben ─────────────────────────────────────────────
# Wichtig für PWA/WebSocket:
#   - proxy_http_version 1.1        (WebSocket braucht HTTP/1.1)
#   - Upgrade + Connection Header   (WebSocket Handshake)
#   - proxy_buffering off           (Echtzeit-Push, kein Puffer)
#   - proxy_read_timeout 3600s      (lange WS-Verbindungen nicht trennen)

cat > "${NGINX_PROXY_CONF}" << EOF
# RaceControl Pro – Reverse Proxy mit WebSocket-Support
# Erstellt von setup_racecontrol_network.sh
# NICHT manuell bearbeiten – Script erneut ausführen zum Ändern.

# Upgrade-Map: normaler HTTP-Request bekommt "close", WebSocket bekommt "upgrade"
map \$http_upgrade \$connection_upgrade {
    default   upgrade;
    ''        close;
}

server {
    listen 80;
    server_name ${RC_HOST} ${RC_HOST}.lan ${RC_HOST}.local;

    # ── Alle Anfragen (HTTP + WebSocket) an RaceControl weiterleiten ──
    location / {
        proxy_pass         http://${RC_IP}:${RC_PORT};
        proxy_http_version 1.1;

        # WebSocket-Upgrade-Header (Pflicht für Livetiming / PWA-Push)
        proxy_set_header   Upgrade           \$http_upgrade;
        proxy_set_header   Connection        \$connection_upgrade;

        # Originalhost und Client-IP weitergeben
        proxy_set_header   Host              \$host;
        proxy_set_header   X-Real-IP         \$remote_addr;
        proxy_set_header   X-Forwarded-For   \$proxy_add_x_forwarded_for;

        # Kein Puffer – sonst kommen Echtzeit-Updates verzögert an
        proxy_buffering    off;

        # Timeout hoch setzen: WebSocket-Verbindungen leben lange
        proxy_read_timeout  3600s;
        proxy_send_timeout  3600s;
        proxy_connect_timeout 10s;
    }
}
EOF

ok "nginx Proxy-Konfiguration geschrieben: ${NGINX_PROXY_CONF}"

# ── Sicherstellen dass conf.d in nginx.conf eingebunden ist ───────────────────
# OpenWRT's UCI-generierte nginx.conf enthält manchmal kein include conf.d/*.conf
if [ -f "${NGINX_MAIN}" ]; then
    if ! grep -q "conf\.d" "${NGINX_MAIN}"; then
        # include-Zeile vor das letzte } einfügen
        sed -i 's|^}$|    include /etc/nginx/conf.d/*.conf;\n}|' "${NGINX_MAIN}"
        ok "nginx.conf: include conf.d/*.conf hinzugefügt."
    else
        ok "nginx.conf: conf.d bereits eingebunden."
    fi
else
    # Keine nginx.conf vorhanden → minimale eigene erstellen
    warn "Keine ${NGINX_MAIN} gefunden – erstelle minimale Konfiguration."
    cat > "${NGINX_MAIN}" << 'NGINXMAIN'
worker_processes  1;
error_log  /var/log/nginx/error.log warn;
pid        /var/run/nginx.pid;

events {
    worker_connections  256;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    sendfile      on;
    keepalive_timeout 65;

    include /etc/nginx/conf.d/*.conf;
}
NGINXMAIN
fi

# ── nginx starten / neu laden ─────────────────────────────────────────────────
/etc/init.d/nginx enable 2>/dev/null || true

# Konfiguration testen vor dem Neustart
if nginx -t 2>/dev/null; then
    if /etc/init.d/nginx reload 2>/dev/null; then
        ok "nginx neu geladen."
    else
        /etc/init.d/nginx start && ok "nginx gestartet." || warn "nginx start fehlgeschlagen – siehe: logread | grep nginx"
    fi
else
    warn "nginx Konfigurationstest fehlgeschlagen!"
    warn "Prüfe mit: nginx -t"
    warn "Logs:       logread | grep nginx"
fi

# ══════════════════════════════════════════════════════════════════════════════
#  SCHRITT 3 – Statischer DHCP-Lease (Laptop bekommt immer dieselbe IP)
# ══════════════════════════════════════════════════════════════════════════════
info "Schritt 3/3 – Statischer DHCP-Lease..."

# Versuche MAC automatisch zu ermitteln (ARP-Tabelle)
LAPTOP_MAC=$(arp -n 2>/dev/null | awk "/${RC_IP}/{print \$3}" | head -1)

if [ -n "${LAPTOP_MAC}" ] && [ "${LAPTOP_MAC}" != "<incomplete>" ]; then
    ok "Laptop-MAC gefunden: ${LAPTOP_MAC}"
    info "  Trage statischen DHCP-Lease ein..."

    # Prüfen ob Lease bereits existiert
    EXISTING=$(uci show dhcp 2>/dev/null | grep -c "${LAPTOP_MAC}" || true)
    if [ "${EXISTING}" -gt 0 ]; then
        warn "  Lease für ${LAPTOP_MAC} existiert bereits – überspringe."
    else
        uci add dhcp host
        uci set dhcp.@host[-1].name='racecontrol-laptop'
        uci set dhcp.@host[-1].mac="${LAPTOP_MAC}"
        uci set dhcp.@host[-1].ip="${RC_IP}"
        uci set dhcp.@host[-1].leasetime='infinite'
        uci commit dhcp
        /etc/init.d/dnsmasq reload
        ok "Statischer DHCP-Lease eingetragen: ${LAPTOP_MAC} → ${RC_IP}"
    fi
else
    warn "Laptop (${RC_IP}) gerade nicht im ARP-Cache."
    warn "Bitte Laptop einschalten und Script erneut ausführen, ODER manuell:"
    printf "\n"
    printf "  ${Y}# MAC-Adresse des Laptops ermitteln (auf dem Laptop):${N}\n"
    printf "  ${Y}  Linux:   ip link show${N}\n"
    printf "  ${Y}  Windows: ipconfig /all${N}\n"
    printf "\n"
    printf "  ${Y}# Dann auf dem Router (MAC ersetzen!):${N}\n"
    printf "  ${Y}uci add dhcp host${N}\n"
    printf "  ${Y}uci set dhcp.@host[-1].name='racecontrol-laptop'${N}\n"
    printf "  ${Y}uci set dhcp.@host[-1].mac='AA:BB:CC:DD:EE:FF'${N}\n"
    printf "  ${Y}uci set dhcp.@host[-1].ip='${RC_IP}'${N}\n"
    printf "  ${Y}uci set dhcp.@host[-1].leasetime='infinite'${N}\n"
    printf "  ${Y}uci commit dhcp && /etc/init.d/dnsmasq reload${N}\n"
fi

# ══════════════════════════════════════════════════════════════════════════════
#  ZUSAMMENFASSUNG & SCHNELLTEST
# ══════════════════════════════════════════════════════════════════════════════
printf "\n${G}══════════════════════════════════════════════════════${N}\n"
printf "${G}  Setup abgeschlossen!${N}\n"
printf "${G}══════════════════════════════════════════════════════${N}\n\n"

printf "  Erreichbar für alle Geräte im WLAN/LAN:\n\n"
printf "    ${G}http://racecontrol${N}             ← empfohlen (sauber)\n"
printf "    ${G}http://racecontrol.lan${N}\n"
printf "    ${G}http://${RC_IP}:${RC_PORT}${N}        ← direkter Zugriff (ohne Proxy)\n"
printf "\n"
printf "  WebSocket:\n"
printf "    ${G}✓${N} map-Block leitet WS-Upgrade korrekt weiter\n"
printf "    ${G}✓${N} proxy_buffering off  → Echtzeit-Push ohne Verzögerung\n"
printf "    ${G}✓${N} Timeout 3600s        → PWA-Verbindung bleibt stabil\n"
printf "\n"
printf "  Diagnose-Befehle:\n"
printf "    DNS-Test:    nslookup ${RC_HOST} 127.0.0.1\n"
printf "    nginx-Test:  nginx -t\n"
printf "    nginx-Log:   logread | grep nginx\n"
printf "    WS-Test:     curl -i -N \\\\\n"
printf "                   -H 'Upgrade: websocket' \\\\\n"
printf "                   -H 'Connection: Upgrade' \\\\\n"
printf "                   http://${RC_HOST}/ws\n"
printf "\n"

# Schnelltest ob RaceControl gerade läuft
if wget -q --spider --timeout=3 "http://${RC_IP}:${RC_PORT}" 2>/dev/null; then
    ok "RaceControl läuft – jetzt erreichbar unter http://${RC_HOST}"
else
    warn "RaceControl antwortet gerade nicht auf ${RC_IP}:${RC_PORT}"
    warn "Sobald der Laptop gestartet ist, funktioniert http://${RC_HOST}"
fi
