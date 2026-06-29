import flet as ft

RED = "#A61E22"
LIGHT_GRAY = "#E9E9E9"
CARD_GRAY = "#D9D9D9"
NAVY_COLOR = "#0F3057"
GREEN_COLOR = "#006400"


def main(page: ft.Page):
    page.title = "GasToKITA"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = LIGHT_GRAY
    page.padding = 0
    page.window.maximized = True

    header = ft.Container(
        bgcolor=RED,
        height=100,
        padding=20,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    "GAStoKITA",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color="white",
                ),

                ft.Row(
                    spacing=15,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(
                            "U-Fuel",
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color="white",
                        ),

                        ft.Container(
                            width=70,
                            height=70,
                            bgcolor="white",
                            border_radius=12,
                            alignment=ft.Alignment(0, 0),
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

    footer = ft.Container(
        height=80,
        bgcolor=RED,
    )
    
    def create_value_btn(value: str):
        return ft.Container(
            width=115,
            height=48,
            bgcolor=RED,
            border_radius=18,
            alignment=ft.Alignment(0, 0),
            content=ft.Text(value, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
        )

    keypad_panel = ft.Container(
        height=380,
        width=780,
        bgcolor=LIGHT_GRAY,
        border_radius=20,
        border=ft.Border.all(width=1.5, color=ft.Colors.BLACK),
        padding=20,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=14,
            controls=[
                ft.Container(
                    width=185,
                    height=50,
                    bgcolor=RED,
                    border_radius=16,
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=35,
                    controls=[
                        create_value_btn("50"),
                        create_value_btn("100"),
                        create_value_btn("200"),
                        create_value_btn("300"),
                    ]
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=35,
                    controls=[
                        create_value_btn("400"),
                        create_value_btn("500"),
                        create_value_btn("600"),
                        create_value_btn("700"),
                    ]
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=35,
                    controls=[
                        create_value_btn("800"),
                        create_value_btn("900"),
                        create_value_btn("1000"),
                    ]
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Container(
                            width=150,
                            height=48,
                            bgcolor=NAVY_COLOR,
                            border_radius=4,
                            alignment=ft.Alignment(0, 0),
                            content=ft.Text("Back", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ),
                        ft.Container(
                            width=220,
                            height=48,
                            bgcolor=RED,
                            border_radius=18,
                            alignment=ft.Alignment(0, 0),
                            content=ft.Text("EXACT AMOUNT", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ),
                        ft.Container(
                            width=150,
                            height=48,
                            bgcolor=GREEN_COLOR,
                            border_radius=4,
                            alignment=ft.Alignment(0, 0),
                            content=ft.Text("Submit", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                        ),
                    ]
                )
            ]
        )
    )

    body = ft.Container(
        expand=True,
        alignment=ft.Alignment(0, 0),
        bgcolor=ft.Colors.WHITE,
        content=keypad_panel
    )
    
    page.add(
        ft.Column(
            spacing=0,
            expand=True,
            controls=[
                header,
                body,
                footer,
            ],
        )
    )


ft.run(main)