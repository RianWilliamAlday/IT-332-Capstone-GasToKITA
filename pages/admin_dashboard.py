import flet as ft

DARK_RED   = "#8B0000"
MED_RED    = "#A00000"
LIGHT_CARD = "#E8E8E8"
WHITE      = "#FFFFFF"
GREEN_ALERT = "#90EE90"
TEXT_DARK  = "#1A1A1A"
TEXT_WHITE = "#FFFFFF"
BODY_BG = "#C0C0C0"

def stat_card(icon, title, value, period_label="daily", show_progress=False, progress_value=0.5, sub_label="", dropdowns=None):
    top_left = None
    if dropdowns:
        top_left = ft.Row(
            [
                ft.Container(ft.Icon(icon, color=TEXT_WHITE, size=20), bgcolor=MED_RED, border_radius=6, padding=6),
                *[
                    ft.Row([ft.Text(d, color=TEXT_WHITE, size=11), ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, color=TEXT_WHITE, size=14)], spacing=0, tight=True)
                    for d in dropdowns
                ],
            ], spacing=8,
        )
    else:
        top_left = ft.Container(ft.Icon(icon, color=TEXT_WHITE, size=22), bgcolor=MED_RED, border_radius=6, padding=6)

    card_header = ft.Row(
        [top_left, ft.Row([ft.Text(period_label, color=TEXT_WHITE, size=11), ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, color=TEXT_WHITE, size=14)], spacing=0, tight=True)],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    body_controls = [
        card_header,
        ft.Text(title, color=TEXT_WHITE, size=13, weight=ft.FontWeight.BOLD),
        ft.Text(value, color=TEXT_WHITE, size=22, weight=ft.FontWeight.BOLD),
    ]

    if show_progress:
        body_controls += [
            ft.Row([ft.Text(sub_label, color=TEXT_WHITE, size=10), ft.Text(f"{int(progress_value*100)}%", color=TEXT_WHITE, size=10)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.ProgressBar(value=progress_value, color="#4CAF50", bgcolor="#6B0000", border_radius=4, bar_height=8, expand=True),
        ]

    return ft.Container(content=ft.Column(body_controls, spacing=6), bgcolor=DARK_RED, border_radius=10, padding=14, expand=True)

def action_button(label: str) -> ft.Container:
    return ft.Container(
        width=float("inf"),
        alignment=ft.Alignment.CENTER,
        content=ft.Text(label, color=TEXT_DARK, size=13, weight=ft.FontWeight.W_500),
        border=ft.Border.all(1.5, DARK_RED),
        border_radius=6,
        padding=ft.Padding.symmetric(vertical=12, horizontal=16),
        bgcolor=WHITE,
        ink=True,
        on_hover=lambda e: (setattr(e.control, "bgcolor", "#F5E6E6" if e.data == "true" else WHITE), e.control.update()),
    )

def main(page: ft.Page):
    page.title = "Admin Dashboard"
    page.bgcolor = DARK_RED
    page.padding = 0
    page.theme = ft.Theme(color_scheme_seed=DARK_RED)

    header = ft.Container(
        content=ft.Row(
            [
                ft.Text("DASHBOARD", color=TEXT_WHITE, size=22, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.Text("U-Fuel", color=TEXT_WHITE, size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(width=42, height=42, bgcolor=TEXT_WHITE, border_radius=20, clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        content=ft.Image(src="u-fuel_logo.jpg", fit=ft.BoxFit.CONTAIN, border_radius=20)),
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ), bgcolor=DARK_RED, padding=ft.Padding.symmetric(vertical=18, horizontal=24),
    )

    stats_row = ft.Row(
        [
            stat_card(icon=ft.Icons.LOCAL_GAS_STATION, title="Current Fuel Stock", value="5,000L / 10,000L", period_label="pump 1", show_progress=True, progress_value=0.5, dropdowns=["regular", "pump 1"]),
            stat_card(icon=ft.Icons.TRENDING_UP, title="Daily Sales", value="₱ 10,000", period_label="daily"),
            stat_card(icon=ft.Icons.ATTACH_MONEY, title="Daily Net Profit", value="₱ 5,000", period_label="daily"),
        ], spacing=16,
    )

    quick_actions = ft.Container(
        content=ft.Column([
            ft.Text("Quick Actions", color=TEXT_DARK, size=14, weight=ft.FontWeight.BOLD),
            ft.Container(height=4),
            action_button("View Analytics"),
            action_button("View Inventory"),
            action_button("Transaction History"),
            action_button("Dipstick Measurement Converter"),
        ], spacing=12, tight=True),
        bgcolor=LIGHT_CARD, border_radius=10, padding=18, expand=True,
    )

    low_stock = ft.Container(
        content=ft.Column([
            ft.Text("Low Stock Alert", color=TEXT_DARK, size=14, weight=ft.FontWeight.BOLD),
            ft.Container(height=8),
            ft.Container(
                content=ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color="#2E7D32", size=16), ft.Text("There is no low stock at the moment.", color="#2E7D32", size=12, italic=True)], spacing=8),
                bgcolor=GREEN_ALERT, border_radius=6, padding=ft.Padding.symmetric(vertical=10, horizontal=14),
            ),
        ], spacing=0, tight=True, alignment=ft.MainAxisAlignment.START),
        bgcolor=LIGHT_CARD, border_radius=10, padding=18, expand=True,
    )

    middle_row = ft.Row([quick_actions, low_stock], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START)

    body = ft.Container(
        bgcolor=BODY_BG,
        expand=True,
        padding=ft.Padding.only(left=20, right=20, top=20, bottom=24),
        content=ft.Column(
            controls=[stats_row, middle_row],
            spacing=16,
            expand=True,
            scroll=ft.ScrollMode.ADAPTIVE
        ),
    )

    footer = ft.Container(
        content=ft.Row([
            ft.Container(content=ft.Row([ft.Icon(ft.Icons.LOGOUT, color=TEXT_WHITE, size=16), ft.Text("LOGOUT", color=TEXT_WHITE, size=13, weight=ft.FontWeight.BOLD)], spacing=6), bgcolor="#6B6B6B", border_radius=6, padding=ft.Padding.symmetric(vertical=8, horizontal=14), ink=True),
            ft.Text("GAStoKITA", color=TEXT_WHITE, size=12, weight=ft.FontWeight.W_500),
            ft.Row([ft.Icon(ft.Icons.PERSON_OUTLINE, color=TEXT_WHITE, size=18), ft.Text("ADMIN", color=TEXT_WHITE, size=13, weight=ft.FontWeight.BOLD)], spacing=4),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=DARK_RED, # was "DARK_RED" string before, now fixed
        padding=ft.Padding.symmetric(vertical=14, horizontal=24),
    )

    page.add(ft.Column([header, body, footer], spacing=0, expand=True))

ft.run(main, assets_dir="assets")

