"""
app.py

FastAPI application entrypoint for SentinelAI.

Endpoints:
  GET  /health                -> service + integration health check
  POST /api/incidents         -> run the full multi-agent pipeline on a
                                  newly reported incident and return the
                                  aggregated dashboard payload
"""

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agent_manager import agent_manager
from config import get_settings
from models import HealthResponse, IncidentRequest, IncidentResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sentinelai.app")

settings = get_settings()

app = FastAPI(
    title="SentinelAI",
    description="AI-Powered Emergency Intelligence Platform — multi-agent backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check() -> HealthResponse:
    """Lightweight health + configuration check, used by the frontend
    to show integration status badges and by deployment platforms
    (Render) as the health probe endpoint."""
    return HealthResponse(
        status="ok",
        environment=settings.ENVIRONMENT,
        gemini_configured=bool(settings.GOOGLE_API_KEY),
        nvidia_configured=bool(settings.NVIDIA_API_KEY),
        weather_configured=bool(settings.OPENWEATHER_API_KEY),
    )


@app.post("/api/incidents", response_model=IncidentResponse, tags=["incidents"])
async def create_incident(request: IncidentRequest) -> IncidentResponse:
    """
    Run the full SentinelAI multi-agent pipeline for a newly reported
    incident:

        Situation -> Weather -> Resource -> Communication -> Decision

    Returns the aggregated result consumed directly by the dashboard.
    """
    try:
        return await agent_manager.run_pipeline(request)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Incident pipeline failed")
        raise HTTPException(
            status_code=502,
            detail=f"Incident pipeline failed: {exc}",
        ) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=settings.PORT, reload=not settings.is_production)
