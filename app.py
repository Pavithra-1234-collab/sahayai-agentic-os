import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="AI Business Manager",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ui.dashboard import render_dashboard
from ui.chat_interface import render_chat
from ui.product_manager import render_product_manager
from ui.reviews_view import render_reviews
from ui.analytics_view import render_analytics
from ui.whatsapp_ui import render_whatsapp

# ── Sidebar ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 AI Business Manager")
    st.markdown("*Your Amazon & Flipkart Co-pilot*")
    st.divider()

    page = st.radio(
        "Navigate",
        [
            "📊 Dashboard",
            "💬 Chat",
            "📦 Products",
            "⭐ Reviews",
            "📈 Analytics",
            "📱 WhatsApp",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    # Demo reset button
    if st.button("🔄 Reset Demo Data", use_container_width=True):
        with st.spinner("Reseeding demo data..."):
            from database.seed_data import seed
            seed()
        st.success("Demo data reset!")
        st.rerun()

    st.markdown("---")
    st.caption("Powered by Groq · LLaMA 3.3 70B")
    st.caption("Amazon.in + Flipkart")

# ── Page Routing ─────────────────────────────────────────────────────────
if page == "📊 Dashboard":
    render_dashboard()
elif page == "💬 Chat":
    render_chat()
elif page == "📦 Products":
    render_product_manager()
elif page == "⭐ Reviews":
    render_reviews()
elif page == "📈 Analytics":
    render_analytics()
elif page == "📱 WhatsApp":
    render_whatsapp()
