import flet as ft
from pages.select import select_transaction

RED = "#A61E22"
LIGHT_GRAY = "#E9E9E9"

def pa_selection(page: ft.Page, auth: dict):
    page.title = "Select Pump Attendant"
    page.bgcolor = LIGHT_GRAY

    def select_attendant(name: str):
        auth["selected_attendant"] = name
        print(f"Selected {name} by:", auth.get("user"))
        page.controls.clear()
        page.add(select_transaction(page, auth))
        page.update()

    def on_1(e): select_attendant("Attendant 1")
    def on_2(e): select_attendant("Attendant 2")
    def on_3(e): select_attendant("Attendant 3")

    header = ft.Container(
        bgcolor=RED, height=100, padding=20,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("GAStoKITA", size=28, weight=ft.FontWeight.BOLD, color="white"),
                ft.Row(spacing=15, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text("U-Fuel", size=28, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Container(width=70, height=70, bgcolor="white", border_radius=12,
                        content=ft.Image(src="u-fuel_logo.jpg", fit=ft.BoxFit.CONTAIN))
                ])
            ]))

    footer = ft.Container(height=80, bgcolor=RED)

    def card(title, handler):
        return ft.Container(
            width=240, height=240, bgcolor=RED, border_radius=25, padding=15,
            on_click=handler, ink=True,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(expand=True, bgcolor="white", border_radius=18),
                    ft.Text(title, size=22, weight=ft.FontWeight.BOLD, color="white")
                ]))

    body = ft.Container(
        expand=True, bgcolor="white", alignment=ft.Alignment(0,0),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER, spacing=50,
            controls=[card("Attendant 1", on_1), card("Attendant 2", on_2), card("Attendant 3", on_3)]
        ))

    return ft.Column(spacing=0, expand=True, controls=[header, body, footer])