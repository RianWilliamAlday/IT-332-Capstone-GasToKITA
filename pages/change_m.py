
import flet as ft
import requests
from pages.api_client import BASE_URL

MOBILE_RED = "#8B0000"
GREEN = "#118C4F"
NAVY = "#0F3057"

def build_change_page_mobile(page: ft.Page, auth: dict, transaction: dict=None, paid: float=0, change: float=0, sale=None, tx_type="fuel"):
    page.title = "Change"
    page.bgcolor = MOBILE_RED
    page.padding = 0
    page.window.width = 390
    page.window.height = 844
    page.window.resizable = False


    def show_snack(msg, color=MOBILE_RED):
        snack = ft.SnackBar(content=ft.Text(msg, color="white"), bgcolor=color, open=True)
        page.overlay.append(snack)
        page.update()

    def on_print(e):
        tx = transaction if isinstance(transaction, dict) else {}
        try:
            res = requests.post(f"{BASE_URL}/api/receipts/print", json={"label": tx.get('label',''), "details": tx.get('details','').replace('₱','P'), "total": float(tx.get('total',0)), "paid": paid, "change": change}, timeout=3)
            if res.status_code!=200: raise Exception(f"Printer offline {res.status_code}")
            data = res.json()
            if isinstance(data, list): data = data[0] if data else {}
            if data.get('status')!='printed': raise Exception(data.get('message','printer error'))
            show_snack("Printed", color=GREEN)
            return
        except Exception as err:
            print(f"Printer fail PDF fallback: {err}")

        if not sale:
            show_snack("No sale data", color=MOBILE_RED)
            return
        s = sale[0] if isinstance(sale, list) and sale else sale
        sale_id = s.get('id') or s.get('sale_id')
        receipt_no = s.get('receipt_no') or s.get('receipt_number') or f"TEMP-{sale_id}"
        try:
            from pages.api_client import save_receipt_pdf
            path = save_receipt_pdf(auth, sale_id, receipt_no, tx_type)
            show_snack(f"Saved to {path}", color=GREEN)
        except Exception as ex:
            show_snack(f"PDF failed: {ex}", color=MOBILE_RED)

    def on_done(e):
        from pages.select_pa_m import build_pa_page_mobile
        page.controls.clear()
        page.add(build_pa_page_mobile(page, auth))
        page.update()

    change_box = ft.Container(content=ft.Column(controls=[ft.Text(f"₱ {change:.2f}", size=22, weight=ft.FontWeight.BOLD, color="white", text_align=ft.TextAlign.CENTER), ft.Text("CHANGE", size=13, weight=ft.FontWeight.BOLD, color="white")], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4), bgcolor=MOBILE_RED, border_radius=10, padding=ft.Padding.symmetric(horizontal=24, vertical=16), alignment=ft.Alignment.CENTER, width=float("inf"))
    details_box = ft.Container(content=ft.Column(controls=[ft.Text(f"{transaction.get('label','')} {transaction.get('details','')}" if transaction else "", size=13, color="grey", text_align=ft.TextAlign.CENTER), ft.Text(f"Paid: ₱{paid:.2f}", size=15, weight=ft.FontWeight.BOLD, color=MOBILE_RED), ft.Text(f"Due: ₱{float(transaction.get('total',0)):.2f}" if transaction else "", size=14), ft.Text(f"Change: ₱{change:.2f}", size=15, weight=ft.FontWeight.BOLD, color=MOBILE_RED)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8), border=ft.Border.all(1.5, MOBILE_RED), border_radius=10, padding=ft.Padding.all(20), width=float("inf"))

    done_btn = ft.Container(content=ft.Text("DONE", size=14, weight=ft.FontWeight.BOLD, color="white"), bgcolor=GREEN, border_radius=10, padding=ft.Padding.symmetric(horizontal=20, vertical=14), ink=True, on_click=on_done, alignment=ft.Alignment.CENTER)
    print_btn = ft.Container(content=ft.Text("PRINT RECEIPT", size=12, weight=ft.FontWeight.BOLD, color="white"), bgcolor=NAVY, border_radius=10, padding=ft.Padding.symmetric(horizontal=20, vertical=14), expand=True, ink=True, on_click=on_print, alignment=ft.Alignment.CENTER)

    outer = ft.Container(content=ft.Column(controls=[change_box, ft.Container(height=16), details_box, ft.Container(height=16), ft.Row(controls=[done_btn, print_btn], spacing=12)], spacing=0), border=ft.Border.all(1.5, MOBILE_RED), border_radius=12, padding=ft.Padding.all(16), width=float("inf"))
    
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
    
    content_card = ft.Container(content=ft.Column(controls=[outer], expand=True, alignment=ft.MainAxisAlignment.CENTER), bgcolor="white", border_radius=ft.BorderRadius(top_left=28, top_right=28, bottom_left=0, bottom_right=0), expand=True, padding=ft.Padding.all(24), alignment=ft.Alignment.CENTER)
    footer = ft.Container(content=ft.Text("GAStoKITA", size=13, color="white", text_align=ft.TextAlign.CENTER), bgcolor=MOBILE_RED, padding=ft.Padding.symmetric(vertical=14), alignment=ft.Alignment.CENTER)
    
    return ft.SafeArea(
        content=ft.Column(controls=[header, ft.Container(height=10), content_card, footer], expand=True, spacing=0),
        expand=True,
    )