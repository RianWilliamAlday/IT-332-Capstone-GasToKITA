import flet as ft


def main(page: ft.Page):
    page.title = "U-FUEL"
    page.bgcolor = "#8B0000"
    page.padding = ft.Padding.all(0)
    page.window.width = 390
    page.window.height = 844
    page.window.resizable = False

    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Cashier", size=16, weight=ft.FontWeight.BOLD, color="white"),
                    ],
                    spacing=0,
                    tight=True,
                ),
                ft.Row(
                    controls=[
                        ft.Text("U-FUEL", size=16, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Container(
                            content=ft.Image(
                                src="u-fuel_logo.jpg",
                                width=55,
                                height=55,
                                fit=ft.BoxFit.CONTAIN,
                            ),
                            bgcolor="#FFD700",
                            border_radius=ft.BorderRadius(top_left=8, top_right=8, bottom_left=8, bottom_right=8),
                            padding=ft.Padding.all(4),
                            width=40,
                            height=40,
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

    change_box = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    "₱ 0.00",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color="white",
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "CHANGE",
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color="white",
                    text_align=ft.TextAlign.CENTER,
                    style=ft.TextStyle(letter_spacing=1.2),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
            tight=True,
        ),
        bgcolor="#8B0000",
        border_radius=ft.BorderRadius(top_left=10, top_right=10, bottom_left=10, bottom_right=10),
        padding=ft.Padding.symmetric(horizontal=24, vertical=16),
        alignment=ft.Alignment.CENTER,
        width=float("inf"),
    )

    details_box = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("GAS - 50",    size=15, weight=ft.FontWeight.BOLD, color="#8B0000", text_align=ft.TextAlign.CENTER),
                ft.Text("PAY - 100",   size=15, weight=ft.FontWeight.BOLD, color="#8B0000", text_align=ft.TextAlign.CENTER),
                ft.Text("CHANGE - 50", size=15, weight=ft.FontWeight.BOLD, color="#8B0000", text_align=ft.TextAlign.CENTER),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            tight=True,
        ),
        border=ft.Border.all(1.5, "#8B0000"),
        border_radius=ft.BorderRadius(top_left=10, top_right=10, bottom_left=10, bottom_right=10),
        padding=ft.Padding.symmetric(horizontal=24, vertical=24),
        width=float("inf"),
    )

    done_button = ft.Button(
            content="DONE",
            bgcolor="#118C4F",
            color="white",
            height=50,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                text_style=ft.TextStyle(size=14, weight=ft.FontWeight.BOLD, letter_spacing=1.2),
            ),
        )

    print_button = ft.Button(
        content="PRINT RECEIPT",
        bgcolor="#0F3057",
        color="white",
        height=50,
        expand=True,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=12, weight=ft.FontWeight.BOLD, letter_spacing=1.0),
        ),
    )

    outer_container = ft.Container(
        content=ft.Column(
            controls=[
                change_box,
                ft.Container(height=16),
                details_box,
                ft.Container(height=16),
                ft.Row(
                    controls=[done_button, print_button],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            spacing=0,
            tight=True,
        ),
        border=ft.Border.all(1.5, "#8B0000"),
        border_radius=ft.BorderRadius(top_left=12, top_right=12, bottom_left=12, bottom_right=12),
        padding=ft.Padding.all(16),
        width=float("inf"),
    )

    content_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            icon_color="#8B0000",
                            icon_size=24,
                            padding=ft.Padding.all(0),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Container(expand=True),
                outer_container,
                ft.Container(height=20),
                ft.Container(expand=True),
            ],
            spacing=0,
            expand=True,
        ),
        bgcolor="white",
        border_radius=ft.BorderRadius(top_left=28, top_right=28, bottom_left=0, bottom_right=0),
        padding=ft.Padding.symmetric(horizontal=24, vertical=16),
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