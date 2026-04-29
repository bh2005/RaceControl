# RaceControl Pro – Windows-Installer bauen

## Übersicht

Der Build-Prozess besteht aus drei Schritten:

```
npm run build          →  frontend/dist/        (Vue-App)
pyinstaller            →  Windows/dist/         (Python-Bundle)
Inno Setup (iscc)      →  Windows/output/       (Setup.exe)
```

---

## Voraussetzungen

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.12+ | https://python.org/downloads/ |
| Node.js | 18+ | https://nodejs.org/ |
| PyInstaller | 6+ | `pip install pyinstaller` |
| Inno Setup | 6.x | https://jrsoftware.org/isdl.php |
| pystray *(optional)* | aktuell | `pip install pystray pillow` |

> **pystray + Pillow**: Nur für das System-Tray-Icon benötigt.  
> Ohne diese Pakete läuft die App mit einem Konsolenfenster.

---

## Schnellstart

```powershell
# Im Projektverzeichnis:
cd Windows
.\build.ps1
```

Der Installer liegt danach unter:  
`Windows\output\RaceControl-Pro-Setup-0.6.0.exe`

---

## Einzelne Schritte überspringen

```powershell
# Nur Installer neu erzeugen (Bundle bereits vorhanden):
.\build.ps1 -SkipFrontend -SkipPyInstaller

# Ohne Inno Setup (nur Bundle testen):
.\build.ps1 -SkipInnoSetup

# Andere Version:
.\build.ps1 -Version "0.7.0"
```

---

## Was wird gebaut?

### PyInstaller-Bundle (`dist/racecontrol/`)

```
dist/racecontrol/
├── racecontrol.exe          ← Startet Server + Browser + Tray-Icon
└── _internal/               ← Python-Laufzeit + alle Abhängigkeiten
    ├── backend/             ← FastAPI-Quellcode
    ├── frontend/dist/       ← Gebautes Vue-Frontend
    ├── schema.sql           ← Datenbankschema
    └── ...                  ← Python, uvicorn, fastapi, etc.
```

### Installiertes Programm (`%LocalAppData%\Programs\RaceControl Pro\`)

```
RaceControl Pro\
├── racecontrol.exe
├── _internal\               ← Unveränderlich (Programmdateien)
├── data\                    ← racecontrol.db  (Datenbank)
└── assets\                  ← Dokumente, Reglements-PDFs etc.
```

---

## App-Icon

Lege eine Datei `Windows\icon.ico` ab (256×256 px, ICO-Format).  
Ohne Icon verwendet die App einen generierten grünen Kreis.

---

## Konsolenfenster ausblenden

In `racecontrol.spec` die Zeile ändern:

```python
console=True   →   console=False
```

Danach benötigt das System-Tray-Icon **pystray + Pillow** (sonst bleibt  
die App im Hintergrund ohne jede Steuerungsmöglichkeit).

---

## Fehlerbehebung

### `ModuleNotFoundError` beim Start des Bundles

Fehlende Module in `racecontrol.spec` unter `hiddenimports` ergänzen  
und PyInstaller erneut ausführen.

### Port 1980 bereits belegt

Eine andere Instanz läuft noch. Im Task-Manager `racecontrol.exe` beenden  
oder `netstat -an | findstr 1980` prüfen.

### Inno Setup nicht gefunden

Inno Setup 6 installieren und sicherstellen, dass `iscc.exe` im PATH liegt  
oder unter `C:\Program Files (x86)\Inno Setup 6\` vorhanden ist.

### Frontend fehlt im Bundle

```powershell
.\build.ps1 -SkipPyInstaller -SkipInnoSetup   # nur Frontend neu bauen
.\build.ps1 -SkipFrontend                      # danach Bundle + Installer
```
