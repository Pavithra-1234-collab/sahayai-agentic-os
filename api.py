import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import json
from collections import defaultdict

from agents.orchestrator import process_message
import re as _re
from agents.inventory_agent import check_inventory
from agents.analytics_agent import get_sales_report
from agents.pricing_agent import get_pricing_advice
from agents.review_agent import analyze_reviews
from agents.listing_agent import create_listing
from agents.invoice_agent import scan_invoice, file_to_gstn, get_treds_offer, DEMO_INVOICE
from agents.ondc_agent import analyze_demand, generate_ondc_listing
from database.db_manager import (
    get_session, get_active_alerts, get_all_products,
    get_all_inventory, get_revenue_summary, save_response_to_review
)

app = FastAPI(title="AI Business Manager API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []

class ListingRequest(BaseModel):
    product_name: str
    category: str = ""
    features: str = ""
    cost_price: float = 0

class ReviewResponseRequest(BaseModel):
    review_id: int
    response_text: str


# ── Chat ─────────────────────────────────────────────────────────────────

@app.post("/api/chat")
def chat(req: ChatRequest):
    try:
        raw = process_message(req.message, req.history)
    except Exception as e:
        return {"response": f"Sorry, I ran into an error: {str(e)}", "report": None}
    # Extract optional [REPORT:id:filename] marker
    report_meta = None
    m = _re.search(r'\[REPORT:([^:]+):([^\]]+)\]', raw)
    if m:
        report_meta = {"report_id": m.group(1), "filename": m.group(2)}
        raw = raw[:m.start()].rstrip()
    return {"response": raw, "report": report_meta}


# In-memory audio cache for TTS voice note replies  {id -> mp3_bytes}
_audio_cache: dict = {}

@app.get("/api/audio/{audio_id}")
def serve_audio(audio_id: str):
    from fastapi.responses import Response as FResp
    mp3 = _audio_cache.get(audio_id)
    if not mp3:
        raise HTTPException(status_code=404, detail="Audio not found")
    return FResp(content=mp3, media_type="audio/mpeg")


@app.get("/api/report/temp/{report_id}")
def serve_temp_report(report_id: str):
    from utils.report_cache import CACHE
    from fastapi.responses import HTMLResponse
    entry = CACHE.get(report_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Report not found or expired")
    return HTMLResponse(content=entry["html"], media_type="text/html")


# ── Dashboard ────────────────────────────────────────────────────────────

@app.get("/api/dashboard")
def dashboard():
    session = get_session()
    try:
        summary_30 = get_revenue_summary(session, 30)
        summary_60 = get_revenue_summary(session, 60)
        alerts = get_active_alerts(session)
        products = get_all_products(session)

        prev_rev = summary_60["total_revenue"] - summary_30["total_revenue"]
        rev_growth = round(
            (summary_30["total_revenue"] - prev_rev) / prev_rev * 100, 1
        ) if prev_rev else 0

        from database.db_manager import get_daily_revenue, get_top_products
        daily_rev = get_daily_revenue(session, 30)
        top_products = get_top_products(session, 30, 5)

        inv_data = check_inventory()

        return {
            "metrics": {
                "total_revenue": summary_30["total_revenue"],
                "total_orders": summary_30["total_orders"],
                "avg_order_value": summary_30["avg_order_value"],
                "amazon_revenue": summary_30["amazon_revenue"],
                "flipkart_revenue": summary_30["flipkart_revenue"],
                "revenue_growth_pct": rev_growth,
                "active_products": len(products),
                "active_alerts": len(alerts),
                "urgent_alerts": sum(1 for a in alerts if a.severity == "urgent"),
            },
            "daily_revenue": [
                {"date": d, "revenue": round(v, 0)}
                for d, v in daily_rev.items()
            ],
            "top_products": [
                {"name": t["product"].name, "revenue": t["revenue"]}
                for t in top_products
            ],
            "alerts": [
                {
                    "id": a.id,
                    "type": a.type,
                    "message": a.message,
                    "severity": a.severity,
                }
                for a in alerts[:5]
            ],
            "low_stock": inv_data.get("low_stock_items", []),
        }
    finally:
        session.close()


# ── Voice (Sarvam STT → AI → Sarvam Translate → Sarvam TTS) ─────────────

@app.post("/api/voice/chat")
async def voice_chat(audio: UploadFile = File(...), history: str = "[]"):
    """
    Full voice pipeline:
    1. Sarvam STT  → transcript + detected language
    2. AI Orchestrator → English response
    3. Sarvam Translate → native-language response
    4. Sarvam TTS → MP3 audio (base64)
    """
    from utils.sarvam import transcribe_audio, translate_text, synthesize_speech, LANGUAGE_NAMES
    from config.settings import SARVAM_API_KEY

    if not SARVAM_API_KEY or SARVAM_API_KEY == "your_sarvam_api_key_here":
        raise HTTPException(status_code=400, detail="SARVAM_API_KEY not configured in .env")

    audio_bytes = await audio.read()
    filename = audio.filename or "audio.webm"

    # 1. Speech → Text (auto-detect language)
    try:
        stt = transcribe_audio(audio_bytes, filename)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Sarvam STT error: {e}")

    transcript = stt.get("transcript", "").strip()
    lang = stt.get("language_code") or "hi-IN"

    if not transcript:
        raise HTTPException(status_code=422, detail="Could not transcribe audio. Please speak clearly and try again.")

    # 2. AI processing (English)
    try:
        hist = json.loads(history)
    except Exception:
        hist = []

    ai_response = process_message(transcript, hist)

    # 3. Translate to detected language (skip if English or unsupported)
    native_response = ai_response
    if lang and lang != "en-IN":
        try:
            native_response = translate_text(ai_response, "en-IN", lang)
        except Exception:
            native_response = ai_response  # graceful fallback to English

    # 4. Text → Speech
    try:
        audio_b64 = synthesize_speech(native_response, lang)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Sarvam TTS error: {e}")

    return {
        "transcript": transcript,
        "language_code": lang,
        "language_name": LANGUAGE_NAMES.get(lang, lang),
        "response_english": ai_response,
        "response_native": native_response,
        "audio_base64": audio_b64,
    }


# ── Inventory ─────────────────────────────────────────────────────────────

@app.get("/api/inventory")
def inventory():
    return check_inventory()


# ── Products ──────────────────────────────────────────────────────────────

@app.get("/api/products")
def products():
    session = get_session()
    try:
        items = get_all_inventory(session)
        return {
            "products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "sku": p.sku,
                    "category": p.category,
                    "cost_price": p.cost_price,
                    "amazon_price": p.amazon_price,
                    "flipkart_price": p.flipkart_price,
                    "description": p.description,
                    "stock_qty": inv.stock_qty,
                    "reorder_threshold": inv.reorder_threshold,
                }
                for p, inv in items
            ]
        }
    finally:
        session.close()


