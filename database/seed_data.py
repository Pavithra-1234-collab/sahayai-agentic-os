"""
Deterministic mock data generator for the AI Business Manager demo.
Run: python database/seed_data.py
"""
import random
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
from database.models import Base, Product, Inventory, Order, Review, Competitor, Alert
from database.db_manager import engine, SessionLocal, init_db

random.seed(42)

PRODUCTS = [
    {
        "name": "SoundWave Pro Bluetooth Speaker",
        "sku": "SWP-001",
        "category": "Electronics",
        "cost_price": 1200,
        "amazon_price": 2499,
        "flipkart_price": 2399,
        "description": "Portable wireless speaker with 20W output and 12-hour battery",
    },
    {
        "name": "AirPods Pro Clone Earbuds",
        "sku": "APE-002",
        "category": "Electronics",
        "cost_price": 600,
        "amazon_price": 1499,
        "flipkart_price": 1399,
        "description": "True wireless earbuds with ANC and 24-hour total battery life",
    },
    {
        "name": "7-Port USB 3.0 Hub",
        "sku": "USB-003",
        "category": "Electronics",
        "cost_price": 350,
        "amazon_price": 899,
        "flipkart_price": 849,
        "description": "Powered USB hub with 7 ports and fast charging support",
    },
    {
        "name": "Stainless Steel Water Bottle 1L",
        "sku": "SSB-004",
        "category": "Home & Kitchen",
        "cost_price": 220,
        "amazon_price": 599,
        "flipkart_price": 549,
        "description": "Double-wall insulated bottle, keeps cold 24h / hot 12h",
    },
    {
        "name": "Adjustable Phone & Tablet Stand",
        "sku": "PTS-005",
        "category": "Accessories",
        "cost_price": 150,
        "amazon_price": 449,
        "flipkart_price": 399,
        "description": "Foldable aluminum desk stand with 270° adjustable angle",
    },
    {
        "name": "Fast Charge 65W GaN Charger",
        "sku": "GAN-006",
        "category": "Electronics",
        "cost_price": 450,
        "amazon_price": 1199,
        "flipkart_price": 1099,
        "description": "3-port GaN charger: 2x USB-C + 1x USB-A, supports 65W PD",
    },
]

# Competitor data: slightly above our prices (room to raise)
COMPETITORS = {
    "SWP-001": [
        ("TechSound India", 2799), ("AudioMax", 2699), ("BeatBlast", 2599),
    ],
    "APE-002": [
        ("SoundGear", 1699), ("TrueSound India", 1599), ("BudPro", 1549),
    ],
    "USB-003": [
        ("HubMaster", 999), ("PortKing", 949), ("UltraHub", 929),
    ],
    "SSB-004": [
        ("HydroFlask India", 799), ("MiltonPro", 699), ("AquaElite", 649),
    ],
    "PTS-005": [
        ("GripMaster", 549), ("DeskPal", 499), ("FlexiStand", 479),
    ],
    "GAN-006": [
        ("ChargeMax", 1399), ("PowerGaN", 1299), ("TurboCharge", 1249),
    ],
}

# Inventory: 2-3 products intentionally low
INVENTORY = {
    "SWP-001": (4, 15),    # LOW — below threshold
    "APE-002": (47, 15),
    "USB-003": (2, 10),    # CRITICAL
    "SSB-004": (83, 20),
    "PTS-005": (8, 10),    # LOW
    "GAN-006": (31, 15),
}

INDIAN_STATES = [
    "Maharashtra", "Karnataka", "Delhi", "Tamil Nadu", "Gujarat",
    "Rajasthan", "Uttar Pradesh", "West Bengal", "Telangana", "Kerala",
]

POSITIVE_REVIEWS = [
    "Absolutely love this product! Works exactly as described. Fast delivery too.",
    "Great value for money. Build quality is excellent and performance is top notch.",
    "Highly recommended! My whole family is happy with the purchase.",
    "Superb product. Packaging was great. Will definitely buy again.",
    "Exceeded my expectations. The quality is premium for this price range.",
    "Very happy with this purchase. 5 stars well deserved!",
    "Perfect product. Works flawlessly. Customer service was also helpful.",
    "Amazing quality! Bought two of these already. Friends loved it too.",
]

NEUTRAL_REVIEWS = [
    "Product is okay. Does the job but nothing special. Delivery was fast.",
    "Average product. Works as described but quality could be better.",
    "Decent for the price. Not the best but not the worst either.",
]

NEGATIVE_REVIEWS = [
    "Shipping was very slow, took 10 days to arrive. Product is okay though.",
    "Delivery was delayed by a week. Very disappointed with the shipping time.",
    "Product quality is not as shown in images. Return process was also difficult.",
    "Shipping took too long. Expected in 2 days but received after 8 days.",
    "Quality is below average. Packaging was damaged when it arrived.",
]

REVIEWER_NAMES = [
    "Rajesh Kumar", "Priya Sharma", "Amit Singh", "Sunita Patel", "Vikram Nair",
    "Deepa Menon", "Arjun Reddy", "Kavitha Iyer", "Rohit Gupta", "Ananya Das",
    "Suresh Joshi", "Meena Krishnan", "Aakash Verma", "Pooja Mehta", "Nikhil Rao",
]


