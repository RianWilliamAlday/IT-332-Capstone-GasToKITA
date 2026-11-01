import flet as ft
import io, base64, time
from pages.api_client_m import (
    get_fuels, get_oils, PUMP_MAP,
    create_gcash_dialog_checkout, check_gcash_status, manual_confirm_gcash,
)
from pages.sidebar_m import Sidebar

MOBILE_RED = "#8B0000"
GREEN = "#2E7D32"
YELLOW = "#F9A825"
BAR_GREEN = "#12B347"

FALLBACK_PRICES = {
    "Regular": 55.0,
    "Premium": 60.0,
    "Diesel": 50.0,
}

def generate_qr_base64(url: str):
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as ex:
        print(f"[QR] Failed to generate QR: {ex}")
        return None

def create_fuel_card(title: str, price: float, percentage: float, on_click):
    base = title.split()[0]
    card_color = COLOR_REGULAR if "Regular" in base else COLOR_PREMIUM if "Premium" in base else COLOR_DIESEL

    return ft.Container(
        width=280, height=130, bgcolor=card_color, border_radius=18,
        border=ft.Border.all(1, "black"), padding=15, ink=True,
        on_click=lambda e: on_click(title, price, PUMP_MAP.get(title, 1)),
        content=ft.Column(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Text(f"₱{price:.2f}", size=12, color="white"),
                    ]
                ),
                ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text(f"{percentage:.0f}%", size=20, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Stack(
                            controls=[
                                ft.Container(height=14, width=185, bgcolor="white", border_radius=10),
                                ft.Container(
                                    height=14, 
                                    width=max(0, min(185, 185 * (percentage / 100))), 
                                    bgcolor=BAR_GREEN, 
                                    border_radius=10
                                )
                            ]
                        )
                    ]
                )
            ]
        )
    )

def generate_qr_base64(url: str):
    if not url:
        return None
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as ex:
        print(f"[QR] qrcode failed ({ex}), trying segno...")
    try:
        import segno
        buf = io.BytesIO()
        segno.make(url, error="m").save(buf, kind="png", scale=8, border=2)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as ex:
        print(f"[QR] segno failed: {ex}")
        return None


def create_oil_card(oil: dict, on_click):
    brand = oil.get("brand", "")
    name = oil.get("name", "")
    stock = oil.get("stock", 0)
    price = oil.get("price", 0.0)
    low = stock <= oil.get("low_stock_threshold", 5)
    card_bg = RED if low else WHITE
    text_main = WHITE if low else "#2B2D36"
    text_sub = "#FFD9DA" if low else "#5F6368"
    divider_color = "#E58A8D" if low else "#E5E7EB"

    def info_row(label, value):
        return ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=8,
            controls=[
                ft.Text(label, size=13, weight=ft.FontWeight.W_500, color=text_sub),
                ft.Text(value, size=13, weight=ft.FontWeight.W_600, color=text_main,
                        expand=True, text_align=ft.TextAlign.RIGHT,
                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
            ],
        )

    return ft.Container(
        width=280,
        bgcolor=card_bg,
        border_radius=20,
        padding=14,
        border=ft.Border.all(1, RED if low else "#E5E7EB"),
        shadow=ft.BoxShadow(blur_radius=12, color=ft.Colors.with_opacity(0.10, "black"), offset=ft.Offset(0, 4)),
        on_click=lambda e: on_click(oil),
        ink=True,
        content=ft.Column(
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                oil_card_image(oil, 150),
                ft.Text(f"Stock: {stock}", size=22, weight=ft.FontWeight.BOLD, color=text_main),
                ft.Text(f"\u20b1{price:.2f}", size=17, weight=ft.FontWeight.W_600, color=text_main),
                ft.Divider(height=1, color=divider_color),
                info_row("Brand:", brand),
                info_row("Item:", name),
            ],
        ),
    )

