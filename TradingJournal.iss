[Setup]
AppName=Trading Journal
AppVersion=1.1.0
AppPublisher=Mohammad Mansour Ataey
AppPublisherURL=https://github.com/mansourataey
DefaultDirName={autopf}\Trading Journal
DefaultGroupName=Trading Journal
OutputDir=installer
OutputBaseFilename=TradingJournal_Setup_v1.1
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
SetupIconFile=app\static\app_icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create Desktop Shortcut"; GroupDescription: "Additional Tasks:"

[Files]
Source: "dist\TradingJournal\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Trading Journal"; Filename: "{app}\TradingJournal.exe"; IconFilename: "{app}\TradingJournal.exe"
Name: "{autodesktop}\Trading Journal"; Filename: "{app}\TradingJournal.exe"; IconFilename: "{app}\TradingJournal.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\TradingJournal.exe"; Description: "Launch Trading Journal"; Flags: nowait postinstall skipifsilent