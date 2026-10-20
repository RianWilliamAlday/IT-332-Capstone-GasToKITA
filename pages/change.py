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

    items = payload.get("items", [])
    if items:
        for item in items:
            p.text(f"{item}\n")
    else:
        line = f"{payload.get('label','')} {payload.get('details','')}".strip()
        p.text(f"{line}\n")

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

    s = sale[0] if isinstance(sale, list) and sale else sale

    ref_no = ""
    if isinstance(s, dict):
        ref_no = (
            s.get('receipt_no') or 
            s.get('transaction_ref') or 
            s.get('receipt_number') or 
            s.get('gcash_ref_no') or ""
        )
        if not ref_no and 'id' in s:
            prefix = "F" if tx_type == "fuel" else "O"
            ref_no = f"{prefix}-{s['id']:06d}"

    tx = transaction or {}
    if isinstance(tx, list):
        tx = tx[0] if tx and isinstance(tx[0], dict) else {}

    raw_label = tx.get('label', '') if isinstance(tx, dict) else ""
    raw_details = tx.get('details', '') if isinstance(tx, dict) else ""

    clean_details = (
        raw_details
        .replace("GCash PAID - ", "")
        .replace("GCash PAID", "")
        .replace('₱', 'P')
        .replace('?', '')
        .strip()
    )
    clean_label = raw_label.replace('₱', 'P').strip()

    items_list = []
    if isinstance(s, dict) and (s.get("fuel_sales") or s.get("oil_sales")):
        for fs in s.get("fuel_sales", []):
            fuel_name = (fs.get('fuel_name') or fs.get('name') or "Fuel").split()[0]
            liters = float(fs.get('liters_sold', 0))
            total = float(fs.get('total_amount', 0))
            price = float(fs.get('unit_price') or fs.get('price') or fs.get('price_per_liter') or (total / liters if liters > 0 else 0))
            items_list.append(f"{fuel_name} {liters:.3f}L x P{price:.2f}")

        for os_item in s.get("oil_sales", []):
            p_name = os_item.get('product_name') or f"{os_item.get('brand','')} {os_item.get('name','')}".strip() or "Oil"
            qty = int(os_item.get('quantity', 1))
            total = float(os_item.get('total_amount', 0))
            price = float(os_item.get('unit_price') or os_item.get('price') or (total / qty if qty > 0 else total))
            items_list.append(f"{p_name} {qty} x P{price:.2f}")
    elif isinstance(auth, dict) and auth.get("cart") and (auth["cart"].get("fuel_items") or auth["cart"].get("oil_items")):
        cart = auth.get("cart", {})
        for fi in cart.get("fuel_items", []):
            fuel_name = (fi.get("fuel_name") or "Fuel").split()[0]
            liters = float(fi.get("liters_sold", 0))
            total = float(fi.get("total", 0))
            price = float(fi.get("unit_price") or fi.get("price") or (total / liters if liters > 0 else 0))
            items_list.append(f"{fuel_name} {liters:.3f}L x P{price:.2f}")

        for oi in cart.get("oil_items", []):
            p_name = oi.get("oil_name", "Oil")
            qty = int(oi.get("quantity", 1))
            price = float(oi.get("price", 0))
            items_list.append(f"{p_name} {qty} x P{price:.2f}")

    def on_print(e):
        try:
            payload = {
                "label": "" if items_list else clean_label,
                "details": "" if items_list else clean_details,
                "total": float(tx.get('total', 0) if isinstance(tx, dict) else 0),
                "paid": paid,
                "change": change,
                "items": items_list
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
            sale_id = s.get('id') or s.get('sale_id') or ref_no or "1"
            receipt_no = ref_no or f"TEMP-{sale_id}"
            
            path = save_receipt_pdf(auth, sale_id, receipt_no, tx_type)
            show_snack(f"Printer offline - Receipt saved to {path}", color=GREEN_BUTTON)
        except Exception as pdf_err:
            show_snack(f"Failed to generate PDF: {pdf_err}", color=RED)

    def on_done(e):
        from pages.select_pa import pa_selection
        page.clean()
        page.add(pa_selection(page, auth))
        page.update()

    display_text = ", ".join(items_list) if items_list else f"{clean_label} {clean_details}".strip()

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
                    padding=15,
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5,
                        controls=[
                            ft.Text(display_text, size=12, color="black", text_align=ft.TextAlign.CENTER, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(f"Paid: ₱{paid:.2f}", size=14),
                            ft.Text(f"Due: ₱{float(tx.get('total',0)):.2f}" if tx else "", size=14),
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