import subprocess, threading, time, sys, os, json, inspect, flet as ft
from pathlib import Path
import httpx, asyncio, socket
from pages.select_pa import pa_selection

AUTH = {"token": None, "role": None, "user": None}
BASE_DIR = Path(__file__).parent if not getattr(sys, 'frozen', False) else Path(sys._MEIPASS)
API_URL = "http://127.0.0.1:8000"
RED = "#A61E22"

def is_backend_running():
    try:
        with socket.create_connection(("127.0.0.1", 8000), timeout=1): return True
    except: return False

def run_backend():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BASE_DIR)
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=BASE_DIR, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in proc.stdout: print("[backend]", line.strip())

async def wait_for_backend():
    for _ in range(30):
        try:
            async with httpx.AsyncClient() as c:
                await c.get(f"{API_URL}/docs", timeout=1)
                return True
        except: await asyncio.sleep(0.5)
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

async def main(page: ft.Page):
    page.title = "GAStoKITA"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window.maximized = True

    loading = ft.Container(expand=True, alignment=ft.Alignment.CENTER, content=ft.Text("Starting backend...", size=18))
    page.add(loading)
    page.update()
    await wait_for_backend()
    page.controls.clear()

    try:
        token = await page.shared_preferences.get("gastokita.auth_token")
        if token:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{API_URL}/api/auth/me", headers={"Authorization": f"Bearer {token}"})
                if resp.status_code == 200:
                    AUTH["token"] = token
                    AUTH["user"] = resp.json()
                    AUTH["role"] = resp.json().get("role")
                    page.controls.clear()
                    page.add(pa_selection(page, AUTH))
                    page.update()
                    return
            await page.shared_preferences.remove("gastokita.auth_token")
    except Exception as e:
        print(f"[AUTO-LOGIN] Error: {e}")

    is_signup_mode = False

    title_text = ft.Text("Login", size=24, weight=ft.FontWeight.BOLD, color="white")
    login_btn_text = ft.Text("Login", size=16, weight=ft.FontWeight.BOLD, color="white")
    toggle_text = ft.Text("Don't have an account? Sign Up", weight=ft.FontWeight.BOLD, color="#1877F2", size=13)
    status_text = ft.Text("", color="white", size=14)

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
        visible=False,
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
            title_text.value = "Sign Up"
            login_btn_text.value = "Create Account"
            toggle_text.value = "Already have an account? Login"
            name_field.visible = True
            login_card.height = 510

    async def login_google(e):
        status_text.color = "white"
        status_text.value = "Connecting to Google..."
        page.update()
        try:
            data = await google_sign_in(page, API_URL)
        except Exception as ex:
            status_text.color = "red"
            status_text.value = f"Google login failed: {ex}"
            page.update()
            return

        token = data.get("access_token")
        user_data = data.get("user") or {}

        if token and user_data:
            AUTH["token"] = token
            AUTH["user"] = user_data
            AUTH["role"] = user_data.get("role", "EMPLOYEE")
            await page.shared_preferences.set("gastokita.auth_token", token)
            await page.shared_preferences.set("gastokita.user_json", json.dumps(user_data))

            page.controls.clear()
            page.add(pa_selection(page, AUTH))
            page.update()
            return

        google_email = data.get("email") or user_data.get("email", "")
        google_name = data.get("name") or user_data.get("name", "")

        switch_to_signup()
        if google_name:
            name_field.value = google_name
        if google_email:
            email_field.value = google_email

        status_text.color = "green"
        status_text.value = "Google profile loaded! Enter a password to complete registration."
        page.update()

    async def handle_auth_action(e):
        status_text.color = "white"
        status_text.value = "Processing..."
        page.update()

        email_val = email_field.value.strip() if email_field.value else ""
        pass_val = password_field.value if password_field.value else ""
        name_val = name_field.value.strip() if name_field.value else ""

        if not email_val or not pass_val or (is_signup_mode and not name_val):
            status_text.color = "red"
            status_text.value = "Please complete all required fields"
            page.update()
            return

        endpoint = f"{API_URL}/api/auth/register" if is_signup_mode else f"{API_URL}/api/auth/employee/login"
        payload = {"email": email_val, "password": pass_val}
        if is_signup_mode:
            payload["name"] = name_val
            payload["role"] = "EMPLOYEE"

        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                resp = await client.post(endpoint, json=payload)
                if resp.status_code != 200:
                    status_text.color = "red"
                    status_text.value = resp.json().get("detail", "Authentication failed")
                    page.update()
                    return

                data = resp.json()
                token = data.get("access_token") or data.get("token")
                user_data = data.get("user") or {}

                AUTH["token"] = token
                AUTH["user"] = user_data
                AUTH["role"] = user_data.get("role", "EMPLOYEE")
                await page.shared_preferences.set("gastokita.auth_token", token)
                await page.shared_preferences.set("gastokita.user_json", json.dumps(user_data))

                page.controls.clear()
                page.add(pa_selection(page, AUTH))
                page.update()
            except Exception as ex:
                status_text.color = "red"
                status_text.value = f"Error: {ex}"
                page.update()

    def toggle_mode(e):
        nonlocal is_signup_mode
        is_signup_mode = not is_signup_mode
        title_text.value = "Sign Up" if is_signup_mode else "Login"
        login_btn_text.value = "Create Account" if is_signup_mode else "Login"
        toggle_text.value = "Already have an account? Login" if is_signup_mode else "Don't have an account? Sign Up"
        name_field.visible = is_signup_mode
        login_card.height = 510 if is_signup_mode else 440
        status_text.value = ""
        page.update()

    async def login_google(e):
        status_text.color = "white"
        status_text.value = "Complete sign-in in your browser..."
        page.update()
        try:
            data = await google_sign_in(page, API_URL)
        except Exception as ex:
            status_text.color = "red"
            status_text.value = f"Google login failed: {ex}"
            page.update()
            return
    
        token = data["access_token"]
        user_data = data.get("user") or {}
        AUTH["token"] = token
        AUTH["user"] = user_data
        AUTH["role"] = user_data.get("role", "EMPLOYEE")
        await page.shared_preferences.set("gastokita.auth_token", token)
        await page.shared_preferences.set("gastokita.user_json", json.dumps(user_data))
        page.controls.clear()
        page.add(pa_selection(page, AUTH))
        page.update()

    name_field.on_submit = handle_auth_action
    password_field.on_submit = handle_auth_action

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
        on_submit=login_employee
    )
    
    status_text = ft.Text("", color="white", size=14)
    header = ft.Container(bgcolor=RED, height=100, padding=20, content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("GAStoKITA", size=28, weight=ft.FontWeight.BOLD, color="white"), ft.Row(spacing=15, controls=[ft.Text("U-Fuel", size=28, weight=ft.FontWeight.BOLD, color="white"), ft.Container(width=70, height=70, bgcolor="white", border_radius=12, content=ft.Image(src="u-fuel_logo.jpg", fit=ft.BoxFit.CONTAIN))])]))
    footer = ft.Container(height=80, bgcolor=RED)

    login_btn = ft.Container(
        width=330,
        height=48,
        bgcolor=RED,
        border_radius=12,
        ink=True,
        on_click=handle_auth_action,
        alignment=ft.Alignment.CENTER,
        content=login_btn_text,
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
        shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.25, ft.Colors.BLACK)), 
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            spacing=14, 
            controls=[
                title_text,
                name_field,
                email_field, 
                password_field, 
                login_btn, 
                ft.GestureDetector(content=toggle_text, on_tap=toggle_mode),
                ft.Row([ft.Container(expand=True, height=1, bgcolor="white"), ft.Text(" OR ", color="white"), ft.Container(expand=True, height=1, bgcolor="white")], alignment=ft.MainAxisAlignment.CENTER, width=330),
                google_btn,
                status_text
            ]
        )
    )
    
    page_content = ft.Column(spacing=0, expand=True, controls=[header, ft.Container(expand=True, alignment=ft.Alignment.CENTER, content=login_card), footer])
    page.add(ft.Stack(expand=True, fit=ft.StackFit.EXPAND, controls=[ft.Container(expand=True, image=ft.DecorationImage(src="background.jpg", fit=ft.BoxFit.COVER)), ft.Container(expand=True, bgcolor=ft.Colors.with_opacity(0.30, ft.Colors.BLACK)), page_content]))
    page.update()

if __name__ == "__main__":
    if not is_backend_running():
        threading.Thread(target=run_backend, daemon=True).start()
        time.sleep(0.5)
    ft.run(main, assets_dir=str(BASE_DIR))