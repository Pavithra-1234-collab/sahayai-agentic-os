"""
Report Agent — builds a styled HTML report from live business data.
Called by the orchestrator's generate_report tool.
"""
import random
import string
from datetime import datetime

from agents.analytics_agent import get_sales_report
from agents.inventory_agent import check_inventory
from agents.review_agent import analyze_reviews
from agents.ondc_agent import analyze_demand
from agents.invoice_agent import file_to_gstn, get_treds_offer, DEMO_INVOICE
from utils.report_cache import CACHE

ALL_SECTIONS = ["sales", "inventory", "reviews", "ondc", "payments"]


def _fmtinr(n):
    try:
        return f"₹{int(n):,}".replace(",", ",")
    except Exception:
        return f"₹{n}"


def _fmt(n):
    try:
        return f"{int(n):,}"
    except Exception:
        return str(n)


def _build_html(data: dict, sections: list, days: int) -> str:
    d = data
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")

    def sales_sec():
        s = d.get("sales", {})
        top = s.get("top_products", [])
        rows = "".join(
            f"<tr><td>{i+1}</td><td>{p.get('product',{}).get('name','—')}</td>"
            f"<td>{_fmtinr(p.get('revenue',0))}</td><td>{p.get('units',0)}</td></tr>"
            for i, p in enumerate(top[:5])
        )
        g = s.get("growth_pct", 0)
        g_cls = "green" if g >= 0 else "red"
        return f"""
<section>
  <h2>📊 Sales Report — Last {days} Days</h2>
  <div class="grid">
    <div class="card"><div class="label">Total Revenue</div><div class="val green">{_fmtinr(s.get('total_revenue',0))}</div></div>
    <div class="card"><div class="label">Total Orders</div><div class="val">{_fmt(s.get('total_orders',0))}</div></div>
    <div class="card"><div class="label">Avg Order Value</div><div class="val">{_fmtinr(s.get('avg_order_value',0))}</div></div>
    <div class="card"><div class="label">Growth</div><div class="val {g_cls}">{g}%</div></div>
    <div class="card"><div class="label">Amazon Revenue</div><div class="val">{_fmtinr(s.get('amazon_revenue',0))}</div></div>
    <div class="card"><div class="label">Flipkart Revenue</div><div class="val">{_fmtinr(s.get('flipkart_revenue',0))}</div></div>
  </div>
  {"<h3>Top Products</h3><table><tr><th>#</th><th>Product</th><th>Revenue</th><th>Units</th></tr>" + rows + "</table>" if rows else ""}
</section>"""

    def inventory_sec():
        inv = d.get("inventory", {})
        low = inv.get("low_stock_items", [])
        rows = "".join(
            f"<tr><td>{p.get('name','—')}</td><td>{p.get('stock_qty',0)}</td>"
            f"<td>{p.get('reorder_threshold',0)}</td>"
            f"<td>{p.get('days_until_stockout','—')}</td>"
            f"<td><span class=\"badge {'red' if p.get('status')=='critical' else 'orange'}\">{p.get('status','—')}</span></td></tr>"
            for p in low
        )
        alert = f'<div class="callout orange">⚠️ {len(low)} products below reorder threshold. Immediate action recommended.</div>' if low else '<div class="callout green">✅ All products are adequately stocked.</div>'
        return f"""
<section>
  <h2>📦 Inventory Status</h2>
  <div class="grid">
    <div class="card"><div class="label">Total Products</div><div class="val">{inv.get('total_products',0)}</div></div>
    <div class="card"><div class="label">Total Units</div><div class="val">{_fmt(inv.get('total_units',0))}</div></div>
    <div class="card"><div class="label">Low Stock</div><div class="val red">{inv.get('low_stock_count',0)}</div></div>
  </div>
  {alert}
  {"<h3>Low Stock Items</h3><table><tr><th>Product</th><th>Stock</th><th>Threshold</th><th>Days Left</th><th>Status</th></tr>" + rows + "</table>" if rows else ""}
</section>"""

    def reviews_sec():
        r = d.get("reviews", {})
        neg = r.get("recent_negative", [])
        rows = "".join(
            f"<tr><td>{x.get('product_name','—')}</td><td>{x.get('rating',0)}/5</td>"
            f"<td>{(x.get('review_text','') or '')[:90]}…</td><td>{x.get('platform','—')}</td></tr>"
            for x in neg[:5]
        )
        raw_complaints = r.get("top_complaints", [])
        # top_complaints can be list of strings OR list of dicts {issue, count}
        if raw_complaints and isinstance(raw_complaints[0], dict):
            complaints_text = " · ".join(c.get("issue", str(c)) for c in raw_complaints)
        else:
            complaints_text = " · ".join(str(c) for c in raw_complaints)
        complaint_html = f'<div class="callout orange"><strong>Top Complaints:</strong> {complaints_text}</div>' if raw_complaints else ""
        return f"""
<section>
  <h2>⭐ Customer Reviews</h2>
  <div class="grid">
    <div class="card"><div class="label">Avg Rating</div><div class="val green">{r.get('avg_rating',0)} / 5</div></div>
    <div class="card"><div class="label">Total Reviews</div><div class="val">{r.get('total_reviews',0)}</div></div>
    <div class="card"><div class="label">Positive</div><div class="val green">{r.get('positive_count',0)}</div></div>
    <div class="card"><div class="label">Negative</div><div class="val red">{r.get('negative_count',0)}</div></div>
  </div>
  {complaint_html}
  {"<h3>Recent Negative Reviews</h3><table><tr><th>Product</th><th>Rating</th><th>Review</th><th>Platform</th></tr>" + rows + "</table>" if rows else ""}
</section>"""

    def ondc_sec():
        o = d.get("ondc", {})
        prods = o.get("top_products", [])
        rows = "".join(
            f"<tr><td>{p.get('name','—')}</td><td><strong>{p.get('demand_score',0)}</strong>/100</td>"
            f"<td>{_fmtinr(p.get('amazon_price',0))}</td><td class=\"green\">{_fmtinr(p.get('ondc_recommended_price',0))}</td>"
            f"<td>{_fmtinr(p.get('ondc_fee_saving',0))}/unit</td>"
            f"<td class=\"{'green' if p.get('growth_pct',0)>=0 else 'red'}\">{p.get('growth_pct',0)}%</td></tr>"
            for p in prods
        )
        nps = ", ".join(o.get("buyer_nps", []))
        return f"""
<section>
  <h2>🌐 ONDC Opportunity</h2>
  <div class="grid">
    <div class="card"><div class="label">Products Analysed</div><div class="val">{o.get('total_products',0)}</div></div>
    <div class="card"><div class="label">Estimated Reach</div><div class="val green">{_fmt(o.get('estimated_reach',0))}</div></div>
    <div class="card"><div class="label">Buyer Networks</div><div class="val">{len(o.get('buyer_nps',[]))}</div></div>
    <div class="card"><div class="label">ONDC Fee vs Amazon</div><div class="val green">~5% vs ~12%</div></div>
  </div>
  <div class="callout green">ONDC's lower fee structure (3–8% + ₹1.5/order) vs Amazon/Flipkart (5–20%) enables significant margin savings, allowing competitive pricing while protecting profitability.</div>
  {"<h3>Top Products for ONDC</h3><table><tr><th>Product</th><th>Demand</th><th>Amazon</th><th>ONDC</th><th>Fee Saving</th><th>Growth</th></tr>" + rows + "</table>" if rows else ""}
  {f'<p class="muted">Active buyer networks: {nps}</p>' if nps else ""}
</section>"""

    def payments_sec():
        inv = d.get("invoice", {})
        demo = inv.get("demo_invoice", {})
        gstn = inv.get("gstn", {})
        best = inv.get("treds_best_offer") or {}
        irn = gstn.get("irn", "")
        return f"""
<section>
  <h2>🧾 Invoicing &amp; Financing</h2>
  <div class="grid">
    <div class="card"><div class="label">Invoice</div><div class="val">{demo.get('number','—')}</div></div>
    <div class="card"><div class="label">Invoice Amount</div><div class="val">{_fmtinr(demo.get('amount',0))}</div></div>
    <div class="card"><div class="label">e-Invoice Status</div><div class="val green">✓ GSTN Filed</div></div>
    <div class="card"><div class="label">Ack No.</div><div class="val">{gstn.get('ack_no','—')}</div></div>
  </div>
  {"" if not best else f'''
  <h3>Best TReDS Financing Offer</h3>
  <div class="callout green">
    <strong>{best.get("financier","—")}</strong> via {best.get("platform","—")} —
    {best.get("annual_rate_pct",0)}% p.a. ·
    Advance: {_fmtinr(best.get("advance_amount",0))} ({best.get("advance_rate_pct",0)}%) ·
    Net proceeds: <strong>{_fmtinr(best.get("net_proceeds",0))}</strong> ·
    Tenor: {best.get("tenor_days",0)} days
  </div>'''}
  <p class="muted">IRN: <code>{irn[:32]}…</code></p>
</section>"""

    sec_map = {
        "sales": sales_sec,
        "inventory": inventory_sec,
        "reviews": reviews_sec,
        "ondc": ondc_sec,
        "payments": payments_sec,
    }
    body = "\n".join(sec_map[s]() for s in sections if s in sec_map)
    ai_summary = d.get("ai_summary", "")
    ai_block = f'<div class="ai-summary"><div class="ai-title">🤖 AI Executive Summary</div>{ai_summary}</div>' if ai_summary else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Business Report — {now}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#0a0a0a;color:#e4e4e7;line-height:1.6;padding:40px 24px;max-width:960px;margin:0 auto}}
