import flet as ft
import os, requests, time
from datetime import datetime, date, timedelta
from concurrent.futures import ThreadPoolExecutor
from pages.api_client import get_unified_history, export_history_csv

DARK_RED   = "#8B0000"
TEXT_WHITE = "#FFFFFF"
BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

def history_page(page: ft.Page, auth: dict):
    page.title = "Transaction History"
    page.bgcolor = "#F5F5F5"
    page.padding = 0
    page.theme = ft.Theme(color_scheme_seed=DARK_RED)

    cache = auth.get("history_cache", {})

    total_sales_text = ft.Text(f"₱{cache.get('total_amount', 0):,.2f}" if cache else "₱0.00", size=20, weight=ft.FontWeight.BOLD, color="#4CAF50")
    transactions_text = ft.Text(str(cache.get("total_count", 0)) if cache else "0", size=20, weight=ft.FontWeight.BOLD, color="#1565C0")
    
    cached_sales = cache.get("sales", [])
    fuel_sales_text = ft.Text(str(sum(1 for s in cached_sales if s.get("product_type")=="fuel")), size=20, weight=ft.FontWeight.BOLD, color="#C62828")
    oil_sales_text = ft.Text(str(sum(1 for s in cached_sales if s.get("product_type")=="oil")), size=20, weight=ft.FontWeight.BOLD, color="#6A1B9A")

    type_dropdown = ft.DropdownM2(
        label="Type", value="all", filled=True, fill_color="white", border_radius=6, 
        border_color="#CCCCCC", focused_border_color=DARK_RED, width=110, 
        options=[ft.dropdownm2.Option("all","All"), ft.dropdownm2.Option("fuel","Fuel"), ft.dropdownm2.Option("oil","Oils")]
    )

    known_attendants = set(s.get("attendant_name") for s in cached_sales if s.get("attendant_name"))

    attendant_dropdown = ft.DropdownM2(
        label="Attendant", value="all", filled=True, fill_color="white", border_radius=6, 
        border_color="#CCCCCC", focused_border_color=DARK_RED, width=180, 
        options=[ft.dropdownm2.Option("all", "All Attendants")]
    )

    known_fuel_products = {s.get("product_name") for s in cached_sales if s.get("product_type") == "fuel" and s.get("product_name")}
    known_oil_products  = {s.get("product_name") for s in cached_sales if s.get("product_type") == "oil" and s.get("product_name")}
    last_loaded_sales = {"data": cached_sales}

    product_dropdown = ft.DropdownM2(
        label="Product", value="all", filled=True, fill_color="white", border_radius=6,
        border_color="#CCCCCC", focused_border_color=DARK_RED, width=160,
        options=[ft.dropdownm2.Option("all", "All Products")]
    )

    def is_mounted(control):
        """Safely checks if a control is mounted to the page without raising RuntimeError."""
        try:
            return control.page is not None
        except (RuntimeError, AttributeError):
            return False

    def safe_ui_refresh(*controls):
        """Safely updates target controls only if they are actively attached to the page."""
        for c in controls:
            try:
                if is_mounted(c):
                    c.update()
            except Exception as ue:
                print(f"[history] control update failed: {ue}")

    def refresh_attendants(sales_list: list):
        """Extracts unique attendant names from sales records and populates the dropdown."""
        new_names = {s.get("attendant_name") for s in sales_list if s.get("attendant_name")}
        
        if new_names - known_attendants or len(attendant_dropdown.options) == 1:
            known_attendants.update(new_names)
            curr_val = attendant_dropdown.value
            
            opts = [ft.dropdownm2.Option("all", "All Attendants")]
            for name in sorted(known_attendants):
                opts.append(ft.dropdownm2.Option(name, name))
            
            attendant_dropdown.options = opts
            
            if curr_val in [o.key for o in opts]:
                attendant_dropdown.value = curr_val
            else:
                attendant_dropdown.value = "all"
                
            safe_ui_refresh(attendant_dropdown)

    def rebuild_product_options():
        t = type_dropdown.value
        if t == "fuel":
            names = known_fuel_products
        elif t == "oil":
            names = known_oil_products
        else:
            names = known_fuel_products | known_oil_products

        curr_val = product_dropdown.value
        opts = [ft.dropdownm2.Option("all", "All Products")]
        opts += [ft.dropdownm2.Option(n, n) for n in sorted(names)]
        product_dropdown.options = opts
        product_dropdown.value = curr_val if curr_val in [o.key for o in opts] else "all"
        safe_ui_refresh(product_dropdown)

    def refresh_products(sales_list: list):
        known_fuel_products.update(
            s.get("product_name") for s in sales_list if s.get("product_type") == "fuel" and s.get("product_name")
        )
        known_oil_products.update(
            s.get("product_name") for s in sales_list if s.get("product_type") == "oil" and s.get("product_name")
        )
        rebuild_product_options()

    def apply_product_filter(sales: list):
        if product_dropdown.value and product_dropdown.value != "all":
            return [s for s in sales if s.get("product_name") == product_dropdown.value]
        return sales

    refresh_attendants(cached_sales)
    refresh_products(cached_sales)

    def handle_from_date_change(e):
        if from_datepicker.value:
            val = from_datepicker.value
            from_date.value = val.strftime("%Y-%m-%d") if isinstance(val, (datetime, date)) else str(val)[:10]
            period_dropdown.value = "all"
            safe_ui_refresh(period_dropdown, from_date)
            load_data()

    def handle_to_date_change(e):
        if to_datepicker.value:
            val = to_datepicker.value
            to_date.value = val.strftime("%Y-%m-%d") if isinstance(val, (datetime, date)) else str(val)[:10]
            period_dropdown.value = "all"
            safe_ui_refresh(period_dropdown, to_date)
            load_data()

    from_datepicker = ft.DatePicker(on_change=handle_from_date_change)
    to_datepicker = ft.DatePicker(on_change=handle_to_date_change)
    page.overlay.extend([from_datepicker, to_datepicker])

    def open_from_picker(e):
        from_datepicker.open = True
        page.update()

    def open_to_picker(e):
        to_datepicker.open = True
        page.update()

    def clear_from_date(e):
        from_date.value = ""
        from_datepicker.value = None
        period_dropdown.value = "all"
        safe_ui_refresh(period_dropdown, from_date)
        load_data()

    def clear_to_date(e):
        to_date.value = ""
        to_datepicker.value = None
        period_dropdown.value = "all"
        safe_ui_refresh(period_dropdown, to_date)
        load_data()

    def handle_period_change(e):
        today = date.today()
        if period_dropdown.value == "daily":
            from_date.value = today.strftime("%Y-%m-%d")
            to_date.value = today.strftime("%Y-%m-%d")
        elif period_dropdown.value == "weekly":
            start_d = today - timedelta(days=6)
            from_date.value = start_d.strftime("%Y-%m-%d")
            to_date.value = today.strftime("%Y-%m-%d")
        elif period_dropdown.value == "monthly":
            start_d = today.replace(day=1)
            from_date.value = start_d.strftime("%Y-%m-%d")
            to_date.value = today.strftime("%Y-%m-%d")
        elif period_dropdown.value == "all":
            from_date.value = ""
            to_date.value = ""
            from_datepicker.value = None
            to_datepicker.value = None

        safe_ui_refresh(from_date, to_date)
        load_data()

    period_dropdown = ft.DropdownM2(
        label="Period", value="all", filled=True, fill_color="white", border_radius=6, 
        border_color="#CCCCCC", focused_border_color=DARK_RED, width=130, 
        options=[
            ft.dropdownm2.Option("all","All"),
            ft.dropdownm2.Option("daily","Daily"), 
            ft.dropdownm2.Option("weekly","Weekly"), 
            ft.dropdownm2.Option("monthly","Monthly")
        ],
        on_change=handle_period_change
    )

    from_date = ft.TextField(
        label="From Date", hint_text="Select date", read_only=True, filled=True, fill_color="white", 
        border_radius=6, border_color="#CCCCCC", focused_border_color=DARK_RED, width=170, 
        text_style=ft.TextStyle(size=13),
        suffix=ft.Row(
            controls=[
                ft.IconButton(icon=ft.Icons.CLEAR, icon_size=16, icon_color="#888888", on_click=clear_from_date, tooltip="Clear From Date"),
                ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, icon_size=18, icon_color=DARK_RED, on_click=open_from_picker, tooltip="Select From Date"),
            ],
            tight=True,
            spacing=0,
        ),
        on_click=open_from_picker
    )
    to_date = ft.TextField(
        label="To Date", hint_text="Select date", read_only=True, filled=True, fill_color="white", 
        border_radius=6, border_color="#CCCCCC", focused_border_color=DARK_RED, width=170, 
        text_style=ft.TextStyle(size=13),
        suffix=ft.Row(
            controls=[
                ft.IconButton(icon=ft.Icons.CLEAR, icon_size=16, icon_color="#888888", on_click=clear_to_date, tooltip="Clear To Date"),
                ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, icon_size=18, icon_color=DARK_RED, on_click=open_to_picker, tooltip="Select To Date"),
            ],
            tight=True,
            spacing=0,
        ),
        on_click=open_to_picker
    )

    columns = ["Attendant", "Date & Time", "Type", "Item", "Pump", "Quantity", "Amount", "Paid", "Change", "Payment", "Recorded By"]
    col_widths = [130, 160, 80, 120, 80, 80, 90, 90, 90, 80, 100]

    def header_cell(text, width): 
        return ft.Container(content=ft.Text(text, size=12, color="#555555", weight=ft.FontWeight.W_600), width=width, padding=ft.Padding.symmetric(horizontal=8, vertical=10))
    def data_cell(text, width, bold=False, color="#111111"): 
        return ft.Container(content=ft.Text(text, size=12, color=color, weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL, overflow=ft.TextOverflow.ELLIPSIS), width=width, padding=ft.Padding.symmetric(horizontal=8, vertical=12))
    def fuel_badge(label: str):
        bg = "#C62828" if label=="fuel" else "#6A1B9A"
        icon = ft.Icons.LOCAL_GAS_STATION if label=="fuel" else ft.Icons.SHOPPING_CART
        return ft.Container(content=ft.Row(controls=[ft.Icon(icon, size=12, color="white"), ft.Text(label, size=11, color="white", weight=ft.FontWeight.BOLD)], spacing=4, tight=True), bgcolor=bg, border_radius=12, padding=ft.Padding.symmetric(horizontal=10, vertical=4))

    table_header = ft.Container(content=ft.Row(controls=[header_cell(col, col_widths[i]) for i, col in enumerate(columns)], spacing=0), border=ft.Border.only(bottom=ft.BorderSide(1, "#E0E0E0")))
    
    def show_snack(msg, color=DARK_RED):
        snack = ft.SnackBar(content=ft.Text(msg, color="white"), bgcolor=color, open=True)
        page.overlay.append(snack)
        page.update()

    def go_dashboard(e):
        from pages.admin_dashboard import dashboard_page
        page.controls.clear()
        page.add(dashboard_page(page, auth))
        page.update()

    def go_logout(e):
        try:
            from admin import build_login_view
            auth.clear(); page.controls.clear()
            page.add(build_login_view(page, auth)); page.update()
        except Exception:
            auth.clear(); page.controls.clear()
            page.add(ft.Container(expand=True, alignment=ft.Alignment.CENTER, content=ft.Text("Logged out")))
            page.update()

    def make_summary_card(label, text_control, icon, icon_color):
        return ft.Container(
            content=ft.Column(controls=[ft.Row(controls=[ft.Text(label, size=12, color="#555555"), ft.Icon(icon, size=16, color=icon_color)], spacing=6), text_control], spacing=6, tight=True),
            bgcolor="white", border_radius=8, padding=ft.Padding.symmetric(horizontal=16, vertical=14), width=160, shadow=ft.BoxShadow(blur_radius=4, color="#00000015", offset=ft.Offset(0, 2)),
        )

    def build_rows(sales: list, search_query=""):
        if search_query:
            sq = search_query.lower()
            sales = [s for s in sales if sq in s.get("product_name","").lower() or sq in s.get("attendant_name","").lower() or sq in s.get("pump_name","").lower()]

        rows = []
        for i, s in enumerate(sales):
            try: dt_str = datetime.fromisoformat(s["sold_at"].replace("Z","+00:00")).strftime("%b %d, %Y, %I:%M %p")
            except: dt_str = s.get("sold_at","")[:16]

            paid = s.get("paid_amount", s.get("amount_paid", s.get("cash_given", s.get("cash", 0))))
            change = s.get("change_amount", s.get("change", s.get("change_given", 0)))

            row = ft.Container(
                content=ft.Row(controls=[
                    data_cell(s.get("attendant_name",""), col_widths[0]), data_cell(dt_str, col_widths[1]),
                    ft.Container(content=fuel_badge(s.get("product_type","")), width=col_widths[2], padding=ft.Padding.symmetric(horizontal=8, vertical=8)),
                    data_cell(s.get("product_name",""), col_widths[3]), data_cell(s.get("pump_name","-"), col_widths[4]),
                    data_cell(f"{s.get('quantity',0):.1f}{s.get('unit','')}", col_widths[5]), data_cell(f"₱{s.get('total_amount',0):.2f}", col_widths[6], bold=True, color=DARK_RED),
                    data_cell(f"₱{paid:.2f}", col_widths[7], bold=True), data_cell(f"₱{change:.2f}", col_widths[8], color="#2E7D32"),
                    data_cell(s.get("payment_method",""), col_widths[9]), data_cell(s.get("recorded_by",""), col_widths[10]),
                ], spacing=0), bgcolor="#FAFAFA" if i%2==0 else "white", border=ft.Border.only(bottom=ft.BorderSide(1, "#F0F0F0")),
            )
            rows.append(row)

        if not rows:
            rows = [ft.Container(padding=20, content=ft.Text("No transactions found", size=13, color="#888888", text_align=ft.TextAlign.CENTER))]
        return rows

    initial_controls = [table_header]
    if cache:
        initial_controls.extend(build_rows(cached_sales, ""))
    else:
        initial_controls.append(ft.Container(padding=20, content=ft.Row([ft.ProgressRing(width=16, height=16, color=DARK_RED), ft.Text("Loading transactions...", size=13, color="#777777")], spacing=10)))

    table_column = ft.Column(controls=initial_controls, spacing=0, scroll=ft.ScrollMode.ADAPTIVE)

    def load_data():
    # Only set loading spinner if the table is already mounted on the page
        if is_mounted(table_column):
            table_column.controls = [
                table_header, 
                ft.Container(
                    padding=20, 
                    content=ft.Row([
                        ft.ProgressRing(width=16, height=16, color=DARK_RED), 
                        ft.Text("Updating transactions...", size=13, color="#777777")
                    ], spacing=10)
                )
            ]
            safe_ui_refresh(table_column)

        def bg():
            time.sleep(0.05)
            sd = from_date.value.strip() if from_date.value else None
            ed = to_date.value.strip() if to_date.value else None
            try: 
                if sd: date.fromisoformat(sd)
            except: sd = None
            try: 
                if ed: date.fromisoformat(ed)
            except: ed = None

            try:
                data = get_unified_history(
                    auth, 
                    product_type=type_dropdown.value, 
                    attendant_name=attendant_dropdown.value, 
                    start_date=sd, 
                    end_date=ed, 
                    page=1, 
                    page_size=200
                )
            
                auth["history_cache"] = data
            
                total_sales_text.value = f"₱{data.get('total_amount',0):,.2f}"
                transactions_text.value = str(data.get("total_count",0))
            
                sales = data.get("sales",[])
                fuel_sales_text.value = str(sum(1 for s in sales if s.get("product_type")=="fuel"))
                oil_sales_text.value = str(sum(1 for s in sales if s.get("product_type")=="oil"))

                refresh_attendants(sales)
                refresh_products(sales)
                last_loaded_sales["data"] = sales

                table_column.controls = [table_header] + build_rows(apply_product_filter(sales))
            
                safe_ui_refresh(
                    total_sales_text, 
                    transactions_text, 
                    fuel_sales_text, 
                    oil_sales_text, 
                    table_column
                )
            except Exception as ex:
                print(f"[history] load_data error: {ex}")
                table_column.controls = [
                    table_header, 
                    ft.Container(padding=20, content=ft.Text(f"Failed to load transactions: {ex}", size=13, color="#C62828"))
                ]
                safe_ui_refresh(table_column)

        page.run_thread(bg)

    def handle_type_change(e):
        rebuild_product_options()
        load_data()

    def handle_product_change(e):
        filtered = apply_product_filter(last_loaded_sales["data"])
        table_column.controls = [table_header] + build_rows(filtered)
        safe_ui_refresh(table_column)

    type_dropdown.on_change = handle_type_change
    product_dropdown.on_change = handle_product_change
    attendant_dropdown.on_change = lambda e: load_data()

    def do_export(e):
        def bg():
            time.sleep(0.05)
            try:
                sd, ed = from_date.value.strip() if from_date.value else None, to_date.value.strip() if to_date.value else None
                csv_text = export_history_csv(auth, product_type=type_dropdown.value, start_date=sd, end_date=ed)
                downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
                os.makedirs(downloads_dir, exist_ok=True)
                filename = f"sales_{sd or 'all'}_{ed or 'all'}.csv"
                path = os.path.join(downloads_dir, filename)
                with open(path, "w", encoding="utf-8", newline="") as f: f.write(csv_text)
                show_snack(f"Exported to Downloads: {filename}", "#2E7D32")
            except Exception as ex:
                show_snack(f"Export failed: {ex}", DARK_RED)
        page.run_thread(bg)

    export_button = ft.Button(content="EXPORT CSV", icon=ft.Icons.DOWNLOAD, bgcolor=DARK_RED, color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), text_style=ft.TextStyle(size=13, weight=ft.FontWeight.BOLD)), height=40, on_click=do_export)

    summary_row = ft.Row(controls=[
        make_summary_card("Total Sales", total_sales_text, ft.Icons.TRENDING_UP, "#4CAF50"),
        make_summary_card("Transactions", transactions_text, ft.Icons.LIST_ALT, "#1565C0"),
        make_summary_card("Fuel Sales", fuel_sales_text, ft.Icons.LOCAL_GAS_STATION, "#C62828"),
        make_summary_card("Oil Sales", oil_sales_text, ft.Icons.SHOPPING_CART, "#6A1B9A"),
    ], spacing=12)

    filters_section = ft.Container(
        content=ft.Column(controls=[
            ft.Text("Filters", size=14, weight=ft.FontWeight.BOLD, color="#222222"), 
            ft.Container(height=8), 
            ft.Row(controls=[type_dropdown, product_dropdown, attendant_dropdown, period_dropdown, from_date, to_date], spacing=12, wrap=True)
        ], spacing=0, tight=True),
        bgcolor="white", border_radius=8, padding=ft.Padding.symmetric(horizontal=20, vertical=16), shadow=ft.BoxShadow(blur_radius=4, color="#00000015", offset=ft.Offset(0, 2)),
    )

    table_section = ft.Container(content=table_column, bgcolor="white", border_radius=8, shadow=ft.BoxShadow(blur_radius=4, color="#00000015", offset=ft.Offset(0, 2)), clip_behavior=ft.ClipBehavior.HARD_EDGE, expand=True)

    header = ft.Container(
        content=ft.Row([
            ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=TEXT_WHITE, on_click=go_dashboard),
            ft.Text("History", color=TEXT_WHITE, size=22, weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.Text("U-Fuel", color=TEXT_WHITE, size=18, weight=ft.FontWeight.BOLD),
                ft.Container(width=42, height=42, bgcolor=TEXT_WHITE, border_radius=20, clip_behavior=ft.ClipBehavior.HARD_EDGE, content=ft.Image(src="u-fuel_logo.jpg", fit=ft.BoxFit.CONTAIN, border_radius=20)),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=DARK_RED, padding=ft.Padding.symmetric(vertical=18, horizontal=24),
    )

    footer = ft.Container(
        content=ft.Row([
            ft.Container(content=ft.Row([ft.Icon(ft.Icons.LOGOUT, color=TEXT_WHITE, size=16), ft.Text("LOGOUT", color=TEXT_WHITE, size=13, weight=ft.FontWeight.BOLD)], spacing=6), bgcolor="#6B6B6B", border_radius=6, padding=ft.Padding.symmetric(vertical=8, horizontal=14), ink=True, on_click=go_logout),
            ft.Text("GAStoKITA", color=TEXT_WHITE, size=12, weight=ft.FontWeight.W_500),
            ft.Row([ft.Icon(ft.Icons.PERSON_OUTLINE, color=TEXT_WHITE, size=18), ft.Text(auth.get("name","ADMIN"), color=TEXT_WHITE, size=13, weight=ft.FontWeight.BOLD)], spacing=4),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER), bgcolor=DARK_RED, padding=ft.Padding.symmetric(vertical=14, horizontal=24),
    )

    content = ft.Container(
        content=ft.Column(controls=[summary_row, ft.Container(height=16), filters_section, ft.Container(height=16), table_section, ft.Container(height=16), ft.Row(controls=[export_button], alignment=ft.MainAxisAlignment.END)], scroll=ft.ScrollMode.ADAPTIVE, spacing=0, expand=True),
        padding=ft.Padding.all(24), expand=True,
    )

    load_data()

    return ft.Column(controls=[header, content, footer], spacing=0, expand=True)
127.0.0.1