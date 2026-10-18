
import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

# Read .env from the main project folder
project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")

supabase_url = os.environ["SUPABASE_URL"]
supabase_key = os.environ["SUPABASE_SECRET_KEY"]

# Initialize server-side Supabase client
supabase = create_client(supabase_url, supabase_key)
