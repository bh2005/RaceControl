# deploy.ps1
# Überträgt das RaceControl-Backend, das gebaute Frontend und Assets
# per SCP auf den Raspberry Pi Compute Module 3 (Veranstaltungsserver).
#
# Aufruf (PowerShell):
#   .\deploy.ps1                          # Standard: Host=cm3-racecontrol User=pi
#   .\deploy.ps1 -CmHost 192.168.1.100   # mit IP-Adresse
#   .\deploy.ps1 -CmHost cm3-racecontrol -CmUser pi -SkipBuild

param(
    [string]$CmHost   = "cm3-racecontrol",   # Hostname oder IP des CM3
    [string]$CmUser   = "pi",
    [switch]$SkipBuild                        # Frontend-Build überspringen
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = Split-Path -Parent (Split-Path -Parent $ScriptDir)
$Target    = "${CmUser}@${CmHost}"

$BackendDir  = Join-Path $RepoRoot "backend"
$FrontendDist = Join-Path $RepoRoot "frontend\dist"
$AssetsDir   = Join-Path $RepoRoot "assets"
$SchemaFile  = Join-Path $RepoRoot "schema.sql"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  RaceControl Pro – CM3 Deploy" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Ziel   : ${Target}:/home/pi/racecontrol/"
Write-Host "  Backend: $BackendDir"
Write-Host "  Dist   : $FrontendDist"
Write-Host ""

# ── Prüfen ob scp verfügbar ist ───────────────────────
if (-not (Get-Command scp -ErrorAction SilentlyContinue)) {
    Write-Host "FEHLER: scp nicht gefunden." -ForegroundColor Red
    Write-Host "        OpenSSH ist ab Windows 10 integriert." -ForegroundColor Red
    Write-Host "        Einstellungen → Apps → Optionale Features → OpenSSH-Client" -ForegroundColor Red
    exit 1
}

# ── Frontend bauen wenn nötig ─────────────────────────
if (-not $SkipBuild) {
    if (-not (Test-Path $FrontendDist)) {
        Write-Host "[BUILD] frontend/dist nicht gefunden – starte npm run build ..." -ForegroundColor Yellow
        $FrontendDir = Join-Path $RepoRoot "frontend"
        if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
            Write-Host "        Installiere Node-Abhängigkeiten (npm install) ..." -ForegroundColor Gray
            Push-Location $FrontendDir
            npm install
            Pop-Location
        }
        Push-Location $FrontendDir
        npm run build
        Pop-Location
        Write-Host "        Build abgeschlossen." -ForegroundColor Green
    } else {
        Write-Host "[BUILD] frontend/dist vorhanden – kein Rebuild nötig." -ForegroundColor Gray
        Write-Host "        (Neu bauen und übertragen: .\deploy.ps1 ohne -SkipBuild)" -ForegroundColor Gray
    }
} else {
    Write-Host "[BUILD] übersprungen (-SkipBuild)." -ForegroundColor Gray
}

Write-Host ""

# ── Zielverzeichnisse anlegen ─────────────────────────
Write-Host "[1/5] Bereite Verzeichnisse auf CM3 vor ..." -ForegroundColor Yellow
ssh $Target "mkdir -p ~/racecontrol/backend ~/racecontrol/frontend ~/racecontrol/assets"

# ── Backend übertragen (ohne Tests und Cache) ─────────
Write-Host "[2/5] Übertrage Backend ..." -ForegroundColor Yellow

# Saubere Staging-Kopie ohne __pycache__ und tests/
$TempBackend = Join-Path $env:TEMP "rc_deploy_backend_$(Get-Random)"
New-Item -ItemType Directory -Force -Path $TempBackend | Out-Null

# robocopy: /E = inkl. Unterverzeichnisse, /XD = exclude dirs, /XF = exclude files
# Exit-Code 0-7 ist OK für robocopy (0=nix kopiert, 1=Dateien kopiert, etc.)
$null = robocopy $BackendDir $TempBackend /E `
    /XD __pycache__ tests .pytest_cache `
    /XF "*.pyc" "*.db" ".coverage" "conftest.py"
if ($LASTEXITCODE -gt 7) {
    Write-Host "FEHLER: robocopy fehlgeschlagen (Exit $LASTEXITCODE)" -ForegroundColor Red
    exit 1
}

scp -r "$TempBackend\*" "${Target}:~/racecontrol/backend/"
Remove-Item $TempBackend -Recurse -Force
Write-Host "        Backend übertragen ✓" -ForegroundColor Gray

# ── schema.sql übertragen ─────────────────────────────
Write-Host "[3/5] Übertrage schema.sql ..." -ForegroundColor Yellow
scp $SchemaFile "${Target}:~/racecontrol/"
Write-Host "        schema.sql übertragen ✓" -ForegroundColor Gray

# ── Frontend-Dist übertragen ──────────────────────────
Write-Host "[4/5] Übertrage frontend/dist ..." -ForegroundColor Yellow
scp -r $FrontendDist "${Target}:~/racecontrol/frontend/"
Write-Host "        frontend/dist übertragen ✓" -ForegroundColor Gray

# ── Assets übertragen ─────────────────────────────────
if (Test-Path $AssetsDir) {
    Write-Host "[5/5] Übertrage assets ..." -ForegroundColor Yellow
    scp -r $AssetsDir "${Target}:~/racecontrol/"
    Write-Host "        assets übertragen ✓" -ForegroundColor Gray
} else {
    Write-Host "[5/5] assets-Verzeichnis nicht gefunden – übersprungen." -ForegroundColor Gray
}

# ── Setup-Dateien übertragen ──────────────────────────
Write-Host ""
Write-Host "[+]  Übertrage Setup-Dateien ..." -ForegroundColor Yellow
scp "$ScriptDir\install.sh"         "${Target}:~/racecontrol/"
scp "$ScriptDir\racecontrol.service" "${Target}:~/racecontrol/"
ssh $Target "chmod +x ~/racecontrol/install.sh"
Write-Host "     Setup-Dateien übertragen ✓" -ForegroundColor Gray

# ── Ergebnis ──────────────────────────────────────────
Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "  Alle Dateien erfolgreich übertragen!" -ForegroundColor Green
Write-Host ""
Write-Host "  Weiter auf dem CM3 (SSH):" -ForegroundColor White
Write-Host "    ssh $Target" -ForegroundColor Gray
Write-Host "    cd ~/racecontrol" -ForegroundColor Gray
Write-Host "    sudo ./install.sh" -ForegroundColor Gray
Write-Host ""
Write-Host "  Oder direkt von hier (Erstinstallation):" -ForegroundColor White
Write-Host "    ssh $Target 'cd ~/racecontrol && sudo ./install.sh'" -ForegroundColor Gray
Write-Host ""
Write-Host "  Nach einem Update (Re-Deploy + Neustart):" -ForegroundColor White
Write-Host "    .\deploy.ps1 -CmHost $CmHost" -ForegroundColor Gray
Write-Host "    ssh $Target 'sudo systemctl restart racecontrol'" -ForegroundColor Gray
Write-Host "==================================================" -ForegroundColor Green
