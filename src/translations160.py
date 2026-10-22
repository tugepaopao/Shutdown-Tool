"""v1.6界面文案；原控件本地化使用同一份映射。"""
EN={
 '你修改的设置还没有保存\n保存后即可在下次启动时继续使用':'Your changes have not been saved\nSave them to keep your settings for next time',
 '保存并关闭':'Save and close','保留当前设置':'Keep current settings','先保存':'Save first',
 '你修改的设置还没有保存\n恢复备份前，可以先保存这次修改':'Your changes have not been saved\nYou can save them before restoring the backup',
 '恢复上次定时':'Restore previous timer','上次的任务还没有完成\n可以继续计时，也可以先恢复为暂停状态':'Your previous timer is unfinished\nContinue the timer or restore it paused',
 '今日跳过':'Skipped today','等待条件':'Waiting','确认中':'Confirming','等待空闲':'Awaiting idle','前置运行':'Preparing','已过期':'Expired','已错过':'Missed','已入队':'Queued','已超时':'Timed out','监控失败':'Monitor failed','入队失败':'Queue failed','保存失败':'Save failed','需重启用':'Re-enable',
 '已过期，未补执行':'Expired; not executed','已错过，未执行':'Missed; not executed','已加入队列':'Added to queue','加入队列失败，未执行':'Could not add to queue; not executed','预约保存失败，未执行':'Schedule could not be saved; not executed','监控结果保存失败，未执行':'Monitoring result could not be saved; not executed','重开后需重新启用任务链':'Re-enable the task chain after restarting',
 '自动保留最近10份正常配置\n计时状态变化不会反复生成备份':'Keep the last 10 good configurations\nTimer updates do not create extra backups',
 '备份范围':'Backup contents',
 '包含：常用设置、命名模板、高级任务定义':'Included: settings, named templates and advanced task definitions',
 '不包含：运行中的定时、队列、自启动项':'Excluded: active timer, queue and startup entry',
 **{str(n)+'天后':'In '+str(n)+' days' for n in range(3,8)},
 '自动化与预览':'Automation & preview','快捷键与通知':'Hotkeys & notifications','备份与恢复':'Backup & recovery',
 '恢复上一次正常配置':'Restore previous good settings','查看自动备份':'View automatic backups',
 '自动备份最近10份正常配置；计时状态变化不会反复生成备份。':'Keep the last 10 good configurations. Timer updates do not create extra backups.',
 '配置损坏时自动尝试恢复；手动恢复前会显示预览。':'Try recovery automatically if settings are damaged. Manual recovery shows a preview first.',
 '恢复不替换运行中计时、当前队列和自启动项；高级任务保持停用。':'Recovery preserves the active timer, queue and startup setting. Restored advanced tasks stay disabled.',
 '删除后撤销':'Undo deletion','撤销上一次删除':'Undo last deletion','删除的队列任务或模板可在5分钟内撤销，最多保留20次；退出后清除。':'Undo queue or template deletions within 5 minutes (up to 20). History clears on exit.',
 '恢复的任务不会自动开始。':'Restored tasks do not start automatically.',
 '已撤销删除':'Deletion undone','没有可撤销的删除（保留5分钟，退出后清除）':'Nothing to undo (5-minute history; cleared on exit).',
 '今天跳过一次':'Skip today','未来7天任务预览':'Next 7 days','管理预约、条件与任务链':'Schedules, conditions & task chains',
 '同一分钟重叠；按队列执行':'Same minute; runs in queue order','时间明确的预约显示在下表；条件任务和任务链不预测完成时刻。':'Dated schedules appear below. Conditions and chains have no predictable finish time.',
 '只显示已启用任务；工作日指周一至周五，不调整法定节假日。':'Enabled tasks only. Weekdays mean Mon–Fri, without holiday adjustments.',
 '刷新预览':'Refresh preview','日期':'Date','时刻':'Time','任务名称':'Task name','提示':'Note',
 '暂无预约':'No bookings',
 '没有未来7天内的预约':'No enabled schedules in the next 7 days',
 '网络安静且无人操作':'Quiet network AND user idle','程序成功后执行':'After a program succeeds',
 '无人操作（分钟）':'User idle (minutes)','前置程序（exe）':'First program (.exe)','前置程序参数':'Program arguments',
 '组合条件须先观察到网络活动，再同时满足安静和无人操作时长。':'Combined conditions require observed traffic, then both quiet traffic and user inactivity.',
 '任务链只在退出码为0时执行后续动作；超时或取消不关闭前置程序。':'Chains continue only after exit code 0. Timeout or cancellation leaves the first program running.',
 '任务链重开程序后不会自动运行，需手动重新启用。':'Chains never restart automatically after reopening this app. Enable them again manually.',
 '请选择已启用的重复预约':'Select an enabled recurring schedule.',
 '等待无人操作':'Waiting for user inactivity','前置程序运行中':'First program running','重开后需重新启用任务链':'Re-enable the chain after reopening',
 '等待活动':'Waiting for activity','传输中':'Transferring','确认安静中':'Confirming quiet traffic',
 '已完成，加入队列':'Completed; added to queue','等待超时，未执行':'Timed out; no action','监控失败，未执行':'Monitoring failed; no action',
 '全局快捷键':'Global hotkeys','启用全局快捷键':'Enable global hotkeys','唤出主窗口':'Show main window','暂停当前定时':'Pause current timer','继续当前定时':'Resume current timer',
 '支持Ctrl、Alt、Shift加字母／数字／F1～F12；快捷键冲突会提示，不会覆盖其他程序。':'Use Ctrl, Alt or Shift plus a letter, digit or F1–F12. Conflicts are reported; other apps keep their shortcuts.',
 'Windows桌面通知':'Windows notifications','启用桌面通知':'Enable desktop notifications','任务已设置':'Task scheduled','任务已完成':'Task completed','任务失败':'Task failed','发送测试通知':'Send test notification',
 '通知跟随Windows通知设置；专注助手或系统禁用通知时可能不弹出。':'Windows controls delivery. Focus Assist or disabled system notifications may hide notifications.',
 '这是一条测试通知。':'This is a test notification.','通知已提交给Windows':'Notification sent to Windows','托盘不可用，无法发送通知':'The tray is unavailable; cannot send a notification.',
 '前五个预设固定；最后一项可选择今天、明天、后天或最多7天后。':'The first five presets are fixed. The last can target today or up to 7 days from today.',
 '第6个按钮的日期':'Preset 6 day','第6个按钮的时间':'Preset 6 time','今天':'Today','明天':'Tomorrow','后天':'In 2 days',
 '今天的时间已过去，请在设置中选择其他日期或更晚的时间。':'That time has passed today. Choose a later time or another day in Settings.',
 '网络流量':'Network traffic','设置已保存，但自动备份失败：':'Settings saved, but automatic backup failed: ','剩余':'Remaining','就绪':'Ready','正在计时':'Counting down','已暂停':'Paused','预计':'Due','后执行':'until action',
 '允许强制关闭应用（关机／重启／注销）':'Force applications to close (shutdown / restart / logoff)',
 '安静阈值（KB/s，收发总和）':'Quiet threshold (KiB/s, total)','连续安静（秒）':'Quiet duration (seconds)',
 '(时:分)':'(HH:MM)','保存模板':'Save template','模板名称：':'Template name:',
 '删除任务':'Delete task','操作未完成':'Operation incomplete','任务设置有误':'Invalid task settings',
 '名称有误':'Invalid name','名称不能为空或重复。':'Names cannot be empty or duplicated.',
 '先停用任务':'Disable this task first','请先停用该任务，再编辑。':'Disable this task before editing.',
 '无法启用':'Cannot enable','导出完成':'Export complete','导出失败':'Export failed','导入完成':'Import complete','导入失败':'Import failed','导入预览':'Import preview',
 '设置、模板和高级任务已保存。运行中定时、队列和开机自启动不包含在备份内。':'Settings, templates and advanced tasks were saved. The active timer, queue and startup entry are excluded.',
 '没有运行中的定时':'No active timer','请先开始一个定时任务。':'Start a timer first.',
 '请只选择一个任务。':'Select exactly one task.','不能编辑':'Cannot edit','复制失败':'Copy failed','排序失败':'Cannot reorder',
 '保存失败':'Save failed','模板保存失败':'Failed to save templates','队列保存失败':'Failed to save queue',
 '配置保存失败，原设置已保留。':'Settings could not be saved. Previous settings were preserved.',
 '备份时间':'Backup time','模板数':'Templates','高级任务数':'Advanced tasks','恢复选中备份':'Restore selected backup',
 '暂无自动备份':'No automatic backups',
 '暂无自动备份；下一次保存正常配置后会自动建立。':'No automatic backups yet. Saving valid settings creates a backup.',
 '请选择一个备份':'Select a backup','确认恢复':'Confirm recovery','恢复完成':'Recovery complete',
 '刷新':'Refresh','关闭':'Close','正常':'OK',
}
EN.update({
 '任务链使用说明':'Using task chains',
 '先观察到网络活动\n再同时满足网络安静与无人操作时长':'Observe network activity first\nThen wait for both network quiet and user inactivity',
 '只显示已启用的预约，含今天共7天\n工作日按周一至周五计算，不调整节假日':'Enabled schedules only; seven days including today\nWorkdays mean Mon–Fri, without holiday adjustments',
 '成功后执行：前置程序退出码为0才继续':'On success: continue only when the program exits with code 0',
 '超时或取消：不关闭正在运行的前置程序':'On timeout or cancellation: leave the program running',
 '重新打开工具：任务链需手动重新启用':'After reopening: enable the task chain manually',
})
# 新增文案及旧功能的常用繁体字，已有核心文案仍优先使用i18n的完整翻译。
CHARS=str.maketrans({'设':'設','置':'置','备':'備','份':'份','复':'復','恢':'恢','删':'刪','销':'銷','队':'隊','列':'列','务':'務','暂':'暫','继':'繼','续':'續','启':'啟','动':'動','后':'後','开':'開','关':'關','闭':'閉','时':'時','间':'間','网':'網','络':'絡','条':'條','链':'鏈','预':'預','览':'覽','显':'顯','执':'執','并':'並','个':'個','钟':'鐘','择':'擇','选':'選','换':'換','输':'輸','入':'入','错':'錯','误':'誤','为':'為','认':'認','写':'寫','说':'說','导':'匯','录':'錄','声':'聲','图':'圖','体':'體','读':'讀','数':'數','标':'標','准':'準','当':'當','损':'損','坏':'壞','储':'儲','存':'存','档':'檔','温':'溫','览':'覽','优':'優','话':'話','键':'鍵','冲':'衝','突':'突','会':'會','这':'這','从':'從','处':'處','级':'級','仅':'僅','与':'與','发':'發','现':'現','实':'實','态':'態','阶':'階','段':'段','过':'過','长':'長','达':'達','还':'還','静':'靜','无':'無','监':'監','测':'測','检':'檢','传':'傳','满':'滿','功':'功','败':'敗','码':'碼','权':'權','限':'限','径':'徑','请':'請','让':'讓','里':'裡','弹':'彈','将':'將','单':'單','屏':'螢','应':'應','导':'匯','称':'稱','称':'稱','查':'查','询':'詢','约':'約','软':'軟','线':'線','简':'簡','阅':'閱','须':'須','盘':'盤','气':'氣','节':'節','假':'假','调':'調','整':'整','总':'總','变':'變','败':'敗','够':'夠','内':'內','触':'觸','达':'達','维':'維','护':'護','围':'圍','够':'夠','断':'斷','议':'議','导':'匯','报':'報','来':'來','误':'誤'})

