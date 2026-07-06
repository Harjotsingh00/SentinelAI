"""
agent_manager.py

Sprint 2: orchestrates the SentinelAI pipeline through a real
google.adk.runners.Runner against a google.adk.sessions.Session, instead
of Sprint 1's hand-rolled sequential async calls.

Public interface is unchanged from Sprint 1 (`agent_manager.run_pipeline`
returns an IncidentResponse) so app.py did not need to change at all —
only the execution layer underneath was swapped for real ADK.

Per-agent timing for the dashboard's "Agent Status" timeline is derived
from the Runner's event stream: ADK emits one or more Events per
sub-agent turn (e.g. a function-call event and a final-response event
for weather_fetch_agent), all tagged with the same `event.author`. We
open a timeline span whenever the author changes and close it when the
next author appears (or the run ends), which gives one timing record
per sub-agent — exactly what Sprint 1's hand-rolled version produced.
"""

import logging
from typing import Any, Optional, Type, TypeVar

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from pydantic import BaseModel

from adk_agents import APP_NAME, AGENT_DISPLAY_NAMES, root_agent
from models import (
    AgentExecutionRecord,
    AgentStatus,
    CommunicationOutput,
    DecisionOutput,
    IncidentRequest,
    IncidentResponse,
    ResourceAllocation,
    SituationAnalysis,
    WeatherAnalysis,
)
from utils import duration_ms, extract_json, new_incident_id, utc_now

logger = logging.getLogger("sentinelai.agent_manager")

T = TypeVar("T", bound=BaseModel)

USER_ID = "eoc_operator"


def _coerce_model(value: Any, model_cls: Type[T]) -> Optional[T]:
    """Session state may hold a dict (typical for output_schema agents),
    a JSON string, or be missing entirely. Normalize all three into the
    target Pydantic model."""
    if value is None:
        return None
    if isinstance(value, model_cls):
        return value
    if isinstance(value, dict):
        return model_cls(**value)
    if isinstance(value, str):
        return model_cls(**extract_json(value))
    raise TypeError(f"Cannot coerce {type(value)} into {model_cls.__name__}")


class AgentManager:
    """Coordinates the SentinelAI ADK pipeline for a single incident."""

    def __init__(self) -> None:
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=self.session_service,
        )

    async def run_pipeline(self, request: IncidentRequest) -> IncidentResponse:
        incident_id = new_incident_id()
        created_at = utc_now()
        session_id = incident_id  # one ADK session per incident

        initial_state = {
            "location_name": request.location_name,
            "latitude": request.latitude,
            "longitude": request.longitude,
            "description": request.description,
            "reported_disaster_type": (
                request.reported_disaster_type.value
                if request.reported_disaster_type
                else "unknown"
            ),
            "affected_population_estimate": request.affected_population_estimate or "unknown",
        }

        await self.session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
            state=initial_state,
        )

        user_message = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=f"New incident reported: {request.description}")],
        )

        timeline: list[AgentExecutionRecord] = []
        current_author: Optional[str] = None
        step_started_at = utc_now()

        def _close_span(author: str, ended_at, failed: bool = False, error: Optional[str] = None):
            timeline.append(
                AgentExecutionRecord(
                    agent_name=AGENT_DISPLAY_NAMES.get(author, author),
                    status=AgentStatus.FAILED if failed else AgentStatus.COMPLETED,
                    started_at=step_started_at,
                    completed_at=ended_at,
                    duration_ms=duration_ms(step_started_at, ended_at),
                    error=error,
                )
            )

        try:
            async for event in self.runner.run_async(
                user_id=USER_ID,
                session_id=session_id,
                new_message=user_message,
            ):
                author = getattr(event, "author", None)
                if author and author != current_author:
                    now = utc_now()
                    if current_author:
                        _close_span(current_author, now)
                    current_author = author
                    step_started_at = now

            if current_author:
                _close_span(current_author, utc_now())

        except Exception as exc:  # noqa: BLE001
            if current_author:
                _close_span(current_author, utc_now(), failed=True, error=str(exc))
            logger.exception("SentinelAI ADK pipeline failed")
            raise

        final_session = await self.session_service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )
        state = final_session.state

        situation = _coerce_model(state.get("situation"), SituationAnalysis)
        weather = _coerce_model(state.get("weather"), WeatherAnalysis)
        resources = _coerce_model(state.get("resources"), ResourceAllocation)
        communication = _coerce_model(state.get("communication_raw"), CommunicationOutput)
        decision = _coerce_model(state.get("decision"), DecisionOutput)

        return IncidentResponse(
            incident_id=incident_id,
            created_at=created_at,
            request=request,
            situation=situation,
            weather=weather,
            resources=resources,
            communication=communication,
            decision=decision,
            agent_timeline=timeline,
        )


# Singleton instance used by app.py
agent_manager = AgentManager()
