#define AppVersion "0.1.0"
#ifndef InstallerAppId
#define InstallerAppId "WinLink-D58F7460-EDC0-4563-98B7-2FB51900B813"
#endif
#ifndef UserDataDir
#define UserDataDir "{userappdata}\WinLink"
#endif
#ifndef OutputBase
#define OutputBase "WinLink-Setup-0.1.0"
#endif
[Setup]
LicenseFile=..\LICENSE
AppId={#InstallerAppId}
AppName=WinLink
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\WinLink
DefaultGroupName=WinLink
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.18362
OutputDir=..\dist
OutputBaseFilename={#OutputBase}
SetupIconFile=..\resources\winlink.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\WinLink.exe
[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; Flags: unchecked
[Files]
Source: "..\dist\WinLink\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\WinLink"; Filename: "{app}\WinLink.exe"
Name: "{userdesktop}\WinLink"; Filename: "{app}\WinLink.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\WinLink.exe"; Description: "Abrir WinLink"; Flags: nowait postinstall skipifsilent
[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var DataDir: String; DeleteHistory: Boolean; I: Integer;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    DataDir := ExpandConstant('{#UserDataDir}\');
    DeleteFile(DataDir + 'config.json');
    DeleteFile(DataDir + 'cache.json');
    DeleteFile(DataDir + 'cache.tmp');
    DeleteFile(DataDir + 'winlink.log');
    DeleteFile(DataDir + 'winlink.log.1');
    DeleteFile(DataDir + 'winlink.log.2');
    DeleteFile(DataDir + 'winlink.log.3');
    DeleteHistory := False;
    for I := 1 to ParamCount do
      if CompareText(ParamStr(I), '/DELETEHISTORY') = 0 then DeleteHistory := True;
    if not UninstallSilent then
      DeleteHistory := MsgBox('Deseja apagar também o histórico de operações? As junções e seus arquivos serão preservados.', mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES;
    if DeleteHistory then DeleteFile(DataDir + 'history.json');
    RemoveDir(DataDir);
  end;
end;
