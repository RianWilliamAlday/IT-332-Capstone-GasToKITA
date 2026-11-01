import flet as ft
import time
import threading
import io
import base64
from pages.admin_dashboard import TEXT_WHITE
from pages.api_client import get_fuels, get_oils, PUMP_MAP, create_gcash_dialog_checkout, check_gcash_status, manual_confirm_gcash

RED = "#A61E22"
LIGHT_GRAY = "#E9E9E9"
WHITE = "white"

# Card background colors per fuel type
COLOR_REGULAR = "#0CA940"
COLOR_PREMIUM = "#E3242B"
COLOR_DIESEL = "#EBB328"
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

def create_oil_card(oil: dict, on_click):
    brand = oil.get("brand", "")
    name = oil.get("name", "")
    stock = oil.get("stock", 0)
    price = oil.get("price", 0.0)
    low = stock <= oil.get("low_stock_threshold", 5)

    return ft.Container(
        width=280, 
        height=220,
        bgcolor=RED, 
        border_radius=20, 
        padding=12,
        on_click=lambda e: on_click(oil), 
        ink=True,
        content=ft.Column(
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            controls=[
                ft.Container(
                    expand=True, 
                    bgcolor=WHITE, 
                    border_radius=15,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER, 
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
                        spacing=4, 
                        controls=[
                            ft.Icon(ft.Icons.WATER_DROP_OUTLINED, size=45, color="black"),
                            ft.Text(f"Stock: {stock}", size=12, weight=ft.FontWeight.BOLD, color=RED if low else "black"),
                            ft.Text(f"₱{price:.2f}", size=12, color="grey"),
                        ]
                    )
                ),
                ft.Column(
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(brand, size=11, weight=ft.FontWeight.BOLD, color=WHITE),
                        ft.Text(name, size=13, weight=ft.FontWeight.BOLD, color=WHITE, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ]
                )
            ]
        ),
    )

