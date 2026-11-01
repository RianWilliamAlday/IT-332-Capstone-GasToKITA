
import flet as ft
import time
from pages.api_client import get_fuels, PUMP_MAP

MOBILE_RED = "#8B0000"
GREEN = "#2E7D32"
YELLOW = "#F9A825"
BAR_GREEN = "#12B347"
BAR_YELLOW = "#F4B400"
BAR_RED = "#E3242B"

FALLBACK = {"Regular":55.0,"Premium":60.0,"Diesel":50.0}

def build_gas_page_mobile(page: ft.Page, auth: dict):
    page.title = "Fuel Selection"
    page.bgcolor = MOBILE_RED
    page.padding = 0
    page.window.width = 390
    page.window.height = 844
    page.window.resizable = False

    def loading_indicator():
        return ft.Container(
            content=ft.ProgressRing(color=MOBILE_RED, width=40, height=40, stroke_width=4),
            alignment=ft.Alignment.CENTER,
            expand=True,
    )

    fuel_lookup = {}
    if "fuels_data" in auth:
        for f in auth["fuels_data"]:
            fuel_lookup[f["name"]] = f

    def go_back(e):
        from pages.select_m import build_transaction_page_mobile
        page.controls.clear()
        page.add(build_transaction_page_mobile(page, auth))
        page.update()

    def open_fuel_dialog(pump_name: str):
        base = pump_name.split()[0]
        fuel = fuel_lookup.get(base)
        price = fuel["price"] if fuel else FALLBACK.get(base, 60)
        stock = fuel["actual_liters"] if fuel else 9999

        lock = {"busy": False}
        liters_field = ft.TextField(label="Liters", keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)
        amount_field = ft.TextField(label="Amount (PHP)", keyboard_type=ft.KeyboardType.NUMBER)
        error_text = ft.Text("", color="red", size=12)

        def on_liters(e):
            if lock["busy"]: return
            try:
                l = float(liters_field.value or 0)
                lock["busy"] = True
                amount_field.value = f"{l*price:.2f}" if l>0 else ""
                error_text.value = f"Only {stock:.1f}L left" if l>stock else ""
                page.update()
            finally:
                lock["busy"]=False
        def on_amount(e):
            if lock["busy"]: return
            try:
                a = float(amount_field.value or 0)
                lock["busy"]=True
                l = a/price if price else 0
                liters_field.value = f"{l:.3f}" if a>0 else ""
                error_text.value = f"Only {stock:.1f}L left" if l>stock else ""
                page.update()
            finally:
                lock["busy"]=False

        liters_field.on_change = on_liters
        amount_field.on_change = on_amount

        def confirm(e):
            try:
                l = float(liters_field.value or 0)
                a = float(amount_field.value or 0)
                if l<=0 and a<=0: 
                    error_text.value="Enter liters or amount"; page.update(); return
                if l<=0: l=a/price
                if a<=0: a=l*price
                if l>stock:
                    error_text.value=f"Insufficient {stock:.1f}L"; page.update(); return
                page.pop_dialog()
                from pages.pos_m import build_pos_page_mobile
                tx = {"label": pump_name, "details": f"{l:.3f}L x ₱{price:.2f}", "total": a, "liters": l, "pump_id": PUMP_MAP.get(pump_name,1), "type":"fuel"}
                page.controls.clear()
                page.add(build_pos_page_mobile(page, auth, tx))
                page.update()
            except Exception as ex:
                error_text.value=str(ex); page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"{pump_name} - ₱{price:.2f}/L", weight=ft.FontWeight.BOLD),
            content=ft.Column(tight=True, controls=[ft.Text(f"Stock: {stock:.0f}L", size=12, color="grey"), liters_field, ft.Text("or", text_align=ft.TextAlign.CENTER), amount_field, error_text]),
            actions=[ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()), ft.FilledButton("Confirm", bgcolor=MOBILE_RED, color="white", on_click=confirm)]
        )
        page.show_dialog(dlg)

    def bar_color(pct):
        if pct > 60: return BAR_GREEN
        if pct > 25: return BAR_YELLOW
        return BAR_RED

    def pump_card(pct, label, color):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(label, size=13, weight=ft.FontWeight.BOLD, color="white", text_align=ft.TextAlign.CENTER),
                    ft.Text(f"{pct:.0f}%", size=22, weight=ft.FontWeight.BOLD, color="white", text_align=ft.TextAlign.CENTER),
                    ft.ProgressBar(
                        value=max(0, min(pct, 100)) / 100,
                        color=bar_color(pct),
                        bgcolor="white",
                        bar_height=8,
                        border_radius=4,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                spacing=6,
            ),
            bgcolor=color, border_radius=12, padding=ft.Padding.symmetric(horizontal=12, vertical=16), expand=True, ink=True, on_click=lambda e, l=label: open_fuel_dialog(l)
        )

    def build_grid():
        def get_card_data(name, color):
            fu = fuel_lookup.get(name.split()[0])
            pct = fu.get("display_percentage", 100) if fu else 100
            return (pct, name, color)

        pumps = [
            get_card_data("Regular 1", GREEN),
            get_card_data("Regular 2", GREEN),
            get_card_data("Premium 1", MOBILE_RED),
            get_card_data("Premium 2", MOBILE_RED),
            get_card_data("Diesel 1", YELLOW),
            get_card_data("Diesel 2", YELLOW),
        ]
        rows = []
        for i in range(0, len(pumps), 2):
            rows.append(ft.Row(controls=[pump_card(*pumps[i]), ft.Container(width=12), pump_card(*pumps[i+1])], spacing=0))
        return ft.Column(controls=rows, spacing=12, scroll=ft.ScrollMode.ADAPTIVE, expand=True, alignment=ft.MainAxisAlignment.CENTER)
    
    body_content = ft.Container(content=build_grid() if "fuels_data" in auth else loading_indicator(), padding=ft.Padding.symmetric(horizontal=20), expand=True)

    def load_fuels():
        try:
            fuels = get_fuels(auth)
            auth["fuels_data"] = fuels
            for f in fuels:
                fuel_lookup[f["name"]] = f
            body_content.content = build_grid()
        except Exception as ex:
            print(f"get_fuels failed {ex}")
            if "fuels_data" not in auth:
                body_content.content = build_grid() # fallback
        page.update()

    if "fuels_data" not in auth:
        page.run_thread(load_fuels)

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

    content_card = ft.Container(content=ft.Column(controls=[ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=MOBILE_RED, on_click=go_back), body_content], spacing=0), bgcolor="white", border_radius=ft.BorderRadius(top_left=28, top_right=28, bottom_left=0, bottom_right=0), expand=True, padding=ft.Padding.only(top=12, bottom=20))
    footer = ft.Container(content=ft.Text("GAStoKITA", size=13, color="white", text_align=ft.TextAlign.CENTER), bgcolor=MOBILE_RED, padding=ft.Padding.symmetric(vertical=14), alignment=ft.Alignment.CENTER)

    return ft.SafeArea(
        content=ft.Column(controls=[header, ft.Container(height=10), content_card, footer], expand=True, spacing=0),
        expand=True,
    )
