# -*- coding: utf-8 -*-
"""
多语言文本包（简体中文 / 正體中文 / English）
文件作者：@wenhao
"""
import os

APP_NAME_CHS = "定时关机工具"
APP_NAME_CHT = "定時關機工具"
APP_NAME_EN = "Scheduled Shutdown Tool"

AUTHOR = "@wenhao"
VERSION = "2.0.18"
BUILD_DATE = "2026-10-19"

FEATURE_EN = {
    '任务管理':'Task management','设置与任务模板备份':'Settings and task backups',
    '新增功能集中在这里，主页面布局保持不变。':'Manage additional features here.',
    '任务队列：编辑、复制、上移／下移':'Queue: edit, copy and reorder',
    '执行日志：搜索、筛选、导出CSV':'Logs: search, filter and export CSV',
    '保存、管理常用任务模板':'Save and manage task templates',
    '年月日／工作日／周末／下载／网络任务':'Calendar, recurring and transfer tasks',
    '延后当前正在计时的任务：':'Postpone the current timer:',
    '高级任务保存后默认停用；启用后才开始等待。\n工作日按周一至周五计算，不包含法定节假日调整。':'New advanced tasks are disabled until enabled.\nWeekdays mean Mon–Fri; public holidays are not adjusted.',
    '导出设置、模板和高级任务为JSON文件。\n导入前会显示预览；导入的高级任务全部停用。\n运行中定时、当前队列、自启动项不被替换。':'Back up settings, templates and advanced tasks as JSON.\nImported advanced tasks are disabled.\nCurrent timers, queue and startup settings are preserved.',
    '导出设置与模板':'Export settings and templates','导入设置与模板':'Import settings and templates',
    '搜索内容／详情':'Search text / details','开始日期':'Start date','结束日期':'End date',
    '全部':'All','搜索／筛选':'Search / Filter','重置':'Reset','日期格式：YYYY-MM-DD':'Date: YYYY-MM-DD',
    '导出当前筛选CSV':'Export filtered CSV','编辑':'Edit','复制':'Copy','上移':'Move up','下移':'Move down',
    '保存为模板':'Save as template','运行中任务先停止再编辑或排序':'Stop the active task before editing.',
    '编辑任务':'Edit task','常用任务模板':'Task templates','高级任务':'Advanced tasks',
    '任务／模板名称':'Task / template name','执行操作':'Action','执行方式':'Schedule',
    '程序／声音路径或消息':'Program / audio path or message','选择文件':'Browse',
    '时长（秒）':'Duration (seconds)','星期（1=周一，7=周日）':'Weekday (1=Mon, 7=Sun)',
    '日期 YYYY-MM-DD':'Date YYYY-MM-DD','时刻 HH:MM:SS':'Time HH:MM:SS','重复规则':'Repeat',
    '下载文件夹':'Download folder','浏览':'Browse','网络安静阈值（KiB/s）':'Quiet threshold (KiB/s)',
    '连续安静时长（秒）':'Quiet duration (seconds)','最长等待（小时）':'Maximum wait (hours)',
    '倒计时':'Countdown','每周指定星期（单次）':'Next selected weekday','时间段循环':'Repeating interval',
    '年月日／重复预约':'Calendar / recurring','下载文件夹结束后':'When downloads finish',
    '网络传输安静后':'When network becomes quiet','仅一次':'Once','每周一至周五':'Mon–Fri',
    '每周六、周日':'Sat–Sun','每天':'Daily','保存':'Save','取消':'Cancel','关闭':'Close',
    '新建':'New','删除':'Delete','启用／停用':'Enable / Disable','加入队列':'Add to queue',
    '保存主页面当前设定':'Save current setup','名称':'Name','操作':'Action','状态':'Status',
    '可用':'Ready','已启用':'Enabled','已停用':'Disabled',
    '预约／下载／网络任务，保存后需手动启用。':'Calendar and transfer tasks must be enabled after saving.',
    '按名称保存任务，双击编辑；使用时会复制到队列。':'Save named templates. Double-click to edit; use to create a copy.',
    '允许强制关闭应用（关机／重启／注销）':'Force applications to close (shutdown / restart / logoff)',
    '保存不会启动任务。启用高级任务后，条件满足会加入队列，保留10秒取消／延后。\n下载检测仅检查直接文件；网络安静不等于某个下载成功。':'Saving does not start a task. Enable advanced tasks to watch conditions.\nTriggered tasks enter the queue with 10 seconds to cancel or postpone.\nFolder checks exclude subfolders; quiet traffic does not guarantee a successful download.',
}

def feature_text(T, text):
    return text

# 语言文件清单（对应“显示界面设置 -> 选择语言”表格）
LANGUAGE_FILES = [
    {"code": "CHS", "file": "CHS.ini"},
    {"code": "CHT", "file": "CHT.ini"},
    {"code": "EN", "file": "English.ini"},
]

