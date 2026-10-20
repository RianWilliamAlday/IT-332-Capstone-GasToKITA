import flet as ft
from pages.api_client import create_fuel_sale, create_oil_sale, submit_multi_sale
from pages.sidebar_m import Sidebar

MOBILE_RED = "#8B0000"
GREEN_COLOR = "#118C4F"
NAVY_COLOR = "#0F3057"

def build_pos_page_mobile(page: ft.Page, auth: dict, transaction: dict = None):
    page.bgcolor = MOBILE_RED
    page.padding = 0
    page.window.width = 390
    page.window.height = 844
    page.window.resizable = False

    sidebar = Sidebar(page, auth, active="pos")

    total_due = float(transaction.get("total", 0)) if transaction else 0
    label = transaction.get("label", "") if transaction else ""
    details = transaction.get("details", "") if transaction else ""
    tx_type = transaction.get("type", "fuel") if transaction else "fuel"

    paid = {"value": 0.0}

    def show_snack(message, bgcolor=None):
        page.show_dialog(ft.SnackBar(content=ft.Text(message), bgcolor=bgcolor))

    amount_field = ft.TextField(
        value="",
        hint_text="0.00",
        width=180,
        height=48,
        text_align=ft.TextAlign.RIGHT,
        keyboard_type=ft.KeyboardType.NUMBER,
        read_only=False,
        autofocus=True,
    )

    def on_amount_change(e):
        v = e.control.value or ""
        s = v.replace("₱", "").replace(",", "").strip()
        try:
            paid["value"] = float(s) if s not in ("", ".") else 0.0
        except ValueError:
            pass

    def on_amount_focus(e):
        if amount_field.value in ("0.00", "0", "0.0"):
            amount_field.value = ""
            page.update()

    def on_amount_blur(e):
        if not amount_field.value and paid["value"] > 0:
            amount_field.value = f"{paid['value']:.2f}"
            page.update()

    amount_field.on_change = on_amount_change
    amount_field.on_focus = on_amount_focus
    amount_field.on_blur = on_amount_blur

    def refresh():
        amount_field.value = f"{paid['value']:.2f}" if paid["value"] > 0 else ""
        page.update()

    def add_value(v):
        paid["value"] += float(v)
        refresh()

    def on_exact(e):
        paid["value"] = total_due
        refresh()

    def on_back(e):
        from pages.select_multi_m import build_multi_page_mobile
        page.controls.clear()
        page.add(build_multi_page_mobile(page, auth))

    def create_btn(val):
        return ft.Container(
            content=ft.Text(val, size=16, weight=ft.FontWeight.BOLD, color="white"),
            bgcolor=MOBILE_RED, border_radius=10, alignment=ft.Alignment(0, 0),
            padding=ft.Padding.symmetric(vertical=12), expand=True, ink=True,
            on_click=lambda e: add_value(val)
        )

    def on_submit(e):
        if paid["value"] < total_due:
            show_snack(f"Insufficient amount. Short by ₱{total_due - paid['value']:.2f}")
            return

        change = paid["value"] - total_due
        attendant = auth.get("selected_attendant") or auth.get("user", {}).get("name") or "Attendant 1"

        try:
            if tx_type == "fuel":
                pump_id = transaction.get("pump_id", 1)
                liters = transaction.get("liters", 0)
                result = create_fuel_sale(auth, pump_id, liters, attendant, "cash", paid["value"])
            elif tx_type == "oil":
                oil_id = transaction.get("oil_id")
                qty = transaction.get("quantity", 1)
                result = create_oil_sale(auth, oil_id, qty, attendant, "cash", paid["value"])
            else:
                # multi-item cart (uses auth["cart"])
                result = submit_multi_sale(
                    auth, attendant_name=attendant,
                    payment_method="cash", amount_paid=paid["value"],
                )

            auth.pop("fuels_data", None)
            auth.pop("oils_data", None)

            # Keep a copy of what was bought for the change page, then clear the cart
            cart = auth.get("cart") or {}
            receipt_tx = dict(transaction)
            receipt_tx["fuel_items"] = list(cart.get("fuel_items", []))
            receipt_tx["oil_items"] = list(cart.get("oil_items", []))
            auth["cart"] = {"fuel_items": [], "oil_items": []}

            from pages.change_m import build_change_page_mobile
            page.controls.clear()
            page.add(build_change_page_mobile(page, auth, receipt_tx, paid["value"], change, sale=result, tx_type=tx_type))
            page.update()

        except Exception as ex:
            show_snack(f"Failed: {ex}")

    header = ft.Container(
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

    keypad = ft.Column(
        controls=[
            ft.Row(controls=[create_btn("50"), create_btn("100"), create_btn("200")], spacing=10),
            ft.Row(controls=[create_btn("300"), create_btn("400"), create_btn("500")], spacing=10),
            ft.Row(controls=[create_btn("600"), create_btn("700"), create_btn("1000")], spacing=10),
            ft.Container(
                content=ft.Text("EXACT AMOUNT", size=14, weight=ft.FontWeight.BOLD, color="white"),
                bgcolor=NAVY_COLOR, border_radius=10, alignment=ft.Alignment(0, 0),
                padding=ft.Padding.symmetric(vertical=12), ink=True, on_click=on_exact
            ),
        ],
        spacing=10
    )

    outer = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(f"{label} ({details})", size=14, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Text(f"Due: ₱{total_due:.2f}", size=18, weight=ft.FontWeight.BOLD, color=MOBILE_RED),
                ft.Container(height=10),
                ft.Row(controls=[ft.Text("Paid: ₱", size=16, weight=ft.FontWeight.BOLD), amount_field], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=10),
                keypad,
                ft.Container(height=10),
                ft.Container(
                    content=ft.Text("SUBMIT", size=16, weight=ft.FontWeight.BOLD, color="white"),
                    bgcolor=GREEN_COLOR, border_radius=10, alignment=ft.Alignment(0, 0),
                    padding=ft.Padding.symmetric(vertical=14), ink=True, on_click=on_submit
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        border=ft.Border.all(1.5, MOBILE_RED),
        border_radius=12,
        padding=ft.Padding.all(16),
        width=float("inf"),
    )

    content_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(controls=[ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=MOBILE_RED, on_click=on_back)], alignment=ft.MainAxisAlignment.START),
                outer,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.ADAPTIVE,
        ),
        bgcolor="white",
        border_radius=ft.BorderRadius(top_left=28, top_right=28, bottom_left=0, bottom_right=0),
        expand=True,
        padding=ft.Padding.all(20)
    )

    footer = ft.Container(content=ft.Text("GAStoKITA", size=13, color="white", text_align=ft.TextAlign.CENTER), bgcolor=MOBILE_RED, padding=ft.Padding.symmetric(vertical=14), alignment=ft.Alignment.CENTER)

    return ft.SafeArea(
        content=sidebar.wrap(ft.Column(controls=[header, ft.Container(height=10), content_card, footer], expand=True, spacing=0)),
        expand=True,
    )