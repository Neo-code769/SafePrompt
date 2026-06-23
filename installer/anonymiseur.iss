; Inno Setup script - Anonymiseur Action Telecom
; Compile avec : "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\anonymiseur.iss
; Genere : installer\Output\Anonymiseur-Setup.exe

#define MyAppName      "Anonymiseur Action Telecom"
#define MyAppVersion   "1.0.0"
#define MyAppPublisher "Action Telecom"
#define MyAppExeName   "Anonymiseur.exe"
#define MyAppURL       "https://www.actiontelecom.fr"

[Setup]
AppId={{C8F4A1E6-4D2B-4F8E-9A2C-ANONYMISEUR0001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\ActionTelecom\Anonymiseur
DefaultGroupName=Action Telecom
DisableProgramGroupPage=no
OutputBaseFilename=Anonymiseur-Setup-{#MyAppVersion}
Compression=lzma2/ultra
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupLogging=yes

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Creer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"; Flags: unchecked
Name: "startupicon"; Description: "Lancer au demarrage de Windows"; GroupDescription: "Raccourcis :"; Flags: unchecked

[Files]
Source: "..\dist\Anonymiseur.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "..\CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\VERSION"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstaller {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; On ne supprime PAS %APPDATA%/ActionTelecom (conserve config utilisateur).
; Pour reset complet, l'utilisateur le fait manuellement.
Type: filesandordirs; Name: "{app}"