_TEXTS = {
    "CHS": {
        'sound_title': '播放声音',
        'sound_custom': '自选音频文件',
        'sound_browse': '选择文件',
        'set_tasks': '任务管理',
        'set_backup': '导入／导出',
        "app_name": APP_NAME_CHS,
        "menu_settings": "程序设置",
        "menu_params": "程序参数",
        "menu_about": "关于本程序",
        "menu_tip": "菜单：设置 / 参数 / 关于",
        "nav_actions": "选择操作",
        "nav_time": "设定时间",
        "nav_queue": "任务队列",
        "nav_log": "执行日志",
        "nav_settings": "程序设置",
        "nav_group_main": "定时设置",
        "nav_group_more": "更多",
        "panel_actions": "第 1 步 · 选择要执行的操作",
        "panel_time": "第 2 步 · 设定执行时间",
        "panel_time_desc": "时间从「现在」开始计算，到点自动执行上面选中的操作。",
        "brand_sub": "轻巧的定时管家",
        "group_mode": "执行方式",
        "mode_hint": "先选一种方式，下面会出现对应的填写框。",
        "hint_timer": "定时器：选择要执行的操作，然后设定要执行操作的时间",
        "group_actions": "可以执行的操作",
        "act_shutdown": "关闭电脑",
        "act_restart": "重启电脑",
        "act_logoff": "注销电脑",
        "act_sleep": "进入睡眠模式",
        "act_monitor_off": "关闭显示器",
        "act_run_program": "运行程序",
        "act_play_sound": "播放声音",
        "act_message": "弹出消息提示框",
        "group_countdown": "倒计时",
        "group_datetime": "日期",
        "group_interval": "时间段",
        "lbl_days": "天数",
        "lbl_hours": "小时数",
        "lbl_minutes": "分钟数",
        "lbl_seconds": "秒数",
        "lbl_h_short": "时",
        "lbl_m_short": "分",
        "lbl_s_short": "秒",
        "lbl_weekday": "星期",
        "btn_start": "开始定时器",
        "btn_pause": "暂停定时器",
        "btn_resume": "继续定时器",
        "btn_stop": "停止定时器",
        # 定时器按钮区改成「四个等宽小板块」后用的短文案（v1.1.2）
        "btn_go": "开始",
        "btn_pause_s": "暂停",
        "btn_resume_s": "继续",
        "btn_stop_s": "停止",
        "btn_clear": "清除",
        "btn_now": "立即执行选中的操作",
        "status_idle": "就绪：请选择操作并设定时间",
        "status_running": "定时器运行中 · 剩余 {t}",
        "status_paused": "定时器已暂停 · 剩余 {t}",
        "status_executed": "操作已执行：{a}",
        "status_stopped": "定时器已停止",
        "status_cleared": "已清除：时间已复位、定时器已停止",
        "status_wait": "等待执行 · 剩余 {t}",
        "prog_none": "",
        "prog_percent": "{p}%",
        "prog_remain": "剩余 {t}",
        "interval_hint": "每隔设定时间循环执行一次",
        "day_short": "天",
        # 设置窗口
        "set_title": "设置",
        "set_general": "通用设置",
        "set_display": "显示界面设置",
        "set_appearance": "外观",
        "set_other": "其他设置",
        "set_theme_group": "深浅色模式",
        "set_theme_light": "浅色",
        "set_theme_dark": "深色",
        "set_theme_system": "跟随系统",
        "set_accent_group": "主题色",
        "set_font_group": "字体大小",
        "set_font_small": "小",
        "set_font_normal": "标准",
        "set_font_large": "大",
        "set_font_huge": "特大",
        "set_appear_tip": "修改后点「应用」，颜色柔和过渡，计时保持运行。",
        "accent_blue": "蓝色",
        "accent_teal": "青色",
        "accent_green": "绿色",
        "accent_orange": "橙色",
        "accent_red": "红色",
        "accent_pink": "粉色",
        "accent_purple": "紫色",
        "accent_indigo": "靛蓝",
        "about_title": "关于本程序",
        "about_version": "版本 {v}",
        "about_author": "程序作者：{a}",
        "about_os": "运行系统：{o}",
        "about_desc": "一个轻巧的 Windows 定时关机小工具：\n"
                      "支持定时关机 / 重启 / 注销 / 睡眠 / 休眠 / 锁定电脑 /\n"
                      "运行或关闭程序 / 播放声音 / 弹出消息提示，并可最小化到系统托盘。",
        "about_tip": "双击桌面图标启动；关闭窗口默认最小化到托盘，\n右键托盘图标可退出程序。",
        "set_msghint_group": "消息提示",
        "set_confirm_before": "在执行操作前弹出窗口询问",
        "set_confirm_key": "仅询问关键操作",
        "set_confirm_on_exit": "在关闭本程序前询问",
        "set_confirm_exit_timer": "仅在计时器运行时询问",
        "set_force_group": "关机/重启/注销",
        "set_force_close": "在关闭/重启/注销电脑时强制关闭阻止这些操作的应用程序",
        "set_autostart_group": "开机启动",
        "set_autostart": "开机时自动启动本程序（最小化到托盘）",
        "set_sound_group": "定时器音效",
        "set_sound_10s": "在仅剩10秒就会执行操作时播放音效",
        "set_exit_group": "退出程序",
        "set_esc": "按下ESC时最小化本程序",
        "set_tray": "最小化本程序到托盘",
        "set_progress_group": "在界面下方的进度条中显示内容：",
        "set_prog_none": "不显示内容",
        "set_prog_percent": "显示进度百分比",
        "set_prog_remain": "显示剩余时间",
        "set_lang_group": "选择语言",
        "set_lang_file": "语言文件：",
        "set_lang_desc": "文件描述",
        "set_lang_name": "文件名",
        "set_lang_author": "文件作者",
        "set_lang_tip": "选择语言后点「应用」，计时保持运行。",
        "set_popup_10s": "在仅剩10秒就会执行操作时弹出本程序的界面",
        "set_tip_group": "定时器提示",
        "col_chs": "简体中文",
        "col_cht": "正體中文",
        "col_en": "English",
        "btn_ok": "确定",
        "btn_cancel": "取消",
        "btn_apply": "应用",
        # 程序参数
        "params_title": "程序参数",
        "params_hint": "程序参数：带参数启动本程序时仅能使用定时器的倒计时模式",
        "params_ok": "确定",
        "param_s": "/s",
        "param_r": "/r",
        "param_l": "/l",
        "param_sm": "/sm",
        "param_som": "/som",
        "param_rp": "/rp[=path]",
        "param_ra": "/ra[=path]",
        "param_m": "/m[=text]",
        "param_w": "/w",
        "param_t": "/t=sec",
        "param_min": "/min",
        "param_h": "/? 或 /h",
        "param_s_desc": "- 关闭电脑",
        "param_r_desc": "- 重启电脑",
        "param_l_desc": "- 注销电脑",
        "param_sm_desc": "- 进入睡眠模式",
        "param_som_desc": "- 关闭显示器",
        "param_rp_desc": "- 运行程序",
        "param_ra_desc": "- 播放声音",
        "param_m_desc": "- 弹出消息提示框",
        "param_w_desc": "- 不要自动开启倒计时",
        "param_t_desc": "- 以秒为单位设置倒计时",
        "param_min_desc": "- 启动后最小化本程序",
        "param_h_desc": "- 显示本帮助窗口",
        # 提示
        "tip_title": "提示",
        "tip_need_action": "请先选择要执行的操作。",
        "tip_need_time": "请设定大于 0 的时间。",
        "tip_need_program": "请先选择要运行的程序。",
        "tip_need_sound": "请先选择要播放的声音文件。",
        "tip_need_message": "请先输入要提示的消息内容。",
        "tip_timer_running": "定时器正在运行中。",
        "tip_exit_confirm": "定时器正在运行中，确定要退出本程序吗？\n退出后本次定时操作将被取消。",
        "tip_confirm_action": "确定要立即执行「{a}」吗？",
        "tip_confirm_action_title": "操作确认",
        "dlg_pick_program": "选择要运行的程序",
        "dlg_pick_sound": "选择要播放的声音文件",
        "dlg_message_title": "消息内容",
        "dlg_message_hint": "请输入要在消息提示框中显示的内容：",
        "dlg_files": "程序文件",
        "dlg_audio": "声音文件",
        "dlg_all_files": "所有文件",
        "tray_show": "显示主界面",
        "tray_start": "开始定时器",
        "tray_pause": "暂停定时器",
        "tray_now": "立即执行选中的操作",
        "tray_settings": "程序设置",
        "tray_exit": "退出",
        "tray_tip": "{n} - 最小化到托盘运行中",
        "tray_minimized_tip": "已最小化到系统托盘，程序仍在后台运行。\n右键托盘图标可退出，双击可打开主界面。",
        "toast_default": "系统将在 {s} 秒后执行操作，请及时保存您的工作！",
        "toast_now": "即将执行操作，请及时保存您的工作！",
        "cat_days": "天",

        # ===== v1.2.0 新增：快捷预设 / 队列 / 执行日志 / 可取消 / 持久化 =====
        "menu_queue": "定时任务队列",
        "menu_log": "执行日志",
        "quick_group": "快捷预设",
        "quick_30m": "30 分钟后",
        "quick_1h": "1 小时后",
        "quick_2h": "2 小时后",
        "quick_18": "今天 18:00",
        "quick_22": "今天 22:00",
        "quick_tmr8": "明天 08:00",
        "quick_at_fmt": "今天 {h}:{m}",
        "quick_tmr_fmt": "明天 {h}:{m}",
        "set_quick_group": "快捷预设",
        "set_quick_tip": "主界面「快捷预设」最后两个按钮的时间可以在这里自己定。",
        "set_quick_p4": "第 4 个按钮（今天几点）",
        "set_quick_p5": "第 5 个按钮（明天几点）",
        "set_quick_note": "格式为「时:分」，例如 22:00、08:30。填错会自动用默认值。",
        "set_quick_reset": "恢复默认（今天 22:00 / 明天 08:00）",
        "btn_enqueue": "把当前设定加入队列",
        "queue_title": "定时任务队列",
        "queue_hint": "队列里的任务按顺序执行：前一个跑完，自动接着下一个。\n点「把当前设定加入队列」，就能把主界面上现在的时间设定排进来。",
        "queue_empty": "队列是空的",
        "queue_col_when": "执行时间",
        "queue_col_action": "操作",
        "queue_col_note": "说明",
        "queue_add_now": "把当前设定加入队列",
        "queue_remove": "删除选中",
        "queue_clear": "清空队列",
        "queue_close": "关闭",
        "queue_bar": "队列中有 {n} 个任务待执行 · 点击管理",
        "queue_added": "已加入队列（共 {n} 个任务）",
        "queue_removed": "已从队列删除 {n} 个任务",
        "queue_cleared": "队列已清空",
        "queue_need_time": "请先设定大于 0 的时间，再加入队列。",
        "when_after": "{t} 后",
        "when_interval": "每 {t} 循环",
        "note_countdown": "倒计时",
        "note_interval": "循环执行",
        "note_datetime": "指定时刻",
        "log_title": "执行日志",
        "log_hint": "记录每一次定时设定、执行结果与取消操作（最多保留 500 条，双击某条可看完整详情）。",
        "log_empty": "暂无记录",
        "log_col_time": "时间",
        "log_col_kind": "事件",
        "log_col_text": "内容",
        "log_col_detail": "详情",
        "log_clear": "清空日志",
        "log_close": "关闭",
        "log_kind_setup": "设定定时",
        "log_kind_done": "执行成功",
        "log_kind_error": "执行失败",
        "log_kind_cancel": "取消/停止",
        "log_kind_info": "信息",
        "log_setup_text": "设定定时：{w} 执行「{a}」",
        "log_exec_text": "开始执行「{a}」",
        "log_done_text": "「{a}」执行成功",
        "log_error_text": "「{a}」执行失败",
        "log_cancel_text": "在到点前取消了定时执行",
        "log_stop_text": "手动停止了定时器",
        "log_clear_text": "清除了定时与队列",
        "log_queue_text": "加入队列：{w} 执行「{a}」",
        "log_resume_text": "恢复上次没跑完的定时：「{a}」还剩 {w}",
        "log_missed_text": "上次的定时在程序关闭期间已经到点，未补执行",
        "status_due": "定时器运行中 · 剩余 {t} · 预计 {d} 执行",
        "status_due_paused": "定时器已暂停 · 剩余 {t} · 预计 {d} 执行",
        "status_cancelled": "已取消本次执行",
        "tip_cancel_title": "即将执行",
        "cancel_toast_text": "「{a}」将在 {s} 秒后执行。\n如需改变主意，请点下面的按钮取消。",
        "btn_cancel_action": "取消执行",
        "confirm_dont_ask": "本次启动不再询问",
        "set_notify_group": "消息提示框",
        "set_toast_seconds": "消息提示框停留时长（秒）",
        "set_toast_tip": "范围 3 ~ 600 秒，默认 15 秒。",
        "set_cancel_group": "到时前提示",
        "set_cancel_10s": "到点前 10 秒弹出提示框，里面可以点「取消执行」",
        "set_log_group": "执行日志",
        "set_log_enabled": "记录执行日志（什么时候设定了什么、有没有执行成功）",
        "set_resume_group": "定时器状态",
        "set_resume_timer": "关闭程序后重新打开时，继续上次没跑完的定时",
        "tray_clear": "清除",
        "tray_queue": "定时任务队列",
    },
    "CHT": {
        'sound_title': '播放聲音',
        'sound_custom': '自選音訊檔案',
        'sound_browse': '選擇檔案',
        'set_tasks': '任務管理',
        'set_backup': '匯入／匯出',
        "app_name": APP_NAME_CHT,
        "menu_settings": "程式設定",
        "menu_params": "程式參數",
        "menu_about": "關於本程式",
        "menu_tip": "選單：設定 / 參數 / 關於",
        "nav_actions": "選擇操作",
        "nav_time": "設定時間",
        "nav_queue": "任務隊列",
        "nav_log": "執行日誌",
        "nav_settings": "程式設定",
        "nav_group_main": "定時設定",
        "nav_group_more": "更多",
        "panel_actions": "第 1 步 · 選擇要執行的操作",
        "panel_time": "第 2 步 · 設定執行時間",
        "panel_time_desc": "時間從「現在」開始計算，到點自動執行上面選中的操作。",
        "brand_sub": "輕巧的定時管家",
        "group_mode": "執行方式",
        "mode_hint": "先選一種方式，下面會出現對應的填寫框。",
        "hint_timer": "定時器：選擇要執行的操作，然後設定要執行操作的時間",
        "group_actions": "可以執行的操作",
        "act_shutdown": "關閉電腦",
        "act_restart": "重新啟動電腦",
        "act_logoff": "登出電腦",
        "act_sleep": "進入睡眠模式",
        "act_monitor_off": "關閉顯示器",
        "act_run_program": "執行程式",
        "act_play_sound": "播放音效",
        "act_message": "彈出訊息提示方塊",
        "group_countdown": "倒數計時",
        "group_datetime": "日期",
        "group_interval": "時間間隔",
        "lbl_days": "天數",
        "lbl_hours": "小時數",
        "lbl_minutes": "分鐘數",
        "lbl_seconds": "秒數",
        "lbl_h_short": "時",
        "lbl_m_short": "分",
        "lbl_s_short": "秒",
        "lbl_weekday": "星期",
        "btn_start": "開始定時器",
        "btn_pause": "暫停定時器",
        "btn_resume": "繼續定時器",
        "btn_stop": "停止定時器",
        "btn_go": "開始",
        "btn_pause_s": "暫停",
        "btn_resume_s": "繼續",
        "btn_stop_s": "停止",
        "btn_clear": "清除",
        "btn_now": "立即執行選取的操作",
        "status_idle": "就緒：請選擇操作並設定時間",
        "status_running": "定時器執行中 · 剩餘 {t}",
        "status_paused": "定時器已暫停 · 剩餘 {t}",
        "status_executed": "操作已執行：{a}",
        "status_stopped": "定時器已停止",
        "status_cleared": "已清除：時間已復位、定時器已停止",
        "status_wait": "等待執行 · 剩餘 {t}",
        "prog_none": "",
        "prog_percent": "{p}%",
        "prog_remain": "剩餘 {t}",
        "interval_hint": "每隔設定的時間循環執行一次",
        "day_short": "天",
        "set_title": "設定",
        "set_general": "一般設定",
        "set_display": "顯示介面設定",
        "set_appearance": "外觀",
        "set_other": "其他設定",
        "set_theme_group": "深淺色模式",
        "set_theme_light": "淺色",
        "set_theme_dark": "深色",
        "set_theme_system": "跟隨系統",
        "set_accent_group": "主題色",
        "set_font_group": "字體大小",
        "set_font_small": "小",
        "set_font_normal": "標準",
        "set_font_large": "大",
        "set_font_huge": "特大",
        "set_appear_tip": "修改後點「套用」，顏色柔和過渡，計時保持執行。",
        "accent_blue": "藍色",
        "accent_teal": "青色",
        "accent_green": "綠色",
        "accent_orange": "橙色",
        "accent_red": "紅色",
        "accent_pink": "粉色",
        "accent_purple": "紫色",
        "accent_indigo": "靛藍",
        "about_title": "關於本程式",
        "about_version": "版本 {v}",
        "about_author": "程式作者：{a}",
        "about_os": "執行系統：{o}",
        "about_desc": "一個輕巧的 Windows 定時關機小工具：\n"
                      "支援定時關機 / 重新啟動 / 登出 / 睡眠 / 休眠 / 鎖定電腦 /\n"
                      "執行或關閉程式 / 播放音效 / 彈出訊息提示，並可最小化到系統匣。",
        "about_tip": "按兩下桌面圖示啟動；關閉視窗預設最小化到系統匣，\n以滑鼠右鍵點系統匣圖示可結束程式。",
        "set_msghint_group": "訊息提示",
        "set_confirm_before": "在執行操作前彈出視窗詢問",
        "set_confirm_key": "僅詢問關鍵操作",
        "set_confirm_on_exit": "在關閉本程式前詢問",
        "set_confirm_exit_timer": "僅在計時器執行時詢問",
        "set_force_group": "關機/重新啟動/登出",
        "set_force_close": "在關閉/重新啟動/登出電腦時強制關閉阻止這些操作的應用程式",
        "set_autostart_group": "開機啟動",
        "set_autostart": "開機時自動啟動本程式（最小化到系統匣）",
        "set_sound_group": "定時器音效",
        "set_sound_10s": "在僅剩10秒就會執行操作時播放音效",
        "set_exit_group": "結束程式",
        "set_esc": "按下ESC時最小化本程式",
        "set_tray": "最小化本程式到系統匣",
        "set_progress_group": "在介面下方的進度列中顯示內容：",
        "set_prog_none": "不顯示內容",
        "set_prog_percent": "顯示進度百分比",
        "set_prog_remain": "顯示剩餘時間",
        "set_lang_group": "選擇語言",
        "set_lang_file": "語言檔案：",
        "set_lang_desc": "檔案描述",
        "set_lang_name": "檔案名稱",
        "set_lang_author": "檔案作者",
        "set_lang_tip": "選擇語言後點「套用」，計時保持執行。",
        "set_popup_10s": "在僅剩10秒就會執行操作時彈出本程式的介面",
        "set_tip_group": "定時器提示",
        "col_chs": "簡體中文",
        "col_cht": "正體中文",
        "col_en": "English",
        "btn_ok": "確定",
        "btn_cancel": "取消",
        "btn_apply": "套用",
        "params_title": "程式參數",
        "params_hint": "程式參數：帶參數啟動本程式時僅能使用定時器的倒數計時模式",
        "params_ok": "確定",
        "param_s": "/s",
        "param_r": "/r",
        "param_l": "/l",
        "param_sm": "/sm",
        "param_som": "/som",
        "param_rp": "/rp[=path]",
        "param_ra": "/ra[=path]",
        "param_m": "/m[=text]",
        "param_w": "/w",
        "param_t": "/t=sec",
        "param_min": "/min",
        "param_h": "/? 或 /h",
        "param_s_desc": "- 關閉電腦",
        "param_r_desc": "- 重新啟動電腦",
        "param_l_desc": "- 登出電腦",
        "param_sm_desc": "- 進入睡眠模式",
        "param_som_desc": "- 關閉顯示器",
        "param_rp_desc": "- 執行程式",
        "param_ra_desc": "- 播放音效",
        "param_m_desc": "- 彈出訊息提示方塊",
        "param_w_desc": "- 不要自動開啟倒數計時",
        "param_t_desc": "- 以秒為單位設定倒數計時",
        "param_min_desc": "- 啟動後最小化本程式",
        "param_h_desc": "- 顯示本說明視窗",
        "tip_title": "提示",
        "tip_need_action": "請先選擇要執行的操作。",
        "tip_need_time": "請設定大於 0 的時間。",
        "tip_need_program": "請先選擇要執行的程式。",
        "tip_need_sound": "請先選擇要播放的音效檔案。",
        "tip_need_message": "請先輸入要提示的訊息內容。",
        "tip_timer_running": "定時器正在執行中。",
        "tip_exit_confirm": "定時器正在執行中，確定要結束本程式嗎？\n結束後本次定時操作將被取消。",
        "tip_confirm_action": "確定要立即執行「{a}」嗎？",
        "tip_confirm_action_title": "操作確認",
        "dlg_pick_program": "選擇要執行的程式",
        "dlg_pick_sound": "選擇要播放的音效檔案",
        "dlg_message_title": "訊息內容",
        "dlg_message_hint": "請輸入要在訊息提示方塊中顯示的內容：",
        "dlg_files": "程式檔案",
        "dlg_audio": "音效檔案",
        "dlg_all_files": "所有檔案",
        "tray_show": "顯示主介面",
        "tray_start": "開始定時器",
        "tray_pause": "暫停定時器",
        "tray_now": "立即執行選取的操作",
        "tray_settings": "程式設定",
        "tray_exit": "結束",
        "tray_tip": "{n} - 最小化到系統匣執行中",
        "tray_minimized_tip": "已最小化到系統匣，程式仍在背景執行。\n以滑鼠右鍵點系統匣圖示可結束，按兩下可開啟主介面。",
        "toast_default": "系統將在 {s} 秒後執行操作，請及時儲存您的工作！",
        "toast_now": "即將執行操作，請及時儲存您的工作！",
        "cat_days": "天",

        "menu_queue": "定時任務佇列",
        "menu_log": "執行日誌",
        "quick_group": "快捷預設",
        "quick_30m": "30 分鐘後",
        "quick_1h": "1 小時後",
        "quick_2h": "2 小時後",
        "quick_18": "今天 18:00",
        "quick_22": "今天 22:00",
        "quick_tmr8": "明天 08:00",
        "quick_at_fmt": "今天 {h}:{m}",
        "quick_tmr_fmt": "明天 {h}:{m}",
        "set_quick_group": "快捷預設",
        "set_quick_tip": "主界面「快捷預設」最後兩個按鈕的時間可以在這裡自己定。",
        "set_quick_p4": "第 4 個按鈕（今天幾點）",
        "set_quick_p5": "第 5 個按鈕（明天幾點）",
        "set_quick_note": "格式為「時:分」，例如 22:00、08:30。填錯會自動用預設值。",
        "set_quick_reset": "恢復預設（今天 22:00 / 明天 08:00）",
        "btn_enqueue": "將目前設定加入佇列",
        "queue_title": "定時任務佇列",
        "queue_hint": "佇列中的任務依序執行：前一個跑完，自動接著下一個。\n點「將目前設定加入佇列」，就能把主介面上現在的時間設定排進來。",
        "queue_empty": "佇列是空的",
        "queue_col_when": "執行時間",
        "queue_col_action": "操作",
        "queue_col_note": "說明",
        "queue_add_now": "將目前設定加入佇列",
        "queue_remove": "刪除選取",
        "queue_clear": "清空佇列",
        "queue_close": "關閉",
        "queue_bar": "佇列中有 {n} 個任務待執行 · 點擊管理",
        "queue_added": "已加入佇列（共 {n} 個任務）",
        "queue_removed": "已從佇列刪除 {n} 個任務",
        "queue_cleared": "佇列已清空",
        "queue_need_time": "請先設定大於 0 的時間，再加入佇列。",
        "when_after": "{t} 後",
        "when_interval": "每 {t} 循環",
        "note_countdown": "倒數計時",
        "note_interval": "循環執行",
        "note_datetime": "指定時刻",
        "log_title": "執行日誌",
        "log_hint": "記錄每一次定時設定、執行結果與取消操作（最多保留 500 筆，按兩下某筆可看完整詳情）。",
        "log_empty": "暫無記錄",
        "log_col_time": "時間",
        "log_col_kind": "事件",
        "log_col_text": "內容",
        "log_col_detail": "詳情",
        "log_clear": "清空日誌",
        "log_close": "關閉",
        "log_kind_setup": "設定定時",
        "log_kind_done": "執行成功",
        "log_kind_error": "執行失敗",
        "log_kind_cancel": "取消/停止",
        "log_kind_info": "資訊",
        "log_setup_text": "設定定時：{w} 執行「{a}」",
        "log_exec_text": "開始執行「{a}」",
        "log_done_text": "「{a}」執行成功",
        "log_error_text": "「{a}」執行失敗",
        "log_cancel_text": "在到點前取消了定時執行",
        "log_stop_text": "手動停止了定時器",
        "log_clear_text": "清除了定時與佇列",
        "log_queue_text": "加入佇列：{w} 執行「{a}」",
        "log_resume_text": "恢復上次沒跑完的定時：「{a}」還剩 {w}",
        "log_missed_text": "上次的定時在程式關閉期間已經到點，未補執行",
        "status_due": "定時器執行中 · 剩餘 {t} · 預計 {d} 執行",
        "status_due_paused": "定時器已暫停 · 剩餘 {t} · 預計 {d} 執行",
        "status_cancelled": "已取消本次執行",
        "tip_cancel_title": "即將執行",
        "cancel_toast_text": "「{a}」將在 {s} 秒後執行。\n如需改變主意，請點下面的按鈕取消。",
        "btn_cancel_action": "取消執行",
        "confirm_dont_ask": "本次啟動不再詢問",
        "set_notify_group": "訊息提示方塊",
        "set_toast_seconds": "訊息提示方塊停留時間（秒）",
        "set_toast_tip": "範圍 3 ~ 600 秒，預設 15 秒。",
        "set_cancel_group": "到時前提示",
        "set_cancel_10s": "到點前 10 秒彈出提示方塊，裡面可以點「取消執行」",
        "set_log_group": "執行日誌",
        "set_log_enabled": "記錄執行日誌（什麼時候設定了什麼、有沒有執行成功）",
        "set_resume_group": "定時器狀態",
        "set_resume_timer": "關閉程式後重新開啟時，繼續上次沒跑完的定時",
        "tray_clear": "清除",
        "tray_queue": "定時任務佇列",
    },
    "EN": {
        'sound_title': 'Play sound',
        'sound_custom': 'Choose an audio file',
        'sound_browse': 'Browse',
        'set_tasks': 'Task management',
        'set_backup': 'Import / Export',
        "app_name": APP_NAME_EN,
        "menu_settings": "Settings",
        "menu_params": "Parameters",
        "menu_about": "About",
        "menu_tip": "Menu: Settings / Parameters / About",
        "nav_actions": "Actions",
        "nav_time": "Set Time",
        "nav_queue": "Task Queue",
        "nav_log": "Log",
        "nav_settings": "Settings",
        "nav_group_main": "TIMER",
        "nav_group_more": "MORE",
        "panel_actions": "Step 1 · Choose an action",
        "panel_time": "Step 2 · Set the time",
        "panel_time_desc": "Counts down from now and runs the selected action automatically.",
        "brand_sub": "A light timer helper",
        "group_mode": "Mode",
        "mode_hint": "Pick a mode first; the matching fields appear below.",
        "hint_timer": "Timer: choose an action, then set the time to perform it",
        "group_actions": "Available actions",
        "act_shutdown": "Shut down",
        "act_restart": "Restart",
        "act_logoff": "Log off",
        "act_sleep": "Sleep",
        "act_monitor_off": "Turn off monitor",
        "act_run_program": "Run program",
        "act_play_sound": "Play sound",
        "act_message": "Show message box",
        "group_countdown": "Countdown",
        "group_datetime": "Date",
        "group_interval": "Interval",
        "lbl_days": "Days",
        "lbl_hours": "Hours",
        "lbl_minutes": "Minutes",
        "lbl_seconds": "Seconds",
        "lbl_h_short": "H",
        "lbl_m_short": "M",
        "lbl_s_short": "S",
        "lbl_weekday": "Day",
        "btn_start": "Start timer",
        "btn_pause": "Pause timer",
        "btn_resume": "Resume timer",
        "btn_stop": "Stop timer",
        "btn_go": "Start",
        "btn_pause_s": "Pause",
        "btn_resume_s": "Resume",
        "btn_stop_s": "Stop",
        "btn_clear": "Clear",
        "btn_now": "Perform selected action now",
        "status_idle": "Ready: choose an action and set the time",
        "status_running": "Timer running · remaining {t}",
        "status_paused": "Timer paused · remaining {t}",
        "status_executed": "Action performed: {a}",
        "status_stopped": "Timer stopped",
        "status_cleared": "Cleared: time reset and timer stopped",
        "status_wait": "Waiting · remaining {t}",
        "prog_none": "",
        "prog_percent": "{p}%",
        "prog_remain": "{t} left",
        "interval_hint": "Repeat the action at the given interval",
        "day_short": "d",
        "set_title": "Settings",
        "set_general": "General",
        "set_display": "Interface",
        "set_appearance": "Appearance",
        "set_other": "Others",
        "set_theme_group": "Light / Dark mode",
        "set_theme_light": "Light",
        "set_theme_dark": "Dark",
        "set_theme_system": "Follow system",
        "set_accent_group": "Accent color",
        "set_font_group": "Font size",
        "set_font_small": "Small",
        "set_font_normal": "Normal",
        "set_font_large": "Large",
        "set_font_huge": "Extra large",
        "set_appear_tip": "Click Apply for a smooth color transition. Running timers are preserved.",
        "accent_blue": "Blue",
        "accent_teal": "Teal",
        "accent_green": "Green",
        "accent_orange": "Orange",
        "accent_red": "Red",
        "accent_pink": "Pink",
        "accent_purple": "Purple",
        "accent_indigo": "Indigo",
        "about_title": "About",
        "about_version": "Version {v}",
        "about_author": "Author: {a}",
        "about_os": "Running on: {o}",
        "about_desc": "A lightweight Windows auto-shutdown utility:\n"
                      "schedule shutdown / restart / log off / sleep / hibernate / lock,\n"
                      "run or close a program, play a sound, or show a message - and minimize to tray.",
        "about_tip": "Double-click the desktop icon to start. Closing the window\n"
                     "minimizes to the tray; right-click the tray icon to exit.",
        "set_msghint_group": "Message prompt",
        "set_confirm_before": "Ask for confirmation before performing an action",
        "set_confirm_key": "Only for critical actions",
        "set_confirm_on_exit": "Ask before closing this program",
        "set_confirm_exit_timer": "Only while the timer is running",
        "set_force_group": "Shutdown / Restart / Log off",
        "set_force_close": "Force-close applications that block these operations",
        "set_autostart_group": "Startup",
        "set_autostart": "Start this program at Windows startup (minimized to tray)",
        "set_sound_group": "Timer sound",
        "set_sound_10s": "Play a sound when only 10 seconds remain",
        "set_exit_group": "Exit",
        "set_esc": "Minimize this program when ESC is pressed",
        "set_tray": "Minimize this program to tray",
        "set_progress_group": "Show in the progress bar:",
        "set_prog_none": "Nothing",
        "set_prog_percent": "Progress percentage",
        "set_prog_remain": "Remaining time",
        "set_lang_group": "Language",
        "set_lang_file": "Language files:",
        "set_lang_desc": "Description",
        "set_lang_name": "File name",
        "set_lang_author": "Author",
        "set_lang_tip": "Select a language and click Apply. Running timers are preserved.",
        "set_popup_10s": "Bring this program's window to front when only 10 seconds remain",
        "set_tip_group": "Timer notice",
        "col_chs": "Simplified Chinese",
        "col_cht": "Traditional Chinese",
        "col_en": "English",
        "btn_ok": "OK",
        "btn_cancel": "Cancel",
        "btn_apply": "Apply",
        "params_title": "Command line parameters",
        "params_hint": "Parameters: when started with parameters, only the countdown mode is available",
        "params_ok": "OK",
        "param_s": "/s",
        "param_r": "/r",
        "param_l": "/l",
        "param_sm": "/sm",
        "param_som": "/som",
        "param_rp": "/rp[=path]",
        "param_ra": "/ra[=path]",
        "param_m": "/m[=text]",
        "param_w": "/w",
        "param_t": "/t=sec",
        "param_min": "/min",
        "param_h": "/? or /h",
        "param_s_desc": "- Shut down the computer",
        "param_r_desc": "- Restart the computer",
        "param_l_desc": "- Log off the computer",
        "param_sm_desc": "- Enter sleep mode",
        "param_som_desc": "- Turn off the monitor",
        "param_rp_desc": "- Run a program",
        "param_ra_desc": "- Play a sound",
        "param_m_desc": "- Show a message box",
        "param_w_desc": "- Do not start the countdown automatically",
        "param_t_desc": "- Set the countdown in seconds",
        "param_min_desc": "- Start minimized",
        "param_h_desc": "- Show this help window",
        "tip_title": "Notice",
        "tip_need_action": "Please select an action first.",
        "tip_need_time": "Please set a time greater than 0.",
        "tip_need_program": "Please select a program to run first.",
        "tip_need_sound": "Please select a sound file first.",
        "tip_need_message": "Please enter the message text first.",
        "tip_timer_running": "The timer is running.",
        "tip_exit_confirm": "The timer is running. Exit anyway?\nThe current timer will be cancelled.",
        "tip_confirm_action": "Perform \"{a}\" now?",
        "tip_confirm_action_title": "Confirm action",
        "dlg_pick_program": "Select a program to run",
        "dlg_pick_sound": "Select a sound file",
        "dlg_message_title": "Message text",
        "dlg_message_hint": "Enter the text to display in the message box:",
        "dlg_files": "Programs",
        "dlg_audio": "Sound files",
        "dlg_all_files": "All files",
        "tray_show": "Show window",
        "tray_start": "Start timer",
        "tray_pause": "Pause timer",
        "tray_now": "Perform action now",
        "tray_settings": "Settings",
        "tray_exit": "Exit",
        "tray_tip": "{n} - running in the notification area",
        "tray_minimized_tip": "Minimized to the notification area; the program is still running.\nRight-click the tray icon to exit, double-click to open the window.",
        "toast_default": "The system will perform the action in {s} seconds. Save your work!",
        "toast_now": "The action is about to be performed. Save your work!",
        "cat_days": "d",

        "menu_queue": "Task queue",
        "menu_log": "Activity log",
        "quick_group": "Quick presets",
        "quick_30m": "In 30 min",
        "quick_1h": "In 1 hour",
        "quick_2h": "In 2 hours",
        "quick_18": "Today 18:00",
        "quick_22": "Today 22:00",
        "quick_tmr8": "Tomorrow 08:00",
        "quick_at_fmt": "Today {h}:{m}",
        "quick_tmr_fmt": "Tomorrow {h}:{m}",
        "set_quick_group": "Quick presets",
        "set_quick_tip": "Set the times of the last two preset buttons here.",
        "set_quick_p4": "4th button (today at)",
        "set_quick_p5": "5th button (tomorrow at)",
        "set_quick_note": "Use H:MM format, e.g. 22:00 or 08:30. Invalid input falls back to defaults.",
        "set_quick_reset": "Reset to defaults (today 22:00 / tomorrow 08:00)",
        "btn_enqueue": "Add current setting to queue",
        "queue_title": "Task queue",
        "queue_hint": "Queued tasks run in order: when one finishes the next starts automatically.\nClick \"Add current setting to queue\" to enqueue the time set in the main window.",
        "queue_empty": "The queue is empty",
        "queue_col_when": "Run at",
        "queue_col_action": "Action",
        "queue_col_note": "Note",
        "queue_add_now": "Add current setting",
        "queue_remove": "Remove selected",
        "queue_clear": "Clear queue",
        "queue_close": "Close",
        "queue_bar": "{n} task(s) queued - click to manage",
        "queue_added": "Added to queue ({n} task(s) total)",
        "queue_removed": "Removed {n} task(s) from the queue",
        "queue_cleared": "Queue cleared",
        "queue_need_time": "Please set a time greater than 0 before adding to the queue.",
        "when_after": "in {t}",
        "when_interval": "every {t}",
        "note_countdown": "Countdown",
        "note_interval": "Repeating",
        "note_datetime": "At a set time",
        "log_title": "Activity log",
        "log_hint": "Records every timer setting, execution result and cancellation (up to 500 entries; double-click a row for full details).",
        "log_empty": "No records",
        "log_col_time": "Time",
        "log_col_kind": "Event",
        "log_col_text": "Detail",
        "log_col_detail": "Message",
        "log_clear": "Clear log",
        "log_close": "Close",
        "log_kind_setup": "Timer set",
        "log_kind_done": "Success",
        "log_kind_error": "Failed",
        "log_kind_cancel": "Cancelled",
        "log_kind_info": "Info",
        "log_setup_text": "Timer set: \"{a}\" at {w}",
        "log_exec_text": "Performing \"{a}\"",
        "log_done_text": "\"{a}\" succeeded",
        "log_error_text": "\"{a}\" failed",
        "log_cancel_text": "Cancelled before the scheduled time",
        "log_stop_text": "Timer stopped manually",
        "log_clear_text": "Timer and queue cleared",
        "log_queue_text": "Queued: \"{a}\" at {w}",
        "log_resume_text": "Resumed previous timer: \"{a}\" with {w} left",
        "log_missed_text": "The previous timer already fired while the program was closed; not re-run",
        "status_due": "Timer running - {t} left - due at {d}",
        "status_due_paused": "Timer paused - {t} left - due at {d}",
        "status_cancelled": "Execution cancelled",
        "tip_cancel_title": "About to run",
        "cancel_toast_text": "\"{a}\" will run in {s} seconds.\nClick the button below to cancel if you changed your mind.",
        "btn_cancel_action": "Cancel execution",
        "confirm_dont_ask": "Do not ask again this session",
        "set_notify_group": "Message box",
        "set_toast_seconds": "Message box duration (seconds)",
        "set_toast_tip": "From 3 to 600 seconds; default 15.",
        "set_cancel_group": "Before it fires",
        "set_cancel_10s": "Show a cancellable notice 10 seconds before the action runs",
        "set_log_group": "Activity log",
        "set_log_enabled": "Keep an activity log (what was scheduled and whether it succeeded)",
        "set_resume_group": "Timer state",
        "set_resume_timer": "Resume the unfinished timer the next time the program starts",
        "tray_clear": "Clear",
        "tray_queue": "Task queue",
    },
}

