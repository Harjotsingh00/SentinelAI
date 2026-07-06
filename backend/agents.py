"""
agents.py

Defines the five autonomous agents that make up SentinelAI's
multi-agent emergency response pipeline:

  1. SituationAgent      - classifies the disaster & estimates severity/risk
  2. WeatherAgent         - fetches live weather & assesses escalation risk
  3. ResourceAgent        - estimates responder resources needed
  4. CommunicationAgent   - drafts public-facing communication (via NVIDIA NIM)
  5. DecisionAgent        - synthesizes everything into a final action plan

Each agent is intentionally provider-agnostic in its public interface
(run(...) -> pydantic model) so agent_manager.py can orchestrate them,
track timing, and swap implementations (e.g. Gemini vs NVIDIA NIM)
without touching orchestration logic.

NOTE ON GOOGLE ADK:
  Google's Agent Development Kit (ADK) is designed to wrap exactly this
  kind of "agent with a role, a prompt, and a tool" pattern into a
  formal Agent/Runner object with built-in session + tool-calling
  support. This file defines each agent as a plain Python class with a
  single async run() method so the orchestration is transparent and
  testable in Sprint 1. Sprint 2 wires these into actual
  google.adk.agents.Agent / Runner objects (session state, ADK tools
  for weather + NIM) — the prompts and schemas below do not change,
  only the execution wrapper does.
"""

import logging
from typing import Optional

from ai_client import call_gemini, call_nvidia_nim
from models import (
    CommunicationOutput,
    DecisionOutput,
    DisasterType,
    IncidentRequest,
    ResourceAllocation,
    SeverityLevel,
    SituationAnalysis,
    WeatherAnalysis,
)
from prompts import (
    COMMUNICATION_AGENT_PROMPT,
    DECISION_AGENT_PROMPT,
    RESOURCE_AGENT_PROMPT,
    SITUATION_AGENT_PROMPT,
    WEATHER_AGENT_PROMPT,
)
from utils import extract_json
from weather import get_current_weather

logger = logging.getLogger("sentinelai.agents")


class SituationAgent:
    name = "Situation Agent"

    async def run(self, request: IncidentRequest) -> SituationAnalysis:
        prompt = SITUATION_AGENT_PROMPT.format(
            description=request.description,
            location_name=request.location_name,
            latitude=request.latitude,
            longitude=request.longitude,
            reported_disaster_type=request.reported_disaster_type.value
            if request.reported_disaster_type
            else "unknown",
            affected_population_estimate=request.affected_population_estimate or "unknown",
        )
        raw = await call_gemini(prompt, temperature=0.2)
        data = extract_json(raw)
        return SituationAnalysis(**data)


class WeatherAgent:
    name = "Weather Agent"

    async def run(self, request: IncidentRequest, situation: SituationAnalysis) -> WeatherAnalysis:
        weather_data = await get_current_weather(request.latitude, request.longitude)

        if weather_data is None:
            # Graceful degradation: no live data available, still produce a
            # reasoned estimate so the pipeline doesn't break.
            weather_data_str = "No live weather data available for this location."
        else:
            weather_data_str = str(weather_data)

        prompt = WEATHER_AGENT_PROMPT.format(
            weather_data=weather_data_str,
            situation_summary=situation.summary,
            disaster_type=situation.disaster_type.value,
            severity=situation.severity.value,
        )
        raw = await call_gemini(prompt, temperature=0.2)
        data = extract_json(raw)

        result = WeatherAnalysis(**data)
        if weather_data:
            result.temperature_celsius = weather_data.get("temperature_celsius")
            result.condition = weather_data.get("condition")
            result.wind_speed_kmh = weather_data.get("wind_speed_kmh")
            result.humidity_percent = weather_data.get("humidity_percent")
        return result


class ResourceAgent:
    name = "Resource Agent"

    async def run(
        self,
        request: IncidentRequest,
        situation: SituationAnalysis,
        weather: WeatherAnalysis,
    ) -> ResourceAllocation:
        prompt = RESOURCE_AGENT_PROMPT.format(
            situation_summary=situation.summary,
            disaster_type=situation.disaster_type.value,
            severity=situation.severity.value,
            risk_score=situation.risk_score,
            escalation_risk=weather.escalation_risk.value,
            affected_population_estimate=request.affected_population_estimate or "unknown",
        )
        raw = await call_gemini(prompt, temperature=0.3)
        data = extract_json(raw)
        return ResourceAllocation(**data)


class CommunicationAgent:
    """
    Uses NVIDIA NIM (rather than Gemini) to satisfy the hackathon's
    requirement of real NVIDIA integration and to demonstrate a
    genuinely multi-provider agent pipeline.
    """

    name = "Communication Agent"

    SYSTEM_PROMPT = (
        "You are a professional emergency communications officer. "
        "You write calm, clear, non-alarmist public safety messaging. "
        "You always respond with strict JSON only."
    )

    async def run(
        self,
        request: IncidentRequest,
        situation: SituationAnalysis,
    ) -> CommunicationOutput:
        prompt = COMMUNICATION_AGENT_PROMPT.format(
            situation_summary=situation.summary,
            disaster_type=situation.disaster_type.value,
            severity=situation.severity.value,
            location_name=request.location_name,
        )
        try:
            raw = await call_nvidia_nim(prompt, system_prompt=self.SYSTEM_PROMPT, temperature=0.4)
        except RuntimeError as exc:
            logger.warning("NVIDIA NIM unavailable (%s); falling back to Gemini.", exc)
            raw = await call_gemini(prompt, temperature=0.4)

        data = extract_json(raw)
        return CommunicationOutput(**data)


class DecisionAgent:
    name = "Decision Agent"

    async def run(
        self,
        situation: SituationAnalysis,
        weather: WeatherAnalysis,
        resources: ResourceAllocation,
        communication: CommunicationOutput,
    ) -> DecisionOutput:
        prompt = DECISION_AGENT_PROMPT.format(
            situation_json=situation.model_dump_json(),
            weather_json=weather.model_dump_json(),
            resources_json=resources.model_dump_json(),
            communication_json=communication.model_dump_json(),
        )
        raw = await call_gemini(prompt, temperature=0.2)
        data = extract_json(raw)
        return DecisionOutput(**data)
