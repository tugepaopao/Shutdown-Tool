"""Windows hardware controls. DDC/CI and WMI brightness; Core Audio volume.
All native resources are scoped to an operation. Never alter gamma ramps.
"""
import base64
import contextlib
import ctypes as C
from ctypes import wintypes as W
from dataclasses import dataclass
import json
import math
import subprocess
import uuid


class ControlError(RuntimeError):
    pass


def percent(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError('Invalid percentage')
    return max(0, min(100, round(value)))


@dataclass(frozen=True)
class Monitor:
    key: str
    primary: bool
    value: object
    method: str = ''
    instance: str = ''
    low: int = 0
    high: int = 100


class Info(C.Structure):
    _fields_ = [('size', W.DWORD), ('rect', W.RECT), ('work', W.RECT),
                ('flags', W.DWORD), ('device', W.WCHAR * 32)]


class Device(C.Structure):
    _fields_ = [('size', W.DWORD), ('name', W.WCHAR * 32),
                ('description', W.WCHAR * 128), ('flags', W.DWORD),
                ('id', W.WCHAR * 128), ('key', W.WCHAR * 128)]


class Physical(C.Structure):
    _fields_ = [('handle', W.HANDLE), ('description', W.WCHAR * 128)]


class WindowsControls:
    def __init__(self):
        self.user = C.WinDLL('user32', use_last_error=True)
        self.ddc = C.WinDLL('dxva2', use_last_error=True)
        self.callback = C.WINFUNCTYPE(W.BOOL, W.HMONITOR, W.HDC, C.POINTER(W.RECT), W.LPARAM)
        self.user.EnumDisplayMonitors.argtypes = [W.HDC, C.POINTER(W.RECT), self.callback, W.LPARAM]
        self.user.GetMonitorInfoW.argtypes = [W.HMONITOR, C.POINTER(Info)]
        self.user.EnumDisplayDevicesW.argtypes = [W.LPCWSTR, W.DWORD, C.POINTER(Device), W.DWORD]
        for name, args in {
            'GetNumberOfPhysicalMonitorsFromHMONITOR': [W.HMONITOR, C.POINTER(W.DWORD)],
            'GetPhysicalMonitorsFromHMONITOR': [W.HMONITOR, W.DWORD, C.POINTER(Physical)],
            'DestroyPhysicalMonitors': [W.DWORD, C.POINTER(Physical)],
            'GetMonitorBrightness': [W.HANDLE, C.POINTER(W.DWORD), C.POINTER(W.DWORD), C.POINTER(W.DWORD)],
            'SetMonitorBrightness': [W.HANDLE, W.DWORD],
            'GetVCPFeatureAndVCPFeatureReply': [W.HANDLE, W.BYTE, C.POINTER(W.DWORD), C.POINTER(W.DWORD), C.POINTER(W.DWORD)],
            'SetVCPFeature': [W.HANDLE, W.BYTE, W.DWORD],
        }.items():
            fn = getattr(self.ddc, name)
            fn.argtypes = args
            fn.restype = W.BOOL

    def _logical(self):
        found = []
        def visit(handle, hdc, rect, data):
            info = Info(size=C.sizeof(Info))
            if self.user.GetMonitorInfoW(handle, C.byref(info)):
                device = Device(size=C.sizeof(Device))
                self.user.EnumDisplayDevicesW(info.device, 0, C.byref(device), 0)
                found.append((handle, str(info.device), bool(info.flags & 1), str(device.id)))
            return True
        callback = self.callback(visit)
        if not self.user.EnumDisplayMonitors(None, None, callback, 0):
            raise ControlError('display_detection_failed')
        return sorted(found, key=lambda item: (not item[2], item[1]))

    @contextlib.contextmanager
    def _physical(self, handle):
        count = W.DWORD()
        if not self.ddc.GetNumberOfPhysicalMonitorsFromHMONITOR(handle, C.byref(count)) or not count.value:
            yield []
            return
        array = (Physical * count.value)()
        if not self.ddc.GetPhysicalMonitorsFromHMONITOR(handle, count.value, array):
            yield []
            return
        try:
            yield array
        finally:
            self.ddc.DestroyPhysicalMonitors(count.value, array)

    @staticmethod
    def _powershell(script):
        encoded = base64.b64encode(script.encode('utf-16-le')).decode('ascii')
        result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded],
                                capture_output=True, timeout=12, creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode:
            raise ControlError('brightness_failed')
        return result.stdout.decode('utf-8-sig').strip()

    def _wmi(self):
        try:
            raw = self._powershell("[Console]::OutputEncoding=[Text.UTF8Encoding]::new(); "
                "$ErrorActionPreference='Stop'; @(Get-CimInstance -Namespace root/wmi -ClassName WmiMonitorBrightness | "
                "Where-Object Active | Select-Object InstanceName,CurrentBrightness) | ConvertTo-Json -Compress")
            data = json.loads(raw or '[]')
            return data if isinstance(data, list) else [data]
        except (OSError, subprocess.TimeoutExpired, ControlError, ValueError):
            return []

    def monitors(self):
        wmi = self._wmi()
        result = []
        for handle, name, primary, device_id in self._logical():
            matched = next((item for item in wmi if device_id and
                str(item['InstanceName']).rsplit('_', 1)[0].casefold() == device_id.casefold()), None)
            with self._physical(handle) as physical:
                for index in range(max(1, len(physical))):
                    key = f'{name}|{index}'
                    if matched:
                        result.append(Monitor(key, primary, percent(matched['CurrentBrightness']),
                                              'wmi', matched['InstanceName']))
                        continue
                    low, current, high = W.DWORD(), W.DWORD(), W.DWORD()
                    if physical and self.ddc.GetMonitorBrightness(physical[index].handle, C.byref(low), C.byref(current), C.byref(high)) and high.value > low.value:
                        result.append(Monitor(key, primary, percent((current.value-low.value)*100/(high.value-low.value)),
                                              'ddc', device_id, low.value, high.value))
                    elif physical and self.ddc.GetVCPFeatureAndVCPFeatureReply(physical[index].handle, 0x10, None, C.byref(current), C.byref(high)) and high.value > 0:
                        result.append(Monitor(key, primary, percent(current.value*100/high.value), 'vcp', device_id, 0, high.value))
                    else:
                        result.append(Monitor(key, primary, None))
        return result

    def set_brightness(self, monitor, value):
        level = percent(value)
        if monitor.method == 'wmi':
            instance = monitor.instance.replace("'", "''")
            raw = self._powershell("[Console]::OutputEncoding=[Text.UTF8Encoding]::new(); $ErrorActionPreference='Stop'; "
                "$m=Get-CimInstance -Namespace root/wmi -ClassName WmiMonitorBrightnessMethods | "
                f"Where-Object {{$_.InstanceName -eq '{instance}'}}; if (!$m) {{throw 'Disconnected'}}; "
                f"$r=Invoke-CimMethod -InputObject $m -MethodName WmiSetBrightness -Arguments @{{Timeout=[uint32]0;Brightness=[byte]{level}}}; "
                "if ($r.ReturnValue -ne 0) {throw 'Brightness failed'}; 'OK'")
            if raw != 'OK':
                raise ControlError('brightness_failed')
            return
        name, index_text = monitor.key.rsplit('|', 1)
        target = next((item for item in self._logical() if item[1] == name), None)
        if not target or (monitor.instance and target[3] != monitor.instance):
            raise ControlError('display_disconnected')
        with self._physical(target[0]) as physical:
            index = int(index_text)
            if index >= len(physical) or monitor.method not in ('ddc', 'vcp'):
                raise ControlError('brightness_unavailable')
            native = round(monitor.low + (monitor.high-monitor.low)*level/100)
            fn = self.ddc.SetMonitorBrightness if monitor.method == 'ddc' else self.ddc.SetVCPFeature
            args = (physical[index].handle, native) if monitor.method == 'ddc' else (physical[index].handle, 0x10, native)
            if not fn(*args):
                raise ControlError('brightness_failed')

    def audio(self):
        with endpoint() as volume:
            level, muted = C.c_float(), W.BOOL()
            call(volume, 9, [C.POINTER(C.c_float)], C.byref(level))
            call(volume, 15, [C.POINTER(W.BOOL)], C.byref(muted))
            return {'value': percent(level.value*100), 'muted': bool(muted.value)}

    def set_volume(self, value):
        with endpoint() as volume:
            call(volume, 7, [C.c_float, C.c_void_p], percent(value)/100, None)

    def set_mute(self, value):
        with endpoint() as volume:
            call(volume, 14, [W.BOOL, C.c_void_p], bool(value), None)


