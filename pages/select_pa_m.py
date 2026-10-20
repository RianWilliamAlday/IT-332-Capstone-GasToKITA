import flet as ft
from pages.api_client import get_attendant_names, DEFAULT_ATTENDANTS
from pages.sidebar_m import Sidebar

RED = "#A61E22"
MOBILE_RED = "#8B0000"

def build_pa_page_mobile(page: ft.Page, auth: dict):
    page.title = "Select Attendant"
    page.bgcolor = MOBILE_RED
    page.padding = 0
    page.window.width = 390
    page.window.height = 844
    page.window.resizable = False

    sidebar = Sidebar(page, auth, active="pos")

    def select_attendant(name: str):
        auth["selected_attendant"] = name
        print(f"Selected {name}")
        from pages.select_multi_m import build_multi_page_mobile
        page.controls.clear()
        page.add(build_multi_page_mobile(page, auth))
        page.update()

    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        sidebar.menu_button(),
                        ft.Column(controls=[ft.Text("Cashier", size=16, weight=ft.FontWeight.BOLD, color="white")], spacing=0),
                    ],
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(controls=[ft.Text("U-FUEL", size=16, weight=ft.FontWeight.BOLD, color="white"), ft.Container(content=ft.Image(src="u-fuel_logo.jpg", width=40, height=40, fit=ft.BoxFit.CONTAIN), bgcolor="white", border_radius=8, padding=4, width=40, height=40)], spacing=8),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.only(left=8, right=20, top=10, bottom=10),
    )

    def attendant_card(name: str):
        is_selected = auth.get("selected_attendant") == name
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.PERSON, size=56, color="white"),
                    ft.Text(name, size=13, weight=ft.FontWeight.BOLD, color="white", text_align=ft.TextAlign.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            bgcolor=MOBILE_RED,
            border_radius=16,
            border=ft.Border.all(2, "white") if is_selected else None,
            padding=ft.Padding.symmetric(horizontal=20, vertical=20),
            width=180,
            ink=True,
            on_click=lambda e, n=name: select_attendant(n),
        )

    attendants = get_attendant_names(auth)
    content = ft.Column(
        controls=[
            ft.Container(content=attendant_card(name), alignment=ft.Alignment.CENTER, padding=ft.Padding.symmetric(vertical=8))
            for name in attendants
        ],
        expand=True,
        scroll=ft.ScrollMode.ADAPTIVE,
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    content_card = ft.Container(content=content, bgcolor="white", border_radius=ft.BorderRadius(top_left=28, top_right=28, bottom_left=0, bottom_right=0), expand=True, padding=ft.Padding.symmetric(horizontal=24, vertical=16))

    footer = ft.Container(content=ft.Text("GAStoKITA", size=13, color="white", text_align=ft.TextAlign.CENTER), bgcolor=MOBILE_RED, padding=ft.Padding.symmetric(vertical=14), alignment=ft.Alignment.CENTER)

    return ft.SafeArea(
        content=sidebar.wrap(ft.Column(controls=[header, ft.Container(height=10), content_card, footer], expand=True, spacing=0)),
        expand=True,
    )