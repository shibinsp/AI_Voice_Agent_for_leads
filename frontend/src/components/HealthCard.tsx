import { AlertTriangle, Server } from "lucide-react";

import type { HealthResponse } from "../types/api";
import { Panel } from "./Panel";
import { StatusPill } from "./StatusPill";

interface HealthCardProps {
  health?: HealthResponse;
  baseUrl: string;
  isLoading: boolean;
  isFetching: boolean;
  error?: string;
}

export function HealthCard({
  health,
  baseUrl,
  isLoading,
  isFetching,
  error,
}: HealthCardProps) {
  return (
    <Panel
      id="health"
      title="Backend Pulse"
      eyebrow="Health"
      subtitle="Connectivity snapshot for the FastAPI service."
    >
      <div className="health-card">
        <div className="health-row">
          <span className="health-label">
            <Server size={16} />
            Backend
          </span>
          <StatusPill status={health ? "live" : "down"} />
        </div>

        <dl className="key-value-list">
          <div>
            <dt>API Base</dt>
            <dd>{baseUrl}</dd>
          </div>
          <div>
            <dt>Environment</dt>
            <dd>{health?.environment ?? (isLoading ? "Checking..." : "Unavailable")}</dd>
          </div>
          <div>
            <dt>Application</dt>
            <dd>{health?.app ?? "No response yet"}</dd>
          </div>
          <div>
            <dt>Refresh State</dt>
            <dd>{isFetching ? "Polling" : "Idle"}</dd>
          </div>
        </dl>

        {error ? (
          <div className="inline-alert">
            <AlertTriangle size={16} />
            <span>{error}</span>
          </div>
        ) : null}
      </div>
    </Panel>
  );
}
