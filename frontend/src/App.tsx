import { startTransition, useDeferredValue, useEffect, useState } from "react";
import { Menu, Search, Sparkles } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

import { ActivityStream } from "./components/ActivityStream";
import { AgentRoster } from "./components/AgentRoster";
import { AgentStudio } from "./components/AgentStudio";
import { AnalyticsPanel } from "./components/AnalyticsPanel";
import { CallAttemptsTable } from "./components/CallAttemptsTable";
import { EnquiryLinkCard } from "./components/EnquiryLinkCard";
import { EnquiryPage } from "./components/EnquiryPage";
import { HealthCard } from "./components/HealthCard";
import { HandoffPanel } from "./components/HandoffPanel";
import { IntegrationReadiness } from "./components/IntegrationReadiness";
import { LeadTable } from "./components/LeadTable";
import { LiveVoiceDemo } from "./components/LiveVoiceDemo";
import { LoginPage } from "./components/LoginPage";
import { OperationsStrip } from "./components/OperationsStrip";
import { Panel } from "./components/Panel";
import { Sidebar } from "./components/Sidebar";
import { VoiceSessionsPanel } from "./components/VoiceSessionsPanel";
import { WebhookSimulator } from "./components/WebhookSimulator";
import {
  AUTH_EXPIRED_EVENT,
  clearStoredSession,
  fetchCurrentUser,
  getApiBaseUrl,
  getStoredSession,
  login as requestLogin,
  setStoredSession,
} from "./lib/api";
import { useVoiceDashboard } from "./hooks/useVoiceDashboard";
import type { AgentRead, CallAttemptRead, LeadRead } from "./types/api";

export function App() {
  // Public enquiry link — rendered before any auth, no login required.
  if (typeof window !== "undefined" && window.location.pathname.startsWith("/enquiry")) {
    return <EnquiryPage />;
  }

  return <OperatorApp />;
}

