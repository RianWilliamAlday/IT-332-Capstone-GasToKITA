import flet as ft

RED = "#A61E22"
LIGHT_GRAY = "#E9E9E9"
CARD_GRAY = "#D9D9D9"
GREEN_BUTTON = "#118C4F"
BLUE_BUTTON = "#0275D8"

def main(page: ft.Page):
    page.title = "GasToKITA - Change Dialog"
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
                    "Cashier",
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

    change_dialog = ft.Container(
        width=500,
        height=380,
        bgcolor=CARD_GRAY,
        border_radius=20,
        border=ft.Border.all(1.5, ft.Colors.BLACK87),
        content=ft.Stack(
            controls=[
                ft.Container(
                    width=420,
                    height=220,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=15,
                    border=ft.Border.all(1.5, ft.Colors.BLACK87),
                    left=40,
                    top=80,
                ),

                ft.Container(
                    width=180,
                    height=75,
                    bgcolor=RED,
                    border_radius=15,
                    left=160,
                    top=2.5,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0,
                        controls=[
                            ft.Text("₱ 0.00", size=24, weight=ft.FontWeight.BOLD, color="white"),
                            ft.Text("CHANGE", size=16, weight=ft.FontWeight.BOLD, color="white"),
                        ]
                    )
                ),
                
                ft.Container(
                    width=110,
                    height=45,
                    bgcolor=GREEN_BUTTON,
                    left=195,
                    top=305,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text("Done", size=20, weight=ft.FontWeight.BOLD, color="white")
                )
            ]
        )
    )

    body_content = ft.Container(
        expand=True,
        bgcolor=ft.Colors.WHITE,
        alignment=ft.Alignment(0, 0),
        content=change_dialog
    )

    page.add(
        ft.Column(
            spacing=0,
            expand=True,
            controls=[
                header,
                body_content,
                footer,
            ],
        )
    )

ft.run(main)