# ── Listing generation ────────────────────────────────────────────────────

@app.post("/api/listing")
def listing(req: ListingRequest):
    result = create_listing(
        product_name=req.product_name,
        category=req.category,
        features=req.features,
        cost_price=req.cost_price,
    )
    return result


# ── Pricing ───────────────────────────────────────────────────────────────

@app.get("/api/pricing")
def pricing(product_name: Optional[str] = None, product_id: Optional[int] = None):
    return get_pricing_advice(product_id=product_id, product_name=product_name)


# ── Reviews ───────────────────────────────────────────────────────────────

@app.get("/api/reviews")
def reviews(days: int = 30):
    return analyze_reviews(days=days)


@app.post("/api/reviews/respond")
def respond_to_review(req: ReviewResponseRequest):
    session = get_session()
    try:
        save_response_to_review(session, req.review_id, req.response_text)
        return {"success": True}
    finally:
        session.close()

@app.post("/api/reviews/draft")
def draft_review_response(body: dict):
    product = body.get("product", "")
    rating = body.get("rating", 1)
    review_text = body.get("review_text", "")
    platform = body.get("platform", "")
    prompt = (
        f"Draft a professional seller response for this customer review on {platform}:\n"
        f"Product: {product}\nRating: {rating}/5\nReview: {review_text}\n\n"
        f"Write a short, empathetic, professional response (2-3 sentences). "
        f"Address the specific complaint and offer resolution. Sign off as 'Team BizManager'."
    )
    response = process_message(prompt, [])
    return {"response": response}


# ── Analytics ─────────────────────────────────────────────────────────────

@app.get("/api/analytics")
def analytics(days: int = 30):
    return get_sales_report(days=days)

