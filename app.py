import flet as ft

RED = "#A61E22"
LIGHT_GRAY = "#E9E9E9"
CARD_GRAY = "#D9D9D9"


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
                                src="ufuel_logo.png",  # Replace with your logo
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

    page.add(
        ft.Column(
            spacing=0,
            expand=True,
            controls=[
                header,

                ft.Container(
                    expand=True,
                    alignment=ft.Alignment(0, 0),
                ),

                footer,
            ],
        )
    )


ft.run(main)