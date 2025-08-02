# cam.py (使用 Picamera2 替换 OpenCV)
import threading
from picamera2 import Picamera2
import numpy as np

_camera = None
_camera_lock = threading.Lock()
_last_frame = None
_running = False


def open_camera():
    global _camera, _running
    with _camera_lock:
        if _camera is None:
            _camera = Picamera2()
            # 配置预览流
            preview_config = _camera.create_preview_configuration(
                main={"format": "RGB888"}
            )
            _camera.configure(preview_config)
            _camera.start()
            _running = True
            threading.Thread(target=_capture_loop, daemon=True).start()
    return _camera is not None


def _capture_loop():
    global _camera, _last_frame, _running
    while _running and _camera:
        # Picamera2的capture_array()是阻塞的, 但速度较快
        try:
            frame = _camera.capture_array()
            _last_frame = frame
        except Exception as e:
            print("Camera error:", e)
            break


def close_camera():
    global _camera, _running
    with _camera_lock:
        _running = False
        if _camera:
            _camera.stop()
            _camera.close()
            _camera = None


def is_camera_open():
    global _camera
    return _camera is not None


def get_last_frame():
    global _last_frame
    return _last_frame


def take_photo():
    # 返回当前帧
    return get_last_frame()
