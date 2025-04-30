; installer.iss
[Setup]
AppName=SAE SAM
AppVersion=1.0.0
DefaultDirName={pf64}\SAE SAM
DefaultGroupName=SAE SAM
OutputDir=.
OutputBaseFilename=sae_sam_installer
Compression=lzma2
SolidCompression=yes

[Files]
Source: "dist\sae_sam\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SAE SAM"; Filename: "{app}\sae_sam.exe"
Name: "{group}\Uninstall SAE SAM"; Filename: "{uninstallexe}"
Name: "{userdesktop}\SAE SAM"; Filename: "{app}\sae_sam.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\sae_sam.exe"; Description: "Launch SAE SAM"; Flags: nowait postinstall skipifsilent
