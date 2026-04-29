<#
.SYNOPSIS
    Baut RaceControl Pro als Windows-Installer (PyInstaller + Inno Setup).

.DESCRIPTION
    Schritt 1: Vue-Frontend bauen  (npm run build)
    Schritt 2: Python-Bundle       (pyinstaller racecontrol.spec)
    Schritt 3: Installer erstellen (iscc installer.iss)

.PARAMETER Version
    Versionsnummer für den Installer-Dateinamen (Standard: 0.6.0)

.PARAMETER SkipFrontend
    npm-Build überspringen (wenn dist\ bereits aktuell ist)

.PARAMETER SkipPyInstaller
    PyInstaller-Schritt überspringen

.PARAMETER SkipInnoSetup
    Inno-Setup-Schritt überspringen

.EXAMPLE
    # Vollständiger Build:
    .\build.ps1

    # Nur Installer neu bauen (Bundle bereits vorhanden):
    .\build.ps1 -SkipFrontend -SkipPyInstaller

.REQUIREMENTS
    - Node.js + npm    (Frontend-Build)
    - Python 3.12+     (im PATH)
    - PyInstaller      (pip install pyinstaller)
    - pystray + Pillow (pip install pystray pillow)  -- optional, für Tray-Icon
    - Inno Setup 6     (https://jrsoftware.org/isdl.php)
#>
param(
    [string]$Version      = "0.6.0",
    [switch]$SkipFrontend,
    [switch]$SkipPyInstaller,
    [switch]$SkipInnoSetup
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot          # Arbeitsverzeichnis = Windows/

$ProjectRoot = Split-Path $PSScriptRoot -Parent

Write-Host ""
Write-Host "══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  RaceControl Pro  –  Windows-Build  v$Version" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Projektordner : $ProjectRoot"
Write-Host "  Build-Ordner  : $PSScriptRoot"
Write-Host ""

# ── 1. Vue-Frontend ──────────────────────────────────────────────────────────
if (-not $SkipFrontend) {
    Write-Host "[1/3] Vue-Frontend bauen..." -ForegroundColor Yellow
    Push-Location "$ProjectRoot\frontend"
    try {
        Write-Host "      npm install"
        npm install --loglevel=warn
        if ($LASTEXITCODE -ne 0) { throw "npm install fehlgeschlagen (Exit $LASTEXITCODE)" }

        Write-Host "      npm run build"
        npm run build
        if ($LASTEXITCODE -ne 0) { throw "npm run build fehlgeschlagen (Exit $LASTEXITCODE)" }

        $distSize = (Get-ChildItem "$ProjectRoot\frontend\dist" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
        Write-Host "      OK – frontend\dist\ ($([math]::Round($distSize,1)) MB)" -ForegroundColor Green
    } finally {
        Pop-Location
    }
} else {
    Write-Host "[1/3] Frontend-Build übersprungen" -ForegroundColor Gray
    if (-not (Test-Path "$ProjectRoot\frontend\dist\index.html")) {
        Write-Warning "frontend\dist\index.html nicht gefunden – bitte zuerst 'npm run build' ausführen!"
    }
}

# ── 2. PyInstaller ───────────────────────────────────────────────────────────
if (-not $SkipPyInstaller) {
    Write-Host ""
    Write-Host "[2/3] PyInstaller-Bundle erstellen..." -ForegroundColor Yellow

    # Abhängigkeiten sicherstellen
    Write-Host "      pip install (Backend + PyInstaller + optional Tray)"
    pip install --quiet --upgrade `
        pyinstaller `
        pystray pillow `
        -r "$ProjectRoot\backend\requirements.txt"
    if ($LASTEXITCODE -ne 0) { throw "pip install fehlgeschlagen" }

    # Alten Build löschen
    if (Test-Path "dist") {
        Remove-Item "dist" -Recurse -Force
        Write-Host "      Altes dist\ gelöscht"
    }
    if (Test-Path "build") {
        Remove-Item "build" -Recurse -Force
        Write-Host "      Altes build\ gelöscht"
    }

    Write-Host "      pyinstaller racecontrol.spec"
    pyinstaller racecontrol.spec --noconfirm
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller fehlgeschlagen" }

    $bundleSize = (Get-ChildItem "dist\racecontrol" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "      OK – Windows\dist\racecontrol\ ($([math]::Round($bundleSize,0)) MB)" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[2/3] PyInstaller übersprungen" -ForegroundColor Gray
    if (-not (Test-Path "dist\racecontrol\racecontrol.exe")) {
        Write-Warning "dist\racecontrol\racecontrol.exe nicht gefunden!"
    }
}

# ── 3. Inno Setup ────────────────────────────────────────────────────────────
if (-not $SkipInnoSetup) {
    Write-Host ""
    Write-Host "[3/3] Inno Setup Installer kompilieren..." -ForegroundColor Yellow

    # iscc.exe suchen
    $iscc = $null
    $candidates = @(
        "iscc",
        "C:\Program Files (x86)\Inno Setup 6\iscc.exe",
        "C:\Program Files\Inno Setup 6\iscc.exe",
        "$env:ProgramFiles\Inno Setup 6\iscc.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 6\iscc.exe"
    )
    foreach ($c in $candidates) {
        $found = Get-Command $c -ErrorAction SilentlyContinue
        if ($found) { $iscc = $found.Source; break }
        if (Test-Path $c) { $iscc = $c; break }
    }

    if (-not $iscc) {
        Write-Warning @"
iscc.exe nicht gefunden. Bitte Inno Setup 6 installieren:
  https://jrsoftware.org/isdl.php

Inno-Setup-Schritt wird übersprungen.
Den Installer manuell erstellen:
  & "C:\Program Files (x86)\Inno Setup 6\iscc.exe" "$PSScriptRoot\installer.iss"
"@
    } else {
        if (-not (Test-Path "output")) { New-Item -ItemType Directory -Path "output" | Out-Null }

        Write-Host "      $iscc installer.iss"
        & $iscc "installer.iss"
        if ($LASTEXITCODE -ne 0) { throw "Inno Setup fehlgeschlagen (Exit $LASTEXITCODE)" }

        $outputFile = "output\RaceControl-Pro-Setup-$Version.exe"
        $setupSize  = [math]::Round((Get-Item $outputFile).Length / 1MB, 0)
        Write-Host "      OK – $outputFile ($setupSize MB)" -ForegroundColor Green
    }
} else {
    Write-Host ""
    Write-Host "[3/3] Inno Setup übersprungen" -ForegroundColor Gray
}

# ── Zusammenfassung ──────────────────────────────────────────────────────────
Write-Host ""
Write-Host "══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Build abgeschlossen!" -ForegroundColor Green
if (Test-Path "output\RaceControl-Pro-Setup-$Version.exe") {
    Write-Host "  Installer: Windows\output\RaceControl-Pro-Setup-$Version.exe" -ForegroundColor Green
}
Write-Host "══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
