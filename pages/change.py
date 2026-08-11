import os, requests
import flet as ft
from pages.api_client import save_receipt_pdf, download_receipt_pdf, BASE_URL

RED = "#A61E22"
LIGHT_GRAY = "#E9E9E9"
CARD_GRAY = "#D9D9D9"
GREEN_BUTTON = "#118C4F"

def build_change_page(page: ft.Page, auth: dict, transaction: dict = None, paid: float = 0, change: float = 0, sale=None, tx_type="fuel"):
    page.title = "Change"
    page.bgcolor = LIGHT_GRAY
    page.padding = 0

    def show_snack(msg, color=RED):
            snack = ft.SnackBar(content=ft.Text(msg, color="white"), bgcolor=color, open=True)
            page.overlay.append(snack)
            page.update()

    def on_print(e):
        tx = transaction
        if isinstance(tx, list):
            tx = tx[0] if tx and isinstance(tx[0], dict) else {}

        try:
            res = requests.post(f"{BASE_URL}/api/receipts/print", json={
                "label": tx.get('label','') if isinstance(tx, dict) else "",
                "details": tx.get('details','').replace('₱','P').replace('?','') if isinstance(tx, dict) else "",
                "total": float(tx.get('total',0) if isinstance(tx, dict) else 0),
                "paid": paid, "change": change
            }, timeout=3)
            if res.status_code!= 200:
                raise Exception(f"Printer offline ({res.status_code})")
            data = res.json()
            if isinstance(data, list):
                data = data[0] if data else {}
            if data.get('status')!= 'printed':
                raise Exception(data.get('message','printer error'))

            show_snack("Printed", color=GREEN_BUTTON)
            return
        except Exception as err:
            print(f"Printer fail, PDF fallback: {err}")

        if not sale:
            show_snack("No sale data", color=RED)
            return

        s = sale[0] if isinstance(sale, list) and sale else sale
        sale_id = s.get('id') or s.get('sale_id')
        receipt_no = s.get('receipt_no') or s.get('receipt_number') or f"TEMP-{sale_id}"
        from pages.api_client import save_receipt_pdf
        path = save_receipt_pdf(auth, sale_id, receipt_no, tx_type)
        show_snack(f"Printer unavailable - Saved to {path}", color=GREEN_BUTTON)

    def on_done(e):
        from pages.select_pa import pa_selection
        page.clean()
        page.add(pa_selection(page, auth))
        page.update()

    header = ft.Container(
        bgcolor=RED, height=100, padding=20,
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

    change_dialog = ft.Container(
    width=500, height=380, bgcolor=CARD_GRAY, border_radius=20,
    border=ft.Border.all(1.5, ft.Colors.BLACK87),
    content=ft.Stack(
        controls=[
            ft.Container(width=420, height=220, bgcolor=ft.Colors.WHITE, border_radius=15,
                border=ft.Border.all(1.5, ft.Colors.BLACK87), left=40, top=80,
                alignment=ft.Alignment(0,0),
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=5,
                    controls=[
                        ft.Text(f"{transaction.get('label','')} {transaction.get('details','')}" if transaction else "", size=12, color="grey"),
                        ft.Text(f"Paid: ₱{paid:.2f}", size=14),
                        ft.Text(f"Due: ₱{float(transaction.get('total',0)):.2f}" if transaction else "", size=14),
                    ]
                )
            ),
            ft.Container(width=180, height=75, bgcolor=RED, border_radius=15, left=160, top=2.5,
                alignment=ft.Alignment(0, 0),
                content=ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, controls=[
                    ft.Text(f"₱ {change:.2f}", size=24, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Text("CHANGE", size=16, weight=ft.FontWeight.BOLD, color="white"),
                ])
            ),
            ft.Container(
                width=500, left=0, top=310,
                alignment=ft.Alignment(0, 0),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=15,
                    controls=[
                        ft.Container(
                            width=110, height=45, bgcolor=GREEN_BUTTON,
                            border_radius=8, ink=True, on_click=on_done,
                            alignment=ft.Alignment(0, 0),
                            content=ft.Text("Done", size=20, weight=ft.FontWeight.BOLD, color="white")
                        ),
                        ft.Container(
                            width=130, height=45, bgcolor="#0F3057",
                            border_radius=8, ink=True, on_click=on_print,
                            alignment=ft.Alignment(0,0),
                            content=ft.Text("Print Receipt", color="white", weight=ft.FontWeight.BOLD)
                        ),
                    ]
                )
            ),
        ]
    )
)

    body_content = ft.Container(expand=True, bgcolor=ft.Colors.WHITE, alignment=ft.Alignment(0, 0), content=change_dialog)

    return ft.Column(spacing=0, expand=True, controls=[header, body_content, footer])