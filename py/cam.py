# cam.py
import cv2
import threading

_camera = None
_camera_lock = threading.Lock()
_last_frame = None
_running = False


def open_camera():
    global _camera, _running
    with _camera_lock:
        if _camera is None:
            _camera = cv2.VideoCapture(0)
            _running = True
            threading.Thread(target=_capture_loop, daemon=True).start()
    return _camera.isOpened()


def _capture_loop():
    global _camera, _last_frame, _running
    while _running and _camera and _camera.isOpened():
        ret, frame = _camera.read()
        if ret:
            _last_frame = frame
        else:
            break


def close_camera():
    global _camera, _running
    with _camera_lock:
        _running = False
        if _camera:
            _camera.release()
            _camera = None


def is_camera_open():
    global _camera
    return _camera is not None and _camera.isOpened()


def get_last_frame():
    global _last_frame
    return _last_frame


def take_photo():
    # 返回当前帧
    return get_last_frame()
