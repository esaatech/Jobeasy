"""
Gemini **client layer** — synchronous helpers above :class:`GeminiService`.

Use this module for app/domain code; keep transport details in ``gemini_service``.

**Surfaces**

1. **Plain text** — :func:`gemini_generate_text_sync` (no structured output).
2. **Structured JSON** — :func:`gemini_generate_structured_sync` returns ``raw`` / ``parsed`` / ``model``;
   :func:`gemini_generate_json_sync` is the same pipeline but returns **only** the raw JSON string
   (backward compatible with older callers).
3. **Tool calling** — :func:`gemini_generate_with_tools_sync`; pass declarations shaped like
   ``task_schema`` tool ``parameters`` blocks (``name``, ``description``, ``parameters`` dict).

Domain services (e.g. ``resume_job_evaluation``, ``why_should_i_apply``) compose these; structured schemas live in ``gemini_schema``.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .gemini_service import GeminiService, SchemaInput, resolve_credentials_from_django

__all__ = [
    "get_gemini_api_key",
    "gemini_generate_json_sync",
    "gemini_generate_structured_sync",
    "gemini_generate_text_sync",
    "gemini_generate_with_tools_sync",
    "resolve_credentials_from_django",
]


def get_gemini_api_key() -> str | None:
    key, _ = resolve_credentials_from_django()
    return key


def gemini_generate_text_sync(
    *,
    system_instruction: str,
    prompt: str,
    model_id: str | None = None,
    temperature: float = 0.7,
    max_output_tokens: int | None = None,
) -> str:
    """Single natural-language completion; returns model text only."""
    svc = GeminiService.from_django_settings()
    out = svc.generate(
        system_instruction=system_instruction,
        prompt=prompt,
        response_schema=None,
        temperature=temperature,
        max_tokens=max_output_tokens,
        model_name=model_id,
    )
    return out["raw"]


def gemini_generate_structured_sync(
    *,
    system_instruction: str,
    user_text: str,
    response_schema: SchemaInput,
    model_id: str | None = None,
    temperature: float = 0.35,
    max_output_tokens: int | None = 8192,
) -> dict[str, Any]:
    """
    Gemini call with native structured JSON (``application/json`` + schema).

    Returns ``{"raw", "parsed", "model"}`` as :meth:`GeminiService.generate`.
    """
    if response_schema is None:
        raise ValueError("response_schema is required for gemini_generate_structured_sync")
    svc = GeminiService.from_django_settings()
    return svc.generate(
        system_instruction=system_instruction,
        prompt=user_text,
        response_schema=response_schema,
        temperature=temperature,
        max_tokens=max_output_tokens,
        model_name=model_id,
    )


def gemini_generate_json_sync(
    *,
    system_instruction: str,
    user_text: str,
    model_id: str | None = None,
    temperature: float = 0.35,
    max_output_tokens: int | None = 8192,
    response_schema: SchemaInput | None = None,
) -> str:
    """
    Returns the raw completion string — structured JSON MIME when ``response_schema`` is set,
    otherwise plain text generation (historical callers may omit schema).
    """
    svc = GeminiService.from_django_settings()
    return svc.generate_json(
        system_instruction=system_instruction,
        user_text=user_text,
        model_id=model_id,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        response_schema=response_schema,
    )


def gemini_generate_with_tools_sync(
    *,
    system_instruction: str,
    prompt: str,
    tools: Sequence[dict[str, Any]],
    model_id: str | None = None,
    temperature: float = 0.3,
    max_output_tokens: int | None = None,
) -> dict[str, Any]:
    """
    Tool / function-calling turn. See :meth:`GeminiService.generate_with_tools`.

    ``tools`` entries: ``{"name", "description?", "parameters?"}`` (OpenAPI-style JSON Schema).
    """
    svc = GeminiService.from_django_settings()
    return svc.generate_with_tools(
        system_instruction=system_instruction,
        prompt=prompt,
        tools=tools,
        temperature=temperature,
        max_tokens=max_output_tokens,
        model_name=model_id,
    )
