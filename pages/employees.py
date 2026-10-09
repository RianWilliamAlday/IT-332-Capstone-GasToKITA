import flet as ft
import time
from datetime import datetime
from pages.api_client import (get_cashiers, get_attendants, create_attendant,
        update_attendant, delete_attendant,
    )

RED = "#A61E22"
DARK_RED = "#8B0000"
LIGHT_GRAY = "#E9E9E9"
CARD_GRAY = "#D9D9D9"
WHITE = "#FFFFFF"
TEXT_DARK = "#1A1A1A"
TEXT_WHITE = "#FFFFFF"
BODY_BG = "#F5F5F5"
GREEN_SUCCESS = "#2E7D32"


def card(title, handler):
    is_selected = auth_context.get("selected_attendant") == title
    return ft.Container(
        width=210, height=210, bgcolor=RED,
        border_radius=20, padding=12,
        border=ft.Border.all(3, "white") if is_selected else None,
        on_click=handler, ink=True,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    expand=True, bgcolor="white", border_radius=14,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(ft.Icons.PERSON, size=65, color=RED)
                ),
                ft.Container(height=6),
                ft.Text(
                    title, size=16, weight=ft.FontWeight.BOLD, 
                    color="white", text_align=ft.TextAlign.CENTER,
                    overflow=ft.TextOverflow.ELLIPSIS
                ),
            ]
        )
    )

auth_context = {"name": "ADMIN", "role": "admin"}

