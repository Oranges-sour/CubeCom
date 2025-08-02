import flet as ft
import threading
import queue
import cv2
import numpy as np
import base64
import time

DEBUG = True

WIDTH, HEIGHT = 480, 640

BG_COLOR = "#ebebeb"
MSG_COLOR = "#111611"
ALERT_COLOR = "#ff6464"
FONT_SIZE = 14
LINE_HEIGHT = 22
PADDING = 20
MAX_LINES = (HEIGHT - PADDING * 2) // LINE_HEIGHT

FONT_FAMILY = "font"
FONT_PATH = "font.ttf"

URL_A = "https://api.creativone.cn/"
URL_B = "https://api.creativone.cn/"
URL_D = "https://api.creativone.cn/"


WELCOME_BG_PATH = "bk1.png"  # 替换为实际欢迎背景图片路径
MAIN_BG_PATH = "bk2.png"  # 替换为实际主界面背景图片路径


_event_queue = queue.Queue()
_lines = []
_gui_running = False
_page = None
_text_column = None

_preview_running = False
_preview_thread = None
_img_control = None
_page = None

# 放到函数外，供更新线程访问
_time_text = None

_page_mode = "welcome"

_main_container = None  # C模式
_a_container = None  # A模式
_b_container = None  # B模式
_start_controls = None  # 开始界面


def _show_welcome_page():
    global _page, _time_text

    def enter_main(e):
        global _page_mode
        _page_mode = "start"
        _update_page_visibility()

    # 显示时间的控件
    _time_text = ft.Text(
        value=time.strftime("%H:%M"),
        size=74,
        color="#ffffff",
        weight=ft.FontWeight.BOLD,
    )

    # 透明按钮用于点击进入
    invisible_button = ft.GestureDetector(
        on_tap=enter_main,
        content=ft.Container(
            width=143,
            height=HEIGHT,
            opacity=0.01,
            bgcolor=ALERT_COLOR,
        ),
        left=338,
        top=0,
    )

    welcome = ft.Container(
        content=ft.Stack(
            [
                ft.Image(
                    src=WELCOME_BG_PATH,
                    width=WIDTH,
                    height=HEIGHT,
                    fit=ft.ImageFit.FILL,
                ),
                invisible_button,
                ft.Container(  # 时间显示位置
                    content=_time_text,
                    left=44,
                    top=156,
                ),
            ]
        ),
        width=WIDTH,
        height=HEIGHT,
        expand=False,
        bgcolor=None,
    )
    _page.controls.clear()
    _page.add(welcome)
    _page.update()


def _time_updater():
    global _gui_running, _time_text, _page
    while _gui_running:
        if _time_text and _page:
            _time_text.value = time.strftime("%H:%M")
            _page.update()
        time.sleep(1)


def _show_start_page():
    global _start_controls, _page

    def on_a(e):
        global _page_mode
        _page_mode = "A"
        _update_page_visibility()

    def on_b(e):
        global _page_mode
        _page_mode = "B"
        _update_page_visibility()

    def on_c(e):
        global _page_mode
        _page_mode = "C"
        _update_page_visibility()

    def on_d(e):
        global _page_mode
        _page_mode = "D"
        _update_page_visibility()

    def on_back(e):
        global _page_mode
        _page_mode = "welcome"
        _update_page_visibility()

    # 虚拟按钮，设置透明背景和指定区域
    virtual_buttons = [
        ft.GestureDetector(  # 按钮 A
            on_tap=on_a,
            content=ft.Container(
                width=400, height=130, opacity=0.01, bgcolor=ALERT_COLOR
            ),
            left=113,
            top=5,
        ),
        ft.GestureDetector(  # 按钮 B
            on_tap=on_b,
            content=ft.Container(
                width=400, height=130, opacity=0.01, bgcolor=ALERT_COLOR
            ),
            left=113,
            top=160,
        ),
        ft.GestureDetector(  # 按钮 C
            on_tap=on_c,
            content=ft.Container(
                width=400, height=130, opacity=0.01, bgcolor=ALERT_COLOR
            ),
            left=113,
            top=300,
        ),
        ft.GestureDetector(  # 预留按钮 D
            on_tap=on_d,
            content=ft.Container(
                width=400, height=130, opacity=0.01, bgcolor=ALERT_COLOR
            ),
            left=113,
            top=450,
        ),
        ft.GestureDetector(  # 返回欢迎界面按钮
            on_tap=on_back,
            content=ft.Container(
                width=100, height=640, opacity=0.01, bgcolor=ALERT_COLOR
            ),
            left=0,
            top=0,
        ),
    ]

    _start_controls = ft.Container(
        content=ft.Stack(
            controls=[
                ft.Image(
                    src=MAIN_BG_PATH,
                    width=WIDTH,
                    height=HEIGHT,
                    fit=ft.ImageFit.COVER,
                )
            ]
            + virtual_buttons
        ),
        width=WIDTH,
        height=HEIGHT,
        expand=False,
        bgcolor=None,
    )

    _page.controls.clear()
    _page.add(_start_controls)
    _page.update()


