import { useCallback } from "react";
import { Mic, PhoneOff, X } from "lucide-react";

import { createVoiceSession, getStoredSession } from "../lib/api";
import { useVoiceCall } from "../hooks/useVoiceCall";
import type { VoiceCallConnection, VoiceCallPhase } from "../hooks/useVoiceCall";
import { StatusPill } from "./StatusPill";

interface LiveVoiceDemoProps {
  attemptId: number;
  onClose: () => void;
  onCompleted: () => void;
}

const PHASE_LABELS: Record<VoiceCallPhase, string> = {
  connecting: "Connecting",
  ready: "Ready",
  recording: "Listening",
  thinking: "Processing",
  completed: "Completed",
  error: "Error",
};

export function LiveVoiceDemo({ attemptId, onClose, onCompleted }: LiveVoiceDemoProps) {
  const connect = useCallback(async (): Promise<VoiceCallConnection> => {
    const session = await createVoiceSession(attemptId);
    return {
      sessionId: session.id,
      token: getStoredSession().token ?? "",
      language: session.language || "te-IN",
      openingTurns: session.transcript_turns
        .filter((t) => t.speaker === "agent")
        .map((t) => t.text),
    };
  }, [attemptId]);

  const {
    phase,
    turns,
    qualification,
    error,
    speechSupported,
    startListening,
    stopListening,
    endCall,
  } = useVoiceCall(connect, onCompleted);

  return (
    <div className="live-demo-overlay" role="dialog" aria-modal="true">
      <div className="live-demo-card">
        <header className="live-demo-header">
          <div>
            <span className="topbar-label">Live Telugu call</span>
            <h2>Attempt #{attemptId}</h2>
          </div>
          <button className="ghost-button" type="button" onClick={onClose} aria-label="Close">
            <X size={16} />
          </button>
        </header>

        <div className="live-demo-status">
          <span className={`status-pill status-pill--${phase}`}>{PHASE_LABELS[phase]}</span>
          {error ? <span className="live-demo-error">{error}</span> : null}
        </div>

        {!speechSupported ? (
          <p className="live-demo-error">
            This browser has no speech recognition. Open the dashboard in Chrome to use the live
            voice loop.
          </p>
        ) : null}

        <div className="live-demo-transcript">
          {turns.length === 0 ? (
            <p className="muted-inline">Connecting… press “Speak” and talk in Telugu.</p>
          ) : (
            turns.map((turn, idx) => (
              <div key={idx} className={`live-turn live-turn--${turn.speaker}`}>
                <strong>{turn.speaker === "agent" ? "Agent" : "Lead"}</strong>
                <span>{turn.text}</span>
              </div>
            ))
          )}
        </div>

        {qualification ? (
          <div className="live-demo-result">
            <StatusPill status={qualification.outcome} />
            <strong>Score {qualification.score}</strong>
            <p>{qualification.summary}</p>
          </div>
        ) : null}

        {phase !== "completed" ? (
          <div className="live-demo-controls">
            {phase === "recording" ? (
              <button className="action-button" type="button" onClick={stopListening}>
                <Mic size={16} />
                Listening… tap to stop
              </button>
            ) : (
              <button
                className="action-button"
                type="button"
                onClick={startListening}
                disabled={phase !== "ready" || !speechSupported}
              >
                <Mic size={16} />
                Speak
              </button>
            )}
            <button
              className="ghost-button"
              type="button"
              onClick={endCall}
              disabled={phase === "connecting"}
            >
              <PhoneOff size={16} />
              End call
            </button>
          </div>
        ) : (
          <div className="live-demo-controls">
            <button className="action-button" type="button" onClick={onClose}>
              Done
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
