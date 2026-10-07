"""
Central config loader. Reads from .env via python-dotenv.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Gmail OAuth2
    GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID", "")
    GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET", "")
    GMAIL_REDIRECT_URI = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:8080/callback")
    GMAIL_SCOPES = os.getenv("GMAIL_SCOPES", "https://www.googleapis.com/auth/gmail.modify")

    # Google's well-known OAuth2 endpoints (these don't change, safe to hardcode)
    GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
    GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"

    # Local LLM (Ollama)
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")

    # Local storage paths
    TOKEN_STORE_PATH = "data/tokens.json"
    AUDIT_LOG_PATH = "data/audit_log.jsonl"


settings = Settings()
