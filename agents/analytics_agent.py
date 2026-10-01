from database.db_manager import (
    get_session, get_revenue_summary, get_top_products,
    get_daily_revenue, get_orders_by_date_range, get_all_products
)
from collections import defaultdict


def get_sales_report(days: int = 30) -> dict:
    """Return comprehensive sales analytics."""
    session = get_session()
    try:
        current = get_revenue_summary(session, days)
        previous = get_revenue_summary(session, days * 2)

        prev_only_rev = previous["total_revenue"] - current["total_revenue"]
        prev_only_orders = previous["total_orders"] - current["total_orders"]

        revenue_growth = 0
        if prev_only_rev > 0:
            revenue_growth = round((current["total_revenue"] - prev_only_rev) / prev_only_rev * 100, 1)

        top_products = get_top_products(session, days)
        daily_rev = get_daily_revenue(session, days)
        orders = get_orders_by_date_range(session, days)

        # State breakdown
        state_orders = defaultdict(int)
        for o in orders:
            if o.status == "delivered" and o.customer_state:
                state_orders[o.customer_state] += 1
        top_states = sorted(state_orders.items(), key=lambda x: x[1], reverse=True)[:5]

        # Return rate
        total = len(orders)
        returns = sum(1 for o in orders if o.status == "returned")
        return_rate = round(returns / total * 100, 1) if total else 0

        return {
            "period_days": days,
            "total_revenue": current["total_revenue"],
            "total_orders": current["total_orders"],
            "amazon_revenue": current["amazon_revenue"],
            "flipkart_revenue": current["flipkart_revenue"],
            "avg_order_value": current["avg_order_value"],
            "revenue_growth_pct": revenue_growth,
            "return_rate_pct": return_rate,
            "top_products": [
                {"name": t["product"].name, "revenue": t["revenue"]}
                for t in top_products
            ],
            "daily_revenue": daily_rev,
            "top_states": [{"state": s, "orders": n} for s, n in top_states],
        }
    finally:
        session.close()
