#!/bin/sh
# =============================================================================
#  RaceControl Pro – Netzwerk-Infrastruktur für OpenWRT
#
#  Was dieses Script macht (auf dem Router):
#    1. DNS: "racecontrol" → Laptop-IP  (für alle WLAN/LAN-Geräte)
#    2. DHCP: Laptop bekommt immer dieselbe IP (statischer Lease)
#
#  Port 80 → 1980 Weiterleitung läuft auf dem LAPTOP (nicht hier),
#  weil LAN-Clients direkt per ARP zur Laptop-IP verbinden –
#  der Router sieht diesen Traffic nicht.
#  → set_infra_laptop.sh auf dem Laptop ausführen!
#
#  Aufruf auf dem Router:
#    scp set_infra_openwrt.sh root@192.168.1.1:/tmp/
#    ssh root@192.168.1.1 "sh /tmp/set_infra_openwrt.sh"
# =============================================================================

set -e

# ── Konfiguration ─────────────────────────────────────────────────────────────
RC_IP="192.168.1.239"
RC_PORT="1980"
RC_HOST="racecontrol"

# ── Farben ────────────────────────────────────────────────────────────────────
G='\033[0;32m'; Y='\033[1;33m'; B='\033[0;34m'; N='\033[0m'
info() { printf "${B}[INFO]${N}  %s\n" "$*"; }
ok()   { printf "${G}[ OK ]${N}  %s\n" "$*"; }
warn() { printf "${Y}[WARN]${N}  %s\n" "$*"; }

printf "\n${G}╔══════════════════════════════════════════════════════╗${N}\n"
printf "${G}║  RaceControl – Netzwerk-Setup für OpenWRT            ║${N}\n"
printf "${G}║  http://racecontrol  →  ${RC_IP}:${RC_PORT}         ║${N}\n"
printf "${G}╚══════════════════════════════════════════════════════╝${N}\n\n"

# ══════════════════════════════════════════════════════════════════════════════
#  SCHRITT 1 – DNS via UCI (dnsmasq address-Liste)
#  Funktioniert auf allen OpenWRT-Versionen ohne confdir-Tricks.
#  "racecontrol" löst für ALLE Geräte im LAN zur Laptop-IP auf.
# ══════════════════════════════════════════════════════════════════════════════
info "Schritt 1/2 – DNS-Eintrag (UCI address-Liste)..."

# Alte confdir-Datei aufräumen, falls vom Vorgänger-Script vorhanden
rm -f /etc/dnsmasq.d/racecontrol.conf

# Bestehende address-Einträge für diesen Host entfernen, damit kein Duplikat entsteht
for ENTRY in $(uci get dhcp.@dnsmasq[0].address 2>/dev/null); do
    case "${ENTRY}" in
        "/${RC_HOST}/"*|"/${RC_HOST}.lan/"*|"/${RC_HOST}.local/"*)
            uci del_list dhcp.@dnsmasq[0].address="${ENTRY}" 2>/dev/null || true
            ;;
    esac
done

uci add_list dhcp.@dnsmasq[0].address="/${RC_HOST}/${RC_IP}"
uci add_list dhcp.@dnsmasq[0].address="/${RC_HOST}.lan/${RC_IP}"
uci add_list dhcp.@dnsmasq[0].address="/${RC_HOST}.local/${RC_IP}"
uci commit dhcp

/etc/init.d/dnsmasq reload 2>/dev/null || /etc/init.d/dnsmasq restart
ok "DNS: '${RC_HOST}' → ${RC_IP}"

# Schnelltest
sleep 1
RESOLVED=$(nslookup "${RC_HOST}" 127.0.0.1 2>/dev/null | awk '/^Address/ && !/127\.0\.0\.1/{print $2}' | head -1)
if [ "${RESOLVED}" = "${RC_IP}" ]; then
    ok "DNS-Auflösung bestätigt: ${RC_HOST} → ${RESOLVED}"
else
    warn "DNS-Test: Auflösung unklar (${RESOLVED:-keine Antwort}) – prüfen mit: nslookup ${RC_HOST} 127.0.0.1"
fi

# ══════════════════════════════════════════════════════════════════════════════
#  SCHRITT 2 – Statischer DHCP-Lease (Laptop bekommt immer dieselbe IP)
# ══════════════════════════════════════════════════════════════════════════════
info "Schritt 2/2 – Statischer DHCP-Lease..."

LAPTOP_MAC=$(arp -n 2>/dev/null | awk "/${RC_IP}/{print \$3}" | head -1)

if [ -n "${LAPTOP_MAC}" ] && [ "${LAPTOP_MAC}" != "<incomplete>" ]; then
    ok "Laptop-MAC gefunden: ${LAPTOP_MAC}"
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
    warn "Laptop einschalten und Script erneut ausführen – ODER manuell:"
    printf "\n"
    printf "  ${Y}# MAC-Adresse des Laptops (auf dem Laptop ausführen):${N}\n"
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
#  ZUSAMMENFASSUNG
# ══════════════════════════════════════════════════════════════════════════════
printf "\n${G}══════════════════════════════════════════════════════${N}\n"
printf "${G}  Router-Setup abgeschlossen!${N}\n"
printf "${G}══════════════════════════════════════════════════════${N}\n\n"

printf "  DNS aktiv für alle WLAN/LAN-Geräte:\n"
printf "    ${G}racecontrol${N}      →  ${RC_IP}\n"
printf "    ${G}racecontrol.lan${N}  →  ${RC_IP}\n\n"

printf "  ${Y}Nächster Schritt: Laptop-Script ausführen!${N}\n"
printf "  Port 80 → ${RC_PORT} Weiterleitung wird auf dem Laptop eingerichtet:\n\n"
printf "    ${G}sudo bash server/set_infra_laptop.sh${N}\n\n"

printf "  Diagnose:\n"
printf "    DNS-Test:  nslookup ${RC_HOST} 127.0.0.1\n"
printf "    Erreichbar (direkt): http://${RC_IP}:${RC_PORT}\n"
printf "\n"

if wget -q --spider --timeout=3 "http://${RC_IP}:${RC_PORT}" 2>/dev/null; then
    ok "RaceControl läuft auf ${RC_IP}:${RC_PORT}"
else
    warn "RaceControl antwortet noch nicht – Laptop starten und set_infra_laptop.sh ausführen"
fi