def feature(T,text):
    lang=getattr(T,'lang','CHS')
    if lang=='CHS':return text
    if lang=='CHT':return text.translate(CHARS)
    from i18n import FEATURE_EN
    if text in EN:return EN[text]
    if text in FEATURE_EN:return FEATURE_EN[text]
    if text.startswith('预约已错过：'):return 'Missed schedule: '+text.split('：',1)[1]
    if text.startswith('高级任务未能加入队列：'):return 'Could not queue advanced task: '+text.split('：',1)[1]
    if text.startswith('快捷键已被其他程序占用：'):return 'Shortcut is already in use: '+text.split('：',1)[1]
    if text.startswith('延后') and text.endswith('分钟'):return 'Postpone '+text[2:-2]+' min'
    if text.endswith('天后') and text[:-2].isdigit():return 'In '+text[:-2]+' days'
    if text.startswith('等待 '):return 'Waiting '+text[3:]
    if text.startswith('今天已跳过；下次 '):return 'Skipped today; next '+text[len('今天已跳过；下次 '):]
    if text.startswith('删除「') and text.endswith('」？'):return 'Delete “'+text[3:-2]+'”?'
    return text

EN.update({'指定星期（单次）':'Selected weekday (once)','循环间隔':'Repeat interval','具体日期／重复预约':'Specific date / repeating schedule','具体日期与重复预约在这里设置；保存后需手动启用。':'Set specific dates and recurring schedules here. Enable tasks after saving.'})

