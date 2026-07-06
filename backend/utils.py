"""
utils.py

Small shared helper functions used across the backend.
"""

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict


def new_incident_id() -> str:
    """Generate a unique, human-friendly incident ID."""
    return f"INC-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def extract_json(raw_text: str) -> Dict[str, Any]:
    """
    Extract a JSON object from a raw LLM response.

    LLMs sometimes wrap JSON in markdown code fences or add stray text.
    This function strips that and safely parses the first JSON object found.
    """
    if not raw_text:
        raise ValueError("Empty response from model, cannot extract JSON.")

    text = raw_text.strip()

    # Strip markdown code fences if present
    text = re.sub(r"^```(json)?", "", text.strip(), flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text.strip()).strip()

    # Find the first { ... } block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in model response: {raw_text[:200]}")

    json_str = match.group(0)
    return json.loads(json_str)


def duration_ms(start: datetime, end: datetime) -> float:
    return round((end - start).total_seconds() * 1000, 2)
