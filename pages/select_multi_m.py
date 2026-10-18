import flet as ft
from pages.api_client_m import get_fuels, get_oils, PUMP_MAP

MOBILE_RED = "#8B0000"
GREEN = "#2E7D32"
YELLOW = "#F9A825"
BAR_GREEN = "#12B347"
BAR_YELLOW = "#F4B400"
BAR_RED = "#E3242B"
GCASH_BLUE = "#007CFF"
GRAY_BG = "#F5F5F5"

FALLBACK = {"Regular": 55.0, "Premium": 60.0, "Diesel": 50.0}
GCASH_MIN = 100.0


def build_multi_page_mobile(page: ft.Page, auth: dict):
    page.title = "Multi Sale"
    page.bgcolor = MOBILE_RED
    page.padding = 0
    page.window.width = 390
    page.window.height = 844
    page.window.resizable = False

    if "cart" not in auth:
        auth["cart"] = {"fuel_items": [], "oil_items": []}
    cart = auth["cart"]

    state = {"tab": "fuel"}  # "fuel" | "oil"

    # ---------- helpers ----------
    def show_snack(msg, color=MOBILE_RED):
        page.show_dialog(ft.SnackBar(content=ft.Text(msg), bgcolor=color))

    def cart_total():
        return sum(i["total"] for i in cart["fuel_items"]) + sum(i["total"] for i in cart["oil_items"])

    def cart_count():
        return len(cart["fuel_items"]) + len(cart["oil_items"])

    def loading_indicator():
        return ft.Container(
            content=ft.ProgressRing(color=MOBILE_RED, width=40, height=40, stroke_width=4),
            alignment=ft.Alignment.CENTER,
            expand=True,
        )

    def bar_color(pct):
        if pct > 60: return BAR_GREEN
        if pct > 25: return BAR_YELLOW
        return BAR_RED

    def go_back(e):
        auth["cart"] = {"fuel_items": [], "oil_items": []}
        from pages.select_m import build_transaction_page_mobile
        page.controls.clear()
        page.add(build_transaction_page_mobile(page, auth))
        page.update()

    # ---------- cart UI ----------
    cart_items_column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)
    sheet_total_text = ft.Text("₱0.00", size=22, weight=ft.FontWeight.BOLD, color=MOBILE_RED)
    badge_text = ft.Text("0", size=11, weight=ft.FontWeight.BOLD, color=MOBILE_RED)
    toggle_holder = ft.Container()
    # extra bottom padding so the floating cart button never covers the last card
    body_holder = ft.Container(expand=True, padding=ft.Padding.only(left=20, right=20, bottom=80))

    def cart_row(title, subtitle, on_remove):
        return ft.Container(
            bgcolor=GRAY_BG, border_radius=10, padding=ft.Padding.only(left=12, top=6, bottom=6, right=4),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(spacing=2, expand=True, controls=[
                        ft.Text(title, weight=ft.FontWeight.BOLD, size=13, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(subtitle, size=11, color="grey"),
                    ]),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="red", icon_size=20, on_click=on_remove),
                ],
            ),
        )

    def refresh_cart_ui():
        cart_items_column.controls.clear()

        for idx, item in enumerate(cart["fuel_items"]):
            def remove_fuel(e, i=idx):
                cart["fuel_items"].pop(i)
                refresh_cart_ui()
            unit_p = item.get("unit_price") or (item["total"] / item["liters_sold"] if item["liters_sold"] else 0)
            cart_items_column.controls.append(cart_row(
                f"Fuel: {item['fuel_name']}",
                f"{item['liters_sold']:.3f}L x ₱{unit_p:.2f}  =  ₱{item['total']:.2f}",
                remove_fuel,
            ))

        for idx, item in enumerate(cart["oil_items"]):
            def remove_oil(e, i=idx):
                cart["oil_items"].pop(i)
                refresh_cart_ui()
            cart_items_column.controls.append(cart_row(
                item["oil_name"],
                f"{item['quantity']} x ₱{item['price']:.2f}  =  ₱{item['total']:.2f}",
                remove_oil,
            ))

        if not cart_items_column.controls:
            cart_items_column.controls.append(
                ft.Container(content=ft.Text("Cart is empty", color="grey"), alignment=ft.Alignment.CENTER, padding=20)
            )

        total = cart_total()
        n = cart_count()
        cart_items_column.height = min(max(n * 64, 70), 300)
        sheet_total_text.value = f"₱{total:.2f}"
        badge_text.value = str(n) if n < 100 else "99+"
        cart_badge.visible = n > 0
        toggle_holder.content = build_toggle()
        page.update()

    # ---------- checkout ----------
    def proceed_checkout(e):
        num_fuel = len(cart["fuel_items"])
        num_oil = len(cart["oil_items"])
        if num_fuel == 0 and num_oil == 0:
            show_snack("Cart is empty")
            return

        auth["cart"] = cart

        if num_fuel == 1 and num_oil == 0:
            f = cart["fuel_items"][0]
            unit_p = f.get("unit_price") or (f["total"] / f["liters_sold"] if f["liters_sold"] else 0)
            tx = {
                "label": f["fuel_name"], "details": f"{f['liters_sold']:.3f}L x ₱{unit_p:.2f}",
                "total": f["total"], "liters": f["liters_sold"], "pump_id": f["pump_id"],
                "fuel_name": f["fuel_name"], "type": "fuel", "payment_method": "cash",
            }
        elif num_fuel == 0 and num_oil == 1:
            o = cart["oil_items"][0]
            tx = {
                "label": o["oil_name"], "details": f"{o['quantity']} x ₱{o['price']:.2f}",
                "total": o["total"], "quantity": o["quantity"], "oil_id": o["oil_id"],
                "type": "oil", "payment_method": "cash",
            }
        else:
            tx = {
                "label": f"({num_fuel + num_oil} items)", "details": "Multi-item Checkout",
                "total": cart_total(), "type": "multi", "payment_method": "cash",
            }

        page.pop_dialog()
        from pages.pos_m import build_pos_page_mobile
        page.controls.clear()
        page.add(build_pos_page_mobile(page, auth, tx))
        page.update()

    def confirm_gcash_multi(e):
        if cart_count() == 0:
            show_snack("Cart is empty")
            return
        total = cart_total()
        if total < GCASH_MIN:
            show_snack(f"GCash minimum total is ₱{GCASH_MIN:.2f} (Current: ₱{total:.2f})")
            return
        # TODO: port gcash_qr_dialog / create_gcash_dialog_checkout flow from select_multi.py
        show_snack("GCash checkout not wired up yet on mobile", color="grey")

    def open_cart_sheet(e=None):
        refresh_cart_ui()
        sheet = ft.BottomSheet(
            show_drag_handle=True,
            content=ft.Container(
                padding=ft.Padding.only(left=20, right=20, top=4, bottom=24),
                content=ft.Column(
                    tight=True, spacing=12,
                    controls=[
                        ft.Text("Cart", size=20, weight=ft.FontWeight.BOLD),
                        cart_items_column,
                        ft.Divider(height=1),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                            ft.Text("Total:", size=16, weight=ft.FontWeight.BOLD),
                            sheet_total_text,
                        ]),
                        ft.Row(spacing=10, controls=[
                            ft.FilledButton("Cash", bgcolor=MOBILE_RED, color="white", expand=True, height=46, on_click=proceed_checkout),
                            ft.FilledButton("GCash", bgcolor=GCASH_BLUE, color="white", expand=True, height=46, on_click=confirm_gcash_multi),
                        ]),
                    ],
                ),
            ),
        )
        page.show_dialog(sheet)

    # ---------- dialogs ----------
    def open_fuel_dialog(pump_name: str, price: float, stock: float):
        fuel_clean_name = pump_name.split()[0]
        pump_id = PUMP_MAP.get(pump_name, 1)
        lock = {"busy": False}
        liters_field = ft.TextField(label="Liters", keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)
        amount_field = ft.TextField(label="Amount (PHP)", keyboard_type=ft.KeyboardType.NUMBER)
        error_text = ft.Text("", color="red", size=12)

        def on_liters(e):
            if lock["busy"]: return
            lock["busy"] = True
            try:
                l = float(liters_field.value or 0)
                amount_field.value = f"{l * price:.2f}" if l > 0 else ""
                error_text.value = f"Only {stock:.1f}L left" if l > stock else ""
                page.update()
            except ValueError:
                pass
            finally:
                lock["busy"] = False

        def on_amount(e):
            if lock["busy"]: return
            lock["busy"] = True
            try:
                a = float(amount_field.value or 0)
                l = a / price if price else 0
                liters_field.value = f"{l:.3f}" if a > 0 else ""
                error_text.value = f"Only {stock:.1f}L left" if l > stock else ""
                page.update()
            except ValueError:
                pass
            finally:
                lock["busy"] = False

        liters_field.on_change = on_liters
        amount_field.on_change = on_amount

        def add_fuel(e):
            try:
                l = float(liters_field.value or 0)
                a = float(amount_field.value or 0)
                if l <= 0 and a <= 0:
                    error_text.value = "Enter liters or amount"; page.update(); return
                if l <= 0: l = a / price
                if a <= 0: a = l * price
                if l > stock:
                    error_text.value = f"Insufficient {stock:.1f}L"; page.update(); return
                cart["fuel_items"].append({
                    "pump_id": pump_id, "liters_sold": round(l, 3), "fuel_name": fuel_clean_name,
                    "unit_price": price, "total": round(a, 2),
                })
                page.pop_dialog()
                refresh_cart_ui()
            except Exception as ex:
                error_text.value = str(ex); page.update()

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text(f"{pump_name} - ₱{price:.2f}/L", weight=ft.FontWeight.BOLD),
            content=ft.Column(tight=True, controls=[
                ft.Text(f"Stock: {stock:.0f}L", size=12, color="grey"),
                liters_field, ft.Text("or", text_align=ft.TextAlign.CENTER), amount_field, error_text,
            ]),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()),
                ft.FilledButton("Add to Order", bgcolor=MOBILE_RED, color="white", on_click=add_fuel),
            ],
        ))

    def open_oil_dialog(oil: dict):
        oil_name = f"{oil.get('brand', '')} {oil.get('name', '')}".strip()
        price = oil["price"]
        stock = oil["stock"]
        qty_field = ft.TextField(label="Quantity", keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)
        total_field = ft.TextField(label="Total", read_only=True, value="₱0.00")
        error_text = ft.Text("", color="red", size=12)

        def on_qty(e):
            try:
                q = float(qty_field.value or 0)
                total_field.value = f"₱{q * price:.2f}" if q > 0 else "₱0.00"
                error_text.value = f"Only {stock} left" if q > stock else ""
                page.update()
            except ValueError:
                pass

        qty_field.on_change = on_qty

        def add_oil(e):
            try:
                q = int(float(qty_field.value or 0))
                if q <= 0:
                    error_text.value = "Enter qty"; page.update(); return
                if q > stock:
                    error_text.value = "Insufficient stock"; page.update(); return
                cart["oil_items"].append({
                    "oil_id": oil["id"], "quantity": q, "oil_name": oil_name,
                    "price": price, "total": round(q * price, 2),
                })
                page.pop_dialog()
                refresh_cart_ui()
            except Exception as ex:
                error_text.value = str(ex); page.update()

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text(oil_name, weight=ft.FontWeight.BOLD),
            content=ft.Column(tight=True, controls=[
                ft.Text(f"Stock: {stock} pcs | ₱{price:.2f}", size=12), qty_field, total_field, error_text,
            ]),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()),
                ft.FilledButton("Add to Order", bgcolor=MOBILE_RED, color="white", on_click=add_oil),
            ],
        ))

    # ---------- cards ----------
    def fuel_card(pump_name: str, color: str):
        base = pump_name.split()[0]
        fu = next((f for f in auth.get("fuels_data", []) if f["name"] == base), None)
        price = fu["price"] if fu else FALLBACK.get(base, 60.0)
        stock = fu["actual_liters"] if fu else 9999
        pct = fu.get("display_percentage", 100) if fu else 100

        return ft.Container(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH, spacing=6,
                controls=[
                    ft.Text(pump_name, size=13, weight=ft.FontWeight.BOLD, color="white", text_align=ft.TextAlign.CENTER),
                    ft.Text(f"₱{price:.2f}/L", size=11, color="white", text_align=ft.TextAlign.CENTER),
                    ft.Text(f"{pct:.0f}%", size=22, weight=ft.FontWeight.BOLD, color="white", text_align=ft.TextAlign.CENTER),
                    ft.ProgressBar(value=max(0, min(pct, 100)) / 100, color=bar_color(pct), bgcolor="white", bar_height=8, border_radius=4),
                ],
            ),
            bgcolor=color, border_radius=12, expand=True, ink=True,
            padding=ft.Padding.symmetric(horizontal=12, vertical=16),
            on_click=lambda e, n=pump_name, p=price, s=stock: open_fuel_dialog(n, p, s),
        )

    def oil_card(oil: dict):
        low = oil["stock"] <= oil.get("low_stock_threshold", 5)
        return ft.Container(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4,
                controls=[
                    ft.Icon(ft.Icons.WATER_DROP_OUTLINED, size=48, color="black"),
                    ft.Text(f"Stock: {oil['stock']}", size=11, weight=ft.FontWeight.BOLD, color=MOBILE_RED if low else "black"),
                    ft.Text(f"₱{oil['price']:.2f}", size=11, color="grey"),
                    ft.Text(f"{oil.get('brand', '')} {oil.get('name', '')}", size=12, weight=ft.FontWeight.BOLD,
                            color=MOBILE_RED, text_align=ft.TextAlign.CENTER, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ],
            ),
            border=ft.Border.all(1.5, MOBILE_RED), border_radius=12, bgcolor="white", expand=True, ink=True,
            padding=ft.Padding.symmetric(horizontal=12, vertical=16),
            on_click=lambda e, o=oil: open_oil_dialog(o),
        )

    def two_col_grid(cards):
        rows = []
        for i in range(0, len(cards), 2):
            pair = [cards[i]]
            if i + 1 < len(cards):
                pair += [ft.Container(width=12), cards[i + 1]]
            else:
                pair += [ft.Container(width=12), ft.Container(expand=True)]  # keep half-width
            rows.append(ft.Row(controls=pair, spacing=0))
        return ft.Column(controls=rows, spacing=12, scroll=ft.ScrollMode.ADAPTIVE, expand=True)

    # ---------- tab toggle + body ----------
    def build_body():
        if "fuels_data" not in auth and "oils_data" not in auth:
            return loading_indicator()

        if state["tab"] == "fuel":
            pumps = [
                ("Regular 1", GREEN), ("Regular 2", GREEN),
                ("Premium 1", MOBILE_RED), ("Premium 2", MOBILE_RED),
                ("Diesel 1", YELLOW), ("Diesel 2", YELLOW),
            ]
            return two_col_grid([fuel_card(n, c) for n, c in pumps])

        oils = [o for o in auth.get("oils_data", []) if o.get("stock", 0) > 0]
        if not oils:
            return ft.Container(content=ft.Text("No oil products in stock", color="grey"), alignment=ft.Alignment.CENTER, expand=True)
        return two_col_grid([oil_card(o) for o in oils])

    def switch_tab(key):
        state["tab"] = key
        toggle_holder.content = build_toggle()
        body_holder.content = build_body()
        page.update()

    def build_toggle():
        def seg(label, key, count):
            active = state["tab"] == key
            text = f"{label} ({count})" if count else label
            return ft.Container(
                content=ft.Text(text, size=13, weight=ft.FontWeight.BOLD, color="white" if active else MOBILE_RED, text_align=ft.TextAlign.CENTER),
                bgcolor=MOBILE_RED if active else "transparent",
                border_radius=20, padding=ft.Padding.symmetric(vertical=10), alignment=ft.Alignment.CENTER,
                expand=True, ink=True, on_click=lambda e, k=key: switch_tab(k),
            )

        return ft.Container(
            content=ft.Row(spacing=0, controls=[
                seg("Fuel", "fuel", len(cart["fuel_items"])),
                seg("Oil", "oil", len(cart["oil_items"])),
            ]),
            border=ft.Border.all(1.5, MOBILE_RED), border_radius=22, padding=2,
            margin=ft.Margin.symmetric(horizontal=20),
        )

    # ---------- data load ----------
    def load_data():
        if "fuels_data" not in auth:
            try:
                auth["fuels_data"] = get_fuels(auth)
            except Exception as ex:
                print(f"[Multi Mobile] get_fuels failed {ex}")
                auth["fuels_data"] = []
        if "oils_data" not in auth:
            try:
                auth["oils_data"] = get_oils(auth)
            except Exception as ex:
                print(f"[Multi Mobile] get_oils failed {ex}")
                auth["oils_data"] = []
        body_holder.content = build_body()
        page.update()

    # ---------- layout ----------
    cart_badge = ft.Container(
        content=badge_text, visible=False,
        bgcolor="white", border=ft.Border.all(1.5, MOBILE_RED), border_radius=10,
        width=22, height=22, alignment=ft.Alignment.CENTER,
        right=0, top=0,
    )
    cart_fab = ft.Stack(
        width=68, height=68,
        right=16, bottom=62,  # sits just above the footer, bottom-right
        controls=[
            ft.FloatingActionButton(
                icon=ft.Icons.SHOPPING_CART_OUTLINED,
                bgcolor=MOBILE_RED, foreground_color="white",
                on_click=open_cart_sheet,
                left=0, bottom=0,
            ),
            cart_badge,
        ],
    )

    header = ft.Container(
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column(spacing=0, controls=[
                    ft.Text("Pump", size=16, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Text("Attendant", size=16, weight=ft.FontWeight.BOLD, color="white"),
                ]),
                ft.Row(spacing=8, controls=[
                    ft.Text("U-FUEL", size=16, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Container(content=ft.Image(src="u-fuel_logo.jpg", width=40, height=40, fit=ft.BoxFit.CONTAIN),
                                 bgcolor="white", border_radius=8, padding=4, width=40, height=40),
                ]),
            ],
        ),
        padding=ft.Padding.symmetric(horizontal=20, vertical=14),
    )

    content_card = ft.Container(
        content=ft.Column(spacing=8, expand=True, controls=[
            ft.Row(spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=MOBILE_RED, on_click=go_back),
                ft.Text("Multi Sale", size=18, weight=ft.FontWeight.BOLD, color=MOBILE_RED),
            ]),
            toggle_holder,
            body_holder,
        ]),
        bgcolor="white",
        border_radius=ft.BorderRadius(top_left=28, top_right=28, bottom_left=0, bottom_right=0),
        expand=True, padding=ft.Padding.only(top=12, bottom=12),
    )

    footer = ft.Container(
        content=ft.Text("GAStoKITA", size=13, color="white", text_align=ft.TextAlign.CENTER),
        bgcolor=MOBILE_RED, padding=ft.Padding.symmetric(vertical=14), alignment=ft.Alignment.CENTER,
    )

    # initial state
    toggle_holder.content = build_toggle()
    body_holder.content = build_body()
    refresh_cart_ui()  # also restores the cart bar if returning from checkout with items

    if "fuels_data" not in auth or "oils_data" not in auth:
        page.run_thread(load_data)

    return ft.SafeArea(
        content=ft.Stack(
            expand=True,
            controls=[
                ft.Column(controls=[header, ft.Container(height=10), content_card, footer], expand=True, spacing=0),
                cart_fab,
            ],
        ),
        expand=True,
    )