import flet as ft
import time
import threading
import io
import base64
from pages.api_client import get_oils, create_gcash_dialog_checkout, check_gcash_status, manual_confirm_gcash
from pages.history import TEXT_WHITE

RED = "#A61E22"
LIGHT_GRAY = "#E9E9E9"
WHITE = "white"

def oil_card(oil: dict, on_click):
    brand = oil.get("brand","")
    name = oil.get("name","")
    stock = oil.get("stock", 0)
    price = oil.get("price", 0)
    low = stock <= oil.get("low_stock_threshold", 5)

    return ft.Container(
        width=185, 
        height=240,
        bgcolor=RED, 
        border_radius=25, 
        padding=15,
        on_click=lambda e: on_click(oil), 
        ink=True,
        content=ft.Column(
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            controls=[
                ft.Container(
                    expand=True, 
                    bgcolor=WHITE, 
                    border_radius=18,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER, 
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
                        spacing=4, 
                        controls=[
                            ft.Icon(ft.Icons.WATER_DROP_OUTLINED, size=50, color="black"),
                            ft.Text(f"Stock: {stock}", size=12, weight=ft.FontWeight.BOLD, color=RED if low else "black"),
                            ft.Text(f"₱{price:.2f}", size=12, color="grey"),
                        ]
                    )
                ),
                ft.Column(
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(brand, size=12, weight=ft.FontWeight.BOLD, color=WHITE),
                        ft.Text(name, size=14, weight=ft.FontWeight.BOLD, color=WHITE, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ]
                )
            ]
        ),
    )


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

