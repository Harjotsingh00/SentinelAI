// components/AgentStatusTimeline.tsx

import type { AgentExecutionRecord, AgentStatusType } from "@/types/incident";

const STATUS_STYLES: Record<AgentStatusType, string> = {
  IDLE: "bg-gray-500",
  RUNNING: "bg-blue-500 animate-pulse",
  COMPLETED: "bg-emerald-500",
  FAILED: "bg-red-500",
};

export default function AgentStatusTimeline({
  records,
}: {
  records: AgentExecutionRecord[];
}) {
  if (records.length === 0) {
    return (
      <p className="text-sm text-gray-500">
        No agent activity yet. Submit an incident to start the pipeline.
      </p>
    );
  }

  return (
    <ol className="space-y-4">
      {records.map((record, idx) => (
        <li key={`${record.agent_name}-${idx}`} className="flex items-start gap-3">
          <span
            className={`mt-1 h-2.5 w-2.5 flex-shrink-0 rounded-full ${STATUS_STYLES[record.status]}`}
          />
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-200">{record.agent_name}</span>
              <span className="text-xs text-gray-500">{record.status}</span>
            </div>
            {record.duration_ms != null && (
              <p className="text-xs text-gray-500">{record.duration_ms} ms</p>
            )}
            {record.error && (
              <p className="mt-1 text-xs text-red-400">{record.error}</p>
            )}
          </div>
        </li>
      ))}
    </ol>
  );
}
