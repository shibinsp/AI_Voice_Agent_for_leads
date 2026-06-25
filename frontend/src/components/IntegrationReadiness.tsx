import { CheckCircle2, CircleAlert } from "lucide-react";

import type { IntegrationReadiness as IntegrationReadinessData } from "../types/api";
import { Panel } from "./Panel";

interface IntegrationReadinessProps {
  readiness?: IntegrationReadinessData;
  isLoading: boolean;
}

const CHECKS = ["auth", "meta", "telephony", "sarvam", "llm", "crm", "handoff"] as const;

export function IntegrationReadiness({ readiness, isLoading }: IntegrationReadinessProps) {
  return (
    <Panel
      id="integrations"
      title="Integration Readiness"
      eyebrow="Runtime"
      subtitle="Provider checks for the live calling path."
    >
      <div className="readiness-grid">
        {CHECKS.map((check) => {
          const ready = Boolean(readiness?.[check]);
          return (
            <div key={check} className={ready ? "readiness-item is-ready" : "readiness-item"}>
              {ready ? <CheckCircle2 size={16} /> : <CircleAlert size={16} />}
              <span>{formatCheckLabel(check)}</span>
            </div>
          );
        })}
      </div>
      <p className="panel-note">
        {isLoading
          ? "Checking provider configuration..."
          : readiness?.missing.length
            ? `Missing: ${readiness.missing.join(", ")}`
            : "All configured for the current environment."}
      </p>
    </Panel>
  );
}

function formatCheckLabel(value: string): string {
  if (value === "llm") {
    return "LLM";
  }
  return value.charAt(0).toUpperCase() + value.slice(1);
}
