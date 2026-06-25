import { TrendingUp } from "lucide-react";

import type { AnalyticsSummary } from "../types/api";
import { Panel } from "./Panel";

interface AnalyticsPanelProps {
  data?: AnalyticsSummary;
  isLoading: boolean;
}

const OUTCOME_LABELS: Record<string, string> = {
  qualified: "Qualified",
  callback_requested: "Callback",
  needs_review: "Needs review",
  not_qualified: "Not qualified",
};

export function AnalyticsPanel({ data, isLoading }: AnalyticsPanelProps) {
  const q = data?.qualification;
  const outcomes = q?.by_outcome ?? {};
  const outcomeTotal = Object.values(outcomes).reduce((a, b) => a + b, 0);

  return (
    <Panel
      id="analytics"
      title="Analytics"
      eyebrow="Insights"
      subtitle="Conversion and qualification performance across all enquiries."
    >
      {isLoading && !data ? (
        <div className="skeleton-stack" aria-label="Loading analytics">
          <span />
          <span />
        </div>
      ) : (
        <>
          <div className="analytics-tiles">
            <div className="analytics-tile">
              <span>Genuine rate</span>
              <strong>{Math.round((q?.genuine_rate ?? 0) * 100)}%</strong>
              <small>{q?.genuine ?? 0} of {q?.total ?? 0} qualified</small>
            </div>
            <div className="analytics-tile">
              <span>Avg. score</span>
              <strong>{q?.avg_score ?? 0}</strong>
              <small>across {q?.total ?? 0} calls</small>
            </div>
            <div className="analytics-tile">
              <span>Sessions done</span>
              <strong>{data?.sessions.completed ?? 0}</strong>
              <small>of {data?.sessions.total ?? 0} started</small>
            </div>
            <div className="analytics-tile">
              <span>Sent to client</span>
              <strong>{data?.handoffs.sent ?? 0}</strong>
              <small>{data?.handoffs.total ?? 0} handoffs</small>
            </div>
          </div>

          <div className="analytics-section">
            <header className="analytics-bar-head">
              <TrendingUp size={14} />
              <span>Qualification outcomes</span>
            </header>
            {outcomeTotal === 0 ? (
              <p className="muted-inline">No qualified calls yet.</p>
            ) : (
              <div className="analytics-bars">
                {Object.entries(outcomes).map(([key, value]) => (
                  <div key={key} className="analytics-bar-row">
                    <span className="analytics-bar-label">{OUTCOME_LABELS[key] ?? key}</span>
                    <div className="analytics-bar-track">
                      <div
                        className={`analytics-bar-fill analytics-bar-fill--${key.replace(/_/g, "-")}`}
                        style={{ width: `${Math.round((value / outcomeTotal) * 100)}%` }}
                      />
                    </div>
                    <span className="analytics-bar-value">{value}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </Panel>
  );
}
