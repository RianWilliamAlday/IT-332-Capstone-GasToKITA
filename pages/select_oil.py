import flet as ft
import time
from pages.api_client import get_oils

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
        width=220, height=180, bgcolor=RED, border_radius=16, padding=8,
        on_click=lambda e: on_click(oil), ink=True,
        content=ft.Column(spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
            ft.Container(expand=True, bgcolor=WHITE, border_radius=12,
                alignment=ft.Alignment(0, 0),
                content=ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4, controls=[
                    ft.Icon(ft.Icons.WATER_DROP_OUTLINED, size=50, color="black"),
                    ft.Text(f"Stock: {stock}", size=12, weight=ft.FontWeight.BOLD, color="black" if not low else RED),
                    ft.Text(f"₱{price:.2f}", size=12, color="grey"),
                ])),
            ft.Container(height=50, alignment=ft.Alignment(0, 0),
                content=ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, controls=[
                    ft.Text(brand, size=12, weight=ft.FontWeight.BOLD, color=WHITE),
                    ft.Text(name, size=14, weight=ft.FontWeight.BOLD, color=WHITE, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ])),
        ]),
    )

def build_oil_page(page: ft.Page, auth: dict):
    page.title = "Oil Selection"
    page.bgcolor = LIGHT_GRAY
    page.padding = 0

    oils_state = {"error": None}

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
        return ft.Column(spacing=10, controls=[banner, oil_grid])

    if "oils_data" in auth:
        main_content = ft.Container(expand=True, bgcolor=WHITE, alignment=ft.Alignment(0, -0.2), padding=40, content=build_oil_layout())
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
                    ft.Text("Cashier", size=28, weight=ft.FontWeight.BOLD, color="white"),
                ]),
                ft.Row(spacing=15, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text("U-Fuel", size=28, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Container(width=70, height=70, bgcolor="white", border_radius=12,
                        content=ft.Image(src="u-fuel_logo.jpg", fit=ft.BoxFit.CONTAIN)),
                ]),
            ],
        ),
    )
    footer = ft.Container(height=80, bgcolor=RED)

    return ft.Column(spacing=0, expand=True, controls=[header, main_content, footer])
