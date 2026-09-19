; AgentBetta Windows installer (Inno Setup 6)
; Per-user install by default; does not delete user data on uninstall.

#define MyAppName "AgentBetta"
#define MyAppVersion "0.2.0-alpha.1"
#define MyAppPublisher "AgentBetta Project"
#define MyAppExeName "AgentBetta.exe"

[Setup]
AppId={{7E9F3A61-2C4B-4E6D-9A11-3B2C1D4E5F60}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\AgentBetta
DefaultGroupName=AgentBetta
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\release\windows\0.2.0-alpha.1
OutputBaseFilename=AgentBetta-{#MyAppVersion}-Windows-x64-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\src\agentbetta\desktop\resources\agentbetta.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
VersionInfoVersion=0.2.0.1
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=AgentBetta installer
DisableWelcomePage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "..\dist\AgentBetta\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\AgentBetta"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall AgentBetta"; Filename: "{uninstallexe}"
Name: "{userdesktop}\AgentBetta"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch AgentBetta"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Intentionally empty for user data: run history and credentials are preserved.
; Application files are removed by Inno Setup automatically.