def build_multi_page(page: ft.Page, auth: dict):
    page.title = "Multi Sale"
    page.bgcolor = LIGHT_GRAY
    page.padding = 0

    sidebar = Sidebar(page, auth, active="pos")

    if "cart" not in auth:
        auth["cart"] = {"fuel_items": [], "oil_items": []}
    cart = auth["cart"]

    state = {"tab": "fuel"}

    def show_snack(msg, color=MOBILE_RED):
        page.show_dialog(ft.SnackBar(content=ft.Text(msg), bgcolor=color))

    def go_back(e):
        auth["cart"] = {"fuel_items": [], "oil_items": []}
        from pages.select_pa_m import build_pa_page_mobile
        page.controls.clear()
        page.add(build_pa_page_mobile(page, auth))
        page.update()

    cart_items_column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)
    sheet_total_text = ft.Text("₱0.00", size=22, weight=ft.FontWeight.BOLD, color=MOBILE_RED)
    badge_text = ft.Text("0", size=11, weight=ft.FontWeight.BOLD, color=MOBILE_RED)
    toggle_holder = ft.Container()
    body_holder = ft.Container(expand=True, padding=ft.Padding.symmetric(horizontal=20))

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
        grand_total = 0.0

        for idx, item in enumerate(cart["fuel_items"]):
            grand_total += item["total"]
            def remove_fuel(e, i=idx):
                cart["fuel_items"].pop(i)
                refresh_cart_ui()

            unit_p = item.get("unit_price") or (item["total"] / item["liters_sold"] if item["liters_sold"] else 0)
            cart_items_column.controls.append(
                ft.Container(
                    bgcolor="#F5F5F5", border_radius=8, padding=10,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(spacing=2, controls=[
                                ft.Text(f"Fuel: {item['fuel_name']}", weight=ft.FontWeight.BOLD, size=13),
                                ft.Text(f"{item['liters_sold']:.3f}L x ₱{unit_p:.2f}", size=11, color="grey"),
                            ]),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="red", icon_size=18, on_click=remove_fuel)
                        ]
                    )
                )
            )

        for idx, item in enumerate(cart["oil_items"]):
            grand_total += item["total"]
            def remove_oil(e, i=idx):
                cart["oil_items"].pop(i)
                refresh_cart_ui()

            cart_items_column.controls.append(
                ft.Container(
                    bgcolor="#F5F5F5", border_radius=8, padding=10,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(spacing=2, controls=[
                                ft.Text(item['oil_name'], weight=ft.FontWeight.BOLD, size=13),
                                ft.Text(f"{item['quantity']} x ₱{item['price']:.2f}", size=11, color="grey"),
                            ]),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="red", icon_size=18, on_click=remove_oil)
                        ]
                    )
                )
            )

        total_text.value = f"₱{grand_total:.2f}"
        page.update()

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

    def build_paid_tx(prod_type, total_amt, sale_id):
        """The tx dict the change page expects, built from the current cart."""
        if prod_type == "fuel":
            f = cart["fuel_items"][0]
            unit_p = f.get("unit_price") or (f["total"] / f["liters_sold"] if f["liters_sold"] else 0)
            tx = {
                "label": f["fuel_name"], "details": f"{f['liters_sold']:.3f}L x ₱{unit_p:.2f}",
                "total": total_amt, "liters": f["liters_sold"], "pump_id": f["pump_id"],
                "fuel_name": f["fuel_name"], "type": "fuel",
            }
        elif prod_type == "oil":
            o = cart["oil_items"][0]
            tx = {
                "label": o["oil_name"], "details": f"{o['quantity']} x ₱{o['price']:.2f}",
                "total": total_amt, "quantity": o["quantity"], "oil_id": o["oil_id"], "type": "oil",
            }
        else:
            tx = {
                "label": f"({cart_count()} items)", "details": f"GCash PAID - ₱{total_amt:.2f}",
                "total": total_amt, "type": "multi",
            }
        tx.update({"payment_method": "gcash", "sale_id": sale_id, "is_paid": True})
        return tx

    def finish_gcash(prod_type, total_amt, sale_id, result):
        tx = build_paid_tx(prod_type, total_amt, sale_id)
        auth["cart"] = {"fuel_items": [], "oil_items": []}
        try:
            from pages.change_m import build_change_page_mobile
        except ImportError:
            receipt = (result or {}).get("receipt_no", "PAID")
            show_snack(f"GCash payment confirmed ({receipt})", "#2E7D32")
            go_back(None)
            return
        page.controls.clear()
        page.add(build_change_page_mobile(page, auth, tx, paid=total_amt, change=0, sale=result, tx_type=prod_type))
        page.update()

    def gcash_qr_dialog(gcash_data: dict, grand_total: float, prod_type: str = "multi"):
        total_amt = float(gcash_data.get("total_amount", grand_total))
        sale_id = gcash_data.get("transaction_ref") or gcash_data.get("sale_id") or gcash_data.get("oil_sale_id")
        checkout_id = gcash_data.get("checkout_id")
        checkout_url = gcash_data.get("checkout_url", "")

        state = {"active": True, "busy": False, "sale_id": sale_id}

        qr_b64 = generate_qr_base64(checkout_url)
        if qr_b64:
            qr_image = ft.Image(src=qr_b64, width=220, height=220, fit=ft.BoxFit.CONTAIN)
        else:
            qr_image = ft.Text("QR failed, use the link below", size=11, color="grey")

        status_text = ft.Text("Waiting for GCash payment...", color=GCASH_BLUE, size=12,
                              weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)

        def close_all(e=None):
            state["active"] = False
            page.pop_dialog()

        def finalize():
            """Confirm the sale on the backend, then go to the change page. Safe to call twice."""
            if state["busy"]:
                return
            state["busy"] = True
            try:
                status_text.value = "Confirming payment..."
                page.update()
                result = manual_confirm_gcash(auth, sale_id, product_type=prod_type)
            except Exception as ex:
                status_text.value = f"Confirm failed: {ex}"
                page.update()
                state["busy"] = False
                return
            state["active"] = False
            status_text.value = f"Paid! {(result or {}).get('receipt_no', '')}".strip()
            page.update()
            time.sleep(0.8)
            page.pop_dialog()
            finish_gcash(prod_type, total_amt, state["sale_id"], result)

        def auto_poll():
            while state["active"]:
                time.sleep(3)
                if not state["active"]:
                    break
                try:
                    status = check_gcash_status(auth, checkout_id)
                    if status.get("is_paid"):
                        state["sale_id"] = status.get("sale_id") or sale_id
                        finalize()
                except Exception as ex:
                    print(f"[GCash Multi Poll] {ex}")

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text(f"GCash - ₱{total_amt:.2f}", weight=ft.FontWeight.BOLD),
            content=ft.Column(
                tight=True, spacing=10, width=260, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("Fuel / Oil Sale" if prod_type != "multi" else "Multi-Item Sale", size=12, color="grey"),
                    ft.Container(content=qr_image, alignment=ft.Alignment.CENTER, bgcolor="white", border_radius=8, padding=4),
                    ft.TextButton("Open GCash Checkout", url=checkout_url, style=ft.ButtonStyle(color=GCASH_BLUE)),
                    status_text,
                ],
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_all),
                ft.TextButton("Manual Confirm", on_click=lambda e: page.run_thread(finalize)),
            ],
        ))
        page.run_thread(auto_poll)

    def confirm_gcash_multi(e):
        num_fuel = len(cart["fuel_items"])
        num_oil = len(cart["oil_items"])
        if num_fuel == 0 and num_oil == 0:
            show_snack("Cart is empty")
            return
        grand_total = cart_total()
        if grand_total < GCASH_MIN:
            show_snack(f"GCash minimum total is ₱{GCASH_MIN:.2f} (Current: ₱{grand_total:.2f})")
            return

        attendant_name = auth.get("selected_attendant") or (auth.get("user") or {}).get("name") or "Attendant 1"

        page.pop_dialog()
        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("Creating GCash Checkout..."),
            content=ft.Column(tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                              controls=[ft.ProgressRing(color=MOBILE_RED), ft.Text("Contacting PayMongo...")]),
        ))

        def do_create():
            try:
                if num_fuel == 1 and num_oil == 0:
                    f = cart["fuel_items"][0]
                    gcash_data = create_gcash_dialog_checkout(
                        auth, product_type="fuel", attendant_name=attendant_name,
                        pump_id=f["pump_id"], liters_sold=f["liters_sold"],
                    )
                    prod_type = "fuel"
                elif num_fuel == 0 and num_oil == 1:
                    o = cart["oil_items"][0]
                    gcash_data = create_gcash_dialog_checkout(
                        auth, product_type="oil", attendant_name=attendant_name,
                        oil_product_id=o["oil_id"], quantity=o["quantity"],
                    )
                    prod_type = "oil"
                else:
                    f_items = [{"pump_id": f["pump_id"], "liters_sold": f["liters_sold"]} for f in cart["fuel_items"]]
                    o_items = [{"oil_product_id": o["oil_id"], "quantity": o["quantity"]} for o in cart["oil_items"]]
                    gcash_data = create_gcash_dialog_checkout(
                        auth, product_type="multi", attendant_name=attendant_name,
                        fuel_items=f_items, oil_items=o_items,
                    )
                    prod_type = "multi"

                page.pop_dialog()
                gcash_qr_dialog(gcash_data, grand_total, prod_type=prod_type)
            except Exception as ex:
                error_msg = str(ex)
                print(f"Multi GCash error: {error_msg}")
                page.pop_dialog()
                show_snack(f"GCash failed: {error_msg}")

        page.run_thread(do_create)

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
                            ft.Button(
                                style=ft.ButtonStyle(bgcolor=GCASH_BLUE, color="white"),
                                expand=True, height=46, on_click=confirm_gcash_multi,
                                content=ft.Row(
                                    alignment=ft.MainAxisAlignment.CENTER, tight=True, spacing=8,
                                    controls=[
                                        ft.Image(src="gcash_logo.png", width=20, height=20, fit=ft.BoxFit.CONTAIN,
                                                 error_content=ft.Icon(ft.Icons.PAYMENT, size=16, color="white")),
                                        ft.Text("GCash", weight=ft.FontWeight.BOLD),
                                    ],
                                ),
                            ),
                        ]),
                    ],
                ),
            ),
        )
        page.show_dialog(sheet)

    def open_fuel_dialog(pump_name: str, price: float, stock: float):
        fuel_clean_name = pump_name.split()[0]
        pump_id = PUMP_MAP.get(pump_name, 1)
        lock = {"busy": False}
        liters_field = ft.TextField(label="Liters", keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)
        amount_field = ft.TextField(label="Amount (PHP)", keyboard_type=ft.KeyboardType.NUMBER)

        def on_liters(e):
            try:
                l = float(liters_field.value or 0)
                amount_field.value = f"{l * price:.2f}" if l > 0 else ""
                page.update()
            except: pass

        def on_amount(e):
            try:
                a = float(amount_field.value or 0)
                liters_field.value = f"{a / price:.3f}" if a > 0 and price else ""
                page.update()
            except: pass

        liters_field.on_change = on_liters
        amount_field.on_change = on_amount

        def add_fuel(e):
            try:
                l = float(liters_field.value or 0)
                a = float(amount_field.value or 0)
                if l > 0 and a > 0:
                    cart["fuel_items"].append({
                        "pump_id": pump_id,
                        "liters_sold": round(l, 3),
                        "fuel_name": fuel_clean_name,
                        "unit_price": price,
                        "total": round(a, 2)
                    })
                    refresh_cart_ui()
                    page.pop_dialog()
            except Exception as ex:
                print(f"[Multi Fuel Add Error] {ex}")

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Add {fuel_clean_name} (₱{price:.2f}/L)"),
            content=ft.Column([liters_field, amount_field], tight=True, spacing=10),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()),
                ft.FilledButton("Add to Order", style=ft.ButtonStyle(bgcolor=RED, color="white"), on_click=add_fuel)
            ]
        )
        page.show_dialog(dlg)

    def open_oil_modal(oil: dict):
        qty_field = ft.TextField(label="Quantity", value="", keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)

        def add_oil(e):
            try:
                q = int(float(qty_field.value or 0))
                if q > 0:
                    cart["oil_items"].append({
                        "oil_id": oil["id"],
                        "quantity": q,
                        "oil_name": f"{oil['brand']} {oil['name']}".strip(),
                        "price": oil["price"],
                        "total": round(q * oil["price"], 2)
                    })
                    refresh_cart_ui()
                    page.pop_dialog()
            except Exception as ex:
                print(f"[Multi Oil Add Error] {ex}")

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Add {oil['brand']} {oil['name']}"),
            content=ft.Column([
                ft.Text(f"Price: ₱{oil['price']:.2f} | Stock: {oil['stock']}"),
                qty_field
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()),
                ft.FilledButton("Add to Order", bgcolor=MOBILE_RED, color="white", on_click=add_oil),
            ],
        ))

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

    def oil_card_image(oil: dict, box_height: int):
        icon = ft.Icon(ft.Icons.WATER_DROP_OUTLINED, size=44, color="black")
        img_url = oil.get("image_url")
        content = ft.Image(
            src=img_url, height=box_height - 12, fit=ft.BoxFit.CONTAIN,
            error_content=icon,
        ) if img_url else icon
        return ft.Container(
            height=box_height, bgcolor="#F4F4F5", border_radius=12, padding=6,
            alignment=ft.Alignment.CENTER, content=content,
        )

    def oil_card(oil: dict):
        stock = oil["stock"]
        low = stock <= oil.get("low_stock_threshold", 5)

        card_bg = MOBILE_RED if low else "white"
        text_main = "white" if low else "#2B2D36"
        text_sub = "#FFD9DA" if low else "#5F6368"
        divider_color = "#C97A7A" if low else "#E5E7EB"

        def info_row(label, value):
            return ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=6,
                controls=[
                    ft.Text(label, size=11, weight=ft.FontWeight.W_500, color=text_sub),
                    ft.Text(value, size=11, weight=ft.FontWeight.W_600, color=text_main,
                            expand=True, text_align=ft.TextAlign.RIGHT,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ],
            )

        return ft.Container(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6,
                controls=[
                    oil_card_image(oil, 110),
                    ft.Text(f"Stock: {stock}", size=16, weight=ft.FontWeight.BOLD, color=text_main),
                    ft.Text(f"\u20b1{oil['price']:.2f}", size=13, weight=ft.FontWeight.W_600, color=text_main),
                    ft.Divider(height=1, color=divider_color),
                    info_row("Brand:", oil.get("brand", "")),
                    info_row("Item:", oil.get("name", "")),
                ],
            ),
            border=ft.Border.all(1, MOBILE_RED if low else "#E5E7EB"),
            border_radius=14, bgcolor=card_bg, expand=True, ink=True,
            padding=ft.Padding.all(10),
            shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.10, "black"), offset=ft.Offset(0, 3)),
            on_click=lambda e, o=oil: open_oil_dialog(o),
        )

    def two_col_grid(cards):
        rows = []
        for i in range(0, len(cards), 2):
            pair = [cards[i]]
            if i + 1 < len(cards):
                pair += [ft.Container(width=12), cards[i + 1]]
            else:
                pair += [ft.Container(width=12), ft.Container(expand=True)]
            rows.append(ft.Row(controls=pair, spacing=0))
        return ft.Column(controls=rows, spacing=12, scroll=ft.ScrollMode.ADAPTIVE, expand=True)

    def build_body():
        if "fuels_data" not in auth and "oils_data" not in auth:
            return loading_indicator()

        if state["tab"] == "fuel":
            pumps = [
                ("Regular 1", GREEN), ("Regular 2", GREEN),
                ("Premium 1", MOBILE_RED), ("Premium 2", MOBILE_RED),
                ("Diesel 1", YELLOW), ("Diesel 2", YELLOW),
            ]
        )

    def load_data():
        if "fuels_data" not in auth:
            try:
                auth["fuels_data"] = get_fuels(auth)
            except Exception as ex:
                print(f"[Multi Load Fuels Error] {ex}")
                auth["fuels_data"] = []

        if "oils_data" not in auth:
            try:
                auth["oils_data"] = get_oils(auth)
            except Exception as ex:
                print(f"[Multi Load Oils Error] {ex}")
                auth["oils_data"] = []

        render_inventory_items()
        page.update()

    cart_badge = ft.Container(
        content=badge_text, visible=False,
        bgcolor="white", border=ft.Border.all(1.5, MOBILE_RED), border_radius=10,
        width=22, height=22, alignment=ft.Alignment.CENTER,
        right=0, top=0,
    )
    cart_fab = ft.Stack(
        width=68, height=68,
        right=16, bottom=62,
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
        bgcolor=RED, height=100, padding=20,
        content=ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        sidebar.menu_button(),
                        ft.Column(controls=[ft.Text("Cashier", size=16, weight=ft.FontWeight.BOLD, color="white")], spacing=0),
                    ],
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(controls=[ft.Text("U-FUEL", size=16, weight=ft.FontWeight.BOLD, color="white"), ft.Container(content=ft.Image(src="u-fuel_logo.jpg", width=40, height=40, fit=ft.BoxFit.CONTAIN), bgcolor="white", border_radius=8, padding=4, width=40, height=40)], spacing=8),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.only(left=8, right=20, top=10, bottom=10),
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
        height=80,
        bgcolor=RED,
        padding=ft.Padding.symmetric(vertical=14, horizontal=24),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.END,
            controls=[
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.LOGOUT, color=TEXT_WHITE, size=16),
                            ft.Text("LOGOUT", color=TEXT_WHITE, size=13, weight=ft.FontWeight.BOLD)
                        ],
                        spacing=6
                    ),
                    bgcolor="#6B6B6B",
                    border_radius=6,
                    padding=ft.Padding.symmetric(vertical=8, horizontal=14),
                    ink=True,
                    on_click=go_logout
                )
            ]
        )
    )

    toggle_holder.content = build_toggle()
    body_holder.content = build_body()
    refresh_cart_ui()

    if "fuels_data" not in auth or "oils_data" not in auth:
        page.run_thread(load_data)

    return ft.SafeArea(
        content=sidebar.wrap(ft.Stack(
            expand=True,
            controls=[
                ft.Column(controls=[header, ft.Container(height=10), content_card, footer], expand=True, spacing=0),
                cart_fab,
            ],
        )),
        expand=True,
    )
