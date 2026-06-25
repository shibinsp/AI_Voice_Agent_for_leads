import type { CallAttemptRead, LeadRead } from "../types/api";
import { Panel } from "./Panel";
import { StatusPill } from "./StatusPill";

interface ActivityStreamProps {
  leads: LeadRead[];
  attempts: CallAttemptRead[];
}

interface ActivityItem {
  id: string;
  title: string;
  detail: string;
  time: string;
  status: LeadRead["status"] | CallAttemptRead["status"];
}

export function ActivityStream({ leads, attempts }: ActivityStreamProps) {
  const items = buildActivityItems(leads, attempts);

  return (
    <Panel
      title="Recent Activity"
      eyebrow="Timeline"
      subtitle="Newest events across lead capture and outbound execution."
    >
      <div className="activity-list">
        {items.length === 0 ? (
          <p className="panel-note">Activity will appear after the first simulated or live lead arrives.</p>
        ) : (
          items.map((item) => (
            <article key={item.id} className="activity-item">
              <div className="activity-copy">
                <strong>{item.title}</strong>
                <p>{item.detail}</p>
                <time dateTime={item.time}>{formatTimestamp(item.time)}</time>
              </div>
              <StatusPill status={item.status} />
            </article>
          ))
        )}
      </div>
    </Panel>
  );
}

function buildActivityItems(leads: LeadRead[], attempts: CallAttemptRead[]): ActivityItem[] {
  const leadItems = leads.map((lead) => ({
    id: `lead-${lead.id}`,
    title: lead.full_name ?? "Unnamed lead",
    detail: `${lead.phone_number ?? "No phone"} • ${lead.city ?? "Unknown city"}`,
    time: lead.created_at,
    status: lead.status,
  }));

  const attemptItems = attempts.map((attempt) => ({
    id: `attempt-${attempt.id}`,
    title: `Attempt #${attempt.id}`,
    detail: `${attempt.provider} • ${attempt.phone_number}`,
    time: attempt.started_at ?? attempt.requested_at,
    status: attempt.status,
  }));

  return [...leadItems, ...attemptItems]
    .sort((left, right) => new Date(right.time).getTime() - new Date(left.time).getTime())
    .slice(0, 8);
}

function formatTimestamp(value: string): string {
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

