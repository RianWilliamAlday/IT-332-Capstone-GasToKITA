import flet as ft
import os, asyncio
from datetime import datetime, date, timedelta
from pages.sidebar_m import Sidebar
from pages.api_client_m import get_cashier_history, get_unified_history, export_history_csv, save_receipt_pdf

MOBILE_RED = "#8B0000"
GREEN_BUTTON = "#118C4F"
PAGE_SIZE = 20

def build_history_page_mobile(page: ft.Page, auth: dict):
    page.title = "Transaction History"
    page.bgcolor = MOBILE_RED
    page.padding = 0
    page.window.width = 390
    page.window.height = 844
    page.window.resizable = False

    sidebar = Sidebar(page, auth, active="history")

    cache = auth.get("history_cache", {}) or {}
    cached_sales = cache.get("sales", []) or []

    pagination_state = {"current_page": 1, "page_size": PAGE_SIZE, "total_count": cache.get("total_count", 0)}
    type_state = {"value": "all"}
    req = {"id": 0}

    fuel_count_init = sum(1 if s.get("product_type") == "fuel" else str(s.get("product_name", "")).count("L)") for s in cached_sales)
    oil_count_init = sum(1 if s.get("product_type") == "oil" else str(s.get("product_name", "")).count("pcs)") for s in cached_sales)

    total_sales_text = ft.Text(f"₱{cache.get('total_amount', 0):,.2f}" if cache else "₱0.00", size=17, weight=ft.FontWeight.BOLD, color="#4CAF50")
    transactions_text = ft.Text(str(cache.get("total_count", 0)) if cache else "0", size=17, weight=ft.FontWeight.BOLD, color="#1565C0")
    fuel_sales_text = ft.Text(str(fuel_count_init), size=17, weight=ft.FontWeight.BOLD, color="#C62828")
    oil_sales_text = ft.Text(str(oil_count_init), size=17, weight=ft.FontWeight.BOLD, color="#6A1B9A")

    def is_mounted(control):
        try:
            return control.page is not None
        except (RuntimeError, AttributeError):
            return False

    def safe_ui_refresh(*controls):
        for c in controls:
            try:
                if is_mounted(c):
                    c.update()
            except Exception as ue:
                print(f"[history_m] control update failed: {ue}")

    def show_snack(msg, color=MOBILE_RED):
        page.show_dialog(ft.SnackBar(content=ft.Text(msg, color="white"), bgcolor=color))

    def go_back(e):
        from pages.select_pa_m import build_pa_page_mobile
        page.controls.clear()
        page.add(build_pa_page_mobile(page, auth))
        page.update()

    known_attendants = {s.get("attendant_name") for s in cached_sales if s.get("attendant_name")}
    known_fuel_products = {s.get("product_name") for s in cached_sales if s.get("product_type") == "fuel" and s.get("product_name")}
    known_oil_products = {s.get("product_name") for s in cached_sales if s.get("product_type") == "oil" and s.get("product_name")}
    last_loaded_sales = {"data": cached_sales}

    def dd(label, options):
        return ft.DropdownM2(
            label=label, value="all", filled=True, fill_color="white", border_radius=8,
            border_color="#CCCCCC", focused_border_color=MOBILE_RED, text_size=13,
            options=options,
        )

    attendant_dropdown = dd("Attendant", [ft.dropdownm2.Option("all", "All Attendants")])
    product_dropdown = dd("Product", [ft.dropdownm2.Option("all", "All Products")])
    period_dropdown = dd("Period", [
        ft.dropdownm2.Option("all", "All"), ft.dropdownm2.Option("daily", "Daily"),
        ft.dropdownm2.Option("weekly", "Weekly"), ft.dropdownm2.Option("monthly", "Monthly"),
        ft.dropdownm2.Option("yearly","Yearly")
    ])

    def refresh_attendants(sales_list):
        new_names = {s.get("attendant_name") for s in sales_list if s.get("attendant_name")}
        if new_names - known_attendants or len(attendant_dropdown.options) == 1:
            known_attendants.update(new_names)
            curr = attendant_dropdown.value
            opts = [ft.dropdownm2.Option("all", "All Attendants")] + [ft.dropdownm2.Option(n, n) for n in sorted(known_attendants)]
            attendant_dropdown.options = opts
            attendant_dropdown.value = curr if curr in [o.key for o in opts] else "all"
            safe_ui_refresh(attendant_dropdown)

    def rebuild_product_options():
        t = type_state["value"]
        names = known_fuel_products if t == "fuel" else known_oil_products if t == "oil" else (known_fuel_products | known_oil_products)
        curr = product_dropdown.value
        opts = [ft.dropdownm2.Option("all", "All Products")] + [ft.dropdownm2.Option(n, n) for n in sorted(names)]
        product_dropdown.options = opts
        product_dropdown.value = curr if curr in [o.key for o in opts] else "all"
        safe_ui_refresh(product_dropdown)

    def refresh_products(sales_list):
        known_fuel_products.update(s.get("product_name") for s in sales_list if s.get("product_type") == "fuel" and s.get("product_name"))
        known_oil_products.update(s.get("product_name") for s in sales_list if s.get("product_type") == "oil" and s.get("product_name"))
        rebuild_product_options()

    def apply_product_filter(sales):
        if product_dropdown.value and product_dropdown.value != "all":
            return [s for s in sales if product_dropdown.value in s.get("product_name", "")]
        return sales

    refresh_attendants(cached_sales)
    refresh_products(cached_sales)

    def make_date_field(label):
        return ft.TextField(
            label=label, hint_text="Select date", read_only=True, filled=True, fill_color="white",
            border_radius=8, border_color="#CCCCCC", focused_border_color=MOBILE_RED, text_size=13,
        )

    from_date = make_date_field("From Date")
    to_date = make_date_field("To Date")

    def open_picker(field):
        def on_pick(e):
            val = e.control.value
            if val:
                field.value = val.strftime("%Y-%m-%d") if isinstance(val, (datetime, date)) else str(val)[:10]
                period_dropdown.value = "all"
                pagination_state["current_page"] = 1
                safe_ui_refresh(period_dropdown, field)
                update_filter_badge()
                load_data()

        initial = None
        try:
            if field.value:
                initial = datetime.strptime(field.value, "%Y-%m-%d")
        except ValueError:
            pass
        page.show_dialog(ft.DatePicker(value=initial, on_change=on_pick))

    def clear_date(field):
        field.value = ""
        period_dropdown.value = "all"
        pagination_state["current_page"] = 1
        safe_ui_refresh(period_dropdown, field)
        update_filter_badge()
        load_data()

    def attach_date_controls(field):
        field.suffix = ft.Row(
            tight=True, spacing=0,
            controls=[
                ft.IconButton(icon=ft.Icons.CLEAR, icon_size=16, icon_color="#888888", on_click=lambda e, f=field: clear_date(f)),
                ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, icon_size=18, icon_color=MOBILE_RED, on_click=lambda e, f=field: open_picker(f)),
            ],
        )
        field.on_click = lambda e, f=field: open_picker(f)

    attach_date_controls(from_date)
    attach_date_controls(to_date)

    def handle_period_change(e):
        today = date.today()
        v = period_dropdown.value
        if v == "daily":
            from_date.value = to_date.value = today.strftime("%Y-%m-%d")
        elif v == "weekly":
            from_date.value = (today - timedelta(days=6)).strftime("%Y-%m-%d")
            to_date.value = today.strftime("%Y-%m-%d")
        elif v == "monthly":
            from_date.value = today.replace(day=1).strftime("%Y-%m-%d")
            to_date.value = today.strftime("%Y-%m-%d")
        elif v == "yearly":
            from_date.value = today.replace(month=1, day=1).strftime("%Y-%m-%d")
            to_date.value = today.strftime("%Y-%m-%d")
        else:
            from_date.value = ""
            to_date.value = ""
        pagination_state["current_page"] = 1
        safe_ui_refresh(from_date, to_date)
        update_filter_badge()
        load_data()

    def handle_product_change(e):
        table_controls(apply_product_filter(last_loaded_sales["data"]))
        update_filter_badge()
        safe_ui_refresh(list_column)

    def handle_attendant_change(e):
        pagination_state["current_page"] = 1
        update_filter_badge()
        load_data()

    period_dropdown.on_change = handle_period_change
    product_dropdown.on_change = handle_product_change
    attendant_dropdown.on_change = handle_attendant_change

    type_holder = ft.Container(expand=True)
    filter_badge_text = ft.Text("", size=10, weight=ft.FontWeight.BOLD, color="white")
    filter_badge = ft.Container(content=filter_badge_text, bgcolor=MOBILE_RED, border_radius=8, padding=ft.Padding.symmetric(horizontal=6, vertical=1), visible=False)

    def active_filter_count():
        n = 0
        if attendant_dropdown.value not in (None, "all"): n += 1
        if product_dropdown.value not in (None, "all"): n += 1
        if from_date.value: n += 1
        if to_date.value: n += 1
        return n

    def update_filter_badge():
        n = active_filter_count()
        filter_badge_text.value = str(n)
        filter_badge.visible = n > 0
        safe_ui_refresh(filter_badge)

    def switch_type(key):
        if type_state["value"] == key:
            return
        type_state["value"] = key
        pagination_state["current_page"] = 1
        type_holder.content = build_type_chips()
        safe_ui_refresh(type_holder)
        rebuild_product_options()
        load_data()

    def build_type_chips():
        def chip(label, key):
            active = type_state["value"] == key
            return ft.Container(
                content=ft.Text(label, size=12, weight=ft.FontWeight.BOLD, color="white" if active else MOBILE_RED, text_align=ft.TextAlign.CENTER),
                bgcolor=MOBILE_RED if active else "transparent",
                border_radius=18, padding=ft.Padding.symmetric(vertical=8), alignment=ft.Alignment.CENTER,
                expand=True, ink=True, on_click=lambda e, k=key: switch_type(k),
            )
        return ft.Container(
            content=ft.Row(spacing=0, controls=[chip("All", "all"), chip("Fuel", "fuel"), chip("Oils", "oil")]),
            border=ft.Border.all(1.5, MOBILE_RED), border_radius=20, padding=2,
        )

    type_holder.content = build_type_chips()

    filters_panel = ft.Container(
        visible=False, bgcolor="#F5F5F5", border_radius=12, padding=12,
        content=ft.Column(
            spacing=10, horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[attendant_dropdown, product_dropdown, period_dropdown, from_date, to_date],
        ),
    )

    def toggle_filters(e):
        filters_panel.visible = not filters_panel.visible
        filters_btn.bgcolor = "#FDECEC" if filters_panel.visible else "white"
        page.update()

    filters_btn = ft.Container(
        content=ft.Row(spacing=4, tight=True, controls=[
            ft.Icon(ft.Icons.TUNE, size=16, color=MOBILE_RED),
            ft.Text("Filters", size=12, weight=ft.FontWeight.BOLD, color=MOBILE_RED),
            filter_badge,
        ]),
        bgcolor="white", border=ft.Border.all(1.5, MOBILE_RED), border_radius=20,
        padding=ft.Padding.symmetric(horizontal=12, vertical=8), ink=True, on_click=toggle_filters,
    )

    def reprint_receipt(s: dict):
        def bg_print():
            tx_type = s.get("product_type", "fuel")
            sale_id = s.get("id") or s.get("sale_id")
            paid = s.get("amount_paid", s.get("paid_amount", s.get("total_amount", 0.0)))
            change = s.get("change_given", s.get("change_amount", 0.0))
            qty_unit = f"{s.get('quantity', 0):.1f}{s.get('unit', '')}"
            payload = {
                "label": s.get("product_name", ""),
                "details": f"{qty_unit} ({s.get('pump_name', '-')})" if s.get("pump_name") and s.get("pump_name") != "-" else qty_unit,
                "total": float(s.get("total_amount", 0.0)),
                "paid": float(paid),
                "change": float(change),
            }
            try:
                from pages.change import print_receipt_locally
                print_receipt_locally(payload, printer_name="XP-58H")
                show_snack("Receipt printed to thermal printer", GREEN_BUTTON)
            except Exception as err:
                print(f"[history_m] Thermal printer error: {err}. Falling back to PDF...")
                try:
                    receipt_no = s.get("receipt_no") or f"REC-{sale_id}"
                    path = save_receipt_pdf(auth, sale_id, receipt_no, tx_type)
                    show_snack(f"Printer offline - receipt PDF saved to {path}", GREEN_BUTTON)
                except Exception as pdf_err:
                    show_snack(f"Failed to generate receipt: {pdf_err}", MOBILE_RED)

        page.run_thread(bg_print)

    def type_badge(label):
        lbl = str(label or "fuel").lower()
        bg = "#C62828" if lbl == "fuel" else "#6A1B9A" if lbl == "oil" else "#0F3057"
        icon = ft.Icons.LOCAL_GAS_STATION if lbl == "fuel" else ft.Icons.WATER_DROP if lbl == "oil" else ft.Icons.SHOPPING_CART
        return ft.Container(
            content=ft.Row(spacing=4, tight=True, controls=[ft.Icon(icon, size=12, color="white"), ft.Text(lbl, size=11, color="white", weight=ft.FontWeight.BOLD)]),
            bgcolor=bg, border_radius=12, padding=ft.Padding.symmetric(horizontal=8, vertical=3),
        )

    def tx_card(s: dict):
        try:
            dt_str = datetime.fromisoformat(str(s.get("sold_at", "")).replace("Z", "+00:00")).strftime("%b %d, %Y, %I:%M %p")
        except Exception:
            dt_str = str(s.get("sold_at", ""))[:16]

        total_amt = float(s.get("total_amount") or 0.0)
        qty_val = float(s.get("quantity") or 0.0)
        paid = float(s.get("paid_amount") or s.get("amount_paid") or s.get("cash_given") or s.get("cash") or total_amt)
        change = float(s.get("change_amount") or s.get("change") or s.get("change_given") or 0.0)
        pump = s.get("pump_name") or "-"
        qty_line = f"{qty_val:.1f}{s.get('unit', '')}" + (f"  •  {pump}" if pump != "-" else "")

        return ft.Container(
            bgcolor="white", border=ft.Border.all(1, "#E6E6E6"), border_radius=12, padding=12,
            content=ft.Column(spacing=6, controls=[
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    type_badge(s.get("product_type", "")),
                    ft.Text(dt_str, size=11, color="#777777"),
                ]),
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.START, controls=[
                    ft.Text(s.get("product_name", ""), size=13, weight=ft.FontWeight.BOLD, color="#111111", expand=True, max_lines=3, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(f"₱{total_amt:,.2f}", size=15, weight=ft.FontWeight.BOLD, color=MOBILE_RED),
                ]),
                ft.Text(qty_line, size=12, color="#555555"),
                ft.Text(f"Paid ₱{paid:,.2f}  •  Change ₱{change:,.2f}", size=12, color="#2E7D32"),
                ft.Divider(height=1, color="#F0F0F0"),
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Column(spacing=0, expand=True, controls=[
                        ft.Text(f"{s.get('attendant_name', 'Unknown')}  •  {str(s.get('payment_method', 'cash')).title()}", size=11, color="#555555", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ]),
                    ft.Container(
                        content=ft.Row(spacing=3, tight=True, controls=[
                            ft.Icon(ft.Icons.PRINT, size=14, color=MOBILE_RED),
                            ft.Text("Receipt", size=11, weight=ft.FontWeight.BOLD, color=MOBILE_RED),
                        ]),
                        border=ft.Border.all(1, MOBILE_RED), border_radius=6,
                        padding=ft.Padding.symmetric(horizontal=10, vertical=6), ink=True,
                        on_click=lambda e, sale=s: reprint_receipt(sale),
                    ),
                ]),
            ]),
        )

    list_column = ft.Column(spacing=10)

    def message_box(controls_row=None, text="", color="#888888"):
        content = controls_row if controls_row is not None else ft.Text(text, size=13, color=color, text_align=ft.TextAlign.CENTER)
        return ft.Container(padding=20, alignment=ft.Alignment.CENTER, content=content)

    def loading_box(text):
        return message_box(controls_row=ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=10, controls=[
            ft.ProgressRing(width=16, height=16, color=MOBILE_RED), ft.Text(text, size=13, color="#777777"),
        ]))

    def table_controls(sales):
        cards = [tx_card(s) for s in sales]
        list_column.controls = cards if cards else [message_box(text="No transactions found")]

    if cache:
        table_controls(apply_product_filter(cached_sales))
    else:
        list_column.controls = [loading_box("Loading transactions...")]

    page_info_text = ft.Text("Page 1", size=13, weight=ft.FontWeight.BOLD, color="#555555")
    prev_btn = ft.IconButton(icon=ft.Icons.CHEVRON_LEFT, icon_color=MOBILE_RED)
    next_btn = ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT, icon_color=MOBILE_RED)

    def on_prev_page(e):
        if pagination_state["current_page"] > 1:
            pagination_state["current_page"] -= 1
            load_data()

    def on_next_page(e):
        max_pages = max(1, (pagination_state["total_count"] + PAGE_SIZE - 1) // PAGE_SIZE)
        if pagination_state["current_page"] < max_pages:
            pagination_state["current_page"] += 1
            load_data()

    prev_btn.on_click = on_prev_page
    next_btn.on_click = on_next_page

    pagination_row = ft.Row(alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=8, controls=[prev_btn, page_info_text, next_btn])

    def load_data():
        req["id"] += 1
        my_req = req["id"]

        if is_mounted(list_column):
            list_column.controls = [loading_box("Updating transactions...")]
            safe_ui_refresh(list_column)

        def bg():
            sd = from_date.value.strip() if from_date.value else None
            ed = to_date.value.strip() if to_date.value else None
            try:
                if sd: date.fromisoformat(sd)
            except ValueError:
                sd = None
            try:
                if ed: date.fromisoformat(ed)
            except ValueError:
                ed = None

            ptype = type_state["value"] if type_state["value"] != "all" else None
            att_name = attendant_dropdown.value if attendant_dropdown.value != "all" else None

            try:
                user_obj = auth.get("user") if isinstance(auth.get("user"), dict) else {}
                cashier_id = auth.get("user_id") or auth.get("id") or user_obj.get("id")
                kwargs = dict(product_type=ptype, attendant_name=att_name, start_date=sd, end_date=ed,
                              page=pagination_state["current_page"], page_size=PAGE_SIZE)
                if cashier_id:
                    data = get_cashier_history(auth, cashier_id=cashier_id, **kwargs)
                else:
                    data = get_unified_history(auth, **kwargs)

                if my_req != req["id"]:
                    return

                auth["history_cache"] = data
                total_sales_text.value = f"₱{float(data.get('total_amount', 0) or 0):,.2f}"
                total_cnt = int(data.get("total_count", 0) or 0)
                transactions_text.value = str(total_cnt)
                pagination_state["total_count"] = total_cnt

                sales = data.get("sales", []) or []
                fuel_sales_text.value = str(data.get("total_fuel_count", 0))
                oil_sales_text.value = str(data.get("total_oil_count", 0))

                refresh_attendants(sales)
                refresh_products(sales)
                last_loaded_sales["data"] = sales
                table_controls(apply_product_filter(sales))

                max_pages = max(1, (total_cnt + PAGE_SIZE - 1) // PAGE_SIZE)
                page_info_text.value = f"Page {pagination_state['current_page']} of {max_pages}"
                prev_btn.disabled = pagination_state["current_page"] <= 1
                next_btn.disabled = pagination_state["current_page"] >= max_pages

                safe_ui_refresh(total_sales_text, transactions_text, fuel_sales_text, oil_sales_text,
                                list_column, page_info_text, prev_btn, next_btn)
            except Exception as ex:
                print(f"[history_m] load_data error: {ex}")
                if my_req == req["id"]:
                    list_column.controls = [message_box(text=f"Failed to load transactions: {ex}", color="#C62828")]
                    safe_ui_refresh(list_column)

        page.run_thread(bg)

    file_picker = None
    try:
        file_picker = ft.FilePicker()
        page.services.append(file_picker)
    except Exception as fp_err:
        print(f"[history_m] FilePicker unavailable, export will use Downloads folder: {fp_err}")
        file_picker = None

    async def do_export(e):
        sd = from_date.value.strip() if from_date.value else None
        ed = to_date.value.strip() if to_date.value else None
        ptype = type_state["value"] if type_state["value"] != "all" else None
        filename = f"sales_{sd or 'all'}_{ed or 'all'}.csv"
        try:
            csv_text = await asyncio.to_thread(export_history_csv, auth, product_type=ptype, start_date=sd, end_date=ed)
            data = csv_text.encode("utf-8")

            if file_picker is not None:
                path = await file_picker.save_file(dialog_title="Save sales export", file_name=filename, src_bytes=data)
                if path:
                    if not os.path.exists(path):  # desktop may only return the chosen path
                        with open(path, "wb") as f:
                            f.write(data)
                    show_snack(f"Exported: {filename}", "#2E7D32")
            else:
                downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
                os.makedirs(downloads_dir, exist_ok=True)
                with open(os.path.join(downloads_dir, filename), "wb") as f:
                    f.write(data)
                show_snack(f"Exported to Downloads: {filename}", "#2E7D32")
        except Exception as ex:
            show_snack(f"Export failed: {ex}", MOBILE_RED)

    export_button = ft.Button(
        content="EXPORT CSV", icon=ft.Icons.DOWNLOAD, bgcolor=MOBILE_RED, color="white",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), text_style=ft.TextStyle(size=13, weight=ft.FontWeight.BOLD)),
        height=44, on_click=do_export,
    )

    def summary_card(label, text_control, icon, icon_color):
        return ft.Container(
            expand=True, bgcolor="white", border_radius=12, border=ft.Border.all(1, "#E6E6E6"),
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            content=ft.Column(spacing=4, tight=True, controls=[
                ft.Row(spacing=6, controls=[ft.Icon(icon, size=14, color=icon_color), ft.Text(label, size=11, color="#555555")]),
                text_control,
            ]),
        )

    summary_grid = ft.Column(spacing=10, controls=[
        ft.Row(spacing=10, controls=[
            summary_card("Total Sales", total_sales_text, ft.Icons.TRENDING_UP, "#4CAF50"),
            summary_card("Transactions", transactions_text, ft.Icons.LIST_ALT, "#1565C0"),
        ]),
        ft.Row(spacing=10, controls=[
            summary_card("Fuel Sales", fuel_sales_text, ft.Icons.LOCAL_GAS_STATION, "#C62828"),
            summary_card("Oil Sales", oil_sales_text, ft.Icons.WATER_DROP, "#6A1B9A"),
        ]),
    ])

    body = ft.Column(
        scroll=ft.ScrollMode.ADAPTIVE, expand=True, spacing=12,
        controls=[
            summary_grid,
            ft.Row(spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[type_holder, filters_btn]),
            filters_panel,
            list_column,
            pagination_row,
            export_button,
            ft.Container(height=8),
        ],
    )

    header = ft.Container(
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    sidebar.menu_button(),
                    ft.Column(spacing=0, controls=[
                        ft.Text("Pump", size=16, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Text("Attendant", size=16, weight=ft.FontWeight.BOLD, color="white"),
                    ]),
                ]),
                ft.Row(spacing=8, controls=[
                    ft.Text("U-FUEL", size=16, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Container(content=ft.Image(src="u-fuel_logo.jpg", width=40, height=40, fit=ft.BoxFit.CONTAIN),
                                 bgcolor="white", border_radius=8, padding=4, width=40, height=40),
                ]),
            ],
        ),
        padding=ft.Padding.only(left=8, right=20, top=10, bottom=10),
    )

    content_card = ft.Container(
        content=ft.Column(spacing=4, expand=True, controls=[
            ft.Row(spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=MOBILE_RED, on_click=go_back),
                ft.Text("History", size=18, weight=ft.FontWeight.BOLD, color=MOBILE_RED),
            ]),
            ft.Container(content=body, padding=ft.Padding.symmetric(horizontal=16), expand=True),
        ]),
        bgcolor="white",
        border_radius=ft.BorderRadius(top_left=28, top_right=28, bottom_left=0, bottom_right=0),
        expand=True, padding=ft.Padding.only(top=12),
    )

    footer = ft.Container(
        content=ft.Text("GAStoKITA", size=13, color="white", text_align=ft.TextAlign.CENTER),
        bgcolor=MOBILE_RED, padding=ft.Padding.symmetric(vertical=14), alignment=ft.Alignment.CENTER,
    )

    load_data()

    return ft.SafeArea(
        content=sidebar.wrap(ft.Column(controls=[header, ft.Container(height=10), content_card, footer], expand=True, spacing=0)),
        expand=True,
    )