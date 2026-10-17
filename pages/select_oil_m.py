
import flet as ft
import time
from pages.api_client import get_oils

MOBILE_RED = "#8B0000"

def build_oil_page_mobile(page: ft.Page, auth: dict):
    page.title = "Oil Selection"
    page.bgcolor = MOBILE_RED
    page.padding = 0
    page.window.width = 390
    page.window.height = 844
    page.window.resizable = False

    def loading_indicator():
        return ft.Container(
            content=ft.ProgressRing(color=MOBILE_RED, width=40, height=40, stroke_width=4),
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.only(top=60),
        )

    def go_back(e):
        from pages.select_m import build_transaction_page_mobile
        page.controls.clear()
        page.add(build_transaction_page_mobile(page, auth))
        page.update()

    def open_oil_dialog(oil: dict):
        oil_id = oil["id"]
        oil_name = f"{oil.get('brand','')} {oil.get('name','')}"
        price = oil["price"]
        stock = oil["stock"]
        qty_field = ft.TextField(label="Quantity", keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)
        total_field = ft.TextField(label="Total", read_only=True, value="₱0.00")
        error_text = ft.Text("", color="red", size=12)

        def on_qty(e):
            try:
                q = float(qty_field.value or 0)
                total_field.value = f"₱{q*price:.2f}" if q>0 else "₱0.00"
                error_text.value = f"Only {stock} left" if q>stock else ""
                page.update()
            except:
                pass

        qty_field.on_change = on_qty

        def confirm(e):
            try:
                q = int(float(qty_field.value or 0))
                if q<=0: error_text.value="Enter qty"; page.update(); return
                if q>stock: error_text.value="Insufficient stock"; page.update(); return
                page.pop_dialog()
                from pages.pos_m import build_pos_page_mobile
                tx = {"label": oil_name, "details": f"{q} x ₱{price:.2f}", "total": q*price, "quantity": q, "oil_id": oil_id, "type":"oil"}
                page.controls.clear()
                page.add(build_pos_page_mobile(page, auth, tx))
                page.update()
            except Exception as ex:
                error_text.value=str(ex); page.update()

        dlg = ft.AlertDialog(
            title=ft.Text(oil_name, weight=ft.FontWeight.BOLD),
            content=ft.Column(tight=True, controls=[ft.Text(f"Stock: {stock} pcs | ₱{price:.2f}", size=12), qty_field, total_field, error_text]),
            actions=[ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()), ft.FilledButton("Confirm", bgcolor=MOBILE_RED, color="white", on_click=confirm)]
        )
        page.show_dialog(dlg)

    def oil_card(oil):
        low = oil["stock"] <= oil.get("low_stock_threshold",5)
        return ft.Container(
            content=ft.Column(controls=[ft.Icon(ft.Icons.WATER_DROP_OUTLINED, size=48, color="black"), ft.Text(f"Stock: {oil['stock']}", size=11, weight=ft.FontWeight.BOLD, color=MOBILE_RED if low else "black"), ft.Text(f"₱{oil['price']:.2f}", size=11, color="grey"), ft.Text(f"{oil.get('brand','')} {oil.get('name','')}", size=12, weight=ft.FontWeight.BOLD, color=MOBILE_RED, text_align=ft.TextAlign.CENTER, max_lines=1)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            border=ft.Border.all(1.5, MOBILE_RED), border_radius=12, padding=ft.Padding.symmetric(horizontal=12, vertical=16), bgcolor="white", expand=True, ink=True, on_click=lambda e, o=oil: open_oil_dialog(o)
        )

    body = ft.Container(expand=True, padding=ft.Padding.symmetric(horizontal=20))

    def build_grid():
        oils = auth.get("oils_data", [])
        rows=[]
        for i in range(0,len(oils),2):
            left = oil_card(oils[i])
            if i+1 < len(oils):
                right = oil_card(oils[i+1])
                rows.append(ft.Row(controls=[left, ft.Container(width=12), right]))
            else:
                rows.append(ft.Row(controls=[left]))
            rows.append(ft.Container(height=12))
        return ft.Column(controls=rows, scroll=ft.ScrollMode.ADAPTIVE, spacing=0, expand=True, alignment=ft.MainAxisAlignment.CENTER)

    def load_oils():
        try:
            oils = get_oils(auth)
            auth["oils_data"] = oils
            body.content = build_grid()
        except Exception as ex:
            print(f"get_oils failed {ex}")
            if "oils_data" not in auth:
                auth["oils_data"] = [{"id": i, "brand": f"Brand {i}", "name": f"OIL {i}", "stock": 20, "price": 250.0, "low_stock_threshold":5} for i in range(1,7)]
                body.content = build_grid()
        page.update()

    if "oils_data" not in auth:
        body.content = loading_indicator()
        page.run_thread(load_oils)
    else:
        body.content = build_grid()

    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Column(controls=[ft.Text("Pump", size=16, weight=ft.FontWeight.BOLD, color="white"), ft.Text("Attendant", size=16, weight=ft.FontWeight.BOLD, color="white")], spacing=0),
                ft.Row(controls=[ft.Text("U-FUEL", size=16, weight=ft.FontWeight.BOLD, color="white"), ft.Container(content=ft.Image(src="u-fuel_logo.jpg", width=40, height=40, fit=ft.BoxFit.CONTAIN), bgcolor="white", border_radius=8, padding=4, width=40, height=40)], spacing=8),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.Padding.symmetric(horizontal=20, vertical=14),
    )

    content_card = ft.Container(content=ft.Column(controls=[ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=MOBILE_RED, on_click=go_back), body], spacing=0), bgcolor="white", border_radius=ft.BorderRadius(top_left=28, top_right=28, bottom_left=0, bottom_right=0), expand=True, padding=ft.Padding.only(top=12))
    footer = ft.Container(content=ft.Text("GAStoKITA", size=13, color="white", text_align=ft.TextAlign.CENTER), bgcolor=MOBILE_RED, padding=ft.Padding.symmetric(vertical=14), alignment=ft.Alignment.CENTER)

    return ft.SafeArea(
        content=ft.Column(controls=[header, ft.Container(height=10), content_card, footer], expand=True, spacing=0),
        expand=True,
    )