[Setup]
AppName=Cline-X App
AppVersion=1.1
DefaultDirName={autopf64}\\Cline-X App
DefaultGroupName=Cline-X App
OutputBaseFilename=cline-x-setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\\cline-x-app.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\\Cline-X App"; Filename: "{app}\\cline-x-app.exe"
Name: "{autodesktop}\\Cline-X App"; Filename: "{app}\\cline-x-app.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:";
