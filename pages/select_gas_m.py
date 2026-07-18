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
                        ft.Text("Pump", size=16, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Text("Attendant", size=16, weight=ft.FontWeight.BOLD, color="white"),
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
                            bgcolor="#FFFFFFF",
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

    def pump_card(percent: str, label: str, color: str):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        percent,
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color="white",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=8),
                    ft.Text(
                        label,
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color="white",
                        text_align=ft.TextAlign.CENTER,
                        style=ft.TextStyle(letter_spacing=1.0),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=0,
                tight=True,
            ),
            bgcolor=color,
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=12, vertical=20),
            expand=True,
            alignment=ft.Alignment.CENTER,
        )

    pumps = [
        ("100%", "REGULAR 1", "#2E7D32"),
        ("100%", "REGULAR 2", "#2E7D32"),
        ("50%",  "PREMIUM 1", "#8B0000"),
        ("50%",  "PREMIUM 2", "#8B0000"),
        ("20%",  "DIESEL 1",  "#F9A825"),
        ("20%",  "DIESEL 2",  "#F9A825"),
    ]

    rows = []
    for i in range(0, len(pumps), 2):
        left = pumps[i]
        right = pumps[i + 1] if i + 1 < len(pumps) else None
        row_controls = [pump_card(*left)]
        if right:
            row_controls.append(ft.Container(width=12))
            row_controls.append(pump_card(*right))
        rows.append(
            ft.Row(controls=row_controls, spacing=0)
        )
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


ft.app(main)