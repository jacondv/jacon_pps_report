; Inno Setup script for Jacon PPS Report.
;
; Builds a standard Windows installer (Welcome -> install location ->
; shortcuts -> install -> finish) around the PyInstaller output in dist/.
; The uninstaller is registered in "Apps & features" / "Programs and
; Features" under the publisher Jacon Equipment, and in the Start menu.
;
; Build the app FIRST — this only packages dist/, and takes the version
; from the exe's version resource (pps.__version__, written by build.spec):
;   pyinstaller build.spec
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
;
; Output: installer_output\Jacon PPS Report Setup <version>.exe
; Wizard images: installer\*.bmp (tools\make_installer_images.py).

#define MyAppName "Jacon PPS Report"
#define MyAppExeName "Jacon PPS Report.exe"
#define MyAppSourceDir "dist\Jacon PPS Report"
#define MyAppPublisher "Jacon Equipment"
#define MyAppURL "https://www.jaconequipment.com"
#define MyAppSupportEmail "productsupport@jaconequipment.com"

#define MyAppExePath AddBackslash(MyAppSourceDir) + MyAppExeName
#if !FileExists(MyAppExePath)
  #error "dist\Jacon PPS Report\Jacon PPS Report.exe not found: run `pyinstaller build.spec` first."
#endif
#define MyAppVersion GetStringFileInfo(MyAppExePath, "ProductVersion")

[Setup]
; Fixed AppId — keep this the same across versions so an upgrade install
; replaces the previous one instead of installing side-by-side.
AppId={{81E5EDF6-AAF3-4B4A-A0F9-346A757E5219}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppContact={#MyAppSupportEmail}
AppCopyright=Copyright (C) {#MyAppPublisher}

; Properties -> Details of the Setup .exe itself.
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup
VersionInfoProductName={#MyAppName}
VersionInfoVersion={#MyAppVersion}
VersionInfoProductVersion={#MyAppVersion}

DefaultDirName={autopf}\{#MyAppPublisher}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Offer to close a running copy (Restart Manager) before upgrading/uninstalling.
CloseApplications=yes
RestartApplications=no

OutputDir=installer_output
OutputBaseFilename={#MyAppName} Setup {#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes

WizardStyle=modern
SetupIconFile=src\pps\ui\icons\app.ico
WizardImageFile=installer\wizard_large.bmp,installer\wizard_large@2x.bmp
WizardSmallImageFile=installer\wizard_small.bmp,installer\wizard_small@2x.bmp

; Installing to Program Files, registering the uninstaller for all users and
; the Defender exclusion task below all require admin rights.
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"
; Checked by default: the app ships to customers' own PCs, where Windows
; Defender otherwise scans every bundled DLL on first launch (slow start).
; On company devices managed by Intune with Tamper Protection, a locally
; added exclusion is overridden by policy — there IT must add it centrally.
Name: "defenderexclusion"; Description: "Add a Windows Defender exclusion for the install folder (recommended: much faster first start)"; GroupDescription: "Startup performance:"

[InstallDelete]
; Upgrading over an older version: remove the old bundle first, otherwise
; libraries a newer build no longer ships (e.g. scipy, unused VTK modules)
; stay behind in the install folder. _internal only holds installer-owned files.
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "{#MyAppSourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""Add-MpPreference -ExclusionPath '{app}'"""; StatusMsg: "Adding Windows Defender exclusion…"; Tasks: defenderexclusion; Flags: runhidden
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Remove the Defender exclusion added by the "defenderexclusion" task (by this
; or an earlier version). Silently continues if it was never added.
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""Remove-MpPreference -ExclusionPath '{app}' -ErrorAction SilentlyContinue"""; Flags: runhidden; RunOnceId: "RemoveDefenderExclusion"
