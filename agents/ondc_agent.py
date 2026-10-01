"""
ONDC Auto-Optimizer Agent
- Analyzes local demand trends from existing sales data
- Recommends optimal ONDC pricing (lower fees → competitive prices)
- Simulates ONDC product listing via Beckn protocol
"""
import json
import random
from datetime import datetime, timedelta
from groq import Groq
from config.settings import GROQ_API_KEY, AMAZON_FEE_RATE, ONDC_FEE_RATE, ONDC_FIXED_FEE
from database.db_manager import (
    get_session, get_all_products, get_orders_by_date_range,
    get_all_inventory, get_competitors_for_product
)
from collections import defaultdict

client = Groq(api_key=GROQ_API_KEY)

# ONDC Buyer Network Providers (BNPs) — real ones in India
ONDC_BUYER_NPS = [
    "PhonePe", "Meesho", "Magicpin", "Craftsvilla",
    "ONDC Reference App", "Mystore", "Shiprocket Commerce",
]


def analyze_demand(days_window: int = 30) -> dict:
    """
    Analyse demand patterns from sales data and score each product
    for ONDC listing opportunity.
    """
    session = get_session()
    try:
        products = get_all_products(session)
        orders_30 = get_orders_by_date_range(session, days=days_window)
        orders_7 = get_orders_by_date_range(session, days=7)
        orders_prev = get_orders_by_date_range(session, days=days_window * 2)

        # Revenue and velocity per product
        rev_30 = defaultdict(float)
        units_30 = defaultdict(int)
        rev_7 = defaultdict(float)
        state_demand = defaultdict(lambda: defaultdict(int))

        for o in orders_30:
            if o.status == "delivered":
                rev_30[o.product_id] += o.sale_price * o.quantity
                units_30[o.product_id] += o.quantity
                if o.customer_state:
                    state_demand[o.product_id][o.customer_state] += o.quantity

        for o in orders_7:
            if o.status == "delivered":
                rev_7[o.product_id] += o.sale_price * o.quantity

        cutoff_recent = datetime.now() - timedelta(days=days_window)
        rev_prev_only = defaultdict(float)
        units_prev = defaultdict(int)
        for o in orders_prev:
            if o.status == "delivered" and o.order_date < cutoff_recent:
                rev_prev_only[o.product_id] += o.sale_price * o.quantity
                units_prev[o.product_id] += o.quantity

        results = []
        for p in products:
            pid = p.id
            daily_units = units_30.get(pid, 0) / days_window
            weekly_rev = rev_7.get(pid, 0)
            monthly_rev = rev_30.get(pid, 0)

            # Growth momentum
            prev_rev = rev_prev_only.get(pid, monthly_rev * 0.8)
            growth_pct = round((monthly_rev - prev_rev) / max(prev_rev, 1) * 100, 1)

            # Demand score 0-100
            velocity_score = min(daily_units * 10, 40)
            growth_score = min(max(growth_pct / 2, 0), 30)
            revenue_score = min(monthly_rev / 5000, 30)
            demand_score = round(velocity_score + growth_score + revenue_score)

            # ONDC pricing: lower fees → pass savings to buyer
            amazon_price = p.amazon_price or 0
            ondc_fee = amazon_price * ONDC_FEE_RATE + ONDC_FIXED_FEE
            amazon_fee = amazon_price * AMAZON_FEE_RATE
            saving = amazon_fee - ondc_fee
            ondc_price = round(amazon_price - (saving * 0.5), -1)  # share 50% saving with buyer

            # Top states for this product
            top_states = sorted(
                state_demand[pid].items(), key=lambda x: x[1], reverse=True
            )[:3]

            results.append({
                "product_id": pid,
                "name": p.name,
                "sku": p.sku,
                "category": p.category,
                "amazon_price": amazon_price,
                "flipkart_price": p.flipkart_price,
                "cost_price": p.cost_price,
                "ondc_recommended_price": ondc_price,
                "ondc_fee_saving": round(saving, 2),
                "daily_units_sold": round(daily_units, 1),
                "monthly_revenue": round(monthly_rev, 2),
                "weekly_revenue": round(weekly_rev, 2),
                "growth_pct": growth_pct,
                "demand_score": demand_score,
                "top_states": [{"state": s, "units": u} for s, u in top_states],
                "ondc_listed": False,  # would be tracked in DB
            })

        results.sort(key=lambda x: x["demand_score"], reverse=True)

        return {
            "products": results,
            "total_products": len(results),
            "buyer_nps": random.sample(ONDC_BUYER_NPS, 5),
            "estimated_reach": random.randint(120000, 280000),
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        }
    finally:
        session.close()


def generate_ondc_listing(product_id: int) -> dict:
    """
    Generate an ONDC-optimised listing for a product.
    Uses AI to create Beckn-compatible product catalogue entry
    with demand-driven pricing.
    """
    session = get_session()
    try:
        from database.db_manager import get_product_by_id
        product = get_product_by_id(session, product_id)
        if not product:
            return {"error": "Product not found"}

        demand_data = analyze_demand()
        product_demand = next(
            (p for p in demand_data["products"] if p["product_id"] == product_id), {}
        )
        ondc_price = product_demand.get("ondc_recommended_price", product.amazon_price)

        prompt = f"""You are an ONDC (Open Network for Digital Commerce) product listing specialist for Indian e-commerce.

Create an optimised ONDC catalogue entry for this product. ONDC has lower fees, targets tier-2/3 India buyers.

Product: {product.name}
Category: {product.category}
Description: {product.description}
ONDC Price: ₹{ondc_price} (vs Amazon ₹{product.amazon_price})
Monthly sales: {product_demand.get('daily_units_sold', 2):.1f} units/day
Top customer states: {[s['state'] for s in product_demand.get('top_states', [])]}

Return JSON with:
{{
  "title": "ONDC-optimised title (60-80 chars)",
  "short_description": "2-sentence benefit-led description for tier-2 India buyers",
  "full_description": "150-word description highlighting value-for-money, local relevance",
  "usp": "Single strongest USP for Indian buyers",
  "search_tags": ["tag1", "tag2", ...8 tags],
  "demand_insight": "One sentence explaining why demand is strong in these regions",
  "pricing_rationale": "Why this ONDC price beats Amazon/Flipkart"
}}"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800,
        )

        raw = response.choices[0].message.content.strip()
        try:
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()
            listing = json.loads(raw)
        except Exception:
            listing = {"raw": raw}

        return {
            "product_id": product_id,
            "product_name": product.name,
            "ondc_price": ondc_price,
            "amazon_price": product.amazon_price,
            "price_advantage": round(product.amazon_price - ondc_price, 2),
            "listing": listing,
            "beckn_item_id": f"ONDC-{product.sku}-{datetime.now().strftime('%Y%m%d')}",
            "buyer_nps_reach": random.sample(ONDC_BUYER_NPS, 4),
            "status": "ready_to_list",
            "estimated_visibility_boost": f"{random.randint(25, 60)}%",
        }
    finally:
        session.close()
