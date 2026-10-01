# AI Business Manager

AI-powered e-commerce business manager for Indian SMB sellers on Amazon.in and Flipkart. Hub-and-spoke agentic system with a React frontend, FastAPI backend, and WhatsApp integration.

## Running the App

### Backend
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend && npm run dev
```

### Streamlit (alternative UI)
```bash
streamlit run app.py
```

### ngrok (for WhatsApp webhook)
```bash
ngrok http 8000
# Update PUBLIC_BASE_URL in .env and Twilio Console sandbox webhook URL
```

## Project Structure

```
api.py                    # FastAPI server — all REST endpoints
app.py                    # Streamlit dashboard (alternative UI)
config/settings.py        # API keys, fee rates, model names
agents/
  orchestrator.py         # Groq tool_use routing — core agent loop
  inventory_agent.py
  pricing_agent.py
  analytics_agent.py
  review_agent.py
  listing_agent.py
  invoice_agent.py        # OCR + GSTN e-invoice + TReDS financing
  ondc_agent.py           # Demand scoring + Beckn catalogue generation
  report_agent.py         # HTML report builder + AI executive summary
database/
  models.py               # SQLAlchemy ORM models
  db_manager.py           # CRUD helpers
  seed_data.py            # Deterministic mock data (random.seed(42))
utils/
  prompt_templates.py     # All LLM system prompts (centralised)
  report_cache.py         # In-memory report cache {id -> {html, filename}}
  sarvam_tts.py           # Sarvam AI text-to-speech (Indian languages)
frontend/src/
  App.jsx                 # Router + sidebar nav
  pages/                  # Dashboard, Chat, Products, Reviews, Analytics,
                          # Payments, ONDC, WhatsApp
  components/VoiceButton.jsx
```

## Tech Stack

- **LLM:** Groq API — `qwen/qwen3-32b` (primary), `llama-3.3-70b-versatile`, `llama-3.1-8b-instant` (fallbacks)
- **Vision/OCR:** `llama-3.2-11b-vision-preview` via Groq
- **TTS:** Sarvam AI (Indian languages)
- **DB:** SQLite + SQLAlchemy
- **WhatsApp:** Twilio sandbox (TwiML webhook at `/webhook/whatsapp`)
- **Frontend:** React 19 + Vite + Tailwind CSS + Recharts

## Key Conventions

- **Model fallback:** `_chat_with_fallback()` in orchestrator retries on `RateLimitError` through the model chain
- **Think-token stripping:** Qwen emits `<think>...</think>` blocks — stripped via regex before returning responses
- **Report flow:** Agent asks 2 follow-up questions (sections + period) before calling `generate_report` tool; result cached and served at `/api/report/temp/{id}`
- **Report marker:** `[REPORT:id:filename]` appended to orchestrator response, extracted by `/api/chat` endpoint
- **WhatsApp sessions:** `_wa_sessions` defaultdict keyed by `whatsapp:+91...`, capped at 40 messages
- **Fee rates:** Amazon 18%, Flipkart 15%, ONDC 3%
- **Thresholds:** Low stock = 10 units, reorder = 5 units

## Environment Variables (.env)

```
GROQ_API_KEY=
SARVAM_API_KEY=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
PUBLIC_BASE_URL=https://<ngrok-subdomain>.ngrok-free.app
```
