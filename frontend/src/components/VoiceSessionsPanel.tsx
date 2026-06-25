import { MessagesSquare } from "lucide-react";

import type { VoiceSessionRead } from "../types/api";
import { EmptyState } from "./EmptyState";
import { Panel } from "./Panel";
import { StatusPill } from "./StatusPill";

interface VoiceSessionsPanelProps {
  sessions: VoiceSessionRead[];
  total: number;
  isLoading: boolean;
}

export function VoiceSessionsPanel({
  sessions,
  total,
  isLoading,
}: VoiceSessionsPanelProps) {
  return (
    <Panel
      id="sessions"
      title="Voice Sessions"
      eyebrow="Conversation"
      subtitle={`${total} sessions with transcripts and qualification output.`}
    >
      <div className="session-list">
        {isLoading ? (
          <div className="skeleton-stack" aria-label="Loading voice sessions">
            <span />
            <span />
            <span />
          </div>
        ) : sessions.length === 0 ? (
          <EmptyState
            icon={MessagesSquare}
            title="No voice sessions yet"
            detail="Run a demo from an initiated call attempt to create transcripts and qualification results."
          />
        ) : (
          sessions.slice(0, 4).map((session) => (
            <article key={session.id} className="session-item">
              <div className="session-header">
                <div>
                  <strong>Session #{session.id}</strong>
                  <span>Attempt #{session.call_attempt_id}</span>
                </div>
                <StatusPill status={session.status} />
              </div>

              <div className="transcript-preview">
                {session.transcript_turns.slice(-3).map((turn) => (
                  <p key={turn.id}>
                    <span>{turn.speaker}</span>
                    {turn.text}
                  </p>
                ))}
              </div>

              {session.qualification_result ? (
                <div className="qualification-strip">
                  <StatusPill status={session.qualification_result.outcome} />
                  <strong>{session.qualification_result.score}</strong>
                  <span>{session.qualification_result.summary}</span>
                </div>
              ) : null}
            </article>
          ))
        )}
      </div>
    </Panel>
  );
}