EN.update({'定点执行（单次）': 'At a set time (once)', '请选择要关闭的程序 exe 文件': 'Select the exe of the program to close', '不能选择本工具或系统关键程序': 'This tool and critical system programs cannot be selected', '目标程序没有可关闭的窗口，请确认程序正在运行': 'No closeable window found; check that the program is running', '程序仍在运行，可能正在等待保存、取消退出或收进托盘': 'Program is still running; it may be waiting to save, have cancelled exit or be in the tray', '关闭请求被系统拒绝，请检查目标程序权限': 'Close request denied; check target permissions', '无法访问目标程序，请检查权限': 'Cannot access the target program; check permissions', '旧版关闭显示器任务已停用，请选择其他操作': 'Legacy display-off tasks are disabled; select another action'})

EN.update({'目标程序当前没有运行': 'The target program is not running', '部分进程无法结束，请以管理员身份运行本工具后重试': 'Some processes could not be ended; run this tool as administrator and retry', '已跳过系统关键进程或本工具，未全部结束': 'Protected system or tool processes were skipped; not all processes ended', '程序仍有进程运行或被其他软件重新启动，请重试': 'Some processes remain or another program restarted the app; retry'})

EN.update({
'通用与启动':'General & startup','提醒与通知':'Reminders & notifications','界面与悬浮':'Interface & floating','任务与预设':'Tasks & presets','备份与诊断':'Backup & diagnostics',
'保存设置':'Save settings','放弃更改':'Discard changes','已保存':'Saved','已修改 {n} 项':'{n} changes unsaved','保存后生效':'Apply after saving','立即生效':'Apply immediately',
'开启':'On','窗口行为':'Window behavior','最小化：回到任务栏':'Minimize: keep in taskbar','关闭主窗口时隐藏到托盘':'Hide to tray when closing the main window','按 Esc 最小化到任务栏':'Esc minimizes to taskbar',
'启动与恢复':'Startup & recovery','重开后的定时恢复':'Timer recovery on reopening','询问恢复':'Ask before restoring','恢复为暂停':'Restore paused','直接继续':'Continue timer','不恢复':'Do not restore','操作确认':'Action confirmation',
'语言':'Language','显示语言':'Display language','简体中文':'Simplified Chinese','繁體中文':'Traditional Chinese','语言信息':'Language details','全局快捷键':'Global shortcuts','启用全局快捷键':'Enable global shortcuts','唤出主窗口':'Show main window','暂停当前定时':'Pause current timer','继续当前定时':'Resume current timer',
'支持 Ctrl、Alt、Shift + 字母／数字／F1～F12':'Use Ctrl, Alt, Shift + letters / digits / F1–F12','执行前提醒':'Before-action reminder','提前提醒不改变任务执行时刻。':'Reminders do not change the execution time.','提前提醒':'Remind in advance','10 秒':'10 seconds','30 秒':'30 seconds','60 秒':'60 seconds','可取消提醒':'Cancellable notice','提示音':'Warning sound','显示主窗口':'Show main window',
'Windows 通知':'Windows notifications','按 Windows 通知设置显示。':'Follows Windows notification settings.','任务已设置':'Task scheduled','任务已完成':'Task completed','任务失败':'Task failed','消息与预览':'Message & preview','消息停留时长':'Message duration','预览提醒':'Preview reminder','测试通知':'Test notification','使用说明':'Instructions',
'拖动滑块立即生效；放弃更改不会撤销硬件调整。':'Sliders apply immediately; discarding changes does not undo hardware adjustments.',
'六个位置，可按习惯设置':'Six customizable slots','第{n}项':'Slot {n}','分钟':'minutes','请输入有效时长或 HH:MM 时间':'Enter a valid duration or HH:MM time','修改后只影响快捷入口；右键可排序或恢复默认。':'Only changes quick actions. Right-click to reorder or reset.','任务中心':'Task center','队列 {q} 项 · 模板 {t} 个 · 高级任务 {a} 项':'Queue {q} · Templates {t} · Advanced {a}','打开任务中心':'Open task center','未来7天预览 →':'Next 7 days →','时间方式说明':'Scheduling modes','前移':'Move earlier','后移':'Move later','恢复默认':'Reset defaults',
'导入与导出':'Import & export','执行日志与诊断':'Logs & diagnostics','复制诊断概要':'Copy diagnostics','默认不包含消息内容和个人文件路径。':'Message text and personal file paths are excluded.','诊断概要已复制':'Diagnostics copied','提醒预览':'Reminder preview','这是预览，不会执行操作或改变当前计时。':'Preview only. No action is performed and your timer stays unchanged.',
'保存更改？':'Save changes?','是：保存；否：放弃；取消：继续编辑。':'Save, discard or keep editing.','放弃':'Discard','继续编辑':'Keep editing','恢复上次定时？':'Restore the previous timer?','继续上次未完成的定时，或先暂停后再决定。':'Continue the unfinished timer, or restore it paused.','继续计时':'Continue timer',
'上方修改的是下次设定，当前任务保持不变。':'The controls edit the next setup. The active task stays unchanged.','右键可延后任务或查看队列。':'Right-click to postpone or view the queue.','置顶主窗口':'Keep main window on top','最小化到任务栏':'Minimize to taskbar','关闭主窗口':'Close main window','停止当前任务':'Stop current task','暂停／继续当前任务':'Pause / resume current task','点击编辑：':'Click to edit: ',
'恢复预览':'Restore preview','选择恢复范围；运行中计时、当前队列与自启动项保留。':'Choose what to restore. Active timer, queue and startup entry are preserved.','常用设置':'Settings','常用模板':'Templates','设置项':'Setting','当前':'Current','备份':'Backup','恢复的高级任务保持停用；仅恢复模板不会修改其他设置。':'Restored advanced tasks stay disabled. Templates-only restore preserves settings.','请选择恢复范围':'Choose what to restore','恢复前先保存或放弃当前设置草稿。':'Save or discard your settings draft before restoring.'
})