def _show_a_page():
    global _a_container, _page

    def on_back(e):
        global _page_mode
        _page_mode = "start"
        _update_page_visibility()

    back_btn = ft.ElevatedButton(
        text="返回",
        on_click=on_back,
        bgcolor="#1677ff",
        color="#ffffff",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
    )

    web_view = ft.WebView(url=URL_A, expand=True)

    _a_container = ft.Container(
        content=ft.Stack(
            controls=[
                web_view,
                ft.Container(content=back_btn, right=20, top=20),
            ],
            expand=True,
        ),
        bgcolor=BG_COLOR,
        padding=0,
        width=WIDTH,
        height=HEIGHT,
        expand=False,
        border_radius=0,
    )
    _page.controls.clear()
    _page.add(_a_container)
    _page.update()


def _show_b_page():
    global _a_container, _page

    def on_back(e):
        global _page_mode
        _page_mode = "start"
        _update_page_visibility()

    back_btn = ft.ElevatedButton(
        text="返回",
        on_click=on_back,
        bgcolor="#1677ff",
        color="#ffffff",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
    )

    web_view = ft.WebView(url=URL_B, expand=True)

    _a_container = ft.Container(
        content=ft.Stack(
            controls=[
                web_view,
                ft.Container(content=back_btn, right=20, top=20),
            ],
            expand=True,
        ),
        width=WIDTH,
        height=HEIGHT,
        expand=False,
        bgcolor=BG_COLOR,
        padding=0,
        border_radius=0,
    )

    _page.controls.clear()
    _page.add(_a_container)
    _page.update()


def _show_c_page():
    global _main_container, _page, _img_control, _text_column

    def on_back(e):
        global _page_mode
        stop_camera_preview()
        _page_mode = "start"
        _update_page_visibility()

    back_btn = ft.ElevatedButton(
        "返回",
        on_click=on_back,
        bgcolor="#1677ff",
        color="#ffffff",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
    )

    _main_container = ft.Container(
        content=ft.Stack(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[_img_control, _text_column],
                        alignment=ft.MainAxisAlignment.START,
                        spacing=10,
                    ),
                    padding=PADDING,
                ),
                ft.Container(content=back_btn, right=20, top=20),
            ],
            expand=True,
        ),
        padding=0,
        bgcolor=BG_COLOR,
        width=WIDTH,
        height=HEIGHT,
        expand=False,
        border_radius=0,
    )
    _page.controls.clear()
    _page.add(_main_container)
    _page.update()


def _show_d_page():
    global _a_container, _page

    def on_back(e):
        global _page_mode
        _page_mode = "start"
        _update_page_visibility()

    back_btn = ft.ElevatedButton(
        "返回",
        on_click=on_back,
        bgcolor="#1677ff",
        color="#ffffff",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
    )

    web_view = ft.WebView(url=URL_D, expand=True)

    _a_container = ft.Container(
        content=ft.Stack(
            controls=[
                web_view,
                ft.Container(content=back_btn, right=20, top=20),
            ],
            expand=True,
        ),
        width=WIDTH,
        height=HEIGHT,
        expand=False,
        bgcolor=BG_COLOR,
        padding=0,
        border_radius=0,
    )
    _page.controls.clear()
    _page.add(_a_container)
    _page.update()


