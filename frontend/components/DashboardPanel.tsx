// components/DashboardPanel.tsx

import type { ReactNode } from "react";

interface DashboardPanelProps {
  title: string;
  icon?: ReactNode;
  children: ReactNode;
  headerRight?: ReactNode;
  className?: string;
}

export default function DashboardPanel({
  title,
  icon,
  children,
  headerRight,
  className = "",
}: DashboardPanelProps) {
  return (
    <div
      className={`rounded-xl border border-sentinel-border bg-sentinel-panel p-5 shadow-panel ${className}`}
    >
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          {icon}
          <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400">
            {title}
          </h2>
        </div>
        {headerRight}
      </div>
      <div>{children}</div>
    </div>
  );
}