def employees_page(page: ft.Page, auth: dict):
    global auth_context
    auth_context = auth

    page.title = "Manage Employees"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = BODY_BG
    page.padding = 0
    page.window.maximized = True

    cashiers_cache = []
    attendants_cache = []
    selected_emp_ref = {"data": None, "role_type": None}

    detail_name = ft.Text("", size=18, weight=ft.FontWeight.BOLD, color=TEXT_DARK)
    detail_role = ft.Text("", size=12, color="#666666")
    detail_id = ft.Text("", size=13, color=TEXT_DARK, weight=ft.FontWeight.W_600)
    detail_contact_label = ft.Text("Contact:", size=11, color="#888888")
    detail_contact = ft.Text("", size=13, color=TEXT_DARK)
    detail_sales = ft.Text("0 txns", size=15, weight=ft.FontWeight.BOLD, color=GREEN_SUCCESS)

    profile_actions_row = ft.Row(
        controls=[
            ft.OutlinedButton(
                content=ft.Row([ft.Icon(ft.Icons.EDIT, size=14, color=DARK_RED), ft.Text("Edit", size=12, color=DARK_RED)]),
                on_click=lambda _: open_edit_dialog()
            ),
            ft.FilledButton(
                content=ft.Row([ft.Icon(ft.Icons.DELETE_OUTLINE, size=14, color=WHITE), ft.Text("Delete", size=12, color=WHITE)]),
                bgcolor=DARK_RED,
                on_click=lambda _: open_delete_dialog()
            )
        ],
        spacing=8,
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        visible=True
    )
    
    def show_snack(msg, color=DARK_RED):
        snack = ft.SnackBar(
            content=ft.Text(msg, color="white"),
            bgcolor=color,
            open=True,
        )
        page.overlay.append(snack)
        page.update()

    cashiers_row = ft.Row(spacing=16, wrap=True, alignment=ft.MainAxisAlignment.START)
    attendants_row = ft.Row(spacing=16, wrap=True, alignment=ft.MainAxisAlignment.START)

    details_panel = ft.Container(
        width=290,
        bgcolor=WHITE,
        border_radius=15,
        padding=20,
        visible=False,
        shadow=ft.BoxShadow(blur_radius=4, color="#00000015", offset=ft.Offset(0, 2)),
        content=ft.Column(
            controls=[
                ft.Row([
                    ft.Text("Employee Profile", size=14, weight=ft.FontWeight.BOLD, color="#666666"),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE, icon_size=18, icon_color="#888888",
                        on_click=lambda _: close_profile_panel()
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(color="#E0E0E0"),
                detail_name,
                detail_role,
                ft.Container(height=8),
                ft.Text("Employee ID:", size=11, color="#888888"),
                detail_id,
                detail_contact_label,
                detail_contact,
                ft.Container(height=8),
                ft.Text("Total Sales Recorded:", size=11, color="#888888"),
                detail_sales,
                ft.Container(height=16),
                profile_actions_row
            ],
            spacing=4,
            tight=True
        )
    )

    def close_profile_panel():
        auth_context["selected_attendant"] = None
        selected_emp_ref["data"] = None
        selected_emp_ref["role_type"] = None
        details_panel.visible = False
        render_grid()

    def select_employee(emp_name, role_type):
        if auth_context.get("selected_attendant") == emp_name:
            close_profile_panel()
            return

        auth_context["selected_attendant"] = emp_name
        
        emp = None
        if role_type == "cashier":
            emp = next((e for e in cashiers_cache if e["name"] == emp_name), None)
        else:
            emp = next((e for e in attendants_cache if e["name"] == emp_name), None)

        selected_emp_ref["data"] = emp
        selected_emp_ref["role_type"] = role_type

        if emp:
            detail_name.value = emp["name"]
            detail_role.value = f"Role: {role_type.upper()}"
            detail_id.value = emp.get("employee_id") or "N/A"
            tx_count = emp.get("total_sales_recorded", 0)
            detail_sales.value = f"{tx_count} Recorded Transactions"

            if role_type == "cashier":
                detail_contact_label.visible = False
                detail_contact.visible = False
                profile_actions_row.visible = False
            else:
                detail_contact_label.visible = True
                detail_contact.visible = True
                detail_contact.value = emp.get("contact") or "N/A"
                profile_actions_row.visible = True

            details_panel.visible = True

        render_grid()

    def render_grid():
        if not cashiers_cache:
            cashiers_row.controls = [ft.Text("No cashier accounts found.", size=12, color="#888888", italic=True)]
        else:
            cashiers_row.controls = [
                card(c["name"], lambda e, n=c["name"]: select_employee(n, "cashier"))
                for c in cashiers_cache
            ]

        if not attendants_cache:
            attendants_row.controls = [ft.Text("No pump attendants registered.", size=12, color="#888888", italic=True)]
        else:
            attendants_row.controls = [
                card(a["name"], lambda e, n=a["name"]: select_employee(n, "attendant"))
                for a in attendants_cache
            ]

        try:
            page.update()
        except Exception:
            pass

    def load_backend_data():
        def bg():
            time.sleep(0.05)
            try:
                all_cashiers = get_cashiers(auth)
                all_attendants = get_attendants(auth, include_inactive=False)

                nonlocal cashiers_cache, attendants_cache
                cashiers_cache = [u for u in all_cashiers if u.get("role", "").lower() != "admin"]
                attendants_cache = all_attendants

                render_grid()
            except Exception as ex:
                show_snack(f"Error loading staff data: {ex}", DARK_RED)

        page.run_thread(bg)

    def open_add_dialog():
        name_field = ft.TextField(label="Full Name", width=300, autofocus=True)
        emp_id_field = ft.TextField(label="Employee ID", width=300, hint_text="e.g. EMP-005")
        contact_field = ft.TextField(label="Contact Number", width=300)
        err_txt = ft.Text("", size=11, color=DARK_RED)

        def save_new(e):
            clean_name = name_field.value.strip() if name_field.value else ""
            if not clean_name:
                err_txt.value = "Name is required."
                err_txt.update()
                return

            def bg():
                try:
                    create_attendant(
                        auth,
                        name=clean_name,
                        employee_id=emp_id_field.value or None,
                        contact=contact_field.value or None,
                    )
                    page.pop_dialog()
                    show_snack(f"Added pump attendant: {clean_name}", GREEN_SUCCESS)
                    load_backend_data()
                except Exception as ex:
                    err_txt.value = str(ex)
                    err_txt.update()

            page.run_thread(bg)

        dlg = ft.AlertDialog(
            title=ft.Text("Add Pump Attendant", weight=ft.FontWeight.BOLD),
            content=ft.Column(tight=True, spacing=10, controls=[name_field, emp_id_field, contact_field, err_txt]),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: page.pop_dialog()),
                ft.FilledButton("Save", bgcolor=DARK_RED, color=WHITE, on_click=save_new)
            ]
        )
        page.show_dialog(dlg)

    def open_edit_dialog():
        emp = selected_emp_ref["data"]
        role_type = selected_emp_ref["role_type"]
        if not emp or role_type == "cashier": return

        if role_type == "cashier":
            show_snack("Cashier user credentials can be managed in User Settings.", DARK_RED)
            return

        name_field = ft.TextField(label="Full Name", width=300, value=emp["name"])
        emp_id_field = ft.TextField(label="Employee ID", width=300, value=emp.get("employee_id", ""))
        contact_field = ft.TextField(label="Contact Number", width=300, value=emp.get("contact", ""))
        err_txt = ft.Text("", size=11, color=DARK_RED)

        def save_edit(e):
            clean_name = name_field.value.strip() if name_field.value else ""
            if not clean_name:
                err_txt.value = "Name is required."
                err_txt.update()
                return

            def bg():
                try:
                    update_attendant(
                        auth,
                        attendant_id=emp["id"],
                        name=clean_name,
                        employee_id=emp_id_field.value or None,
                        contact=contact_field.value or None,
                    )
                    page.pop_dialog()
                    close_profile_panel()
                    show_snack("Attendant details updated.", GREEN_SUCCESS)
                    load_backend_data()
                except Exception as ex:
                    err_txt.value = str(ex)
                    err_txt.update()

            page.run_thread(bg)

        dlg = ft.AlertDialog(
            title=ft.Text(f"Edit {emp['name']}", weight=ft.FontWeight.BOLD),
            content=ft.Column(tight=True, spacing=10, controls=[name_field, emp_id_field, contact_field, err_txt]),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: page.pop_dialog()),
                ft.FilledButton("Save Changes", bgcolor=DARK_RED, color=WHITE, on_click=save_edit)
            ]
        )
        page.show_dialog(dlg)

    def open_delete_dialog():
        emp = selected_emp_ref["data"]
        role_type = selected_emp_ref["role_type"]
        if not emp or role_type == "cashier": return

        if role_type == "cashier":
            show_snack("Cashier user accounts cannot be deleted directly from this view.", DARK_RED)
            return

        def confirm_delete(e):
            def bg():
                try:
                    try:
                        delete_attendant(auth, attendant_id=emp["id"], force=False)
                    except Exception:
                        delete_attendant(auth, attendant_id=emp["id"], force=True)
                    
                    page.pop_dialog()
                    close_profile_panel()
                    show_snack(f"Removed attendant {emp['name']}.", DARK_RED)
                    load_backend_data()
                except Exception as ex:
                    show_snack(str(ex), DARK_RED)
            page.update
            page.run_thread(bg)

        dlg = ft.AlertDialog(
            title=ft.Text("Confirm Deletion"),
            content=ft.Text(f"Are you sure you want to remove attendant {emp['name']}?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: page.pop_dialog()),
                ft.FilledButton("Delete", bgcolor=DARK_RED, color=WHITE, on_click=confirm_delete)
            ]
        )
        page.show_dialog(dlg)

    def go_dashboard(e):
        from pages.admin_dashboard import dashboard_page
        page.controls.clear()
        page.add(dashboard_page(page, auth))
        page.update()

    def go_logout(e):
        auth.clear()
        page.controls.clear()
        from admin import build_login_view
        page.add(build_login_view(page, auth))
        page.update()

    add_btn = ft.Button(
        content=ft.Row([
            ft.Icon(ft.Icons.ADD, size=16, color=WHITE),
            ft.Text("ADD ATTENDANT", color=WHITE, size=12, weight=ft.FontWeight.BOLD),
        ], spacing=6, tight=True),
        bgcolor=DARK_RED, height=40,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
        on_click=lambda _: open_add_dialog()
    )

    header = ft.Container(
        content=ft.Row([
            ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=WHITE, on_click=go_dashboard),
            ft.Text("Employees", color=WHITE, size=22, weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.Text("U-Fuel", color=WHITE, size=18, weight=ft.FontWeight.BOLD),
                ft.Container(width=42, height=42, bgcolor=WHITE, border_radius=20, clip_behavior=ft.ClipBehavior.HARD_EDGE, content=ft.Image(src="u-fuel_logo.jpg", fit=ft.BoxFit.CONTAIN, border_radius=20)),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=DARK_RED, padding=ft.Padding.symmetric(vertical=18, horizontal=24),
    )
    
    footer = ft.Container(
        content=ft.Row([
            ft.Container(content=ft.Row([ft.Icon(ft.Icons.LOGOUT, color=WHITE, size=16), ft.Text("LOGOUT", color=WHITE, size=13, weight=ft.FontWeight.BOLD)], spacing=6), bgcolor="#6B6B6B", border_radius=6, padding=ft.Padding.symmetric(vertical=8, horizontal=14), ink=True, on_click=go_logout),
            ft.Text("GAStoKITA", color=WHITE, size=12),
            ft.Row([ft.Icon(ft.Icons.PERSON_OUTLINE, color=WHITE, size=18), ft.Text(auth.get("name","ADMIN"), color=WHITE, size=13, weight=ft.FontWeight.BOLD)], spacing=4),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        bgcolor=DARK_RED, padding=ft.Padding.symmetric(vertical=14, horizontal=24),
    )

    accounts_column = ft.Column(
        controls=[
            ft.Row([
                ft.Icon(ft.Icons.POINT_OF_SALE, size=20, color=DARK_RED),
                ft.Text("CASHIERS", size=15, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
            ], spacing=8),
            ft.Container(height=4),
            cashiers_row,
            ft.Container(height=16),
            ft.Divider(color="#D0D0D0", height=1),
            ft.Container(height=16),
            ft.Row([
                ft.Icon(ft.Icons.LOCAL_GAS_STATION, size=20, color=DARK_RED),
                ft.Text("PUMP ATTENDANTS", size=15, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
            ], spacing=8),
            ft.Container(height=4),
            attendants_row,
        ],
        spacing=0,
        expand=True,
        scroll=ft.ScrollMode.ADAPTIVE
    )

    body = ft.Container(
        expand=True, padding=24,
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Active Staff", size=16, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                        add_btn
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Container(height=16),
                ft.Row(
                    controls=[
                        accounts_column,
                        details_panel
                    ],
                    spacing=24,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    expand=True
                )
            ],
            spacing=0,
            expand=True
        )
    )

    load_backend_data()

    return ft.Column(controls=[header, body, footer], spacing=0, expand=True)