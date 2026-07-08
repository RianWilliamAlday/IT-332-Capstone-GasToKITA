import flet as ft

RED = "#A61E22"
LIGHT_GRAY = "#E9E9E9"
CARD_GRAY = "#D9D9D9"
WHITE = "white"

def oil_card(label: str, on_click):
    """Returns a single OIL card widget"""
    return ft.Container(
        width=220,
        height=160,
        bgcolor=RED,
        border_radius=16,
        padding=8,
        on_click=lambda e, l=label: on_click(l),
        ink=True,
        content=ft.Column(
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    expand=True,
                    bgcolor=WHITE,
                    border_radius=12,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(
                        ft.Icons.WATER_DROP_OUTLINED,
                        size=70,
                        color="black",
                    ),
                ),
                ft.Container(
                    height=40,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text(
                        label,
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=WHITE,
                    ),
                ),
            ],
        ),
    )

def main(page: ft.Page):
    page.title = "GasToKITA"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = LIGHT_GRAY
    page.padding = 0
    page.window.maximized = True
    
    def handle_oil_click(oil_name: str):
        page.snack_bar = ft.SnackBar(ft.Text(f"Selected: {oil_name}"))
        page.snack_bar.open = True
        page.update()

    header = ft.Container(
        bgcolor=RED,
        height=100,
        padding=ft.Padding.symmetric(horizontal=30),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(
                            "Pump Attendant",
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color=WHITE,
                        ),
                        ft.Text("⛽", size=28)
                    ],
                ),
                ft.Row(
                    spacing=15,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(
                            "U-Fuel",
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color=WHITE,
                        ),
                        ft.Container(
                            width=70,
                            height=70,
                            bgcolor=WHITE,
                            border_radius=12,
                            padding=5,
                            content=ft.Image(
                                src="u-fuel_logo.jpg",
                                fit=ft.BoxFit.CONTAIN,
                            ),
                        ),
                    ],
                ),
            ],
        ),
    )

    oil_grid = ft.ResponsiveRow(
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=30,
        run_spacing=30,
        controls=[
            ft.Container(
                content=oil_card(f"OIL {i}", handle_oil_click),
                col={"sm": 12, "md": 4, "lg": 4}
            )
            for i in range(1, 7)
        ],
    )

    main_content = ft.Container(
        expand=True,
        bgcolor=WHITE,
        alignment=ft.Alignment(0, -0.2),
        padding=40,
        content=oil_grid,
    )

    footer = ft.Container(
        height=80,
        bgcolor=RED,
    )

    page.add(
        ft.Column(
            spacing=0,
            expand=True,
            controls=[
                header,
                main_content,
                footer,
            ],
        )
    )

ft.run(main, assets_dir="assets")