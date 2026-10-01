import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")

# Twilio WhatsApp
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv(
    "TWILIO_WHATSAPP_FROM",
    "whatsapp:+14155238886"
)  # sandbox default

PUBLIC_BASE_URL = os.getenv(
    "PUBLIC_BASE_URL",
    "http://localhost:8000"
)  # set to ngrok URL

GROQ_MODEL = "openai/gpt-oss-120b"

# Fallback models tried in order when primary hits rate limit
GROQ_FALLBACK_MODELS = ["openai/gpt-oss-20b"]

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "business.db"
)

DB_URL = f"sqlite:///{DB_PATH}"

# Approximate mid-range referral fees
AMAZON_FEE_RATE = 0.12
FLIPKART_FEE_RATE = 0.10

# ONDC
ONDC_FEE_RATE = 0.05
ONDC_FIXED_FEE = 1.5

LOW_STOCK_THRESHOLD = 10
REORDER_THRESHOLD = 5