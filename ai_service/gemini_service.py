"""
GeminiService — reusable adapter for **Google AI Gemini** using the ``google-genai`` SDK.

This fills the same “base AI service” slot as a **Vertex AI** ``GeminiService`` in other
repos, except:

- Authentication is an **API key** (AI Studio style), **not** a GCP project +
  ``GOOGLE_APPLICATION_CREDENTIALS``.
- Network calls go through ``genai.Client(api_key=...)`` and
  ``client.models.generate_content(...)``.

Typical layering in this project:

1. ``GeminiService`` (this file) — connection, ``generate()``, structured JSON, and ``generate_with_tools()``.
2. ``ai_service.gemini_schema`` — Pydantic payloads / literals for Gemini structured outputs.
3. ``gemini_client`` — app-facing sync helpers (plain text, structured dict, JSON string, tools) built on this service.
4. ``resume_job_evaluation`` — domain prompts, normalization, persistence.

Embedding and batch inference APIs are not wrapped here yet.

Usage (after ``django.setup()``)::

    from ai_service.gemini_service import GeminiService

    service = GeminiService()

    # Unstructured: model answers in plain text (no enforced JSON MIME type).
    out = service.generate(
        system_instruction="You are a helpful assistant.",
        prompt="Explain quantum computing in two sentences.",
        temperature=0.7,
    )
    print(out["raw"])

    # Structured: native JSON schema + ``application/json``; ``parsed`` is a Python dict.
    out = service.generate(
        system_instruction="You are a grading assistant.",
        prompt="Grade this essay: ...",
        response_schema={...},  # JSON Schema dict or a Pydantic model class
        temperature=0.3,
    )
    print(out["parsed"])

Environment / Django settings (see ``jobeas.settings``):

- ``GEMINI_API_KEY`` primary; if empty, ``GOOGLE_API_KEY`` is used as fallback.
- ``GEMINI_RESUME_JOB_EVAL_MODEL`` selects the default model id (e.g. ``gemini-2.5-flash``).

Automated integration tests (live API; skipped automatically when no key is configured)::

    poetry run python manage.py test ai_service.tests.GeminiServiceLiveIntegrationTests -v 2

Manual exploration (Django shell)::

    from ai_service.gemini_service import GeminiService
    service = GeminiService()
    print(service.generate(
        system_instruction="You reply in one sentence.",
        prompt="Say hello.",
    ))
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Sequence
from typing import Any

logger = logging.getLogger("ai_service.gemini_service")

# ``response_schema`` for ``google-genai``: JSON Schema dict, generated ``Schema`` object,
# or a Pydantic **model class** (not an instance). The SDK maps these to Gemini structured output.
SchemaInput = Any


def resolve_credentials_from_django() -> tuple[str | None, str]:
    """
    Read Gemini API credentials and default model id from Django settings.

    Intended to be called only after Django has loaded ``settings``
    (e.g. runtime in ``manage.py``, ASGI/WSGI, or after ``django.setup()`` in scripts).

    Resolution order:

    - **API key:** ``settings.GEMINI_API_KEY`` (non-empty string). If missing, falls back to
      ``settings.GOOGLE_API_KEY_FALLBACK`` (wired from ``GOOGLE_API_KEY`` env in our settings).
    - **Model id:** ``settings.GEMINI_RESUME_JOB_EVAL_MODEL``, with fallback string
      ``gemini-2.5-flash`` if unset or blank.

    Returns:
        Tuple ``(api_key_or_none, default_model_id_string)``.
        ``api_key_or_none`` is ``None`` when both key sources are empty — callers must fail fast.

    Raises:
        ImportError: If Django settings cannot be imported (usually means ``django.setup()`` was not run).
    """
    from django.conf import settings

    # Prefer dedicated Gemini key so other Google keys are not overloaded accidentally.
    key = (getattr(settings, "GEMINI_API_KEY", "") or "").strip()
    if not key:
        fb = getattr(settings, "GOOGLE_API_KEY_FALLBACK", "") or ""
        key = str(fb).strip() if fb else ""

    mid = getattr(
        settings,
        "GEMINI_RESUME_JOB_EVAL_MODEL",
        "gemini-2.5-flash",
    )
    mid = str(mid).strip() or "gemini-2.5-flash"

    return (key if key else None), mid


def _strip_json_code_fence(text: str) -> str:
    """
    Remove a single markdown code fence around JSON if present.

    When ``response_mime_type`` is ``application/json``, responses are usually bare JSON.
    If a model still wraps output in ```json ... ```, this helper strips those markers so
    ``json.loads`` succeeds.

    Args:
        text: Raw model response string.

    Returns:
        Trimmed inner JSON string, or ``text.strip()`` when no fence pattern matches.
    """
    s = text.strip()
    m = re.match(r"^```(?:json)?\s*\n?(.*)\n?```\s*$", s, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return s


def _coerce_function_call_args(raw: Any) -> dict[str, Any]:
    """Normalize ``FunctionCall.args`` from the SDK into a plain ``dict``."""
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return dict(raw)
    if hasattr(raw, "items"):
        try:
            return dict(raw.items())  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return {}
    return {}


def _gemini_function_parameters_schema(parameters: dict[str, Any]) -> dict[str, Any]:
    """
    Gemini ``FunctionDeclaration`` parameter Schema rejects some JSON Schema extensions (e.g.
    ``additionalProperties``) sent from OpenAI-style tool definitions. Strip those keys recursively.
    """

    def _walk(node: Any) -> Any:
        if isinstance(node, dict):
            return {
                k: _walk(v)
                for k, v in node.items()
                if k not in ("additionalProperties", "additional_properties")
            }
        if isinstance(node, list):
            return [_walk(x) for x in node]
        return node

    return dict(_walk(parameters))




class GeminiService:
    """
    Thin wrapper around the Google **AI Studio / API key** Gemini client.

    Responsibilities:

    - Hold one ``google.genai.Client`` + a **default model id** shared by ``generate()`` calls.
    - Expose ``generate()`` (text or structured JSON) and ``generate_with_tools()`` when the model
      should emit function calls.
    - Live API checks belong in tests (see ``ai_service.tests.GeminiServiceLiveIntegrationTests``),
      not in this module as a runnable script.

    Typical construction:

    - **Inside Django:** ``GeminiService()`` — reads key + model via
      ``resolve_credentials_from_django()``.
    - **Scripts/tests:** ``GeminiService(api_key=\"...\", default_model_id=\"gemini-2.5-flash\")``.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        default_model_id: str | None = None,
    ) -> None:
        """
        Build a Gemini client ready for ``generate()``.

        If either ``api_key`` or ``default_model_id`` is omitted, missing values are pulled from
        Django settings through ``resolve_credentials_from_django()``. That requires Django to be
        configured (``django.setup()`` or running under ``manage.py``).

        Args:
            api_key: Google AI Gemini API key. If ``None``, taken from Django settings.
            default_model_id: Model id passed to ``generate_content`` when ``generate(..., model_name=None)``.
                If ``None``, taken from Django settings.

        Raises:
            RuntimeError: No API key after resolution / explicit empty string — service cannot authenticate.
            RuntimeError: ``google-genai`` import failed (dependency not installed).
        """
        # Fill any missing ctor args from the same central place as ``manage.py`` consumes.
        if api_key is None or default_model_id is None:
            k, mid = resolve_credentials_from_django()
            if api_key is None:
                api_key = k
            if default_model_id is None:
                default_model_id = mid

        ks = (api_key or "").strip()
        if not ks:
            raise RuntimeError(
                "No Gemini API key configured. Set GEMINI_API_KEY (or GOOGLE_API_KEY as fallback) "
                "in your environment / Django settings, or pass api_key= to GeminiService()."
            )

        try:
            from google import genai  # noqa: WPS433
        except ImportError as e:
            raise RuntimeError(
                "google-genai is not installed. Run: poetry install (see pyproject.toml)."
            ) from e

        # Persist defaults for downstream calls; callers can still override ``model_name`` per request.
        self._default_model_id = (default_model_id or "gemini-2.5-flash").strip() or "gemini-2.5-flash"
        self._client = genai.Client(api_key=ks)

    @property
    def model_name(self) -> str:
        """
        Default model id used whenever ``generate(..., model_name=None)``.

        Mirrors naming from Vertex-style helpers where instances expose ``self.model_name``.
        """
        return self._default_model_id

    @classmethod
    def from_django_settings(cls) -> GeminiService:
        """
        Construct ``GeminiService()`` using Django loaded settings — alias for readability.

        Use this in code that wants to make the settings dependency obvious; behavior is identical
        to calling ``GeminiService()`` with no arguments.
        """
        return cls()

    def generate(
        self,
        system_instruction: str,
        prompt: str,
        response_schema: SchemaInput | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        model_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Single entry point for text generation (plain or structured JSON).

        Workflow:

        #. Validate required text inputs.
        #. Choose ``model_id`` — explicit ``model_name`` parameter wins, otherwise
           ``self._default_model_id``.
        #. Build ``GenerateContentConfig`` with ``system_instruction``, ``temperature``, optional
           ``max_output_tokens``, and optional JSON mode.
        #. **Structured path** (``response_schema`` not ``None``):
           request ``response_mime_type=application/json`` and pass ``response_schema`` to the API.
           On failure (some keys / schema shapes are rejected server-side), **retry once** with the
           same JSON MIME type but **without** ``response_schema`` so the caller still receives JSON text.
        #. **Unstructured path** (``response_schema`` is ``None``):
           do **not** set JSON MIME type — response is natural language in ``raw``.
        #. If structured, parse ``raw`` with ``json.loads`` into ``parsed``; on failure raise
           ``ValueError`` with truncated logging.

        Args:
            system_instruction: Developer/system prompt (Gemini ``system_instruction``).
            prompt: End-user content (single string user turn).
            response_schema: Optional JSON schema / Pydantic model class for native structured output.
            temperature: Sampling temperature passed through to Gemini.
            max_tokens: Maps to ``max_output_tokens`` in the API when set and positive.
            model_name: Override model id for this call only.

        Returns:
            Dictionary with keys:

            - ``raw`` (``str``): verbatim model text response.
            - ``parsed`` (``Any`` or ``None``): decoded JSON **only** when ``response_schema`` was
              provided; otherwise ``None``.
            - ``model`` (``str``): model id actually used for the request.

        Raises:
            ValueError: Missing ``system_instruction`` or ``prompt``, or invalid JSON in structured mode.
            RuntimeError: Empty model body (no text returned).
        """
        if not system_instruction:
            raise ValueError("system_instruction is required")
        if not prompt:
            raise ValueError("prompt is required")

        from google.genai import types

        model = (model_name or self._default_model_id).strip()

        def _call(
            *,
            use_json_mime: bool,
            schema: SchemaInput | None,
        ) -> str:
            """Run one ``generate_content`` with shared temperature / system prompt / optional JSON mode."""
            cfg: dict[str, Any] = {
                "temperature": temperature,
                "system_instruction": system_instruction,
            }
            # JSON MIME asks the API to constrain output shape; omit for free-form answers.
            if use_json_mime:
                cfg["response_mime_type"] = "application/json"
            if max_tokens is not None and max_tokens > 0:
                cfg["max_output_tokens"] = max_tokens
            if schema is not None:
                cfg["response_schema"] = schema

            config = types.GenerateContentConfig(**cfg)
            logger.info(
                "GeminiService.generate model=%s structured=%s",
                model,
                schema is not None,
            )
            response = self._client.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )
            text = (response.text or "").strip()
            if not text:
                raise RuntimeError("Gemini returned an empty response body.")
            return text

        # Branch: structured vs unstructured generation.
        raw: str
        if response_schema is not None:
            # First attempt: full native structured output.
            try:
                raw = _call(use_json_mime=True, schema=response_schema)
            except Exception as exc:
                # Some schema + model combinations error at the API; degrade gracefully to JSON-only mime.
                logger.warning(
                    "GeminiService: structured output failed (%s); retrying without response_schema",
                    exc,
                    exc_info=logger.isEnabledFor(logging.DEBUG),
                )
                raw = _call(use_json_mime=True, schema=None)
        else:
            # Natural language answer — avoid forcing JSON.
            raw = _call(use_json_mime=False, schema=None)

        parsed: Any = None
        if response_schema is not None:
            cleaned = _strip_json_code_fence(raw)
            try:
                parsed = json.loads(cleaned)
            except json.JSONDecodeError as e:
                logger.error("GeminiService: invalid JSON (schema mode): %s", e)
                logger.error("GeminiService: raw (truncated): %s", raw[:800])
                raise ValueError(f"Invalid JSON response from Gemini: {e}") from e

        return {"raw": raw, "parsed": parsed, "model": model}

    def generate_json(
        self,
        *,
        system_instruction: str,
        user_text: str,
        model_id: str | None = None,
        temperature: float = 0.35,
        max_output_tokens: int | None = 8192,
        response_schema: SchemaInput | None = None,
    ) -> str:
        """
        Return **only** the raw response string — compatibility with older callers.

        ``gemini_generate_json_sync`` can call this wrapper for callers that only need ``raw``.
        Prefer :func:`~ai_service.gemini_client.gemini_generate_structured_sync` in domain code when
        you need ``parsed``.

        Args:
            system_instruction: System prompt passed to Gemini.
            user_text: End-user payload (historical name; same as ``generate(..., prompt=...)``).
            model_id: Per-call model override (maps to ``generate(..., model_name=...)``).
            temperature: Passed through to ``generate``.
            max_output_tokens: Maps to ``generate(..., max_tokens=...)``.
            response_schema: Optional structured output constraint.

        Returns:
            Raw model text — for JSON MIME requests, typically a JSON object string.
        """
        out = self.generate(
            system_instruction=system_instruction,
            prompt=user_text,
            response_schema=response_schema,
            temperature=temperature,
            max_tokens=max_output_tokens,
            model_name=model_id,
        )
        return out["raw"]

    def generate_with_tools(
        self,
        *,
        system_instruction: str,
        prompt: str,
        tools: Sequence[dict[str, Any]],
        temperature: float = 0.3,
        max_tokens: int | None = None,
        model_name: str | None = None,
    ) -> dict[str, Any]:
        """
        One-shot ``generate_content`` with **function declarations** (tool calling).

        Each entry in ``tools`` should resemble OpenAI-style tool metadata (same spirit as
        ``TASK_SCHEMAS`` entries in ``task_schema``):

        ``{"name": str, "description": str, "parameters": <JSON Schema object>}``

        JSON Schema keys like ``additionalProperties`` are stripped recursively because the Gemini
        API does not accept them on function parameters.

        Args:
            system_instruction: System prompt.
            prompt: User/content turn.
            tools: Non-empty list of declarations with ``name`` and optional ``description`` /
                ``parameters`` (defaults to ``{"type":"object","properties":{}}``).
            temperature: Sampling temperature.
            max_tokens: Optional ``max_output_tokens``.
            model_name: Per-call model id override.

        Returns:
            ``{"model": str, "text": str, "function_calls": [{"name": str, "args": dict}, ...]}``

            Model text may be empty when only tool calls were returned.

        Raises:
            ValueError: Missing inputs or invalid tool specs.
            RuntimeError: Completely empty reply (no text and no ``function_calls``).
        """
        if not system_instruction:
            raise ValueError("system_instruction is required")
        if not prompt:
            raise ValueError("prompt is required")
        if not tools:
            raise ValueError("tools must be a non-empty list of function declarations")

        from google.genai import types

        model = (model_name or self._default_model_id).strip()
        declarations: list[Any] = []
        for spec in tools:
            if not isinstance(spec, dict):
                raise ValueError("each tool declaration must be a dict")
            name = spec.get("name")
            if not name or not isinstance(name, str):
                raise ValueError("each tool declaration must include a string 'name'")
            params_in = spec.get("parameters")
            if not isinstance(params_in, dict):
                params_in = {"type": "object", "properties": {}}
            declarations.append(
                types.FunctionDeclaration(
                    name=name.strip(),
                    description=str(spec.get("description") or ""),
                    parameters=_gemini_function_parameters_schema(params_in),
                )
            )

        tool_union = types.Tool(function_declarations=declarations)
        cfg_kw: dict[str, Any] = {
            "temperature": temperature,
            "system_instruction": system_instruction,
            "tools": [tool_union],
        }
        if max_tokens is not None and max_tokens > 0:
            cfg_kw["max_output_tokens"] = max_tokens

        config = types.GenerateContentConfig(**cfg_kw)
        logger.info("GeminiService.generate_with_tools model=%s declarations=%s", model, len(declarations))

        response = self._client.models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )

        function_calls: list[dict[str, Any]] = []
        text_chunks: list[str] = []

        cands = getattr(response, "candidates", None) or []
        if cands:
            content = getattr(cands[0], "content", None)
            parts = getattr(content, "parts", None) if content is not None else None
            for part in parts or []:
                fc = getattr(part, "function_call", None)
                if fc:
                    nm = getattr(fc, "name", None) or ""
                    args_raw = getattr(fc, "args", None)
                    args_dict = _coerce_function_call_args(args_raw)
                    if nm:
                        function_calls.append({"name": nm, "args": args_dict})
                tx = getattr(part, "text", None)
                if tx:
                    text_chunks.append(str(tx))

        aggregated = "\n".join(text_chunks).strip()
        fallback_text = (getattr(response, "text", None) or "").strip()
        final_text = aggregated if aggregated else fallback_text

        if not final_text and not function_calls:
            raise RuntimeError("Gemini returned an empty response body (no text and no tool calls).")

        return {"model": model, "text": final_text, "function_calls": function_calls}