def _update_page_visibility():
    if _page_mode == "welcome":
        _show_welcome_page()
    elif _page_mode == "start":
        _show_start_page()
    elif _page_mode == "A":
        _show_a_page()
    elif _page_mode == "B":
        _show_b_page()
    elif _page_mode == "C":
        _show_c_page()
    elif _page_mode == "D":
        _show_d_page()


def _cv2_to_flet_image(frame):
    frame_flip = cv2.flip(frame, 1)
    success, buf = cv2.imencode(".jpg", frame_flip)
    if not success:
        return None
    return buf.tobytes()


def show_image(frame):
    global _img_control, _page
    img_bytes = _cv2_to_flet_image(frame)
    if img_bytes is not None and _img_control:
        img_base64 = base64.b64encode(img_bytes).decode()
        _img_control.src_base64 = img_base64
        if _page:
            _page.update()


def start_camera_preview():
    global _preview_running, _preview_thread
    if _preview_running:
        return
    _preview_running = True
    if _preview_thread is None or not _preview_thread.is_alive():
        _preview_thread = threading.Thread(target=_camera_preview_loop, daemon=True)
        _preview_thread.start()
        _img_control.visible = True


def stop_camera_preview():
    global _preview_running
    _img_control.visible = False
    _preview_running = False
    if _page and _gui_running:
        _page.update()


def _camera_preview_loop():
    import cam

    global _preview_running, _img_control, _page
    while _preview_running and _gui_running:
        if cam.is_camera_open():
            frame = cam.get_last_frame()
            if frame is not None:
                show_image(frame)
        time.sleep(0.03)  # 约33fps


def display_message(text):
    _event_queue.put(("msg", text))


def display_alert(text):
    _event_queue.put(("alert", text))


def close_gui():
    global _gui_running
    _gui_running = False
    stop_camera_preview()


def _ui_updater():
    global _lines, _gui_running, _page, _text_column
    while _gui_running:
        updated = False
        try:
            while True:
                evt_type, content = _event_queue.get_nowait()
                color = MSG_COLOR if evt_type == "msg" else ALERT_COLOR
                for line in content.splitlines():
                    _lines.append((evt_type, line))
                while len(_lines) > MAX_LINES:
                    _lines.pop(0)
                updated = True
        except queue.Empty:
            pass

        if updated and _page and _text_column:
            _text_column.controls.clear()
            for typ, line in _lines:
                color = MSG_COLOR if typ == "msg" else ALERT_COLOR
                _text_column.controls.append(
                    ft.Text(
                        line,
                        size=FONT_SIZE,
                        color=color,
                        font_family=FONT_FAMILY,
                    )
                )
            _page.update()
        time.sleep(0.1)


def run(page: ft.Page):
    """
    必须在主线程调用，Flet的入口。
    """

    global _gui_running, _page, _text_column, _img_control
    _gui_running = True
    _page = page

    page.title = "CubeCom"
    page.bgcolor = None
    if not DEBUG:
        # page.window.left = 0
        # page.window.top = 0
        # page.window.movable = False
        page.window.title_bar_buttons_hidden = True
    page.padding = 0
    # page.spacing = 0
    page.window.width = WIDTH
    page.window.height = HEIGHT
    page.window.resizable = False
    page.window.title_bar_hidden = True

    _text_column = ft.Column(
        controls=[],
        spacing=2,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    _img_control = ft.Image(
        src_base64="",
        width=WIDTH,
        height=300,
        fit=ft.ImageFit.FIT_WIDTH,
        visible=False,
    )

    _show_welcome_page()

    threading.Thread(target=_ui_updater, daemon=True).start()

    # 启动时间更新线程
    threading.Thread(target=_time_updater, daemon=True).start()

    page.update()


if __name__ == "__main__":
    ft.app(target=run, assets_dir="assets")
