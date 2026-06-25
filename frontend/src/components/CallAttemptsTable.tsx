import { PhoneCall } from "lucide-react";

import type { CallAttemptRead } from "../types/api";
import { EmptyState } from "./EmptyState";
import { Panel } from "./Panel";
import { StatusPill } from "./StatusPill";

interface CallAttemptsTableProps {
  attempts: CallAttemptRead[];
  total: number;
  isLoading: boolean;
  activeAttemptId?: number;
  activeDemoAttemptId?: number;
  onDispatch: (attemptId: number) => void;
  onRunDemo: (attemptId: number) => void;
  onRunLive: (attemptId: number) => void;
  onRetryFailed: () => void;
  isRetryingFailed: boolean;
}

export function CallAttemptsTable({
  attempts,
  total,
  isLoading,
  activeAttemptId,
  activeDemoAttemptId,
  onDispatch,
  onRunDemo,
  onRunLive,
  onRetryFailed,
  isRetryingFailed,
}: CallAttemptsTableProps) {
  return (
    <Panel
      id="calls"
      title="Call Attempts"
      eyebrow="Outbound"
      subtitle={`${total} attempts tracked across providers and dispatch states.`}
      actions={
        <button
          className="ghost-button"
          type="button"
          onClick={onRetryFailed}
          disabled={isRetryingFailed}
        >
          {isRetryingFailed ? "Retrying..." : "Retry Failed"}
        </button>
      }
    >
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Attempt</th>
              <th>Provider</th>
              <th>Status</th>
              <th>Phone</th>
              <th>Requested</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={6} className="table-empty">
                  <div className="skeleton-stack" aria-label="Loading call attempts">
                    <span />
                    <span />
                    <span />
                  </div>
                </td>
              </tr>
            ) : attempts.length === 0 ? (
              <tr>
                <td colSpan={6} className="table-empty">
                  <EmptyState
                    icon={PhoneCall}
                    title="No calls queued"
                    detail="New leads create call attempts automatically when dispatch is enabled."
                  />
                </td>
              </tr>
            ) : (
              attempts.map((attempt) => {
                const canDispatch =
                  attempt.status === "queued" || attempt.status === "failed";

                return (
                  <tr key={attempt.id}>
                    <td>
                      <div className="primary-cell">
                        <strong>Attempt #{attempt.id}</strong>
                        <span>{attempt.script_key}</span>
                      </div>
                    </td>
                    <td>
                      <div className="primary-cell">
                        <strong>{attempt.provider}</strong>
                        <span>{attempt.provider_call_id ?? "No provider call ID"}</span>
                      </div>
                    </td>
                    <td>
                      <StatusPill status={attempt.status} />
                    </td>
                    <td>{attempt.phone_number}</td>
                    <td>
                      <time dateTime={attempt.requested_at}>
                        {formatTimestamp(attempt.requested_at)}
                      </time>
                    </td>
                    <td>
                      {attempt.status === "initiated" || attempt.status === "in_progress" ? (
                        <div className="action-group">
                          <button
                            className="action-button"
                            type="button"
                            onClick={() => onRunLive(attempt.id)}
                          >
                            Live call
                          </button>
                          <button
                            className="ghost-button"
                            type="button"
                            onClick={() => onRunDemo(attempt.id)}
                            disabled={activeDemoAttemptId === attempt.id}
                          >
                            {activeDemoAttemptId === attempt.id ? "Running..." : "Run Demo"}
                          </button>
                        </div>
                      ) : canDispatch ? (
                        <button
                          className="action-button"
                          type="button"
                          onClick={() => onDispatch(attempt.id)}
                          disabled={activeAttemptId === attempt.id}
                          title="Places the call via the configured telephony provider (real phone when Exotel is configured)"
                        >
                          {activeAttemptId === attempt.id ? "Calling..." : "Call now"}
                        </button>
                      ) : (
                        <span className="muted-inline">
                          {attempt.failure_reason ? "Reviewed" : "Auto-managed"}
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

function formatTimestamp(value: string): string {
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
