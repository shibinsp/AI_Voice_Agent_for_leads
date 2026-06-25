import { Route } from "lucide-react";

import type { HandoffEventRead } from "../types/api";
import { EmptyState } from "./EmptyState";
import { Panel } from "./Panel";
import { StatusPill } from "./StatusPill";

interface HandoffPanelProps {
  handoffs: HandoffEventRead[];
  total: number;
  isLoading: boolean;
}

export function HandoffPanel({ handoffs, total, isLoading }: HandoffPanelProps) {
  return (
    <Panel
      id="handoffs"
      title="Genuine enquiries → client"
      eyebrow="Human Loop"
      subtitle={`${total} genuine enquiries routed to the client.`}
    >
      <div className="handoff-list">
        {isLoading ? (
          <div className="skeleton-stack" aria-label="Loading handoffs">
            <span />
            <span />
          </div>
        ) : handoffs.length === 0 ? (
          <EmptyState
            icon={Route}
            title="No handoffs yet"
            detail="Qualified sessions will create CRM or operator handoff records here."
          />
        ) : (
          handoffs.slice(0, 6).map((handoff) => (
            <article key={handoff.id} className="handoff-item">
              <div>
                <strong>Lead #{handoff.lead_id}</strong>
                <p>{handoff.destination}</p>
              </div>
              <StatusPill status={handoff.status} />
            </article>
          ))
        )}
      </div>
    </Panel>
  );
}
