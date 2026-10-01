from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, Product, Inventory, Order, Review, Competitor, Alert
from config.settings import DB_URL
from datetime import datetime, timedelta

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()


# --- Products ---

def get_all_products(session):
    return session.query(Product).filter(Product.is_active == True).all()


def get_product_by_id(session, product_id):
    return session.query(Product).filter(Product.id == product_id).first()


# --- Inventory ---

def get_low_stock_products(session, threshold=None):
    from config.settings import LOW_STOCK_THRESHOLD
    t = threshold or LOW_STOCK_THRESHOLD
    results = (
        session.query(Product, Inventory)
        .join(Inventory, Product.id == Inventory.product_id)
        .filter(Inventory.stock_qty <= t)
        .filter(Product.is_active == True)
        .all()
    )
    return results


def get_all_inventory(session):
    return (
        session.query(Product, Inventory)
        .join(Inventory, Product.id == Inventory.product_id)
        .filter(Product.is_active == True)
        .all()
    )


# --- Orders ---

def get_orders_by_date_range(session, days=30):
    since = datetime.utcnow() - timedelta(days=days)
    return session.query(Order).filter(Order.order_date >= since).all()


def get_revenue_summary(session, days=30):
    since = datetime.utcnow() - timedelta(days=days)
    orders = session.query(Order).filter(
        Order.order_date >= since,
        Order.status == "delivered"
    ).all()

    total_revenue = sum(o.sale_price * o.quantity for o in orders)
    total_orders = len(orders)
    amazon_rev = sum(o.sale_price * o.quantity for o in orders if o.platform == "amazon")
    flipkart_rev = sum(o.sale_price * o.quantity for o in orders if o.platform == "flipkart")

    return {
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "amazon_revenue": round(amazon_rev, 2),
        "flipkart_revenue": round(flipkart_rev, 2),
        "avg_order_value": round(total_revenue / total_orders, 2) if total_orders else 0,
    }


def get_top_products(session, days=30, limit=5):
    since = datetime.utcnow() - timedelta(days=days)
    orders = session.query(Order).filter(
        Order.order_date >= since,
        Order.status == "delivered"
    ).all()

    product_rev = {}
    for o in orders:
        product_rev[o.product_id] = product_rev.get(o.product_id, 0) + o.sale_price * o.quantity

    sorted_prods = sorted(product_rev.items(), key=lambda x: x[1], reverse=True)[:limit]
    result = []
    for pid, rev in sorted_prods:
        p = get_product_by_id(session, pid)
        if p:
            result.append({"product": p, "revenue": round(rev, 2)})
    return result


def get_daily_revenue(session, days=30):
    since = datetime.utcnow() - timedelta(days=days)
    orders = session.query(Order).filter(
        Order.order_date >= since,
        Order.status == "delivered"
    ).all()

    daily = {}
    for o in orders:
        day = o.order_date.date().isoformat()
        daily[day] = daily.get(day, 0) + o.sale_price * o.quantity

    return dict(sorted(daily.items()))


# --- Reviews ---

def get_recent_reviews(session, days=30, product_id=None):
    since = datetime.utcnow() - timedelta(days=days)
    q = session.query(Review).filter(Review.review_date >= since)
    if product_id:
        q = q.filter(Review.product_id == product_id)
    return q.order_by(Review.review_date.desc()).all()


def get_review_summary(session, days=30):
    reviews = get_recent_reviews(session, days)
    if not reviews:
        return {"avg_rating": 0, "total": 0, "positive": 0, "neutral": 0, "negative": 0}

    ratings = [r.rating for r in reviews]
    return {
        "avg_rating": round(sum(ratings) / len(ratings), 1),
        "total": len(reviews),
        "positive": sum(1 for r in ratings if r >= 4),
        "neutral": sum(1 for r in ratings if r == 3),
        "negative": sum(1 for r in ratings if r <= 2),
    }


# --- Competitors ---

def get_competitors_for_product(session, product_id):
    return session.query(Competitor).filter(Competitor.product_id == product_id).all()


# --- Alerts ---

def get_active_alerts(session):
    return session.query(Alert).filter(Alert.resolved == False).order_by(Alert.created_at.desc()).all()


def resolve_alert(session, alert_id):
    alert = session.query(Alert).filter(Alert.id == alert_id).first()
    if alert:
        alert.resolved = True
        session.commit()


def save_response_to_review(session, review_id, response_text):
    review = session.query(Review).filter(Review.id == review_id).first()
    if review:
        review.responded = True
        review.response_text = response_text
        session.commit()
