"""本地流式音频播放，不依赖系统MP3的MCI关联或外部播放器。"""
import threading,time
_lock=threading.RLock()
_current=None

def stop():
    global _current
    with _lock:
        current=_current;_current=None
        if current:
            device,stream=current
            device.close()
            stream.close()

def play(path):
    global _current
    import miniaudio
    with _lock:
        stop();stream=None;device=None
        try:
            stream=miniaudio.stream_file(path)
            device=miniaudio.PlaybackDevice(backends=[miniaudio.Backend.WASAPI,miniaudio.Backend.DSOUND,miniaudio.Backend.WINMM])
            device.start(stream);_current=(device,stream)
        except Exception:
            if device:device.close()
            if stream:stream.close()
            raise
    def release_when_finished():
        while True:
            time.sleep(.2)
            with _lock:
                if _current is None or _current[0] is not device:return
                if device.callback_generator is None:stop();return
    threading.Thread(target=release_when_finished,daemon=True,name='HaozaiziAudioCleanup').start()
    return device.backend
