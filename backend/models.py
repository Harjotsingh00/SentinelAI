"""
models.py

Pydantic data models shared across the SentinelAI backend.
These define the contract between the FastAPI routes, the agent layer,
and the frontend dashboard.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AgentStatus(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DisasterType(str, Enum):
    FLOOD = "FLOOD"
    EARTHQUAKE = "EARTHQUAKE"
    WILDFIRE = "WILDFIRE"
    HURRICANE = "HURRICANE"
    LANDSLIDE = "LANDSLIDE"
    INDUSTRIAL_ACCIDENT = "INDUSTRIAL_ACCIDENT"
    OTHER = "OTHER"


# ---------------------------------------------------------------------------
# Incoming request from the dashboard when an operator reports an incident
# ---------------------------------------------------------------------------
class IncidentRequest(BaseModel):
    location_name: str = Field(..., description="Human readable location, e.g. 'Chennai, India'")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    description: str = Field(..., min_length=10, description="Free-text description of the incident")
    reported_disaster_type: Optional[DisasterType] = Field(
        default=None, description="Optional operator hint of disaster type"
    )
    affected_population_estimate: Optional[int] = Field(
        default=None, ge=0, description="Optional rough estimate of people affected"
    )


# ---------------------------------------------------------------------------
# Individual agent outputs
# ---------------------------------------------------------------------------
class SituationAnalysis(BaseModel):
    disaster_type: DisasterType
    severity: SeverityLevel
    risk_score: float = Field(..., ge=0, le=100)
    summary: str
    key_hazards: List[str] = Field(default_factory=list)


class WeatherAnalysis(BaseModel):
    temperature_celsius: Optional[float] = None
    condition: Optional[str] = None
    wind_speed_kmh: Optional[float] = None
    humidity_percent: Optional[float] = None
    escalation_risk: SeverityLevel
    impact_summary: str


class ResourceAllocation(BaseModel):
    ambulances: int = Field(..., ge=0)
    rescue_teams: int = Field(..., ge=0)
    police_units: int = Field(..., ge=0)
    shelters: int = Field(..., ge=0)
    medical_kits: int = Field(..., ge=0)
    food_supplies_units: int = Field(..., ge=0)
    justification: str


class CommunicationOutput(BaseModel):
    public_alert: str
    sms_message: str
    email_message: str
    press_release: str


class DecisionOutput(BaseModel):
    action_plan: List[str]
    confidence_score: float = Field(..., ge=0, le=100)
    priority: SeverityLevel
    reasoning: str


# ---------------------------------------------------------------------------
# Per-agent execution metadata (for the dashboard "Agent Status" panel)
# ---------------------------------------------------------------------------
class AgentExecutionRecord(BaseModel):
    agent_name: str
    status: AgentStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Final aggregated response returned to the frontend dashboard
# ---------------------------------------------------------------------------
class IncidentResponse(BaseModel):
    incident_id: str
    created_at: datetime
    request: IncidentRequest

    situation: Optional[SituationAnalysis] = None
    weather: Optional[WeatherAnalysis] = None
    resources: Optional[ResourceAllocation] = None
    communication: Optional[CommunicationOutput] = None
    decision: Optional[DecisionOutput] = None

    agent_timeline: List[AgentExecutionRecord] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    environment: str
    gemini_configured: bool
    nvidia_configured: bool
    weather_configured: bool