@app.post("/api/analytics/report")
def generate_report(body: dict):
    days = body.get("days", 30)
    data = get_sales_report(days=days)
    prompt = (
        f"Generate a concise but insightful business performance report for the last {days} days. "
        f"Data: {json.dumps(data, default=str)}. "
        f"Structure: 1) Headline summary, 2) Key wins, 3) Areas of concern, "
        f"4) Platform performance (Amazon vs Flipkart), 5) Top 3 recommendations. "
        f"Use ₹ and Indian number format. Be specific and actionable."
    )
    report = process_message(prompt, [])
    return {"report": report}


# ── Invoice & Financing ───────────────────────────────────────────────────

@app.get("/api/invoice/demo")
def invoice_demo():
    """Return the pre-built demo invoice for testing."""
    return DEMO_INVOICE

@app.post("/api/invoice/scan")
async def invoice_scan(image: UploadFile = File(...)):
    """OCR an invoice image using Groq vision."""
    import base64
    raw = await image.read()
    b64 = base64.b64encode(raw).decode()
    mime = image.content_type or "image/jpeg"
    return scan_invoice(b64, mime)

@app.post("/api/invoice/gstn")
def invoice_gstn(invoice_data: dict):
    """Simulate filing invoice to GSTN IRP."""
    return file_to_gstn(invoice_data)

@app.post("/api/invoice/treds")
def invoice_treds(body: dict):
    """Get TReDS discounting offers for an invoice."""
    invoice_data = body.get("invoice_data", {})
    irn = body.get("irn", "")
    return get_treds_offer(invoice_data, irn)


# ── Full Business Report ──────────────────────────────────────────────────

@app.get("/api/report/full")
def full_report(days: int = 30):
    """Aggregate data from all modules for the downloadable report."""
    from agents.inventory_agent import check_inventory
    from agents.analytics_agent import get_sales_report
    from agents.review_agent import analyze_reviews
    from agents.ondc_agent import analyze_demand
    from agents.invoice_agent import file_to_gstn, get_treds_offer, DEMO_INVOICE

    sales = get_sales_report(days=days)
    inventory = check_inventory()
    reviews = analyze_reviews(days=days)
    ondc = analyze_demand(days_window=days)
    gstn = file_to_gstn(DEMO_INVOICE)
    treds = get_treds_offer(DEMO_INVOICE, gstn["irn"])

    # AI executive summary
    prompt = (
        f"You are an AI business analyst. Write a concise 3-paragraph executive summary for an Indian e-commerce seller. "
        f"Data (last {days} days):\n"
        f"Sales: total_revenue=₹{sales.get('total_revenue',0):,.0f}, orders={sales.get('total_orders',0)}, "
        f"growth={sales.get('growth_pct',0)}%, top_product={sales.get('top_products',[{}])[0].get('product',{}).get('name','') if sales.get('top_products') else 'N/A'}.\n"
        f"Inventory: {len(inventory.get('low_stock_items',[]))} low-stock items.\n"
        f"Reviews: avg_rating={reviews.get('avg_rating',0)}, total={reviews.get('total_reviews',0)}, "
        f"positive={reviews.get('positive_count',0)}, negative={reviews.get('negative_count',0)}.\n"
        f"ONDC: top_opportunity={ondc['products'][0]['name'] if ondc.get('products') else 'N/A'}, "
        f"demand_score={ondc['products'][0]['demand_score'] if ondc.get('products') else 0}, "
        f"fee_saving=₹{ondc['products'][0]['ondc_fee_saving'] if ondc.get('products') else 0}/unit.\n"
        f"Invoice financing: best_offer={treds['best_offer']['financier'] if treds.get('best_offer') else 'N/A'} at "
        f"{treds['best_offer']['annual_rate_pct'] if treds.get('best_offer') else 0}% p.a., "
        f"net_proceeds=₹{treds['best_offer']['net_proceeds'] if treds.get('best_offer') else 0:,.0f}.\n\n"
        f"Write 3 paragraphs: 1) Business health summary, 2) Key opportunities, 3) Action items."
    )
    ai_summary = process_message(prompt, [])

    return {
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "days": days,
        "ai_summary": ai_summary,
        "sales": sales,
        "inventory": inventory,
        "reviews": reviews,
        "ondc": {
            "total_products": ondc["total_products"],
            "estimated_reach": ondc["estimated_reach"],
            "buyer_nps": ondc["buyer_nps"],
            "top_products": ondc["products"][:3],
        },
        "invoice": {
            "demo_invoice": {
                "number": DEMO_INVOICE["invoice_number"],
                "amount": DEMO_INVOICE["total_amount"],
                "seller": DEMO_INVOICE["seller_name"],
                "buyer": DEMO_INVOICE["buyer_name"],
            },
            "gstn": {"irn": gstn["irn"], "ack_no": gstn["ack_no"]},
            "treds_best_offer": treds["best_offer"],
        },
    }


