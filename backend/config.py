import os
from pathlib import Path
from dotenv import load_dotenv

# Find .env at root of the project
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# --- LLM API Keys ---
# Using Groq for LLM to avoid rate limits
GROQ_API_KEY = os.getenv("Groq_API_KEY") or os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_BASE_URL = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
OPENEXCHANGERATES_APP_ID = os.getenv("OPENEXCHANGERATES_APP_ID")
PORT = int(os.getenv("PORT", "8000"))
MAX_REPAIR_RETRIES = int(os.getenv("MAX_REPAIR_RETRIES", "3"))

# Check required keys
required_keys = {
    "GEMINI_API_KEY": GEMINI_API_KEY,
    "LANGFUSE_PUBLIC_KEY": LANGFUSE_PUBLIC_KEY,
    "LANGFUSE_SECRET_KEY": LANGFUSE_SECRET_KEY,
    "OPENEXCHANGERATES_APP_ID": OPENEXCHANGERATES_APP_ID,
}

missing_keys = [k for k, v in required_keys.items() if not v]
if missing_keys:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_keys)}")
