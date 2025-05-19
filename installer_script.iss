; Inno Setup Script for KarabelaTrade
#define MyAppName "KarabelaTrade"
#define MyAppVersion "1.0"
#define MyAppPublisher "KarabelaTrade"
#define MyAppExeName "KarabelaTrade.exe"

[Setup]
AppId={{F4E17513-0E11-4176-8F26-A6EC75C312B5}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installer
OutputBaseFilename=KarabelaTrade_Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
UsedUserAreasWarning=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "MQL5\*"; DestDir: "{app}\MQL5"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "*.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "*.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
