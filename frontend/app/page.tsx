// app/page.tsx

"use client";

import { useState } from "react";
import DashboardPanel from "@/components/DashboardPanel";
import SeverityBadge from "@/components/SeverityBadge";
import AgentStatusTimeline from "@/components/AgentStatusTimeline";
import IncidentForm from "@/components/IncidentForm";
import { createIncident } from "@/services/api";
import type { IncidentRequest, IncidentResponse } from "@/types/incident";

export default function Home() {
  const [result, setResult] = useState<IncidentResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSubmit(payload: IncidentRequest) {
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const response = await createIncident(payload);
      setResult(response);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to run the SentinelAI agent pipeline.";
      setErrorMessage(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-sentinel-bg px-6 py-8">
      <header className="mx-auto mb-8 flex max-w-7xl items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">
            Sentinel<span className="text-sentinel-accent">AI</span>
          </h1>
          <p className="text-sm text-gray-500">
            AI-Powered Emergency Intelligence Platform — Multi-Agent Operations Center
          </p>
        </div>
        <span className="rounded-full border border-sentinel-border bg-sentinel-panel px-3 py-1 text-xs text-gray-400">
          Gen AI Academy · Cohort 2 · Track 2
        </span>
      </header>

      <div className="mx-auto grid max-w-7xl grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left column: incident intake form */}
        <div className="lg:col-span-1">
          <DashboardPanel title="Report Incident">
            <IncidentForm onSubmit={handleSubmit} isSubmitting={isSubmitting} />
            {errorMessage && (
              <p className="mt-3 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-400">
                {errorMessage}
              </p>
            )}
          </DashboardPanel>

          <div className="mt-6">
            <DashboardPanel title="Agent Status">
              <AgentStatusTimeline records={result?.agent_timeline ?? []} />
            </DashboardPanel>
          </div>
        </div>

        {/* Right column: agent outputs */}
        <div className="space-y-6 lg:col-span-2">
          {!result && (
            <DashboardPanel title="Incident Overview">
              <p className="text-sm text-gray-500">
                No active incident. Submit a report on the left to run the Situation, Weather,
                Resource, Communication, and Decision agents.
              </p>
            </DashboardPanel>
          )}

          {result && (
            <>
              <DashboardPanel
                title="Incident Overview"
                headerRight={
                  result.situation && <SeverityBadge level={result.situation.severity} />
                }
              >
                <p className="mb-2 text-xs text-gray-500">
                  Incident ID: <span className="text-gray-300">{result.incident_id}</span>
                </p>
                <p className="text-sm text-gray-300">{result.situation?.summary}</p>
                {result.situation?.key_hazards && result.situation.key_hazards.length > 0 && (
                  <ul className="mt-3 flex flex-wrap gap-2">
                    {result.situation.key_hazards.map((hazard) => (
                      <li
                        key={hazard}
                        className="rounded-full border border-sentinel-border bg-sentinel-bg px-2.5 py-1 text-xs text-gray-400"
                      >
                        {hazard}
                      </li>
                    ))}
                  </ul>
                )}
              </DashboardPanel>

              <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                <DashboardPanel
                  title="Weather Impact"
                  headerRight={
                    result.weather && <SeverityBadge level={result.weather.escalation_risk} />
                  }
                >
                  <p className="text-sm text-gray-300">{result.weather?.impact_summary}</p>
                  <dl className="mt-3 grid grid-cols-2 gap-2 text-xs text-gray-400">
                    <div>
                      <dt className="text-gray-500">Temperature</dt>
                      <dd>{result.weather?.temperature_celsius ?? "—"} °C</dd>
                    </div>
                    <div>
                      <dt className="text-gray-500">Wind Speed</dt>
                      <dd>{result.weather?.wind_speed_kmh ?? "—"} km/h</dd>
                    </div>
                    <div>
                      <dt className="text-gray-500">Humidity</dt>
                      <dd>{result.weather?.humidity_percent ?? "—"}%</dd>
                    </div>
                    <div>
                      <dt className="text-gray-500">Condition</dt>
                      <dd className="capitalize">{result.weather?.condition ?? "—"}</dd>
                    </div>
                  </dl>
                </DashboardPanel>

                <DashboardPanel title="Resource Allocation">
                  {result.resources && (
                    <dl className="grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <dt className="text-xs text-gray-500">Ambulances</dt>
                        <dd className="text-lg font-semibold text-gray-100">
                          {result.resources.ambulances}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-xs text-gray-500">Rescue Teams</dt>
                        <dd className="text-lg font-semibold text-gray-100">
                          {result.resources.rescue_teams}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-xs text-gray-500">Police Units</dt>
                        <dd className="text-lg font-semibold text-gray-100">
                          {result.resources.police_units}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-xs text-gray-500">Shelters</dt>
                        <dd className="text-lg font-semibold text-gray-100">
                          {result.resources.shelters}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-xs text-gray-500">Medical Kits</dt>
                        <dd className="text-lg font-semibold text-gray-100">
                          {result.resources.medical_kits}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-xs text-gray-500">Food Supplies</dt>
                        <dd className="text-lg font-semibold text-gray-100">
                          {result.resources.food_supplies_units}
                        </dd>
                      </div>
                    </dl>
                  )}
                  {result.resources?.justification && (
                    <p className="mt-3 text-xs text-gray-500">{result.resources.justification}</p>
                  )}
                </DashboardPanel>
              </div>

              <DashboardPanel title="Public Communication">
                {result.communication && (
                  <div className="space-y-3 text-sm">
                    <div>
                      <p className="text-xs uppercase text-gray-500">Public Alert</p>
                      <p className="text-gray-200">{result.communication.public_alert}</p>
                    </div>
                    <div>
                      <p className="text-xs uppercase text-gray-500">SMS</p>
                      <p className="text-gray-300">{result.communication.sms_message}</p>
                    </div>
                    <div>
                      <p className="text-xs uppercase text-gray-500">Email</p>
                      <p className="text-gray-300">{result.communication.email_message}</p>
                    </div>
                    <div>
                      <p className="text-xs uppercase text-gray-500">Press Release</p>
                      <p className="text-gray-300">{result.communication.press_release}</p>
                    </div>
                  </div>
                )}
              </DashboardPanel>

              <DashboardPanel
                title="Final Decision"
                headerRight={
                  result.decision && <SeverityBadge level={result.decision.priority} />
                }
              >
                {result.decision && (
                  <>
                    <p className="mb-3 text-sm text-gray-300">{result.decision.reasoning}</p>
                    <div className="mb-3 flex items-center gap-2">
                      <span className="text-xs text-gray-500">Confidence Score:</span>
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-sentinel-bg">
                        <div
                          className="h-full bg-sentinel-accent"
                          style={{ width: `${result.decision.confidence_score}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-300">
                        {result.decision.confidence_score}%
                      </span>
                    </div>
                    <ol className="list-inside list-decimal space-y-1 text-sm text-gray-300">
                      {result.decision.action_plan.map((step, idx) => (
                        <li key={idx}>{step}</li>
                      ))}
                    </ol>
                  </>
                )}
              </DashboardPanel>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
