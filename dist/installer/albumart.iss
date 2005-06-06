[Setup]
AppName=Album Cover Art Downloader
AppVerName=Album Cover Art Downloader 1.6.0
AppPublisher=Sami Kyöstilä
AppPublisherURL=http://kempele.fi/~skyostil/projects/albumart
AppSupportURL=http://kempele.fi/~skyostil/projects/albumart
AppUpdatesURL=http://kempele.fi/~skyostil/projects/albumart
DefaultDirName={pf}\Album Cover Art Downloader
DefaultGroupName=Album Cover Art Downloader
InfoBeforeFile=distalbumart-qt-w32\Copying.txt
Compression=lzma
SolidCompression=yes
OutputDir=.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "distalbumart-qt-w32\albumart-qt.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "distalbumart-qt-w32\support\*"; DestDir: "{app}\support"; Flags: ignoreversion recursesubdirs
Source: "distalbumart-qt-w32\Changelog.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "distalbumart-qt-w32\Copying.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "distalbumart-qt-w32\Readme.txt"; DestDir: "{app}"; Flags: ignoreversion isreadme
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[INI]
Filename: "{app}\albumart-qt.url"; Section: "InternetShortcut"; Key: "URL"; String: "http://kempele.fi/~skyostil/projects/albumart"

[Icons]
Name: "{group}\Album Cover Art Downloader"; Filename: "{app}\albumart-qt.exe"
Name: "{group}\{cm:ProgramOnTheWeb,Album Cover Art Downloader}"; Filename: "{app}\albumart-qt.url"
Name: "{userdesktop}\Album Cover Art Downloader"; Filename: "{app}\albumart-qt.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\albumart-qt.exe"; Description: "{cm:LaunchProgram,Album Cover Art Downloader}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\albumart-qt.url"
Type: files; Name: "{app}\log.txt"

