import { Activity, PhoneCall, Radar, RefreshCw } from "lucide-react";

import { MetricCard } from "./MetricCard";
import { StatusPill } from "./StatusPill";

interface HeroPanelProps {
  id?: string;
  totalLeads: number;
  activeCalls: number;
  connectedCalls: number;
  failureRate: string;
  backendUrl: string;
  isSyncing: boolean;
  isHealthy: boolean;
}

export function HeroPanel({
  id,
  totalLeads,
  activeCalls,
  connectedCalls,
  failureRate,
  backendUrl,
  isSyncing,
  isHealthy,
}: HeroPanelProps) {
  return (
    <section id={id} className="hero-panel">
      <div className="hero-copy">
        <span className="hero-kicker">Telugu-First Voice Ops</span>
        <h1>Convert high-intent leads before attention drops.</h1>
        <p>
          A focused command center for agent readiness, Meta lead ingestion, outbound callbacks,
          qualification sessions, and human handoffs.
        </p>
        <div className="hero-meta">
          <div className="hero-chip">
            <Radar size={16} />
            <span>API</span>
            <code>{backendUrl}</code>
          </div>
          <div className="hero-chip">
            {isSyncing ? <RefreshCw size={16} className="spin" /> : <Activity size={16} />}
            <span>{isSyncing ? "Syncing now" : "Live polling enabled"}</span>
          </div>
          <StatusPill status={isHealthy ? "live" : "down"} />
        </div>
      </div>

      <div className="hero-metrics">
        <MetricCard
          label="Total Leads"
          value={String(totalLeads)}
          helper="Captured from webhook events in the current dashboard window."
          tone="ink"
        />
        <MetricCard
          label="Active Calls"
          value={String(activeCalls)}
          helper="Attempts that are queued, initiated, or currently in progress."
          tone="teal"
        />
        <MetricCard
          label="Connected Calls"
          value={String(connectedCalls)}
          helper="Attempts that completed far enough to be marked contacted."
          tone="lime"
        />
        <MetricCard
          label="Failure Rate"
          value={failureRate}
          helper="Busy, no-answer, and failed attempts as a share of all attempts."
          tone="coral"
        />
      </div>

      <div className="hero-rail">
        <div className="hero-rail-item">
          <PhoneCall size={18} />
          <div>
            <strong>Thin slice status</strong>
            <p>Webhook ingestion, storage, dispatch, qualification, and handoff are visible end to end.</p>
          </div>
        </div>
        <div className="hero-rail-item">
          <Activity size={18} />
          <div>
            <strong>Best next move</strong>
            <p>Keep one active agent ready, inject a lead, and validate the queue through handoff.</p>
          </div>
        </div>
      </div>
    </section>
  );
}
