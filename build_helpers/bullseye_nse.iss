; bullseye_nse.iss
; Inno Setup 6 installer script for Bullseye Fintech — NSE EOD Dashboard
;
; Prerequisites
; ─────────────
;   • Inno Setup 6.x  (https://jrsoftware.org/isinfo.php)
;   • The PyInstaller one-folder build must exist at:
;       dist\BullseyeNSE\
;   before running this script.
;
; To compile:
;   iscc bullseye_nse.iss
; or open in Inno Setup IDE and press F9.

#define MyAppName      "Bullseye Fintech NSE EOD"
#define MyAppVersion   "2.0.4"
#define MyAppPublisher "Bullseye Fintech"
#define MyAppURL       "https://bullseyefintech.com"
#define MyAppExeName   "BullseyeNSE.exe"
#define BuildDir       "dist\BullseyeNSE"

[Setup]
; ── Installer identity ───────────────────────────────────────────────────────
AppId={{A3F2B1C4-7E89-4D56-B2A0-9F3C8E1D4B67}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; ── Installation target ───────────────────────────────────────────────────────
; {autopf} resolves to "C:\Program Files" for 64-bit admin installs.
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes

; ── Architecture ─────────────────────────────────────────────────────────────
; Force 64-bit install mode so {autopf} → C:\Program Files (not x86).
ArchitecturesInstallIn64BitMode=x64

; ── Output ────────────────────────────────────────────────────────────────────
OutputDir=installer_output
OutputBaseFilename=BullseyeNSE_Setup_{#MyAppVersion}
;SetupIconFile=icon.ico          ; remove this line if you have no icon
Compression=lzma2/ultra64
SolidCompression=yes

; ── Privileges ────────────────────────────────────────────────────────────────
; FIX: "admin" forces a machine-wide install into Program Files and always
; prompts for UAC elevation.  The "lowest" + dialog combo that was here
; previously allowed per-user installs which put the app outside Program
; Files — Streamlit's multiprocessing child process can then be blocked by
; Windows because it runs from an untrusted user-writable path.
; The PrivilegesRequiredOverridesAllowed line has been removed so there is
; no "Install for me only" option in the wizard.
PrivilegesRequired=admin

; ── Minimum Windows version: Windows 10 ──────────────────────────────────────
MinVersion=10.0

; ── Wizard appearance ────────────────────────────────────────────────────────
;WizardStyle=modern
;WizardSmallImageFile=wizard_small.bmp   ; 55×58 px bitmap (optional — remove if absent)

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Bundle the entire PyInstaller one-folder build
Source: "{#BuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start-menu shortcut
Name: "{group}\{#MyAppName}";           Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

; Desktop shortcut (only if user ticked the task above)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
; Offer to launch the app immediately after install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove the data folder created by the app (opt-in — comment out to preserve user data)
; Type: filesandordirs; Name: "{userappdata}\BullseyeFintech"

[Code]
// Optionally run a pre-install check here (e.g. Windows version, disk space).
// Left empty for now.
