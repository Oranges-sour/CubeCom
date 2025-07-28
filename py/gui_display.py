import pygame
import queue

WIDTH, HEIGHT = 640, 480
SCALE = 2
RENDER_WIDTH, RENDER_HEIGHT = WIDTH * SCALE, HEIGHT * SCALE

BG_COLOR = (30, 30, 30)
MSG_COLOR = (200, 255, 200)
ALERT_COLOR = (255, 100, 100)
FONT_SIZE = 14
LINE_HEIGHT = 30
MAX_LINES = (HEIGHT - 40) // LINE_HEIGHT

FONT_PATH = "font.ttf"

_event_queue = queue.Queue()
_lines = []
_gui_running = False


def display_message(text):
    _event_queue.put(("msg", text))


def display_alert(text):
    _event_queue.put(("alert", text))


def close_gui():
    global _gui_running
    _gui_running = False


def wrap_text(text, font, max_width):
    """将text按像素宽度max_width自动换行，返回行列表。"""
    words = text.split(" ")
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + ("" if current_line == "" else " ") + word
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            # 单个单词可能超长，强行拆分
            while font.size(word)[0] > max_width:
                for i in range(1, len(word) + 1):
                    if font.size(word[:i])[0] > max_width:
                        break
                # i-1字符能塞下
                lines.append(word[: i - 1])
                word = word[i - 1 :]
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def run():
    """必须在主线程调用。"""
    global _gui_running
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("消息与警告显示")
    font = pygame.font.Font(FONT_PATH, FONT_SIZE * SCALE)
    clock = pygame.time.Clock()
    _gui_running = True

    margin = 20 * SCALE
    max_text_width = RENDER_WIDTH - 2 * margin

    while _gui_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                _gui_running = False

        # 消息处理
        try:
            while True:
                evt_type, content = _event_queue.get_nowait()
                color = MSG_COLOR if evt_type == "msg" else ALERT_COLOR
                # 自动换行
                wrapped = wrap_text(content, font, max_text_width)
                for line in wrapped:
                    _lines.append((evt_type, line))
                # 保持最大行数
                while len(_lines) > MAX_LINES:
                    _lines.pop(0)
        except queue.Empty:
            pass

        # 在高分辨率surface绘制
        render_surf = pygame.Surface((RENDER_WIDTH, RENDER_HEIGHT))
        render_surf.fill(BG_COLOR)
        y = margin
        for typ, line in _lines:
            color = MSG_COLOR if typ == "msg" else ALERT_COLOR
            text_surf = font.render(line, True, color)
            render_surf.blit(text_surf, (margin, y))
            y += LINE_HEIGHT * SCALE

        # 缩放回窗口
        scaled_surf = pygame.transform.scale(render_surf, (WIDTH, HEIGHT))
        screen.blit(scaled_surf, (0, 0))

        pygame.display.flip()
        clock.tick(30)
    pygame.quit()
