import flet as ft

RED = "#A61E22"
CARD_GRAY = "#D9D9D9"
GREEN = "#43A047"
LIGHT_GREEN = "#B9F6B1"

def main(page: ft.Page):
    page.title = "GasToKITA"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = RED
    page.padding = 0
    page.window_maximized = True

    header = ft.Container(
        bgcolor=RED,
        height=70,
        padding=20,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("DASHBOARD", size=22, weight=ft.FontWeight.BOLD, color="white"),
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Text("U-Fuel", size=22, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Container(
                            width=45,
                            height=45,
                            bgcolor="white",
                            border_radius=23,
                            content=ft.Image(src="u-fuel_logo.jpg", fit=ft.BoxFit.CONTAIN),
                        ),
                    ],
                ),
            ],
        ),
    )

    def action_btn(text):
        return ft.Container(
            bgcolor="white",
            border=ft.Border(1, RED),
            border_radius=10,
            padding=12,
            on_click=lambda e: print(text),
            content=ft.Text(text, color=RED, weight=ft.FontWeight.BOLD, size=14),
        )

    stock_card = ft.Container(
        bgcolor=RED,
        border_radius=16,
        padding=18,
        expand=True,
        content=ft.Column(
            spacing=8,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Icon(ft.Icons.STORAGE, color="white", size=28),
                        ft.Row(spacing=12, controls=[
                            ft.Text("regular ▼", color="white", size=12),
                            ft.Text("pump 1 ▼", color="white", size=12),
                        ])
                    ],
                ),
                ft.Text("Current Fuel Stock", color="white", weight=ft.FontWeight.BOLD),
                ft.Text("5,000L / 10,000L", color="white", size=12),
                ft.Container(
                    height=8,
                    bgcolor="white",
                    border_radius=4,
                    content=ft.Row(spacing=0, controls=[
                        ft.Container(expand=1, bgcolor=GREEN, border_radius=4),
                        ft.Container(expand=1),
                    ])
                ),
                ft.Text("50%", color="white", size=11, text_align=ft.TextAlign.RIGHT),
            ],
        ),
    )

    sales_card = ft.Container(
        bgcolor=RED,
        border_radius=16,
        padding=18,
        expand=True,
        content=ft.Column(
            spacing=8,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Icon(ft.Icons.SHOW_CHART, color="white", size=28),
                        ft.Text("daily ▼", color="white", size=12),
                    ],
                ),
                ft.Text("Daily Sales", color="white", weight=ft.FontWeight.BOLD),
                ft.Text("₱ 10,000", color="white", size=26, weight=ft.FontWeight.BOLD),
            ],
        ),
    )

    profit_card = ft.Container(
        bgcolor=RED,
        border_radius=16,
        padding=18,
        expand=True,
        content=ft.Column(
            spacing=8,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Icon(ft.Icons.MONETIZATION_ON, color="white", size=28),
                        ft.Text("daily ▼", color="white", size=12),
                    ],
                ),
                ft.Text("Daily Net Profit", color="white", weight=ft.FontWeight.BOLD),
                ft.Text("₱ 5,000", color="white", size=26, weight=ft.FontWeight.BOLD),
            ],
        ),
    )

    quick_actions = ft.Container(
        bgcolor=CARD_GRAY,
        border_radius=20,
        padding=20,
        expand=True,
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Text("Quick Actions", color=RED, size=16, weight=ft.FontWeight.BOLD),
                action_btn("View Analytics"),
                action_btn("View Inventory"),
                action_btn("Transaction History"),
            ],
        ),
    )

    low_stock = ft.Container(
        bgcolor=CARD_GRAY,
        border_radius=20,
        padding=20,
        expand=True,
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Text("Low Stock Alert", color=RED, size=16, weight=ft.FontWeight.BOLD),
                ft.Container(
                    bgcolor=LIGHT_GREEN,
                    border_radius=30,
                    padding=12,
                    content=ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.CHECK, color="#2E7D32", size=18),
                            ft.Text("There is no low stock at the moment.", color="#2E7D32", size=13),
                        ],
                    ),
                ),
            ],
        ),
    )

    body = ft.Container(
        expand=True,
        bgcolor="white",
        border_radius=28,
        padding=30,
        margin=ft.Margin(left=15, right=15),
        content=ft.Column(
            spacing=25,
            controls=[
                ft.Row(spacing=20, controls=[stock_card, sales_card, profit_card]),
                ft.Row(spacing=20, controls=[quick_actions, low_stock]),
            ],
        ),
    )

    footer = ft.Container(
        height=55,
        bgcolor=RED,
        padding=20,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Container(
                    border=ft.Border(1, "white"),
                    border_radius=20,
                    padding=8,
                    content=ft.Row(spacing=6, controls=[
                        ft.Icon(ft.Icons.LOGOUT, color="white", size=16),
                        ft.Text("LOGOUT", color="white", size=12, weight=ft.FontWeight.BOLD),
                    ]),
                ),
                ft.Text("GAStoKITA", color="white", size=12),
                ft.Row(spacing=6, controls=[
                    ft.Icon(ft.Icons.PERSON, color="white", size=18),
                    ft.Text("ADMIN", color="white", size=12, weight=ft.FontWeight.BOLD),
                ]),
            ],
        ),
    )

    page.add(ft.Column(spacing=0, expand=True, controls=[header, body, footer]))

ft.run(main)