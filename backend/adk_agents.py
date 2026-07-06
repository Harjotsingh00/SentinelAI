"""
adk_agents.py

Sprint 2: the REAL Google ADK wiring for SentinelAI's multi-agent
pipeline (Sprint 1 shipped a plain-Python stand-in with the same
prompts/schemas — this file replaces the execution layer only).

Architecture — a google.adk.agents.SequentialAgent chaining six
sub-agents, all sharing one ADK Session so each agent can read the
prior agents' structured output straight out of session state via
ADK's `{state_key}` instruction templating:

    situation_agent        (Gemini, output_schema=SituationAnalysis)
        -> weather_fetch_agent   (Gemini, calls a real ADK FunctionTool
                                   that hits OpenWeather)
        -> weather_analysis_agent(Gemini, output_schema=WeatherAnalysis)
    -> resource_agent      (Gemini, output_schema=ResourceAllocation)
    -> communication_agent (NVIDIA NIM via ADK's LiteLlm model wrapper)
    -> decision_agent      (Gemini, output_schema=DecisionOutput)

NOTE ON output_schema + NVIDIA NIM:
  ADK's `output_schema` (structured output) maps to Gemini's native
  response_schema feature and is well supported for Gemini-backed
  agents. Many open-weight models hosted on NVIDIA NIM don't reliably
  support strict JSON-schema-constrained decoding through the
  OpenAI-compatible endpoint, so the Communication Agent instead uses
  a plain "respond with JSON only" instruction (same approach as
  Sprint 1's prompts.py) and we validate/parse its output ourselves
  with utils.extract_json after the run completes. This is a
  deliberate reliability choice, not an oversight.
"""

from typing import Any, Dict

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm

from config import get_settings
from models import (
    DecisionOutput,
    ResourceAllocation,
    SituationAnalysis,
    WeatherAnalysis,
)
from weather import get_current_weather

settings = get_settings()

APP_NAME = "sentinelai"

# Human-readable labels for the dashboard's Agent Status timeline,
# keyed by each sub-agent's ADK `name` (which is what shows up as
# `event.author` when the Runner streams events).
AGENT_DISPLAY_NAMES: Dict[str, str] = {
    "situation_agent": "Situation Agent",
    "weather_fetch_agent": "Weather Agent (data retrieval)",
    "weather_analysis_agent": "Weather Agent (impact analysis)",
    "resource_agent": "Resource Agent",
    "communication_agent": "Communication Agent",
    "decision_agent": "Decision Agent",
}


# ---------------------------------------------------------------------------
# Real ADK tool: the Weather Agent calls this itself (genuine tool-calling,
# not a pre-fetch hidden from the model).
# ---------------------------------------------------------------------------
async def fetch_live_weather_tool(latitude: float, longitude: float) -> dict:
    """Fetches current live weather conditions for a coordinate pair.

    Args:
        latitude: Latitude of the incident location.
        longitude: Longitude of the incident location.

    Returns:
        A dict with a 'status' field ('success' or 'unavailable') and,
        on success, temperature_celsius, condition, wind_speed_kmh,
        humidity_percent, and related fields.
    """
    data = await get_current_weather(latitude, longitude)
    if data is None:
        return {
            "status": "unavailable",
            "message": "Live weather data could not be retrieved for this location.",
        }
    return {"status": "success", **data}


# ---------------------------------------------------------------------------
# 1. Situation Agent
# ---------------------------------------------------------------------------
situation_agent = LlmAgent(
    name="situation_agent",
    model=settings.GEMINI_MODEL,
    description="Classifies the disaster type and estimates severity and risk.",
    instruction="""You are the Situation Analysis Agent inside SentinelAI, an
Emergency Operations Center (EOC) platform.

Incident description reported by the field operator:
{description}

Location: {location_name} (latitude {latitude}, longitude {longitude})
Operator's disaster type hint (may be "unknown"): {reported_disaster_type}
Estimated affected population (may be "unknown"): {affected_population_estimate}

Classify the disaster type, estimate a severity level (LOW, MODERATE, HIGH,
or CRITICAL), estimate a numeric risk score from 0 to 100, write a concise
2-3 sentence professional incident summary suitable for an EOC dashboard,
and list the 3-5 most important key hazards responders should be aware of.
""",
    output_schema=SituationAnalysis,
    output_key="situation",
)


# ---------------------------------------------------------------------------
# 2. Weather Fetch Agent — genuinely calls the live weather tool
# ---------------------------------------------------------------------------
weather_fetch_agent = LlmAgent(
    name="weather_fetch_agent",
    model=settings.GEMINI_MODEL,
    description="Retrieves live weather data for the incident location using a tool call.",
    instruction="""You are the Weather Retrieval Agent inside SentinelAI.

Call the fetch_live_weather_tool function exactly once with:
  latitude = {latitude}
  longitude = {longitude}

Then respond with ONLY the raw JSON result from the tool call, and nothing else.
""",
    tools=[fetch_live_weather_tool],
    output_key="live_weather_raw",
)


