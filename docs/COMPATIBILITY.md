# Windows兼容性核查（v1.6.8）

| 系统 | 当前交付状态 | 验证范围 |
| --- | --- | --- |
| Windows10 x64 | 正式版、本机实测 | 新旧功能回归、后台进程树强制结束、正式exe |
| Windows11 x64 | 保持兼容设计，未现场实测 | 22000/22631/26100版本识别，DPI首选及旧接口回退，DWM缺失时安全降级 |
| Windows7 SP1 | 当前exe不能运行 | 源码语法可由Python3.8解析，但不能证明二进制及运行时兼容 |

## 为什么没有给正式版直接加Win7支持

目前正式版使用Python3.12.14，官方明确Win7需Python3.8。安装程序MinVersion=10.0仍保留，避免把不能启动的程序安装到Win7。Pillow12.3等当前依赖不能直接搬到Python3.8，音频及图像二进制也需分别确认系统导入接口。

未修改Win10正式版的Python、Pillow、psutil、音频或打包依赖，没有用未经验证的旧DLL替换现有组件。

## Win7独立兼容构建所需工作

1. 在独立Win7 SP1 x64虚拟机/实机配置Python3.8及Tk，禁止复用正式版虚拟环境
2. 为Pillow、psutil、miniaudio/cffi及PyInstaller选定Python3.8和Win7兼容版本，确认wheel/DLL不导入Win8+专用接口，固定完整依赖指纹
3. 核对Win7字体、DPI、无Aero时的窗口恢复、WMI/DDC亮度、CoreAudio音量、托盘与全局快捷键；缺失能力需明确降级
4. 在Win7环境单独构建exe，安装器仅该兼容构建允许MinVersion=6.1sp1；使用独立成品名称，不覆盖Win10/11成品
5. 在Win7实测定时、队列、模板、重复预约、网络条件、音频、强制关闭及权限失败；再标成可用，不把Win10上的模拟测试写成Win7实测

本次未创建Win7虚拟机，也未下载/降级正式版依赖；因此没有交付或宣称Win7兼容exe。

## 官方依据

- [Python3.12 Windows系统支持](https://docs.python.org/3.12/using/windows.html)：Win7需Python3.8
- [Pillow Python版本支持](https://pillow.readthedocs.io/en/stable/installation/python-support.html)
- [Inno Setup最低系统限制](https://jrsoftware.org/ishelp/topic_setup_minversion.htm)：安装器门槛不等于应用兼容性
- [psutil强制结束接口](https://psutil.readthedocs.io/stable/)：Windows的kill使用TerminateProcess
