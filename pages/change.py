import os
import flet as ft
from pages.api_client import save_receipt_pdf, BASE_URL

RED = "#A61E22"
LIGHT_GRAY = "#E9E9E9"
CARD_GRAY = "#D9D9D9"
GREEN_BUTTON = "#118C4F"

def check_printer(name="XP-58H"):
    """Checks via WMI whether the local Windows USB thermal printer is online."""
    try:
        import win32com.client
        wmi = win32com.client.GetObject("winmgmts:")
        for p in wmi.ExecQuery(f"Select * from Win32_Printer where Name='{name}'"):
            return not p.WorkOffline
        return False
    except Exception as e:
        print(f"WMI check fail, attempting print anyway: {e}")
        return True

def print_receipt_locally(payload: dict, printer_name: str = "XP-58H"):
    """Direct ESC/POS thermal print over local USB."""
    if not check_printer(printer_name):
        raise Exception("Printer offline or USB unplugged")

    from escpos.printer import Win32Raw
    p = Win32Raw(printer_name)
    
    p.set(align='center', bold=True, width=2, height=2)
    p.text("GASTOKITA\n")
    p.set(align='center', bold=False, width=1, height=1)
    p.text("U-Fuel Receipt\n")
    p.text("------------------------------\n")
    p.set(align='left')
    p.text(f"{payload.get('label','')} {payload.get('details','')}\n")
    p.text(f"Due:  P{payload.get('total',0):.2f}\n")
    p.text(f"Paid: P{payload.get('paid',0):.2f}\n")
    p.set(align='center', bold=True, width=2, height=2)
    p.text(f"\nP {payload.get('change',0):.2f}\n")
    p.set(align='center', bold=True, width=1, height=1)
    p.text("CHANGE\n\n")
    p.set(align='center')
    p.text("Thank you!\n")
    p.text("------------------------------\n")
    p.cut()
    p.close()

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
            payload = {
                "label": tx.get('label', '') if isinstance(tx, dict) else "",
                "details": tx.get('details', '').replace('₱', 'P').replace('?', '') if isinstance(tx, dict) else "",
                "total": float(tx.get('total', 0) if isinstance(tx, dict) else 0),
                "paid": paid,
                "change": change
            }
            
            print_receipt_locally(payload, printer_name="XP-58H")
            show_snack("Printed successfully", color=GREEN_BUTTON)
            return

        except Exception as err:
            print(f"Local printer failed, falling back to PDF download: {err}")
        if not sale:
            show_snack("Printer unavailable & no sale data found for PDF", color=RED)
            return
        try:
            s = sale[0] if isinstance(sale, list) and sale else sale
            sale_id = s.get('id') or s.get('sale_id')
            receipt_no = s.get('receipt_no') or s.get('receipt_number') or f"TEMP-{sale_id}"
            
            path = save_receipt_pdf(auth, sale_id, receipt_no, tx_type)
            show_snack(f"Printer offline - Receipt saved to {path}", color=GREEN_BUTTON)
        except Exception as pdf_err:
            show_snack(f"Failed to generate PDF: {pdf_err}", color=RED)

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
                    alignment=ft.Alignment(0, 0),
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
                                alignment=ft.Alignment(0, 0),
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