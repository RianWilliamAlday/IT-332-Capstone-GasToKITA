
import os, json, sys, time, threading, socket, subprocess
from pathlib import Path
import flet as ft
import httpx, asyncio

AUTH = {"token": None, "role": None, "user": None, "access_token": None}

# FOR PC TESTING: use 127.0.0.1 so backend auto-starts
# FOR REAL PHONE: change to your PC IP like http://192.168.1.15:8000
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

BASE_DIR = Path(__file__).parent if not getattr(sys, 'frozen', False) else Path(sys._MEIPASS)
MOBILE_RED = "#8B0000"

def is_backend_running():
    try:
        with socket.create_connection(("127.0.0.1", 8000), timeout=1):
            return True
    except:
        return False

def run_backend():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BASE_DIR)
    # same as your desktop app.py
    print("[backend] starting uvicorn backend.main:app ...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(BASE_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    for line in proc.stdout:
        print("[backend]", line.strip())

async def wait_for_backend():
    print("[backend] waiting for backend...")
    for _ in range(30):
        try:
            async with httpx.AsyncClient() as c:
                await c.get(f"{API_URL}/docs", timeout=1)
                print("[backend] backend is up!")
                return True
        except:
            await asyncio.sleep(0.5)
    print("[backend] backend failed to start")
    return False

def show_login(page: ft.Page, auth: dict):
    page.title = "GAStoKITA Login"
    page.bgcolor = MOBILE_RED
    page.padding = 0
    page.window.width = 390
    page.window.height = 844
    page.window.resizable = False

    email_field = ft.TextField(
        label="EMAIL ADDRESS",
        label_style=ft.TextStyle(size=11, weight=ft.FontWeight.BOLD, color="#555555"),
        filled=True, fill_color="#EBEBEB", border_color=ft.Colors.TRANSPARENT, focused_border_color=MOBILE_RED,
        border_radius=10, text_style=ft.TextStyle(size=14),
    )
    password_field = ft.TextField(
        label="PASSWORD",
        label_style=ft.TextStyle(size=11, weight=ft.FontWeight.BOLD, color="#555555"),
        password=True, can_reveal_password=True,
        filled=True, fill_color="#EBEBEB", border_color=ft.Colors.TRANSPARENT, focused_border_color=MOBILE_RED,
        border_radius=10, text_style=ft.TextStyle(size=14),
    )
    status_text = ft.Text("", color="red", size=12)

    def login_click(e):
        status_text.value = "Logging in..."
        page.update()

        def do_login():
            try:
                import requests
                r = requests.post(f"{API_URL}/api/auth/employee/login", json={"email": email_field.value.strip(), "password": password_field.value}, timeout=5)
                if r.status_code != 200:
                    status_text.value = f"Login failed: {r.text[:150]}"
                    page.update()
                    return
                data = r.json()
                token = data.get("access_token") or data.get("token")
                if not token:
                    status_text.value = "No token in response"
                    page.update()
                    return
                me_r = requests.get(f"{API_URL}/api/auth/me", headers={"Authorization": f"Bearer {token}"}, timeout=5)
                user_data = me_r.json() if me_r.status_code==200 else {}
                AUTH["token"] = token
                AUTH["access_token"] = token
                AUTH["user"] = user_data
                AUTH["role"] = user_data.get("role","EMPLOYEE")

                async def save():
                    await page.shared_preferences.set("gastokita.auth_token", token)
                    await page.shared_preferences.set("gastokita.user_json", json.dumps(user_data))
                page.run_task(save)

                from pages.select_pa_m import build_pa_page_mobile
                page.controls.clear()
                page.add(build_pa_page_mobile(page, AUTH))
                page.update()

            except Exception as ex:
                status_text.value = f"Error: {ex}"
                page.update()
                import traceback; traceback.print_exc()

        page.run_thread(do_login)

    login_button = ft.Container(
        content=ft.Text("LOGIN", size=15, weight=ft.FontWeight.BOLD, color="white", text_align=ft.TextAlign.CENTER),
        bgcolor=MOBILE_RED, border_radius=8, padding=ft.Padding.symmetric(vertical=14), ink=True, on_click=login_click, alignment=ft.Alignment.CENTER
    )

    header = ft.Container(
        content=ft.Row(controls=[ft.Container(content=ft.Image(src="u-fuel_logo.jpg", width=40, height=40, fit=ft.BoxFit.CONTAIN), bgcolor="white", border_radius=8, padding=6, width=40, height=40), ft.Text("U-FUEL", size=20, weight=ft.FontWeight.BOLD, color="white")], spacing=10),
        padding=ft.Padding.symmetric(horizontal=20, vertical=16),
    )

    login_card = ft.Container(
        content=ft.Column(
            controls=[ft.Text("LOGIN", size=28, weight=ft.FontWeight.BOLD, color="#111111"), ft.Container(height=20), email_field, ft.Container(height=14), password_field, ft.Container(height=20), login_button, status_text],
            spacing=0,
            scroll=ft.ScrollMode.ADAPTIVE,
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor="white", border_radius=ft.BorderRadius(top_left=28, top_right=28, bottom_left=0, bottom_right=0), padding=ft.Padding.symmetric(horizontal=24, vertical=36), expand=True,
    )

    footer = ft.Container(content=ft.Text("GAStoKITA", size=13, color="white", text_align=ft.TextAlign.CENTER), bgcolor=MOBILE_RED, padding=ft.Padding.symmetric(vertical=14), alignment=ft.Alignment.CENTER)

    return ft.SafeArea(
        content=ft.Column(controls=[header, ft.Container(height=10), login_card, footer], expand=True, spacing=0),
        expand=True,
    )

async def main(page: ft.Page):
    page.title = "GasToKITA"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window.width = 390
    page.window.height = 844
    page.window.resizable = False

    # --- AUTO START BACKEND FOR PC TESTING (same as your desktop app.py) ---
    loading_backend = ft.Container(expand=True, alignment=ft.Alignment.CENTER, content=ft.Column(controls=[ft.ProgressRing(color="white"), ft.Text("Starting backend...", color="white")], horizontal_alignment=ft.CrossAxisAlignment.CENTER))
    page.add(loading_backend)
    page.update()

    # only auto-start if API_URL is local (for PC testing)
    if "127.0.0.1" in API_URL or "localhost" in API_URL:
        if not is_backend_running():
            threading.Thread(target=run_backend, daemon=True).start()
            time.sleep(0.5)
        await wait_for_backend()
    else:
        # remote IP - skip backend start
        print(f"[mobile] using remote API {API_URL}, skipping local backend start")

    page.controls.clear()
    # --- AUTO LOGIN TRY ---
    loading = ft.Container(expand=True, alignment=ft.Alignment.CENTER, content=ft.Column(controls=[ft.ProgressRing(color="white"), ft.Text("Loading...", color="white")], horizontal_alignment=ft.CrossAxisAlignment.CENTER))
    page.add(loading)
    page.update()

    try:
        token = await page.shared_preferences.get("gastokita.auth_token")
        if token:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{API_URL}/api/auth/me", headers={"Authorization": f"Bearer {token}"})
                if resp.status_code == 200:
                    AUTH["token"] = token
                    AUTH["access_token"] = token
                    AUTH["user"] = resp.json()
                    AUTH["role"] = resp.json().get("role")
                    page.controls.clear()
                    from pages.select_pa_m import build_pa_page_mobile
                    page.add(build_pa_page_mobile(page, AUTH))
                    page.update()
                    return
            await page.shared_preferences.remove("gastokita.auth_token")
    except Exception as e:
        print(f"Auto-login error {e}")

    page.controls.clear()
    page.add(show_login(page, AUTH))
    page.update()

if __name__ == "__main__":
    threading.Thread(target=run_backend, daemon=True).start()  # fine in a thread
    ft.run(main, assets_dir="assets")             