def generate_orders(session, products):
    """Generate 90 days of orders with realistic patterns."""
    orders = []
    now = datetime.utcnow()

    for product in products:
        # Base daily order rate — higher for popular items
        base_rates = {
            "SWP-001": 4, "APE-002": 3, "USB-003": 2,
            "SSB-004": 5, "PTS-005": 3, "GAN-006": 2,
        }
        base = base_rates.get(product.sku, 2)

        for day_offset in range(90, 0, -1):
            date = now - timedelta(days=day_offset)

            # Growth trend: last 30 days ~20% more orders
            growth_factor = 1.2 if day_offset <= 30 else 1.0

            # Weekend boost (Fri/Sat/Sun)
            day_of_week = date.weekday()
            weekend_boost = 1.5 if day_of_week >= 4 else 1.0

            # Festival spike: simulate a sale event ~2 weeks ago (within current period)
            festival_boost = 2.5 if 10 <= day_offset <= 18 else 1.0

            expected = base * growth_factor * weekend_boost * festival_boost
            num_orders = max(0, int(random.gauss(expected, 0.8)))

            for _ in range(num_orders):
                platform = random.choices(["amazon", "flipkart"], weights=[60, 40])[0]
                price = product.amazon_price if platform == "amazon" else product.flipkart_price
                # Small price variation
                price = price * random.uniform(0.97, 1.03)
                status = random.choices(
                    ["delivered", "returned", "cancelled"],
                    weights=[88, 8, 4]
                )[0]

                order = Order(
                    product_id=product.id,
                    platform=platform,
                    quantity=random.choices([1, 2, 3], weights=[75, 20, 5])[0],
                    sale_price=round(price, 2),
                    order_date=date + timedelta(
                        hours=random.randint(6, 22),
                        minutes=random.randint(0, 59)
                    ),
                    status=status,
                    customer_state=random.choice(INDIAN_STATES),
                )
                orders.append(order)

    session.add_all(orders)
    session.commit()
    print(f"  Created {len(orders)} orders")


def generate_reviews(session, products):
    """Generate mixed reviews with patterns."""
    reviews = []
    now = datetime.utcnow()

    for product in products:
        num_reviews = random.randint(18, 30)
        for i in range(num_reviews):
            # 70% positive, 20% neutral, 10% negative
            category = random.choices(
                ["positive", "neutral", "negative"],
                weights=[70, 20, 10]
            )[0]

            if category == "positive":
                rating = random.choices([5, 4], weights=[65, 35])[0]
                text = random.choice(POSITIVE_REVIEWS)
            elif category == "neutral":
                rating = 3
                text = random.choice(NEUTRAL_REVIEWS)
            else:
                rating = random.choices([2, 1], weights=[60, 40])[0]
                text = random.choice(NEGATIVE_REVIEWS)

            reviews.append(Review(
                product_id=product.id,
                platform=random.choice(["amazon", "flipkart"]),
                rating=rating,
                review_text=text,
                reviewer_name=random.choice(REVIEWER_NAMES),
                review_date=now - timedelta(days=random.randint(0, 60)),
                responded=False,
            ))

    session.add_all(reviews)
    session.commit()
    print(f"  Created {len(reviews)} reviews")


def generate_alerts(session, products_by_sku):
    """Generate active alerts for low-stock products."""
    alerts = []
    low_sku_messages = {
        "SWP-001": ("low_stock", "SoundWave Pro Bluetooth Speaker has only 4 units left. At current sales velocity, stock will run out in ~2 days.", "urgent"),
        "USB-003": ("low_stock", "7-Port USB 3.0 Hub has only 2 units left. Consider reordering immediately.", "urgent"),
        "PTS-005": ("low_stock", "Adjustable Phone Stand has only 8 units left — below reorder threshold.", "high"),
    }

    for sku, (alert_type, msg, severity) in low_sku_messages.items():
        product = products_by_sku.get(sku)
        alerts.append(Alert(
            type=alert_type,
            product_id=product.id if product else None,
            message=msg,
            severity=severity,
            created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 12)),
            resolved=False,
        ))

    # Add a pricing opportunity alert
    p = products_by_sku.get("SWP-001")
    alerts.append(Alert(
        type="pricing_opportunity",
        product_id=p.id if p else None,
        message="Competitors average ₹2,699 for similar Bluetooth speakers. You're at ₹2,499 — potential to increase price by ₹150-200.",
        severity="medium",
        created_at=datetime.utcnow() - timedelta(hours=3),
        resolved=False,
    ))

    session.add_all(alerts)
    session.commit()
    print(f"  Created {len(alerts)} alerts")


def seed():
    print("Initialising database...")
    init_db()

    session = SessionLocal()

    # Clear existing data
    for model in [Alert, Review, Competitor, Order, Inventory, Product]:
        session.query(model).delete()
    session.commit()

    print("Seeding products...")
    products = []
    products_by_sku = {}
    for p_data in PRODUCTS:
        p = Product(**p_data)
        session.add(p)
        products.append(p)
    session.commit()
    for p in products:
        products_by_sku[p.sku] = p
    print(f"  Created {len(products)} products")

    print("Seeding inventory...")
    for p in products:
        qty, threshold = INVENTORY.get(p.sku, (50, 10))
        session.add(Inventory(
            product_id=p.id,
            stock_qty=qty,
            reorder_threshold=threshold,
            last_updated=datetime.utcnow(),
        ))
    session.commit()

    print("Seeding competitors...")
    for p in products:
        for comp_name, price in COMPETITORS.get(p.sku, []):
            session.add(Competitor(
                product_id=p.id,
                competitor_name=comp_name,
                platform=random.choice(["amazon", "flipkart"]),
                price=price,
                snapshot_date=datetime.utcnow() - timedelta(hours=random.randint(1, 48)),
            ))
    session.commit()

    print("Seeding orders...")
    generate_orders(session, products)

    print("Seeding reviews...")
    generate_reviews(session, products)

    print("Seeding alerts...")
    generate_alerts(session, products_by_sku)

    session.close()
    print("\nDatabase seeded successfully!")


if __name__ == "__main__":
    seed()
