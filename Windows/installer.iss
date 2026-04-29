; Inno Setup 6 – RaceControl Pro
; https://jrsoftware.org/isinfo.php
;
; Erstellt einen Ein-Klick-Installer für Windows 10/11.
; Erfordert KEINE Admin-Rechte (Installation in %LocalAppData%\Programs).

#define AppName      "RaceControl Pro"
#define AppVersion   "0.6.1"
#define AppPublisher "MSC Braach 1980 e.V im ADAC"
#define AppExeName   "racecontrol.exe"
#define SourceDir    "dist\racecontrol"

[Setup]
; Eindeutige App-ID (GUID nicht ändern nach erstem Release)
AppId={{F7E2A1B4-3C9D-4E8F-A05B-6D2C1E4F7890}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=http://localhost:1980
AppSupportURL=http://localhost:1980
AppUpdatesURL=http://localhost:1980

; Installation ohne Admin-Rechte in %LocalAppData%\Programs
PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
DisableProgramGroupPage=no

; Installer-Ausgabe
OutputDir=output
OutputBaseFilename=RaceControl-Pro-Setup-{#AppVersion}
SetupIconFile=icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardResizable=yes

; Mindest-Windows-Version: Windows 10
MinVersion=10.0

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon";   Description: "Desktop-Verknüpfung erstellen"; GroupDescription: "Zusätzliche Symbole:"
Name: "autostart";     Description: "Beim Windows-Start automatisch starten";  GroupDescription: "Autostart:"; Flags: unchecked

[Files]
; Alle PyInstaller-Ausgabedateien
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
; Schreibbare Unterordner neben der .exe anlegen
Name: "{app}\data"
Name: "{app}\assets"

[Icons]
; Startmenü
Name: "{group}\{#AppName}";                     Filename: "{app}\{#AppExeName}"; Comment: "Kart-Slalom Veranstaltungssoftware"
Name: "{group}\{#AppName} – Browser öffnen";   Filename: "http://localhost:1980"; IconFilename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
; Desktop (optional)
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Registry]
; Autostart (optional, nur wenn Aufgabe gewählt)
Root: HKCU; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#AppName}"; ValueData: """{app}\{#AppExeName}"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
; Nach Installation starten (optional)
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Prozess vor Deinstallation beenden
Filename: "taskkill.exe"; Parameters: "/F /IM {#AppExeName}"; Flags: runhidden skipifdoesntexist

[Code]
// Prüfen ob der Port 1980 bereits belegt ist
function IsPortInUse: Boolean;
var
  TmpFile: String;
  ResultCode: Integer;
begin
  TmpFile := ExpandConstant('{tmp}\port_check.txt');
  Exec('cmd.exe', '/C netstat -an | find "1980" > "' + TmpFile + '"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := FileExists(TmpFile) and (FileSize(TmpFile) > 0);
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpReady then
  begin
    if IsPortInUse then
      MsgBox('Hinweis: Port 1980 ist bereits belegt.' + #13#10 +
             'Bitte beenden Sie eine laufende Instanz von RaceControl Pro' + #13#10 +
             'bevor Sie das Programm erneut starten.', mbInformation, MB_OK);
  end;
end;
