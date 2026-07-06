// types/incident.ts
// Mirrors backend/models.py exactly — keep these two files in sync.

export type SeverityLevel = "LOW" | "MODERATE" | "HIGH" | "CRITICAL";

export type AgentStatusType = "IDLE" | "RUNNING" | "COMPLETED" | "FAILED";

export type DisasterType =
  | "FLOOD"
  | "EARTHQUAKE"
  | "WILDFIRE"
  | "HURRICANE"
  | "LANDSLIDE"
  | "INDUSTRIAL_ACCIDENT"
  | "OTHER";

export interface IncidentRequest {
  location_name: string;
  latitude: number;
  longitude: number;
  description: string;
  reported_disaster_type?: DisasterType | null;
  affected_population_estimate?: number | null;
}

export interface SituationAnalysis {
  disaster_type: DisasterType;
  severity: SeverityLevel;
  risk_score: number;
  summary: string;
  key_hazards: string[];
}

export interface WeatherAnalysis {
  temperature_celsius?: number | null;
  condition?: string | null;
  wind_speed_kmh?: number | null;
  humidity_percent?: number | null;
  escalation_risk: SeverityLevel;
  impact_summary: string;
}

export interface ResourceAllocation {
  ambulances: number;
  rescue_teams: number;
  police_units: number;
  shelters: number;
  medical_kits: number;
  food_supplies_units: number;
  justification: string;
}

export interface CommunicationOutput {
  public_alert: string;
  sms_message: string;
  email_message: string;
  press_release: string;
}

export interface DecisionOutput {
  action_plan: string[];
  confidence_score: number;
  priority: SeverityLevel;
  reasoning: string;
}

export interface AgentExecutionRecord {
  agent_name: string;
  status: AgentStatusType;
  started_at?: string | null;
  completed_at?: string | null;
  duration_ms?: number | null;
  error?: string | null;
}

export interface IncidentResponse {
  incident_id: string;
  created_at: string;
  request: IncidentRequest;
  situation?: SituationAnalysis | null;
  weather?: WeatherAnalysis | null;
  resources?: ResourceAllocation | null;
  communication?: CommunicationOutput | null;
  decision?: DecisionOutput | null;
  agent_timeline: AgentExecutionRecord[];
}

export interface HealthResponse {
  status: string;
  environment: string;
  gemini_configured: boolean;
  nvidia_configured: boolean;
  weather_configured: boolean;
}
