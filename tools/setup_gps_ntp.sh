#!/usr/bin/env bash
# RaceControl Pro – GPS-NTP-Server einrichten (u-blox 8, LMDE/Debian)
#
# Konzept: u-blox 8 (USB) → gpsd → chrony → NTP-Server im WLAN
# Alle Raspberry Pis synchronisieren automatisch von diesem Laptop.
#
# Voraussetzung: u-blox 8 per USB angeschlossen (erscheint als /dev/ttyACM0)
# Doku:          RaPi_lichtschranke/BAUANLEITUNG_GPS_NTP_Server.md

set -e

# ── Konfiguration ─────────────────────────────────────────────────────────────
GPS_DEVICE="${GPS_DEVICE:-}"          # leer = automatisch ermitteln
NTP_ALLOW="${NTP_ALLOW:-192.168.0.0/24}"  # WLAN-Netz der Veranstaltung

echo "=================================================="
echo "  RaceControl Pro – GPS-NTP-Server Setup"
echo "  u-blox 8 (USB, CDC ACM)"
echo "=================================================="

# ── GPS-Gerät ermitteln ───────────────────────────────
if [ -z "$GPS_DEVICE" ]; then
    # u-blox 8 meldet sich als CDC ACM → /dev/ttyACM*
    for dev in /dev/ttyACM* /dev/ttyUSB*; do
        if [ -e "$dev" ]; then
            # udevadm auf VID/PID prüfen
            if udevadm info "$dev" 2>/dev/null | grep -q "1546"; then
                GPS_DEVICE="$dev"
                break
            fi
        fi
    done
    # Fallback: erstes ttyACM
    if [ -z "$GPS_DEVICE" ] && [ -e /dev/ttyACM0 ]; then
        GPS_DEVICE="/dev/ttyACM0"
    fi
fi

if [ -z "$GPS_DEVICE" ]; then
    echo ""
    echo "  WARNUNG: u-blox 8 nicht gefunden."
    echo "  Bitte GPS-Maus anschließen und erneut starten,"
    echo "  oder Gerät manuell setzen: GPS_DEVICE=/dev/ttyACM0 bash $0"
    echo ""
    GPS_DEVICE="/dev/ttyACM0"
    echo "  Fahre fort mit Standard-Gerät: $GPS_DEVICE"
fi
echo ""
echo "  GPS-Gerät : $GPS_DEVICE"
echo "  NTP-Netz  : $NTP_ALLOW"
echo ""

# ── [1/5] Pakete installieren ─────────────────────────
echo "[1/5] Installiere gpsd, chrony ..."
sudo apt install -y gpsd gpsd-clients chrony

# ── [2/5] udev-Regel (Symlink /dev/gps0 + Berechtigungen) ────────────────────
echo ""
echo "[2/5] Richte udev-Regel ein ..."
sudo tee /etc/udev/rules.d/99-ublox8.rules > /dev/null << 'EOF'
SUBSYSTEM=="tty", ATTRS{idVendor}=="1546", ATTRS{idProduct}=="01a8", \
    SYMLINK+="gps0", MODE="0666", GROUP="dialout"
EOF
sudo udevadm control --reload-rules && sudo udevadm trigger
echo "      Symlink: /dev/gps0 → $GPS_DEVICE"

# Benutzer zur Gruppe dialout hinzufügen
sudo usermod -aG dialout "$USER"
echo "      Benutzer '$USER' zur Gruppe 'dialout' hinzugefügt"

# ── [3/5] gpsd konfigurieren ──────────────────────────
echo ""
echo "[3/5] Konfiguriere gpsd ..."
sudo tee /etc/default/gpsd > /dev/null << EOF
START_DAEMON="true"
USBAUTO="true"
DEVICES="$GPS_DEVICE"
GPSD_OPTIONS="-n"
EOF
sudo systemctl enable gpsd
sudo systemctl restart gpsd
echo "      gpsd konfiguriert für $GPS_DEVICE"

# ── [4/5] chrony konfigurieren ────────────────────────
echo ""
echo "[4/5] Konfiguriere chrony als GPS-NTP-Server ..."

# Backup der Original-Konfig
if [ ! -f /etc/chrony/chrony.conf.orig ]; then
    sudo cp /etc/chrony/chrony.conf /etc/chrony/chrony.conf.orig
fi

sudo tee /etc/chrony/chrony.conf > /dev/null << EOF
# GPS via gpsd (u-blox 8, NMEA)
# Genauigkeit: ±50–150 ms (u-blox 8 / M8030-KT)
refclock SHM 0 refid GPS precision 1e-1 offset 0.9999 delay 0.2

# Fallback: Internet-NTP wenn verfügbar
server 0.de.pool.ntp.org iburst
server 1.de.pool.ntp.org iburst

# NTP-Server für alle Geräte im lokalen WLAN-Netz
allow $NTP_ALLOW

makestep 1.0 3
rtcsync
EOF

sudo systemctl enable chrony
sudo systemctl restart chrony
echo "      chrony konfiguriert – NTP-Freigabe für $NTP_ALLOW"

# ── [5/5] GPS-Empfang testen ──────────────────────────
echo ""
echo "[5/5] Warte auf GPS-Fix (bis zu 60 s, Ctrl+C zum Überspringen) ..."
echo "      Hinweis: Freie Himmelssicht nötig — unter Dach kann es länger dauern."
echo ""
GPS_OK=false
for i in $(seq 1 12); do
    if gpspipe -w -n 5 2>/dev/null | grep -q '"status":"3D"'; then
        GPS_OK=true
        break
    fi
    printf "      Warte... (%d/12)\r" "$i"
    sleep 5
done
echo ""
if $GPS_OK; then
    echo "      GPS: 3D-Fix erhalten!"
else
    echo "      GPS: Noch kein Fix – bitte nach draußen gehen und"
    echo "      'cgps -s' oder 'chronyc sources' manuell prüfen."
fi

echo ""
echo "=================================================="
echo "  Setup abgeschlossen!"
echo ""
echo "  GPS-Empfang prüfen:"
echo "    cgps -s"
echo ""
echo "  NTP-Synchronisation prüfen:"
echo "    chronyc sources -v"
echo "    chronyc tracking"
echo ""
echo "  Raspberry Pis auf diesen Server zeigen lassen:"
echo "    /etc/chrony/chrony.conf auf den RPis:"
echo "    server <IP-dieses-Laptops> iburst prefer"
echo ""
echo "  Neu anmelden (Gruppe 'dialout' wird aktiv)"
echo "=================================================="
