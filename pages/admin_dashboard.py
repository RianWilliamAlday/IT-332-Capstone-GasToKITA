import flet as ft
import threading, os, requests

DARK_RED   = "#8B0000"
MED_RED    = "#A00000"
LIGHT_CARD = "#E8E8E8"
WHITE      = "#FFFFFF"
GREEN_ALERT = "#90EE90"
LIGHT_RED = "#FFCDD2"
LIGHT_ORANGE = "#FFE0B2"
TEXT_DARK  = "#1A1A1A"
TEXT_WHITE = "#FFFFFF"
BODY_BG = "#C0C0C0"
DARK_GREEN = "#2E7D32"

BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

def _headers(auth: dict):
    token = auth.get("access_token") or auth.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}

def get_low_stock(auth: dict, include_warning=True):
    try:
        r = requests.get(f"{BASE_URL}/api/ai-inventory/low-stock", params={"product_type":"all","include_warning":include_warning}, headers=_headers(auth), timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as ex:
        print(f"[low-stock] {ex}")
        return {"total_count":0, "items":[]}

def open_dialog_compat(page: ft.Page, dialog):
    if hasattr(page, "open_dialog"):
        page.open_dialog(dialog)
    elif hasattr(page, "show_dialog"):
        page.show_dialog(dialog)
    else:
        page.dialog = dialog
        dialog.open = True
        page.update()

def close_dialog_compat(page: ft.Page):
    if hasattr(page, "close_dialog"):
        try: page.close_dialog(); return
        except: pass
    if hasattr(page, "dialog") and page.dialog:
        page.dialog.open = False
        page.update()
    if hasattr(page, "pop_dialog"):
        try: page.pop_dialog()
        except: pass

def stat_card(icon, title, value, period_label="daily", show_progress=False, progress_value=0.5, sub_label="", dropdowns=None):
    top_left = None
    if dropdowns:
        top_left = ft.Row([
            ft.Container(ft.Icon(icon, color=TEXT_WHITE, size=20), bgcolor=MED_RED, border_radius=6, padding=6),
            *[ft.Row([ft.Text(d, color=TEXT_WHITE, size=11), ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, color=TEXT_WHITE, size=14)], spacing=0, tight=True) for d in dropdowns],
        ], spacing=8)
    else:
        top_left = ft.Container(ft.Icon(icon, color=TEXT_WHITE, size=22), bgcolor=MED_RED, border_radius=6, padding=6)

    card_header = ft.Row([top_left, ft.Row([ft.Text(period_label, color=TEXT_WHITE, size=11), ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, color=TEXT_WHITE, size=14)], spacing=0, tight=True)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    body_controls = [card_header, ft.Text(title, color=TEXT_WHITE, size=13, weight=ft.FontWeight.BOLD), ft.Text(value, color=TEXT_WHITE, size=22, weight=ft.FontWeight.BOLD)]
    if show_progress:
        body_controls += [ft.Row([ft.Text(sub_label, color=TEXT_WHITE, size=10), ft.Text(f"{int(progress_value*100)}%", color=TEXT_WHITE, size=10)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), ft.ProgressBar(value=progress_value, color="#4CAF50", bgcolor="#6B0000", border_radius=4, bar_height=8, expand=True)]
    return ft.Container(content=ft.Column(body_controls, spacing=6), bgcolor=DARK_RED, border_radius=10, padding=14, expand=True)

def action_button(label: str, on_click=None) -> ft.Container:
    return ft.Container(
        width=float("inf"), alignment=ft.Alignment.CENTER,
        content=ft.Text(label, color=TEXT_DARK, size=13, weight=ft.FontWeight.W_500),
        border=ft.Border.all(1.5, DARK_RED), border_radius=6,
        padding=ft.Padding.symmetric(vertical=12, horizontal=16),
        bgcolor=WHITE, ink=True, on_click=on_click,
        on_hover=lambda e: (setattr(e.control, "bgcolor", "#F5E6E6" if e.data == "true" else WHITE), e.control.update()),
    )

def dashboard_page(page: ft.Page, auth: dict):
    page.title = "Admin Dashboard"
    page.bgcolor = DARK_RED
    page.padding = 0
    page.theme = ft.Theme(color_scheme_seed=DARK_RED)

    def show_snack(msg, color=DARK_RED):
        page.snack_bar = ft.SnackBar(content=ft.Text(msg, color="white"), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def go_inventory(e):
        from pages.inventory import inventory_page
        page.controls.clear()
        page.add(inventory_page(page, auth))
        page.update()

    def go_logout(e):
        try:
            from admin import build_login_view
            auth.clear()
            page.controls.clear()
            page.add(build_login_view(page, auth))
            page.update()
        except Exception:
            auth.clear()
            page.controls.clear()
            page.add(ft.Container(expand=True, alignment=ft.Alignment.CENTER, content=ft.Text("Logged out", size=18, color=WHITE)))
            page.update()

    def go_analytics(e):
        from pages.analytics import analytics_page
        page.controls.clear()
        page.add(analytics_page(page, auth))

    def go_history(e):
        from pages.history import history_page
        page.controls.clear()
        page.add(history_page(page, auth))

    def open_optimization(e):
        from pages.optimization import ai_optimization_page
        page.controls.clear()
        page.add(ai_optimization_page(page, auth))

    header = ft.Container(
        content=ft.Row([
            ft.Text("DASHBOARD", color=TEXT_WHITE, size=22, weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.Text("U-Fuel", color=TEXT_WHITE, size=18, weight=ft.FontWeight.BOLD),
                ft.Container(width=42, height=42, bgcolor=TEXT_WHITE, border_radius=20, clip_behavior=ft.ClipBehavior.HARD_EDGE, content=ft.Image(src="u-fuel_logo.jpg", fit=ft.BoxFit.CONTAIN, border_radius=20)),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=DARK_RED, padding=ft.Padding.symmetric(vertical=18, horizontal=24),
    )

    stats_row = ft.Row([
        stat_card(icon=ft.Icons.LOCAL_GAS_STATION, title="Current Fuel Stock", value="5,000L / 10,000L", period_label="pump 1", show_progress=True, progress_value=0.5, dropdowns=["regular", "pump 1"]),
        stat_card(icon=ft.Icons.TRENDING_UP, title="Daily Sales", value="₱ 10,000", period_label="daily"),
        stat_card(icon=ft.Icons.ATTACH_MONEY, title="Daily Net Profit", value="₱ 5,000", period_label="daily"),
    ], spacing=16)

    quick_actions_col = ft.Column([
        ft.Text("Quick Actions", color=TEXT_DARK, size=14, weight=ft.FontWeight.BOLD),
        ft.Container(height=4),
        action_button("View Analytics", on_click=go_analytics),
        action_button("View Inventory", on_click=go_inventory),
        action_button("Transaction History", on_click=go_history),
        action_button("Inventory Optimization"),
    ], spacing=12, tight=True)

    quick_actions = ft.Container(content=quick_actions_col, bgcolor=LIGHT_CARD, border_radius=10, padding=18, expand=True)

    low_stock_col = ft.Column([
        ft.Text("Low Stock Alert", color=TEXT_DARK, size=14, weight=ft.FontWeight.BOLD),
        ft.Container(height=8),
        ft.Container(
            content=ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color=DARK_GREEN, size=16), ft.Text("Checking stock...", color=TEXT_DARK, size=12, italic=True)], spacing=8),
            bgcolor=LIGHT_CARD, border_radius=6, padding=ft.Padding.symmetric(vertical=10, horizontal=14),
        ),
    ], spacing=0, tight=True)

    def render_low_stock(data: dict):
        items = data.get("items", [])
        total = data.get("total_count", 0)
        if total == 0:
            low_stock_col.controls = [
                ft.Text("Low Stock Alert", color=TEXT_DARK, size=14, weight=ft.FontWeight.BOLD),
                ft.Container(height=8),
                ft.Container(
                    content=ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color=DARK_GREEN, size=16), ft.Text("There is no low stock at the moment.", color=DARK_GREEN, size=12, italic=True)], spacing=8),
                    bgcolor=GREEN_ALERT, border_radius=6, padding=ft.Padding.symmetric(vertical=10, horizontal=14),
                ),
            ]
        else:
            alert_widgets = []
            for it in items[:5]:
                name = it.get("product_name","")
                ptype = it.get("product_type","")
                stock = it.get("current_stock",0)
                thresh = it.get("threshold",0)
                urgency = it.get("urgency","warning")
                unit = it.get("unit","")
                if urgency == "critical":
                    bg, ic, ic_color = LIGHT_RED, ft.Icons.ERROR, "#C62828"
                else:
                    bg, ic, ic_color = LIGHT_ORANGE, ft.Icons.WARNING, "#EF6C00"
                alert_widgets.append(
                    ft.Container(
                        bgcolor=bg, border_radius=6, padding=ft.Padding.symmetric(vertical=10, horizontal=14),
                        content=ft.Row([
                            ft.Icon(ic, color=ic_color, size=16),
                            ft.Column([
                                ft.Text(f"{name} ({ptype})", size=11, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                                ft.Text(f"{stock:.0f}{unit} left • Threshold {thresh:.0f}{unit} • {urgency.upper()}", size=10, color=TEXT_DARK)
                            ], spacing=2, expand=True)
                        ], spacing=8)
                    )
                )
            if total > 5:
                alert_widgets.append(ft.Text(f"+{total-5} more...", size=10, color=DARK_RED, italic=True))

            low_stock_col.controls = [
                ft.Row([ft.Text("Low Stock Alert", color=TEXT_DARK, size=14, weight=ft.FontWeight.BOLD), ft.Container(content=ft.Text(f"{total}", size=11, color=WHITE, weight=ft.FontWeight.BOLD), bgcolor=DARK_RED, border_radius=10, padding=ft.Padding.symmetric(horizontal=8, vertical=2))], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=8),
                *alert_widgets,
                ft.Container(height=6),
                ft.Container(content=ft.Text("View Inventory →", size=11, color=DARK_RED, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER), border=ft.Border.all(1, DARK_RED), border_radius=6, padding=8, ink=True, on_click=go_inventory)
            ]
        try: page.update()
        except: pass

    def load_low_stock():
        def bg():
            data = get_low_stock(auth, include_warning=True)
            render_low_stock(data)
        threading.Thread(target=bg, daemon=True).start()

    low_stock = ft.Container(content=low_stock_col, bgcolor=LIGHT_CARD, border_radius=10, padding=18, expand=True)

    middle_row = ft.Row([quick_actions, low_stock], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START)

    body = ft.Container(
        bgcolor=BODY_BG, expand=True, padding=ft.Padding.only(left=20, right=20, top=20, bottom=24),
        content=ft.Column(controls=[stats_row, middle_row], spacing=16, expand=True, scroll=ft.ScrollMode.ADAPTIVE),
    )

    footer = ft.Container(
        content=ft.Row([
            ft.Container(content=ft.Row([ft.Icon(ft.Icons.LOGOUT, color=TEXT_WHITE, size=16), ft.Text("LOGOUT", color=TEXT_WHITE, size=13, weight=ft.FontWeight.BOLD)], spacing=6), bgcolor="#6B6B6B", border_radius=6, padding=ft.Padding.symmetric(vertical=8, horizontal=14), ink=True, on_click=go_logout),
            ft.Text("GAStoKITA", color=TEXT_WHITE, size=12, weight=ft.FontWeight.W_500),
            ft.Row([ft.Icon(ft.Icons.PERSON_OUTLINE, color=TEXT_WHITE, size=18), ft.Text(auth.get("name","ADMIN"), color=TEXT_WHITE, size=13, weight=ft.FontWeight.BOLD)], spacing=4),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=DARK_RED, padding=ft.Padding.symmetric(vertical=14, horizontal=24),
    )

    load_low_stock()

    return ft.Column([header, body, footer], spacing=0, expand=True)