# ── ONDC Auto-Optimizer ───────────────────────────────────────────────────

@app.get("/api/ondc/analyze")
def ondc_analyze(days: int = 30):
    """Analyse demand patterns and score products for ONDC listing opportunity."""
    return analyze_demand(days_window=days)

@app.get("/api/ondc/listing/{product_id}")
def ondc_listing(product_id: int):
    """Generate an AI-optimised ONDC catalogue entry for a product."""
    return generate_ondc_listing(product_id)


# ── WhatsApp via Twilio ───────────────────────────────────────────────────

from xml.sax.saxutils import escape

# Per-user conversation history
_wa_sessions: dict = defaultdict(list)
_MAX_HISTORY = 20


def _twiml(text: str) -> "Response":
    """Return valid TwiML XML response for Twilio WhatsApp."""
    from fastapi.responses import Response as FResponse

    text = text[:1599]
    safe_text = escape(text)

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Response>'
        f'<Message>{safe_text}</Message>'
        '</Response>'
    )

    return FResponse(
        content=xml,
        media_type="application/xml"
    )


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """Twilio WhatsApp webhook."""
    from fastapi.responses import Response as FResponse
    from config.settings import PUBLIC_BASE_URL
    import re as re2
    import base64

    form = await request.form()

    sender = form.get("From", "")
    body = (form.get("Body", "") or "").strip()
    num_media = int(form.get("NumMedia", 0) or 0)

    if not sender:
        return FResponse(
            content="",
            media_type="application/xml"
        )

    # ── Invoice image ─────────────────────────────────────────────────────
    if num_media > 0 and "image" in (
        form.get("MediaContentType0", "") or ""
    ):
        media_url = form.get("MediaUrl0", "")
        media_type = form.get(
            "MediaContentType0",
            "image/jpeg"
        )

        try:
            from config.settings import (
                TWILIO_ACCOUNT_SID,
                TWILIO_AUTH_TOKEN
            )
            from agents.invoice_agent import scan_invoice
            import urllib.request as urlreq

            credentials = base64.b64encode(
                f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}".encode()
            ).decode()

            req = urlreq.Request(
                media_url,
                headers={
                    "Authorization": f"Basic {credentials}"
                }
            )

            with urlreq.urlopen(req, timeout=10) as resp:
                img_bytes = resp.read()

            img_b64 = base64.b64encode(img_bytes).decode()
            result = scan_invoice(img_b64, media_type)

            if "error" not in result:
                reply = (
                    f"🧾 Invoice Scanned\n\n"
                    f"Invoice: {result.get('invoice_number', '—')}\n"
                    f"Seller: {result.get('seller_name', '—')}\n"
                    f"Amount: ₹{result.get('total_amount', 0):,}\n"
                    f"Due: {result.get('due_date', '—')}\n\n"
                    f"Reply FILE GSTN to register or TREDS for financing."
                )

                _wa_sessions[sender] = [
                    {
                        "role": "system",
                        "content": f"invoice_scanned:{json.dumps(result)}"
                    }
                ]
            else:
                reply = "❌ Could not read invoice. Please send a clearer image."

        except Exception as e:
            reply = f"❌ Invoice scan error: {str(e)[:80]}"

        return _twiml(reply)

    # ── Voice note ────────────────────────────────────────────────────────
    if num_media > 0 and "audio" in (
        form.get("MediaContentType0", "") or ""
    ):
        media_url = form.get("MediaUrl0", "")
        media_type = form.get(
            "MediaContentType0",
            "audio/ogg"
        )

        ext_map = {
            "audio/ogg": "ogg",
            "audio/mpeg": "mp3",
            "audio/mp4": "m4a",
            "audio/amr": "amr",
            "audio/aac": "aac",
            "audio/wav": "wav",
        }

        ext = ext_map.get(
            media_type.split(";")[0].strip(),
            "ogg"
        )

        filename = f"voice.{ext}"

        try:
            from config.settings import (
                TWILIO_ACCOUNT_SID,
                TWILIO_AUTH_TOKEN
            )
            from utils.sarvam import (
                transcribe_audio,
                LANGUAGE_NAMES
            )
            import urllib.request as urlreq

            creds = base64.b64encode(
                f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}".encode()
            ).decode()

            req2 = urlreq.Request(
                media_url,
                headers={
                    "Authorization": f"Basic {creds}"
                }
            )

            with urlreq.urlopen(req2, timeout=15) as resp2:
                audio_bytes = resp2.read()

            stt = transcribe_audio(
                audio_bytes,
                filename
            )

            transcript = (
                stt.get("transcript") or ""
            ).strip()

            lang_code = stt.get(
                "language_code",
                "en-IN"
            )

            lang_name = LANGUAGE_NAMES.get(
                lang_code,
                lang_code
            )

            if not transcript:
                return _twiml(
                    "❌ Couldn't transcribe your voice note. "
                    "Please try speaking clearly or send a text message."
                )

            history = [
                m
                for m in _wa_sessions[sender][-_MAX_HISTORY:]
                if m.get("role") in ("user", "assistant")
            ]

            ai_response = process_message(
                transcript,
                history
            )

            ai_response = re2.sub(
                r'\[REPORT:[^\]]+\]',
                '',
                ai_response
            ).strip()

            _wa_sessions[sender].append(
                {
                    "role": "user",
                    "content": transcript
                }
            )

            _wa_sessions[sender].append(
                {
                    "role": "assistant",
                    "content": ai_response
                }
            )

            if len(_wa_sessions[sender]) > _MAX_HISTORY:
                _wa_sessions[sender] = (
                    _wa_sessions[sender][-_MAX_HISTORY:]
                )

            try:
                from utils.sarvam import synthesize_speech
                import uuid

                tts_text = ai_response

                if len(tts_text) > 2400:
                    tts_text = (
                        tts_text[:2400]
                        .rsplit(" ", 1)[0]
                        + "…"
                    )

                audio_b64 = synthesize_speech(
                    tts_text,
                    lang_code
                )

                mp3_bytes = base64.b64decode(
                    audio_b64
                )

                audio_id = uuid.uuid4().hex
                _audio_cache[audio_id] = mp3_bytes

                audio_url = (
                    f"{PUBLIC_BASE_URL}/api/audio/{audio_id}"
                )

                caption = f"🎙️ _{transcript}_"

                if lang_code != "en-IN":
                    caption = (
                        f"🎙️ [{lang_name}] _{transcript}_"
                    )

                xml = (
                    '<?xml version="1.0" encoding="UTF-8"?>'
                    '<Response>'
                    f'<Message><Body>{escape(caption)}</Body></Message>'
                    f'<Message><Media>{escape(audio_url)}</Media></Message>'
                    '</Response>'
                )

                return FResponse(
                    content=xml,
                    media_type="application/xml"
                )

            except Exception:
                reply = (
                    f"🎙️ _{transcript}_\n\n"
                    f"{ai_response}"
                )

                if len(reply) > 1599:
                    reply = reply[:1596] + "…"

                return _twiml(reply)

        except Exception as e:
            reply = (
                f"❌ Voice note error: {str(e)[:120]}"
            )

        return _twiml(reply)

    if not body:
        return FResponse(
            content="",
            media_type="application/xml"
        )

    # ── FILE GSTN ─────────────────────────────────────────────────────────
    sys_msgs = [
        m
        for m in _wa_sessions[sender]
        if m.get("role") == "system"
    ]

    last_sys = (
        sys_msgs[-1]["content"]
        if sys_msgs
        else ""
    )

    if (
        body.upper() == "FILE GSTN"
        and last_sys.startswith("invoice_scanned:")
    ):
        try:
            from agents.invoice_agent import file_to_gstn

            inv_data = json.loads(
                last_sys.split(
                    "invoice_scanned:",
                    1
                )[1]
            )

            gstn = file_to_gstn(inv_data)

            irn_short = gstn["irn"][:32]

            eway = (
                f"\nE-Way Bill: "
                f"{gstn['eway_bill']['number']}"
                if gstn.get("eway_bill")
                else ""
            )

            reply = (
                f"✅ e-Invoice Registered on GSTN IRP\n\n"
                f"IRN: {irn_short}...\n"
                f"Ack No: {gstn['ack_no']}\n"
                f"Date: {gstn['ack_date']}"
                f"{eway}\n\n"
                f"Reply TREDS for financing offers."
            )

            _wa_sessions[sender].append(
                {
                    "role": "system",
                    "content": f"gstn:{gstn['irn']}"
                }
            )

        except Exception as e:
            reply = (
                f"❌ GSTN filing error: {str(e)[:80]}"
            )

        return _twiml(reply)

    # ── TREDS ─────────────────────────────────────────────────────────────
    if body.upper() == "TREDS":
        try:
            from agents.invoice_agent import (
                file_to_gstn,
                get_treds_offer,
                DEMO_INVOICE
            )

            inv_data = DEMO_INVOICE
            irn = ""

            for m in reversed(_wa_sessions[sender]):
                if m.get("content", "").startswith(
                    "invoice_scanned:"
                ):
                    inv_data = json.loads(
                        m["content"].split(
                            "invoice_scanned:",
                            1
                        )[1]
                    )

                if m.get("content", "").startswith(
                    "gstn:"
                ):
                    irn = m["content"].split(
                        "gstn:",
                        1
                    )[1]

            if not irn:
                gstn = file_to_gstn(inv_data)
                irn = gstn["irn"]

            offers = get_treds_offer(
                inv_data,
                irn
            )

            best = offers["best_offer"]

            reply = (
                f"🏦 TReDS Financing "
                f"({len(offers['offers'])} bids)\n\n"
                f"Best: {best['financier']} "
                f"via {best['platform']}\n"
                f"Rate: {best['annual_rate_pct']}% p.a.\n"
                f"Advance: ₹{best['advance_amount']:,.0f} "
                f"({best['advance_rate_pct']}%)\n"
                f"Net Proceeds: ₹{best['net_proceeds']:,.0f}\n"
                f"Tenor: {best['tenor_days']} days"
            )

        except Exception as e:
            reply = (
                f"❌ TReDS error: {str(e)[:80]}"
            )

        return _twiml(reply)

    # ── CLEAR ─────────────────────────────────────────────────────────────
    if body.upper() in (
        "CLEAR",
        "RESET",
        "START OVER"
    ):
        _wa_sessions[sender].clear()

        return _twiml(
            "🔄 Conversation cleared. "
            "How can I help you today?"
        )

    # ── Main AI orchestrator ─────────────────────────────────────────────
    history = [
        m
        for m in _wa_sessions[sender][-_MAX_HISTORY:]
        if m.get("role") in ("user", "assistant")
    ]

    try:
        ai_response = process_message(
            body,
            history
        )

    except Exception as e:
        err = str(e)

        if (
            "rate_limit" in err.lower()
            or "429" in err
        ):
            return _twiml(
                "⏳ I'm a bit busy right now — "
                "please try again in a minute!"
            )

        return _twiml(
            "❌ Sorry, something went wrong. "
            "Please try again.\n"
            f"({err[:80]})"
        )

    # ── Report marker ─────────────────────────────────────────────────────
    rm = re2.search(
        r'\[REPORT:([^:]+):([^\]]+)\]',
        ai_response
    )

    if rm:
        report_id = rm.group(1)

        ai_response = (
            ai_response[:rm.start()]
            .rstrip()
        )

        report_url = (
            f"{PUBLIC_BASE_URL.rstrip('/')}"
            f"/api/report/temp/{report_id}"
        )

        ai_response += (
            "\n\n📊 Your report is ready:\n"
            f"{report_url}\n"
            "(Open in browser → Print → Save as PDF)"
        )

    # ── Save conversation ─────────────────────────────────────────────────
    _wa_sessions[sender].append(
        {
            "role": "user",
            "content": body
        }
    )

    _wa_sessions[sender].append(
        {
            "role": "assistant",
            "content": ai_response
        }
    )

    if len(_wa_sessions[sender]) > _MAX_HISTORY * 2:
        _wa_sessions[sender] = (
            _wa_sessions[sender][-_MAX_HISTORY * 2:]
        )

    return _twiml(ai_response)