import flet as ft

RED = "#A61E22"
LIGHT_GRAY = "#E9E9E9"
NAVY_COLOR = "#0F3057"
GREEN_COLOR = "#006400"

def build_pos_page(page: ft.Page, auth: dict, transaction: dict = None):
    page.title = "GasToKITA"
    page.bgcolor = LIGHT_GRAY
    page.padding = 0

    total_due = float(transaction.get("total", 0)) if transaction else 0
    label = transaction.get("label", "") if transaction else ""
    details = transaction.get("details", "") if transaction else ""
    tx_type = transaction.get("type", "fuel") if transaction else "fuel"

    paid = {"value": 0.0}

    def show_snack(message, bgcolor=None):
        snack = ft.SnackBar(content=ft.Text(message), bgcolor=bgcolor)
        page.show_dialog(snack)

    amount_field = ft.TextField(
        value=f"{paid['value']:.2f}",
        width=160,
        height=44,
        text_align=ft.TextAlign.RIGHT,
        keyboard_type=ft.KeyboardType.NUMBER,
        filled=False,
        border=None,
    )

    def on_amount_change(e):
        v = e.control.value or ""
        s = v.replace("â‚±", "").replace(",", "").strip()
        try:
            paid["value"] = float(s) if s not in ("", ".") else 0.0
        except ValueError:
            return

    amount_field.on_change = on_amount_change

    amount_box = ft.Container(
        width=185,
        height=50,
        bgcolor=LIGHT_GRAY,
        border_radius=16,
        padding=ft.Padding.only(left=10, right=10),
        alignment=ft.Alignment(0, 0),
        content=amount_field
    )

    def refresh():
        amount_field.value = f"{paid['value']:.2f}"
        page.update()

    def add_value(e, v):
        paid["value"] += float(v)
        refresh()

    def on_back(e):
        if paid["value"] > 0:
            paid["value"] = 0
            refresh()
            return
        if tx_type == "fuel":
            from pages.select_gas import build_pump_page
            page.controls.clear()
            page.add(build_pump_page(page, auth))
            page.update()
        else:
            from pages.select_oil import build_oil_page
            page.controls.clear()
            page.add(build_oil_page(page, auth))
            page.update()

    def on_exact(e):
        paid["value"] = total_due
        refresh()

    def on_submit(e):
        if paid["value"] < total_due:
            show_snack(f"Insufficient. Need â‚±{total_due - paid['value']:.2f}", bgcolor=RED)
            return
        change = paid["value"] - total_due
        print(f"PAID {label} {details} Total:{total_due} Paid:{paid['value']} Change:{change} by {auth.get('selected_attendant')}")
        show_snack(f"Paid! Change â‚±{change:.2f}", bgcolor=GREEN_COLOR)
        from pages.change import build_change_page
        page.controls.clear()
        page.add(build_change_page(page, auth, transaction, paid["value"], change))
        page.update()

    def create_value_btn(value: str):
        return ft.Container(
            width=115,
            height=48,
            bgcolor=RED,
            border_radius=18,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=lambda e, v=value: add_value(e, v),
            content=ft.Text(value, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
        )

    header = ft.Container(
        bgcolor=RED,
        height=100,
        padding=20,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("GAStoKITA", size=28, weight=ft.FontWeight.BOLD, color="white"),
                ft.Row(spacing=15, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text("U-Fuel", size=28, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Container(width=70, height=70, bgcolor="white", border_radius=12,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Image(src="u-fuel_logo.jpg", fit=ft.BoxFit.CONTAIN)),
                ]),
            ],
        ),
    )

    footer = ft.Container(height=80, bgcolor=RED)

    keypad_panel = ft.Container(
        height=380,
        width=780,
        bgcolor=LIGHT_GRAY,
        border_radius=20,
        border=ft.Border.all(width=1.5, color=ft.Colors.BLACK),
        padding=20,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=14,
            controls=[
                amount_box,
                ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=35, controls=[
                    create_value_btn("50"), create_value_btn("100"), create_value_btn("200"), create_value_btn("300"),
                ]),
                ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=35, controls=[
                    create_value_btn("400"), create_value_btn("500"), create_value_btn("600"), create_value_btn("700"),
                ]),
                ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=35, controls=[
                    create_value_btn("800"), create_value_btn("900"), create_value_btn("1000"),
                ]),
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Container(width=150, height=48, bgcolor=NAVY_COLOR, border_radius=4, ink=True, on_click=on_back,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text("Back", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                    ft.Container(width=220, height=48, bgcolor=RED, border_radius=18, ink=True, on_click=on_exact,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text("EXACT AMOUNT", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                    ft.Container(width=150, height=48, bgcolor=GREEN_COLOR, border_radius=4, ink=True, on_click=on_submit,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text("Submit", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ])
            ]
        )
    )

    body = ft.Container(
        expand=True,
        alignment=ft.Alignment(0, 0),
        bgcolor=ft.Colors.WHITE,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Text(f"{label}  {details}  |  Due: â‚±{total_due:.2f}" if transaction else "Enter Payment",
                        weight=ft.FontWeight.BOLD),
                keypad_panel
            ]
        )
    )

    return ft.Column(spacing=0, expand=True, controls=[header, body, footer])