EN.update({'今天':'Today','明天':'Tomorrow','后天':'In 2 days','修改后只影响快捷入口；右键可更改方式、排序或恢复默认。':'Only changes quick actions. Right-click for type, ordering or reset.'})

EN.update({'电脑快控':'PC controls','队列':'Queue','六格快捷预设':'Six quick presets','恢复未完成定时':'Restore unfinished timer','Esc 最小化':'Esc minimize','提醒提前量':'Reminder lead time','任务已设置通知':'Task scheduled notification','任务已完成通知':'Task completed notification','任务失败通知':'Task failed notification','开机启动设置失败，原设置已保留。':'Startup setting failed. Previous settings are preserved.','配置保存失败，原设置已保留。':'Saving failed. Previous settings are preserved.','保存失败，原设置已保留':'Saving failed. Previous settings are preserved','恢复范围无效':'Invalid restore selection','数值超出允许范围':'Value is out of range','提醒提前量无效':'Invalid reminder lead time','恢复方式无效':'Invalid recovery policy','恢复为暂停':'Restore paused'})

EN.update({'不透明度可调范围：40%～100%。保存设置后生效。':'Opacity range: 40%–100%. Applies after saving settings.'})

EN.update({'已修改':'Modified','未修改':'No changes','修改后需保存才会生效':'Save changes to apply them','亮度与音量调整立即生效':'Brightness & volume: live','其他设置已修改，需保存生效':'Save other settings to apply','开启／关闭悬浮倒计时':'Toggle floating countdown'})