# v1.6.3：只有第6项自定义，第5项固定22:00。
_TEXTS['CHS'].update(set_quick_tip='前五个快捷预设固定；只有最后一个按钮（明天几点）可自定义。',set_quick_p5='第6个按钮（明天几点）',set_quick_reset='恢复默认（明天08:00）')
_TEXTS['CHT'].update(set_quick_tip='前五個快捷預設固定；只有最後一個按鈕（明天幾點）可自訂。',set_quick_p5='第6個按鈕（明天幾點）',set_quick_reset='恢復預設（明天08:00）')
_TEXTS['EN'].update(set_quick_tip='The first five presets are fixed. Only the last (tomorrow) time is editable.',set_quick_p5='Preset 6 (tomorrow)',set_quick_reset='Reset (tomorrow08:00)')


# v1.6.3 appearance page; language follows existing language selection.
_APPEARANCE_TEXT = {
 'CHS': {'appearance_choose':'选择喜欢的颜色，先查看预览，再点「应用」。', 'appearance_preview':'配色预览', 'appearance_preview_name':'预览 · {name}', 'appearance_card':'普通卡片', 'appearance_selected':'✓ 选中状态', 'appearance_about':'使用说明', 'appearance_note':'• 背景、卡片、边框、预设图标统一跟随主题色。\n• 关机等操作图标保留原有颜色，方便辨认。\n• 固定浅色界面与标准字号，保持清晰、稳定。\n• 点「应用」后柔和切换，不会中断正在运行的计时。'},
 'CHT': {'appearance_choose':'選擇喜歡的顏色，先查看預覽，再點「套用」。', 'appearance_preview':'配色預覽', 'appearance_preview_name':'預覽 · {name}', 'appearance_card':'一般卡片', 'appearance_selected':'✓ 選取狀態', 'appearance_about':'使用說明', 'appearance_note':'• 背景、卡片、邊框、預設圖示統一跟隨主題色。\n• 關機等操作圖示保留原有顏色，方便辨認。\n• 固定淺色介面與標準字級，保持清晰、穩定。\n• 點「套用」後柔和切換，不會中斷正在執行的計時。'},
 'EN': {'appearance_choose':'Choose a color, preview it, then click Apply.', 'appearance_preview':'Color preview', 'appearance_preview_name':'Preview · {name}', 'appearance_card':'Standard card', 'appearance_selected':'✓ Selected', 'appearance_about':'How it works', 'appearance_note':'• Backgrounds, cards, borders and preset icons follow your color.\n• Action icons retain their familiar colors.\n• Light mode and standard font size are fixed.\n• Apply changes smoothly without interrupting the timer.'}}
