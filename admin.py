import subprocess, threading, time, sys, os, socket, inspect
from pathlib import Path
import flet as ft
import httpx, asyncio
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent

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

async def google_sign_in(page, api_url: str, role: str = "admin", timeout: int = 120) -> dict:
    """Asks the backend for a Google sign-in URL, opens it in the browser,
    then polls the backend until the login finishes. Returns the token response."""
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{api_url}/api/auth/google/start", params={"role": role})
        r.raise_for_status()
        info = r.json()

        res = page.launch_url(info["url"])
        if inspect.isawaitable(res):
            await res

        deadline = time.time() + timeout
        while time.time() < deadline:
            await asyncio.sleep(1.5)
            p = await c.get(f"{api_url}/api/auth/google/poll/{info['state']}")
            if p.status_code == 404:
                raise RuntimeError("Login expired")
            data = p.json()
            if data["status"] == "ok":
                return data
            if data["status"] == "error":
                raise RuntimeError(data["detail"])
    raise RuntimeError("Timed out waiting for Google sign-in")

def build_login_view(page: ft.Page, auth: dict):
    is_signup_mode = False

    status_text = ft.Text("", color=RED, size=14)
    title_text = ft.Text("Admin Login", size=28, weight=ft.FontWeight.BOLD, color="white")
    btn_text = ft.Text("Login", size=18, weight=ft.FontWeight.BOLD, color="white")
    toggle_text = ft.Text("Don't have an admin account? Sign Up", weight=ft.FontWeight.BOLD, color="#1877F2", size=13)

    name_field = ft.TextField(
        label="USERNAME",
        label_style=ft.TextStyle(size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE70),
        hint_text="Enter your username",
        hint_style=ft.TextStyle(color=ft.Colors.WHITE38),
        filled=True,
        fill_color=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
        color=ft.Colors.WHITE,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=RED,
        cursor_color=ft.Colors.WHITE,
        border_radius=12,
        width=330,
        height=50,
        text_style=ft.TextStyle(size=14, color=ft.Colors.WHITE),
        visible=False
    )

    email_field = ft.TextField(
        label="EMAIL ADDRESS",
        label_style=ft.TextStyle(size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE70),
        hint_text="Enter your email",
        hint_style=ft.TextStyle(color=ft.Colors.WHITE38),
        keyboard_type=ft.KeyboardType.EMAIL,
        filled=True,
        fill_color=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
        color=ft.Colors.WHITE,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=RED,
        cursor_color=ft.Colors.WHITE,
        border_radius=12,
        width=330,
        height=50,
        text_style=ft.TextStyle(size=14, color=ft.Colors.WHITE),
    )
    
    password_field = ft.TextField(
        label="PASSWORD",
        label_style=ft.TextStyle(size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE70),
        hint_text="Enter your password",
        hint_style=ft.TextStyle(color=ft.Colors.WHITE38),
        password=True,
        can_reveal_password=True,
        filled=True,
        fill_color=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
        color=ft.Colors.WHITE,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=RED,
        cursor_color=ft.Colors.WHITE,
        border_radius=12,
        width=330,
        height=50,
        text_style=ft.TextStyle(size=14, color=ft.Colors.WHITE),
    )

    def switch_to_signup():
        nonlocal is_signup_mode
        if not is_signup_mode:
            is_signup_mode = True
            title_text.value = "Admin Sign Up"
            btn_text.value = "Create Admin"
            toggle_text.value = "Already have an admin account? Login"
            name_field.visible = True
            login_card.height = 510

    async def login_google(e=None):
        status_text.value = "Connecting to Google..."
        page.update()
        try:
            data = await google_sign_in(page, API_URL, role="admin")
        except Exception as ex:
            status_text.value = f"Google login failed: {ex}"
            page.update()
            return

        token = data.get("access_token")
        user_data = data.get("user") or {}

        if token and user_data:
            auth["token"] = token
            auth["access_token"] = token
            auth["name"] = user_data.get("name", "Admin")
            from pages.admin_dashboard import dashboard_page
            page.controls.clear()
            page.add(dashboard_page(page, auth))
            page.update()
            return

        google_email = data.get("email") or user_data.get("email", "")
        google_name = data.get("name") or user_data.get("name", "")

        switch_to_signup()
        if google_name:
            name_field.value = google_name
        if google_email:
            email_field.value = google_email

        status_text.value = "Google profile loaded! Set a password to create admin account."
        page.update()

    async def handle_auth_action(e=None):
        if not email_field.value or not password_field.value or (is_signup_mode and not name_field.value):
            status_text.value = "All fields are required"
            page.update()
            return

        login_btn.disabled = True
        login_btn.content = ft.ProgressRing(width=18, height=18, color="white")
        page.update()

        endpoint = f"{API_URL}/api/auth/register" if is_signup_mode else f"{API_URL}/api/auth/admin/login"
        payload = {"email": email_field.value, "password": password_field.value}
        if is_signup_mode:
            payload["name"] = name_field.value
            payload["role"] = "ADMIN"

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(endpoint, json=payload)
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
                detail = resp.json().get("detail", "Authentication failed")
                status_text.value = str(detail)
        except Exception as ex:
            status_text.value = f"Connection error: {ex}"
        finally:
            login_btn.disabled = False
            login_btn.content = btn_text
            page.update()

    def toggle_mode(e):
        nonlocal is_signup_mode
        is_signup_mode = not is_signup_mode
        title_text.value = "Admin Sign Up" if is_signup_mode else "Admin Login"
        btn_text.value = "Create Admin" if is_signup_mode else "Login"
        toggle_text.value = "Already have an admin account? Login" if is_signup_mode else "Don't have an admin account? Sign Up"
        name_field.visible = is_signup_mode
        login_card.height = 510 if is_signup_mode else 440
        status_text.value = ""
        page.update()

    async def login_google(e=None):
            status_text.value = "Complete sign-in in your browser..."
            page.update()
            try:
                data = await google_sign_in(page, API_URL, role="admin")
            except Exception as ex:
                status_text.value = f"Google login failed: {ex}"
                page.update()
                return
    
            auth["token"] = data.get("access_token")
            auth["access_token"] = data.get("access_token")
            auth["name"] = data.get("name", "Admin")
            from pages.admin_dashboard import dashboard_page
            page.controls.clear()
            page.add(dashboard_page(page, auth))
            page.update()

    email_field.on_submit = handle_auth_action
    password_field.on_submit = handle_auth_action
    name_field.on_submit = handle_auth_action

    login_btn = ft.Container(
        width=330, 
        height=48, 
        bgcolor=RED, 
        border_radius=12, 
        ink=True, 
        on_click=handle_auth_action,
        alignment=ft.Alignment.CENTER, 
        content=btn_text
    )

    google_btn = ft.Container(
        width=330,
        height=45,
        border_radius=25,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        bgcolor=ft.Colors.with_opacity(0.85, ft.Colors.WHITE),
        blur=ft.Blur(5, 5, ft.BlurTileMode.MIRROR),
        content=ft.OutlinedButton(
            content="Sign in with Google",
            icon=ft.Icons.LOGIN,
            width=330,
            height=45,
            on_click=login_google,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.TRANSPARENT,
                color="black",
                shape=ft.RoundedRectangleBorder(radius=25),
                side=ft.BorderSide(1, "black")
            )
        )
    )

    login_card = ft.Container(
        width=460,
        height=440,
        border_radius=25,
        padding=25,
        bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
        border=ft.Border.all(1.2, ft.Colors.with_opacity(0.3, ft.Colors.WHITE)),
        blur=ft.Blur(5, 5, ft.BlurTileMode.MIRROR),
        shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK)),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            spacing=12, 
            controls=[
                title_text,
                name_field,
                email_field,
                password_field,
                login_btn, 
                ft.GestureDetector(content=toggle_text, on_tap=toggle_mode),
                ft.Row([ft.Container(expand=True, height=1, bgcolor="white"), ft.Text(" OR ", color="white"), ft.Container(expand=True, height=1, bgcolor="white")], alignment=ft.MainAxisAlignment.CENTER, width=330),
                google_btn,
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
    page.title = "GAStoKITA - Admin"
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

if __name__ == "__main__":
    if not is_backend_running():
        threading.Thread(target=run_backend, daemon=True).start()
        time.sleep(0.5)
    ft.run(main, assets_dir=str(BASE_DIR))