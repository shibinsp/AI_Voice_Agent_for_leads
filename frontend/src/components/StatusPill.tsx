import type {
  CallAttemptStatus,
  HandoffStatus,
  LeadStatus,
  QualificationOutcome,
  VoiceSessionStatus,
} from "../types/api";

type StatusValue =
  | LeadStatus
  | CallAttemptStatus
  | VoiceSessionStatus
  | QualificationOutcome
  | HandoffStatus
  | "live"
  | "down";

interface StatusPillProps {
  status: StatusValue;
}

const LABELS: Record<StatusValue, string> = {
  new: "New",
  call_queued: "Call Queued",
  calling: "Calling",
  contacted: "Contacted",
  qualified: "Qualified",
  not_qualified: "Not Qualified",
  callback_requested: "Callback",
  failed: "Failed",
  created: "Created",
  pending: "Pending",
  sent: "Sent",
  skipped: "Skipped",
  needs_review: "Needs Review",
  queued: "Queued",
  initiated: "Initiated",
  in_progress: "In Progress",
  completed: "Completed",
  busy: "Busy",
  no_answer: "No Answer",
  live: "Live",
  down: "Down",
};

export function StatusPill({ status }: StatusPillProps) {
  return (
    <span className={`status-pill status-pill--${status.replace(/_/g, "-")}`}>
      {LABELS[status]}
    </span>
  );
}