EN.update({'悬浮倒计时快捷键':'Floating countdown shortcut'})

EN.update({'选择界面语言，保存后应用。': 'Choose a display language; save to apply.', '点击组合键框后，直接按下新的快捷键': 'Click a shortcut, then press the new key combination.', '恢复默认快捷键': 'Restore default shortcuts', '修改明细': 'Changes', '暂无快捷键修改': 'No shortcut changes', '已注册': 'Registered', '待保存': 'Unsaved', '被占用': 'In use', '格式无效': 'Invalid format', '重复快捷键': 'Duplicate', '未启用': 'Disabled', '当前任务': 'Current task', '当前没有正在运行的任务': 'No active task', '等待队列 · 前一项完成后自动开始下一项': 'Waiting queue · Starts after the previous task completes', '前一项完成后': 'After previous task:', '顺序': 'Order', '任务': 'Task', '执行条件': 'Trigger', '操作': 'Actions', '更多操作': 'More actions', '把当前设定加入队列': 'Add current setup to queue', '选中 {n} 项': '{n} selected', '复制任务': 'Copy task', '队列为空，将当前设定加入队列即可开始': 'Queue is empty. Add the current setup to begin.', '快捷键至少包含Ctrl或Alt': 'Include Ctrl or Alt in the shortcut.', '快捷键注册线程无响应': 'Shortcut service did not respond.'})