for _lang,_values in _APPEARANCE_TEXT.items():_TEXTS[_lang].update(_values)

for _lang in _TEXTS:
    _TEXTS[_lang]['set_quick_tip']={'CHS':'前五个预设固定；最后一项可选择今天、明天、后天或最多7天后。','CHT':'前五個預設固定；最後一項可選今天、明天、後天或最多7天後。','EN':'The first five presets are fixed. The last can target today or up to 7 days from today.'}[_lang]
    _TEXTS[_lang]['set_quick_p5']={'CHS':'第6个按钮的时间','CHT':'第6個按鈕的時間','EN':'Preset 6 time'}[_lang]
_TEXTS['EN'].update(act_message='Message box',btn_now='Run now',btn_enqueue='Add to queue',queue_add_now='Add current setup',queue_hint='Tasks run in order. Add the current setup to schedule another task.',set_tasks='Task management')

_STRINGS = {
    'pc_title': ('电脑快控', '電腦快控', 'PC controls'),
    'pc_brightness': ('显示器亮度', '顯示器亮度', 'Display brightness'),
    'pc_primary': ('主屏亮度', '主螢幕亮度', 'Main display'),
    'pc_secondary': ('副屏 {n} 亮度', '副螢幕 {n} 亮度', 'Display {n} brightness'),
    'pc_count': ('已检测到 {n} 个显示器', '已偵測到 {n} 個顯示器', '{n} displays detected'),
    'pc_refresh': ('刷新设备', '重新偵測裝置', 'Refresh devices'),
    'pc_link': ('联动调整支持调节的显示器', '連動調整支援調節的顯示器', 'Link supported displays'),
    'pc_volume': ('系统音量', '系統音量', 'System volume'),
    'pc_mute': ('静音', '靜音', 'Mute'),
    'pc_unmute': ('取消静音', '取消靜音', 'Unmute'),
    'pc_detecting': ('正在检测设备…', '正在偵測裝置…', 'Detecting devices…'),
    'pc_missing': ('未检测到显示器，可连接后刷新', '未偵測到顯示器，連接後請重新偵測', 'No display found. Connect one and refresh'),
    'pc_unavailable': ('不支持调节，请检查显示器 DDC/CI 设置', '不支援調節，請檢查顯示器 DDC/CI 設定', 'Unavailable. Check the display DDC/CI setting'),
    'pc_audio_unavailable': ('未检测到可用的音频输出设备', '未偵測到可用的音訊輸出裝置', 'No available audio output device'),
    'pc_live': ('拖动滑块即时调整，无需点击“保存设置”', '拖動滑桿即時調整，無需點擊「儲存設定」', 'Sliders apply immediately; no need to click Save settings'),
    'pc_guide': ('使用说明', '使用說明', 'How it works'),
    'pc_guide_display': ('显示器按连接情况自动识别，不按分辨率区分', '顯示器依連接情況自動辨識，不以解析度區分', 'Displays are detected automatically, regardless of resolution'),
    'pc_guide_ddc': ('外接屏需开启 DDC/CI；不支持的设备仍会显示，但不可调节', '外接螢幕需開啟 DDC/CI；不支援的裝置仍會顯示，但不可調節', 'External displays require DDC/CI. Unsupported displays remain listed'),
    'pc_guide_audio': ('音量与静音跟随 Windows 当前默认播放设备', '音量與靜音跟隨 Windows 目前預設播放裝置', 'Volume and mute control the current Windows playback device'),
    'pc_guide_cancel': ('这里的调整即时生效；关闭或取消设置不会还原音量和亮度', '此處調整即時生效；關閉或取消設定不會還原音量與亮度', 'Changes are immediate. Closing or cancelling settings does not undo them'),
    'pc_ready': ('设备状态已更新', '裝置狀態已更新', 'Device status updated'),
    'pc_applied': ('已调整', '已調整', 'Adjusted'),
    'pc_partial': ('部分显示器调节失败，请刷新设备后重试', '部分顯示器調節失敗，請重新偵測裝置後重試', 'Some displays could not be adjusted. Refresh and retry'),
    'pc_failed': ('调节失败，请检查设备连接后刷新', '調節失敗，請檢查裝置連接後重新偵測', 'Adjustment failed. Check connections and refresh'),
    'pc_detection_failed': ('设备检测失败，请点击刷新重试', '裝置偵測失敗，請重新偵測', 'Device detection failed. Refresh to retry'),
}
for key, values in _STRINGS.items():
    for lang, text in zip(('CHS', 'CHT', 'EN'), values):
        _TEXTS[lang][key] = text



