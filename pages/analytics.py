import flet as ft
import os, time
from datetime import datetime
import flet_charts as fch

DARK_RED   = "#8B0000"
TEXT_WHITE = "#FFFFFF"
BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

try:
    from api_client import (
        get_peak_hours, get_heatmap, get_fuel_profit_margins,
        get_oil_profit_margins, get_unified_profit_margins,
        get_revenue_summary, get_top_oils
    )
except ImportError:
    try:
        from .api_client import (
            get_peak_hours, get_heatmap, get_fuel_profit_margins,
            get_oil_profit_margins, get_unified_profit_margins,
            get_revenue_summary, get_top_oils
        )
    except:
        import requests
        def _headers(auth: dict):
            token = auth.get("access_token") or auth.get("token")
            return {"Authorization": f"Bearer {token}"} if token else {}
        def get_peak_hours(auth, days=30, product_type="all"):
            r = requests.get(f"{BASE_URL}/analytics/peak-hours", params={"days": days, "product_type": product_type}, headers=_headers(auth), timeout=10)
            r.raise_for_status(); return r.json()
        def get_heatmap(auth, days=30, product_type="fuel"):
            r = requests.get(f"{BASE_URL}/analytics/heatmap", params={"days": days, "product_type": product_type}, headers=_headers(auth), timeout=10)
            r.raise_for_status(); return r.json()
        def get_fuel_profit_margins(auth, days=30):
            r = requests.get(f"{BASE_URL}/analytics/profit-margins/fuel", params={"days": days}, headers=_headers(auth), timeout=10)
            r.raise_for_status(); return r.json()
        def get_oil_profit_margins(auth, days=30):
            r = requests.get(f"{BASE_URL}/analytics/profit-margins/oil", params={"days": days}, headers=_headers(auth), timeout=10)
            r.raise_for_status(); return r.json()
        def get_unified_profit_margins(auth, days=30):
            r = requests.get(f"{BASE_URL}/analytics/profit-margins/unified", params={"days": days}, headers=_headers(auth), timeout=10)
            r.raise_for_status(); return r.json()
        def get_revenue_summary(auth, days=30):
            r = requests.get(f"{BASE_URL}/analytics/revenue/summary", params={"days": days}, headers=_headers(auth), timeout=10)
            r.raise_for_status(); return r.json()
        def get_top_oils(auth, days=30, limit=5):
            r = requests.get(f"{BASE_URL}/analytics/oil/top-selling", params={"days": days, "limit": limit}, headers=_headers(auth), timeout=10)
            r.raise_for_status(); return r.json()

