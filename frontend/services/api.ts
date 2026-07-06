// services/api.ts
// Centralized Axios client for talking to the SentinelAI FastAPI backend.

import axios from "axios";
import type { HealthResponse, IncidentRequest, IncidentResponse } from "@/types/incident";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180000, // 3 minutes — the pipeline runs 5 sequential LLM calls
  headers: {
    "Content-Type": "application/json",
  },
});

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>("/health");
  return data;
}

export async function createIncident(payload: IncidentRequest): Promise<IncidentResponse> {
  const { data } = await apiClient.post<IncidentResponse>("/api/incidents", payload);
  return data;
}
