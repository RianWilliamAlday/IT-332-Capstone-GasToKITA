import flet as ft
import os, time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import flet_charts as fch
from pages.api_client import (
        get_peak_hours, get_heatmap, get_fuel_profit_margins,
        get_oil_profit_margins, get_unified_profit_margins,
        get_revenue_summary, get_top_oils, get_attendant_rankings,
        get_attendant_performance, get_attendant_leaderboard
    )

DARK_RED   = "#8B0000"
TEXT_WHITE = "#FFFFFF"
BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
COLOR_REGULAR = "#0CA940"
COLOR_PREMIUM = "#E3242B"
COLOR_DIESEL = "#F5C243"

def analytics_page(page: ft.Page, auth: dict):
    page.title = "Analytics & Performance Dashboard"
    page.bgcolor = "#F5F5F5"
    page.padding = 0
    page.theme = ft.Theme(color_scheme_seed=DARK_RED)
    selected_attendant = {"name": None}

    days_dropdown = ft.DropdownM2(
        label="Period", value="30", filled=True, fill_color="white",
        border_radius=6, border_color="#CCCCCC", focused_border_color=DARK_RED,
        width=140,
        options=[
            ft.dropdownm2.Option("7", "Last 7 days"),
            ft.dropdownm2.Option("30", "Last 30 days"),
            ft.dropdownm2.Option("90", "Last 90 days"),
            ft.dropdownm2.Option("365", "Last Year"),
        ]
    )
    product_dropdown = ft.DropdownM2(
        label="Product", value="all", filled=True, fill_color="white",
        border_radius=6, border_color="#CCCCCC", focused_border_color=DARK_RED,
        width=140,
        options=[
            ft.dropdownm2.Option("all", "All"),
            ft.dropdownm2.Option("fuel", "Fuel only"),
            ft.dropdownm2.Option("oil", "Oil only"),
        ]
    )

    attendant_sort_dropdown = ft.DropdownM2(
        label="Sort Attendants By", value="revenue", filled=True, fill_color="white",
        border_radius=6, border_color="#CCCCCC", focused_border_color=DARK_RED,
        width=180,
        options=[
            ft.dropdownm2.Option("revenue", "Revenue"),
            ft.dropdownm2.Option("liters", "Liters Sold"),
            ft.dropdownm2.Option("transactions", "Transactions"),
            ft.dropdownm2.Option("oil_pcs", "Oil Pieces"),
            ft.dropdownm2.Option("avg_ticket", "Avg Ticket Size"),
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

    podium_container = ft.Row(spacing=20, alignment=ft.MainAxisAlignment.CENTER)
    
    ranking_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Rank")),
            ft.DataColumn(ft.Text("Attendant")),
            ft.DataColumn(ft.Text("Total Revenue")),
            ft.DataColumn(ft.Text("Transactions")),
            ft.DataColumn(ft.Text("Liters Sold")),
            ft.DataColumn(ft.Text("Oil Qty")),
            ft.DataColumn(ft.Text("Avg Ticket")),
            ft.DataColumn(ft.Text("Action")),
        ],
        rows=[]
    )
    
    leaderboard_container = ft.Container(
        content=ft.Column(controls=[
            ft.Row([
                ft.Text("Attendant Sales Leaderboard", size=15, weight=ft.FontWeight.BOLD, color="#222"),
                attendant_sort_dropdown
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=10),
            ft.Text("🏆 Quick Dashboard Podium (Top 3 by Revenue)", size=12, color="#555", weight=ft.FontWeight.W_600),
            podium_container,
            ft.Divider(color="#EEEEEE"),
            ft.Container(
                content=ft.Column([ranking_table], scroll=ft.ScrollMode.ADAPTIVE),
                clip_behavior=ft.ClipBehavior.HARD_EDGE
            )
        ]),
        bgcolor="white", border_radius=8, padding=ft.Padding.all(20),
        shadow=ft.BoxShadow(blur_radius=4, color="#00000015", offset=ft.Offset(0, 2))
    )

    detailed_perf_container = ft.Container(
        content=ft.Text("Select an attendant from the leaderboard above to view deep performance analytics.", color="#777", size=12),
        bgcolor="white", border_radius=8, padding=ft.Padding.all(20),
        shadow=ft.BoxShadow(blur_radius=4, color="#00000015", offset=ft.Offset(0, 2)),
        visible=False
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
            return ft.Text("No fuel sales")
            
        total = sum([f.get("liters_sold", 0) for f in fuel_data]) or 1
        
        fuel_color_map = {
            "regular": COLOR_REGULAR,
            "unleaded": COLOR_REGULAR,
            "premium": COLOR_PREMIUM,
            "diesel": COLOR_DIESEL,
        }
        
        sections = []
        legend = []
        
        for i, f in enumerate(fuel_data):
            fuel_name = f.get('fuel_name', '')
            liters = f.get("liters_sold", 0)
            pct = liters / total * 100
            matched_color = DARK_RED
            for key, val in fuel_color_map.items():
                if key in fuel_name.lower():
                    matched_color = val
                    break

            sections.append(fch.PieChartSection(
                value=float(liters),
                title=f"{pct:.0f}%" if pct > 5 else "",
                color=matched_color,
                radius=70
            ))
            
            legend.append(ft.Row([
                ft.Container(width=10, height=10, bgcolor=matched_color, border_radius=2),
                ft.Text(f"{fuel_name} - {pct:.1f}% ({liters:.0f}L)", size=11)
            ]))
            
        return ft.Column([
            ft.Container(content=fch.PieChart(sections=sections, center_space_radius=35, sections_space=2), height=200),
            ft.Row(controls=legend, spacing=8)
        ])

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

    def view_individual_performance(name):
        selected_attendant["name"] = name
        detailed_perf_container.visible = True
        detailed_perf_container.content = ft.Row([ft.ProgressRing(width=20, height=20), ft.Text(f" Fetching profile metrics for {name}...")])
        page.update()
        
        try:
            days = int(days_dropdown.value)
            perf = get_attendant_performance(auth, attendant_name=name, days=days)
            summary = perf.get("summary", {})
            f_mix = perf.get("fuel_mix", [])
            fuel_mix_text = ", ".join([f"{f['fuel_name']}: {f['liters']}L" for f in f_mix]) if f_mix else "No fuel mix logs"
            
            detailed_perf_container.content = ft.Column(controls=[
                ft.Row([
                    ft.Text(f"📊 Detailed Card: {perf.get('attendant_name')}", size=14, weight=ft.FontWeight.BOLD, color=DARK_RED),
                    ft.IconButton(ft.Icons.CLOSE, icon_size=16, on_click=lambda _: hide_perf_view())
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(perf.get("insight", ""), italic=True, size=12, color="#555"),
                ft.Container(height=6),
                ft.Row(controls=[
                    make_summary_card("Attendant Revenue", ft.Text(f"₱{summary.get('total_revenue', 0):,.2f}", size=14, color=DARK_RED, weight=ft.FontWeight.BOLD), ft.Icons.MONETIZATION_ON, DARK_RED),
                    make_summary_card("Total Txns", ft.Text(str(summary.get('total_transactions', 0)), size=14, weight=ft.FontWeight.BOLD), ft.Icons.RECEIPT_LONG, "#666"),
                    make_summary_card("Fuel Efficiency", ft.Text(f"{summary.get('fuel', {}).get('liters', 0):,.1f} L", size=14, color="#1565C0", weight=ft.FontWeight.BOLD), ft.Icons.LOCAL_GAS_STATION, "#1565C0"),
                    make_summary_card("Oil Sold", ft.Text(f"{summary.get('oil', {}).get('quantity', 0)} pcs", size=14, color="#2E7D32", weight=ft.FontWeight.BOLD), ft.Icons.OPACITY, "#2E7D32"),
                ], wrap=True, spacing=10),
                ft.Container(height=6),
                ft.Text(f"Fuel Product Mix: {fuel_mix_text}", size=11, color="#444", weight=ft.FontWeight.W_500)
            ], spacing=6)
        except Exception as e:
            detailed_perf_container.content = ft.Text(f"Error loading attendant profile: {e}", color="red")
        page.update()

    def hide_perf_view():
        detailed_perf_container.visible = False
        selected_attendant["name"] = None
        page.update()

    def make_podium_card(rank_idx, name, subtitle, value_str):
        colors = {1: "#FFD700", 2: "#C0C0C0", 3: "#CD7F32"}
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        return ft.Container(
            content=ft.Column([
                ft.Text(medals.get(rank_idx, ""), size=22, text_align=ft.TextAlign.CENTER),
                ft.Text(name if name else "Empty Slot", size=12, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, max_lines=1),
                ft.Text(value_str, size=11, color=DARK_RED, weight=ft.FontWeight.BOLD),
                ft.Text(subtitle, size=9, color="#777")
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
            width=130, height=120, bgcolor="#F9F9F9", border_radius=8, border=ft.Border.all(1.5, colors.get(rank_idx, "#DDD")),
            padding=8
        )

    def safe_ui_refresh(*controls):
        try:
            for c in controls:
                c.update()
        except Exception as ue:
            print(f"[analytics] update failed: {ue}")

    def build_rank_rows(rankings):
        rows = []
        for r in rankings:
            name_str = r.get("attendant_name", "")
            medal = r.get("medal") or ""
            rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(f"{r.get('rank')} {medal}")),
                    ft.DataCell(ft.Text(name_str, weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(f"₱{r.get('total_revenue', 0):,.2f}")),
                    ft.DataCell(ft.Text(str(r.get('transaction_count', 0)))),
                    ft.DataCell(ft.Text(f"{r.get('total_liters', 0):,.1f} L")),
                    ft.DataCell(ft.Text(str(r.get('total_oil_pcs', 0)))),
                    ft.DataCell(ft.Text(f"₱{r.get('avg_ticket', 0):,.2f}")),
                    ft.DataCell(
                        ft.TextButton("Inspect Profile", on_click=lambda e, name=name_str: view_individual_performance(name))
                    ),
                ])
            )
        return rows

    def load_data():
        def bg():
            time.sleep(0.05)
            try:
                days = int(days_dropdown.value)
            except Exception:
                days = 30
            prod = product_dropdown.value
            attendant_sort = attendant_sort_dropdown.value

            with ThreadPoolExecutor(max_workers=8) as ex:
                f_rev  = ex.submit(get_revenue_summary, auth, days=days)
                f_uni  = ex.submit(get_unified_profit_margins, auth, days=days)
                f_peak = ex.submit(get_peak_hours, auth, days=days, product_type=prod)
                f_fuel = ex.submit(get_fuel_profit_margins, auth, days=days)
                f_oils = ex.submit(get_top_oils, auth, days=days, limit=5)
                f_heat = ex.submit(get_heatmap, auth, days=days, product_type="fuel" if prod == "all" else prod)
                f_lb   = ex.submit(get_attendant_leaderboard, auth, days=days)
                f_rank = ex.submit(get_attendant_rankings, auth, days=days, product_type=prod,
                                   sort_by=attendant_sort, limit=15, include_breakdown=False)

                try:
                    rev = f_rev.result()
                    if rev and "combined" in rev:
                        rev_text.value = f"₱{rev['combined'].get('revenue', 0):,.0f}"
                    safe_ui_refresh(rev_text)
                except Exception as e:
                    print(f"[analytics] revenue: {e}")

                try:
                    uni = f_uni.result()
                    if uni and "summary" in uni:
                        profit_text.value = f"₱{uni['summary'].get('total_profit', 0):,.0f}"
                        margin_text.value = f"{uni['summary'].get('total_margin_percent', 0):.1f}%"
                    safe_ui_refresh(profit_text, margin_text)
                except Exception as e:
                    print(f"[analytics] profit: {e}")

                try:
                    peak = f_peak.result()
                    if peak:
                        peak_text.value = peak.get("peak_window_3h", "N/A")
                        insight_text.value = peak.get("insight", "No anomalous insights processing out.")
                        peak_chart = build_peak_bar_chart(peak.get("hourly_breakdown", []))
                        peak_chart_container.content = ft.Column(controls=[
                            ft.Text(f"Peak Hours ({prod.upper()}) - {peak.get('peak_window_3h','')}", size=13, weight=ft.FontWeight.BOLD, color="#222"),
                            ft.Container(content=peak_chart, height=200, expand=True),
                        ], spacing=8)
                    safe_ui_refresh(peak_text, insight_text, peak_chart_container)
                except Exception as e:
                    print(f"[analytics] peak: {e}")

                try:
                    fuel_m = f_fuel.result()
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
                    safe_ui_refresh(fuel_pie_container, profit_bar_container)
                except Exception as e:
                    print(f"[analytics] fuel: {e}")

                try:
                    top_oils = f_oils.result()
                    if top_oils:
                        oil_bar_container.content = ft.Column(controls=[
                            ft.Text(f"Top Selling Oils - Last {days}d", size=13, weight=ft.FontWeight.BOLD, color="#222"),
                            build_oil_bar(top_oils)
                        ], spacing=8)
                    safe_ui_refresh(oil_bar_container)
                except Exception as e:
                    print(f"[analytics] oils: {e}")

                try:
                    heat = f_heat.result()
                    if heat:
                        grid = build_heatmap_grid(heat.get("data", []), heat.get("day_labels", []))
                        heatmap_container.content = ft.Column(controls=[
                            ft.Text(f"Demand Heatmap ({heat.get('product_type','').upper()})", size=13, weight=ft.FontWeight.BOLD, color="#222"),
                            grid
                        ], spacing=8)
                    safe_ui_refresh(heatmap_container)
                except Exception as e:
                    print(f"[analytics] heatmap: {e}")

                try:
                    lb = f_lb.result()
                    podium = lb.get("podium", [])
                    t1 = lb.get("top_1") or (podium[0] if len(podium) > 0 else None)
                    t2 = lb.get("top_2") or (podium[1] if len(podium) > 1 else None)
                    t3 = lb.get("top_3") or (podium[2] if len(podium) > 2 else None)
                    podium_container.controls = [
                        make_podium_card(2, t2.get("attendant_name") if t2 else None, "2nd Place", f"₱{t2.get('total_revenue',0):,.0f}" if t2 else "₱0"),
                        make_podium_card(1, t1.get("attendant_name") if t1 else None, "Top Performer", f"₱{t1.get('total_revenue',0):,.0f}" if t1 else "₱0"),
                        make_podium_card(3, t3.get("attendant_name") if t3 else None, "3rd Place", f"₱{t3.get('total_revenue',0):,.0f}" if t3 else "₱0"),
                    ]
                    safe_ui_refresh(podium_container)
                except Exception as e:
                    print(f"[analytics] podium: {e}")

                try:
                    rank_data = f_rank.result()
                    ranking_table.rows = build_rank_rows(rank_data.get("rankings", []))
                    safe_ui_refresh(ranking_table)
                    if selected_attendant["name"]:
                        view_individual_performance(selected_attendant["name"])
                except Exception as e:
                    print(f"[analytics] rankings: {e}")

        page.run_thread(bg)

    def refresh_rankings_only():
        def bg():
            try:
                rank_data = get_attendant_rankings(
                    auth,
                    days=int(days_dropdown.value),
                    product_type=product_dropdown.value,
                    sort_by=attendant_sort_dropdown.value,
                    limit=15,
                    include_breakdown=False,
                )
                ranking_table.rows = build_rank_rows(rank_data.get("rankings", []))
                ranking_table.update()
            except Exception as e:
                print(f"[analytics] rankings refresh: {e}")
        page.run_thread(bg)

    days_dropdown.on_change = lambda e: load_data()
    product_dropdown.on_change = lambda e: load_data()
    attendant_sort_dropdown.on_change = lambda e: refresh_rankings_only()

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
            ft.Text("Analytics Dashboard", color=TEXT_WHITE, size=22, weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.Text("U-Fuel", color=TEXT_WHITE, size=18, weight=ft.FontWeight.BOLD),
                ft.Container(width=42, height=42, bgcolor=TEXT_WHITE, border_radius=20, clip_behavior=ft.ClipBehavior.HARD_EDGE, content=ft.Image(src="u-fuel_logo.jpg", fit=ft.BoxFit.CONTAIN, border_radius=20)),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=DARK_RED, padding=ft.Padding.symmetric(vertical=18, horizontal=24),
    )
    
    footer = ft.Container(
        content=ft.Row([
            ft.Container(content=ft.Row([ft.Icon(ft.Icons.LOGOUT, color=TEXT_WHITE, size=16), ft.Text("LOGOUT", color=TEXT_WHITE, size=13, weight=ft.FontWeight.BOLD)], spacing=6), bgcolor="#6B6B6B", border_radius=6, padding=ft.Padding.symmetric(vertical=8, horizontal=14), ink=True, on_click=go_logout),
            ft.Text("GAStoKITA", color=TEXT_WHITE, size=12, weight=ft.FontWeight.W_500),
            ft.Row([ft.Icon(ft.Icons.PERSON_OUTLINE, color=TEXT_WHITE, size=18), ft.Text(auth.get("name","ADMIN"), color=TEXT_WHITE, size=13, weight=ft.FontWeight.BOLD)], spacing=4),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER), bgcolor=DARK_RED, padding=ft.Padding.symmetric(vertical=14, horizontal=24),
    )

    content = ft.Container(
        content=ft.Column(controls=[
            ft.Row(controls=[ft.Text("Overview", size=16, weight=ft.FontWeight.BOLD, color="#222")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            summary_row,
            ft.Container(height=8),
            filters_section,
            ft.Container(height=8),
            leaderboard_container,
            detailed_perf_container,
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
127.0.0.1