from database.db_manager import get_session, get_low_stock_products, get_all_inventory, get_orders_by_date_range
from collections import defaultdict


def check_inventory(threshold: int = 15) -> dict:
    """Return inventory status with low-stock alerts."""
    session = get_session()
    try:
        all_inv = get_all_inventory(session)
        low_stock = get_low_stock_products(session, threshold)
        orders_30 = get_orders_by_date_range(session, days=30)

        # Avg daily sales per product
        daily_sales = defaultdict(float)
        for o in orders_30:
            if o.status == "delivered":
                daily_sales[o.product_id] += o.quantity / 30

        inventory_list = []
        for product, inv in all_inv:
            avg_daily = round(daily_sales.get(product.id, 0.1), 2)
            days_left = int(inv.stock_qty / avg_daily) if avg_daily > 0 else 999
            status = "ok"
            if inv.stock_qty == 0:
                status = "out_of_stock"
            elif inv.stock_qty <= inv.reorder_threshold // 2:
                status = "critical"
            elif inv.stock_qty <= inv.reorder_threshold:
                status = "low"

            inventory_list.append({
                "product_id": product.id,
                "name": product.name,
                "sku": product.sku,
                "stock_qty": inv.stock_qty,
                "reorder_threshold": inv.reorder_threshold,
                "avg_daily_sales": avg_daily,
                "days_until_stockout": days_left,
                "status": status,
            })

        low_items = [i for i in inventory_list if i["status"] in ("critical", "low", "out_of_stock")]

        return {
            "inventory": inventory_list,
            "low_stock_items": low_items,
            "summary": f"{len(low_items)} items need attention out of {len(inventory_list)} total products.",
        }
    finally:
        session.close()
