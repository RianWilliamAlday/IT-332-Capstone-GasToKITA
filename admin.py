import subprocess
import threading
import time
import sys
import os
import flet as ft
from pathlib import Path
import httpx
import asyncio
import socket
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

AUTH = {"token": None, "name": None}

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent

API_URL = "http://127.0.0.1:8000"

RED = "#A61E22"
LIGHT_GRAY = "#E9E9E9"
CARD_GRAY = "#D9D9D9"

def is_backend_running():
    try:
        with socket.create_connection(("127.0.0.1", 8000), timeout=1):
            return True
    except:
        return False

def run_backend():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BASE_DIR)
    print(f"Starting uvicorn from: {BASE_DIR}")
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "backend.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--log-level", "error"
    ],
    cwd=BASE_DIR,
    env=env
    )

async def wait_for_backend(page, max_wait=20):
    for i in range(max_wait):
        try:
            async with httpx.AsyncClient() as client:
                await client.get(f"{API_URL}/docs", timeout=1)
                return True
        except:
            page.controls[0].content.value = f"Starting backend... {i+1}s"
            page.update()
            await asyncio.sleep(0.5)
    return False

async def main(page: ft.Page):
    page.title = "GasToKITA - Admin"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = LIGHT_GRAY
    page.padding = 0
    page.window.maximized = True

    loading = ft.Container(
        expand=True,
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            controls=[
                ft.ProgressRing(width=40, height=40, color=RED),
                ft.Text("Starting backend...", size=20, weight=ft.FontWeight.BOLD)
            ]
        )
    )
    page.add(loading)
    page.update()

    backend_ok = await wait_for_backend(page)
    if not backend_ok:
        loading.content.controls[1].value = "Backend failed to start. Check console."
        page.update()
        return

    page.controls.clear()

    password_field = ft.TextField(
        hint_text="Enter your password",
        password=True,
        can_reveal_password=True,
        border_radius=25,
        border_color="black",
        bgcolor="white",
        width=330,
        height=50,
    )
    status_text = ft.Text("", color=RED, size=14)

    async def login(e):
        if not password_field.value:
            status_text.value = "Password required"
            page.update()
            return

        e.control.disabled = True
        e.control.text = "Logging in..."
        page.update()

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{API_URL}/api/auth/admin/login",
                    json={"password": password_field.value}
                )
            if resp.status_code == 200:
                data = resp.json()
                AUTH["token"] = data.get("access_token")
                AUTH["name"] = data.get("name", "Admin")
                page.snack_bar = ft.SnackBar(ft.Text(f"Welcome {data['name']}!"), bgcolor="green")
                page.snack_bar.open = True
                status_text.value = ""
            else:
                status_text.value = "Incorrect password"
        except Exception as ex:
            status_text.value = f"Connection error: {ex}"
        finally:
            e.control.disabled = False
            e.control.text = "Login"
            page.update()

    login_btn = ft.Button(
        "Login", width=130, height=45, on_click=login,
        style=ft.ButtonStyle(bgcolor=RED, color="white",
            shape=ft.RoundedRectangleBorder(radius=25),
            text_style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD))
    )

    login_card = ft.Container(
        width=460, height=340, bgcolor=CARD_GRAY,
        border=ft.Border.all(2, ft.Colors.BLACK), border_radius=25, padding=20,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=18,
            controls=[
                ft.Text("Admin Login", size=32, weight=ft.FontWeight.BOLD),
                ft.Text("Please enter your password", size=14, text_align=ft.TextAlign.CENTER),
                ft.Column(spacing=8, controls=[ft.Text("Password:", weight=ft.FontWeight.BOLD), password_field]),
                login_btn,
                status_text,
            ],
        ),
    )

    header = ft.Container(bgcolor=RED, height=100, padding=20,
        content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text("GAStoKITA", size=28, weight=ft.FontWeight.BOLD, color="white"),
                ft.Row([ft.Text("U-Fuel", size=28, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Container(width=70, height=70, bgcolor="white", border_radius=12,
                                     content=ft.Image(src="u-fuel_logo.jpg", fit=ft.BoxFit.CONTAIN))])
            ]))

    footer = ft.Container(height=80, bgcolor=RED)

    page.add(ft.Column(spacing=0, expand=True, controls=[
        header,
        ft.Container(expand=True, alignment=ft.Alignment.CENTER, content=login_card),
        footer,
    ]))

if __name__ == "__main__":
    if not is_backend_running():
        t = threading.Thread(target=run_backend, daemon=True)
        t.start()
        time.sleep(0.5)

    ft.run(main, assets_dir=str(BASE_DIR))