# deploy.ps1
# Überträgt alle LSU200-Dateien per SCP von Windows auf den Raspberry Pi 2.
#
# Aufruf (PowerShell):
#   .\deploy.ps1                          # Standard: Host=pi2-lsu200 User=pi
#   .\deploy.ps1 -PiHost 192.168.1.50    # mit IP-Adresse
#   .\deploy.ps1 -PiHost pi2-lsu200 -PiUser pi

param(
    [string]$PiHost = "pi2-lsu200",   # Hostname oder IP-Adresse des Pi 2
    [string]$PiUser = "pi"
)

$ErrorActionPreference = "Stop"

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot   = Split-Path -Parent (Split-Path -Parent $ScriptDir)
$ClientScript = Join-Path $RepoRoot "lichtschranken\LSU200\lsu200_linux_client.py"
$Target     = "${PiUser}@${PiHost}"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  RaceControl Pro – Pi2 LSU200 Deploy" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Ziel  : $Target"
Write-Host "  Skript: $ClientScript"
Write-Host ""

# Prüfen ob scp verfügbar ist
if (-not (Get-Command scp -ErrorAction SilentlyContinue)) {
    Write-Host "FEHLER: scp nicht gefunden." -ForegroundColor Red
    Write-Host "        OpenSSH ist ab Windows 10 integriert." -ForegroundColor Red
    Write-Host "        Einstellungen → Apps → Optionale Features → OpenSSH-Client" -ForegroundColor Red
    exit 1
}

# Prüfen ob Python-Client vorhanden ist
if (-not (Test-Path $ClientScript)) {
    Write-Host "FEHLER: $ClientScript nicht gefunden." -ForegroundColor Red
    exit 1
}

# Zielverzeichnis auf Pi anlegen
Write-Host "[1/3] Erstelle ~/lsu200 auf dem Pi ..." -ForegroundColor Yellow
ssh $Target "mkdir -p ~/lsu200"

# Python-Client übertragen
Write-Host "[2/3] Übertrage lsu200_linux_client.py ..." -ForegroundColor Yellow
scp $ClientScript "${Target}:~/lsu200/"

# Setup-Dateien übertragen
Write-Host "[3/3] Übertrage Setup-Dateien ..." -ForegroundColor Yellow
scp "$ScriptDir\install.sh"     "${Target}:~/lsu200/"
scp "$ScriptDir\lsu200.service" "${Target}:~/lsu200/"
scp "$ScriptDir\.env.example"   "${Target}:~/lsu200/"

# .env übertragen wenn lokal vorhanden (nicht .env.example)
$LocalEnv = Join-Path $ScriptDir ".env"
if (Test-Path $LocalEnv) {
    Write-Host "      Übertrage .env (lokal vorhanden) ..." -ForegroundColor Yellow
    scp $LocalEnv "${Target}:~/lsu200/"
}

# install.sh ausführbar machen
ssh $Target "chmod +x ~/lsu200/install.sh"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "  Dateien erfolgreich übertragen!" -ForegroundColor Green
Write-Host ""
Write-Host "  Weiter auf dem Pi (SSH):" -ForegroundColor White
Write-Host "    ssh $Target" -ForegroundColor Gray
Write-Host "    nano ~/lsu200/.env          # BACKEND_WS + TIMING_API_KEY eintragen" -ForegroundColor Gray
Write-Host "    cd ~/lsu200" -ForegroundColor Gray
Write-Host "    sudo ./install.sh" -ForegroundColor Gray
Write-Host ""
Write-Host "  Oder direkt von hier:" -ForegroundColor White
Write-Host "    ssh $Target 'cd ~/lsu200 && sudo ./install.sh'" -ForegroundColor Gray
Write-Host "==================================================" -ForegroundColor Green
