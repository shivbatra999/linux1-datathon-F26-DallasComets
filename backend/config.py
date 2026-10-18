from pathlib import Path
import os

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=False)

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_PUBLISHABLE_KEY = os.getenv(
    "SUPABASE_PUBLISHABLE_KEY", ""
).strip()
SIMPLECATER_ORIGIN = os.getenv(
    "SIMPLECATER_ORIGIN", 'http://127.0.0.1:8001'
).rstrip("/")
SIMPLECATER_LLM_URL = os.getenv(
    "SIMPLECATER_LLM_URL", "http://127.0.0.1:8080/v1"
).rstrip("/")
SIMPLECATER_LLM_MODEL = os.getenv("SIMPLECATER_LLM_MODEL", "granite").strip()
SIMPLECATER_LLM_TIMEOUT_SECONDS = float(
    os.getenv("SIMPLECATER_LLM_TIMEOUT_SECONDS", "45")
)
SIMPLECATER_LLM_REASONING_FORMAT = os.getenv(
    "SIMPLECATER_LLM_REASONING_FORMAT", "none"
).strip()


def supabase_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY)
