"""Central configuration. All env-driven so nothing secret is hard-coded."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from repo root (api/../.env) then any local override.
_API_DIR = Path(__file__).resolve().parent.parent          # .../api
_REPO_ROOT = _API_DIR.parent                                # repo root
load_dotenv(_REPO_ROOT / ".env")
load_dotenv(_API_DIR / ".env", override=False)

# --- paths -------------------------------------------------------------
DB_PATH = Path(os.getenv("SITEMIND_DB", _API_DIR / "sitemind.db"))
DATA_DIR = Path(os.getenv("SITEMIND_DATA_DIR", _REPO_ROOT / "data"))
GENERATED_DIR = DATA_DIR / "generated"

# --- models ------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
REASONING_MODEL = os.getenv("SITEMIND_REASONING_MODEL", "openai/gpt-oss-120b")
FAST_MODEL = os.getenv("SITEMIND_FAST_MODEL", "llama-3.1-8b-instant")
EMBED_MODEL = os.getenv("SITEMIND_EMBED_MODEL", "BAAI/bge-small-en-v1.5")
EMBED_DIM = 384  # bge-small-en-v1.5

# Map the plan's effort vocabulary -> gpt-oss reasoning_effort levels.
EFFORT_MAP = {"low": "low", "high": "medium", "xhigh": "high"}


def require_key() -> str:
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return GROQ_API_KEY
