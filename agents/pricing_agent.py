from database.db_manager import get_session, get_product_by_id, get_all_products, get_competitors_for_product
from config.settings import AMAZON_FEE_RATE, FLIPKART_FEE_RATE


def get_pricing_advice(product_id: int = None, product_name: str = None) -> dict:
    """Return pricing recommendations for one or all products."""
    session = get_session()
    try:
        if product_id:
            products = [get_product_by_id(session, product_id)]
        elif product_name:
            all_p = get_all_products(session)
            products = [p for p in all_p if product_name.lower() in p.name.lower()]
            if not products:
                products = all_p
        else:
            products = get_all_products(session)

        results = []
        for p in products:
            if not p:
                continue
            competitors = get_competitors_for_product(session, p.id)
            comp_prices = [c.price for c in competitors]
            avg_comp = round(sum(comp_prices) / len(comp_prices), 2) if comp_prices else None
            min_comp = min(comp_prices) if comp_prices else None
            max_comp = max(comp_prices) if comp_prices else None

            amazon_fee = round(p.amazon_price * AMAZON_FEE_RATE, 2)
            flipkart_fee = round(p.flipkart_price * FLIPKART_FEE_RATE, 2)

            amazon_margin = round(p.amazon_price - p.cost_price - amazon_fee, 2)
            amazon_margin_pct = round(amazon_margin / p.amazon_price * 100, 1)

            flipkart_margin = round(p.flipkart_price - p.cost_price - flipkart_fee, 2)
            flipkart_margin_pct = round(flipkart_margin / p.flipkart_price * 100, 1)

            # Recommend: undercut cheapest competitor by ₹50-100
            rec_price = round(min_comp - 75, -1) if min_comp else p.amazon_price

            results.append({
                "product_id": p.id,
                "name": p.name,
                "current_amazon_price": p.amazon_price,
                "current_flipkart_price": p.flipkart_price,
                "cost_price": p.cost_price,
                "amazon_fee": amazon_fee,
                "flipkart_fee": flipkart_fee,
                "amazon_margin": amazon_margin,
                "amazon_margin_pct": amazon_margin_pct,
                "flipkart_margin": flipkart_margin,
                "flipkart_margin_pct": flipkart_margin_pct,
                "competitor_avg_price": avg_comp,
                "competitor_min_price": min_comp,
                "competitor_max_price": max_comp,
                "recommended_price": rec_price,
                "competitors": [{"name": c.competitor_name, "price": c.price, "platform": c.platform} for c in competitors],
            })

        return {"pricing_data": results}
    finally:
        session.close()
