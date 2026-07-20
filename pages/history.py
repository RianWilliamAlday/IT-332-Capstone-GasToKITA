import flet as ft

DARK_RED   = "#8B0000"
TEXT_WHITE = "#FFFFFF"

def main(page: ft.Page):
    page.title = "Transaction History"
    page.bgcolor = "#F5F5F5"
    page.padding = ft.Padding.all(0)
    page.window.width = 1024
    page.window.height = 600

    def summary_card(label: str, value: str, icon: ft.IconData, icon_color: str, value_color: str):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(label, size=12, color="#555555"),
                            ft.Icon(icon, size=16, color=icon_color),
                        ],
                        spacing=6,
                    ),
                    ft.Text(value, size=20, weight=ft.FontWeight.BOLD, color=value_color),
                ],
                spacing=6,
                tight=True,
            ),
            bgcolor="white",
            border_radius=ft.BorderRadius(top_left=8, top_right=8, bottom_left=8, bottom_right=8),
            padding=ft.Padding.symmetric(horizontal=16, vertical=14),
            width=160,
            shadow=ft.BoxShadow(blur_radius=4, color="#00000015", offset=ft.Offset(0, 2)),
        )

    summary_row = ft.Row(
        controls=[
            summary_card("Total Sales", "₱4,965.40", ft.Icons.TRENDING_UP, "#4CAF50", "#4CAF50"),
            summary_card("Transactions", "5", ft.Icons.LIST_ALT, "#1565C0", "#1565C0"),
            summary_card("Fuel Sales", "4", ft.Icons.LOCAL_GAS_STATION, "#C62828", "#C62828"),
            summary_card("oil Sales", "1", ft.Icons.SHOPPING_CART, "#6A1B9A", "#6A1B9A"),
        ],
        spacing=12,
    )

    search_field = ft.TextField(
        hint_text="Search",
        filled=True,
        fill_color="white",
        border_radius=ft.BorderRadius(top_left=6, top_right=6, bottom_left=6, bottom_right=6),
        border_color="#CCCCCC",
        focused_border_color="#8B0000",
        height=42,
        width=160,
        text_style=ft.TextStyle(size=13),
        content_padding=ft.Padding.symmetric(horizontal=12, vertical=8),
    )

    type_dropdown = ft.Dropdown(
        label="Type",
        value="all",
        filled=True,
        fill_color="white",
        border_radius=ft.BorderRadius(top_left=6, top_right=6, bottom_left=6, bottom_right=6),
        border_color="#CCCCCC",
        focused_border_color="#8B0000",
        width=100,
        options=[
            ft.DropdownOption(key="all", text="All"),
            ft.DropdownOption(key="fuel", text="Fuel"),
            ft.DropdownOption(key="oil", text="Oils"),
        ],
    )

    attendant_dropdown = ft.Dropdown(
        label="Attendant",
        value="all",
        filled=True,
        fill_color="white",
        border_radius=ft.BorderRadius(top_left=6, top_right=6, bottom_left=6, bottom_right=6),
        border_color="#CCCCCC",
        focused_border_color="#8B0000",
        width=160,
        options=[
            ft.DropdownOption(key="all", text="All Attendants"),
            ft.DropdownOption(key="a1", text="Pump Attendant 1"),
            ft.DropdownOption(key="a2", text="Pump Attendant 2"),
            ft.DropdownOption(key="a3", text="Pump Attendant 3"),
        ],
    )

    from_date = ft.TextField(
        label="From Date",
        hint_text="dd/mm/yyyy",
        filled=True,
        fill_color="white",
        border_radius=ft.BorderRadius(top_left=6, top_right=6, bottom_left=6, bottom_right=6),
        border_color="#CCCCCC",
        focused_border_color="#8B0000",
        width=140,
        text_style=ft.TextStyle(size=13),
        content_padding=ft.Padding.symmetric(horizontal=12, vertical=8),
    )

    to_date = ft.TextField(
        label="To Date",
        hint_text="dd/mm/yyyy",
        filled=True,
        fill_color="white",
        border_radius=ft.BorderRadius(top_left=6, top_right=6, bottom_left=6, bottom_right=6),
        border_color="#CCCCCC",
        focused_border_color="#8B0000",
        width=140,
        text_style=ft.TextStyle(size=13),
        content_padding=ft.Padding.symmetric(horizontal=12, vertical=8),
    )

    filters_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Filters", size=14, weight=ft.FontWeight.BOLD, color="#222222"),
                ft.Container(height=8),
                ft.Row(
                    controls=[search_field, type_dropdown, attendant_dropdown, from_date, to_date],
                    spacing=12,
                    wrap=True,
                ),
            ],
            spacing=0,
            tight=True,
        ),
        bgcolor="white",
        border_radius=ft.BorderRadius(top_left=8, top_right=8, bottom_left=8, bottom_right=8),
        padding=ft.Padding.symmetric(horizontal=20, vertical=16),
        shadow=ft.BoxShadow(blur_radius=4, color="#00000015", offset=ft.Offset(0, 2)),
    )

    columns = ["Attendant", "Date & Time", "Type", "Item", "Pump", "Quantity", "Amount", "Paid", "Change"]
    col_widths = [160, 180, 100, 100, 80, 90, 100, 100, 90]

    def header_cell(text, width):
        return ft.Container(
            content=ft.Text(text, size=12, color="#555555", weight=ft.FontWeight.W_600),
            width=width,
            padding=ft.Padding.symmetric(horizontal=8, vertical=10),
        )

    def data_cell(text, width, bold=False, color="#111111"):
        return ft.Container(
            content=ft.Text(text, size=13, color=color, weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL),
            width=width,
            padding=ft.Padding.symmetric(horizontal=8, vertical=12),
        )

    def fuel_badge(label: str):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.LOCAL_GAS_STATION, size=12, color="white"),
                    ft.Text(label, size=11, color="white", weight=ft.FontWeight.BOLD),
                ],
                spacing=4,
                tight=True,
            ),
            bgcolor="#C62828",
            border_radius=ft.BorderRadius(top_left=12, top_right=12, bottom_left=12, bottom_right=12),
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        )

    table_header = ft.Container(
        content=ft.Row(
            controls=[header_cell(col, col_widths[i]) for i, col in enumerate(columns)],
            spacing=0,
        ),
        border=ft.Border.only(bottom=ft.BorderSide(1, "#E0E0E0")),
    )

    transactions = [
        ("Pump Attendant 1", "May 8, 2026, 08:30 AM", "fuel", "Regular", "Pump 1", "15.5L", "₱965.65", "₱1000.00", "₱34.35"),
        ("Pump Attendant 2", "May 8, 2026, 09:10 AM", "fuel", "Premium", "Pump 2", "10.0L", "₱820.00", "₱1000.00", "₱180.00"),
        ("Pump Attendant 1", "May 8, 2026, 10:45 AM", "fuel", "Diesel",  "Pump 3", "20.0L", "₱1400.00","₱1500.00", "₱100.00"),
        ("Pump Attendant 2", "May 8, 2026, 11:20 AM", "fuel", "Regular", "Pump 1", "8.0L",  "₱496.00", "₱500.00",  "₱4.00"),
        ("Pump Attendant 1", "May 8, 2026, 01:00 PM", "product", "Oil Filter", "-", "1 pc", "₱284.75", "₱300.00",  "₱15.25"),
    ]

    def table_row(row_data, is_even):
        attendant, datetime, rtype, item, pump, qty, amount, paid, change = row_data
        return ft.Container(
            content=ft.Row(
                controls=[
                    data_cell(attendant, col_widths[0]),
                    data_cell(datetime, col_widths[1]),
                    ft.Container(
                        content=fuel_badge(rtype),
                        width=col_widths[2],
                        padding=ft.Padding.symmetric(horizontal=8, vertical=8),
                    ),
                    data_cell(item, col_widths[3]),
                    data_cell(pump, col_widths[4]),
                    data_cell(qty, col_widths[5]),
                    data_cell(amount, col_widths[6], bold=True, color="#8B0000"),
                    data_cell(paid, col_widths[7]),
                    data_cell(change, col_widths[8]),
                ],
                spacing=0,
            ),
            bgcolor="#FAFAFA" if is_even else "white",
            border=ft.Border.only(bottom=ft.BorderSide(1, "#F0F0F0")),
        )

    table_rows = [table_row(t, i % 2 == 0) for i, t in enumerate(transactions)]

    table_section = ft.Container(
        content=ft.Column(
            controls=[table_header] + table_rows,
            spacing=0,
        ),
        bgcolor="white",
        border_radius=ft.BorderRadius(top_left=8, top_right=8, bottom_left=8, bottom_right=8),
        shadow=ft.BoxShadow(blur_radius=4, color="#00000015", offset=ft.Offset(0, 2)),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )

    export_button = ft.Button(
        content="EXPORT CSV",
        icon=ft.Icons.DOWNLOAD,
        bgcolor="#8B0000",
        color="white",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=6),
            text_style=ft.TextStyle(size=13, weight=ft.FontWeight.BOLD),
        ),
        height=40,
    )

    header = ft.Container(
    content=ft.Row(
        [
            ft.Text(
                "History",
                color=TEXT_WHITE,
                size=22,
                weight=ft.FontWeight.BOLD,
            ),
            ft.Row(
                [
                    ft.Text(
                        "U-Fuel",
                        color=TEXT_WHITE,
                        size=18,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Container(
                        width=42,
                        height=42,
                        bgcolor=TEXT_WHITE,
                        border_radius=20,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        content=ft.Image(
                            src="u-fuel_logo.jpg",
                            fit=ft.BoxFit.CONTAIN,
                            border_radius=20,
                        ),
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    ),
    bgcolor=DARK_RED,
    padding=ft.Padding.symmetric(vertical=18, horizontal=24),
    )

    footer = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.LOGOUT, color=TEXT_WHITE, size=16),
                            ft.Text("LOGOUT", color=TEXT_WHITE, size=13, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=6,
                    ),
                    bgcolor="#6B6B6B",
                    border_radius=6,
                    padding=ft.Padding.symmetric(vertical=8, horizontal=14),
                    ink=True,
                ),
                ft.Text(
                    "GAStoKITA",
                    color=TEXT_WHITE,
                    size=12,
                    weight=ft.FontWeight.W_500,
                ),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.PERSON_OUTLINE, color=TEXT_WHITE, size=18),
                        ft.Text("ADMIN", color=TEXT_WHITE, size=13, weight=ft.FontWeight.BOLD),
                    ],
                    spacing=4,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=DARK_RED,
        padding=ft.Padding.symmetric(vertical=14, horizontal=24),
    )

    page.add(
        ft.Column(
            controls=[
                header,
                ft.Container(
                    content=ft.Column(
                        controls=[
                            summary_row,
                            ft.Container(height=16),
                            filters_section,
                            ft.Container(height=16),
                            table_section,
                            ft.Container(height=16),
                            ft.Row(
                                controls=[export_button],
                                alignment=ft.MainAxisAlignment.END,
                            ),
                        ],
                        scroll=ft.ScrollMode.ADAPTIVE,
                        spacing=0,
                    ),
                    padding=ft.Padding.all(24),
                    expand=True,
                ),
                footer,
            ],
            spacing=0,
            expand=True,
        )
    )


ft.run(main)