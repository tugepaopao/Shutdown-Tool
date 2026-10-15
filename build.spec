# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置 —— 豪崽子の自动关机工具
作者：@wenhao

打包命令（在项目根目录执行）：
    .venv\\Scripts\\pyinstaller.exe --noconfirm --clean build.spec
"""

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('LICENSE', '.'),
        ('THIRD_PARTY_NOTICES.md', '.'),
        ('docs/licenses', 'licenses'),
        ('assets/ui', 'assets/ui'),
        ('assets/skins', 'assets/skins'),
        # 图标母图 assets/power_source.png（透明底蓝色电源开关球）→ tools/make_icon.py 生成下面这批
        # 注意：母图本身不打进包里，只打生成好的成品图
        ('assets/icon.ico', 'assets'),        # 桌面 / 安装包 / 便携版文件图标
        ('assets/icon.png', 'assets'),
        ('assets/icon_app.ico', 'assets'),    # 系统标题栏 / 任务栏 / 托盘图标（与 icon.ico 同源同内容）
        ('assets/icon_app.png', 'assets'),
        ('assets/icon_gear.png', 'assets'),   # 主界面顶栏右上角头像菜单（设置齿轮）
    ],
    hiddenimports=[
        'pystray._win32',
        'pystray._util.win32',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageTk',
        # v1.2.0：下面这几个是在函数内部延迟 import 的，显式写进来更保险
        'run_log',
        'ui_queue', 'ui_task_center',
        'ui_log',
        'ui_settings',
        'ui_dialogs', 'ui_reminder',
        'ui_compact', 'task_store', 'task_features', 'transfer_monitor', 'automation', 'ui_tasks', 'psutil',
        'quick_presets', 'diagnostics', 'ui_runtime_context', 'ui_restore', 'ui_settings_controls', 'ui_messagebox', 'ui_window', 'ui_native_restore', 'ui_dialog_palette', 'ui_dialog_transition', 'ui_popup_menu', 'ui_template_name', 'ui_titlebar', 'ui_transition', 'sound_library',
        'ui_sound','config_backups','condition_jobs','desktop_services','undo_store','schedule_preview','translations160','ui_localize','ui_extras','ui_summary',
        'ui_floating', 'ui_cozy', 'program_control', 'ui_close_program', 'display_awake', 'pc_controls', 'ui_pc_controls', 'audio_player', 'miniaudio', '_miniaudio', '_cffi_backend',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'numpy', 'matplotlib', 'scipy', 'pandas', 'PyQt5', 'PyQt6',
        'PySide2', 'PySide6', 'IPython', 'pytest', 'pydoc_data',
        'sqlite3', 'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='定时关机工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                 # 窗口程序，不弹黑框
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
    version='installer/version_info.txt',
)
