; BullseyeNSE_Installer.iss
; Inno Setup script for Bullseye Fintech — NSE EOD Dashboard
;
; Prerequisites:
;   1. Build with PyInstaller first (see INSTRUCTIONS.md)
;   2. The dist\BullseyeNSE\ folder must exist before compiling this script
;   3. Inno Setup 6+ must be installed

#define AppName      "Bullseye Fintech NSE EOD"
#define AppVersion   "3.0"
#define AppPublisher "Bullseye Fintech"
#define AppExeName   "BullseyeNSE.exe"
#define AppURL       "https://bullseyefintech.com"

; ── Paths — adjust if your project layout differs ──────────────────────────
; SOURCE_DIR should be the dist\BullseyeNSE folder produced by PyInstaller.
; Change the path below if your repo root is different.
#define SourceDir    "dist\BullseyeNSE"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\BullseyeFintech\NSE_EOD
DefaultGroupName=Bullseye Fintech
AllowNoIcons=yes
; Uncomment the next line to require admin rights:
; PrivilegesRequired=admin
PrivilegesRequired=lowest
OutputDir=installer_output
OutputBaseFilename=BullseyeNSE_Setup_v{#AppVersion}
; Set your .ico path here or remove the Compression line to skip icon
; SetupIconFile=icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
; Data directory inside AppData so no admin rights are needed for writes
UsedUserAreasWarning=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startmenuicon"; Description: "Create Start Menu shortcut"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; Bundle entire PyInstaller output directory
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}";    DestPath: "{app}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
Name: "{userstartmenu}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: startmenuicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove the data folder the app creates in AppData on uninstall (optional — comment out to keep user data)
; Type: filesandordirs; Name: "{localappdata}\BullseyeFintech\NSE_EOD"

[Code]
// Optional: check that no old instance is running before install
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
