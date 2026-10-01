import json
from groq import Groq
from config.settings import GROQ_API_KEY, GROQ_MODEL, GROQ_FALLBACK_MODELS
from utils.prompt_templates import ORCHESTRATOR_SYSTEM
from agents.inventory_agent import check_inventory
from agents.pricing_agent import get_pricing_advice
from agents.analytics_agent import get_sales_report
from agents.review_agent import analyze_reviews
from agents.listing_agent import create_listing
from agents.ondc_agent import analyze_demand
from agents.invoice_agent import file_to_gstn, get_treds_offer, generate_payment_request, DEMO_INVOICE
from agents.report_agent import build_and_cache_report

client = Groq(api_key=GROQ_API_KEY)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_inventory",
            "description": "Check stock levels for all products. Use when asked about inventory, stock, low stock, reorder, or out-of-stock items.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pricing_advice",
            "description": "Get pricing recommendations, competitor analysis, and margin calculations. Use for questions about pricing, competitors, margins, or price changes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Name or partial name of the product to analyse. Leave empty for all products.",
                    },
                    "product_id": {
                        "type": "integer",
                        "description": "Product ID to analyse specifically.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sales_report",
            "description": "Get sales analytics, revenue data, order counts, top products, platform breakdown, and growth trends.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of past days to analyse. Default 30. Use 7 for weekly, 90 for quarterly.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_reviews",
            "description": "Analyse customer reviews for sentiment, patterns, complaints, and get recent review summaries. Use for questions about reviews, ratings, customer feedback, complaints.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of past days to analyse reviews. Default 30.",
                    },
                    "product_id": {
                        "type": "integer",
                        "description": "Product ID to filter reviews. Leave empty for all products.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_listing",
            "description": "Generate an optimised Amazon and Flipkart product listing. Use when asked to create, write, or optimise a product listing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Name of the product to create a listing for.",
                    },
                    "category": {
                        "type": "string",
                        "description": "Product category (e.g. Electronics, Home & Kitchen)",
                    },
                    "features": {
                        "type": "string",
                        "description": "Key features or specs the seller wants to highlight.",
                    },
                    "cost_price": {
                        "type": "number",
                        "description": "Cost price of the product in INR.",
                    },
                },
                "required": ["product_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_report",
            "description": (
                "Generate and prepare a downloadable business performance report as a PDF/HTML file. "
                "Use this ONLY after you have confirmed with the user: (1) which sections they want "
                "(sales, inventory, reviews, ondc, payments — or 'full' for all), and "
                "(2) the time period (7, 30, or 90 days). "
                "Do NOT call this tool without first collecting these two pieces of information through follow-up questions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of past days to include. Must be 7, 30, or 90.",
                    },
                    "sections": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of sections to include. Valid values: sales, inventory, reviews, ondc, payments. Pass all five for a full report.",
                    },
                },
                "required": ["days", "sections"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_ondc_demand",
            "description": "Analyse demand trends and score all products for ONDC listing opportunity. ONDC has lower fees (3–8% + ₹1.5/order) vs Amazon/Flipkart (5–20%), enabling competitive pricing. Use when asked about ONDC, Open Network for Digital Commerce, expanding to new channels, or fee savings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Days of sales history to analyse. Default 30.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_invoice_financing",
            "description": "Get TReDS invoice discounting offers from banks (SBI, HDFC, Axis, ICICI, Kotak) for the demo invoice. Use when asked about invoice financing, working capital, TReDS, invoice discounting, or cash flow from invoices.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_upi_payment",
            "description": "Generate a UPI payment link and WhatsApp payment message. Use when asked to create a payment request, send a payment link, or collect payment via UPI.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "Amount in INR to request.",
                    },
                    "payee_name": {
                        "type": "string",
                        "description": "Name of the payee (seller/business).",
                    },
                    "upi_id": {
                        "type": "string",
                        "description": "UPI ID of the payee (e.g. business@upi).",
                    },
                    "invoice_number": {
                        "type": "string",
                        "description": "Invoice number for reference.",
                    },
                },
                "required": ["amount", "payee_name", "upi_id"],
            },
        },
    },
]


def _analyze_ondc_demand(days: int = 30) -> dict:
    result = analyze_demand(days_window=days)
    # Trim to top 3 products for chat context
    result["products"] = result["products"][:3]
    return result


def _get_invoice_financing() -> dict:
    gstn = file_to_gstn(DEMO_INVOICE)
    offers = get_treds_offer(DEMO_INVOICE, gstn["irn"])
    return {
        "invoice_number": DEMO_INVOICE["invoice_number"],
        "invoice_amount": DEMO_INVOICE["total_amount"],
        "irn": gstn["irn"],
        "best_offer": offers["best_offer"],
        "total_offers": len(offers["offers"]),
        "message": offers["message"],
    }