EN.update({'自动保留最近10份正常配置':'Keeps the 10 most recent valid configurations','执行日志':'Execution log'})

EN.update({'剩余 {t}':'Remaining {t}'})

EN.update({'快捷键格式：Ctrl+Alt+H（字母、数字或F1～F12）':'Shortcut format: Ctrl+Alt+H (letters, digits or F1–F12)','快捷键修饰键有误或重复':'Invalid or repeated shortcut modifier','不同操作不能使用相同快捷键':'Each action needs a different shortcut'})

EN.update({'删除选中':'Delete selected','清空队列':'Clear queue'})

EN.update({'快捷预设':'Quick presets'})

EN.update({'我的模板':'My templates','下次执行':'Next run','新建任务':'New task',
    '常用':'Favorite','普通':'Standard','重复':'Repeat','尚未启用':'Not enabled',
    '暂无已启用任务':'No enabled tasks','条件满足后执行':'When conditions are met',
    '条件任务（单次）':'Conditional task (once)','新建任务后手动启用':'Create a task, then enable it',
    '保存常用设定，一键加入队列':'Save setups and add them to the queue',
    '暂无高级任务，点击“新建任务”开始':'No tasks yet. Select New task to begin.',
    '暂无模板，可保存主页面当前设定':'No templates yet. Save your current setup.',
    '收藏状态必须是布尔值':'Favorite must be true or false'})
EN.update({'{n} 分钟':'{n} min','{n} 秒':'{n} sec','倒计时 {t}':'In {t}','每 {t} 循环':'Every {t}'})
CHARS.update(str.maketrans({'诊':'診','异':'異','补':'補','结':'結','询':'詢','择':'擇'}))
EN.update({
 '搜索名称':'Search name','等待中':'Waiting','需处理':'Attention','收藏':'Favorites','没有匹配的任务':'No matching tasks',
 '重新启用':'Re-enable','打开日志':'Open log','每周':'Weekly','自定义':'Custom','待确认':'Needs confirmation','待补执行':'Pending recovery',
 '错过待确认':'Missed; awaiting confirmation','等待补执行':'Waiting to recover one missed run','已结束':'Ended','已到结束日期':'The end date has been reached',
 '编辑高级任务':'Edit advanced task','保存后需手动启用':'Enable after saving','保存任务':'Save task','执行时间':'Time',
 '例外日期':'Exception dates','＋ 添加日期':'+ Add date','这些日期将跳过执行':'These dates will be skipped','错过执行处理':'Missed runs',
 '跳过，不补执行':'Skip missed runs','下次启动后询问':'Ask after reopening','启动后执行一次':'Run once after reopening','补执行仍保留10秒取消时间':'Recovered runs still allow 10 seconds to cancel',
 '请输入 YYYY-MM-DD 日期，最多366个':'Enter YYYY-MM-DD dates, up to 366','请至少选择一个星期':'Select at least one weekday',
 '例外日期最多366个':'Up to 366 exception dates are allowed','日期格式应为 YYYY-MM-DD':'Use YYYY-MM-DD for dates',
 '结束日期不能早于开始日期':'End date must not be before start date','错过处理方式无效':'Invalid missed-run policy',
 '错过的预约':'Missed schedule','任务“{name}”错过了 {at}。是否补执行一次？加入队列后保留10秒取消时间。':'“{name}” missed {at}. Run it once now? You will have 10 seconds to cancel after it enters the queue.',
 '运行状态':'Runtime status','任务调度':'Task scheduler','正常':'Healthy','未运行':'Not running','运行中':'Running','已开启':'On','已关闭':'Off',
 '刷新状态':'Refresh status','最近异常':'Recent issues','最近7天，仅打开页面或手动刷新时更新':'Last 7 days. Updated on opening this page or manual refresh.',
 '诊断与恢复':'Diagnostics & recovery','复制诊断':'Copy diagnostics','导出备份':'Export backup','导入备份':'Import backup',
 '最近7天暂无异常记录':'No recorded issues in the last 7 days','更多记录可在执行日志中查看':'See the execution log for more records',
 '日志记录已关闭，仅显示已有记录':'Logging is off; showing existing records only',
})