def build_multi_page(page: ft.Page, auth: dict):
    page.title = "Multi Sale"
    page.bgcolor = LIGHT_GRAY
    page.padding = 0

    if "cart" not in auth:
        auth["cart"] = {"fuel_items": [], "oil_items": []}
    cart = auth["cart"]

    cart_items_column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
    total_text = ft.Text("₱0.00", size=24, weight=ft.FontWeight.BOLD, color=RED)
    
    fuel_layout_column = ft.Column(spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    oil_layout_column = ft.Column(spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    
    left_content_area = ft.Container(
        expand=True, 
        padding=20,
        alignment=ft.Alignment(0, -1),
        content=ft.ProgressRing(width=40, color=RED)
    )

    def show_snack(msg, color=RED):
        page.snack_bar = ft.SnackBar(content=ft.Text(msg), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def go_back(e):
        auth["cart"] = {"fuel_items": [], "oil_items": []}
        from pages.select import select_transaction
        page.controls.clear()
        page.add(select_transaction(page, auth))
        page.update()

    async def go_logout(e):
        await page.shared_preferences.remove("gastokita.auth_token")
        await page.shared_preferences.remove("gastokita.user_json")
        auth.clear()
        auth.update({"token": None, "role": None, "user": None})
        page.controls.clear()
        from app import main as app_main
        await app_main(page)
        page.update()
    
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

    refresh_cart_ui()

    def open_fuel_modal(fuel_pump_name: str, price: float, pump_id: int):
        fuel_clean_name = fuel_pump_name.split()[0]
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
                ft.FilledButton("Add to Order", style=ft.ButtonStyle(bgcolor=RED, color="white"), on_click=add_oil)
            ]
        )
        page.show_dialog(dlg)

    def render_inventory_items():
        fuels_data = auth.get("fuels_data", [])
        fuel_lookup = {f["name"]: f for f in fuels_data}
        oils_data = auth.get("oils_data", [])

        row1_names = ["Regular 1", "Premium 1", "Diesel 1"]
        row2_names = ["Regular 2", "Premium 2", "Diesel 2"]

        row1_cards = []
        for p_name in row1_names:
            base = p_name.split()[0]
            f = fuel_lookup.get(base)
            price = f["price"] if f else FALLBACK_PRICES.get(base, 60.0)
            pct = f.get("display_percentage", 78) if f else (78 if "Regular" in p_name else 63 if "Premium" in p_name else 83)
            row1_cards.append(create_fuel_card(p_name, price, pct, open_fuel_modal))

        row2_cards = []
        for p_name in row2_names:
            base = p_name.split()[0]
            f = fuel_lookup.get(base)
            price = f["price"] if f else FALLBACK_PRICES.get(base, 60.0)
            pct = f.get("display_percentage", 78) if f else (78 if "Regular" in p_name else 63 if "Premium" in p_name else 83)
            row2_cards.append(create_fuel_card(p_name, price, pct, open_fuel_modal))

        fuel_layout_column.controls = [
            ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=15, controls=row1_cards),
            ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=15, controls=row2_cards)
        ]

        # Filter out oil products where stock is 0 or less
        available_oils = [
            oil for oil in oils_data 
            if oil.get("stock", 0) > 0
        ]

        oil_cards = [create_oil_card(oil, open_oil_modal) for oil in available_oils]
        oil_rows = [
            ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=15, controls=oil_cards[i:i+3])
            for i in range(0, len(oil_cards), 3)
        ]
        oil_layout_column.controls = oil_rows

        left_content_area.alignment = ft.Alignment(0, -1)
        left_content_area.content = ft.Column(
            scroll=ft.ScrollMode.AUTO, 
            expand=True, 
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("Pumps / Fuel Types", size=20, weight=ft.FontWeight.BOLD),
                fuel_layout_column,
                ft.Divider(height=2, color="#CCCCCC"),
                ft.Text("Engine Oils & Lubricants", size=20, weight=ft.FontWeight.BOLD),
                oil_layout_column,
            ]
        )

    def load_multi_data():
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

    page.run_thread(load_multi_data)

    def proceed_checkout(e):
        num_fuel = len(cart["fuel_items"])
        num_oil = len(cart["oil_items"])

        if num_fuel == 0 and num_oil == 0:
            show_snack("Cart is empty", color=RED)
            return

        auth["cart"] = cart

        # Single Fuel Sale detection
        if num_fuel == 1 and num_oil == 0:
            f_item = cart["fuel_items"][0]
            unit_p = f_item.get("unit_price") or (f_item["total"] / f_item["liters_sold"] if f_item["liters_sold"] else 0)
            tx = {
                "label": f_item["fuel_name"],
                "details": f"{f_item['liters_sold']:.3f}L x ₱{unit_p:.2f}",
                "total": f_item["total"],
                "liters": f_item["liters_sold"],
                "pump_id": f_item["pump_id"],
                "fuel_name": f_item["fuel_name"],
                "type": "fuel",
                "payment_method": "cash"
            }

        # Single Oil Sale detection
        elif num_fuel == 0 and num_oil == 1:
            o_item = cart["oil_items"][0]
            tx = {
                "label": o_item["oil_name"],
                "details": f"{o_item['quantity']} x ₱{o_item['price']:.2f}",
                "total": o_item["total"],
                "quantity": o_item["quantity"],
                "oil_id": o_item["oil_id"],
                "type": "oil",
                "payment_method": "cash"
            }

        # True Multi Sale
        else:
            grand_total = sum(i["total"] for i in cart["fuel_items"]) + sum(i["total"] for i in cart["oil_items"])
            tx = {
                "label": f"({num_fuel + num_oil} items)",
                "details": "Multi-item Checkout",
                "total": grand_total,
                "type": "multi",
                "payment_method": "cash"
            }

        from pages.pos import build_pos_page
        page.controls.clear()
        page.add(build_pos_page(page, auth, tx))
        page.update()

    def gcash_qr_dialog(gcash_data: dict, grand_total: float, prod_type: str = "multi"):
        total_amt = float(gcash_data.get("total_amount", grand_total))
        sale_id_captured = (
            gcash_data.get("transaction_ref") or 
            gcash_data.get("sale_id") or 
            gcash_data.get("oil_sale_id")
        )
        checkout_id_captured = gcash_data.get("checkout_id")
        checkout_url = gcash_data.get("checkout_url", "")

        qr_data_uri = generate_qr_base64(checkout_url)
        status_text = ft.Text("Waiting for GCash payment...", color="#007CFF", size=12, weight=ft.FontWeight.BOLD)
        polling = {"active": True}

        if qr_data_uri:
            qr_image = ft.Image(src=qr_data_uri, width=220, height=220, fit=ft.BoxFit.CONTAIN)
        else:
            qr_image = ft.Text("QR failed, use link below", size=10)

        checkout_link = ft.TextButton(
            content="Open GCash Checkout",
            url=checkout_url,
            style=ft.ButtonStyle(color="#007CFF")
        )

        def close_all(e=None):
            polling["active"] = False
            page.pop_dialog()

        def manual_confirm(e=None):
            try:
                result = manual_confirm_gcash(auth, sale_id_captured, product_type=prod_type)
                status_text.value = f"Manually confirmed: {result.get('receipt_no','PAID')}"
                page.update()
                time.sleep(1)
                polling["active"] = False
                page.pop_dialog()

                from pages.change import build_change_page
                
                if prod_type == "fuel":
                    f_item = cart["fuel_items"][0]
                    unit_p = f_item.get("unit_price") or (f_item["total"] / f_item["liters_sold"] if f_item["liters_sold"] else 0)
                    tx = {
                        "label": f_item["fuel_name"],
                        "details": f"{f_item['liters_sold']:.3f}L x ₱{unit_p:.2f}",
                        "total": total_amt,
                        "liters": f_item["liters_sold"],
                        "pump_id": f_item["pump_id"],
                        "fuel_name": f_item["fuel_name"],
                        "type": "fuel",
                        "payment_method": "gcash",
                        "sale_id": sale_id_captured,
                        "is_paid": True
                    }
                elif prod_type == "oil":
                    o_item = cart["oil_items"][0]
                    tx = {
                        "label": o_item["oil_name"],
                        "details": f"{o_item['quantity']} x ₱{o_item['price']:.2f}",
                        "total": total_amt,
                        "quantity": o_item["quantity"],
                        "oil_id": o_item["oil_id"],
                        "type": "oil",
                        "payment_method": "gcash",
                        "sale_id": sale_id_captured,
                        "is_paid": True
                    }
                else:
                    tx = {
                        "label": f"({len(cart['fuel_items']) + len(cart['oil_items'])} items)",
                        "details": f"GCash PAID - ₱{total_amt:.2f}",
                        "total": total_amt,
                        "type": "multi",
                        "payment_method": "gcash",
                        "sale_id": sale_id_captured,
                        "is_paid": True
                    }

                auth["cart"] = {"fuel_items": [], "oil_items": []}
                page.controls.clear()
                page.add(build_change_page(page, auth, tx, paid=total_amt, change=0, sale=result, tx_type=prod_type))
                page.update()
            except Exception as ex:
                status_text.value = f"Confirm failed: {ex}"
                page.update()

        def auto_poll():
            while polling["active"]:
                time.sleep(3)
                try:
                    status = check_gcash_status(auth, checkout_id_captured)
                    if status.get("is_paid"):
                        def on_paid():
                            status_text.value = "Paid! Redirecting..."
                            page.update()
                            polling["active"] = False
                            page.pop_dialog()

                            result = manual_confirm_gcash(auth, sale_id_captured, product_type=prod_type)

                            from pages.change import build_change_page
                            if prod_type == "fuel":
                                f_item = cart["fuel_items"][0]
                                unit_p = f_item.get("unit_price") or (f_item["total"] / f_item["liters_sold"] if f_item["liters_sold"] else 0)
                                tx = {
                                    "label": f_item["fuel_name"],
                                    "details": f"{f_item['liters_sold']:.3f}L x ₱{unit_p:.2f}",
                                    "total": total_amt,
                                    "liters": f_item["liters_sold"],
                                    "pump_id": f_item["pump_id"],
                                    "fuel_name": f_item["fuel_name"],
                                    "type": "fuel",
                                    "payment_method": "gcash",
                                    "sale_id": status.get("sale_id") or sale_id_captured,
                                    "is_paid": True
                                }
                            elif prod_type == "oil":
                                o_item = cart["oil_items"][0]
                                tx = {
                                    "label": o_item["oil_name"],
                                    "details": f"{o_item['quantity']} x ₱{o_item['price']:.2f}",
                                    "total": total_amt,
                                    "quantity": o_item["quantity"],
                                    "oil_id": o_item["oil_id"],
                                    "type": "oil",
                                    "payment_method": "gcash",
                                    "sale_id": status.get("sale_id") or sale_id_captured,
                                    "is_paid": True
                                }
                            else:
                                tx = {
                                    "label": f"({len(cart['fuel_items']) + len(cart['oil_items'])} items)",
                                    "details": f"GCash PAID - ₱{total_amt:.2f}",
                                    "total": total_amt,
                                    "type": "multi",
                                    "payment_method": "gcash",
                                    "sale_id": status.get("sale_id") or sale_id_captured,
                                    "is_paid": True
                                }

                            auth["cart"] = {"fuel_items": [], "oil_items": []}
                            page.controls.clear()
                            page.add(build_change_page(page, auth, tx, paid=total_amt, change=0, sale=result, tx_type=prod_type))
                            page.update()
                        page.run_thread(on_paid)
                        break
                except Exception as ex:
                    print(f"[GCash Multi Poll] {ex}")

        qr_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"GCash - ₱{total_amt:.2f}", weight=ft.FontWeight.BOLD),
            content=ft.Column(tight=True, spacing=12, width=280, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Text("Fuel / Oil Sale" if prod_type != "multi" else "Multi-Item Sale", size=12, color="grey"),
                ft.Container(alignment=ft.Alignment.CENTER, content=qr_image),
                checkout_link,
                status_text
            ]),
            actions=[
                ft.TextButton("Cancel", on_click=close_all),
                ft.TextButton("Manual Confirm", on_click=manual_confirm),
            ],
        )
        page.show_dialog(qr_dialog)
        threading.Thread(target=auto_poll, daemon=True).start()

    def confirm_gcash_multi(e=None):
        num_fuel = len(cart["fuel_items"])
        num_oil = len(cart["oil_items"])

        if num_fuel == 0 and num_oil == 0:
            show_snack("Cart is empty", color=RED)
            return

        grand_total = sum(i["total"] for i in cart["fuel_items"]) + sum(i["total"] for i in cart["oil_items"])
        if grand_total < 100:
            show_snack(f"GCash minimum total is ₱100.00 (Current: ₱{grand_total:.2f})", color=RED)
            return

        attendant_name = auth.get("selected_attendant") or auth.get("user", {}).get("name") or "Attendant 1"

        loading_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Creating GCash Checkout..."),
            content=ft.Column(tight=True, controls=[ft.ProgressRing(), ft.Text("Contacting PayMongo...")])
        )
        page.show_dialog(loading_dialog)

        def do_create():
            try:
                # Single Fuel Sale
                if num_fuel == 1 and num_oil == 0:
                    f_item = cart["fuel_items"][0]
                    gcash_data = create_gcash_dialog_checkout(
                        auth,
                        product_type="fuel",
                        attendant_name=attendant_name,
                        pump_id=f_item["pump_id"],
                        liters_sold=f_item["liters_sold"],
                    )
                    prod_type = "fuel"

                # Single Oil Sale
                elif num_fuel == 0 and num_oil == 1:
                    o_item = cart["oil_items"][0]
                    gcash_data = create_gcash_dialog_checkout(
                        auth,
                        product_type="oil",
                        attendant_name=attendant_name,
                        oil_product_id=o_item["oil_id"],
                        quantity=o_item["quantity"],
                    )
                    prod_type = "oil"

                # True Multi Sale
                else:
                    f_items = [{"pump_id": f["pump_id"], "liters_sold": f["liters_sold"]} for f in cart["fuel_items"]]
                    o_items = [{"oil_product_id": o["oil_id"], "quantity": o["quantity"]} for o in cart["oil_items"]]

                    gcash_data = create_gcash_dialog_checkout(
                        auth,
                        product_type="multi",
                        attendant_name=attendant_name,
                        fuel_items=f_items,
                        oil_items=o_items,
                    )
                    prod_type = "multi"

                def show_qr():
                    page.pop_dialog()
                    gcash_qr_dialog(gcash_data, grand_total, prod_type=prod_type)
                page.run_thread(show_qr)
            except Exception as ex:
                error_msg = str(ex)
                print(f"Multi GCash error: {error_msg}")
                def show_error():
                    page.pop_dialog()
                    show_snack(f"GCash failed: {error_msg}", color=RED)
                page.run_thread(show_error)

        threading.Thread(target=do_create, daemon=True).start()

    right_summary = ft.Container(
        width=340, bgcolor="white", padding=20, border_radius=15, margin=10,
        content=ft.Column(
            expand=True, spacing=15,
            controls=[
                ft.Text("Cart", size=20, weight=ft.FontWeight.BOLD),
                cart_items_column,
                ft.Divider(),
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Text("Total:", size=16, weight=ft.FontWeight.BOLD),
                    total_text
                ]),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    spacing=10,
                    controls=[
                        ft.FilledButton(
                            "Cash Checkout",
                            style=ft.ButtonStyle(bgcolor=RED, color="white"),
                            expand=True, height=45,
                            on_click=proceed_checkout
                        ),
                        ft.Button(
                            style=ft.ButtonStyle(bgcolor="#007CFF", color="white"),
                            expand=True, height=45,
                            on_click=confirm_gcash_multi,
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER, tight=True,
                                controls=[
                                    ft.Image(src="assets/gcash_logo.png", width=20, height=20, fit=ft.BoxFit.CONTAIN, error_content=ft.Icon(ft.Icons.PAYMENT, size=16, color="white")),
                                    ft.Text("GCash", weight=ft.FontWeight.BOLD),
                                ],
                            ),
                        ),
                    ]
                )
            ]
        )
    )

    header = ft.Container(
        bgcolor=RED, height=100, padding=20,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(spacing=10, controls=[
                    ft.TextButton("← Back", style=ft.ButtonStyle(color="white"), on_click=go_back),
                    ft.Text("Multi Sale", size=28, weight=ft.FontWeight.BOLD, color="white"),
                ]),
                ft.Row(spacing=15, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text("U-Fuel", size=28, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Container(width=70, height=70, bgcolor="white", border_radius=12,
                        content=ft.Image(src="u-fuel_logo.jpg", fit=ft.BoxFit.CONTAIN)),
                ]),
            ],
        ),
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

    body = ft.Row(expand=True, controls=[left_content_area, right_summary], spacing=0)

    return ft.Column(spacing=0, expand=True, controls=[header, body, footer])