# ---------------------------------------------------------------------------
# 3. Weather Analysis Agent — reasons over the fetched data
# ---------------------------------------------------------------------------
weather_analysis_agent = LlmAgent(
    name="weather_analysis_agent",
    model=settings.GEMINI_MODEL,
    description="Assesses whether current weather will escalate the emergency.",
    instruction="""You are the Weather Impact Agent inside SentinelAI.

Live weather data retrieved for the incident location:
{live_weather_raw}

Situation analysis from the previous agent:
{situation}

Assess the weather escalation risk (LOW, MODERATE, HIGH, or CRITICAL) and
write a 1-3 sentence impact summary explaining how weather affects response
and risk. If the live weather data includes temperature, wind speed, or
humidity, include those exact values in your structured output; otherwise
leave those fields null. If the data is unavailable, reason from the
disaster type and general seasonal expectations instead, and say so in
your summary.
""",
    output_schema=WeatherAnalysis,
    output_key="weather",
)


# ---------------------------------------------------------------------------
# 4. Resource Agent
# ---------------------------------------------------------------------------
resource_agent = LlmAgent(
    name="resource_agent",
    model=settings.GEMINI_MODEL,
    description="Estimates responder resources required for the incident.",
    instruction="""You are the Resource Allocation Agent inside SentinelAI.

Situation analysis:
{situation}

Weather impact analysis:
{weather}

Estimated affected population (may be "unknown"): {affected_population_estimate}

Estimate the number of ambulances, rescue teams, police units, shelters,
medical kits, and food supply units required to respond effectively, and
give a 1-2 sentence justification for your estimate.
""",
    output_schema=ResourceAllocation,
    output_key="resources",
)


# ---------------------------------------------------------------------------
# 5. Communication Agent — runs on NVIDIA NIM via ADK's LiteLlm wrapper
# ---------------------------------------------------------------------------
def _build_communication_model():
    """Use NVIDIA NIM if configured (satisfies the hackathon's NVIDIA
    integration requirement); otherwise fall back to Gemini so the
    pipeline still runs end-to-end without a NIM key."""
    if settings.NVIDIA_API_KEY:
        return LiteLlm(
            model=f"openai/{settings.NVIDIA_NIM_MODEL}",
            api_base=settings.NVIDIA_NIM_BASE_URL,
            api_key=settings.NVIDIA_API_KEY,
        )
    return settings.GEMINI_MODEL


communication_agent = LlmAgent(
    name="communication_agent",
    model=_build_communication_model(),
    description="Drafts public-facing emergency communication.",
    instruction="""You are a professional emergency communications officer
inside SentinelAI. You write calm, clear, non-alarmist public safety
messaging.

Situation summary: {situation}
Location: {location_name}

Draft:
1. A short urgent public-facing alert (1-2 sentences)
2. An SMS message (under 160 characters)
3. An email to registered residents (3-5 sentences)
4. A formal press release (4-6 sentences)

Respond with ONLY a single JSON object with exactly these four string keys:
public_alert, sms_message, email_message, press_release.
Do not include markdown code fences, labels, or any text outside the JSON object.
""",
    output_key="communication_raw",
)


# ---------------------------------------------------------------------------
# 6. Decision Agent
# ---------------------------------------------------------------------------
decision_agent = LlmAgent(
    name="decision_agent",
    model=settings.GEMINI_MODEL,
    description="Synthesizes all agent outputs into a final action plan.",
    instruction="""You are the Decision Coordination Agent inside SentinelAI.
Synthesize the outputs below into a final action plan for EOC commanders.

Situation: {situation}
Weather: {weather}
Resources: {resources}
Communication plan (raw): {communication_raw}

Produce an ordered list of concrete action-plan steps, a confidence score
from 0 to 100, an overall priority (LOW, MODERATE, HIGH, or CRITICAL), and
a 2-3 sentence explanation of your reasoning.
""",
    output_schema=DecisionOutput,
    output_key="decision",
)


# ---------------------------------------------------------------------------
# Root pipeline — deterministic, ordered execution via SequentialAgent
# ---------------------------------------------------------------------------
root_agent = SequentialAgent(
    name="sentinelai_pipeline",
    description="SentinelAI's full emergency-response multi-agent pipeline.",
    sub_agents=[
        situation_agent,
        weather_fetch_agent,
        weather_analysis_agent,
        resource_agent,
        communication_agent,
        decision_agent,
    ],
)
