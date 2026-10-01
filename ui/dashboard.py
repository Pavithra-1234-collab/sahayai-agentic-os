import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from database.db_manager import (
    get_session, get_revenue_summary, get_top_products,
    get_daily_revenue, get_active_alerts, get_all_products
)
from agents.analytics_agent import get_sales_report
from agents.inventory_agent import check_inventory


def render_dashboard():
    st.title("📊 Business Dashboard")

    session = get_session()

    try:
        summary_30 = get_revenue_summary(session, 30)
        summary_7 = get_revenue_summary(session, 7)
        summary_prev_30 = get_revenue_summary(session, 60)
        alerts = get_active_alerts(session)
        products = get_all_products(session)

        prev_rev = summary_prev_30["total_revenue"] - summary_30["total_revenue"]
        rev_delta = round(summary_30["total_revenue"] - prev_rev, 0)
        rev_delta_pct = round(rev_delta / prev_rev * 100, 1) if prev_rev else 0

        # ── KPI Cards ──────────────────────────────────────────────────
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            rev = summary_30["total_revenue"]
            st.metric(
                "Revenue (30 days)",
                f"₹{rev:,.0f}",
                delta=f"{rev_delta_pct:+.1f}% vs prev 30d",
            )

        with col2:
            st.metric(
                "Orders (30 days)",
                f"{summary_30['total_orders']:,}",
                delta=f"₹{summary_30['avg_order_value']:,.0f} avg value",
            )

        with col3:
            st.metric("Active Products", len(products))

        with col4:
            urgent = sum(1 for a in alerts if a.severity == "urgent")
            st.metric(
                "Active Alerts",
                len(alerts),
                delta=f"{urgent} urgent" if urgent else "All clear",
                delta_color="inverse",
            )

        st.divider()

        # ── Charts ─────────────────────────────────────────────────────
        col_left, col_right = st.columns([2, 1])

        with col_left:
            daily_rev = get_daily_revenue(session, 30)
            if daily_rev:
                dates = list(daily_rev.keys())
                values = list(daily_rev.values())
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=dates, y=values,
                    mode="lines+markers",
                    fill="tozeroy",
                    line=dict(color="#25D366", width=2),
                    fillcolor="rgba(37, 211, 102, 0.1)",
                    name="Revenue",
                ))
                fig.update_layout(
                    title="Daily Revenue — Last 30 Days",
                    xaxis_title="Date",
                    yaxis_title="Revenue (₹)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=300,
                    margin=dict(l=0, r=0, t=40, b=0),
                )
                st.plotly_chart(fig, use_container_width=True)

        with col_right:
            amazon_rev = summary_30["amazon_revenue"]
            flipkart_rev = summary_30["flipkart_revenue"]
            fig2 = go.Figure(data=[go.Pie(
                labels=["Amazon", "Flipkart"],
                values=[amazon_rev, flipkart_rev],
                hole=0.5,
                marker_colors=["#FF9900", "#F7D000"],
            )])
            fig2.update_layout(
                title="Platform Split",
                height=300,
                margin=dict(l=0, r=0, t=40, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig2, use_container_width=True)

        # ── Top Products ───────────────────────────────────────────────
        st.subheader("🏆 Top Products (Last 30 Days)")
        top = get_top_products(session, 30, 5)
        if top:
            names = [t["product"].name for t in top]
            revs = [t["revenue"] for t in top]
            fig3 = px.bar(
                x=revs, y=names,
                orientation="h",
                color=revs,
                color_continuous_scale=["#128C7E", "#25D366"],
                labels={"x": "Revenue (₹)", "y": ""},
            )
            fig3.update_layout(
                height=250, showlegend=False,
                margin=dict(l=0, r=0, t=10, b=0),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig3, use_container_width=True)

        st.divider()

        # ── Proactive AI Insights ──────────────────────────────────────
        st.subheader("🤖 AI Insights")

        with st.spinner("Analysing your business..."):
            inv_data = check_inventory()
            low_items = inv_data.get("low_stock_items", [])

        insights = []

        for item in low_items:
            if item["status"] == "critical":
                insights.append(("🔴", f"**{item['name']}** has only **{item['stock_qty']} units** left — will run out in ~{item['days_until_stockout']} days at current sales pace. Reorder now!"))
            elif item["status"] == "low":
                insights.append(("🟡", f"**{item['name']}** is running low ({item['stock_qty']} units). Consider reordering."))

        amazon_share = round(amazon_rev / (amazon_rev + flipkart_rev) * 100) if (amazon_rev + flipkart_rev) else 0
        if amazon_share > 55:
            insights.append(("📈", f"Amazon drives **{amazon_share}%** of your revenue. Focus your ad spend there for maximum ROI."))

        if rev_delta_pct > 10:
            insights.append(("🚀", f"Revenue grew **{rev_delta_pct:.1f}%** vs the previous 30 days. You're on a strong growth trajectory!"))
        elif rev_delta_pct < -5:
            insights.append(("⚠️", f"Revenue dropped **{abs(rev_delta_pct):.1f}%** vs previous period. Check pricing and inventory."))

        insights.append(("💡", "Festival season is coming — consider stocking up 30% extra for Diwali and Amazon Great Indian Festival."))

        if insights:
            for icon, text in insights:
                st.info(f"{icon} {text}")
        else:
            st.success("✅ Everything looks good! No urgent issues detected.")

        # ── Active Alerts ──────────────────────────────────────────────
        if alerts:
            st.subheader("🚨 Active Alerts")
            for alert in alerts[:5]:
                severity_color = {
                    "urgent": "error", "high": "warning",
                    "medium": "info", "low": "info"
                }.get(alert.severity, "info")
                getattr(st, severity_color)(f"**{alert.severity.upper()}**: {alert.message}")

    finally:
        session.close()
