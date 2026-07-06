// components/SeverityBadge.tsx

import type { SeverityLevel } from "@/types/incident";

const SEVERITY_STYLES: Record<SeverityLevel, string> = {
  LOW: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  MODERATE: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  HIGH: "bg-orange-500/15 text-orange-400 border-orange-500/30",
  CRITICAL: "bg-red-500/15 text-red-400 border-red-500/30",
};

export default function SeverityBadge({ level }: { level: SeverityLevel }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold tracking-wide uppercase ${SEVERITY_STYLES[level]}`}
    >
      {level}
    </span>
  );
}
