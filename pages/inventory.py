import flet as ft

DARK_RED = "#8B0000"
LIGHT_BG = "#F0F0F0"
WHITE = "#FFFFFF"
BLACK = "#000000"
TEXT_DARK = "#1A1A1A" # pure black text everywhere
GREEN = "#15803D"

def main(page: ft.Page):
    page.title = "U-FUEL - Inventory Management"
    page.bgcolor = LIGHT_BG
    page.padding = 0
    page.window.width = 1100
    page.window.height = 750

    header = ft.Container(
        content=ft.Row([
            ft.Text("DASHBOARD", color=WHITE, size=22, weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.Text("U-Fuel", color=WHITE, size=18, weight=ft.FontWeight.BOLD),
                ft.Container(width=42, height=42, bgcolor=WHITE, border_radius=20, clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    content=ft.Image(src="u-fuel_logo.jpg", fit=ft.BoxFit.CONTAIN, border_radius=20)),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=DARK_RED, padding=ft.Padding.symmetric(vertical=18, horizontal=24),
    )

    footer = ft.Container(
        content=ft.Row([
            ft.Container(content=ft.Row([ft.Icon(ft.Icons.LOGOUT, color=WHITE, size=16), ft.Text("LOGOUT", color=WHITE, size=13, weight=ft.FontWeight.BOLD)], spacing=6),
                bgcolor="#6B6B6B", border_radius=6, padding=ft.Padding.symmetric(vertical=8, horizontal=14), ink=True),
            ft.Text("GAStoKITA", color=WHITE, size=12),
            ft.Row([ft.Icon(ft.Icons.PERSON_OUTLINE, color=WHITE, size=18), ft.Text("ADMIN", color=WHITE, size=13, weight=ft.FontWeight.BOLD)], spacing=4),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        bgcolor=DARK_RED, padding=ft.Padding.symmetric(vertical=14, horizontal=24),
    )

    def status_badge(text):
        return ft.Container(content=ft.Text(text, size=11, color=WHITE, weight=ft.FontWeight.BOLD),
            bgcolor=GREEN, border_radius=20, padding=ft.Padding.symmetric(horizontal=12, vertical=4))

    def fuel_card(name, capacity, current, percent, dipstick, threshold, price):
        progress = percent / 100
        return ft.Container(
            bgcolor=WHITE, border_radius=10, padding=20,
            shadow=ft.BoxShadow(blur_radius=6, color="#00000012", offset=ft.Offset(0, 2)),
            content=ft.Column([
                ft.Row([
                    ft.Column([ft.Text(name, size=16, weight=ft.FontWeight.BOLD, color=BLACK),
                               ft.Text(f"Capacity: {capacity:,} L", size=12, color=BLACK)], spacing=2),
                    ft.Container(content=ft.Text("RESTOCK", size=11, color=DARK_RED, weight=ft.FontWeight.BOLD),
                                 border=ft.Border.all(1, DARK_RED), border_radius=6, padding=ft.Padding.symmetric(horizontal=12, vertical=6))
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=14),
                ft.Row([
                    ft.Container(expand=True, content=ft.Column([
                        ft.Row([ft.Text("Current Level", size=12, color=BLACK, weight=ft.FontWeight.W_600),
                                ft.Text(f"{current:,} L ({percent}%)", size=12, color=BLACK, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.ProgressBar(value=progress, color=DARK_RED, bgcolor="#E5E7EB", bar_height=6, border_radius=4),
                        ft.Container(height=8),
                        ft.Row([
                            ft.Container(expand=True, bgcolor="#F9FAFB", border_radius=6, padding=12,
                                content=ft.Column([ft.Text("Dipstick Reading", size=11, color=BLACK, weight=ft.FontWeight.W_600), ft.Text(f"{dipstick} cm", size=16, color=BLACK, weight=ft.FontWeight.BOLD)], spacing=4)),
                            ft.Container(expand=True, bgcolor="#F9FAFB", border_radius=6, padding=12,
                                content=ft.Column([ft.Text("Threshold", size=11, color=BLACK, weight=ft.FontWeight.W_600), ft.Text(f"{threshold:,} L", size=16, color=BLACK, weight=ft.FontWeight.BOLD)], spacing=4)),
                        ], spacing=12)
                    ], spacing=8)),
                    ft.Container(width=200, bgcolor="#FFFBF5", border=ft.Border.all(1, "#F3E8D3"), border_radius=8, padding=16,
                        content=ft.Column([
                            ft.Row([ft.Icon(ft.Icons.LOCAL_OFFER_OUTLINED, size=16, color=DARK_RED), ft.Text("Current Price", size=11, color=BLACK, weight=ft.FontWeight.BOLD)], spacing=6),
                            ft.Container(height=4),
                            ft.Row([ft.Text(f"₱{price:.2f}", size=24, weight=ft.FontWeight.BOLD, color=DARK_RED), ft.Text("/ L", size=12, color=BLACK, weight=ft.FontWeight.BOLD)], spacing=4, vertical_alignment=ft.CrossAxisAlignment.END),
                            ft.Container(height=6),
                            ft.Text("Hardcoded for now", size=10, color=BLACK, italic=True)
                        ], spacing=2, tight=True))
                ], spacing=20, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ], spacing=0)
        )

    def oil_table():
        headers = ["Oil Name", "Category", "Current Stock", "Reorder Point", "Status"]
        widths = [200, 120, 120, 120, 120]
        rows = [("Engine Oil 1L","Oil","25","10"), ("Engine Oil 4L","Oil","15","10"), ("Brake Fluid","Oil","30","15"), ("Chips","Snacks","50","20"), ("Water 500ml","Drinks","80","30")]
        def h_cell(t,w): return ft.Container(width=w, padding=10, content=ft.Text(t, size=12, color=BLACK, weight=ft.FontWeight.BOLD))
        def d_cell(t,w): return ft.Container(width=w, padding=10, content=ft.Text(t, size=13, color=BLACK, weight=ft.FontWeight.W_500))
        header_row = ft.Container(border=ft.Border.only(bottom=ft.BorderSide(1, "#E5E7EB")), bgcolor="#F9FAFB", content=ft.Row([h_cell(headers[i], widths[i]) for i in range(5)], spacing=0))
        data_rows = []
        for i,r in enumerate(rows):
            data_rows.append(ft.Container(bgcolor="#FAFAFA" if i%2==0 else WHITE, border=ft.Border.only(bottom=ft.BorderSide(1, "#F3F4F6")),
                content=ft.Row([d_cell(r[0],widths[0]), d_cell(r[1],widths[1]), d_cell(r[2],widths[2]), d_cell(r[3],widths[3]),
                                ft.Container(width=widths[4], padding=10, content=status_badge("In Stock"))], spacing=0)))
        return ft.Container(bgcolor=WHITE, border_radius=10, clip_behavior=ft.ClipBehavior.HARD_EDGE,
            shadow=ft.BoxShadow(blur_radius=6, color="#00000012", offset=ft.Offset(0,2)), content=ft.Column([header_row, *data_rows], spacing=0))

    dipstick_btn = ft.Button(
        content=ft.Row([ft.Icon(ft.Icons.ADD, size=16, color=WHITE), ft.Text("DIPSTICK CONVERTER", color=WHITE, size=12, weight=ft.FontWeight.BOLD)], spacing=6, tight=True),
        bgcolor=DARK_RED, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=ft.Padding.symmetric(horizontal=16, vertical=10))
    )
    add_oil_btn = ft.Button(
        content=ft.Row([ft.Icon(ft.Icons.ADD, size=16, color=WHITE), ft.Text("ADD OIL", color=WHITE, size=12, weight=ft.FontWeight.BOLD)], spacing=6, tight=True),
        bgcolor=DARK_RED, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=ft.Padding.symmetric(horizontal=16, vertical=10)), visible=False
    )
    restock_oil_btn = ft.Button(
        content=ft.Row([ft.Icon(ft.Icons.INVENTORY_2_OUTLINED, size=16, color=WHITE), ft.Text("RESTOCK OIL", color=WHITE, size=12, weight=ft.FontWeight.BOLD)], spacing=6, tight=True),
        bgcolor=DARK_RED, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=ft.Padding.symmetric(horizontal=16, vertical=10)), visible=False
    )

    title_row = ft.Row(controls=[dipstick_btn, ft.Row(controls=[add_oil_btn, restock_oil_btn], spacing=10, tight=True)], alignment=ft.MainAxisAlignment.END)

    selected = {"tab": "fuel"}
    content_area = ft.Container(expand=True)
    tab_fuel = ft.Container(padding=ft.Padding.symmetric(vertical=10, horizontal=16), ink=True)
    tab_oil = ft.Container(padding=ft.Padding.symmetric(vertical=10, horizontal=16), ink=True)

    def build_content():
        if selected["tab"] == "fuel":
            return ft.Column([fuel_card("Regular", 10000, 9500, 95, 95, 2000, 62.30), fuel_card("Premium", 10000, 5000, 50, 55, 2000, 70.50), fuel_card("Diesel", 10000, 7200, 72, 78, 2000, 64.80)], spacing=16, scroll=ft.ScrollMode.ADAPTIVE, expand=True)
        else:
            return ft.Column([oil_table()], spacing=0, scroll=ft.ScrollMode.ADAPTIVE, expand=True)

    def refresh_tabs():
        is_fuel = selected["tab"] == "fuel"
        dipstick_btn.visible = is_fuel
        add_oil_btn.visible = not is_fuel
        restock_oil_btn.visible = not is_fuel

        # Active = DARK_RED, Inactive = BLACK (no more muted gray)
        tab_fuel.content = ft.Row([ft.Icon(ft.Icons.LOCAL_GAS_STATION, size=18, color=DARK_RED if is_fuel else BLACK),
                                   ft.Text("FUEL INVENTORY", size=12, weight=ft.FontWeight.BOLD, color=DARK_RED if is_fuel else BLACK)], spacing=6, alignment=ft.MainAxisAlignment.CENTER)
        tab_fuel.border = ft.Border.only(bottom=ft.BorderSide(2, DARK_RED if is_fuel else ft.Colors.TRANSPARENT))

        tab_oil.content = ft.Row([ft.Icon(ft.Icons.SHOPPING_CART, size=18, color=DARK_RED if not is_fuel else BLACK),
                                      ft.Text("OIL INVENTORY", size=12, weight=ft.FontWeight.BOLD, color=DARK_RED if not is_fuel else BLACK)], spacing=6, alignment=ft.MainAxisAlignment.CENTER)
        tab_oil.border = ft.Border.only(bottom=ft.BorderSide(2, DARK_RED if not is_fuel else ft.Colors.TRANSPARENT))

        content_area.content = build_content()
        page.update()

    tab_fuel.on_click = lambda e: (selected.update(tab="fuel"), refresh_tabs())
    tab_oil.on_click = lambda e: (selected.update(tab="oil"), refresh_tabs())

    tabs_row = ft.Row([tab_fuel, tab_oil], spacing=12)
    body = ft.Container(expand=True, padding=24, content=ft.Column([title_row, ft.Container(height=12), tabs_row, ft.Container(height=12), content_area], spacing=0, expand=True))

    page.add(ft.Column([header, body, footer], spacing=0, expand=True))
    refresh_tabs()

ft.run(main, assets_dir="assets")