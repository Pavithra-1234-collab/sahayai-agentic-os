import json
from groq import Groq
from config.settings import GROQ_API_KEY, GROQ_MODEL
from utils.prompt_templates import LISTING_SYSTEM

client = Groq(api_key=GROQ_API_KEY)


def create_listing(product_name: str, category: str = "", features: str = "", cost_price: float = 0) -> dict:
    """Generate optimised Amazon and Flipkart listings for a product."""
    user_prompt = f"""Create a complete product listing for:
Product: {product_name}
Category: {category or "Electronics / Accessories"}
Key features mentioned by seller: {features or "Not specified — infer from product name"}
Cost price: ₹{cost_price if cost_price else "unknown"}

Generate:
1. AMAZON LISTING (JSON):
   - title (150-200 chars, keyword-rich)
   - bullet_points (list of 5 strings, each starting with capital benefit word)
   - description (150-200 words, HTML-free, benefit-led)
   - backend_keywords (comma-separated, 10-15 keywords)

2. FLIPKART LISTING (JSON):
   - title (80-100 chars)
   - highlights (list of 5 short phrases)
   - description (150 words, conversational)

3. SEO KEYWORDS (list of 10 search terms Indian buyers would use)

Return as JSON with keys: amazon, flipkart, seo_keywords"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": LISTING_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=1500,
    )

    raw = response.choices[0].message.content

    # Try to parse JSON from the response
    try:
        # Find JSON block if wrapped in markdown
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        listing_data = json.loads(raw)
    except Exception:
        # Fallback: return raw text
        listing_data = {"raw": raw, "amazon": {}, "flipkart": {}, "seo_keywords": []}

    listing_data["product_name"] = product_name
    return listing_data
