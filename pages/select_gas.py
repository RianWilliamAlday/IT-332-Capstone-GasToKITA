import flet as ft

RED = "#A61E22"
LIGHT_GRAY = "#E9E9E9"
COLOR_REGULAR = "#0CA940"
COLOR_PREMIUM = "#E3242B"
COLOR_DIESEL = "#F5C243"
BAR_GREEN = "#12B347"
BAR_YELLOW = "#F4B400"
BAR_RED = "#E3242B"

def build_pump_page(page: ft.Page, auth: dict):
    page.title = "Gasoline Selector"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = LIGHT_GRAY
    page.padding = 0

    def on_fuel_click(fuel_name: str):
        print(f"{fuel_name} selected by {auth.get('selected_attendant')}")
        page.snack_bar = ft.SnackBar(ft.Text(f"Selected: {fuel_name}"))
        page.snack_bar.open = True
        page.update()

    def go_back(e):
        from pages.select import select_transaction
        page.controls.clear()
        page.add(select_transaction(page, auth))
        page.update()

    header = ft.Container(
        bgcolor=RED, height=100, padding=20,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.TextButton("← Back", style=ft.ButtonStyle(color="white"), on_click=go_back),
                    ft.Text("Cashier", size=28, weight=ft.FontWeight.BOLD, color="white"),
                ]),
                ft.Row(spacing=15, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text("U-Fuel", size=28, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Container(width=70, height=70, bgcolor="white", border_radius=12,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Image(src="u-fuel_logo.jpg", fit=ft.BoxFit.CONTAIN)),
                ]),
            ],
        ),
    )

    footer = ft.Container(height=80, bgcolor=RED)

    text_shadow = ft.TextStyle(
        shadow=ft.BoxShadow(color=ft.Colors.BLACK38, offset=ft.Offset(1, 1), blur_radius=2)
    )

    def create_fuel_card(title, percentage, card_color, bar_color):
        return ft.Container(
            width=260, height=140, bgcolor=card_color, border_radius=15,
            border=ft.Border.all(1, ft.Colors.BLACK87), padding=20, ink=True,
            on_click=lambda e, t=title: on_fuel_click(t),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.BLACK26, offset=ft.Offset(0, 3)),
            content=ft.Column(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Container(alignment=ft.Alignment(0, 0),
                        content=ft.Text(title, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, style=text_shadow)),
                    ft.Column(spacing=5, controls=[
                        ft.Container(alignment=ft.Alignment(0, 0),
                            content=ft.Text(f"{percentage}%", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, style=text_shadow)),
                        ft.Stack(controls=[
                            ft.Container(height=16, width=220, bgcolor=ft.Colors.WHITE, border_radius=10, border=ft.Border.all(0.5, ft.Colors.BLACK26)),
                            ft.Container(height=16, width=220 * (percentage / 100), bgcolor=bar_color, border_radius=10,
                                shadow=ft.BoxShadow(spread_radius=0, blur_radius=3, color=ft.Colors.BLACK38, offset=ft.Offset(0, 2)))
                        ])
                    ])
                ]
            )
        )

    body_content = ft.Container(
        expand=True, bgcolor=ft.Colors.WHITE, alignment=ft.Alignment(0, 0),
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=40,
            controls=[
                ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=40, controls=[
                    create_fuel_card("Regular 1", 100, COLOR_REGULAR, BAR_GREEN),
                    create_fuel_card("Premium 1", 50, COLOR_PREMIUM, BAR_YELLOW),
                    create_fuel_card("Diesel 1", 20, COLOR_DIESEL, BAR_RED),
                ]),
                ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=40, controls=[
                    create_fuel_card("Regular 2", 100, COLOR_REGULAR, BAR_GREEN),
                    create_fuel_card("Premium 2", 50, COLOR_PREMIUM, BAR_YELLOW),
                    create_fuel_card("Diesel 2", 20, COLOR_DIESEL, BAR_RED),
                ])
            ]
        )
    )

    return ft.Column(spacing=0, expand=True, controls=[header, body_content, footer])
