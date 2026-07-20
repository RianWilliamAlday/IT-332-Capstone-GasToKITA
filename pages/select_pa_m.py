import flet as ft


def main(page: ft.Page):
    page.title = "U-FUEL"
    page.bgcolor = "#8B0000"
    page.padding = 0
    page.window.width = 360
    page.window.height = 700

    # Header
    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(
                            "Pump",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color="white",
                        ),
                        ft.Text(
                            "Attendant",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color="white",
                        ),
                    ],
                    spacing=0,
                    tight=True,
                ),
                ft.Row(
                    controls=[
                        ft.Text(
                            "U-FUEL",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color="white",
                        ),
                        ft.Container(
                            content=ft.Image(
                                src="u-fuel_logo.jpg",
                                width=55,
                                height=55,
                                fit=ft.BoxFit.CONTAIN,
                            ),
                            bgcolor="#FFFFF",
                            border_radius=8,
                            padding=ft.Padding.all(4),
                            width=55,
                            height=55,
                            alignment=ft.Alignment.CENTER,
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=20, vertical=14),
    )

    def attendant_card(name: str):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.PERSON,
                        size=56,
                        color="white",
                    ),
                    ft.Text(
                        name,
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color="white",
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                tight=True,
            ),
            bgcolor="#8B0000",
            border_radius=16,
            padding=ft.Padding.symmetric(horizontal=20, vertical=20),
            width=180,
            alignment=ft.Alignment.CENTER,
        )

    attendants = ["Pump Attendant 1", "Pump Attendant 2", "Pump Attendant 3"]

    list_view = ft.ListView(
        controls=[
            ft.Container(
                content=attendant_card(name),
                alignment=ft.Alignment.CENTER,
                padding=ft.Padding.symmetric(vertical=8),
            )
            for name in attendants
        ],
        expand=True,
        padding=ft.Padding.symmetric(horizontal=24, vertical=16),
    )

    content_card = ft.Container(
        content=list_view,
        bgcolor="white",
        border_radius=ft.BorderRadius(
            top_left=28,
            top_right=28,
            bottom_left=0,
            bottom_right=0,
        ),
        expand=True,
    )

    footer = ft.Container(
        content=ft.Text(
            "GAStoKITA",
            size=13,
            color="white",
            text_align=ft.TextAlign.CENTER,
        ),
        bgcolor="#8B0000",
        padding=ft.Padding.symmetric(vertical=14),
        alignment=ft.Alignment.CENTER,
    )

    page.add(
        ft.Column(
            controls=[
                header,
                ft.Container(height=10),
                content_card,
                footer,
            ],
            expand=True,
            spacing=0,
        )
    )


ft.run(main)