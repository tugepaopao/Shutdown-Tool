# Windows源码运行与构建

## 环境

Windows10/11 x64、带Tcl/Tk的Python3.12 x64。正式发行运行时为Python3.12.14，固定第三方版本见requirements.txt。安装包编译使用Inno Setup6.5或更高版本；Inno Setup不是运行程序所需依赖。

## 安装依赖与启动

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src\main.py /m="测试提醒" /w
```

`/w`仅预选操作，不自动计时。普通启动可用run_dev.bat。

## 构建便携版

图标资源已预生成。无需运行图标生成脚本即可构建：

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --workpath build_work --distpath dist build.spec
```

生成dist/定时关机工具.exe。PyInstaller包含运行时；用户不需要安装Python。请使用干净构建目录避免旧缓存；所有assets/ui及图标必须在源码目录中。公开配置不含assets/audio。

## 构建安装包

```powershell
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" installer\setup.iss
```

如ISCC安装在其他目录，请替换路径。默认从dist取exe；改变目录时用`/DSrcExeDir=..\你的目录`。生成output/定时关机工具_v1.6.9_安装包.exe。安装AppId及数据目录保留历史兼容标识。

也可双击build.bat完成打包；该脚本需要项目内.venv和已安装Inno Setup。缺少Inno Setup时只能产出便携版。

## 可选：重绘图标

```powershell
.\.venv\Scripts\python.exe tools\make_icon.py
.\.venv\Scripts\python.exe tools\make_ui_icons.py
```

会更新assets中的生成资源。发布前重新截图并核对界面；一般无需重绘。

## 回归与发布

```powershell
.\.venv\Scripts\python.exe tools\platform_regression.py
.\.venv\Scripts\python.exe tools\force_regression.py
.\.venv\Scripts\python.exe tools\public_regression.py
.\.venv\Scripts\python.exe tools\widgets_regression.py
```

平台检查为模拟接口测试，不是Win11/Win7实机测试。强制结束测试会编译并终止自行创建的临时测试程序，需要Windows .NET Framework C#编译器；不会选择用户程序。GUI测试使用隔离APPDATA，不创建真实电源任务。

发布时使用Releases保存exe/文档归档及SHA256，不把exe提交到源码Git历史。检查源码、版本号、构建输入与产物一致；不上传个人配置、凭据、日志、虚拟环境或缓存。
