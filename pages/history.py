import flet as ft
import os, requests, time
from datetime import datetime, date

DARK_RED   = "#8B0000"
TEXT_WHITE = "#FFFFFF"
BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

def _headers(auth: dict):
    token = auth.get("access_token") or auth.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}

def get_unified_history(auth: dict, product_type=None, attendant_name=None, start_date=None, end_date=None, page=1, page_size=100):
    params = {"page": page, "page_size": page_size}
    if product_type and product_type != "all": params["product_type"] = product_type
    if attendant_name and attendant_name != "all": params["attendant_name"] = attendant_name
    if start_date: params["start_date"] = start_date
    if end_date: params["end_date"] = end_date
    try:
        r = requests.get(f"{BASE_URL}/api/sales/history", params=params, headers=_headers(auth), timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as ex:
        print(f"[history] {ex}")
        return {"sales":[],"total_count":0,"total_amount":0,"total_liters":0,"total_oil_pcs":0}

def export_history_csv(auth: dict, product_type=None, start_date=None, end_date=None):
    params = {}
    if product_type and product_type != "all": params["product_type"] = product_type
    if start_date: params["start_date"] = start_date
    if end_date: params["end_date"] = end_date
    try:
        r = requests.get(f"{BASE_URL}/api/sales/history/export", params=params, headers=_headers(auth), timeout=15)
        r.raise_for_status()
        return r.text
    except Exception as ex:
        raise Exception(f"Export failed: {ex}")

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

    search_field = ft.TextField(hint_text="Search", filled=True, fill_color="white", border_radius=6, border_color="#CCCCCC", focused_border_color=DARK_RED, height=42, width=160, text_style=ft.TextStyle(size=13), content_padding=ft.Padding.symmetric(horizontal=12, vertical=8))
    type_dropdown = ft.Dropdown(label="Type", value="all", filled=True, fill_color="white", border_radius=6, border_color="#CCCCCC", focused_border_color=DARK_RED, width=100, options=[ft.dropdown.Option("all","All"), ft.dropdown.Option("fuel","Fuel"), ft.dropdown.Option("oil","Oils")])
    attendant_dropdown = ft.Dropdown(label="Attendant", value="all", filled=True, fill_color="white", border_radius=6, border_color="#CCCCCC", focused_border_color=DARK_RED, width=160, options=[
        ft.dropdown.Option("all","All Attendants"), ft.dropdown.Option("Attendant 1","Pump Attendant 1"), ft.dropdown.Option("Attendant 2","Pump Attendant 2"), ft.dropdown.Option("Attendant 3","Pump Attendant 3"),
    ])
    from_date = ft.TextField(label="From Date", hint_text="yyyy-mm-dd", filled=True, fill_color="white", border_radius=6, border_color="#CCCCCC", focused_border_color=DARK_RED, width=140, text_style=ft.TextStyle(size=13))
    to_date = ft.TextField(label="To Date", hint_text="yyyy-mm-dd", filled=True, fill_color="white", border_radius=6, border_color="#CCCCCC", focused_border_color=DARK_RED, width=140, text_style=ft.TextStyle(size=13))

    columns = ["Attendant", "Date & Time", "Type", "Item", "Pump", "Quantity", "Amount", "Payment", "Recorded By"]
    col_widths = [130, 160, 80, 120, 80, 80, 90, 80, 100]

    def header_cell(text, width): return ft.Container(content=ft.Text(text, size=12, color="#555555", weight=ft.FontWeight.W_600), width=width, padding=ft.Padding.symmetric(horizontal=8, vertical=10))
    def data_cell(text, width, bold=False, color="#111111"): return ft.Container(content=ft.Text(text, size=12, color=color, weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL, overflow=ft.TextOverflow.ELLIPSIS), width=width, padding=ft.Padding.symmetric(horizontal=8, vertical=12))
    def fuel_badge(label: str):
        bg = "#C62828" if label=="fuel" else "#6A1B9A"
        icon = ft.Icons.LOCAL_GAS_STATION if label=="fuel" else ft.Icons.SHOPPING_CART
        return ft.Container(content=ft.Row(controls=[ft.Icon(icon, size=12, color="white"), ft.Text(label, size=11, color="white", weight=ft.FontWeight.BOLD)], spacing=4, tight=True), bgcolor=bg, border_radius=12, padding=ft.Padding.symmetric(horizontal=10, vertical=4))

    table_header = ft.Container(content=ft.Row(controls=[header_cell(col, col_widths[i]) for i, col in enumerate(columns)], spacing=0), border=ft.Border.only(bottom=ft.BorderSide(1, "#E0E0E0")))
    
    def show_snack(msg, color=DARK_RED):
        page.snack_bar = ft.SnackBar(content=ft.Text(msg, color="white"), bgcolor=color)
        page.snack_bar.open = True
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

            row = ft.Container(
                content=ft.Row(controls=[
                    data_cell(s.get("attendant_name",""), col_widths[0]), data_cell(dt_str, col_widths[1]),
                    ft.Container(content=fuel_badge(s.get("product_type","")), width=col_widths[2], padding=ft.Padding.symmetric(horizontal=8, vertical=8)),
                    data_cell(s.get("product_name",""), col_widths[3]), data_cell(s.get("pump_name","-") or s.get("brand","-"), col_widths[4]),
                    data_cell(f"{s.get('quantity',0):.1f}{s.get('unit','')}", col_widths[5]), data_cell(f"₱{s.get('total_amount',0):.2f}", col_widths[6], bold=True, color=DARK_RED),
                    data_cell(s.get("payment_method",""), col_widths[7]), data_cell(s.get("recorded_by",""), col_widths[8]),
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
        def bg():
            time.sleep(0.1)
            sd = from_date.value.strip() if from_date.value else None
            ed = to_date.value.strip() if to_date.value else None
            try: 
                if sd: date.fromisoformat(sd)
            except: sd = None
            try: 
                if ed: date.fromisoformat(ed)
            except: ed = None

            data = get_unified_history(auth, product_type=type_dropdown.value, attendant_name=attendant_dropdown.value, start_date=sd, end_date=ed, page=1, page_size=200)
            
            auth["history_cache"] = data
            
            total_sales_text.value = f"₱{data.get('total_amount',0):,.2f}"
            transactions_text.value = str(data.get("total_count",0))
            
            sales = data.get("sales",[])
            fuel_sales_text.value = str(sum(1 for s in sales if s.get("product_type")=="fuel"))
            oil_sales_text.value = str(sum(1 for s in sales if s.get("product_type")=="oil"))

            table_column.controls = [table_header] + build_rows(sales, search_field.value or "")
            try: page.update()
            except: pass
            
        page.run_thread(bg)

    search_field.on_change = lambda e: load_data()
    type_dropdown.on_change = lambda e: load_data()
    attendant_dropdown.on_change = lambda e: load_data()
    from_date.on_change = lambda e: load_data()
    to_date.on_change = lambda e: load_data()

    def do_export(e):
        def bg():
            time.sleep(0.1)
            try:
                sd, ed = from_date.value.strip() if from_date.value else None, to_date.value.strip() if to_date.value else None
                csv_text = export_history_csv(auth, product_type=type_dropdown.value, start_date=sd, end_date=ed)
                path = os.path.join(os.path.expanduser("~"), "Downloads", f"sales_{sd or 'all'}_{ed or 'all'}.csv")
                with open(path, "w", encoding="utf-8", newline="") as f: f.write(csv_text)
                show_snack(f"Exported to {path}", "#2E7D32")
            except Exception as ex: show_snack(f"Export failed: {ex}", DARK_RED)
        page.run_thread(bg)

    export_button = ft.Button(content="EXPORT CSV", icon=ft.Icons.DOWNLOAD, bgcolor=DARK_RED, color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), text_style=ft.TextStyle(size=13, weight=ft.FontWeight.BOLD)), height=40, on_click=do_export)

    summary_row = ft.Row(controls=[
        make_summary_card("Total Sales", total_sales_text, ft.Icons.TRENDING_UP, "#4CAF50"),
        make_summary_card("Transactions", transactions_text, ft.Icons.LIST_ALT, "#1565C0"),
        make_summary_card("Fuel Sales", fuel_sales_text, ft.Icons.LOCAL_GAS_STATION, "#C62828"),
        make_summary_card("Oil Sales", oil_sales_text, ft.Icons.SHOPPING_CART, "#6A1B9A"),
    ], spacing=12)

    filters_section = ft.Container(
        content=ft.Column(controls=[ft.Text("Filters", size=14, weight=ft.FontWeight.BOLD, color="#222222"), ft.Container(height=8), ft.Row(controls=[search_field, type_dropdown, attendant_dropdown, from_date, to_date], spacing=12, wrap=True)], spacing=0, tight=True),
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