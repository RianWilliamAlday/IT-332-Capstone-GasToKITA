import sys
import flet as ft
from pathlib import Path
import httpx

AUTH = {"token": None, "role": None, "user": None}

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent

API_URL = "http://127.0.0.1:8000"
RED = "#A61E22"
LIGHT_GRAY = "#E9E9E9"
CARD_GRAY = "#D9D9D9"

async def main(page: ft.Page):
    page.title = "GasToKITA"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = LIGHT_GRAY
    page.padding = 0
    page.window.maximized = True

    header = ft.Container(bgcolor=RED, height=100, padding=20,
        content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text("GAStoKITA", size=28, weight=ft.FontWeight.BOLD, color="white"),
                ft.Row(spacing=15, controls=[
                    ft.Text("U-Fuel", size=28, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Container(width=70, height=70, bgcolor="white", border_radius=12,
                        content=ft.Image(src="u-fuel_logo.jpg", fit=ft.ImageFit.CONTAIN))
                ])
            ]))

    footer = ft.Container(height=80, bgcolor=RED)

    email_field = ft.TextField(hint_text="Enter your email", keyboard_type=ft.KeyboardType.EMAIL,
        border_radius=25, border_color="black", bgcolor="white", width=330, height=50)
    password_field = ft.TextField(hint_text="Enter your password", password=True,
        can_reveal_password=True, border_radius=25, border_color="black", bgcolor="white",
        width=330, height=50)

    status_text = ft.Text("", color=RED, size=14)

    async def login_employee(e):
        status_text.value = "Connecting..."
        page.update()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    f"{API_URL}/api/auth/employee/login",
                    json={"email": email_field.value.strip(), "password": password_field.value}
                )
            print("RAW:", resp.status_code, resp.text)
            data = resp.json()
            token = data.get("access_token") or data.get("token")
            user = data.get("user", {})
            
            if resp.status_code == 200 and token:
                AUTH["token"] = token
                AUTH["role"] = user.get("role", "EMPLOYEE")
                AUTH["user"] = user
                status_text.value = f"Welcome {user.get('name','')}!"
                page.snack_bar = ft.SnackBar(ft.Text("Login successful"), bgcolor="green")
                page.snack_bar.open = True
                # page.go("/dashboard")  # add when your dashboard is ready
            else:
                status_text.value = f"Login failed: {data.get('detail','Check credentials')}"
        except Exception as ex:
            status_text.value = f"Cannot reach backend: {ex}"
            print("ERROR:", ex)
        page.update()

    login_btn = ft.FilledButton("Login", width=130, height=45, on_click=login_employee,
        style=ft.ButtonStyle(bgcolor=RED, color="white",
            shape=ft.RoundedRectangleBorder(radius=25),
            text_style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD)))

    login_card = ft.Container(width=460, height=400, bgcolor=CARD_GRAY,
        border=ft.Border.all(2, ft.Colors.BLACK), border_radius=25, padding=20,
        content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15,
            controls=[
                ft.Text("Pump Attendant Login", size=28, weight=ft.FontWeight.BOLD),
                ft.Column(spacing=4, controls=[ft.Text("Email:", weight=ft.FontWeight.BOLD), email_field]),
                ft.Column(spacing=4, controls=[ft.Text("Password:", weight=ft.FontWeight.BOLD), password_field]),
                ft.Container(height=5),
                login_btn,
                status_text,
            ]))

    page.add(ft.Column(spacing=0, expand=True, controls=[
        header,
        ft.Container(expand=True, alignment=ft.Alignment.CENTER, content=login_card),
        footer
    ]))

if __name__ == "__main__":
    ft.run(main, assets_dir=str(BASE_DIR))