def analytics_page(page: ft.Page, auth: dict):
    page.title = "Analytics Dashboard"
    page.bgcolor = "#F5F5F5"
    page.padding = 0
    page.theme = ft.Theme(color_scheme_seed=DARK_RED)

    days_dropdown = ft.Dropdown(
        label="Period", value="30", filled=True, fill_color="white",
        border_radius=6, border_color="#CCCCCC", focused_border_color=DARK_RED,
        width=140,
        options=[
            ft.dropdown.Option("7", "Last 7 days"),
            ft.dropdown.Option("30", "Last 30 days"),
            ft.dropdown.Option("90", "Last 90 days"),
            ft.dropdown.Option("365", "Last Year"),
        ]
    )
    product_dropdown = ft.Dropdown(
        label="Product", value="all", filled=True, fill_color="white",
        border_radius=6, border_color="#CCCCCC", focused_border_color=DARK_RED,
        width=140,
        options=[
            ft.dropdown.Option("all", "All"),
            ft.dropdown.Option("fuel", "Fuel only"),
            ft.dropdown.Option("oil", "Oil only"),
        ]
    )

    rev_text = ft.Text("₱0", size=18, weight=ft.FontWeight.BOLD, color=DARK_RED)
    profit_text = ft.Text("₱0", size=18, weight=ft.FontWeight.BOLD, color="#2E7D32")
    margin_text = ft.Text("0%", size=18, weight=ft.FontWeight.BOLD, color="#1565C0")
    peak_text = ft.Text("N/A", size=18, weight=ft.FontWeight.BOLD, color="#4A148C")

    def make_summary_card(label, value_ctrl, icon, icon_color):
        return ft.Container(
            content=ft.Column(controls=[
                ft.Row(controls=[ft.Text(label, size=11, color="#666"), ft.Icon(icon, size=16, color=icon_color)], spacing=6),
                value_ctrl
            ], spacing=6, tight=True),
            bgcolor="white", border_radius=8, padding=ft.Padding.symmetric(horizontal=16, vertical=14),
            width=180, shadow=ft.BoxShadow(blur_radius=4, color="#00000015", offset=ft.Offset(0, 2))
        )

    summary_row = ft.Row(controls=[
        make_summary_card("Total Revenue", rev_text, ft.Icons.ATTACH_MONEY, "#2E7D32"),
        make_summary_card("Total Profit", profit_text, ft.Icons.TRENDING_UP, "#1565C0"),
        make_summary_card("Margin", margin_text, ft.Icons.PIE_CHART, DARK_RED),
        make_summary_card("Peak Window", peak_text, ft.Icons.ACCESS_TIME, "#4A148C"),
    ], spacing=12, wrap=True)

    peak_chart_container = ft.Container(
        content=ft.Column(controls=[
            ft.Text("Peak Hours - Transactions per Hour", size=13, weight=ft.FontWeight.BOLD, color="#222"),
            ft.Container(padding=20, content=ft.Row([ft.ProgressRing(width=16, height=16, color=DARK_RED), ft.Text("Loading...", size=12, color="#777")], spacing=10))
        ], spacing=8),
        bgcolor="white", border_radius=8, padding=ft.Padding.all(16),
        shadow=ft.BoxShadow(blur_radius=4, color="#00000015", offset=ft.Offset(0, 2)),
        expand=True, height=300
    )

    fuel_pie_container = ft.Container(
        content=ft.Column(controls=[
            ft.Text("Fuel Consumption (Liters Sold)", size=13, weight=ft.FontWeight.BOLD, color="#222"),
            ft.Container(padding=20, content=ft.Row([ft.ProgressRing(width=16, height=16, color=DARK_RED), ft.Text("Loading...", size=12, color="#777")], spacing=10))
        ], spacing=8),
        bgcolor="white", border_radius=8, padding=ft.Padding.all(16),
        shadow=ft.BoxShadow(blur_radius=4, color="#00000015", offset=ft.Offset(0, 2)),
        expand=True, height=300
    )

    oil_bar_container = ft.Container(
        content=ft.Column(controls=[
            ft.Text("Top Selling Oils (Qty)", size=13, weight=ft.FontWeight.BOLD, color="#222"),
            ft.Container(padding=20, content=ft.Row([ft.ProgressRing(width=16, height=16, color=DARK_RED), ft.Text("Loading...", size=12, color="#777")], spacing=10))
        ], spacing=8),
        bgcolor="white", border_radius=8, padding=ft.Padding.all(16),
        shadow=ft.BoxShadow(blur_radius=4, color="#00000015", offset=ft.Offset(0, 2)),
        expand=True, height=300
    )

    profit_bar_container = ft.Container(
        content=ft.Column(controls=[
            ft.Text("Profit Margins per Fuel", size=13, weight=ft.FontWeight.BOLD, color="#222"),
            ft.Container(padding=20, content=ft.Row([ft.ProgressRing(width=16, height=16, color=DARK_RED), ft.Text("Loading...", size=12, color="#777")], spacing=10))
        ], spacing=8),
        bgcolor="white", border_radius=8, padding=ft.Padding.all(16),
        shadow=ft.BoxShadow(blur_radius=4, color="#00000015", offset=ft.Offset(0, 2)),
        expand=True, height=300
    )

    heatmap_container = ft.Container(
        content=ft.Column(controls=[
            ft.Text("Demand Heatmap (Day vs Hour)", size=13, weight=ft.FontWeight.BOLD, color="#222"),
            ft.Container(padding=20, content=ft.Row([ft.ProgressRing(width=16, height=16, color=DARK_RED), ft.Text("Loading...", size=12, color="#777")], spacing=10))
        ], spacing=8),
        bgcolor="white", border_radius=8, padding=ft.Padding.all(16),
        shadow=ft.BoxShadow(blur_radius=4, color="#00000015", offset=ft.Offset(0, 2)),
        expand=False
    )

    insight_text = ft.Text("Loading insights...", size=12, color="#333")

    def build_peak_bar_chart(hourly_data):
        if not hourly_data:
            return ft.Container(content=ft.Text("No transaction data recorded for this window.", size=12, color="#777"), padding=20)
        
        max_y = max([h.get("transaction_count", 0) for h in hourly_data]) if hourly_data else 10
        if max_y == 0: max_y = 10
        
        bar_groups = []
        for h in hourly_data:
            bar_groups.append(
                fch.BarChartGroup(
                    x=h.get("hour", 0),
                    rods=[
                        fch.BarChartRod(
                            from_y=0,
                            to_y=float(h.get("transaction_count", 0)),
                            width=8,
                            color=DARK_RED,
                            border_radius=ft.BorderRadius.all(2),
                        )
                    ]
                )
            )
        return fch.BarChart(
            groups=bar_groups,
            border=ft.Border.all(1, "#EEEEEE"),
            left_axis=fch.ChartAxis(label_size=36),
            bottom_axis=fch.ChartAxis(label_size=30),
            horizontal_grid_lines=fch.ChartGridLines(interval=max_y/4 if max_y>4 else 1, color="#F0F0F0", width=1),
            max_y=max_y*1.25,
            expand=True,
        )

    def build_fuel_pie(fuel_data):
        if not fuel_data:
            return ft.Container(content=ft.Text("No fuel sales data available.", size=12, color="#888"), padding=20)
        colors = ["#8B0000", "#C62828", "#EF5350", "#FF8A65", "#FFCCBC", "#B71C1C"]
        total = sum([f.get("liters_sold", 0) for f in fuel_data]) or 1
        sections = []
        for i, f in enumerate(fuel_data):
            liters = f.get("liters_sold", 0)
            pct = liters / total * 100
            sections.append(
                fch.PieChartSection(
                    value=float(liters),
                    title=f"{f.get('fuel_name','Unknown')}\n{pct:.0f}%",
                    color=colors[i % len(colors)],
                    radius=70,
                    title_style=ft.TextStyle(size=10, color="white", weight=ft.FontWeight.BOLD)
                )
            )
        return fch.PieChart(sections=sections, sections_space=2, center_space_radius=35, expand=True)

    def build_oil_bar(top_oils):
        if not top_oils:
            return ft.Container(content=ft.Text("No lubricant sales found.", size=12, color="#888"), padding=20)
        max_q = max([o.get("quantity_sold", 0) for o in top_oils]) or 10
        bar_groups = []
        for idx, o in enumerate(top_oils):
            bar_groups.append(
                fch.BarChartGroup(
                    x=idx,
                    rods=[fch.BarChartRod(from_y=0, to_y=float(o.get("quantity_sold", 0)), width=18, color="#2E7D32", border_radius=ft.BorderRadius.all(3))]
                )
            )
        chart = fch.BarChart(
            groups=bar_groups,
            border=ft.Border.all(1, "#EEEEEE"),
            left_axis=fch.ChartAxis(label_size=36),
            bottom_axis=fch.ChartAxis(label_size=0), 
            max_y=max_q*1.25,
            expand=True
        )
        labels_row = ft.Row(
            controls=[ft.Container(width=60, content=ft.Text(f"{o.get('brand','')} {o.get('name','')}"[:12], size=9, color="#555", text_align=ft.TextAlign.CENTER)) for o in top_oils],
            spacing=8, alignment=ft.MainAxisAlignment.SPACE_AROUND
        )
        return ft.Column(controls=[ft.Container(content=chart, height=180, expand=True), labels_row], spacing=6)

    def build_profit_bar(fuel_margins):
        if not fuel_margins:
            return ft.Container(content=ft.Text("No structural margin logs found.", size=12, color="#888"), padding=20)
        max_m = max([abs(f.get("margin_percent", 0)) for f in fuel_margins]) or 20
        bar_groups = []
        for idx, f in enumerate(fuel_margins):
            bar_groups.append(
                fch.BarChartGroup(
                    x=idx,
                    rods=[fch.BarChartRod(from_y=0, to_y=float(f.get("margin_percent", 0)), width=18, color="#1565C0", border_radius=ft.BorderRadius.all(3))]
                )
            )
        chart = fch.BarChart(
            groups=bar_groups,
            border=ft.Border.all(1, "#EEEEEE"),
            left_axis=fch.ChartAxis(label_size=36),
            bottom_axis=fch.ChartAxis(label_size=0),
            max_y=max_m*1.3,
            min_y=0,
            expand=True
        )
        labels_row = ft.Row(
            controls=[ft.Container(width=60, content=ft.Text(f.get("fuel_name","")[:10], size=9, color="#555", text_align=ft.TextAlign.CENTER)) for f in fuel_margins],
            spacing=8, alignment=ft.MainAxisAlignment.SPACE_AROUND
        )
        return ft.Column(controls=[ft.Container(content=chart, height=180, expand=True), labels_row], spacing=6)

    def build_heatmap_grid(heatmap_data, day_labels):
        if not heatmap_data:
            return ft.Container(content=ft.Text("Insufficient cluster metrics for data map grid.", size=12, color="#777"), padding=20)
        
        lookup = {(d.get("day"), d.get("hour")): d.get("count", 0) for d in heatmap_data if d}
        max_c = max(lookup.values()) if lookup else 1
        if max_c == 0: max_c = 1

        def color_for(v):
            if v == 0: return "#F5F5F5"
            ratio = v / max_c
            if ratio > 0.75: return DARK_RED
            if ratio > 0.5: return "#C62828"
            if ratio > 0.25: return "#EF9A9A"
            return "#FFCDD2"

        header_cells = [ft.Container(width=40, content=ft.Text("", size=9))]
        header_cells += [ft.Container(width=22, content=ft.Text(str(h), size=8, color="#777", text_align=ft.TextAlign.CENTER)) for h in range(24)]
        rows = [ft.Row(controls=header_cells, spacing=2)]

        clean_days = day_labels or ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for day_idx, label in enumerate(clean_days):
            cells = [ft.Container(width=40, content=ft.Text(label, size=10, weight=ft.FontWeight.BOLD, color="#333"))]
            for hour in range(24):
                cnt = lookup.get((day_idx, hour), 0)
                bg = color_for(cnt)
                cells.append(
                    ft.Container(
                        width=22, height=22, bgcolor=bg, border_radius=3,
                        tooltip=f"{label} {hour}:00 - {cnt} transactions",
                        alignment=ft.Alignment.CENTER,
                    )
                )
            rows.append(ft.Row(controls=cells, spacing=2))

        legend = ft.Row(controls=[
            ft.Text("Low", size=9, color="#777"),
            ft.Container(width=12, height=12, bgcolor="#FFCDD2", border_radius=2),
            ft.Container(width=12, height=12, bgcolor="#EF9A9A", border_radius=2),
            ft.Container(width=12, height=12, bgcolor="#C62828", border_radius=2),
            ft.Container(width=12, height=12, bgcolor=DARK_RED, border_radius=2),
            ft.Text("High", size=9, color="#777"),
        ], spacing=4)

        return ft.Column(controls=rows + [ft.Container(height=8), legend], spacing=2)

    def load_data():
        def bg():
            time.sleep(0.05)
            try:
                days = int(days_dropdown.value)
            except:
                days = 30
            prod = product_dropdown.value

            def safe_ui_refresh():
                try: page.update()
                except: pass

            try:
                rev = get_revenue_summary(auth, days=days)
                if rev and "combined" in rev:
                    rev_text.value = f"₱{rev['combined'].get('revenue', 0):,.0f}"
                safe_ui_refresh()
            except Exception as e:
                print(f"[analytics] Error retrieving revenue structural block: {e}")

            try:
                uni = get_unified_profit_margins(auth, days=days)
                if uni and "summary" in uni:
                    profit_text.value = f"₱{uni['summary'].get('total_profit', 0):,.0f}"
                    margin_text.value = f"{uni['summary'].get('total_margin_percent', 0):.1f}%"
                safe_ui_refresh()
            except Exception as e:
                print(f"[analytics] Error evaluating corporate profit metrics: {e}")

            try:
                peak = get_peak_hours(auth, days=days, product_type=prod)
                if peak:
                    peak_text.value = peak.get("peak_window_3h", "N/A")
                    insight_text.value = peak.get("insight", "No anomalous insights processing out.")
                    
                    peak_chart = build_peak_bar_chart(peak.get("hourly_breakdown", []))
                    busiest = peak.get('busiest_hour') or {}
                    peak_chart_container.content = ft.Column(controls=[
                        ft.Text(f"Peak Hours ({prod.upper()}) - {peak.get('peak_window_3h','')}", size=13, weight=ft.FontWeight.BOLD, color="#222"),
                        ft.Container(content=peak_chart, height=200, expand=True),
                        ft.Text(f"Busiest: {busiest.get('label','N/A')} | Recommended Staffing Level: {busiest.get('staffing_level','')}", size=10, color="#666")
                    ], spacing=8)
                safe_ui_refresh()
            except Exception as e:
                print(f"[analytics] Peak chart runtime anomaly: {e}")

            try:
                fuel_m = get_fuel_profit_margins(auth, days=days)
                if fuel_m:
                    pie = build_fuel_pie(fuel_m)
                    fuel_pie_container.content = ft.Column(controls=[
                        ft.Text("Fuel Consumption Share", size=13, weight=ft.FontWeight.BOLD, color="#222"),
                        ft.Container(content=pie, height=220, expand=True)
                    ], spacing=8)

                    profit_chart = build_profit_bar(fuel_m)
                    profit_bar_container.content = ft.Column(controls=[
                        ft.Text("Fuel Margin %", size=13, weight=ft.FontWeight.BOLD, color="#222"),
                        ft.Container(content=profit_chart, height=220, expand=True)
                    ], spacing=8)
                safe_ui_refresh()
            except Exception as e:
                print(f"[analytics] Fuel distribution block layout exception: {e}")

            try:
                top_oils = get_top_oils(auth, days=days, limit=5)
                if top_oils:
                    oil_chart = build_oil_bar(top_oils)
                    oil_bar_container.content = ft.Column(controls=[
                        ft.Text(f"Top Selling Oils - Last {days}d", size=13, weight=ft.FontWeight.BOLD, color="#222"),
                        oil_chart
                    ], spacing=8)
                safe_ui_refresh()
            except Exception as e:
                print(f"[analytics] Lubricant inventory matrix build failure: {e}")

            try:
                heat = get_heatmap(auth, days=days, product_type="fuel" if prod=="all" else prod)
                if heat:
                    grid = build_heatmap_grid(heat.get("data", []), heat.get("day_labels", []))
                    heatmap_container.content = ft.Column(controls=[
                        ft.Text(f"Demand Heatmap ({heat.get('product_type','').upper()})", size=13, weight=ft.FontWeight.BOLD, color="#222"),
                        grid
                    ], spacing=8)
                safe_ui_refresh()
            except Exception as e:
                print(f"[analytics] Heatmap render matrix collapse: {e}")

        page.run_thread(bg)

    days_dropdown.on_change = lambda e: load_data()
    product_dropdown.on_change = lambda e: load_data()

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

    filters_section = ft.Container(
        content=ft.Column(controls=[
            ft.Text("Filters", size=14, weight=ft.FontWeight.BOLD, color="#222"),
            ft.Container(height=8),
            ft.Row(controls=[days_dropdown, product_dropdown], spacing=12, wrap=True)
        ], spacing=0, tight=True),
        bgcolor="white", border_radius=8, padding=ft.Padding.symmetric(horizontal=20, vertical=16),
        shadow=ft.BoxShadow(blur_radius=4, color="#00000015", offset=ft.Offset(0, 2)),
    )

    charts_top = ft.Row(controls=[peak_chart_container, fuel_pie_container], spacing=12)
    charts_mid = ft.Row(controls=[oil_bar_container, profit_bar_container], spacing=12)

    insight_card = ft.Container(
        content=ft.Column(controls=[
            ft.Row(controls=[ft.Icon(ft.Icons.AUTO_AWESOME, size=16, color=DARK_RED), ft.Text("Insight", size=13, weight=ft.FontWeight.BOLD, color="#222")], spacing=6),
            insight_text
        ], spacing=8),
        bgcolor="white", border_radius=8, padding=ft.Padding.all(16),
        shadow=ft.BoxShadow(blur_radius=4, color="#00000015", offset=ft.Offset(0, 2)),
    )

    header = ft.Container(
        content=ft.Row([
            ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=TEXT_WHITE, on_click=go_dashboard),
            ft.Text("Analytics Dashboard", color=TEXT_WHITE, size=20, weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.Text("U-Fuel", color=TEXT_WHITE, size=16, weight=ft.FontWeight.BOLD),
                ft.Container(width=38, height=38, bgcolor=TEXT_WHITE, border_radius=18, clip_behavior=ft.ClipBehavior.HARD_EDGE,
                             content=ft.Image(src="u-fuel_logo.jpg", fit=ft.BoxFit.CONTAIN, border_radius=18)),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=DARK_RED, padding=ft.Padding.symmetric(vertical=16, horizontal=20),
    )

    footer = ft.Container(
        content=ft.Row([
            ft.Container(content=ft.Row([ft.Icon(ft.Icons.LOGOUT, color=TEXT_WHITE, size=16), ft.Text("LOGOUT", color=TEXT_WHITE, size=13, weight=ft.FontWeight.BOLD)], spacing=6),
                         bgcolor="#6B6B6B", border_radius=6, padding=ft.Padding.symmetric(vertical=8, horizontal=14), ink=True, on_click=go_logout),
            ft.Text("GAStoKITA", color=TEXT_WHITE, size=12, weight=ft.FontWeight.W_500),
            ft.Row([ft.Icon(ft.Icons.PERSON_OUTLINE, color=TEXT_WHITE, size=18), ft.Text(auth.get("name","ADMIN"), color=TEXT_WHITE, size=13, weight=ft.FontWeight.BOLD)], spacing=4),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=DARK_RED, padding=ft.Padding.symmetric(vertical=14, horizontal=24),
    )

    content = ft.Container(
        content=ft.Column(controls=[
            ft.Row(controls=[ft.Text("Overview", size=16, weight=ft.FontWeight.BOLD, color="#222")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            summary_row,
            ft.Container(height=8),
            filters_section,
            ft.Container(height=8),
            charts_top,
            ft.Container(height=8),
            charts_mid,
            ft.Container(height=8),
            heatmap_container,
            ft.Container(height=8),
            insight_card,
        ], spacing=8, scroll=ft.ScrollMode.ADAPTIVE, expand=True),
        padding=ft.Padding.all(20), expand=True
    )

    load_data()
    return ft.Column(controls=[header, content, footer], spacing=0, expand=True)