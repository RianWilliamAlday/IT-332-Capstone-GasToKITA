import flet as ft
from pages.api_client import (
    get_ai_inventory_optimization,
    get_inventory_optimization,
    get_low_stock,
)

# ==============================================================================
# UI HELPERS & THEMING (matches analytics.py / history.py)
# ==============================================================================
DARK_RED = "#8B0000"
TEXT_WHITE = "#FFFFFF"

COLOR_GREEN = "#2E7D32"
COLOR_BLUE = "#1565C0"
COLOR_PURPLE = "#6A1B9A"
COLOR_RED = "#C62828"
COLOR_AMBER = "#F5C243"        # same yellow as COLOR_DIESEL in analytics.py
COLOR_AMBER_TEXT = "#A66F00"   # darker amber for text on white

SHADOW = ft.BoxShadow(blur_radius=4, color="#00000015", offset=ft.Offset(0, 2))

URGENCY_COLORS = {
    "critical": {"border": "#EF9A9A", "badge": COLOR_RED, "text": TEXT_WHITE},
    "warning": {"border": "#FFE08A", "badge": COLOR_AMBER, "text": "#222222"},
    "normal": {"border": "#A5D6A7", "badge": COLOR_GREEN, "text": TEXT_WHITE},
    "overstocked": {"border": "#CE93D8", "badge": COLOR_PURPLE, "text": TEXT_WHITE},
}

TREND_ICONS = {
    "increasing": (ft.Icons.TRENDING_UP, COLOR_RED),
    "decreasing": (ft.Icons.TRENDING_DOWN, COLOR_GREEN),
    "stable": (ft.Icons.TRENDING_FLAT, COLOR_BLUE),
}

def get_urgency_badge(urgency: str) -> ft.Container:
    u = urgency.lower()
    style = URGENCY_COLORS.get(u, URGENCY_COLORS["normal"])
    return ft.Container(
        content=ft.Text(u.upper(), size=11, weight=ft.FontWeight.BOLD, color=style["text"]),
        bgcolor=style["badge"],
        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
        border_radius=12,
    )

def create_kpi_card(title: str, value: str, icon: str, icon_color: str, value_color: str, subtitle: str = "") -> ft.Container:
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(title, size=11, color="#666666", weight=ft.FontWeight.W_500),
                        ft.Icon(icon, size=16, color=icon_color),
                    ],
                    spacing=6,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Text(value, size=18, weight=ft.FontWeight.BOLD, color=value_color),
                ft.Text(subtitle, size=10, color="#777777") if subtitle else ft.Container(),
            ],
            spacing=6,
            tight=True,
        ),
        bgcolor="white",
        border_radius=8,
        padding=ft.Padding.symmetric(horizontal=16, vertical=14),
        width=220,
        shadow=SHADOW,
    )