def _generate_upi_payment(amount: float, payee_name: str, upi_id: str, invoice_number: str = "") -> dict:
    return generate_payment_request(amount, payee_name, upi_id, invoice_number=invoice_number)


TOOL_MAP = {
    "generate_report": build_and_cache_report,
    "check_inventory": check_inventory,
    "get_pricing_advice": get_pricing_advice,
    "get_sales_report": get_sales_report,
    "analyze_reviews": analyze_reviews,
    "create_listing": create_listing,
    "analyze_ondc_demand": _analyze_ondc_demand,
    "get_invoice_financing": _get_invoice_financing,
    "generate_upi_payment": _generate_upi_payment,
}


def _chat_with_fallback(**kwargs):
    """Call Groq, automatically retrying with fallback models on rate-limit (429)."""
    from groq import RateLimitError
    models_to_try = [GROQ_MODEL] + GROQ_FALLBACK_MODELS
    last_err = None
    for model in models_to_try:
        try:
            return client.chat.completions.create(model=model, **kwargs)
        except RateLimitError as e:
            last_err = e
            continue  # try next model
    raise last_err  # all models exhausted


def process_message(user_message: str, history: list) -> str:
    """
    Process a user message through the orchestrator.
    history: list of {"role": "user"/"assistant", "content": "..."} dicts
    Returns the assistant's response string.
    """
    messages = [{"role": "system", "content": ORCHESTRATOR_SYSTEM}]
    # Keep last 10 turns for context
    messages.extend(history[-10:])
    messages.append({"role": "user", "content": user_message})

    # First call — let the model decide if it needs a tool
    response = _chat_with_fallback(
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        temperature=0.1,
        max_tokens=2000,
    )

    msg = response.choices[0].message

    # If no tool call, check for LLaMA text-format tool call (model sometimes writes
    # generate_report(days=30, sections=[...]) as text instead of using the API)
    if not msg.tool_calls:
        content = (msg.content or "").strip()
        gr_match = __import__("re").search(
            r'generate_report\s*\(([^)]+)\)', content, __import__("re").DOTALL
        )
        if gr_match:
            args_text = gr_match.group(1)
            days_m = __import__("re").search(r'days\s*=\s*(\d+)', args_text)
            sec_m = __import__("re").search(r'sections\s*=\s*(\[[^\]]+\])', args_text)
            try:
                days_val = int(days_m.group(1)) if days_m else 30
                sec_val = json.loads(sec_m.group(1)) if sec_m else ["sales","inventory","reviews","ondc","payments"]
                result = build_and_cache_report(days=days_val, sections=sec_val)
                final_text = (
                    f"Your report is ready! It covers {', '.join(sec_val)} for the last {days_val} days, "
                    f"including an AI executive summary."
                )
                final_text += f"\n[REPORT:{result['report_id']}:{result['filename']}]"
                return final_text
            except Exception as e:
                pass  # fall through to normal response
        clean = __import__("re").sub(r'<think>.*?</think>', '', msg.content or "", flags=__import__("re").DOTALL).strip()
        return clean or "I'm sorry, I couldn't process that request. Please try again."

    # Execute all tool calls
    messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": [
        {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
        for tc in msg.tool_calls
    ]})

    for tool_call in msg.tool_calls:
        fn_name = tool_call.function.name
        try:
            args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
        except json.JSONDecodeError:
            args = {}
        if args is None:
            args = {}

        # Coerce numeric args that Groq sometimes passes as strings
        for k in ("days", "product_id", "threshold", "cost_price"):
            if k in args and isinstance(args[k], str):
                try:
                    args[k] = int(args[k]) if k != "cost_price" else float(args[k])
                except ValueError:
                    pass

        fn = TOOL_MAP.get(fn_name)
        if fn:
            try:
                result = fn(**args)
            except Exception as e:
                result = {"error": str(e)}
        else:
            result = {"error": f"Unknown tool: {fn_name}"}

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result, default=str),
        })

    # Second call — generate final natural language response
    final_response = _chat_with_fallback(
        messages=messages,
        temperature=0.1,
        max_tokens=2000,
    )

    raw_final = final_response.choices[0].message.content or "Done! Let me know if you need anything else."
    # Strip <think>...</think> reasoning blocks emitted by Qwen/QwQ models
    import re as _re2
    final_text = _re2.sub(r'<think>.*?</think>', '', raw_final, flags=_re2.DOTALL).strip()

    # If generate_report was called, append the download marker to the response
    for tc in msg.tool_calls:
        if tc.function.name == "generate_report":
            # Find this tool's result in messages
            for m in messages:
                if m.get("role") == "tool" and m.get("tool_call_id") == tc.id:
                    try:
                        result = json.loads(m["content"])
                        if "report_id" in result:
                            final_text += f"\n[REPORT:{result['report_id']}:{result['filename']}]"
                    except Exception:
                        pass
            break

    return final_text
