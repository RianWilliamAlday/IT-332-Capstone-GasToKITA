import subprocess, threading, time, sys, os, socket
from pathlib import Path
import flet as ft
import httpx, asyncio
from dotenv import load_dotenv

load_dotenv(Path(_file_).parent / ".env")

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(_file_).parent

API_URL = "http://127.0.0.1:8000"
RED = "#A61E22"
LIGHT_GRAY = "#E9E9E9"
CARD_GRAY = "#D9D9D9"
DARK_RED = "#8B0000"
WHITE = "#FFFFFF"

AUTH = {"token": None, "name": None, "access_token": None}

def is_backend_running():
    try:
        with socket.create_connection(("127.0.0.1", 8000), timeout=1):
            return True
    except:
        return False

def run_backend():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BASE_DIR)
    subprocess.run([sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000", "--log-level", "error"], cwd=BASE_DIR, env=env)

async def wait_for_backend(page, max_wait=20):
    for i in range(max_wait):
        try:
            async with httpx.AsyncClient() as client:
                await client.get(f"{API_URL}/docs", timeout=1)
                return True
        except:
            if page.controls:
                try:
                    page.controls[0].content.controls[1].value = f"Starting backend... {i+1}s"
                    page.update()
                except: pass
            await asyncio.sleep(0.5)
    return False

def build_login_view(page: ft.Page, auth: dict):
    password_field = ft.TextField(hint_text="Enter your password", password=True, can_reveal_password=True, border_radius=25, border_color="black", bgcolor="white", width=330, height=50)
    status_text = ft.Text("", color=RED, size=14)

    async def login(e):
        if not password_field.value:
            status_text.value = "Password required"; page.update(); return
        e.control.disabled = True
        try:
            e.control.content = ft.ProgressRing(width=18, height=18, color="white")
        except:
            e.control.text = "Logging in..."
        page.update()
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(f"{API_URL}/api/auth/admin/login", json={"password": password_field.value})
            if resp.status_code == 200:
                data = resp.json()
                auth["token"] = data.get("access_token")
                auth["access_token"] = data.get("access_token")
                auth["name"] = data.get("name", "Admin")
                from pages.admin_dashboard import dashboard_page
                page.controls.clear()
                page.add(dashboard_page(page, auth))
                page.update()
            else:
                status_text.value = "Incorrect password"
        except Exception as ex:
            status_text.value = f"Connection error: {ex}"
        finally:
            try:
                e.control.disabled = False
                e.control.content = ft.Text("Login", size=20, weight=ft.FontWeight.BOLD, color="white")
                page.update()
            except: pass

    login_btn = ft.Container(
        width=130, height=45, bgcolor=RED, border_radius=25, ink=True, on_click=login,
        alignment=ft.Alignment.CENTER, content=ft.Text("Login", size=20, weight=ft.FontWeight.BOLD, color="white")
    )

    login_card = ft.Container(
        width=460,
        height=360,
        border_radius=25,
        padding=25,
        bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
        border=ft.Border.all(1.2, ft.Colors.with_opacity(0.3, ft.Colors.WHITE)),
        blur=ft.Blur(5, 5, ft.BlurTileMode.MIRROR),
        shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK)),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            spacing=18, 
            controls=[
                ft.Text("Admin Login", size=32, weight=ft.FontWeight.BOLD, color="white"),
                ft.Text("Please enter your password", size=14, text_align=ft.TextAlign.CENTER, color=ft.Colors.with_opacity(0.8, "white")),
                ft.Column(spacing=8, controls=[
                    ft.Text("Password:", weight=ft.FontWeight.BOLD, color="white"), 
                    password_field
                ]),
                login_btn, 
                status_text,
            ]
        ),
    )

    header = ft.Container(
        content=ft.Row([
            ft.Text("GAStoKITA", color=WHITE, size=22, weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.Text("U-Fuel", color=WHITE, size=18, weight=ft.FontWeight.BOLD),
                ft.Container(width=42, height=42, bgcolor=WHITE, border_radius=20, clip_behavior=ft.ClipBehavior.HARD_EDGE, content=ft.Image(src="u-fuel_logo.jpg", fit=ft.BoxFit.CONTAIN, border_radius=20)),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=DARK_RED, padding=ft.Padding.symmetric(vertical=18, horizontal=24),
    )

    footer = ft.Container(
        content=ft.Row([ft.Text("GAStoKITA", color=WHITE, size=12)], alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=DARK_RED, padding=ft.Padding.symmetric(vertical=14, horizontal=24),
    )

    page_content = ft.Column(spacing=0, expand=True, controls=[
        header,
        ft.Container(expand=True, alignment=ft.Alignment.CENTER, content=login_card),
        footer
    ])

    return ft.Stack(
        expand=True,
        fit=ft.StackFit.EXPAND,
        controls=[
            ft.Container(
                expand=True,
                image=ft.DecorationImage(
                    src="background.jpg",
                    fit=ft.BoxFit.COVER,
                )
            ),
            ft.Container(
                expand=True,
                bgcolor=ft.Colors.with_opacity(0.30, ft.Colors.BLACK)
            ),
            page_content
        ]
    )

async def main(page: ft.Page):
    page.title = "GasToKITA - Admin"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = LIGHT_GRAY
    page.padding = 0
    page.window.maximized = True

    loading = ft.Container(expand=True, alignment=ft.Alignment.CENTER, content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20, controls=[ft.ProgressRing(width=40, height=40, color=RED), ft.Text("Starting backend...", size=20, weight=ft.FontWeight.BOLD)]))
    page.add(loading)
    page.update()

    backend_ok = await wait_for_backend(page)
    if not backend_ok:
        loading.content.controls[1].value = "Backend failed to start. Check console."
        page.update()
        return

    page.controls.clear()
    page.add(build_login_view(page, AUTH))
    page.update()

if _name_ == "_main_":
    if not is_backend_running():
        threading.Thread(target=run_backend, daemon=True).start()
        time.sleep(0.5)
    ft.run(main, assets_dir=str(BASE_DIR))
