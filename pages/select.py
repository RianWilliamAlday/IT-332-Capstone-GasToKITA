import flet as ft
from pages.select_oil import build_oil_page
from pages.select_gas import build_pump_page
from pages.history import TEXT_WHITE

RED = "#A61E22"
LIGHT_GRAY = "#E9E9E9"

def select_transaction(page: ft.Page, auth: dict):
    page.title = "Transaction Selection"
    page.bgcolor = LIGHT_GRAY

    async def go_logout(e):
            await page.shared_preferences.remove("gastokita.auth_token")
            await page.shared_preferences.remove("gastokita.user_json")
        
            auth.clear()
            auth.update({"token": None, "role": None, "user": None})
        
            page.controls.clear()
            from app import main as app_main
            await app_main(page)
            page.update()

    def go_back(e):
                from pages.select_pa import pa_selection
                page.controls.clear()
                page.add(pa_selection(page, auth))
                page.update()
    
    header = ft.Container(
                bgcolor=RED, height=100, padding=20,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Row(spacing=10, controls=[
                            ft.TextButton("← Back", style=ft.ButtonStyle(color="white"), on_click=go_back),
                            ft.Text("Cashier", size=28, weight=ft.FontWeight.BOLD, color="white"),
                        ]),
                        ft.Row(spacing=15, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                            ft.Text("U-Fuel", size=28, weight=ft.FontWeight.BOLD, color="white"),
                            ft.Container(width=70, height=70, bgcolor="white", border_radius=12,
                                content=ft.Image(src="u-fuel_logo.jpg", fit=ft.BoxFit.CONTAIN)),
                        ]),
                    ],
                ),
            )
    footer = ft.Container(height=80,bgcolor=RED, padding=ft.Padding.symmetric(vertical=14, horizontal=24),content=ft.Row([
                            ft.Container(content=ft.Row([ft.Icon(ft.Icons.LOGOUT, color=TEXT_WHITE, size=16), ft.Text("LOGOUT", color=TEXT_WHITE, size=13, weight=ft.FontWeight.BOLD)], spacing=6), bgcolor="#6B6B6B", border_radius=6, padding=ft.Padding.symmetric(vertical=8, horizontal=14), ink=True, on_click=go_logout)
                            ]
                        )
                    )

    def on_pump(e):
        print("Pump Gas clicked by:", auth.get("user"), "Attendant:", auth.get("selected_attendant"))
        page.controls.clear()
        page.add(build_pump_page(page, auth))
        page.update()

    def on_oils(e):
        print("Oils clicked by:", auth.get("user"), "Attendant:", auth.get("selected_attendant"))
        page.controls.clear()
        page.add(build_oil_page(page, auth))
        page.update()

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
            controls=[card("Pump Gas", on_pump), card("Oils", on_oils)]
        ))

    return ft.Column(spacing=0, expand=True, controls=[header, body, footer])