function OperatorApp() {
  const queryClient = useQueryClient();
  const [session, setSession] = useState(() => getStoredSession());
  const [isCheckingSession, setIsCheckingSession] = useState(true);
  const [sessionError, setSessionError] = useState<string | null>(null);

  useEffect(() => {
    if (!session.token) {
      setIsCheckingSession(false);
      return;
    }

    let isActive = true;
    setIsCheckingSession(true);

    fetchCurrentUser()
      .then((currentUser) => {
        if (!isActive) {
          return;
        }

        const nextSession = {
          token: session.token,
          username: currentUser.username,
        };
        setStoredSession(nextSession);
        setSession(nextSession);
        setSessionError(null);
      })
      .catch(() => {
        if (!isActive) {
          return;
        }

        clearStoredSession();
        setSession({ token: null, username: null });
        setSessionError("Session expired. Sign in again.");
        queryClient.clear();
      })
      .finally(() => {
        if (isActive) {
          setIsCheckingSession(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [queryClient, session.token]);

  useEffect(() => {
    function handleAuthExpired(): void {
      clearStoredSession();
      setSession({ token: null, username: null });
      setSessionError("Session expired. Sign in again.");
      queryClient.clear();
    }

    window.addEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired);
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired);
  }, [queryClient]);

  async function handleLogin(username: string, password: string): Promise<void> {
    const response = await requestLogin(username, password);
    const nextSession = {
      token: response.access_token,
      username: response.username,
    };
    setStoredSession(nextSession);
    setSession(nextSession);
    setSessionError(null);
    await queryClient.invalidateQueries();
  }

  function handleLogout(): void {
    clearStoredSession();
    setSession({ token: null, username: null });
    setSessionError(null);
    queryClient.clear();
  }

  if (!session.token) {
    return (
      <LoginPage
        onLogin={handleLogin}
        isCheckingSession={isCheckingSession}
        sessionError={sessionError}
      />
    );
  }

  return <DashboardApp username={session.username} onLogout={handleLogout} />;
}

interface DashboardAppProps {
  username: string | null;
  onLogout: () => void;
}

function DashboardApp({ username, onLogout }: DashboardAppProps) {
  const [searchText, setSearchText] = useState("");
  const deferredSearchText = useDeferredValue(searchText);
  const [liveAttemptId, setLiveAttemptId] = useState<number | null>(null);
  const [navOpen, setNavOpen] = useState(false);

  const {
    healthQuery,
    readinessQuery,
    agentsQuery,
    leadsQuery,
    callAttemptsQuery,
    voiceSessionsQuery,
    handoffsQuery,
    analyticsQuery,
    dispatchMutation,
    runDemoSessionMutation,
    retryFailedMutation,
    createAgentMutation,
    updateAgentMutation,
    webhookMutation,
    refreshAll,
  } = useVoiceDashboard();

  const agents = agentsQuery.data?.items ?? [];
  const leads = leadsQuery.data?.items ?? [];
  const attempts = callAttemptsQuery.data?.items ?? [];
  const voiceSessions = voiceSessionsQuery.data?.items ?? [];
  const handoffs = handoffsQuery.data?.items ?? [];

  const filteredAgents = filterAgents(agents, deferredSearchText);
  const filteredLeads = filterLeads(leads, deferredSearchText);
  const filteredAttempts = filterAttempts(attempts, deferredSearchText);

  const activeCalls = attempts.filter((attempt) =>
    ["queued", "initiated", "in_progress"].includes(attempt.status),
  ).length;
  const queuedCalls = attempts.filter((attempt) => attempt.status === "queued").length;
  const failedCalls = attempts.filter((attempt) =>
    ["busy", "no_answer", "failed"].includes(attempt.status),
  ).length;
  const activeAgents = agents.filter((agent) => agent.is_active).length;
  const readyIntegrations = readinessQuery.data
    ? [
        readinessQuery.data.auth,
        readinessQuery.data.meta,
        readinessQuery.data.telephony,
        readinessQuery.data.sarvam,
        readinessQuery.data.llm,
        readinessQuery.data.crm,
        readinessQuery.data.handoff,
      ].filter(Boolean).length
    : 0;
  const isSyncing =
    healthQuery.isFetching ||
    agentsQuery.isFetching ||
    leadsQuery.isFetching ||
    callAttemptsQuery.isFetching ||
    voiceSessionsQuery.isFetching ||
    handoffsQuery.isFetching;
  const filterLabel =
    deferredSearchText.trim().length === 0
      ? `${filteredLeads.length} recent records`
      : `${filteredLeads.length} matching "${deferredSearchText}"`;

  return (
    <div className="app-layout">
      <Sidebar
        username={username}
        open={navOpen}
        onClose={() => setNavOpen(false)}
        onLogout={onLogout}
      />

      <div className="app-main">
        <header className="app-topbar">
          <button
            className="ghost-button topbar-menu"
            type="button"
            onClick={() => setNavOpen(true)}
            aria-label="Open navigation"
          >
            <Menu size={18} />
          </button>
          <div className="app-topbar-title">
            <h1>Lead response operations</h1>
            {isSyncing ? <span className="sync-indicator">Syncing…</span> : null}
          </div>
          <label className="search-field" htmlFor="search-input">
            <Search size={16} />
            <input
              id="search-input"
              type="search"
              value={searchText}
              onChange={(event) =>
                startTransition(() => {
                  setSearchText(event.target.value);
                })
              }
              placeholder="Search enquiries, phone, scripts…"
            />
          </label>
          {healthQuery.data ? (
            <span className="env-badge">{healthQuery.data.environment}</span>
          ) : null}
          <button className="ghost-button" type="button" onClick={() => void refreshAll()}>
            <Sparkles size={15} />
            Refresh
          </button>
        </header>

        <main className="app-content">
          <div id="overview">
            <OperationsStrip
              activeCalls={activeCalls}
              queuedCalls={queuedCalls}
              failedCalls={failedCalls}
              readyIntegrations={readyIntegrations}
              totalIntegrations={7}
              activeAgents={activeAgents}
            />
          </div>

          <AnalyticsPanel data={analyticsQuery.data} isLoading={analyticsQuery.isLoading} />

          <section className="dashboard-grid">
        <section className="dashboard-main">
          <AgentRoster
            agents={filteredAgents}
            total={agentsQuery.data?.total ?? 0}
            isLoading={agentsQuery.isLoading}
            activeAgentId={updateAgentMutation.variables?.agentId}
            onToggle={(agent) =>
              updateAgentMutation.mutate({
                agentId: agent.id,
                payload: { is_active: !agent.is_active },
              })
            }
          />
          <LeadTable
            leads={filteredLeads}
            total={leadsQuery.data?.total ?? 0}
            isLoading={leadsQuery.isLoading}
            filterLabel={filterLabel}
          />
          <CallAttemptsTable
            attempts={filteredAttempts}
            total={callAttemptsQuery.data?.total ?? 0}
            isLoading={callAttemptsQuery.isLoading}
            activeAttemptId={dispatchMutation.variables}
            activeDemoAttemptId={runDemoSessionMutation.variables}
            onDispatch={(attemptId) => dispatchMutation.mutate(attemptId)}
            onRunDemo={(attemptId) => runDemoSessionMutation.mutate(attemptId)}
            onRunLive={(attemptId) => setLiveAttemptId(attemptId)}
            onRetryFailed={() => retryFailedMutation.mutate()}
            isRetryingFailed={retryFailedMutation.isPending}
          />
          <VoiceSessionsPanel
            sessions={voiceSessions}
            total={voiceSessionsQuery.data?.total ?? 0}
            isLoading={voiceSessionsQuery.isLoading}
          />
        </section>

        <aside className="dashboard-side">
          <EnquiryLinkCard />

          <HealthCard
            health={healthQuery.data}
            baseUrl={getApiBaseUrl()}
            isLoading={healthQuery.isLoading}
            isFetching={healthQuery.isFetching}
            error={healthQuery.error instanceof Error ? healthQuery.error.message : undefined}
          />

          <div id="integrations">
            <IntegrationReadiness
              readiness={readinessQuery.data}
              isLoading={readinessQuery.isLoading}
            />
          </div>

          <AgentStudio
            onCreate={(payload) => createAgentMutation.mutate(payload)}
            isCreating={createAgentMutation.isPending}
            error={
              createAgentMutation.error instanceof Error
                ? createAgentMutation.error.message
                : undefined
            }
          />

          <Panel
            title="Operator Notes"
            eyebrow="Guidance"
            subtitle="What this frontend is optimized to show right now."
          >
            <ul className="notes-list">
              <li>Simulate leads first, then confirm they move through queued and initiated states.</li>
              <li>Use the dispatch button only for queued or failed attempts that need a manual retry.</li>
              <li>The current simulator is ideal for local demo loops before real Meta and Exotel credentials land.</li>
            </ul>
          </Panel>

          <WebhookSimulator
            onSubmit={(payload) => webhookMutation.mutate(payload)}
            isSubmitting={webhookMutation.isPending}
            lastResult={webhookMutation.data}
            error={webhookMutation.error instanceof Error ? webhookMutation.error.message : undefined}
          />

          <HandoffPanel
            handoffs={handoffs}
            total={handoffsQuery.data?.total ?? 0}
            isLoading={handoffsQuery.isLoading}
          />

          <ActivityStream leads={leads} attempts={attempts} />
        </aside>
          </section>
        </main>
      </div>

      {liveAttemptId !== null ? (
        <LiveVoiceDemo
          attemptId={liveAttemptId}
          onClose={() => setLiveAttemptId(null)}
          onCompleted={() => void refreshAll()}
        />
      ) : null}
    </div>
  );
}

function filterAgents(agents: AgentRead[], searchValue: string): AgentRead[] {
  const query = searchValue.trim().toLowerCase();
  if (!query) {
    return agents;
  }

  return agents.filter((agent) =>
    [
      agent.name,
      agent.script_key,
      agent.vertical,
      agent.language,
      agent.voice_provider,
      agent.telephony_provider,
      agent.is_active ? "active" : "paused",
    ]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(query)),
  );
}

function filterLeads(leads: LeadRead[], searchValue: string): LeadRead[] {
  const query = searchValue.trim().toLowerCase();
  if (!query) {
    return leads;
  }

  return leads.filter((lead) =>
    [
      lead.full_name,
      lead.phone_number,
      lead.email,
      lead.city,
      lead.external_lead_id,
      lead.status,
    ]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(query)),
  );
}

function filterAttempts(
  attempts: CallAttemptRead[],
  searchValue: string,
): CallAttemptRead[] {
  const query = searchValue.trim().toLowerCase();
  if (!query) {
    return attempts;
  }

  return attempts.filter((attempt) =>
    [
      attempt.phone_number,
      attempt.provider,
      attempt.provider_call_id,
      attempt.script_key,
      attempt.status,
      String(attempt.id),
    ]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(query)),
  );
}
