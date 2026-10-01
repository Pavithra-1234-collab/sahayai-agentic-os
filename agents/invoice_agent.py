"""
Smart Invoicing & Financing Agent
- OCR via Groq vision (llama-3.2-11b-vision-preview)
- Simulated GSTN e-Invoice (IRP) upload
- Simulated TReDS Invoice Discounting
- UPI payment request generation
"""
import json
import base64
import random
import string
import hashlib
from datetime import datetime, timedelta
from groq import Groq
from config.settings import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)
VISION_MODEL = "llama-3.2-11b-vision-preview"

# ── OCR ───────────────────────────────────────────────────────────────────

def scan_invoice(image_b64: str, mime_type: str = "image/jpeg") -> dict:
    """
    Extract structured invoice data from an image using Groq vision.
    Returns a parsed invoice dict ready for GSTN filing.
    """
    prompt = """You are an expert Indian invoice data extractor. Analyze this invoice image and extract ALL details.
Return ONLY a valid JSON object with these exact keys (use null if not found):
{
  "invoice_number": "",
  "invoice_date": "YYYY-MM-DD",
  "due_date": "YYYY-MM-DD",
  "seller_name": "",
  "seller_gstin": "",
  "seller_address": "",
  "buyer_name": "",
  "buyer_gstin": "",
  "buyer_address": "",
  "line_items": [
    {"description": "", "hsn_code": "", "quantity": 0, "unit": "", "rate": 0, "amount": 0, "gst_rate": 0}
  ],
  "subtotal": 0,
  "cgst": 0,
  "sgst": 0,
  "igst": 0,
  "total_gst": 0,
  "total_amount": 0,
  "payment_terms": "",
  "bank_account": "",
  "ifsc": "",
  "upi_id": ""
}
If this is not an invoice, return {"error": "Not an invoice image"}."""

    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}},
                {"type": "text", "text": prompt},
            ],
        }],
        temperature=0.1,
        max_tokens=1500,
    )

    raw = response.choices[0].message.content.strip()
    # Extract JSON from response
    try:
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        data = json.loads(raw)
    except Exception:
        # If parsing fails, return the raw text with a flag
        data = {"error": "Could not parse invoice", "raw_text": raw}

    if "error" not in data:
        data["scan_timestamp"] = datetime.now().isoformat()
        data["status"] = "scanned"

    return data


# ── GSTN e-Invoice ────────────────────────────────────────────────────────

def _generate_irn(invoice_data: dict) -> str:
    """Generate a realistic 64-char IRN (Invoice Reference Number)."""
    gstin = invoice_data.get("seller_gstin", "DEMO01") or "DEMO01"
    inv_no = invoice_data.get("invoice_number", "INV001") or "INV001"
    date = invoice_data.get("invoice_date", datetime.now().strftime("%Y-%m-%d")) or ""
    seed = f"{gstin}{inv_no}{date}"
    return hashlib.sha256(seed.encode()).hexdigest()


def file_to_gstn(invoice_data: dict) -> dict:
    """
    Simulate filing an invoice to GSTN IRP (Invoice Registration Portal).
    In production: POST to https://einvoice1.gst.gov.in/EInvoice/OtherOpr
    Returns IRN, acknowledgement number, and signed QR data.
    """
    irn = _generate_irn(invoice_data)
    ack_no = "".join(random.choices(string.digits, k=15))
    ack_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # Simulate e-way bill generation if value > 50,000
    total = invoice_data.get("total_amount", 0) or 0
    eway_bill = None
    if total > 50000:
        eway_bill = {
            "number": "EWB" + "".join(random.choices(string.digits, k=12)),
            "valid_till": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        }

    return {
        "success": True,
        "irn": irn,
        "ack_no": ack_no,
        "ack_date": ack_date,
        "signed_invoice": f"eyJhbGciOiJSUzI1NiJ9...{irn[:20]}",  # simulated JWT
        "eway_bill": eway_bill,
        "qr_data": f"IRN:{irn}|AckNo:{ack_no}|AckDt:{ack_date}",
        "status": "gstn_filed",
        "message": "e-Invoice successfully generated and registered on GSTN IRP",
    }


# ── TReDS Invoice Discounting ─────────────────────────────────────────────

FINANCIERS = [
    {"name": "State Bank of India", "rate": 8.5, "platform": "RXIL"},
    {"name": "HDFC Bank", "rate": 9.2, "platform": "M1Xchange"},
    {"name": "Axis Bank", "rate": 9.8, "platform": "NTREBIA"},
    {"name": "ICICI Bank", "rate": 10.1, "platform": "RXIL"},
    {"name": "Kotak Mahindra Bank", "rate": 9.5, "platform": "M1Xchange"},
]


