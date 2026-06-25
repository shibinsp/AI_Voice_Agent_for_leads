import { startTransition, useState } from "react";
import { FlaskConical, RefreshCcw, SendHorizontal } from "lucide-react";

import type { MetaWebhookPayload, MetaWebhookResponse } from "../types/api";
import { Panel } from "./Panel";

interface WebhookSimulatorProps {
  onSubmit: (payload: MetaWebhookPayload) => void;
  isSubmitting: boolean;
  lastResult?: MetaWebhookResponse;
  error?: string;
}

export function WebhookSimulator({
  onSubmit,
  isSubmitting,
  lastResult,
  error,
}: WebhookSimulatorProps) {
  const [payloadText, setPayloadText] = useState(() =>
    JSON.stringify(createDemoPayload(), null, 2),
  );
  const [parseError, setParseError] = useState<string | null>(null);

  function handleGenerate(): void {
    startTransition(() => {
      setPayloadText(JSON.stringify(createDemoPayload(), null, 2));
      setParseError(null);
    });
  }

  function handleSubmit(): void {
    try {
      const parsed = JSON.parse(payloadText) as MetaWebhookPayload;
      setParseError(null);
      onSubmit(parsed);
    } catch {
      setParseError("Payload is not valid JSON.");
    }
  }

  return (
    <Panel
      id="webhooks"
      title="Webhook Simulator"
      eyebrow="Lab"
      subtitle="Generate a fresh Meta lead event and inject it into the backend."
      actions={
        <button className="ghost-button" type="button" onClick={handleGenerate}>
          <RefreshCcw size={16} />
          Fresh Payload
        </button>
      }
    >
      <div className="simulator-note">
        <FlaskConical size={16} />
        <span>
          In development, the backend can mint mock lead details when no live Meta token is configured.
        </span>
      </div>

      <label className="simulator-label" htmlFor="payload-editor">
        Event JSON
      </label>
      <textarea
        id="payload-editor"
        className="payload-editor"
        value={payloadText}
        onChange={(event) => setPayloadText(event.target.value)}
        rows={14}
        spellCheck={false}
      />

      <div className="button-row">
        <button
          className="primary-button"
          type="button"
          onClick={handleSubmit}
          disabled={isSubmitting}
        >
          <SendHorizontal size={16} />
          {isSubmitting ? "Sending..." : "Send Webhook"}
        </button>
      </div>

      {parseError ? <p className="inline-error">{parseError}</p> : null}
      {error ? <p className="inline-error">{error}</p> : null}
      {lastResult ? (
        <div className="result-strip">
          <span>Received: {lastResult.received}</span>
          <span>Created: {lastResult.created}</span>
          <span>Duplicates: {lastResult.duplicates}</span>
          <span>Attempts: {lastResult.scheduled_call_attempt_ids.join(", ") || "None"}</span>
        </div>
      ) : null}
    </Panel>
  );
}

function createDemoPayload(): MetaWebhookPayload {
  const timestamp = Date.now();
  const suffix = String(timestamp).slice(-6);

  return {
    object: "page",
    entry: [
      {
        id: "page-demo-01",
        time: Math.floor(timestamp / 1000),
        changes: [
          {
            field: "leadgen",
            value: {
              leadgen_id: `lead-${suffix}`,
              form_id: "clinic-form-01",
              campaign_id: "hyderabad-clinic-callback",
              page_id: "page-demo-01",
              created_time: Math.floor(timestamp / 1000),
            },
          },
        ],
      },
    ],
  };
}
