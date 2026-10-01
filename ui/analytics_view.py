import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from agents.analytics_agent import get_sales_report
from agents.orchestrator import process_message


def render_analytics():
    st.title("📈 Analytics & Reports")
    st.caption("Deep dive into your sales performance")

    col1, col2 = st.columns([3, 1])
    with col1:
        period = st.selectbox("Report period", [7, 14, 30, 60, 90],
                              index=2, format_func=lambda x: f"Last {x} days")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        generate_report = st.button("🤖 Generate AI Report", type="primary", use_container_width=True)

    with st.spinner("Loading analytics..."):
        data = get_sales_report(days=period)

    # ── KPIs ────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Revenue", f"₹{data['total_revenue']:,.0f}",
                  delta=f"{data['revenue_growth_pct']:+.1f}% growth")
    with col2:
        st.metric("Total Orders", f"{data['total_orders']:,}")
    with col3:
        st.metric("Avg Order Value", f"₹{data['avg_order_value']:,.0f}")
    with col4:
        st.metric("Return Rate", f"{data['return_rate_pct']}%",
                  delta_color="inverse",
                  delta=f"{data['return_rate_pct']}%")

    st.divider()

    # ── Charts ───────────────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        daily = data.get("daily_revenue", {})
        if daily:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=list(daily.keys()),
                y=list(daily.values()),
                marker_color="#25D366",
                name="Revenue",
            ))
            fig.update_layout(
                title=f"Daily Revenue ({period}d)",
                height=280,
                margin=dict(l=0, r=0, t=40, b=0),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        amazon_rev = data["amazon_revenue"]
        flipkart_rev = data["flipkart_revenue"]
        fig2 = go.Figure(data=[go.Pie(
            labels=["Amazon.in", "Flipkart"],
            values=[amazon_rev, flipkart_rev],
            hole=0.5,
            marker_colors=["#FF9900", "#F7D000"],
        )])
        fig2.update_layout(
            title="Platform Revenue Split",
            height=280,
            margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Top Products & States ────────────────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("🏆 Top Products by Revenue")
        top = data.get("top_products", [])
        if top:
            for i, item in enumerate(top, 1):
                st.markdown(f"**{i}.** {item['name']} — ₹{item['revenue']:,.0f}")

    with col_r:
        st.subheader("📍 Top Customer States")
        states = data.get("top_states", [])
        if states:
            for s in states:
                st.markdown(f"📍 **{s['state']}** — {s['orders']} orders")

    st.divider()

    # ── AI Narrative Report ──────────────────────────────────────────────
    if generate_report:
        st.subheader("🤖 AI-Generated Business Report")
        with st.spinner("Generating your report..."):
            prompt = (
                f"Generate a concise but insightful business performance report for the last {period} days. "
                f"Here is the data: {data}. "
                f"Structure it as: 1) Headline summary, 2) Key wins, 3) Areas of concern, "
                f"4) Platform performance, 5) Top 3 actionable recommendations. "
                f"Use ₹ and Indian number format. Be specific and actionable."
            )
            report = process_message(prompt, [])
        st.markdown(report)
    elif "ai_report" in st.session_state:
        st.subheader("🤖 AI-Generated Business Report")
        st.markdown(st.session_state["ai_report"])
