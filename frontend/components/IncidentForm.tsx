// components/IncidentForm.tsx

"use client";

import { useState } from "react";
import type { IncidentRequest } from "@/types/incident";

interface IncidentFormProps {
  onSubmit: (payload: IncidentRequest) => void;
  isSubmitting: boolean;
}

export default function IncidentForm({ onSubmit, isSubmitting }: IncidentFormProps) {
  const [locationName, setLocationName] = useState("");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [description, setDescription] = useState("");
  const [affectedPopulation, setAffectedPopulation] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    const payload: IncidentRequest = {
      location_name: locationName,
      latitude: parseFloat(latitude),
      longitude: parseFloat(longitude),
      description,
      affected_population_estimate: affectedPopulation
        ? parseInt(affectedPopulation, 10)
        : null,
    };

    onSubmit(payload);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" suppressHydrationWarning>
      <div>
        <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-gray-400">
          Location Name
        </label>
        <input
          suppressHydrationWarning
          required
          value={locationName}
          onChange={(e) => setLocationName(e.target.value)}
          placeholder="e.g. Chennai, India"
          className="w-full rounded-lg border border-sentinel-border bg-sentinel-bg px-3 py-2 text-sm text-gray-100 outline-none focus:border-sentinel-accent"
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-gray-400">
            Latitude
          </label>
          <input
          suppressHydrationWarning
            required
            type="number"
            step="any"
            value={latitude}
            onChange={(e) => setLatitude(e.target.value)}
            placeholder="13.0827"
            className="w-full rounded-lg border border-sentinel-border bg-sentinel-bg px-3 py-2 text-sm text-gray-100 outline-none focus:border-sentinel-accent"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-gray-400">
            Longitude
          </label>
          <input
          suppressHydrationWarning
            required
            type="number"
            step="any"
            value={longitude}
            onChange={(e) => setLongitude(e.target.value)}
            placeholder="80.2707"
            className="w-full rounded-lg border border-sentinel-border bg-sentinel-bg px-3 py-2 text-sm text-gray-100 outline-none focus:border-sentinel-accent"
          />
        </div>
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-gray-400">
          Incident Description
        </label>
        <textarea
          suppressHydrationWarning
          required
          minLength={10}
          rows={4}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Describe what is being observed on the ground..."
          className="w-full resize-none rounded-lg border border-sentinel-border bg-sentinel-bg px-3 py-2 text-sm text-gray-100 outline-none focus:border-sentinel-accent"
        />
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-gray-400">
          Estimated Affected Population (optional)
        </label>
        <input
          suppressHydrationWarning
          type="number"
          min={0}
          value={affectedPopulation}
          onChange={(e) => setAffectedPopulation(e.target.value)}
          placeholder="e.g. 5000"
          className="w-full rounded-lg border border-sentinel-border bg-sentinel-bg px-3 py-2 text-sm text-gray-100 outline-none focus:border-sentinel-accent"
        />
      </div>

      <button
        suppressHydrationWarning
        type="submit"
        disabled={isSubmitting}
        className="w-full rounded-lg bg-sentinel-accent px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-600 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isSubmitting ? "Running Agent Pipeline..." : "Report Incident"}
      </button>
    </form>
  );
}
