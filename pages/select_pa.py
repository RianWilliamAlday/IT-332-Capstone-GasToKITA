import flet as ft
from pages.history import TEXT_WHITE
from pages.select import select_transaction
from pages.api_client import get_attendant_names, DEFAULT_ATTENDANTS

RED = "#A61E22"
LIGHT_GRAY = "#E9E9E9"

def pa_selection(page: ft.Page, auth: dict):
    page.title = "Select Pump Attendant"
    page.bgcolor = LIGHT_GRAY
    page.padding = 0

    if not auth.get("access_token") and not auth.get("token"):
        print("[WARN] No token in auth, user might not be logged in")

    def select_attendant(name: str):
        auth["selected_attendant"] = name
        print(f"Selected {name} by: {auth.get('name') or auth.get('user')}")
        page.controls.clear()
        page.add(select_transaction(page, auth))
        page.update()

    async def go_logout(e):
        await page.shared_preferences.remove("gastokita.auth_token")
        await page.shared_preferences.remove("gastokita.user_json")
        auth.clear()
        auth.update({"token": None, "role": None, "user": None})
        page.controls.clear()
        from app import main as app_main
        await app_main(page)
        page.update()

    header = ft.Container(
        bgcolor=RED, height=100, padding=20,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Column(spacing=10, controls=[
                    ft.Text("Cashier", size=28, weight=ft.FontWeight.BOLD, color="white")
                ]),
                ft.Row(spacing=15, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text("U-Fuel", size=28, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Container(width=70, height=70, bgcolor="white", border_radius=12,
                        content=ft.Image(src="u-fuel_logo.jpg", fit=ft.BoxFit.CONTAIN))
                ])
            ]))

    footer = ft.Container(height=80,bgcolor=RED, padding=ft.Padding.symmetric(vertical=14, horizontal=24),content=ft.Row([
                        ft.Container(content=ft.Row([ft.Icon(ft.Icons.LOGOUT, color=TEXT_WHITE, size=16), ft.Text("LOGOUT", color=TEXT_WHITE, size=13, weight=ft.FontWeight.BOLD)], spacing=6), bgcolor="#6B6B6B", border_radius=6, padding=ft.Padding.symmetric(vertical=8, horizontal=14), ink=True, on_click=go_logout)
                        ]
                    )
                )

    def card(title, handler):
        is_selected = auth.get("selected_attendant") == title
        return ft.Container(
            width=240, height=240, bgcolor=RED,
            border_radius=25, padding=15,
            border=ft.Border.all(2, "white") if is_selected else None,
            on_click=handler, ink=True,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(expand=True, bgcolor="white", border_radius=18,
                        alignment=ft.Alignment(0,0),
                        content=ft.Icon(ft.Icons.PERSON, size=80, color=RED)),
                    ft.Text(title, size=22, weight=ft.FontWeight.BOLD, color="white", text_align=ft.TextAlign.CENTER),
                ]))

    attendants = get_attendant_names(auth)

    def make_handler(name):
        return lambda e: select_attendant(name)

    cards_wrap = ft.Row(
        wrap=True,
        spacing=50,
        run_spacing=30,
        alignment=ft.MainAxisAlignment.CENTER,
        controls=[card(name, make_handler(name)) for name in attendants]
    )

    body = ft.Container(
        expand=True, bgcolor="white", alignment=ft.Alignment(0,0),
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Container(height=20),
                ft.Container(content=cards_wrap, padding=20, alignment=ft.Alignment(0, 0))
            ]
        ))

    return ft.Column(spacing=0, expand=True, controls=[header, body, footer])
