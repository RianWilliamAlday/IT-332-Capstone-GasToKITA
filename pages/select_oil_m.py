import flet as ft


def main(page: ft.Page):
    page.title = "U-FUEL"
    page.bgcolor = "#8B0000"
    page.padding = ft.Padding.all(0)
    page.window.width = 390
    page.window.height = 844

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

    def oil_card(label: str):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.WATER_DROP_OUTLINED, size=64, color="#111111"),
                    ft.Text(
                        label,
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color="#8B0000",
                        text_align=ft.TextAlign.CENTER,
                        style=ft.TextStyle(letter_spacing=1.0),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                tight=True,
            ),
            border=ft.Border.all(1.5, "#8B0000"),
            border_radius=ft.BorderRadius(top_left=12, top_right=12, bottom_left=12, bottom_right=12),
            padding=ft.Padding.symmetric(horizontal=12, vertical=20),
            bgcolor="white",
            expand=True,
            alignment=ft.Alignment.CENTER,
        )

    oils = ["OIL 1", "OIL 2", "OIL 3", "OIL 4", "OIL 5", "OIL 6"]

    rows = []
    for i in range(0, len(oils), 2):
        left = oils[i]
        right = oils[i + 1] if i + 1 < len(oils) else None
        row_controls = [oil_card(left)]
        if right:
            row_controls.append(ft.Container(width=12))
            row_controls.append(oil_card(right))
        rows.append(ft.Row(controls=row_controls, spacing=0))
        rows.append(ft.Container(height=12))

    back_button = ft.Container(
        content=ft.Icon(ft.Icons.ARROW_BACK, color="#8B0000", size=24),
        padding=ft.Padding.only(left=16, top=12, bottom=4),
    )

    content_card = ft.Container(
        content=ft.Column(
            controls=[
                back_button,
                ft.Container(height=8),
                ft.Container(
                    content=ft.Column(controls=rows, spacing=0),
                    padding=ft.Padding.symmetric(horizontal=20),
                ),
            ],
            spacing=0,
            scroll=ft.ScrollMode.ADAPTIVE,
        ),
        bgcolor="white",
        border_radius=ft.BorderRadius(top_left=28, top_right=28, bottom_left=0, bottom_right=0),
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