# Keep the About identity independent from the public application title.
for lang, name, contact in (
    ('CHS', '定时关机工具', '联系方式'),
    ('CHT', '定時關機工具', '聯絡方式'),
    ('EN', 'Scheduled Shutdown Tool', 'Contact')):
    _TEXTS[lang].update(about_app_name=name, about_contact=contact)


_TEXTS['CHS']['group_datetime'] = '指定星期'
_TEXTS['CHT']['group_datetime'] = '指定星期'
_TEXTS['EN']['group_datetime'] = 'Weekday'
_TEXTS['CHS']['group_interval'] = '循环间隔'
_TEXTS['CHT']['group_interval'] = '循環間隔'
_TEXTS['EN']['group_interval'] = 'Repeat interval'
_TEXTS['CHS']['menu_queue'] = '任务管理'
_TEXTS['CHT']['menu_queue'] = '任務管理'
_TEXTS['EN']['menu_queue'] = 'Task manager'
_TEXTS['CHS']['center_title'] = '任务管理'
_TEXTS['CHT']['center_title'] = '任務管理'
_TEXTS['EN']['center_title'] = 'Task manager'
_TEXTS['CHS']['center_queue'] = '任务队列'
_TEXTS['CHT']['center_queue'] = '任務佇列'
_TEXTS['EN']['center_queue'] = 'Queue'
_TEXTS['CHS']['center_templates'] = '常用模板'
_TEXTS['CHT']['center_templates'] = '常用範本'
_TEXTS['EN']['center_templates'] = 'Templates'
_TEXTS['CHS']['center_advanced'] = '高级任务'
_TEXTS['CHT']['center_advanced'] = '進階任務'
_TEXTS['EN']['center_advanced'] = 'Advanced tasks'
_TEXTS['CHS']['center_hint'] = '队列、常用模板与高级任务，在一个窗口中管理'
_TEXTS['CHT']['center_hint'] = '佇列、常用範本與進階任務，在一個視窗中管理'
_TEXTS['EN']['center_hint'] = 'Manage the queue, templates and advanced tasks in one window'
_TEXTS['CHS']['center_open'] = '打开任务管理'
_TEXTS['CHT']['center_open'] = '開啟任務管理'
_TEXTS['EN']['center_open'] = 'Open task manager'
_TEXTS['CHS']['mode_guide'] = '时间方式说明'
_TEXTS['CHT']['mode_guide'] = '時間方式說明'
_TEXTS['EN']['mode_guide'] = 'Scheduling modes'
_TEXTS['CHS']['mode_guide_countdown'] = '倒计时：等待指定时长，只执行一次'
_TEXTS['CHT']['mode_guide_countdown'] = '倒數計時：等待指定時長，只執行一次'
_TEXTS['EN']['mode_guide_countdown'] = 'Countdown: wait for a duration, then run once'
_TEXTS['CHS']['mode_guide_weekday'] = '指定星期：到下一个选定星期的时刻，只执行一次'
_TEXTS['CHT']['mode_guide_weekday'] = '指定星期：到下一個選定星期的時刻，只執行一次'
_TEXTS['EN']['mode_guide_weekday'] = 'Weekday: run once at the next selected weekday and time'
_TEXTS['CHS']['mode_guide_interval'] = '循环间隔：每隔指定时长，重复执行'
_TEXTS['CHT']['mode_guide_interval'] = '循環間隔：每隔指定時長，重複執行'
_TEXTS['EN']['mode_guide_interval'] = 'Repeat interval: run repeatedly at the chosen interval'
_TEXTS['CHS']['mode_guide_calendar'] = '具体日期／重复预约：在高级任务中设置年月日、每天、工作日或周末'
_TEXTS['CHT']['mode_guide_calendar'] = '具體日期／重複預約：在進階任務中設定年月日、每天、平日或週末'
_TEXTS['EN']['mode_guide_calendar'] = 'Advanced tasks: choose a date or repeat daily, on weekdays or weekends'

