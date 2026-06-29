import flet as ft

RED = "#A61E22"
LIGHT_GRAY = "#E9E9E9"
CARD_GRAY = "#D9D9D9"


def main(page: ft.Page):
    page.title = "Transaction Selection"
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

    def create_menu_card(title: str):
        return ft.Container(
            width=240,
            height=240,
            bgcolor=RED,
            border_radius=25,
            padding=15,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
                controls=[
                    # White inner display frame
                    ft.Container(
                        expand=True,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=18,
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Container(
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text(
                            title, 
                            size=22, 
                            weight=ft.FontWeight.BOLD, 
                            color=ft.Colors.WHITE
                        )
                    )
                ]
            )
        )

    body = ft.Container(
        expand=True,
        alignment=ft.Alignment(0, 0),
        bgcolor=ft.Colors.WHITE,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=50,
            controls=[
                create_menu_card("Pump Gas"),
                create_menu_card("Oils"),
            ]
        )
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
                    content=body
                ),

                footer,
            ],
        )
    )


ft.run(main)