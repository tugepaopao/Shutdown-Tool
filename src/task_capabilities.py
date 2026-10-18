"""Cheap local prerequisites, checked at save/enable and again before dispatch."""
import ctypes
import os
import shutil

def hibernate_available():
    # SYSTEM_POWER_CAPABILITIES begins with 8 BOOLEAN fields; HiberFilePresent=7.
    data=(ctypes.c_ubyte*128)()
    api=ctypes.WinDLL('powrprof',use_last_error=True).GetPwrCapabilities
    api.argtypes=[ctypes.c_void_p];api.restype=ctypes.c_ubyte
    return bool(data[7]) if api(ctypes.byref(data)) else None

def validate(task):
    action=task.get('action');mode=task.get('mode')
    if action=='hibernate' and hibernate_available() is False:raise ValueError('本机未启用休眠，无法安排休眠任务。请先在 Windows 中启用休眠。')
    if action=='run_program':
        from actions import _split_cmd
        parts=_split_cmd(task.get('program_path',''))
        if not parts or not (os.path.isfile(parts[0]) or shutil.which(parts[0])):raise ValueError('目标程序或文件不存在，请重新选择执行路径。')
    if action=='close_program':
        from program_control import validate_target
        validate_target(task.get('close_program_path'))
    if action=='play_sound':
        from sound_library import resolve
        if not resolve(task.get('sound_file')):raise ValueError('音频文件不存在，请重新选择。')
    if mode=='download' and not os.path.isdir(task.get('folder','')):raise ValueError('监控目录不存在或暂不可用，请重新选择目录。')
    if mode=='chain' and not os.path.isfile(task.get('prepare_path','')):raise ValueError('前置程序不存在，请重新选择。')
