import { useCallback, useMemo, useState } from "react";
import { Mic, PhoneOff, Send } from "lucide-react";

import { submitEnquiry } from "../lib/api";
import { useVoiceCall } from "../hooks/useVoiceCall";
import type { VoiceCallConnection, VoiceCallPhase } from "../hooks/useVoiceCall";
import type { EnquiryStartResponse } from "../types/api";

const PHASE_LABELS: Record<VoiceCallPhase, string> = {
  connecting: "Connecting",
  ready: "Ready",
  recording: "Listening",
  thinking: "One moment…",
  completed: "Completed",
  error: "Error",
};

function readSource(): "linkedin" | "instagram" | "other" {
  const src = new URLSearchParams(window.location.search).get("src");
  return src === "linkedin" || src === "instagram" ? src : "other";
}

export function EnquiryPage() {
  const [started, setStarted] = useState<EnquiryStartResponse | null>(null);

  return (
    <div className="enquiry-shell">
      <div className="background-blur background-blur--one" />
      <div className="background-blur background-blur--two" />
      <div className="enquiry-card">
        {started ? (
          <EnquiryCall start={started} />
        ) : (
          <EnquiryForm onStarted={setStarted} />
        )}
      </div>
      <p className="enquiry-footnote">Powered by a Telugu-first AI assistant</p>
    </div>
  );
}

interface EnquiryFormProps {
  onStarted: (response: EnquiryStartResponse) => void;
}

function EnquiryForm({ onStarted }: EnquiryFormProps) {
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [requirement, setRequirement] = useState("");
  const [city, setCity] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const source = useMemo(readSource, []);

  async function handleSubmit(event: React.FormEvent): Promise<void> {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const response = await submitEnquiry({
        full_name: fullName.trim(),
        phone_number: phone.trim(),
        requirement: requirement.trim(),
        city: city.trim() || null,
        source,
      });
      onStarted(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
      setSubmitting(false);
    }
  }

  return (
    <form className="enquiry-form" onSubmit={handleSubmit}>
      <span className="topbar-label">Quick enquiry</span>
      <h1>Tell us what you’re looking for</h1>
      <p className="enquiry-intro">
        Share a few details and our assistant will call you right here to understand your
        requirement.
      </p>

      <label className="enquiry-field">
        <span>Your name</span>
        <input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
      </label>
      <label className="enquiry-field">
        <span>Phone number</span>
        <input
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          inputMode="tel"
          placeholder="98765 43210"
          required
        />
      </label>
      <label className="enquiry-field">
        <span>What are you looking for?</span>
        <textarea
          value={requirement}
          onChange={(e) => setRequirement(e.target.value)}
          rows={3}
          placeholder="e.g. 2BHK flat near Gachibowli, budget around 80 lakhs"
          required
        />
      </label>
      <label className="enquiry-field">
        <span>City (optional)</span>
        <input value={city} onChange={(e) => setCity(e.target.value)} placeholder="Hyderabad" />
      </label>

      {error ? <p className="live-demo-error">{error}</p> : null}

      <button className="action-button enquiry-submit" type="submit" disabled={submitting}>
        <Send size={16} />
        {submitting ? "Starting your call…" : "Start enquiry call"}
      </button>
    </form>
  );
}

interface EnquiryCallProps {
  start: EnquiryStartResponse;
}

function EnquiryCall({ start }: EnquiryCallProps) {
  const connect = useCallback(
    async (): Promise<VoiceCallConnection> => ({
      sessionId: start.session_id,
      token: start.token,
      language: start.language,
      openingTurns: start.opening_line ? [start.opening_line] : [],
    }),
    [start],
  );

  const { phase, turns, error, speechSupported, startListening, stopListening, endCall } =
    useVoiceCall(connect);

  if (phase === "completed") {
    return (
      <div className="enquiry-done">
        <h1>Thank you! 🙏</h1>
        <p>We’ve noted your requirement. Our team will reach out to you shortly.</p>
      </div>
    );
  }

  return (
    <div className="enquiry-call">
      <span className="topbar-label">Talking to our assistant</span>
      <div className="live-demo-status">
        <span className={`status-pill status-pill--${phase}`}>{PHASE_LABELS[phase]}</span>
        {error ? <span className="live-demo-error">{error}</span> : null}
      </div>

      {!speechSupported ? (
        <p className="live-demo-error">
          Your browser can’t capture speech. Please open this link in Google Chrome.
        </p>
      ) : null}

      <div className="live-demo-transcript">
        {turns.length === 0 ? (
          <p className="muted-inline">Connecting you to our assistant…</p>
        ) : (
          turns.map((turn, idx) => (
            <div key={idx} className={`live-turn live-turn--${turn.speaker}`}>
              <strong>{turn.speaker === "agent" ? "Assistant" : "You"}</strong>
              <span>{turn.text}</span>
            </div>
          ))
        )}
      </div>

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
            Hold a conversation — tap to speak
          </button>
        )}
        <button className="ghost-button" type="button" onClick={endCall} disabled={phase === "connecting"}>
          <PhoneOff size={16} />
          Finish
        </button>
      </div>
    </div>
  );
}
