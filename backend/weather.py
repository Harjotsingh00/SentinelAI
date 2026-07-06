"""
weather.py

Live weather data retrieval via the OpenWeather Current Weather API.
Used by the Weather Agent to ground its escalation analysis in real data.
"""

import logging
from typing import Any, Dict, Optional

import httpx

from config import get_settings

logger = logging.getLogger("sentinelai.weather")

settings = get_settings()

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


async def get_current_weather(latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
    """
    Fetch live weather for a given coordinate pair from OpenWeather.

    Returns a normalized dict, or None if the API key is missing or the
    request fails (callers should degrade gracefully rather than crash
    the whole incident pipeline over a weather outage).
    """
    if not settings.OPENWEATHER_API_KEY:
        logger.warning("OPENWEATHER_API_KEY not configured; skipping live weather fetch.")
        return None

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(OPENWEATHER_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to fetch weather data")
        return None

    return {
        "temperature_celsius": data.get("main", {}).get("temp"),
        "feels_like_celsius": data.get("main", {}).get("feels_like"),
        "humidity_percent": data.get("main", {}).get("humidity"),
        "condition": (data.get("weather") or [{}])[0].get("description"),
        "wind_speed_kmh": round((data.get("wind", {}).get("speed") or 0) * 3.6, 1),
        "cloudiness_percent": data.get("clouds", {}).get("all"),
        "raw_location_name": data.get("name"),
    }
