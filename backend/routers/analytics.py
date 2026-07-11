from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, text
from ..db.database import get_session

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/peak-hours")
def get_peak_hours(
    days: int = Query(30, description="Last N days to analyze"),
    fuel_id: Optional[int] = None,
    session: Session = Depends(get_session)
):
    since_date = datetime.now() - timedelta(days=days)

    # Uses your actual columns: sold_at, liters_sold, total_amount
    sql = text("""
        SELECT
            CAST(strftime('%H', sold_at) AS INTEGER) as hour,
            COUNT(*) as transaction_count,
            COALESCE(SUM(total_amount), 0) as total_revenue,
            COALESCE(SUM(liters_sold), 0) as total_liters
        FROM sale
        WHERE sold_at >= :since_date
        AND (:fuel_id IS NULL OR fuel_id = :fuel_id)
        GROUP BY hour
        ORDER BY hour
    """)

    rows = session.execute(sql, {"since_date": since_date, "fuel_id": fuel_id}).fetchall()

    hourly_map = {r[0]: {"count": r[1], "revenue": r[2], "liters": r[3]} for r in rows}

    hourly_data = []
    for h in range(24):
        d = hourly_map.get(h, {"count": 0, "revenue": 0, "liters": 0})
        hourly_data.append({
            "hour": h,
            "label": f"{h:02d}:00",
            "transaction_count": d["count"],
            "total_revenue": round(d["revenue"], 2),
            "total_liters": round(d["liters"], 2)
        })

    # Find best 3-hour window for staffing recommendation
    max_window, max_count = None, 0
    for i in range(22): # 0-2, 1-3... 21-23
        wc = sum(hourly_data[j]["transaction_count"] for j in range(i, i+3))
        if wc > max_count:
            max_count, max_window = wc, f"{i:02d}:00 - {i+3:02d}:00"

    avg = sum(h["transaction_count"] for h in hourly_data) / 24 if hourly_data else 0
    for h in hourly_data:
        if h["transaction_count"] >= avg * 1.8:
            h["staffing_level"] = "High - 2 Cashiers Recommended"
        elif h["transaction_count"] >= avg * 1.2:
            h["staffing_level"] = "Medium - 1 + Standby"
        else:
            h["staffing_level"] = "Low - 1 Cashier"

    busiest = max(hourly_data, key=lambda x: x["transaction_count"])

    return {
        "period_days": days,
        "busiest_hour": busiest,
        "peak_window_3h": max_window,
        "peak_window_transactions": max_count,
        "hourly_breakdown": hourly_data,
        "insight": f"Peak demand is {max_window} with {max_count} transactions. Busiest single hour is {busiest['label']}."
    }

@router.get("/heatmap")
def get_demand_heatmap(days: int = 30, session: Session = Depends(get_session)):
    since_date = datetime.now() - timedelta(days=days)
    sql = text("""
        SELECT
            CAST(strftime('%w', sold_at) AS INTEGER) as day_of_week,
            CAST(strftime('%H', sold_at) AS INTEGER) as hour,
            COUNT(*) as count
        FROM sale
        WHERE sold_at >= :since_date
        GROUP BY day_of_week, hour
    """)
    rows = session.execute(sql, {"since_date": since_date}).fetchall()
    return {
        "data": [{"day": r[0], "hour": r[1], "count": r[2]} for r in rows],
        "day_labels": ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]
    }

@router.get("/profit-margins")
def get_profit_margins(days: int = 30, session: Session = Depends(get_session)):
    since = datetime.now() - timedelta(days=days)

    # Weighted average cost per fuel from RestockLog
    # cost is total cost per restock, so cost_per_liter = SUM(cost)/SUM(liters_added)
    sql = text("""
        WITH fuel_costs AS (
            SELECT fuel_id,
                   SUM(cost) as total_cost,
                   SUM(liters_added) as total_liters_added,
                   CASE WHEN SUM(liters_added) > 0 THEN SUM(cost)/SUM(liters_added) ELSE 0 END as avg_cost_per_liter
            FROM restocklog WHERE restocked_at >= :since GROUP BY fuel_id
        ),
        fuel_sales AS (
            SELECT fuel_id,
                   SUM(liters_sold) as liters_sold,
                   SUM(total_amount) as revenue,
                   AVG(price_per_liter) as avg_selling_price
            FROM sale WHERE sold_at >= :since GROUP BY fuel_id
        )
        SELECT
            f.id, f.name,
            COALESCE(fs.revenue, 0) as revenue,
            COALESCE(fs.liters_sold, 0) as liters_sold,
            COALESCE(fc.avg_cost_per_liter, 0) as avg_cost,
            COALESCE(fs.avg_selling_price, f.price) as selling_price,
            COALESCE(fs.revenue, 0) - (COALESCE(fs.liters_sold,0) * COALESCE(fc.avg_cost_per_liter,0)) as gross_profit
        FROM fuel f
        LEFT JOIN fuel_sales fs ON fs.fuel_id = f.id
        LEFT JOIN fuel_costs fc ON fc.fuel_id = f.id
    """)
    rows = session.execute(sql, {"since": since}).fetchall()

    result = []
    for r in rows:
        revenue = r[2]
        profit = r[6]
        margin_pct = (profit / revenue * 100) if revenue > 0 else 0
        result.append({
            "fuel_id": r[0],
            "fuel_name": r[1],
            "revenue": round(revenue, 2),
            "liters_sold": round(r[3], 2),
            "avg_cost_per_liter": round(r[4], 2),
            "avg_selling_price": round(r[5], 2),
            "gross_profit": round(profit, 2),
            "margin_percent": round(margin_pct, 2)
        })
    return result