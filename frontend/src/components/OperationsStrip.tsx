import { Gauge, PhoneCall, ShieldCheck, TimerReset } from "lucide-react";

interface OperationsStripProps {
  activeCalls: number;
  queuedCalls: number;
  failedCalls: number;
  readyIntegrations: number;
  totalIntegrations: number;
  activeAgents: number;
}

export function OperationsStrip({
  activeCalls,
  queuedCalls,
  failedCalls,
  readyIntegrations,
  totalIntegrations,
  activeAgents,
}: OperationsStripProps) {
  const nextAction =
    activeAgents === 0
      ? "Create or activate an agent"
      : queuedCalls > 0
        ? "Dispatch queued calls"
        : failedCalls > 0
          ? "Review failed attempts"
          : "Monitor live capture";

  return (
    <section className="ops-strip" aria-label="Operations summary">
      <article className="ops-card ops-card--primary">
        <Gauge size={20} />
        <div>
          <span>Next action</span>
          <strong>{nextAction}</strong>
        </div>
      </article>
      <article className="ops-card">
        <PhoneCall size={20} />
        <div>
          <span>Call pipeline</span>
          <strong>
            {activeCalls} active / {queuedCalls} queued
          </strong>
        </div>
      </article>
      <article className="ops-card">
        <ShieldCheck size={20} />
        <div>
          <span>Runtime readiness</span>
          <strong>
            {readyIntegrations}/{totalIntegrations} checks ready
          </strong>
        </div>
      </article>
      <article className="ops-card">
        <TimerReset size={20} />
        <div>
          <span>Exception queue</span>
          <strong>{failedCalls} need review</strong>
        </div>
      </article>
    </section>
  );
}