_TEXTS['CHS']['about_contact_line']='联系方式：wenhao3843@gmail.com'
_TEXTS['CHT']['about_contact_line']='聯絡方式：wenhao3843@gmail.com'
_TEXTS['EN']['about_contact_line']='Contact: wenhao3843@gmail.com'


# v1.6.7 action and screen controls
_TEXTS['CHS'].update({'group_datetime': '定点执行', 'act_lock': '锁定电脑', 'act_hibernate': '休眠电脑', 'act_close_program': '关闭程序', 'pc_awake_title': '屏幕常亮', 'pc_awake_toggle': '防止电脑自动息屏', 'pc_awake_hint': '防止自动息屏和自动睡眠，收进托盘仍有效。关闭开关或退出工具后恢复系统策略；手动锁屏、睡眠与定时休眠照常执行。', 'pc_awake_save_error': '保存失败，已恢复原来的常亮状态', 'close_title': '选择要关闭的程序', 'close_running': '正在运行的程序', 'close_refresh': '刷新列表', 'close_browse': '选择 exe 文件', 'close_hint': '按完整exe路径强制结束所有实例及子进程。\n托盘或后台运行的进程也会结束。\n未保存内容可能丢失，请先保存。', 'close_choose': '请选择程序，或浏览 exe 文件', 'close_none': '没有可选窗口，可浏览 exe 文件', 'mode_guide_weekday': '定点执行：在下一次所选星期与时刻执行一次。'})
_TEXTS['CHT'].update({'group_datetime': '定點執行', 'act_lock': '鎖定電腦', 'act_hibernate': '休眠電腦', 'act_close_program': '關閉程式', 'pc_awake_title': '螢幕常亮', 'pc_awake_toggle': '防止電腦自動關閉螢幕', 'pc_awake_hint': '防止自動關閉螢幕和自動睡眠，縮至系統匣仍有效。關閉開關或退出工具後恢復系統策略；手動鎖定、睡眠與定時休眠照常執行。', 'pc_awake_save_error': '儲存失敗，已恢復原本的常亮狀態', 'close_title': '選擇要關閉的程式', 'close_running': '正在執行的程式', 'close_refresh': '重新整理', 'close_browse': '選擇 exe 檔案', 'close_hint': '依完整exe路徑強制結束所有執行個體及子程序。\n系統匣或背景執行的程序也會結束。\n未儲存內容可能遺失，請先儲存。', 'close_choose': '請選擇程式，或瀏覽 exe 檔案', 'close_none': '沒有可選視窗，可瀏覽 exe 檔案', 'mode_guide_weekday': '定點執行：在下一次所選星期與時刻執行一次。'})
_TEXTS['EN'].update({'group_datetime': 'At a set time', 'act_lock': 'Lock computer', 'act_hibernate': 'Hibernate', 'act_close_program': 'Close program', 'pc_awake_title': 'Keep screen on', 'pc_awake_toggle': 'Prevent automatic display off', 'pc_awake_hint': 'Prevents automatic display off and idle sleep, even in the tray. Turn off or exit to restore Windows policy. Manual lock, sleep and scheduled hibernation still work.', 'pc_awake_save_error': 'Save failed; previous display state restored', 'close_title': 'Choose program to close', 'close_running': 'Running programs', 'close_refresh': 'Refresh list', 'close_browse': 'Browse exe', 'close_hint': 'Force-ends all instances matching the full exe path and their child processes, including tray/background apps. Unsaved work may be lost; save first.', 'close_choose': 'Choose a program or browse its exe', 'close_none': 'No selectable windows; browse an exe', 'mode_guide_weekday': 'At a set time: run once at the next selected weekday and time.'})

