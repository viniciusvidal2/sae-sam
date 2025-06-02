; installer.iss
[Setup]
AppName=SAE SAM
AppVersion=1.2.2
DefaultDirName={pf64}\SAE SAM
DefaultGroupName=SAE SAM
OutputDir=.
OutputBaseFilename=sae_sam_installer
Compression=lzma2
SolidCompression=yes

[Files]
Source: "dist\sae_sam\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs
Source: "resources\saesam_icon.ico"; DestDir: "{app}\resources"

[Icons]
Name: "{group}\SAE SAM"; Filename: "{app}\sae_sam.exe"; IconFilename: "{app}\resources\saesam_icon.ico"
Name: "{autodesktop}\SAE SAM"; Filename: "{app}\sae_sam.exe"; Tasks: desktopicon; IconFilename: "{app}\resources\saesam_icon.ico"
Name: "{group}\Uninstall SAE SAM"; Filename: "{uninstallexe}"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\sae_sam.exe"; Description: "Launch SAE SAM"; Flags: nowait postinstall skipifsilent
