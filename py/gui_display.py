import flet as ft
import threading
import queue
import time

DEBUG = True

WIDTH, HEIGHT = 640, 480

BG_COLOR = "#1e1e1e"
MSG_COLOR = "#c8ffc8"
ALERT_COLOR = "#ff6464"
FONT_SIZE = 14
LINE_HEIGHT = 22
PADDING = 20
MAX_LINES = (HEIGHT - PADDING * 2) // LINE_HEIGHT

FONT_FAMILY = "font"  # 如有自定义字体需配置
FONT_PATH = "font.ttf"  # 静态资源路径，见Flet文档

_event_queue = queue.Queue()
_lines = []
_gui_running = False
_page = None
_text_column = None
_update_lock = threading.Lock()


def display_message(text):
    _event_queue.put(("msg", text))


def display_alert(text):
    _event_queue.put(("alert", text))


def close_gui():
    global _gui_running
    _gui_running = False


def _ui_updater():
    # 后台线程：处理队列和刷新UI
    global _lines, _gui_running, _page, _text_column
    while _gui_running:
        updated = False
        try:
            # 批量处理所有新消息
            while True:
                evt_type, content = _event_queue.get_nowait()
                color = MSG_COLOR if evt_type == "msg" else ALERT_COLOR
                # 按原来策略拆分成多
                for line in content.splitlines():
                    _lines.append((evt_type, line))
                # 保持最大行数
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
    global _gui_running, _page, _text_column
    _gui_running = True
    _page = page

    page.title = "CubeCom"
    page.bgcolor = BG_COLOR
    if not DEBUG:
        page.window.left = 0
        page.window.top = 0
        page.window.movable = False
        page.window.title_bar_buttons_hidden = True
    page.window.width = WIDTH
    page.window.height = HEIGHT
    page.window.resizable = False
    page.window.title_bar_hidden = True


    # 用Column按行显示文本
    _text_column = ft.Column(
        controls=[],
        spacing=2,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    # 页面布局
    container = ft.Container(
        content=_text_column,
        padding=PADDING,
        bgcolor=BG_COLOR,
        width=WIDTH - PADDING * 2,
        height=HEIGHT - PADDING * 2,
        border_radius=0,
    )

    page.add(container)

    t = threading.Thread(target=_ui_updater, daemon=True)
    t.start()

    page.update()


# 如果作为脚本运行也可以这样启动
if __name__ == "__main__":
    ft.app(target=run)