.header{{border-bottom:1px solid #27272a;padding-bottom:24px;margin-bottom:32px}}
.header h1{{font-size:28px;font-weight:800;color:#fff}}
.header p{{color:#71717a;font-size:13px;margin-top:4px}}
.logo{{display:inline-flex;align-items:center;gap:8px;background:#25D366;color:#fff;font-weight:700;font-size:14px;padding:6px 14px;border-radius:20px;margin-bottom:16px}}
section{{margin-bottom:40px}}
h2{{font-size:18px;font-weight:700;color:#fff;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid #27272a}}
h3{{font-size:14px;font-weight:600;color:#a1a1aa;margin:16px 0 8px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px;margin-bottom:16px}}
.card{{background:#18181b;border:1px solid #27272a;border-radius:12px;padding:14px}}
.label{{font-size:11px;color:#71717a;margin-bottom:4px;text-transform:uppercase;letter-spacing:.05em}}
.val{{font-size:20px;font-weight:700;color:#fff}}
.val.green{{color:#4ade80}}.val.red{{color:#f87171}}
table{{width:100%;border-collapse:collapse;font-size:13px;margin-bottom:16px}}
th{{text-align:left;padding:8px 12px;background:#18181b;color:#71717a;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.05em;border-bottom:1px solid #27272a}}
td{{padding:10px 12px;border-bottom:1px solid #1f1f23;color:#d4d4d8}}
td.green{{color:#4ade80;font-weight:600}}td.red{{color:#f87171}}
tr:last-child td{{border-bottom:none}}
.badge{{display:inline-block;padding:2px 8px;border-radius:20px;font-size:10px;font-weight:600;text-transform:uppercase}}
.badge.red{{background:rgba(248,113,113,.15);color:#f87171;border:1px solid rgba(248,113,113,.3)}}
.badge.orange{{background:rgba(251,146,60,.15);color:#fb923c;border:1px solid rgba(251,146,60,.3)}}
.callout{{border-radius:10px;padding:14px 16px;font-size:13px;margin-bottom:16px}}
.callout.green{{background:rgba(37,211,102,.08);border:1px solid rgba(37,211,102,.25);color:#86efac}}
.callout.orange{{background:rgba(251,146,60,.08);border:1px solid rgba(251,146,60,.25);color:#fdba74}}
.ai-summary{{background:#18181b;border:1px solid #27272a;border-radius:16px;padding:24px;margin-bottom:40px;white-space:pre-wrap;font-size:14px;color:#d4d4d8;line-height:1.8}}
.ai-title{{font-size:12px;color:#25D366;font-weight:700;text-transform:uppercase;letter-spacing:.1em;margin-bottom:12px}}
.muted{{font-size:12px;color:#52525b;margin-top:8px}}
code{{font-family:monospace;font-size:11px;color:#71717a}}
footer{{margin-top:48px;padding-top:24px;border-top:1px solid #27272a;text-align:center;font-size:11px;color:#3f3f46}}
@media print{{body{{background:#fff;color:#111}}.card{{background:#f5f5f5;border-color:#e5e5e5}}}}
</style>
</head>
<body>
<div class="header">
  <div class="logo">BizManager AI</div>
  <h1>Business Performance Report</h1>
  <p>Generated on {now} · Last {days} days · Amazon.in + Flipkart + ONDC</p>
</div>
{ai_block}
{body}
<footer>Powered by AI Business Manager · Groq LLaMA 3.3 70B · Sarvam AI · ONDC · TReDS</footer>
</body>
</html>"""


def build_and_cache_report(days: int = 30, sections: list = None) -> dict:
    """
    Gather data, generate HTML report, cache it, return metadata.
    """
    if sections is None:
        sections = ALL_SECTIONS

    # Gather data
    sales = get_sales_report(days=days)
    inventory = check_inventory()
    reviews = analyze_reviews(days=days)
    ondc_data = analyze_demand(days_window=days)
    gstn = file_to_gstn(DEMO_INVOICE)
    treds = get_treds_offer(DEMO_INVOICE, gstn["irn"])

    # AI executive summary
    from groq import Groq
    from config.settings import GROQ_API_KEY, GROQ_MODEL
    client = Groq(api_key=GROQ_API_KEY)
    top_prod = ondc_data["products"][0]["name"] if ondc_data.get("products") else "N/A"
    best_fin = treds["best_offer"]["financier"] if treds.get("best_offer") else "N/A"
    prompt = (
        f"Write a concise 3-paragraph executive summary for an Indian e-commerce seller (last {days} days).\n"
        f"Revenue: ₹{sales.get('total_revenue',0):,.0f}, Orders: {sales.get('total_orders',0)}, Growth: {sales.get('growth_pct',0)}%\n"
        f"Inventory: {len(inventory.get('low_stock_items',[]))} low-stock items\n"
        f"Reviews: avg {reviews.get('avg_rating',0)}/5, {reviews.get('total_reviews',0)} reviews\n"
        f"ONDC top opportunity: {top_prod}, best TReDS offer: {best_fin}\n\n"
        f"Para 1: Business health. Para 2: Key opportunities. Para 3: 3 action items."
    )
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=400,
    )
    ai_summary = resp.choices[0].message.content.strip()

    data = {
        "days": days,
        "ai_summary": ai_summary,
        "sales": sales,
        "inventory": inventory,
        "reviews": reviews,
        "ondc": {
            "total_products": ondc_data["total_products"],
            "estimated_reach": ondc_data["estimated_reach"],
            "buyer_nps": ondc_data["buyer_nps"],
            "top_products": ondc_data["products"][:3],
        },
        "invoice": {
            "demo_invoice": {
                "number": DEMO_INVOICE["invoice_number"],
                "amount": DEMO_INVOICE["total_amount"],
            },
            "gstn": {"irn": gstn["irn"], "ack_no": gstn["ack_no"]},
            "treds_best_offer": treds["best_offer"],
        },
    }

    html = _build_html(data, sections, days)
    report_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
    filename = f"bizreport-{datetime.now().strftime('%Y-%m-%d')}.html"
    CACHE[report_id] = {"html": html, "filename": filename}

    return {
        "report_id": report_id,
        "filename": filename,
        "days": days,
        "sections": sections,
        "pages": len(sections),
    }