def get_treds_offer(invoice_data: dict, irn: str) -> dict:
    """
    Simulate TReDS (Trade Receivables Discounting System) financing offer.
    TReDS is RBI-regulated: RXIL, M1Xchange, NTREBIA.
    Returns available financing offers sorted by discount rate.
    """
    total = invoice_data.get("total_amount", 0) or 0
    due_date_str = invoice_data.get("due_date")

    # Calculate payment tenor
    if due_date_str:
        try:
            due = datetime.strptime(due_date_str, "%Y-%m-%d")
            tenor_days = max(15, (due - datetime.now()).days)
        except Exception:
            tenor_days = 45
    else:
        tenor_days = 45

    offers = []
    for fin in FINANCIERS:
        # Financing amount: 90-95% of invoice value
        advance_rate = random.uniform(0.90, 0.95)
        advance_amount = round(total * advance_rate, 2)

        # Discount cost = principal × rate × (tenor/365)
        discount_cost = round(advance_amount * (fin["rate"] / 100) * (tenor_days / 365), 2)
        net_proceed = round(advance_amount - discount_cost, 2)

        offers.append({
            "financier": fin["name"],
            "platform": fin["platform"],
            "annual_rate_pct": fin["rate"],
            "advance_rate_pct": round(advance_rate * 100, 1),
            "advance_amount": advance_amount,
            "discount_cost": discount_cost,
            "net_proceeds": net_proceed,
            "tenor_days": tenor_days,
            "maturity_date": (datetime.now() + timedelta(days=tenor_days)).strftime("%Y-%m-%d"),
        })

    # Sort by best net proceeds
    offers.sort(key=lambda x: x["net_proceeds"], reverse=True)

    return {
        "irn": irn,
        "invoice_amount": total,
        "invoice_number": invoice_data.get("invoice_number"),
        "buyer": invoice_data.get("buyer_name"),
        "offers": offers,
        "best_offer": offers[0] if offers else None,
        "status": "offers_received",
        "message": f"{len(offers)} financiers have bid on your invoice on TReDS",
    }


# ── UPI Payment Request ───────────────────────────────────────────────────

def generate_payment_request(
    amount: float,
    payee_name: str,
    upi_id: str,
    note: str = "",
    invoice_number: str = "",
) -> dict:
    """Generate a UPI deep link and payment request details."""
    note_str = note or f"Invoice {invoice_number}" if invoice_number else "Business Payment"
    upi_link = f"upi://pay?pa={upi_id}&pn={payee_name.replace(' ', '%20')}&am={amount:.2f}&tn={note_str.replace(' ', '%20')}&cu=INR"

    return {
        "upi_link": upi_link,
        "amount": amount,
        "payee_name": payee_name,
        "upi_id": upi_id,
        "note": note_str,
        "invoice_number": invoice_number,
        "whatsapp_message": (
            f"🧾 *Payment Request*\n\n"
            f"Amount: *₹{amount:,.2f}*\n"
            f"To: {payee_name}\n"
            f"Invoice: {invoice_number}\n\n"
            f"Pay via UPI: `{upi_id}`\n"
            f"Or click: {upi_link}\n\n"
            f"_Powered by AI Business Manager_"
        ),
        "created_at": datetime.now().isoformat(),
    }


# ── Demo invoice for testing without real image ───────────────────────────

DEMO_INVOICE = {
    "invoice_number": "INV/2026/0342",
    "invoice_date": "2026-03-15",
    "due_date": "2026-04-14",
    "seller_name": "TechSupplies India Pvt Ltd",
    "seller_gstin": "27AABCT1234M1ZX",
    "seller_address": "14, MIDC Industrial Area, Pune, Maharashtra 411019",
    "buyer_name": "My Business Store",
    "buyer_gstin": "29AADCB1234N1ZS",
    "buyer_address": "12, Rajaji Nagar, Bengaluru, Karnataka 560010",
    "line_items": [
        {"description": "Bluetooth Speaker (SWP-001)", "hsn_code": "8518", "quantity": 50, "unit": "PCS", "rate": 1100, "amount": 55000, "gst_rate": 18},
        {"description": "USB Hub 7-Port (USB-003)", "hsn_code": "8471", "quantity": 30, "unit": "PCS", "rate": 320, "amount": 9600, "gst_rate": 18},
        {"description": "GaN Charger 65W (GAN-006)", "hsn_code": "8504", "quantity": 20, "unit": "PCS", "rate": 410, "amount": 8200, "gst_rate": 18},
    ],
    "subtotal": 72800,
    "cgst": 6552,
    "sgst": 6552,
    "igst": 0,
    "total_gst": 13104,
    "total_amount": 85904,
    "payment_terms": "Net 30 days",
    "bank_account": "00112233445566",
    "ifsc": "SBIN0001234",
    "upi_id": "techsupplies@sbi",
    "scan_timestamp": datetime.now().isoformat(),
    "status": "scanned",
}
