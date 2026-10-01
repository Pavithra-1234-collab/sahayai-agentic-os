import streamlit as st
import json
from database.db_manager import get_session, get_all_products, get_all_inventory
from agents.listing_agent import create_listing


def render_product_manager():
    st.title("📦 Product Manager")
    st.caption("Manage your Amazon & Flipkart product listings")

    session = get_session()
    try:
        products_inv = get_all_inventory(session)

        if not products_inv:
            st.info("No products found. Run seed_data.py first.")
            return

        # Product table
        st.subheader("Your Products")

        for product, inv in products_inv:
            with st.expander(f"**{product.name}** — SKU: {product.sku}", expanded=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Amazon Price", f"₹{product.amazon_price:,.0f}")
                    st.metric("Cost Price", f"₹{product.cost_price:,.0f}")
                with col2:
                    st.metric("Flipkart Price", f"₹{product.flipkart_price:,.0f}")
                    margin = round((product.amazon_price - product.cost_price * 1.18) / product.amazon_price * 100, 1)
                    st.metric("Est. Margin", f"{margin}%")
                with col3:
                    stock_color = "🔴" if inv.stock_qty <= 5 else ("🟡" if inv.stock_qty <= 10 else "🟢")
                    st.metric("Stock", f"{stock_color} {inv.stock_qty} units")
                    platforms = []
                    if product.amazon_price:
                        platforms.append("🟠 Amazon")
                    if product.flipkart_price:
                        platforms.append("🟡 Flipkart")
                    st.markdown("**Platforms:** " + "  ".join(platforms))

                st.markdown(f"*{product.description}*")

                # Listing optimiser
                st.markdown("---")
                if st.button(f"✨ Optimise Listing", key=f"list_{product.id}", type="primary"):
                    with st.spinner(f"Generating optimised listing for {product.name}..."):
                        listing = create_listing(
                            product_name=product.name,
                            category=product.category,
                            cost_price=product.cost_price,
                        )
                    _render_listing(listing, product.name)

    finally:
        session.close()

    # ── Custom Listing Generator ──────────────────────────────────────
    st.divider()
    st.subheader("✍️ Create New Listing")
    st.caption("Generate an optimised listing for any product")

    with st.form("new_listing_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_product_name = st.text_input("Product Name", placeholder="e.g. Wireless Gaming Mouse")
            new_category = st.selectbox(
                "Category",
                ["Electronics", "Home & Kitchen", "Accessories", "Sports & Outdoors", "Fashion", "Other"],
            )
        with col2:
            new_features = st.text_area(
                "Key Features",
                placeholder="e.g. RGB lighting, 7 buttons, 16000 DPI, ergonomic design",
                height=100,
            )
            new_cost = st.number_input("Cost Price (₹)", min_value=0, value=0)

        submitted = st.form_submit_button("🚀 Generate Listing", type="primary", use_container_width=True)

    if submitted and new_product_name:
        with st.spinner("Creating your optimised listing..."):
            listing = create_listing(
                product_name=new_product_name,
                category=new_category,
                features=new_features,
                cost_price=new_cost,
            )
        _render_listing(listing, new_product_name)


def _render_listing(listing: dict, product_name: str):
    st.success(f"✅ Listing generated for **{product_name}**!")

    if "raw" in listing and listing.get("raw"):
        st.markdown("### Generated Listing")
        st.markdown(listing["raw"])
        return

    tab1, tab2, tab3 = st.tabs(["🟠 Amazon Listing", "🟡 Flipkart Listing", "🔍 SEO Keywords"])

    with tab1:
        amazon = listing.get("amazon", {})
        if amazon:
            st.markdown("**Title:**")
            st.info(amazon.get("title", ""))
            st.markdown("**Bullet Points:**")
            for bp in amazon.get("bullet_points", []):
                st.markdown(f"• {bp}")
            st.markdown("**Description:**")
            st.text_area("", amazon.get("description", ""), height=150, key="amz_desc", disabled=True)
            if amazon.get("backend_keywords"):
                st.markdown("**Backend Keywords:**")
                st.code(amazon.get("backend_keywords", ""), language=None)
        else:
            st.info("Amazon listing not generated.")

    with tab2:
        flipkart = listing.get("flipkart", {})
        if flipkart:
            st.markdown("**Title:**")
            st.info(flipkart.get("title", ""))
            st.markdown("**Highlights:**")
            for h in flipkart.get("highlights", []):
                st.markdown(f"• {h}")
            st.markdown("**Description:**")
            st.text_area("", flipkart.get("description", ""), height=150, key="fk_desc", disabled=True)
        else:
            st.info("Flipkart listing not generated.")

    with tab3:
        keywords = listing.get("seo_keywords", [])
        if keywords:
            cols = st.columns(3)
            for i, kw in enumerate(keywords):
                with cols[i % 3]:
                    st.markdown(f"🏷️ `{kw}`")
        else:
            st.info("No keywords generated.")
