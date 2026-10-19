# v2.0.20 源码运行与构建

需要 Windows 10/11 x64、带 Tcl/Tk 的 Python 3.12 x64。正式运行时为 Python 3.12.14，依赖固定于 requirements.txt。安装包另需 Inno Setup 6.5+。

## 准备与运行

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src\main.py /m="测试提醒" /w
```

## 便携版和安装版

运行 `build.bat` 可生成两种 EXE 并编译安装包。单文件便携版位于 `dist/定时关机工具.exe`；目录式安装版位于 `installed/定时关机工具/`；安装包位于 `output/Shutdown-Tool-v2.0.20-Setup.exe`。

也可手动构建：

```powershell
Remove-Item Env:SHUTDOWN_BUILD_LAYOUT -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --workpath build_portable --distpath dist build.spec
$env:SHUTDOWN_BUILD_LAYOUT='onedir'
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --workpath build_installed --distpath installed build.spec
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" '/DSrcExeDir=..\installed\定时关机工具' installer\setup.iss
Remove-Item Env:SHUTDOWN_BUILD_LAYOUT -ErrorAction SilentlyContinue
```

目录式安装版必须保留 `_internal` 及所有随附文件。该方式避免单文件每次启动解包，下载包大小、安装占用和启动速度是不同指标。默认图标及紫樱资源已预生成，构建无需重绘。

公开版不包含 assets/audio，音频仅接受用户选择的路径；保留原安装 GUID、APP_ID 和启动项兼容身份。

## 隔离验证

```powershell
.\.venv\Scripts\python.exe tools\v220_main_regression.py 1.25
.\.venv\Scripts\python.exe tools\v211_runtime_regression.py
.\.venv\Scripts\python.exe tools\v211_ui_regression.py 1.5
.\.venv\Scripts\python.exe tools\v211_ui_regression.py 2.0
.\.venv\Scripts\python.exe tools\v210_runtime_regression.py
.\.venv\Scripts\python.exe tools\v210_ui_regression.py
.\.venv\Scripts\python.exe tools\calendar_rules_regression.py
.\.venv\Scripts\python.exe tools\automation_status_regression.py
.\.venv\Scripts\python.exe tools\workspace_regression.py 1.25
.\.venv\Scripts\python.exe tools\package_smoke.py dist\定时关机工具.exe
```

这些专项脚本使用临时 APPDATA，禁止真实电源操作，结果写入被忽略的核验目录。旧版脚本仅供历史参考，不应盲目运行涉及启动项、安装或卸载的旧测试。性能启动样本不是受控的系统冷缓存基准；验证边界见 [VALIDATION.md](VALIDATION.md)。

发布前核对版本与 EXE 内嵌源码一致，排除配置、日志、凭据、虚拟环境、缓存、音频和旧交接文件。二进制、源码归档、手册与 SHA256 放入 Releases。
