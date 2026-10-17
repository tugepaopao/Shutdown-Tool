# v2.0.7 源码运行与构建

需要 Windows 10/11 x64、带 Tcl/Tk 的 Python 3.12 x64。正式运行时为 Python 3.12.14，依赖固定于 requirements.txt。安装包另需 Inno Setup 6.5+。

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src\main.py /m="测试提醒" /w
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --workpath build_work --distpath dist build.spec
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" installer\setup.iss
```

单文件程序为 dist/定时关机工具.exe，安装包为 output/Shutdown-Tool-v2.0.7-Setup.exe。默认图标及紫樱素材已预生成，构建无需重绘。build.bat 可完成以上两个构建步骤。

公开版不包含 assets/audio，sound_library 仅接受用户选择的路径；旧 builtin 标识解析为空，不读取缺失资源。保留公开版安装 GUID、APP_ID 和启动项兼容身份。

## 隔离验证

```powershell
.\.venv\Scripts\python.exe tools\v207_ui_regression.py
.\.venv\Scripts\python.exe tools\calendar_rules_regression.py
.\.venv\Scripts\python.exe tools\automation_status_regression.py
.\.venv\Scripts\python.exe tools\workspace_regression.py 1.5
.\.venv\Scripts\python.exe tools\package_smoke.py dist\定时关机工具.exe
```

上述测试使用临时 APPDATA，禁止真实电源操作。界面结果写入被忽略的核验目录。旧版本回归脚本保留作历史参考，其中多语言或旧布局断言不适用于仅简体中文的 v2.0.7。不要在日常账号盲目运行涉及启动项的旧 self_test。

发布前核对源码、版本和打包内容一致，排除配置、日志、凭据、缓存、音频和旧交接文件。exe、源码归档、使用手册和 SHA256 放入 Releases。常规维护须经用户对该次发布明确授权后再上传。
