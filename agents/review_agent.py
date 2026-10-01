from database.db_manager import get_session, get_recent_reviews, get_review_summary
from collections import Counter


def analyze_reviews(days: int = 30, product_id: int = None) -> dict:
    """Analyse recent reviews for sentiment patterns."""
    session = get_session()
    try:
        reviews = get_recent_reviews(session, days, product_id)
        summary = get_review_summary(session, days)

        # Find common complaint patterns
        complaint_keywords = ["shipping", "delay", "quality", "damage", "return", "fake", "wrong"]
        complaint_counts = Counter()
        negative_reviews = []

        for r in reviews:
            if r.rating <= 2:
                text_lower = r.review_text.lower()
                for kw in complaint_keywords:
                    if kw in text_lower:
                        complaint_counts[kw] += 1
                product_name = r.product.name if r.product else "Unknown"
                negative_reviews.append({
                    "id": r.id,
                    "product": product_name,
                    "rating": r.rating,
                    "text": r.review_text,
                    "reviewer": r.reviewer_name,
                    "date": r.review_date.strftime("%d %b %Y") if r.review_date else "",
                    "platform": r.platform,
                    "responded": r.responded,
                })

        top_complaints = complaint_counts.most_common(3)

        recent_sample = []
        for r in reviews[:10]:
            product_name = r.product.name if r.product else "Unknown"
            recent_sample.append({
                "id": r.id,
                "product": product_name,
                "rating": r.rating,
                "text": r.review_text,
                "reviewer": r.reviewer_name,
                "platform": r.platform,
                "responded": r.responded,
            })

        return {
            "summary": summary,
            "top_complaints": [{"issue": kw, "count": cnt} for kw, cnt in top_complaints],
            "negative_reviews": negative_reviews,
            "recent_reviews": recent_sample,
            "period_days": days,
        }
    finally:
        session.close()
