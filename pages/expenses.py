import flet as ft
from datetime import datetime, date
import time
from pages.api_client import (
        get_unified_expenses,get_expenses_summary,create_operational_expense,
        delete_operational_expense,
    )

DARK_RED = "#8B0000"
MED_RED = "#A00000"
LIGHT_GRAY = "#E9E9E9"
CARD_GRAY = "#D9D9D9"
WHITE = "#FFFFFF"
TEXT_DARK = "#1A1A1A"
TEXT_WHITE = "#FFFFFF"
BODY_BG = "#F5F5F5"
GREEN_SUCCESS = "#2E7D32"
BLUE_INFO = "#1565C0"
PURPLE_ACCENT = "#6A1B9A"

def expenses_page(page: ft.Page, auth: dict):
    page.title = "Expenses"
    page.bgcolor = BODY_BG
    page.padding = 0
    page.theme = ft.Theme(color_scheme_seed=DARK_RED)

    expenses_cache = []

    def show_snack(msg, color=DARK_RED):
        page.snack_bar = ft.SnackBar(content=ft.Text(msg, color="white"), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def make_summary_card(label, text_control, icon, icon_color):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(label, size=11, color="#555555", weight=ft.FontWeight.W_500),
                            ft.Icon(icon, size=16, color=icon_color),
                        ],
                        spacing=6,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    text_control,
                ],
                spacing=6,
                tight=True,
            ),
            bgcolor=WHITE,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=16, vertical=14),
            expand=True,
            shadow=ft.BoxShadow(blur_radius=4, color="#00000015", offset=ft.Offset(0, 2)),
        )

    total_exp_text = ft.Text("₱0.00", size=18, weight=ft.FontWeight.BOLD, color=DARK_RED)
    op_exp_text = ft.Text("₱0.00", size=18, weight=ft.FontWeight.BOLD, color=BLUE_INFO)
    fuel_exp_text = ft.Text("₱0.00", size=18, weight=ft.FontWeight.BOLD, color=GREEN_SUCCESS)
    oil_exp_text = ft.Text("₱0.00", size=18, weight=ft.FontWeight.BOLD, color=PURPLE_ACCENT)

    summary_row = ft.Row(
        controls=[
            make_summary_card("Total Combined", total_exp_text, ft.Icons.ACCOUNT_BALANCE_WALLET, DARK_RED),
            make_summary_card("Operational", op_exp_text, ft.Icons.RECEIPT_LONG, BLUE_INFO),
            make_summary_card("Fuel Restocks", fuel_exp_text, ft.Icons.LOCAL_GAS_STATION, GREEN_SUCCESS),
            make_summary_card("Oil Restocks", oil_exp_text, ft.Icons.SHOPPING_BAG, PURPLE_ACCENT),
        ],
        spacing=12,
    )

    def handle_from_date_change(e):
        if from_datepicker.value:
            val = from_datepicker.value
            from_date.value = val.strftime("%Y-%m-%d") if isinstance(val, (datetime, date)) else str(val)[:10]
            from_date.update()
            load_backend_data()

    def handle_to_date_change(e):
        if to_datepicker.value:
            val = to_datepicker.value
            to_date.value = val.strftime("%Y-%m-%d") if isinstance(val, (datetime, date)) else str(val)[:10]
            to_date.update()
            load_backend_data()

    from_datepicker = ft.DatePicker(on_change=handle_from_date_change)
    to_datepicker = ft.DatePicker(on_change=handle_to_date_change)
    page.overlay.extend([from_datepicker, to_datepicker])

    from_date = ft.TextField(
        label="From Date",
        hint_text="Select date",
        read_only=True,
        filled=True,
        fill_color=WHITE,
        border_radius=6,
        border_color="#CCCCCC",
        focused_border_color=DARK_RED,
        width=140,
        text_style=ft.TextStyle(size=13),
        suffix=ft.IconButton(
            icon=ft.Icons.CALENDAR_MONTH,
            icon_size=18,
            icon_color=DARK_RED,
            on_click=lambda _: setattr(from_datepicker, "open", True) or page.update(),
        ),
        on_click=lambda _: setattr(from_datepicker, "open", True) or page.update(),
    )

    to_date = ft.TextField(
        label="To Date",
        hint_text="Select date",
        read_only=True,
        filled=True,
        fill_color=WHITE,
        border_radius=6,
        border_color="#CCCCCC",
        focused_border_color=DARK_RED,
        width=140,
        text_style=ft.TextStyle(size=13),
        suffix=ft.IconButton(
            icon=ft.Icons.CALENDAR_MONTH,
            icon_size=18,
            icon_color=DARK_RED,
            on_click=lambda _: setattr(to_datepicker, "open", True) or page.update(),
        ),
        on_click=lambda _: setattr(to_datepicker, "open", True) or page.update(),
    )

    type_dropdown = ft.DropdownM2(
        label="Expense Source",
        value="all",
        filled=True,
        fill_color=WHITE,
        border_radius=6,
        border_color="#CCCCCC",
        focused_border_color=DARK_RED,
        width=160,
        options=[
            ft.dropdownm2.Option("all", "All Sources"),
            ft.dropdownm2.Option("operational", "Operational Only"),
            ft.dropdownm2.Option("fuel_restock", "Fuel Restocks"),
            ft.dropdownm2.Option("oil_restock", "Oil Restocks"),
        ],
    )

    def source_badge(source_type: str):
        if source_type == "fuel_restock":
            bg, label, icon = GREEN_SUCCESS, "Fuel Restock", ft.Icons.LOCAL_GAS_STATION
        elif source_type == "oil_restock":
            bg, label, icon = PURPLE_ACCENT, "Oil Restock", ft.Icons.SHOPPING_BAG
        else:
            bg, label, icon = BLUE_INFO, "Operational", ft.Icons.RECEIPT

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(icon, size=11, color=WHITE),
                    ft.Text(label, size=10, color=WHITE, weight=ft.FontWeight.BOLD),
                ],
                spacing=4,
                tight=True,
            ),
            bgcolor=bg,
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
        )

    columns = ["Date & Time", "Source", "Category", "Description", "Supplier", "Amount", "Recorded By", "Actions"]
    col_widths = [140, 120, 150, 240, 130, 110, 110, 80]

    def header_cell(text, width):
        return ft.Container(
            content=ft.Text(text, size=12, color="#555555", weight=ft.FontWeight.W_600),
            width=width,
            padding=ft.Padding.symmetric(horizontal=8, vertical=10),
        )

    def data_cell(text, width, bold=False, color="#111111"):
        return ft.Container(
            content=ft.Text(
                text,
                size=12,
                color=color,
                weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
            width=width,
            padding=ft.Padding.symmetric(horizontal=8, vertical=12),
        )

    table_header = ft.Container(
        content=ft.Row(
            controls=[header_cell(col, col_widths[i]) for i, col in enumerate(columns)],
            spacing=0,
        ),
        bgcolor="#F0F0F0",
        border=ft.Border.only(bottom=ft.BorderSide(1, "#E0E0E0")),
    )

    table_column = ft.Column(
        controls=[
            table_header,
            ft.Container(
                padding=20,
                content=ft.Row(
                    [
                        ft.ProgressRing(width=16, height=16, color=DARK_RED),
                        ft.Text("Loading expenses...", size=13, color="#777777"),
                    ],
                    spacing=10,
                ),
            ),
        ],
        spacing=0,
    )

    def open_delete_dialog(item_id: int):
        def confirm_delete(e):
            def bg():
                try:
                    delete_operational_expense(auth, item_id)
                    page.pop_dialog()
                    show_snack("Expense entry removed.", DARK_RED)
                    load_backend_data()
                except Exception as ex:
                    show_snack(str(ex), DARK_RED)

            page.run_thread(bg)

        dlg = ft.AlertDialog(
            title=ft.Text("Confirm Deletion"),
            content=ft.Text("Are you sure you want to delete this operational expense entry?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()),
                ft.FilledButton("Delete", bgcolor=DARK_RED, color=WHITE, on_click=confirm_delete),
            ],
        )
        page.show_dialog(dlg)

    def render_ui_data():
        st = type_dropdown.value

        filtered = []
        for x in expenses_cache:
            match_type = True if st == "all" else x.get("source_type") == st
            if match_type:
                filtered.append(x)

        rows = []
        for i, item in enumerate(filtered):
            try:
                dt_str = datetime.fromisoformat(item["expense_date"]).strftime("%b %d, %Y %I:%M %p")
            except Exception:
                dt_str = str(item.get("expense_date", ""))[:16]

            is_op = item.get("source_type") == "operational"
            del_btn = ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE,
                icon_color=DARK_RED if is_op else "#CCCCCC",
                icon_size=18,
                tooltip="Delete Operational Expense" if is_op else "Inventory logs cannot be deleted directly",
                disabled=not is_op,
                on_click=lambda e, idx=item["id"]: open_delete_dialog(idx),
            )

            row = ft.Container(
                content=ft.Row(
                    controls=[
                        data_cell(dt_str, col_widths[0]),
                        ft.Container(
                            content=source_badge(item.get("source_type", "")),
                            width=col_widths[1],
                            padding=ft.Padding.symmetric(horizontal=4, vertical=8),
                        ),
                        data_cell(item.get("category", ""), col_widths[2], bold=True),
                        data_cell(item.get("description", ""), col_widths[3]),
                        data_cell(item.get("supplier") or "—", col_widths[4]),
                        data_cell(f"₱{item.get('amount', 0):,.2f}", col_widths[5], bold=True, color=DARK_RED),
                        data_cell(item.get("recorded_by", "System"), col_widths[6]),
                        ft.Container(content=del_btn, width=col_widths[7], alignment=ft.Alignment.CENTER),
                    ],
                    spacing=0,
                ),
                bgcolor="#FAFAFA" if i % 2 == 0 else WHITE,
                border=ft.Border.only(bottom=ft.BorderSide(1, "#F0F0F0")),
            )
            rows.append(row)

        if not rows:
            rows = [
                ft.Container(
                    padding=30,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Text("No expense records match the specified filters.", size=13, color="#888888"),
                )
            ]

        table_column.controls = [table_header] + rows
        try:
            page.update()
        except Exception:
            pass

    def load_backend_data():
        def bg():
            time.sleep(0.05)
            sd = from_date.value.strip() if from_date.value else None
            ed = to_date.value.strip() if to_date.value else None

            expenses = get_unified_expenses(auth, start_date=sd, end_date=ed)
            summary_data = get_expenses_summary(auth, start_date=sd, end_date=ed)

            nonlocal expenses_cache
            expenses_cache = expenses

            summary = summary_data.get("summary", {})
            total_exp_text.value = f"₱{summary.get('total_expenses', 0.0):,.2f}"
            op_exp_text.value = f"₱{summary.get('operational_expenses', 0.0):,.2f}"
            fuel_exp_text.value = f"₱{summary.get('fuel_restock_expenses', 0.0):,.2f}"
            oil_exp_text.value = f"₱{summary.get('oil_restock_expenses', 0.0):,.2f}"

            render_ui_data()

        page.run_thread(bg)

    type_dropdown.on_change = lambda e: render_ui_data()

    def open_add_expense_dialog(e):
        category_field = ft.DropdownM2(
            label="Category",
            width=300,
            options=[
                ft.dropdownm2.Option("Utilities", "Utilities (Electricity, Water)"),
                ft.dropdownm2.Option("Maintenance & Repairs", "Maintenance & Repairs"),
                ft.dropdownm2.Option("Salaries & Payroll", "Salaries & Wages"),
                ft.dropdownm2.Option("Supplies", "Station Supplies"),
                ft.dropdownm2.Option("Taxes & Permits", "Taxes & Permits"),
                ft.dropdownm2.Option("Miscellaneous", "Miscellaneous"),
            ],
            value="Utilities",
        )
        amount_field = ft.TextField(
            label="Amount (₱)",
            width=300,
            keyboard_type=ft.KeyboardType.NUMBER,
            autofocus=True,
        )
        desc_field = ft.TextField(
            label="Description / Notes",
            width=300,
            multiline=True,
            max_lines=3,
        )
        err_text = ft.Text("", size=11, color=DARK_RED)

        def save_expense(ev):
            try:
                amt = float(amount_field.value or 0)
                if amt <= 0:
                    err_text.value = "Please enter a valid amount greater than 0."
                    err_text.update()
                    return

                def bg():
                    try:
                        create_operational_expense(
                            auth,
                            category=category_field.value,
                            amount=amt,
                            description=desc_field.value or category_field.value,
                        )
                        page.pop_dialog()
                        show_snack(f"Added operational expense: ₱{amt:,.2f}", GREEN_SUCCESS)
                        load_backend_data()
                    except Exception as ex:
                        err_text.value = str(ex)
                        err_text.update()

                page.run_thread(bg)

            except ValueError:
                err_text.value = "Invalid amount value."
                err_text.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Record Operational Expense", weight=ft.FontWeight.BOLD),
            content=ft.Column(
                tight=True,
                spacing=12,
                controls=[category_field, amount_field, desc_field, err_text],
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()),
                ft.FilledButton("Save Expense", bgcolor=DARK_RED, color=WHITE, on_click=save_expense),
            ],
        )
        page.show_dialog(dialog)

    add_expense_btn = ft.Button(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.ADD, size=16, color=WHITE),
                ft.Text("RECORD EXPENSE", color=WHITE, size=12, weight=ft.FontWeight.BOLD),
            ],
            spacing=6,
            tight=True,
        ),
        bgcolor=DARK_RED,
        height=40,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
        on_click=open_add_expense_dialog,
    )

    def go_dashboard(e):
            from pages.admin_dashboard import dashboard_page
            page.controls.clear()
            page.add(dashboard_page(page, auth))
            page.update()

    def go_logout(e):
        auth.clear()
        page.controls.clear()
        from admin import build_login_view
        page.add(build_login_view(page, auth))

    header = ft.Container(
        content=ft.Row([
            ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=WHITE, on_click=go_dashboard),
            ft.Text("Expenses", color=WHITE, size=22, weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.Text("U-Fuel", color=WHITE, size=18, weight=ft.FontWeight.BOLD),
                ft.Container(width=42, height=42, bgcolor=WHITE, border_radius=20, clip_behavior=ft.ClipBehavior.HARD_EDGE, content=ft.Image(src="u-fuel_logo.jpg", fit=ft.BoxFit.CONTAIN, border_radius=20)),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=DARK_RED, padding=ft.Padding.symmetric(vertical=18, horizontal=24),
    )
    
    footer = ft.Container(
        content=ft.Row([
            ft.Container(content=ft.Row([ft.Icon(ft.Icons.LOGOUT, color=WHITE, size=16), ft.Text("LOGOUT", color=WHITE, size=13, weight=ft.FontWeight.BOLD)], spacing=6), bgcolor="#6B6B6B", border_radius=6, padding=ft.Padding.symmetric(vertical=8, horizontal=14), ink=True, on_click=go_logout),
            ft.Text("GAStoKITA", color=WHITE, size=12),
            ft.Row([ft.Icon(ft.Icons.PERSON_OUTLINE, color=WHITE, size=18), ft.Text(auth.get("name","ADMIN"), color=WHITE, size=13, weight=ft.FontWeight.BOLD)], spacing=4),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        bgcolor=DARK_RED, padding=ft.Padding.symmetric(vertical=14, horizontal=24),
    )

    filters_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Filters", size=14, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                        add_expense_btn,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=8),
                ft.Row(controls=[type_dropdown, from_date, to_date], spacing=12, wrap=True),
            ],
            spacing=0,
            tight=True,
        ),
        bgcolor=WHITE,
        border_radius=8,
        padding=ft.Padding.symmetric(horizontal=20, vertical=16),
        shadow=ft.BoxShadow(blur_radius=4, color="#00000015", offset=ft.Offset(0, 2)),
    )

    table_section = ft.Container(
        content=ft.Column([table_column], scroll=ft.ScrollMode.ADAPTIVE),
        bgcolor=WHITE,
        border_radius=8,
        shadow=ft.BoxShadow(blur_radius=4, color="#00000015", offset=ft.Offset(0, 2)),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        expand=True,
    )

    content = ft.Container(
        content=ft.Column(
            controls=[
                summary_row,
                ft.Container(height=12),
                filters_section,
                ft.Container(height=12),
                table_section,
            ],
            spacing=0,
            expand=True,
        ),
        padding=ft.Padding.all(24),
        expand=True,
    )

    load_backend_data()

    return ft.Column(controls=[header, content, footer], spacing=0, expand=True)