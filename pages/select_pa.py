import flet as ft
from pages.select import select_transaction

RED = "#A61E22"
LIGHT_GRAY = "#E9E9E9"

DEFAULT_ATTENDANTS = ["Attendant 1", "Attendant 2", "Attendant 3"]

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

    header = ft.Container(
        bgcolor=RED, height=100, padding=20,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Column(spacing=0, controls=[
                    ft.Text("GAStoKITA", size=28, weight=ft.FontWeight.BOLD, color="white")
                ]),
                ft.Row(spacing=15, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text("U-Fuel", size=28, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Container(width=70, height=70, bgcolor="white", border_radius=12,
                        content=ft.Image(src="u-fuel_logo.jpg", fit=ft.BoxFit.CONTAIN))
                ])
            ]))

    footer = ft.Container(height=80, bgcolor=RED)

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
                    ft.Text(title, size=22, weight=ft.FontWeight.BOLD, color="white"),
                ]))

    attendants = DEFAULT_ATTENDANTS

    def make_handler(name):
        return lambda e: select_attendant(name)

    body = ft.Container(
        expand=True, bgcolor="white", alignment=ft.Alignment(0,0),
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Container(height=20),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER, spacing=50,
                    controls=[card(name, make_handler(name)) for name in attendants]
                )
            ]
        ))

    return ft.Column(spacing=0, expand=True, controls=[header, body, footer])