def guid(value):
    return (C.c_ubyte * 16).from_buffer_copy(uuid.UUID(value).bytes_le)


def call(ptr, index, types, *args):
    table = C.cast(ptr, C.POINTER(C.POINTER(C.c_void_p))).contents
    fn = C.WINFUNCTYPE(C.c_long, C.c_void_p, *types)(table[index])
    hr = fn(ptr, *args)
    if hr < 0:
        raise ControlError('audio_unavailable')
    return hr


@contextlib.contextmanager
def endpoint():
    ole = C.OleDLL('ole32')
    ole.CoInitializeEx.argtypes = [C.c_void_p, W.DWORD]
    ole.CoInitializeEx.restype = C.c_long
    ole.CoCreateInstance.argtypes = [C.c_void_p, C.c_void_p, W.DWORD, C.c_void_p, C.POINTER(C.c_void_p)]
    ole.CoCreateInstance.restype = C.c_long
    # A UI thread may already be STA. Do not uninitialize an existing apartment.
    initialized = ole.CoInitializeEx(None, 0) in (0, 1)
    enum, device, volume = C.c_void_p(), C.c_void_p(), C.c_void_p()
    try:
        hr = ole.CoCreateInstance(guid('BCDE0395-E52F-467C-8E3D-C4579291692E'), None, 1,
                                  guid('A95664D2-9614-4F35-A746-DE8DB63617E6'), C.byref(enum))
        if hr < 0:
            raise ControlError('audio_unavailable')
        call(enum, 4, [C.c_int, C.c_int, C.POINTER(C.c_void_p)], 0, 1, C.byref(device))
        call(device, 3, [C.c_void_p, W.DWORD, C.c_void_p, C.POINTER(C.c_void_p)],
             guid('5CDF2C82-841E-4546-9722-0CF74078229A'), 1, None, C.byref(volume))
        yield volume
    finally:
        for ptr in (volume, device, enum):
            if ptr.value:
                table = C.cast(ptr, C.POINTER(C.POINTER(C.c_void_p))).contents
                C.WINFUNCTYPE(W.ULONG, C.c_void_p)(table[2])(ptr)
        if initialized:
            ole.CoUninitialize()
