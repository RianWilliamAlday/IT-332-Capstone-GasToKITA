import os, json, sys, time, threading, socket, subprocess, inspect
from pathlib import Path
import flet as ft
import httpx, asyncio

AUTH = {"token": None, "role": None, "user": None, "access_token": None}

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

async def google_sign_in(page, api_url: str, timeout: int = 120) -> dict:
    """Asks the backend for a Google sign-in URL, opens it in the browser,
    then polls the backend until the login finishes. Returns the token response."""
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{api_url}/api/auth/google/start")
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

def show_login(page: ft.Page, auth: dict):
    page.title = "GAStoKITA Login"
    page.bgcolor = MOBILE_RED
    page.padding = 0
    page.window.width = 390
    page.window.height = 844
    page.window.resizable = False

    is_signup_mode = False

    name_field = ft.TextField(
        label="USERNAME",
        label_style=ft.TextStyle(size=11, weight=ft.FontWeight.BOLD, color="#555555"),
        filled=True,
        expand=True,
        fill_color="#EBEBEB",
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=MOBILE_RED,
        border_radius=10,
        text_style=ft.TextStyle(size=14),
        visible=False, 
    )

    email_field = ft.TextField(
        label="EMAIL ADDRESS",
        label_style=ft.TextStyle(size=11, weight=ft.FontWeight.BOLD, color="#555555"),
        filled=True,
        fill_color="#EBEBEB",
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=MOBILE_RED,
        border_radius=10,
        text_style=ft.TextStyle(size=14),
        expand=True,
    )

    password_field = ft.TextField(
        label="PASSWORD",
        label_style=ft.TextStyle(size=11, weight=ft.FontWeight.BOLD, color="#555555"),
        password=True,
        can_reveal_password=True,
        filled=True,
        expand=True,
        fill_color="#EBEBEB",
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=MOBILE_RED,
        border_radius=10,
        text_style=ft.TextStyle(size=14),
    )

    title_text = ft.Text("LOGIN", size=28, weight=ft.FontWeight.BOLD, color="#111111")
    action_button_text = ft.Text("LOGIN", size=15, weight=ft.FontWeight.BOLD, color="white", text_align=ft.TextAlign.CENTER)
    status_text = ft.Text("", color="red", size=12)

    toggle_mode_text = ft.Text("Don't have an account? Sign Up", size=13, color="#1877F2", weight=ft.FontWeight.W_500)

    def auth_action_click(e):
        email_val = email_field.value.strip() if email_field.value else ""
        pass_val = password_field.value if password_field.value else ""
        name_val = name_field.value.strip() if name_field.value else ""

        if not email_val or not pass_val or (is_signup_mode and not name_val):
            status_text.value = "Please fill in all required fields."
            page.update()
            return

        status_text.value = "Processing..."
        page.update()

        def do_auth():
            try:
                import requests
                endpoint = f"{API_URL}/api/auth/register" if is_signup_mode else f"{API_URL}/api/auth/employee/login"
                payload = {"email": email_val, "password": pass_val}
                if is_signup_mode:
                    payload["name"] = name_val

                r = requests.post(endpoint, json=payload, timeout=5)
                if r.status_code != 200:
                    status_text.value = f"Failed: {r.json().get('detail', r.text[:150])}"
                    page.update()
                    return

                data = r.json()
                token = data.get("access_token") or data.get("token")
                if not token:
                    status_text.value = "Authentication token missing."
                    page.update()
                    return

                user_data = data.get("user") or {}
                AUTH["token"] = token
                AUTH["access_token"] = token
                AUTH["user"] = user_data
                AUTH["role"] = user_data.get("role", "EMPLOYEE")

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

        page.run_thread(do_auth)

    async def google_click(e):
        status_text.value = "Fetching Google account info..."
        page.update()
        
        try:
            data = await google_sign_in(page, API_URL)
        except Exception as ex:
            status_text.value = f"Google sign-in failed: {ex}"
            page.update()
            return

        token = data.get("access_token")
        user_data = data.get("user") or {}

        if token and user_data:
            AUTH["token"] = token
            AUTH["access_token"] = token
            AUTH["user"] = user_data
            AUTH["role"] = user_data.get("role", "EMPLOYEE")
            
            await page.shared_preferences.set("gastokita.auth_token", token)
            await page.shared_preferences.set("gastokita.user_json", json.dumps(user_data))

            from pages.select_pa_m import build_pa_page_mobile
            page.controls.clear()
            page.add(build_pa_page_mobile(page, AUTH))
            page.update()
            return

        google_email = data.get("email") or user_data.get("email", "")
        google_name = data.get("name") or user_data.get("name", "")

        if google_email or google_name:
            nonlocal is_signup_mode
            if not is_signup_mode:
                is_signup_mode = True
                title_text.value = "SIGN UP"
                action_button_text.value = "CREATE ACCOUNT"
                name_field.visible = True
                toggle_mode_text.value = "Already have an account? Login"

            if google_name:
                name_field.value = google_name
            if google_email:
                email_field.value = google_email
            
            password_field.focus()

            status_text.color = "green"
            status_text.value = "Google profile connected! Set a password to complete registration."
            page.update()

    def toggle_mode_click(e):
        nonlocal is_signup_mode
        is_signup_mode = not is_signup_mode

        title_text.value = "SIGN UP" if is_signup_mode else "LOGIN"
        action_button_text.value = "CREATE ACCOUNT" if is_signup_mode else "LOGIN"
        name_field.visible = is_signup_mode
        toggle_mode_text.value = "Already have an account? Login" if is_signup_mode else "Don't have an account? Sign Up"
        status_text.value = ""
        page.update()

    action_button = ft.Container(
        content=action_button_text,
        bgcolor=MOBILE_RED,
        border_radius=8,
        padding=ft.Padding.symmetric(vertical=14),
        ink=True,
        on_click=auth_action_click,
        alignment=ft.Alignment.CENTER
    )

    toggle_container = ft.GestureDetector(
        content=toggle_mode_text,
        on_tap=toggle_mode_click,
    )

    google_button = ft.OutlinedButton(
        content="Sign in with Google",
        icon=ft.Icons.LOGIN,
        width=330,
        height=45,
        on_click=google_click,
        style=ft.ButtonStyle(
            bgcolor="white",
            color="black",
            shape=ft.RoundedRectangleBorder(radius=25),
            side=ft.BorderSide(1, "black")
        )
    )

    login_card = ft.Container(
        content=ft.Column(
            controls=[
                title_text,
                ft.Container(height=16),
                name_field,
                email_field,
                password_field,
                ft.Container(height=16),
                action_button,
                ft.Container(height=12),
                toggle_container,
                ft.Container(height=12),
                google_button,
                ft.Container(height=8),
                status_text
            ],
            spacing=12,
            scroll=ft.ScrollMode.ADAPTIVE,
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor="white",
        border_radius=ft.BorderRadius(top_left=28, top_right=28, bottom_left=0, bottom_right=0),
        padding=ft.Padding.symmetric(horizontal=24, vertical=28),
        expand=True,
    )

    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(content=ft.Image(src="u-fuel_logo.jpg", width=40, height=40, fit=ft.BoxFit.CONTAIN), bgcolor="white", border_radius=8, padding=6, width=40, height=40),
                ft.Text("U-FUEL", size=20, weight=ft.FontWeight.BOLD, color="white")
            ],
            spacing=10
        ),
        padding=ft.Padding.symmetric(horizontal=20, vertical=16),
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

    loading_backend = ft.Container(expand=True, alignment=ft.Alignment.CENTER, content=ft.Column(controls=[ft.ProgressRing(color="white"), ft.Text("Starting backend...", color="white")], horizontal_alignment=ft.CrossAxisAlignment.CENTER))
    page.add(loading_backend)
    page.update()

    if "127.0.0.1" in API_URL or "localhost" in API_URL:
        if not is_backend_running():
            threading.Thread(target=run_backend, daemon=True).start()
            time.sleep(0.5)
        await wait_for_backend()
    else:
        print(f"[mobile] using remote API {API_URL}, skipping local backend start")

    page.controls.clear()
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
    threading.Thread(target=run_backend, daemon=True).start()
    ft.run(main, assets_dir="assets")