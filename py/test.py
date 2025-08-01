import flet as ft
import numpy as np


WIDTH, HEIGHT = 480, 640

def run(page: ft.Page):
    page.title = "CubeCom"
    page.bgcolor = None
    page.padding = 0
    page.spacing = 0
    page.window.width = WIDTH
    page.window.height = HEIGHT
    page.window.resizable = False
    page.window.title_bar_hidden = True
    page.window.title_bar_buttons_hidden = True

    img = ft.Image(
        src=f"bk1.png",
        width=WIDTH,
        height=HEIGHT,
    )
    page.add(img)


if __name__ == "__main__":
    ft.app(target=run, assets_dir="assets")
