# 第三方组件说明

本项目的MIT许可证仅适用于作者提供的第一方代码。依赖通过requirements.txt安装，许可证以各项目随版本提供的文本为准；打包时请保留其要求的声明，不把第三方组件改称MIT。

| 组件 | 用途 | 官方项目 |
| --- | --- | --- |
| Python / Tcl / Tk | 运行时、Tkinter界面 | https://www.python.org / https://www.tcl.tk |
| Pillow | 图像与图标 | https://github.com/python-pillow/Pillow |
| pystray | 系统托盘 | https://github.com/moses-palmer/pystray |
| psutil | 进程与网络统计 | https://github.com/giampaolo/psutil |
| miniaudio / miniaudio C库 | 音频解码播放 | https://github.com/irmen/pyminiaudio / https://github.com/mackron/miniaudio |
| cffi / pycparser | 外部接口与构建依赖 | https://cffi.readthedocs.io / https://github.com/eliben/pycparser |
| PyInstaller | exe打包及引导程序 | https://github.com/pyinstaller/pyinstaller |
| Inno Setup | 安装程序构建 | https://jrsoftware.org/isinfo.php |

## 安装器中文翻译

installer/ChineseSimplified.isl为Inno Setup用户贡献的中文翻译文件，保留原始文件头及维护者署名：Zhenghan Yang (Kira)。来源：https://github.com/kira-96/Inno-Setup-Chinese-Simplified-Translation 。不将该翻译文件宣称为本项目原创。

## 音频

公开版不包含内置音乐或任何其他音频资源。音频由用户选择本地文件；本项目许可证不覆盖用户选择的第三方音乐。

随公开源码及程序提供的依赖许可证文本见[docs/licenses](docs/licenses)。pystray为LGPL组件，本项目未修改该依赖；完整版本源码可从其官方仓库对应v0.19.5获取，构建可通过requirements.txt替换依赖。
