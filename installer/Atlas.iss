; Atlas Installer Script (Windows XP Compatible)

#define MyAppName "Atlas"
#define MyAppVersion "1.2"
#define MyAppPublisher "Michael Dorman"
#define MyAppURL "https://github.com/JunimoByte/atlas-retro"

; Select the PyInstaller output and installer architecture from the file that
; actually exists in dist. Refuse an ambiguous directory rather than package
; the wrong architecture.
#ifexist "..\dist\Atlas-x86_64-Portable.exe"
  #ifexist "..\dist\Atlas-x86-Portable.exe"
    #error "Both x86 and x86_64 builds exist in dist. Keep only the release to package."
  #endif
  #define MyAppArch "x86_64"
  #define MyAppSourceExe "Atlas-x86_64-Portable.exe"
  #define MyAppExeName "Atlas-x86_64.exe"
  #define MyAppIs64Bit 1
#else
  #ifexist "..\dist\Atlas-x86-Portable.exe"
    #define MyAppArch "x86"
    #define MyAppSourceExe "Atlas-x86-Portable.exe"
    #define MyAppExeName "Atlas-x86.exe"
    #define MyAppIs64Bit 0
  #else
    #error "Build Atlas with pyinstaller main.spec before compiling the installer."
  #endif
#endif

[Setup]
AppId={{27AD91DA-5BAA-4318-AD23-53E47A279351}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Target Windows XP SP3+
MinVersion=5.1.2600

DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}

; Installer icon
SetupIconFile=..\assets\icons\Icon.ico

#if MyAppIs64Bit
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
#endif

DisableProgramGroupPage=yes
PrivilegesRequired=lowest

OutputBaseFilename=Atlas-{#MyAppArch}-Setup
OutputDir=..\dist
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\{#MyAppSourceExe}"; DestDir: "{app}"; DestName: "{#MyAppExeName}"; Flags: ignoreversion

[Icons]
Name: "{userprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