class Texts(object):
    """文本访问器，缺省回退到简体中文。"""

    def __init__(self, lang="CHS"):
        self.set_language(lang)

    def set_language(self, lang):
        self.lang = "CHS"
        self._d = _TEXTS[self.lang]

    def __call__(self, key, **kw):
        """取文本，支持 {x} 占位符替换。"""
        s = self._d.get(key) or _TEXTS["CHS"].get(key) or key
        if kw:
            try:
                s = s.format(**kw)
            except Exception:
                pass
        return s

    def get(self, key, **kw):
        return self(key, **kw)

    def app_name(self):
        return self("app_name")


def language_desc(code, lang):
    """返回某语言文件“文件描述”列在当前界面语言下的写法。"""
    mapping = {"CHS": "col_chs", "CHT": "col_cht", "EN": "col_en"}
    return _TEXTS[lang if lang in _TEXTS else "CHS"].get(mapping.get(code, "col_chs"), code)


def language_file(code):
    for item in LANGUAGE_FILES:
        if item["code"] == code:
            return item["file"]
    return "CHS.ini"


def resource_path(rel):
    """兼容 PyInstaller 打包后的资源路径。"""
    import sys
    base = getattr(sys, "_MEIPASS", None)
    if base:
        p = os.path.join(base, rel)
        if os.path.exists(p):
            return p
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(here, rel)