# ==============================================================================
# MAIN PAGE
# ==============================================================================
def optimization_page(page: ft.Page, auth: dict):
    page.title = "Inventory Optimization"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=DARK_RED)
    page.padding = 0
    page.bgcolor = "#F5F5F5"

    selected_product_type = "all"
    is_ai_enabled = False
    include_warning_stock = True
    latest_request = {"id": 0}

    kpi_row = ft.Row(spacing=12, wrap=True)
    inventory_cards_grid = ft.Column(spacing=12, expand=True, scroll=ft.ScrollMode.AUTO)
    low_stock_list_view = ft.ListView(spacing=8, expand=True, padding=10)
    reorder_table_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    loading_bar = ft.ProgressBar(color=DARK_RED, bgcolor="#E0E0E0", visible=False)
    status_text = ft.Text("", size=12, color=COLOR_RED, visible=False)

    def safe_update():
        try:
            page.update()
        except Exception as ue:
            print(f"[inventory] update failed: {ue}")

    def render_dashboard(metrics, low_stock_data, show_ai):
        # Update KPIs
        critical_cnt = sum(1 for m in metrics if m.get("urgency") == "critical")
        warning_cnt = sum(1 for m in metrics if m.get("urgency") == "warning")
        total_reorder_cost = sum((m.get("cost_of_order") or 0) for m in metrics)

        kpi_row.controls = [
            create_kpi_card("Total Items", str(len(metrics)), ft.Icons.INVENTORY_2, COLOR_BLUE, COLOR_BLUE),
            create_kpi_card("Critical Urgency", str(critical_cnt), ft.Icons.WARNING_ROUNDED, COLOR_RED, COLOR_RED),
            create_kpi_card("Warning Urgency", str(warning_cnt), ft.Icons.REPORT_PROBLEM, COLOR_AMBER, COLOR_AMBER_TEXT),
            create_kpi_card("Estimated Reorder Cost", f"₱{total_reorder_cost:,.2f}", ft.Icons.ATTACH_MONEY, COLOR_GREEN, COLOR_GREEN),
        ]

        # Update Cards
        inventory_cards_grid.controls.clear()
        for m in metrics:
            urgency = m.get("urgency") or "normal"
            style = URGENCY_COLORS.get(urgency, URGENCY_COLORS["normal"])
            trend = m.get("trend") or "stable"
            trend_icon, trend_color = TREND_ICONS.get(trend, TREND_ICONS["stable"])
            ptype = m.get("product_type") or "item"
            type_color = COLOR_RED if ptype == "fuel" else COLOR_PURPLE

            capacity = m.get("tank_capacity") or m.get("max_stock_level") or 1.0
            stock_ratio = min(1.0, max(0.0, (m.get("current_stock") or 0) / capacity))

            metric_cols = ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column([
                        ft.Text("Stock Level", size=11, color="#666666"),
                        ft.Text(f"{m.get('current_stock')} / {capacity} {m.get('unit')}", weight=ft.FontWeight.BOLD, color="#222222"),
                        ft.ProgressBar(value=stock_ratio, color=style["badge"], bgcolor="#E0E0E0", width=160),
                    ]),
                    ft.Column([
                        ft.Text("Avg Daily / StdDev", size=11, color="#666666"),
                        ft.Text(f"{m.get('avg_daily_usage')}{m.get('unit')}/d (±{m.get('usage_std_dev')})", weight=ft.FontWeight.W_500, color="#222222"),
                    ]),
                    ft.Column([
                        ft.Text("Days Left", size=11, color="#666666"),
                        ft.Text(f"~{m.get('days_remaining')} days", weight=ft.FontWeight.BOLD, color=COLOR_AMBER_TEXT if urgency == "warning" else style["badge"]),
                    ]),
                    ft.Column([
                        ft.Text("Trend", size=11, color="#666666"),
                        ft.Row([ft.Icon(trend_icon, color=trend_color, size=16), ft.Text(trend.capitalize(), size=12, color="#222222")]),
                    ]),
                ]
            )

            ai_section = ft.Container()
            if show_ai and "ai_urgency_explanation" in m:
                risk_chips = [ft.Chip(label=ft.Text(r, size=10, color="#222222"), bgcolor="#FFCDD2") for r in m.get("ai_risk_factors", [])]
                action_items = [ft.Text(f"• {act}", size=12, color="#333333") for act in m.get("ai_action_items", [])]

                ai_section = ft.Container(
                    margin=ft.Margin.only(top=10),
                    padding=12,
                    bgcolor="#F9F9F9",
                    border_radius=8,
                    border=ft.Border.all(1, "#E0E0E0"),
                    content=ft.Column(
                        controls=[
                            ft.Row([ft.Icon(ft.Icons.AUTO_AWESOME, color=DARK_RED, size=16), ft.Text("AI Optimization Insights", weight=ft.FontWeight.BOLD, size=12, color="#222222")], spacing=6),
                            ft.Text(f"Urgency: {m.get('ai_urgency_explanation')}", size=12, color="#333333"),
                            ft.Text(f"Demand: {m.get('ai_demand_insight')}", size=12, color="#333333"),
                            ft.Text(f"Recommendation: {m.get('ai_purchase_recommendation')}", size=12, weight=ft.FontWeight.W_600, color=DARK_RED),
                            ft.Row(controls=risk_chips, wrap=True) if risk_chips else ft.Container(),
                            ft.Column(controls=[ft.Text("Action Items:", weight=ft.FontWeight.BOLD, size=11, color="#222222")] + action_items) if action_items else ft.Container(),
                        ],
                        spacing=6,
                    )
                )

            card_item = ft.Container(
                padding=16,
                bgcolor="white",
                border=ft.Border.all(1, style["border"]),
                border_radius=8,
                shadow=SHADOW,
                content=ft.Column([
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row([
                                ft.Icon(ft.Icons.LOCAL_GAS_STATION if ptype == "fuel" else ft.Icons.OIL_BARREL, color=type_color),
                                ft.Text(m.get("product_name"), size=16, weight=ft.FontWeight.BOLD, color="#222222"),
                                ft.Container(
                                    content=ft.Text(ptype.upper(), size=10, color="white", weight=ft.FontWeight.BOLD),
                                    bgcolor=type_color,
                                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                    border_radius=12,
                                ),
                            ]),
                            get_urgency_badge(urgency),
                        ]
                    ),
                    ft.Divider(height=1, color="#E0E0E0"),
                    metric_cols,
                    ai_section
                ], spacing=10)
            )
            inventory_cards_grid.controls.append(card_item)

        # Update Low Stock
        low_stock_list_view.controls.clear()
        low_items = low_stock_data.get("items", [])
        if not low_items:
            low_stock_list_view.controls.append(ft.Container(padding=20, content=ft.Text("No low stock alerts for selected criteria.", italic=True, color="#777777")))
        else:
            for item in low_items:
                item_urgency = item.get("urgency") or "warning"
                low_stock_list_view.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(
                            ft.Icons.WARNING_AMBER_ROUNDED if item_urgency == "critical" else ft.Icons.INFO_OUTLINE,
                            color=COLOR_RED if item_urgency == "critical" else COLOR_AMBER_TEXT
                        ),
                        title=ft.Text(f"{item.get('product_name')} ({(item.get('product_type') or 'item').upper()})", weight=ft.FontWeight.BOLD, color="#222222"),
                        subtitle=ft.Text(f"Current: {item.get('current_stock')} {item.get('unit')} | Threshold: {item.get('threshold')} {item.get('unit')}", color="#555555"),
                        trailing=get_urgency_badge(item_urgency),
                        bgcolor="white",
                    )
                )

        # Update Reorder Table
        rows = []
        for m in metrics:
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(m.get("product_name"), weight=ft.FontWeight.W_500)),
                        ft.DataCell(ft.Text(f"{m.get('reorder_point')} {m.get('unit')}")),
                        ft.DataCell(ft.Text(f"{m.get('safety_stock')} {m.get('unit')}")),
                        ft.DataCell(ft.Text(f"{m.get('economic_order_qty')} {m.get('unit')}")),
                        ft.DataCell(ft.Text(f"{m.get('suggested_quantity')} {m.get('unit')}", weight=ft.FontWeight.BOLD if m.get("should_reorder") else ft.FontWeight.NORMAL)),
                        ft.DataCell(ft.Text(f"₱{(m.get('cost_of_order') or 0):,.2f}", weight=ft.FontWeight.BOLD, color=DARK_RED)),
                        ft.DataCell(ft.Text(str(m.get("suggested_reorder_date")))),
                        ft.DataCell(ft.Text(f"{m.get('days_of_supply_after_reorder')} days")),
                    ]
                )
            )

        reorder_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Product")),
                ft.DataColumn(ft.Text("Reorder Pt"), numeric=True),
                ft.DataColumn(ft.Text("Safety Stock"), numeric=True),
                ft.DataColumn(ft.Text("EOQ"), numeric=True),
                ft.DataColumn(ft.Text("Suggested Order"), numeric=True),
                ft.DataColumn(ft.Text("Est Cost"), numeric=True),
                ft.DataColumn(ft.Text("Order Date")),
                ft.DataColumn(ft.Text("Supply After")),
            ],
            rows=rows,
            border=ft.Border.all(1, "#E0E0E0"),
            vertical_lines=ft.BorderSide(1, "#F0F0F0"),
        )
        reorder_table_container.controls = [ft.Row([reorder_table], scroll=ft.ScrollMode.AUTO)]

    def refresh_dashboard(e=None):
        # The AI endpoint calls Gemini once per flagged item, so load in a background thread.
        latest_request["id"] += 1
        request_id = latest_request["id"]
        product_type = selected_product_type
        ai_on = is_ai_enabled
        warn_on = include_warning_stock

        loading_bar.visible = True
        status_text.visible = False
        safe_update()

        def bg():
            try:
                if ai_on:
                    metrics = get_ai_inventory_optimization(auth, product_type)
                else:
                    metrics = get_inventory_optimization(auth, product_type)
                low_stock_data = get_low_stock(auth, include_warning=warn_on, product_type=product_type)

                if request_id != latest_request["id"]:
                    return  # a newer refresh was started, drop this result
                render_dashboard(metrics, low_stock_data, ai_on)
            except Exception as ex:
                if request_id != latest_request["id"]:
                    return
                print(f"[inventory] load failed: {ex}")
                status_text.value = f"Could not load inventory data: {ex}"
                status_text.visible = True
            finally:
                if request_id == latest_request["id"]:
                    loading_bar.visible = False
                    safe_update()

        page.run_thread(bg)

    # Event Handlers
    def on_type_change(e):
        nonlocal selected_product_type
        selected_product_type = e.control.value
        refresh_dashboard()

    def on_ai_toggle(e):
        nonlocal is_ai_enabled
        is_ai_enabled = e.control.value
        refresh_dashboard()

    def on_warning_toggle(e):
        nonlocal include_warning_stock
        include_warning_stock = e.control.value
        refresh_dashboard()

    def go_dashboard(e):
        from pages.admin_dashboard import dashboard_page
        page.controls.clear()
        page.add(dashboard_page(page, auth))
        page.update()

    def go_logout(e):
        auth.clear()
        page.controls.clear()
        try:
            from admin import build_login_view
            page.add(build_login_view(page, auth))
        except Exception:
            page.add(ft.Container(expand=True, alignment=ft.Alignment.CENTER, content=ft.Text("Logged out securely.")))
        page.update()

    # Controls setup
    type_dropdown = ft.DropdownM2(
        label="Product Type", value="all", filled=True, fill_color="white",
        border_radius=6, border_color="#CCCCCC", focused_border_color=DARK_RED,
        width=150,
        options=[
            ft.dropdownm2.Option("all", "All Items"),
            ft.dropdownm2.Option("fuel", "Fuel Only"),
            ft.dropdownm2.Option("oil", "Oil Only"),
        ],
    )
    type_dropdown.on_change = on_type_change

    ai_switch = ft.Switch(label="AI Insights", value=False, active_color=DARK_RED)
    ai_switch.on_change = on_ai_toggle

    warning_switch = ft.Switch(label="Include Warnings in Low Stock", value=True, active_color=DARK_RED)
    warning_switch.on_change = on_warning_toggle

    refresh_btn = ft.IconButton(icon=ft.Icons.REFRESH, icon_color=DARK_RED, tooltip="Sync data", on_click=refresh_dashboard)

    # --------------------------------------------------------------------------
    # HEADER, FILTERS, FOOTER
    # --------------------------------------------------------------------------
    header = ft.Container(
        content=ft.Row([
            ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=TEXT_WHITE, on_click=go_dashboard),
            ft.Column([
                ft.Text("Inventory Optimization", color=TEXT_WHITE, size=22, weight=ft.FontWeight.BOLD),
            ], spacing=0),
            ft.Row([
                ft.Text("U-Fuel", color=TEXT_WHITE, size=18, weight=ft.FontWeight.BOLD),
                ft.Container(
                    width=42, height=42, bgcolor=TEXT_WHITE, border_radius=20,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    content=ft.Image(src="u-fuel_logo.jpg", fit=ft.BoxFit.CONTAIN, border_radius=20),
                ),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=DARK_RED, padding=ft.Padding.symmetric(vertical=18, horizontal=24),
    )

    footer = ft.Container(
        content=ft.Row([
            ft.Container(
                content=ft.Row([ft.Icon(ft.Icons.LOGOUT, color=TEXT_WHITE, size=16), ft.Text("LOGOUT", color=TEXT_WHITE, size=13, weight=ft.FontWeight.BOLD)], spacing=6),
                bgcolor="#6B6B6B", border_radius=6, padding=ft.Padding.symmetric(vertical=8, horizontal=14),
                ink=True, on_click=go_logout,
            ),
            ft.Text("GAStoKITA", color=TEXT_WHITE, size=12, weight=ft.FontWeight.W_500),
            ft.Row([ft.Icon(ft.Icons.PERSON_OUTLINE, color=TEXT_WHITE, size=18), ft.Text(auth.get("name", "ADMIN"), color=TEXT_WHITE, size=13, weight=ft.FontWeight.BOLD)], spacing=4),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=DARK_RED, padding=ft.Padding.symmetric(vertical=14, horizontal=24),
    )

    filters_section = ft.Container(
        content=ft.Column(controls=[
            ft.Text("Filters", size=14, weight=ft.FontWeight.BOLD, color="#222222"),
            ft.Container(height=8),
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    type_dropdown,
                    ft.Row([ai_switch, ft.VerticalDivider(width=1, color="#CCCCCC"), warning_switch, refresh_btn], spacing=15),
                ],
            ),
        ], spacing=0, tight=True),
        bgcolor="white", border_radius=8, padding=ft.Padding.symmetric(horizontal=20, vertical=16),
        shadow=SHADOW,
    )

    # --------------------------------------------------------------------------
    # TAB CONTROLLER (Flet TabBar + TabBarView)
    # --------------------------------------------------------------------------
    tabs_control = ft.Tabs(
        length=3,
        content=ft.Column(
            controls=[
                ft.TabBar(
                    indicator_color=DARK_RED,
                    label_color=DARK_RED,
                    unselected_label_color="#757575",
                    tabs=[
                        ft.Tab(label="Optimization Insights", icon=ft.Icons.ANALYTICS),
                        ft.Tab(label="Low Stock Monitor", icon=ft.Icons.WARNING_AMBER),
                        ft.Tab(label="EOQ & Reorder Planner", icon=ft.Icons.TABLE_CHART),
                    ]
                ),
                ft.TabBarView(
                    controls=[
                        ft.Container(padding=10, content=inventory_cards_grid),
                        ft.Container(padding=10, content=low_stock_list_view),
                        ft.Container(padding=10, content=reorder_table_container),
                    ],
                    expand=True,
                ),
            ],
            expand=True,
        ),
        expand=True,
    )

    content = ft.Container(
        content=ft.Column(
            controls=[
                kpi_row,
                ft.Container(height=8),
                filters_section,
                loading_bar,
                status_text,
                ft.Container(height=8),
                tabs_control,
            ],
            spacing=0,
            expand=True,
        ),
        padding=ft.Padding.all(24),
        expand=True,
    )

    refresh_dashboard()

    return ft.Column(controls=[header, content, footer], spacing=0, expand=True)