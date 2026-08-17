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

    amount_display = ft.Container(
        content=ft.Text(
            "₱ 0.00",
            size=20,
            weight=ft.FontWeight.BOLD,
            color="white",
            text_align=ft.TextAlign.CENTER,
        ),
        bgcolor="#8B0000",
        border_radius=ft.BorderRadius(top_left=10, top_right=10, bottom_left=10, bottom_right=10),
        padding=ft.Padding.symmetric(horizontal=20, vertical=14),
        alignment=ft.Alignment.CENTER,
        width=float("inf"),
    )

    def amount_btn(label: str):
        return ft.Button(
            content=label,
            bgcolor="#8B0000",
            color="white",
            expand=True,
            height=48,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                text_style=ft.TextStyle(size=15, weight=ft.FontWeight.BOLD),
            ),
        )

    denominations = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]

    denom_rows = []
    groups = [denominations[i:i+3] for i in range(0, len(denominations), 3)]
    for group in groups:
        row_controls = []
        for val in group:
            row_controls.append(amount_btn(str(val)))
        denom_rows.append(
            ft.Row(controls=row_controls, spacing=10, expand=False)
        )

    exact_button = ft.Button(
        content="EXACT AMOUNT",
        bgcolor="#8B0000",
        color="white",
        width=float("inf"),
        height=50,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=14, weight=ft.FontWeight.BOLD, letter_spacing=1.2),
        ),
    )

    submit_button = ft.Button(
        content="SUBMIT",
        bgcolor="#006400",
        color="white",
        width=float("inf"),
        height=50,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(size=14, weight=ft.FontWeight.BOLD, letter_spacing=1.2),
        ),
    )

    outer_container = ft.Container(
        content=ft.Column(
            controls=[
                amount_display,
                ft.Container(height=16),
                *denom_rows,
                ft.Container(height=10),
                exact_button,
                ft.Container(height=10),
                submit_button
            ],
            spacing=6,
            tight=True,
        ),
        border=ft.Border.all(1.5, "#8B0000"),
        border_radius=ft.BorderRadius(top_left=12, top_right=12, bottom_left=12, bottom_right=12),
        padding=ft.Padding.all(16),
        width=float("inf"),
    )

    back_button = ft.Container(
        content=ft.Icon(ft.Icons.ARROW_BACK, color="#8B0000", size=24),
        padding=ft.Padding.only(left=4, top=4, bottom=8),
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
                ft.Container(height=16),
                outer_container,
            ],
            spacing=10,
            scroll=ft.ScrollMode.ADAPTIVE,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor="white",
        border_radius=ft.BorderRadius(top_left=28, top_right=28, bottom_left=0, bottom_right=0),
        padding=ft.Padding.symmetric(horizontal=24, vertical=20),
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