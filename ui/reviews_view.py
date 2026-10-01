import streamlit as st
from database.db_manager import get_session, get_recent_reviews, get_review_summary, save_response_to_review
from agents.orchestrator import process_message


def render_reviews():
    st.title("⭐ Reviews & Reputation")
    st.caption("Monitor customer sentiment and draft professional responses")

    session = get_session()
    try:
        days = st.selectbox("Time period", [7, 14, 30, 60], index=2, format_func=lambda x: f"Last {x} days")
        summary = get_review_summary(session, days)

        # ── Summary Cards ───────────────────────────────────────────────
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            rating = summary["avg_rating"]
            emoji = "🌟" if rating >= 4.5 else ("⭐" if rating >= 3.5 else "⚠️")
            st.metric("Avg Rating", f"{emoji} {rating}/5")
        with col2:
            st.metric("Total Reviews", summary["total"])
        with col3:
            st.metric("Positive (4-5★)", summary["positive"], delta=None)
        with col4:
            st.metric("Neutral (3★)", summary["neutral"])
        with col5:
            pct_neg = round(summary["negative"] / summary["total"] * 100) if summary["total"] else 0
            st.metric("Negative (1-2★)", summary["negative"], delta=f"{pct_neg}%", delta_color="inverse")

        st.divider()

        # ── Sentiment bar ───────────────────────────────────────────────
        total = summary["total"]
        if total > 0:
            pos_pct = round(summary["positive"] / total * 100)
            neu_pct = round(summary["neutral"] / total * 100)
            neg_pct = 100 - pos_pct - neu_pct

            st.markdown("**Sentiment breakdown:**")
            bar_html = f"""
            <div style="display:flex;border-radius:8px;overflow:hidden;height:24px;margin-bottom:12px;">
              <div style="width:{pos_pct}%;background:#25D366;"></div>
              <div style="width:{neu_pct}%;background:#FFC107;"></div>
              <div style="width:{neg_pct}%;background:#FF4444;"></div>
            </div>
            <div style="display:flex;gap:16px;font-size:13px;">
              <span>🟢 Positive {pos_pct}%</span>
              <span>🟡 Neutral {neu_pct}%</span>
              <span>🔴 Negative {neg_pct}%</span>
            </div>
            """
            st.markdown(bar_html, unsafe_allow_html=True)

        st.divider()

        # ── Reviews List ────────────────────────────────────────────────
        reviews = get_recent_reviews(session, days)

        filter_opt = st.radio("Filter", ["All", "Negative only", "Needs response"], horizontal=True)

        filtered = reviews
        if filter_opt == "Negative only":
            filtered = [r for r in reviews if r.rating <= 2]
        elif filter_opt == "Needs response":
            filtered = [r for r in reviews if not r.responded and r.rating <= 3]

        if not filtered:
            st.info("No reviews matching the filter.")
        else:
            for review in filtered:
                _render_review_card(review, session)

    finally:
        session.close()


def _render_review_card(review, session):
    stars = "⭐" * review.rating + "☆" * (5 - review.rating)
    border_color = "#25D366" if review.rating >= 4 else ("#FFC107" if review.rating == 3 else "#FF4444")
    product_name = review.product.name if review.product else "Unknown"
    platform_badge = "🟠 Amazon" if review.platform == "amazon" else "🟡 Flipkart"
    date_str = review.review_date.strftime("%d %b %Y") if review.review_date else ""

    with st.container():
        st.markdown(
            f"""<div style="border-left:4px solid {border_color};padding:10px 14px;
            border-radius:4px;background:rgba(0,0,0,0.03);margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
              <strong>{review.reviewer_name}</strong>
              <span style="font-size:12px;color:#888;">{platform_badge} · {date_str}</span>
            </div>
            <div>{stars} · <em>{product_name}</em></div>
            <div style="margin-top:6px;">{review.review_text}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        if review.responded and review.response_text:
            with st.expander("✅ Response sent"):
                st.markdown(f"*{review.response_text}*")
        elif review.rating <= 3:
            if st.button(f"📝 Draft Response", key=f"draft_{review.id}", type="secondary"):
                with st.spinner("Drafting response..."):
                    prompt = (
                        f"Draft a professional seller response for this customer review on {review.platform}:\n"
                        f"Product: {product_name}\nRating: {review.rating}/5\nReview: {review.review_text}\n\n"
                        f"Write a short, empathetic, professional response (2-3 sentences). "
                        f"Address the specific complaint and offer resolution. Sign off as 'Team [Business Name]'."
                    )
                    response_text = process_message(prompt, [])

                save_response_to_review(session, review.id, response_text)
                st.success("Response drafted and saved!")
                st.markdown(f"**Draft:** {response_text}")
