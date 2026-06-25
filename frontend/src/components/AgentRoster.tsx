import { Bot, Pause, Play } from "lucide-react";

import type { AgentRead } from "../types/api";
import { EmptyState } from "./EmptyState";
import { Panel } from "./Panel";

interface AgentRosterProps {
  agents: AgentRead[];
  total: number;
  isLoading: boolean;
  activeAgentId?: number;
  onToggle: (agent: AgentRead) => void;
}

export function AgentRoster({
  agents,
  total,
  isLoading,
  activeAgentId,
  onToggle,
}: AgentRosterProps) {
  const activeCount = agents.filter((agent) => agent.is_active).length;

  return (
    <Panel
      id="agents"
      title="Agents"
      eyebrow="Registry"
      subtitle={`${total} configured agents, ${activeCount} active in the current view.`}
    >
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Agent</th>
              <th>Providers</th>
              <th>Goal</th>
              <th>State</th>
              <th>Updated</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={6} className="table-empty">
                  <div className="skeleton-stack" aria-label="Loading agents">
                    <span />
                    <span />
                    <span />
                  </div>
                </td>
              </tr>
            ) : agents.length === 0 ? (
              <tr>
                <td colSpan={6} className="table-empty">
                  <EmptyState
                    icon={Bot}
                    title="No agents in this view"
                    detail="Create an agent from Agent Studio or clear the search filter."
                  />
                </td>
              </tr>
            ) : (
              agents.map((agent) => (
                <tr key={agent.id}>
                  <td>
                    <div className="primary-cell">
                      <strong>{agent.name}</strong>
                      <span>{agent.script_key}</span>
                    </div>
                  </td>
                  <td>
                    <div className="primary-cell">
                      <strong>{agent.voice_provider}</strong>
                      <span>{agent.telephony_provider}</span>
                    </div>
                  </td>
                  <td>
                    <p className="table-copy">
                      {agent.qualification_goal ?? agent.description ?? agent.vertical ?? "Default"}
                    </p>
                  </td>
                  <td>
                    <span className={agent.is_active ? "agent-state is-active" : "agent-state"}>
                      {agent.is_active ? "Active" : "Paused"}
                    </span>
                  </td>
                  <td>
                    <time dateTime={agent.updated_at}>{formatTimestamp(agent.updated_at)}</time>
                  </td>
                  <td>
                    <button
                      className={agent.is_active ? "action-button action-button--pause" : "action-button"}
                      type="button"
                      onClick={() => onToggle(agent)}
                      disabled={activeAgentId === agent.id}
                      aria-label={agent.is_active ? `Pause ${agent.name}` : `Activate ${agent.name}`}
                    >
                      {agent.is_active ? <Pause size={15} /> : <Play size={15} />}
                      {activeAgentId === agent.id
                        ? "Saving..."
                        : agent.is_active
                          ? "Pause"
                          : "Activate"}
                    </button>
                  </td>
                </tr>
              ))
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