def build_oil_page(page: ft.Page, auth: dict):
    page.title = "Oil Selection"
    page.bgcolor = LIGHT_GRAY
    page.padding = 0

    oils_state = {"error": None}

    async def go_logout(e):
            await page.shared_preferences.remove("gastokita.auth_token")
            await page.shared_preferences.remove("gastokita.user_json")
        
            auth.clear()
            auth.update({"token": None, "role": None, "user": None})
        
            page.controls.clear()
            from app import main as app_main
            await app_main(page)
            page.update()

    def go_back(e):
        from pages.select import select_transaction
        page.controls.clear()
        page.add(select_transaction(page, auth))
        page.update()

    def open_oil_dialog(oil: dict):
        oil_id = oil["id"]
        oil_name = f"{oil['brand']} {oil['name']}"
        unit_price = oil["price"]
        stock = oil["stock"]

        qty_field = ft.TextField(label="Quantity (bottles)", keyboard_type=ft.KeyboardType.NUMBER, width=260, autofocus=True)
        total_field = ft.TextField(label="Total Amount (PHP)", width=260, read_only=True, value="₱0.00")
        error_text = ft.Text("", color=RED, size=12)

        def on_qty_change(e):
            try:
                qty = float(qty_field.value or 0)
                if qty > stock:
                    error_text.value = f"Only {stock} in stock"
                else:
                    error_text.value = ""
                total = qty * unit_price
                total_field.value = f"₱{total:.2f}" if qty > 0 else "₱0.00"
                page.update()
            except:
                total_field.value = "₱0.00"
                page.update()

        qty_field.on_change = on_qty_change

        def close_dlg(e=None):
            page.pop_dialog()

        def confirm_dlg(e=None):
            try:
                qty = int(float(qty_field.value or 0))
                if qty <= 0:
                    error_text.value = "Enter valid quantity"
                    page.update()
                    return
                if qty > stock:
                    error_text.value = f"Insufficient stock"
                    page.update()
                    return
                total = qty * unit_price
                page.pop_dialog()
                from pages.pos import build_pos_page
                tx = {
                    "label": oil_name,
                    "details": f"{qty} x ₱{unit_price:.2f}",
                    "total": total,
                    "quantity": qty,
                    "oil_id": oil_id,
                    "type": "oil"
                }
                page.controls.clear()
                page.add(build_pos_page(page, auth, tx))
                page.update()
            except Exception as ex:
                error_text.value = f"Invalid: {ex}"
                page.update()

        def gcash_qr_dialog(gcash_data: dict):
            total_amt = float(gcash_data.get("total_amount", 0))
            sale_id_captured = gcash_data.get("sale_id")
            checkout_id_captured = gcash_data.get("checkout_id")
            checkout_url = gcash_data.get("checkout_url", "")
            qty_captured = int(float(qty_field.value or 0))

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
                    result = manual_confirm_gcash(auth, sale_id_captured, product_type="oil")
                    status_text.value = f"Manually confirmed: {result.get('receipt_no','PAID')}"
                    page.update()
                    time.sleep(1)
                    polling["active"] = False
                    page.pop_dialog()

                    from pages.change import build_change_page
                    tx = {
                        "label": oil_name,
                        "details": f"GCash PAID - ₱{total_amt:.2f}",
                        "total": total_amt,
                        "quantity": qty_captured,
                        "oil_id": oil_id,
                        "type": "oil",
                        "payment_method": "gcash",
                        "sale_id": sale_id_captured,
                        "is_paid": True
                    }
                    page.controls.clear()
                    page.add(build_change_page(page, auth, tx, paid=total_amt, change=0, sale=result, tx_type="oil"))
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
                                from pages.change import build_change_page
                                tx = {
                                    "label": oil_name,
                                    "details": f"GCash PAID - ₱{total_amt:.2f}",
                                    "total": total_amt,
                                    "quantity": qty_captured,
                                    "oil_id": oil_id,
                                    "type": "oil",
                                    "payment_method": "gcash",
                                    "sale_id": status.get("sale_id") or sale_id_captured,
                                    "is_paid": True
                                }
                                page.controls.clear()
                                page.add(build_change_page(page, auth, tx, paid=total_amt, change=0, sale={"sale_id": tx["sale_id"]}, tx_type="oil"))
                                page.update()
                            page.run_thread(on_paid)
                            break
                    except Exception as ex:
                        print(f"[GCash Poll] {ex}")

            qr_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text(f"GCash - ₱{total_amt:.2f}", weight=ft.FontWeight.BOLD),
                content=ft.Column(tight=True, spacing=12, scroll=ft.ScrollMode.AUTO, controls=[
                    ft.Text(oil_name, size=12, color="grey"),
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

        def confirm_gcash_dlg(e=None):
            try:
                qty = int(float(qty_field.value or 0))
                if qty <= 0:
                    error_text.value = "Enter valid quantity"
                    page.update()
                    return
                if qty > stock:
                    error_text.value = "Insufficient stock"
                    page.update()
                    return

                attendant_name = auth.get("selected_attendant") or auth.get("user", {}).get("name") or "Attendant 1"

                page.pop_dialog()
                loading_dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Creating GCash Checkout..."),
                    content=ft.Column(tight=True, controls=[ft.ProgressRing(), ft.Text("Contacting PayMongo...")])
                )
                page.show_dialog(loading_dialog)

                def do_create():
                    try:
                        gcash_data = create_gcash_dialog_checkout(
                            auth,
                            product_type="oil",
                            attendant_name=attendant_name,
                            oil_product_id=oil_id,
                            quantity=qty,
                        )
                        def show_qr():
                            page.pop_dialog()
                            gcash_qr_dialog(gcash_data)
                        page.run_thread(show_qr)
                    except Exception as ex:
                        error_msg = str(ex)
                        print(f"GCash error: {error_msg}")
                        def show_error():
                            page.pop_dialog()
                            page.snack_bar = ft.SnackBar(content=ft.Text(f"GCash failed: {error_msg}"), bgcolor=RED)
                            page.snack_bar.open = True
                            open_oil_dialog(oil)
                            page.update()
                        page.run_thread(show_error)

                threading.Thread(target=do_create, daemon=True).start()

            except Exception as ex:
                error_text.value = f"Invalid: {ex}"
                page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(oil_name, weight=ft.FontWeight.BOLD),
            content=ft.Column(tight=True, spacing=14, controls=[
                ft.Container(
                    bgcolor="#F5F5F5", border_radius=8, padding=10,
                    content=ft.Column(spacing=4, controls=[
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                            ft.Text("Unit Price:", weight=ft.FontWeight.BOLD),
                            ft.Text(f"₱{unit_price:.2f}", weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                            ft.Text("Stock:"),
                            ft.Text(f"{stock} pcs", color=RED if stock <= oil.get("low_stock_threshold",5) else "green"),
                        ]),
                    ])
                ),
                qty_field,
                total_field,
                error_text,
            ]),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.FilledButton("Confirm", style=ft.ButtonStyle(bgcolor=RED, color="white"), on_click=confirm_dlg),
                ft.Button(
                    style=ft.ButtonStyle(bgcolor="#007CFF", color="white"),
                    on_click=confirm_gcash_dlg,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER, tight=True,
                        controls=[
                            ft.Image(src="assets/gcash_logo.png", width=20, height=20, fit=ft.BoxFit.CONTAIN, error_content=ft.Icon(ft.Icons.PAYMENT, size=16, color="white")),
                            ft.Text("GCash"),
                        ],
                    ),
                ),
            ],
        )
        page.show_dialog(dialog)

    banner = ft.Container()
    oil_grid = ft.ResponsiveRow(alignment=ft.MainAxisAlignment.CENTER, spacing=30, run_spacing=30)
    
    def build_oil_layout():
        if oils_state["error"]:
            banner.bgcolor = "#FFF3CD"
            banner.padding = 8
            banner.content = ft.Text(f"API offline, using cached fallbacks. {oils_state['error']}", size=11)
        else:
            banner.content = None
            banner.padding = 0

        oil_grid.controls = [
            ft.Container(content=oil_card(oil, open_oil_dialog), col={"sm": 12, "md": 4, "lg": 4})
            for oil in auth.get("oils_data", [])
        ]
        return ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True, controls=[banner, oil_grid])

    if "oils_data" in auth:
        main_content = ft.Container(expand=True, bgcolor=WHITE, alignment=ft.Alignment(0, -0.1), padding=40, content=build_oil_layout())
    else:
        main_content = ft.Container(expand=True, bgcolor=WHITE, alignment=ft.Alignment(0, 0), content=ft.ProgressRing(width=40, color=RED))

    def load_oils(e=None):
        if "oils_data" not in auth:
            time.sleep(0.1)
        try:
            try:
                oils = get_oils(auth)
                auth["oils_data"] = oils
            except Exception as ex:
                oils_state["error"] = str(ex)
                if "oils_data" not in auth:
                    auth["oils_data"] = [
                        {"id": i, "brand": f"Brand {i}", "name": f"OIL {i}", "stock": 20, "price": 250.0 + i*20, "low_stock_threshold": 5}
                        for i in range(1,7)
                    ]
                print(f"[API] get_oils failed: {ex}")

            main_content.alignment = ft.Alignment(0, -0.2)
            main_content.padding = 40
            main_content.content = build_oil_layout()
            
        except Exception as thread_error:
            print(f"[Thread Error] Crash while rendering UI: {thread_error}")
        finally:
            page.update()

    page.run_thread(load_oils)

    header = ft.Container(
        bgcolor=RED, height=100, padding=20,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(spacing=10, controls=[
                    ft.TextButton("← Back", style=ft.ButtonStyle(color="white"), on_click=go_back),
                    ft.Text("Oils", size=28, weight=ft.FontWeight.BOLD, color="white"),
                ]),
                ft.Row(spacing=15, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text("U-Fuel", size=28, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Container(width=70, height=70, bgcolor="white", border_radius=12,
                        content=ft.Image(src="u-fuel_logo.jpg", fit=ft.BoxFit.CONTAIN)),
                ]),
            ],
        ),
    )
    footer = ft.Container(height=80,bgcolor=RED, padding=ft.Padding.symmetric(vertical=14, horizontal=24),content=ft.Row([
                        ft.Container(content=ft.Row([ft.Icon(ft.Icons.LOGOUT, color=TEXT_WHITE, size=16), ft.Text("LOGOUT", color=TEXT_WHITE, size=13, weight=ft.FontWeight.BOLD)], spacing=6), bgcolor="#6B6B6B", border_radius=6, padding=ft.Padding.symmetric(vertical=8, horizontal=14), ink=True, on_click=go_logout)
                        ]
                    )
                )

    return ft.Column(spacing=0, expand=True, controls=[header, main_content, footer])