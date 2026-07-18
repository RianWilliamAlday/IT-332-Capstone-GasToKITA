import flet as ft
import time, threading, traceback

from pages.api_client import (
    get_fuels, get_oils, restock_fuel, update_fuel_price,
    dipstick_convert, sync_dipstick, create_oil_product, restock_oil,
    update_oil
)

DARK_RED = "#8B0000"
LIGHT_BG = "#F0F0F0"
WHITE = "#FFFFFF"
BLACK = "#000000"
GREEN = "#15803D"
ORANGE = "#D97706"

def open_dialog_compat(page: ft.Page, dialog: ft.AlertDialog):
    try:
        page.open(dialog)
    except:
        if hasattr(page, "open_dialog"):
            page.open_dialog(dialog)
        elif hasattr(page, "show_dialog"):
            page.show_dialog(dialog)
        else:
            page.dialog = dialog
            dialog.open = True
            page.update()

def close_dialog_compat(page: ft.Page, dialog=None):
    try:
        if dialog:
            dialog.open = False
    except: pass
    try:
        if dialog:
            page.close(dialog)
    except: pass
    try:
        if hasattr(page, "close_dialog"):
            page.close_dialog()
    except: pass
    try:
        if hasattr(page, "pop_dialog"):
            page.pop_dialog()
    except: pass
    try:
        page.dialog = None
        page.update()
    except: pass