def format_remain(seconds, T):
    """把秒格式化成 3 天 02:03:04 形式。"""
    seconds = max(0, int(seconds))
    d, rem = divmod(seconds, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    body = "%02d:%02d:%02d" % (h, m, s)
    if d > 0:
        return "%d %s %s" % (d, T("day_short"), body)
    return body


def weekday_names(lang):
    if lang == "EN":
        return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    if lang == "CHT":
        return ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    return ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

_TEXTS['CHS'].update({'mon_title': '系统监控', 'mon_cpu': 'CPU 使用率', 'mon_memory': '内存', 'mon_disk': '磁盘空间', 'mon_network': '网络速率', 'mon_uptime': '系统运行时长', 'mon_hint': '每秒刷新；磁盘显示已用空间，网络为全机收发速率。切换页面或关闭设置后停止采样，不保存监控历史。', 'float_title': '悬浮倒计时', 'float_enabled': '开启桌面悬浮倒计时', 'float_topmost': '保持悬浮窗置顶', 'float_opacity': '不透明度', 'float_hint': '拖动标题或时间可移动悬浮窗，位置自动记住。暂停／继续和取消只作用于当前计时；取消不会清空等待队列。无计时任务时显示就绪状态。', 'float_running': '正在计时 · 可拖动移动', 'float_paused': '已暂停 · 可继续', 'float_idle': '暂无计时任务', 'float_cancel': '取消当前任务', 'float_reset': '重置悬浮窗位置', 'float_apply_hint': '修改后点「保存设置」生效；关闭开关只隐藏悬浮窗，不会停止任务。'})

_TEXTS['CHT'].update({'mon_title': '系統監控', 'mon_cpu': 'CPU 使用率', 'mon_memory': '記憶體', 'mon_disk': '磁碟空間', 'mon_network': '網路速率', 'mon_uptime': '系統運行時長', 'mon_hint': '每秒更新；磁碟顯示已用空間，網路為全機收發速率。切換頁面或關閉設定後停止取樣，不保存監控歷史。', 'float_title': '浮動倒數計時', 'float_enabled': '開啟桌面浮動倒數計時', 'float_topmost': '保持浮動視窗置頂', 'float_opacity': '不透明度', 'float_hint': '拖動標題或時間可移動視窗，自動記住位置。暫停／繼續及取消只作用於目前計時；取消不清空等待佇列。沒有任務時顯示就緒。', 'float_running': '正在計時 · 可拖動移動', 'float_paused': '已暫停 · 可繼續', 'float_idle': '目前沒有計時任務', 'float_cancel': '取消目前任務', 'float_reset': '重設浮動視窗位置', 'float_apply_hint': '修改後按「儲存設定」生效；關閉開關只隱藏視窗，不停止任務。'})

_TEXTS['EN'].update({'mon_title': 'System monitor', 'mon_cpu': 'CPU usage', 'mon_memory': 'Memory', 'mon_disk': 'Disk space', 'mon_network': 'Network speed', 'mon_uptime': 'System uptime', 'mon_hint': 'Updates every second. Disk shows used space; network rates cover all adapters. Sampling stops when you leave this page or close Settings. No history is stored.', 'float_title': 'Floating countdown', 'float_enabled': 'Enable desktop countdown', 'float_topmost': 'Keep countdown on top', 'float_opacity': 'Opacity', 'float_hint': 'Drag the title or time to move; the position is saved. Pause/resume and cancel affect the current timer only. Cancel keeps the waiting queue. Idle state is shown when no timer is running.', 'float_running': 'Counting down · Drag to move', 'float_paused': 'Paused · Resume when ready', 'float_idle': 'No active timer', 'float_cancel': 'Cancel current task', 'float_reset': 'Reset window position', 'float_apply_hint': 'Click Save settings to apply changes. Disabling this window keeps the task running.'})

_TEXTS['CHS']['float_info']='使用说明'
_TEXTS['CHT']['float_info']='使用說明'
_TEXTS['EN']['float_info']='How it works'

_TEXTS['CHS'].update(float_hint='拖动空白或时间移动；双击可打开主窗口。暂停／继续、取消仅作用于当前任务，取消不清空队列。',float_ready='就绪',float_short_running='计时中',float_short_paused='已暂停')
_TEXTS['CHT'].update(float_hint='拖動空白或時間移動；雙擊開啟主視窗。暫停／繼續、取消只作用於目前任務，取消不清空佇列。',float_ready='就緒',float_short_running='計時中',float_short_paused='已暫停')
_TEXTS['EN'].update(float_hint='Drag to move. Double-click to open the main window. Pause/resume and cancel control the current timer; cancel keeps the queue.',float_ready='Ready',float_short_running='Counting',float_short_paused='Paused')

_TEXTS['CHS'].update(tray_floating='悬浮倒计时',float_save_error='悬浮窗设置保存失败，已保留原状态。')
_TEXTS['CHT'].update(tray_floating='浮動倒數計時',float_save_error='浮動視窗設定儲存失敗，已保留原狀態。')
_TEXTS['EN'].update(tray_floating='Floating countdown',float_save_error='Could not save the countdown setting. The previous state was kept.')

# v1.7.11: approved skin gallery replaces accent swatches.
_TEXTS['CHS'].update(skin_group='皮肤',skin_choose='选择喜欢的皮肤，再点「应用」；切换不会中断正在运行的计时。',skin_about='皮肤说明',skin_note='八款人物皮肤会同步设置背景与按钮配色。主页面保持原有布局，浅色卡片与清晰输入框让操作文字易于阅读。')
_TEXTS['CHT'].update(skin_group='外觀皮膚',skin_choose='選擇喜歡的皮膚，再按「套用」；切換不會中斷計時。',skin_about='皮膚說明',skin_note='八款人物皮膚同步設定背景與按鈕配色。主頁保持原有版面，淺色卡片與清晰輸入框讓文字易於閱讀。')
_TEXTS['EN'].update(skin_group='Skins',skin_choose='Choose a skin, then click Apply. Switching keeps the current timer running.',skin_about='About skins',skin_note='Eight character skins coordinate the wallpaper and controls. The existing layout is preserved; light cards and clear input fields keep text readable.')

_TEXTS['CHS'].update(skin_choose='选择「默认纯色」或「内置皮肤」，预览选中效果后点「应用」。',skin_note='默认纯色提供八种主题色与配色预览。内置皮肤提供八张原图，只在此模式显示。切换保留计时和任务；悬浮窗使用固定橙色与绿植配色。',skin_colors='主题色',skin_preview='配色预览',skin_normal_card='普通卡片',skin_selected_card='✓ 选中状态')
_TEXTS['CHT'].update(skin_choose='選擇「預設純色」或「內建皮膚」，預覽後按「套用」。',skin_note='純色提供八種主題色與預覽。八張內建原圖只在皮膚模式顯示。切換保留計時與任務；懸浮窗維持橙色與綠植配色。',skin_colors='主題色',skin_preview='配色預覽',skin_normal_card='一般卡片',skin_selected_card='✓ 選取狀態')
_TEXTS['EN'].update(skin_choose='Choose Solid colors or Built-in skins, preview your selection, then Apply.',skin_note='Solid mode offers eight colors and a palette preview. Eight artwork thumbnails appear only in Built-in skins. Timers and tasks are preserved; the floating countdown keeps its warm orange and green palette.',skin_colors='Theme colors',skin_preview='Palette preview',skin_normal_card='Normal card',skin_selected_card='✓ Selected')
