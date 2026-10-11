; ============================================================
;  Inno Setup 安装包脚本 —— 定时关机工具
;  作者：@wenhao
;  编译命令：
;     "C:\Users\<用户>\AppData\Local\Programs\Inno Setup 6\ISCC.exe" installer\setup.iss
; ============================================================

#define MyAppName "定时关机工具"
#define MyAppVersion "1.7.4"
#define MyAppPublisher "@wenhao"
#define MyAppExeName "定时关机工具.exe"
#define MyAppId "{{8F3C1A72-5B4E-4C9D-9E21-7A6B0C5D3F10}"

; 便携版 exe 所在目录；一般不用改，也可在命令行覆盖：
;   ISCC.exe /DSrcExeDir=..\dist_v4 installer\setup.iss
#ifndef SrcExeDir
  #define SrcExeDir "..\dist"
#endif

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppCopyright=Copyright (C) 2026 {#MyAppPublisher}
DefaultDirName={autopf}\HaozaiziShutdownTool
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
AllowNoIcons=yes
; 默认按当前用户安装（不需要管理员权限、不弹 UAC）；
; 用户也可在向导里勾选“为所有用户安装”改写安装目录到 Program Files。
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\output
OutputBaseFilename=定时关机工具_v1.7.4_安装包
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} v{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no
MinVersion=10.0
VersionInfoVersion=1.7.4.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} 安装程序
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion=1.7.4.0

[Languages]
Name: "chinese"; MessagesFile: "ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
chinese.create_desktop_shortcut=创建桌面快捷方式
english.create_desktop_shortcut=Create a desktop shortcut
chinese.group_startup=开机启动：
english.group_startup=Startup:
chinese.startup_task=开机时自动启动（最小化到托盘，可随时在程序设置里关闭）
english.startup_task=Start automatically at Windows startup (minimized to tray)
chinese.launch_now=立即运行 {#MyAppName}
english.launch_now=Launch {#MyAppName} now
chinese.readme=查看使用说明
english.readme=View the readme

[Tasks]
Name: "desktopicon"; Description: "{cm:create_desktop_shortcut}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startupicon"; Description: "{cm:startup_task}"; GroupDescription: "{cm:group_startup}"

[Files]
Source: "{#SrcExeDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\使用说明.md"; DestDir: "{app}"; Flags: ignoreversion

[InstallDelete]
Type: files; Name: "{app}\豪崽子の自动关机工具.exe"
Type: files; Name: "{autodesktop}\豪崽子の自动关机工具.lnk"
Type: files; Name: "{autoprograms}\豪崽子の自动关机工具\豪崽子の自动关机工具.lnk"

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "{#MyAppName}"
Name: "{autoprograms}\{#MyAppName} 使用说明"; Filename: "{sys}\notepad.exe"; Parameters: """{app}\使用说明.md"""
Name: "{autoprograms}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
    ValueType: string; ValueName: "豪崽子の自动关机工具"; \
    ValueData: """{app}\{#MyAppExeName}"" /min"; \
    Flags: uninsdeletevalue; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:launch_now}"; \
    Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/f /im ""{#MyAppExeName}"""; \
    Flags: runhidden; RunOnceId: "KillRunningApp"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
