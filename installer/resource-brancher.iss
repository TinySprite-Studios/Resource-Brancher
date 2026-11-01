#ifndef AppVersion
  #error AppVersion is required
#endif
#ifndef BuildAppId
  #define BuildAppId "{{A7C901E2-472A-44CD-9C11-8CB3DA2E8329}"
#endif
[Setup]
AppId={#BuildAppId}
AppName=Resource Brancher
AppVersion={#AppVersion}
AppPublisher=TinySprite Studios
DefaultDirName={localappdata}\Programs\Resource Brancher
DefaultGroupName=Resource Brancher
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=Resource-Brancher-Setup-{#AppVersion}
SetupIconFile=..\build\resource-brancher.ico
UninstallDisplayIcon={app}\Resource Brancher.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked
[Files]
Source: "..\dist\Resource Brancher\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "installed.marker"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{autoprograms}\Resource Brancher"; Filename: "{app}\Resource Brancher.exe"
Name: "{autodesktop}\Resource Brancher"; Filename: "{app}\Resource Brancher.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\Resource Brancher.exe"; Description: "Launch Resource Brancher"; Flags: nowait postinstall skipifsilent
