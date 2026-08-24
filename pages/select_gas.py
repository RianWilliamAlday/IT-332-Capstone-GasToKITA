import flet as ft
import time
import threading
import io
import base64
from pages.api_client import get_fuels, PUMP_MAP, create_gcash_dialog_checkout, check_gcash_status, manual_confirm_gcash
from pages.history import TEXT_WHITE

RED = "#A61E22"
LIGHT_GRAY = "#E9E9E9"
COLOR_REGULAR = "#0CA940"
COLOR_PREMIUM = "#E3242B"
COLOR_DIESEL = "#F5C243"
BAR_GREEN = "#12B347"
BAR_YELLOW = "#F4B400"
BAR_RED = "#E3242B"

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

def build_pump_page(page: ft.Page, auth: dict):
    page.title = "Fuel Selection"
    page.bgcolor = LIGHT_GRAY
    page.padding = 0

    fuels_state = {"loading": "fuels_data" not in auth, "error": None}
    fuel_lookup = {}

    if "fuels_data" in auth:
        for f in auth["fuels_data"]:
            fuel_lookup[f["name"]] = f

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

    def get_fuel_for_pump(pump_name: str):
        base = pump_name.split()[0]
        return fuel_lookup.get(base)

    def show_snack(message, bgcolor=None):
        page.snack_bar = ft.SnackBar(content=ft.Text(message), bgcolor=bgcolor)
        page.snack_bar.open = True
        page.update()

    def create_fuel_card(title, card_color, bar_color):
        fuel = get_fuel_for_pump(title)
        if fuel:
            percentage = fuel.get("display_percentage", 100)
            price = fuel["price"]
        else:
            percentage = 100 if "Regular" in title else 50 if "Premium" in title else 20
            price = FALLBACK_PRICES.get(title.split()[0], 60)

        if percentage > 60:
            bar = BAR_GREEN
        elif percentage > 25:
            bar = BAR_YELLOW
        else:
            bar = BAR_RED

        return ft.Container(
            width=260, height=150, bgcolor=card_color, border_radius=15,
            border=ft.Border.all(1, "black"), padding=20, ink=True,
            on_click=lambda e, t=title: open_fuel_dialog(t),
            content=ft.Column(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Text(title, size=18, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Text(f"₱{price:.2f}", size=12, color="white"),
                ]),
                ft.Column(spacing=5, controls=[
                    ft.Text(f"{percentage:.0f}%", size=22, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Stack(controls=[
                        ft.Container(height=16, width=220, bgcolor="white", border_radius=10),
                        ft.Container(height=16, width=220 * (percentage / 100), bgcolor=bar, border_radius=10)
                    ])
                ])
            ])
        )

    def open_fuel_dialog(fuel_pump_name: str):
        fuel = get_fuel_for_pump(fuel_pump_name)
        if fuel:
            price = fuel["price"]
            stock = fuel["actual_liters"]
            tank_capacity = fuel["tank_capacity"]
        else:
            base = fuel_pump_name.split()[0]
            price = FALLBACK_PRICES.get(base, 60.0)
            stock = 9999
            tank_capacity = 8092

        lock = {"busy": False}
        liters_field = ft.TextField(label="Liters", keyboard_type=ft.KeyboardType.NUMBER, width=300, autofocus=True)
        amount_field = ft.TextField(label="Amount (PHP)", keyboard_type=ft.KeyboardType.NUMBER, width=300)
        error_text = ft.Text("", color=RED, size=12)

        def on_liters(e):
            if lock["busy"]: return
            try:
                l = float(liters_field.value or 0)
                lock["busy"] = True
                amount_field.value = f"{l * price:.2f}" if l > 0 else ""
                error_text.value = f"Only {stock:.1f}L left in tank" if l > stock else ""
                page.update()
            except:
                pass
            finally:
                lock["busy"] = False

        def on_amount(e):
            if lock["busy"]: return
            try:
                a = float(amount_field.value or 0)
                lock["busy"] = True
                liters = a / price if price else 0
                liters_field.value = f"{liters:.3f}" if a > 0 else ""
                error_text.value = f"Only {stock:.1f}L left" if liters > stock else ""
                page.update()
            except:
                pass
            finally:
                lock["busy"] = False

        liters_field.on_change = on_liters
        amount_field.on_change = on_amount

        def close_dlg(e=None):
            page.pop_dialog()

        def confirm_cash_dlg(e=None):
            try:
                l = float(liters_field.value or 0)
                a = float(amount_field.value or 0)
                if l <= 0 and a <= 0:
                    error_text.value = "Enter liters or amount"
                    page.update()
                    return
                if l <= 0: l = a / price
                if a <= 0: a = l * price
                if l > stock:
                    error_text.value = f"Insufficient stock ({stock:.1f}L)"
                    page.update()
                    return

                page.pop_dialog()
                from pages.pos import build_pos_page
                tx = {
                    "label": fuel_pump_name,
                    "details": f"{l:.3f}L x ₱{price:.2f}",
                    "total": a,
                    "liters": l,
                    "pump_id": PUMP_MAP.get(fuel_pump_name, 1),
                    "fuel_name": fuel_pump_name.split()[0],
                    "type": "fuel",
                    "payment_method": "cash"
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
            liters_captured = float(liters_field.value or 0)

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
                    result = manual_confirm_gcash(auth, sale_id_captured, product_type="fuel")
                    status_text.value = f"Manually confirmed: {result.get('receipt_no','PAID')}"
                    page.update()
                    time.sleep(1)
                    polling["active"] = False
                    page.pop_dialog()

                    from pages.change import build_change_page
                    tx = {
                        "label": fuel_pump_name,
                        "details": f"GCash PAID - ₱{total_amt:.2f}",
                        "total": total_amt,
                        "liters": liters_captured,
                        "pump_id": PUMP_MAP.get(fuel_pump_name, 1),
                        "fuel_name": fuel_pump_name.split()[0],
                        "type": "fuel",
                        "payment_method": "gcash",
                        "sale_id": sale_id_captured,
                        "is_paid": True
                    }
                    page.controls.clear()
                    page.add(build_change_page(page, auth, tx, paid=total_amt, change=0, sale=result, tx_type="fuel"))
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
                                    "label": fuel_pump_name,
                                    "details": f"GCash PAID - ₱{total_amt:.2f}",
                                    "total": total_amt,
                                    "liters": liters_captured,
                                    "pump_id": PUMP_MAP.get(fuel_pump_name, 1),
                                    "fuel_name": fuel_pump_name.split()[0],
                                    "type": "fuel",
                                    "payment_method": "gcash",
                                    "sale_id": status.get("sale_id") or sale_id_captured,
                                    "is_paid": True
                                }
                                page.controls.clear()
                                page.add(build_change_page(page, auth, tx, paid=total_amt, change=0, sale={"sale_id": tx["sale_id"]}, tx_type="fuel"))
                                page.update()
                            page.run_thread(on_paid)
                            break
                    except Exception as ex:
                        print(f"[GCash Poll] {ex}")

            qr_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text(f"GCash - ₱{total_amt:.2f}", weight=ft.FontWeight.BOLD),
                content=ft.Column(tight=True, spacing=12, scroll=ft.ScrollMode.AUTO, controls=[
                    ft.Text(f"{fuel_pump_name}", size=12, color="grey"),
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
                l = float(liters_field.value or 0)
                a = float(amount_field.value or 0)
                if l <= 0 and a <= 0:
                    error_text.value = "Enter liters or amount"
                    page.update()
                    return
                if l <= 0: l = a / price
                if l > stock:
                    error_text.value = f"Insufficient stock ({stock:.1f}L)"
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
                        pump_id = PUMP_MAP.get(fuel_pump_name, 1)
                        gcash_data = create_gcash_dialog_checkout(
                            auth,
                            product_type="fuel",
                            attendant_name=attendant_name,
                            pump_id=pump_id,
                            liters_sold=l,
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
                            show_snack(ft.SnackBar(ft.Text(f"GCash failed: {error_msg}"), bgcolor=RED))
                            open_fuel_dialog(fuel_pump_name)
                        page.run_thread(show_error)

                threading.Thread(target=do_create, daemon=True).start()

            except Exception as ex:
                error_text.value = f"Invalid: {ex}"
                page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"{fuel_pump_name} - ₱{price:.2f}/L", weight=ft.FontWeight.BOLD),
            content=ft.Column(tight=True, spacing=12, controls=[
                ft.Text(f"Stock: {stock:.0f}L / {tank_capacity:.0f}L" if fuel else f"Price: ₱{price:.2f}", size=12, color="grey"),
                liters_field,
                ft.Text("or", text_align=ft.TextAlign.CENTER),
                amount_field,
                error_text
            ]),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.FilledButton("Confirm", style=ft.ButtonStyle(bgcolor=RED, color="white"), on_click=confirm_cash_dlg),
                ft.Button(
                    style=ft.ButtonStyle(bgcolor="#007CFF", color="white"),
                    on_click=confirm_gcash_dlg,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        tight=True,
                        controls=[
                            ft.Image(src="assets/gcash_logo.png", width=20, height=20, fit=ft.BoxFit.CONTAIN, error_content=ft.Icon(ft.Icons.PAYMENT, size=16, color="white")),
                            ft.Text("GCash"),
                        ],
                    ),
                ),
            ],
        )
        page.show_dialog(dialog)

    status_banner = ft.Container()

    def build_dashboard_layout():
        if fuels_state["error"]:
            status_banner.bgcolor = "#FFF3CD"
            status_banner.padding = 10
            status_banner.border_radius = 8
            status_banner.content = ft.Text(f"API offline, using cached/fallback prices. Error: {fuels_state['error']}", size=12, color="#856404")
        else:
            status_banner.content = None
            status_banner.padding = 0

        return ft.Column(
            alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20, 
            controls=[
                status_banner,
                ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=40, controls=[
                    create_fuel_card("Regular 1", COLOR_REGULAR, BAR_GREEN),
                    create_fuel_card("Premium 1", COLOR_PREMIUM, BAR_YELLOW),
                    create_fuel_card("Diesel 1", COLOR_DIESEL, BAR_RED),
                ]),
                ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=40, controls=[
                    create_fuel_card("Regular 2", COLOR_REGULAR, BAR_GREEN),
                    create_fuel_card("Premium 2", COLOR_PREMIUM, BAR_YELLOW),
                    create_fuel_card("Diesel 2", COLOR_DIESEL, BAR_RED),
                ])
            ]
        )
    
    if "fuels_data" in auth:
        body = ft.Container(expand=True, bgcolor="white", alignment=ft.Alignment(0, 0), content=build_dashboard_layout())
    else:
        body = ft.Container(expand=True, bgcolor="white", alignment=ft.Alignment(0, 0), content=ft.ProgressRing(width=40, color=RED))

    def load_fuels(e=None):
        if "fuels_data" not in auth:
            time.sleep(0.1)
        try:
            try:
                fuels = get_fuels(auth)
                auth["fuels_data"] = fuels
                fuel_lookup.clear()
                for f in fuels:
                    fuel_lookup[f["name"]] = f
            except Exception as ex:
                fuels_state["error"] = str(ex)
                print(f"[API] get_fuels failed: {ex}")

            if "fuels_data" in auth or fuels_state["error"]:
                body.content = build_dashboard_layout()
        except Exception as thread_error:
            print(f"[Thread Error] Crash while rendering UI: {thread_error}")
        finally:
            page.update()

    page.run_thread(load_fuels)

    header = ft.Container(
        bgcolor=RED, height=100, padding=20,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(spacing=10, controls=[
                    ft.TextButton("← Back", style=ft.ButtonStyle(color="white"), on_click=go_back),
                    ft.Text("Fuels", size=28, weight=ft.FontWeight.BOLD, color="white"),
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

    return ft.Column(spacing=0, expand=True, controls=[header, body, footer])
