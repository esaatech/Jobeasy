"""
DeepSeek chat client — OpenAI-compatible API.

https://api-docs.deepseek.com/
Set ``DEEPSEEK_API_KEY`` in the environment (see ``.env.example``).
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

load_dotenv()

DEEPSEEK_BASE_URL = "https://api.deepseek.com"

__all__ = ["DEEPSEEK_BASE_URL", "OpenAIError", "get_deepseek_client"]


def get_deepseek_client() -> OpenAI:
    """Return an OpenAI SDK client pointed at DeepSeek."""
    api_key = (os.getenv("DEEPSEEK_API_KEY") or "").strip()
    if not api_key:
        raise ValueError(
            "DEEPSEEK_API_KEY is not set. Add it to .env (see .env.example)."
        )
    return OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