def inventory_page(page: ft.Page, auth: dict):
    page.title = "U-FUEL - Inventory Management"
    page.bgcolor = LIGHT_BG
    page.padding = 0

    selected = {"tab": "fuel"}
    content_area = ft.Column([], spacing=16, scroll=ft.ScrollMode.ADAPTIVE, expand=True)
    loading_ring = ft.Container(expand=True, alignment=ft.Alignment.CENTER, content=ft.Column(controls=[ft.ProgressRing(color=DARK_RED), ft.Text("Loading...", color=BLACK)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER))

    def show_snack(msg, color=DARK_RED):
        try:
            page.show_snack_bar(ft.SnackBar(content=ft.Text(msg, color="white"), bgcolor=color))
        except:
            page.snack_bar = ft.SnackBar(content=ft.Text(msg, color="white"), bgcolor=color)
            page.snack_bar.open = True
            page.update()
        print(f"[SNACK] {msg}")

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
            page.add(ft.Container(expand=True, alignment=ft.Alignment.CENTER, content=ft.Text("Logged out. Restart app.", size=18)))
            page.update()

    def status_badge(stock, threshold):
        if stock <= threshold * 0.5: bg, txt = "#DC2626", "Critical"
        elif stock <= threshold: bg, txt = ORANGE, "Low Stock"
        else: bg, txt = GREEN, "In Stock"
        return ft.Container(content=ft.Text(txt, size=11, color=WHITE, weight=ft.FontWeight.BOLD), bgcolor=bg, border_radius=20, padding=ft.Padding.symmetric(horizontal=12, vertical=4))

    def load_fuels():
        cached_fuels = auth.get("fuels_cache")
        if cached_fuels and selected["tab"] == "fuel":
            content_area.controls = [fuel_card(f) for f in cached_fuels]
            try: page.update()
            except: pass
        elif not cached_fuels and selected["tab"] == "fuel":
            content_area.controls = [loading_ring]
            try: page.update()
            except: pass

        def bg():
            time.sleep(0.1)
            try:
                fuels = get_fuels(auth)
                auth["fuels_cache"] = fuels  
                if selected["tab"] == "fuel":
                    content_area.controls = [fuel_card(f) for f in fuels]
                    page.update()
            except Exception as ex:
                print("load_fuels error:", traceback.format_exc())
                if not auth.get("fuels_cache") and selected["tab"] == "fuel":
                    content_area.controls = [ft.Text(f"Failed to load fuels: {ex}", color=DARK_RED)]
                    page.update()
        page.run_thread(bg)

    def load_oils():
        cached_oils = auth.get("oils_cache")
        if cached_oils and selected["tab"] == "oil":
            content_area.controls = [oil_table(cached_oils)]
            try: page.update()
            except: pass
        elif not cached_oils and selected["tab"] == "oil":
            content_area.controls = [loading_ring]
            try: page.update()
            except: pass

        def bg():
            time.sleep(0.1)
            try:
                oils = get_oils(auth)
                auth["oils_cache"] = oils  
                if selected["tab"] == "oil":
                    content_area.controls = [oil_table(oils)]
                    page.update()
            except Exception as ex:
                print("load_oils error:", traceback.format_exc())
                if not auth.get("oils_cache") and selected["tab"] == "oil":
                    content_area.controls = [ft.Text(f"Failed to load oils: {ex}", color=DARK_RED)]
                    page.update()
        page.run_thread(bg)

    def fuel_card(fuel: dict):
        fid, name, capacity, current = fuel["id"], fuel["name"], fuel["tank_capacity"], fuel["actual_liters"]
        percent, dipstick, threshold, price = fuel["display_percentage"], fuel.get("display_cm", 0), fuel["threshold"], fuel["price"]
        progress = min(1.0, percent / 100.0)

        def open_restock(e):
            remaining = max(0, round(capacity - current, 2))
            liters_field = ft.TextField(label="Liters to add", width=200, keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)
            cost_field = ft.TextField(label="Total cost", width=200, value="0", keyboard_type=ft.KeyboardType.NUMBER)
            err = ft.Text("", size=11, color=DARK_RED)
            
            def fill_full(ev):
                if remaining <= 0:
                    err.value = "Tank is already full"; err.update(); return
                liters_field.value = str(int(remaining)) if remaining == int(remaining) else f"{remaining:.2f}"
                liters_field.update()
                err.value = ""; err.update()

            def do_restock(ev):
                try:
                    liters = float(liters_field.value or 0)
                    if liters <= 0: 
                        err.value="Enter liters"; err.update(); return
                    if liters > remaining and remaining > 0:
                        err.value=f"Exceeds capacity. Max is {remaining:,.0f}L"; err.update(); return
                    close_dialog_compat(page)
                    def bg():
                        time.sleep(0.1)
                        try:
                            restock_fuel(auth, fid, liters, float(cost_field.value or 0))
                            show_snack(f"{name} restocked +{liters}L", GREEN)
                            auth.pop("fuels_cache", None)  
                            load_fuels()
                        except Exception as ex: show_snack(str(ex), DARK_RED)
                    page.run_thread(bg)
                except Exception as ex: 
                    err.value=str(ex); err.update()

            dialog = ft.AlertDialog(
                title=ft.Text(f"Restock {name}"),
                content=ft.Column(tight=True, spacing=10, controls=[
                    ft.Text(f"Current: {current:,.0f}L / {capacity:,}L", size=12),
                    ft.Text(f"Space left: {remaining:,.0f}L to full", size=12, weight=ft.FontWeight.BOLD, color=DARK_RED) if remaining > 0 else ft.Text("Tank is already at full capacity!", size=12, weight=ft.FontWeight.BOLD, color=GREEN),
                    liters_field,
                    ft.OutlinedButton(content=f"FILL TO FULL - {remaining:,.0f}L", icon=ft.Icons.WATER_DROP, on_click=fill_full) if remaining > 0 else ft.Container(),
                    cost_field, 
                    err
                ]),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e: close_dialog_compat(page)), 
                    ft.FilledButton("Restock", bgcolor=DARK_RED, color="white", on_click=do_restock)
                ]
            )
            open_dialog_compat(page, dialog)

        def open_price(e):
            pf = ft.TextField(label="New price", width=200, value=str(price), keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)
            err = ft.Text("", size=11, color=DARK_RED)
            def do_save(ev):
                try:
                    np = float(pf.value)
                    close_dialog_compat(page)
                    def bg():
                        time.sleep(0.1)
                        try:
                            update_fuel_price(auth, fid, np)
                            show_snack(f"{name} → ₱{np:.2f}", GREEN)
                            auth.pop("fuels_cache", None)
                            load_fuels()
                        except Exception as ex: show_snack(str(ex), DARK_RED)
                    page.run_thread(bg)
                except Exception as ex: err.value=str(ex); err.update()
            dialog = ft.AlertDialog(title=ft.Text(f"Update {name} Price"), content=ft.Column(tight=True, controls=[pf, err]), actions=[ft.TextButton("Cancel", on_click=lambda e: close_dialog_compat(page)), ft.FilledButton("Save", bgcolor=DARK_RED, color="white", on_click=do_save)])
            open_dialog_compat(page, dialog)

        return ft.Container(
            bgcolor=WHITE, border_radius=10, padding=20, shadow=ft.BoxShadow(blur_radius=6, color="#00000012", offset=ft.Offset(0, 2)),
            content=ft.Column([
                ft.Row([ft.Column([ft.Text(name, size=16, weight=ft.FontWeight.BOLD, color=BLACK), ft.Text(f"Capacity: {capacity:,} L", size=12, color=BLACK)], spacing=2),
                        ft.Container(content=ft.Text("RESTOCK", size=11, color=DARK_RED, weight=ft.FontWeight.BOLD), border=ft.Border.all(1, DARK_RED), border_radius=6, padding=ft.Padding.symmetric(horizontal=12, vertical=6), ink=True, on_click=open_restock)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=12),
                ft.Row([
                    ft.Container(expand=True, content=ft.Column([
                        ft.Row([ft.Text("Current Level", size=12, color=BLACK, weight=ft.FontWeight.W_600), ft.Text(f"{current:,.0f} L ({percent:.0f}%)", size=12, color=BLACK, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.ProgressBar(value=progress, color=DARK_RED, bgcolor="#E5E7EB", bar_height=6, border_radius=4),
                        ft.Row([ft.Container(expand=True, bgcolor="#F9FAFB", border_radius=6, padding=12, content=ft.Column([ft.Text("Dipstick", size=11, color=BLACK, weight=ft.FontWeight.W_600), ft.Text(f"{dipstick} cm", size=16, weight=ft.FontWeight.BOLD, color=BLACK)], spacing=4)),
                                ft.Container(expand=True, bgcolor="#F9FAFB", border_radius=6, padding=12, content=ft.Column([ft.Text("Threshold", size=11, color=BLACK, weight=ft.FontWeight.W_600), ft.Text(f"{threshold:,.0f} L", size=16, weight=ft.FontWeight.BOLD, color=BLACK)], spacing=4))], spacing=12)
                    ], spacing=8)),
                    ft.Container(width=200, bgcolor="#FFFBF5", border=ft.Border.all(1, "#F3E8D3"), border_radius=8, padding=16, ink=True, on_click=open_price,
                        content=ft.Column([ft.Row([ft.Icon(ft.Icons.LOCAL_OFFER_OUTLINED, size=16, color=DARK_RED), ft.Text("Current Price", size=11, weight=ft.FontWeight.BOLD, color=BLACK)], spacing=6),
                                           ft.Row([ft.Text(f"₱{price:.2f}", size=24, weight=ft.FontWeight.BOLD, color=DARK_RED), ft.Text("/ L", size=12, color=BLACK)], spacing=4),
                                           ft.Text("Tap to edit", size=10, color=BLACK, italic=True)], spacing=2))
                ], spacing=20)
            ], spacing=0)
        )
    
    def open_global_restock_oil_dialog(e):
        oils = auth.get("oils_cache", [])
        if not oils:
            show_snack("Inventory database loading. Please wait.", DARK_RED)
            return

        oil_options = [
            ft.dropdown.Option(key=str(o["id"]), text=f"{o.get('brand','')} {o.get('name','')}") 
            for o in oils
        ]
        
        oil_dropdown = ft.Dropdown(
            label="Select Oil Product", 
            options=oil_options, 
            width=200, 
            value=oil_options[0].key if oil_options else None
        )
        qf = ft.TextField(label="Qty to add", width=200, keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)
        cf = ft.TextField(label="Total cost", width=200, value="0", keyboard_type=ft.KeyboardType.NUMBER)
        err = ft.Text("", size=11, color=DARK_RED)

        def do_r(ev):
            try:
                if not oil_dropdown.value:
                    err.value = "Select an oil product"; err.update(); return
                q = int(float(qf.value or 0))
                if q <= 0: err.value = "Enter qty"; err.update(); return
                
                selected_id = int(oil_dropdown.value)
                matched_oil = next((x for x in oils if x["id"] == selected_id), {})
                
                close_dialog_compat(page)
                def bg():
                    time.sleep(0.1)
                    try:
                        restock_oil(auth, selected_id, q, float(cf.value or 0))
                        show_snack(f"Restocked {matched_oil.get('brand','')} {matched_oil.get('name','')}", GREEN)
                        auth.pop("oils_cache", None)
                        load_oils()
                    except Exception as ex: show_snack(str(ex), DARK_RED)
                page.run_thread(bg)
            except Exception as ex: err.value = str(ex); err.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Restock Oil Product"), 
            content=ft.Column(tight=True, controls=[oil_dropdown, qf, cf, err]), 
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: close_dialog_compat(page)), 
                ft.FilledButton("Restock", bgcolor=DARK_RED, color="white", on_click=do_r)
            ]
        )
        open_dialog_compat(page, dialog)

    def open_edit_oil_dialog(o: dict):
        oil_id = o.get("id")
        bf = ft.TextField(label="Brand", width=200, value=o.get('brand',''))
        nf = ft.TextField(label="Oil Name", width=200, value=o.get('name',''))
        vf = ft.TextField(label="Variant", width=200, value=o.get('variant',''))
        sf = ft.TextField(label="Stock", width=200, value=str(o.get('stock',0)), keyboard_type=ft.KeyboardType.NUMBER)
        pf = ft.TextField(label="Price", width=200, value=str(o.get('price',0)), keyboard_type=ft.KeyboardType.NUMBER)
        tf = ft.TextField(label="Reorder Point", width=200, value=str(o.get('low_stock_threshold',5)), keyboard_type=ft.KeyboardType.NUMBER)
        err = ft.Text("", size=11, color=DARK_RED)
        
        def do_save(ev):
            try:
                if not bf.value or not nf.value: 
                    err.value = "Brand and name required"
                    err.update()
                    return

                payload = {
                    "brand": bf.value,
                    "name": nf.value,
                    "variant": vf.value,
                    "stock": int(float(sf.value or 0)),
                    "price": float(pf.value or 0),
                    "low_stock_threshold": int(float(tf.value or 5))
                }
                
                close_dialog_compat(page)
                
                def bg():
                    time.sleep(0.1)
                    try:
                        update_oil(auth, oil_id, payload)
                        show_snack(f"Updated product details for {bf.value} {nf.value}", GREEN)
                        auth.pop("oils_cache", None)
                        load_oils()                  
                    except Exception as ex: 
                        show_snack(f"Update failed: {str(ex)}", DARK_RED)
                page.run_thread(bg)
            except Exception as ex: 
                err.value = str(ex)
                err.update()
            
        dialog = ft.AlertDialog(
            title=ft.Text(f"Edit Product Settings"), 
            content=ft.Column(tight=True, controls=[bf, nf, vf, sf, pf, tf, err]), 
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: close_dialog_compat(page)), 
                ft.FilledButton("Save Changes", bgcolor=DARK_RED, color="white", on_click=do_save)
            ]
        )
        open_dialog_compat(page, dialog)

    def oil_table(oils: list):
        def h_cell(t,w): return ft.Container(width=w, padding=10, content=ft.Text(t, size=12, weight=ft.FontWeight.BOLD, color=BLACK))
        def d_cell(t,w): return ft.Container(width=w, padding=10, content=ft.Text(str(t), size=13, color=BLACK))
        header_row = ft.Container(bgcolor="#F9FAFB", border=ft.Border.only(bottom=ft.BorderSide(1, "#E5E7EB")), content=ft.Row([h_cell("Oil Name",200), h_cell("Brand",100), h_cell("Stock",110), h_cell("Reorder",110), h_cell("Price",80), h_cell("Status",120)], spacing=0))
        rows=[]
        for i, oil in enumerate(oils):
            def make_handler(o):
                def handler(e):
                    open_edit_oil_dialog(o)
                return handler
            rows.append(ft.Container(bgcolor="#FAFAFA" if i%2==0 else WHITE, border=ft.Border.only(bottom=ft.BorderSide(1, "#F3F4F6")), ink=True, on_click=make_handler(oil),
                content=ft.Row([d_cell(oil.get('name',''),200), d_cell(oil.get('brand',''),100), d_cell(f"{oil.get('stock',0)} pcs",110), d_cell(f"{oil.get('low_stock_threshold',5)}",110), d_cell(f"₱{oil.get('price',0):.2f}",80), ft.Container(width=120, padding=10, content=status_badge(oil.get('stock',0), oil.get('low_stock_threshold',5)))], spacing=0)))
        return ft.Container(bgcolor=WHITE, border_radius=10, clip_behavior=ft.ClipBehavior.HARD_EDGE, shadow=ft.BoxShadow(blur_radius=6, color="#00000012", offset=ft.Offset(0,2)), content=ft.Column([header_row, *rows], spacing=0))

    def go_dashboard(e):
        from pages.admin_dashboard import dashboard_page
        page.controls.clear()
        page.add(dashboard_page(page, auth))
        page.update()
        
    def open_dipstick(e):
        cmf = ft.TextField(label="Dipstick cm", width=200, keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)
        drop = ft.Dropdown(label="Fuel Type", width=200, options=[ft.dropdown.Option("Regular"), ft.dropdown.Option("Premium"), ft.dropdown.Option("Diesel")], value="Regular")
        res = ft.Text("", size=12)
        err = ft.Text("", size=11, color=DARK_RED)
        def convert(ev):
            try:
                cm=int(float(cmf.value or 0))
                r=dipstick_convert(auth, cm, drop.value)
                res.value=f"{cm}cm = {r['liters']}L ({r['percentage']:.1f}%)"; res.update()
            except Exception as ex: err.value=str(ex); err.update()
        def sync(ev):
            try:
                cm=int(float(cmf.value or 0))
                fuels = auth.get("fuels_cache") or get_fuels(auth)
                f = next((x for x in fuels if x["name"]==drop.value), None)
                if not f: err.value="Fuel not found"; err.update(); return
                sync_dipstick(auth, f["id"], cm)
                show_snack(f"{drop.value} synced to {cm}cm", GREEN)
                close_dialog_compat(page)
                auth.pop("fuels_cache", None)
                load_fuels()
            except Exception as ex: err.value=str(ex); err.update()
        dialog = ft.AlertDialog(title=ft.Text("Dipstick Converter"), content=ft.Column(tight=True, controls=[drop, cmf, res, err]), actions=[ft.TextButton("Close", on_click=lambda e: close_dialog_compat(page)), ft.FilledButton("Convert", bgcolor=DARK_RED, color="white", on_click=convert), ft.FilledButton("Sync", bgcolor=GREEN, color="white", on_click=sync)])
        open_dialog_compat(page, dialog)

    def open_add_oil(e):
        bf, nf, vf = ft.TextField(label="Brand", width=200, autofocus=True), ft.TextField(label="Oil Name", width=200), ft.TextField(label="Variant", width=200)
        sf, pf, tf = ft.TextField(label="Stock", width=200, value="0", keyboard_type=ft.KeyboardType.NUMBER), ft.TextField(label="Price", width=200, value="0", keyboard_type=ft.KeyboardType.NUMBER), ft.TextField(label="Reorder Point", width=200, value="5", keyboard_type=ft.KeyboardType.NUMBER)
        err=ft.Text("", size=11, color=DARK_RED)
        def do_add(ev):
            try:
                if not bf.value or not nf.value: err.value="Brand and name required"; err.update(); return
                close_dialog_compat(page)
                def bg():
                    time.sleep(0.1)
                    try:
                        create_oil_product(auth, bf.value, nf.value, int(float(sf.value or 0)), float(pf.value or 0), vf.value, int(float(tf.value or 5)))
                        show_snack(f"Added {bf.value} {nf.value}", GREEN)
                        auth.pop("oils_cache", None)
                        load_oils()
                    except Exception as ex: show_snack(str(ex), DARK_RED)
                page.run_thread(bg)
            except Exception as ex: err.value=str(ex); err.update()
        dialog = ft.AlertDialog(title=ft.Text("Add Oil Product"), content=ft.Column(tight=True, controls=[bf, nf, vf, sf, pf, tf, err]), actions=[ft.TextButton("Cancel", on_click=lambda e: close_dialog_compat(page)), ft.FilledButton("Add", bgcolor=DARK_RED, color="white", on_click=do_add)])
        open_dialog_compat(page, dialog)

    dipstick_btn = ft.Button(content=ft.Row([ft.Icon(ft.Icons.STRAIGHTEN, size=16, color=WHITE), ft.Text("DIPSTICK CONVERTER", color=WHITE, size=12, weight=ft.FontWeight.BOLD)], spacing=6, tight=True), bgcolor=DARK_RED, on_click=open_dipstick)
    add_oil_btn = ft.Button(content=ft.Row([ft.Icon(ft.Icons.ADD, size=16, color=WHITE), ft.Text("ADD OIL", color=WHITE, size=12, weight=ft.FontWeight.BOLD)], spacing=6, tight=True), bgcolor=DARK_RED, on_click=open_add_oil, visible=False)
    
    restock_oil_btn = ft.Button(
        content=ft.Row([ft.Icon(ft.Icons.INVENTORY_2_OUTLINED, size=16, color=WHITE), ft.Text("RESTOCK OIL", color=WHITE, size=12, weight=ft.FontWeight.BOLD)], spacing=6, tight=True),
        bgcolor=DARK_RED, 
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=ft.Padding.symmetric(horizontal=16, vertical=10)), 
        visible=False,
        on_click=open_global_restock_oil_dialog
    )
    
    title_row = ft.Row(controls=[ft.Container(expand=True), dipstick_btn, add_oil_btn, restock_oil_btn], alignment=ft.MainAxisAlignment.END, spacing=10)

    tab_fuel = ft.Container(padding=ft.Padding.symmetric(vertical=10, horizontal=16), ink=True)
    tab_oil = ft.Container(padding=ft.Padding.symmetric(vertical=10, horizontal=16), ink=True)
    tabs_row = ft.Row([tab_fuel, tab_oil], spacing=12)

    def refresh_tabs(update_page=True):
        is_fuel = selected["tab"] == "fuel"
        dipstick_btn.visible = is_fuel
        add_oil_btn.visible = not is_fuel
        restock_oil_btn.visible = not is_fuel  
        
        tab_fuel.content = ft.Row([ft.Icon(ft.Icons.LOCAL_GAS_STATION, size=18, color=DARK_RED if is_fuel else BLACK), ft.Text("FUEL INVENTORY", size=12, weight=ft.FontWeight.BOLD, color=DARK_RED if is_fuel else BLACK)], spacing=6, alignment=ft.MainAxisAlignment.CENTER)
        tab_fuel.border = ft.Border.only(bottom=ft.BorderSide(2, DARK_RED if is_fuel else ft.Colors.TRANSPARENT))
        tab_oil.content = ft.Row([ft.Icon(ft.Icons.SHOPPING_CART, size=18, color=DARK_RED if not is_fuel else BLACK), ft.Text("OIL INVENTORY", size=12, weight=ft.FontWeight.BOLD, color=DARK_RED if not is_fuel else BLACK)], spacing=6, alignment=ft.MainAxisAlignment.CENTER)
        tab_oil.border = ft.Border.only(bottom=ft.BorderSide(2, DARK_RED if not is_fuel else ft.Colors.TRANSPARENT))

        if is_fuel:
            load_fuels()  
        else:
            load_oils()  
                
        if update_page:
            try: page.update()
            except: pass

    tab_fuel.on_click = lambda e: (selected.update(tab="fuel"), refresh_tabs(update_page=True))
    tab_oil.on_click = lambda e: (selected.update(tab="oil"), refresh_tabs(update_page=True))

    refresh_tabs(update_page=False)

    header = ft.Container(
        content=ft.Row([
            ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=WHITE, on_click=go_dashboard),
            ft.Text("Inventory", color=WHITE, size=22, weight=ft.FontWeight.BOLD),
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

    body = ft.Container(expand=True, padding=24, content=ft.Column([title_row, ft.Container(height=12), tabs_row, ft.Container(height=12), content_area], spacing=0, expand=True))

    return ft.Column(spacing=0, expand=True, controls=[header, body, footer])