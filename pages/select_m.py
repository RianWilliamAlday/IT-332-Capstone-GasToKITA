import flet as ft

MOBILE_RED = "#8B0000"

def build_transaction_page_mobile(page: ft.Page, auth: dict):
    page.title = "Transaction Selection"
    page.bgcolor = MOBILE_RED
    page.padding = 0
    page.window.width = 390
    page.window.height = 844
    page.window.resizable = False

    def go_back(e):
        from pages.select_pa_m import build_pa_page_mobile
        page.controls.clear()
        page.add(build_pa_page_mobile(page, auth))
        page.update()

    def on_pump(e):
        from pages.select_gas_m import build_gas_page_mobile
        page.controls.clear()
        page.add(build_gas_page_mobile(page, auth))
        page.update()

    def on_oil(e):
        from pages.select_oil_m import build_oil_page_mobile
        page.controls.clear()
        page.add(build_oil_page_mobile(page, auth))
        page.update()

    def on_multi(e):
        from pages.select_multi_m import build_multi_page_mobile
        page.controls.clear()
        page.add(build_multi_page_mobile(page, auth))
        page.update()

    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Column(controls=[ft.Text("Pump", size=16, weight=ft.FontWeight.BOLD, color="white"), ft.Text("Attendant", size=16, weight=ft.FontWeight.BOLD, color="white")], spacing=0),
                ft.Row(controls=[ft.Text("U-FUEL", size=16, weight=ft.FontWeight.BOLD, color="white"), ft.Container(content=ft.Image(src="u-fuel_logo.jpg", width=40, height=40, fit=ft.BoxFit.CONTAIN), bgcolor="white", border_radius=8, padding=4, width=40, height=40)], spacing=8),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.Padding.symmetric(horizontal=20, vertical=14),
    )

    def menu_card(icon, label, handler):
        return ft.Container(
            content=ft.Column(controls=[ft.Icon(icon, size=64, color="white"), ft.Text(label, size=14, weight=ft.FontWeight.BOLD, color="white")], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            bgcolor=MOBILE_RED, border_radius=16, padding=ft.Padding.symmetric(horizontal=20, vertical=24), width=180, ink=True, on_click=handler,
        )

    content_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=MOBILE_RED, on_click=go_back)
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Container(expand=True),
                ft.Container(content=menu_card(ft.Icons.LOCAL_GAS_STATION, "PUMP GAS", on_pump), alignment=ft.Alignment.CENTER),
                ft.Container(height=16),
                ft.Container(content=menu_card(ft.Icons.WATER_DROP, "OILS", on_oil), alignment=ft.Alignment.CENTER),
                ft.Container(expand=True),
                ft.Container(content=menu_card(ft.Icons.LOCAL_GAS_STATION, "Multi Sale", on_multi), alignment=ft.Alignment.CENTER),
                ft.Container(height=16),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor="white", border_radius=ft.BorderRadius(top_left=28, top_right=28, bottom_left=0, bottom_right=0), expand=True, padding=ft.Padding.all(20)
    )

    footer = ft.Container(content=ft.Text("GAStoKITA", size=13, color="white", text_align=ft.TextAlign.CENTER), bgcolor=MOBILE_RED, padding=ft.Padding.symmetric(vertical=14), alignment=ft.Alignment.CENTER)

    return ft.SafeArea(
        content=ft.Column(controls=[header, ft.Container(height=10), content_card, footer], expand=True, spacing=0),
        expand=True,
    )