"""
ai_client.py

Thin wrapper around the two LLM providers used by SentinelAI:

1. Google Gemini (via google-generativeai) — primary reasoning engine
   used by the Situation, Weather, Resource, and Decision agents.

2. NVIDIA NIM (OpenAI-compatible REST endpoint) — used by the
   Communication Agent to demonstrate real multi-provider inference,
   as required by the hackathon's NVIDIA sponsorship track.

Both methods return raw text. JSON parsing happens in agents.py via
utils.extract_json, keeping this module provider-focused only.
"""

import logging
from typing import Optional

import httpx

from config import get_settings

logger = logging.getLogger("sentinelai.ai_client")

settings = get_settings()

_gemini_model = None


def _get_gemini_model():
    """Lazily initialize the Gemini client so the app can still boot
    (e.g. for local frontend development) without a configured key."""
    global _gemini_model
    if _gemini_model is not None:
        return _gemini_model

    if not settings.GOOGLE_API_KEY:
        raise RuntimeError(
            "GOOGLE_API_KEY is not configured. Set it in backend/.env to enable Gemini."
        )

    import google.generativeai as genai

    genai.configure(api_key=settings.GOOGLE_API_KEY)
    _gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
    return _gemini_model


async def call_gemini(prompt: str, temperature: float = 0.3) -> str:
    """Call Gemini with a text prompt and return the raw text response."""
    model = _get_gemini_model()
    try:
        response = await model.generate_content_async(
            prompt,
            generation_config={"temperature": temperature},
            request_options={"timeout": 45},
        )
        return response.text
    except Exception as exc:  # noqa: BLE001
        logger.exception("Gemini call failed")
        raise RuntimeError(f"Gemini call failed: {exc}") from exc


async def call_nvidia_nim(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.4,
) -> str:
    """
    Call an NVIDIA NIM model through its OpenAI-compatible /chat/completions
    endpoint and return the raw text response.
    """
    if not settings.NVIDIA_API_KEY:
        raise RuntimeError(
            "NVIDIA_API_KEY is not configured. Set it in backend/.env to enable NVIDIA NIM."
        )

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": settings.NVIDIA_NIM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 1024,
    }

    headers = {
        "Authorization": f"Bearer {settings.NVIDIA_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    url = f"{settings.NVIDIA_NIM_BASE_URL.rstrip('/')}/chat/completions"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as exc:
            logger.exception("NVIDIA NIM call failed with HTTP error")
            raise RuntimeError(
                f"NVIDIA NIM call failed: {exc.response.status_code} {exc.response.text}"
            ) from exc
        except Exception as exc:  # noqa: BLE001
            logger.exception("NVIDIA NIM call failed")
            raise RuntimeError(f"NVIDIA NIM call failed: {exc}") from exc
