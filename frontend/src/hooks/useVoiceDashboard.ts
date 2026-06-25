import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createAgent,
  dispatchCallAttempt,
  fetchAgents,
  fetchAnalytics,
  fetchCallAttempts,
  fetchHandoffs,
  fetchHealth,
  fetchLeads,
  fetchReadiness,
  fetchVoiceSessions,
  retryFailedAttempts,
  runDemoVoiceSession,
  sendMetaWebhook,
  updateAgent,
} from "../lib/api";
import type { AgentCreate, AgentUpdate, MetaWebhookPayload } from "../types/api";

const HEALTH_QUERY_KEY = ["health"] as const;
const READINESS_QUERY_KEY = ["readiness"] as const;
const AGENTS_QUERY_KEY = ["agents"] as const;
const LEADS_QUERY_KEY = ["leads"] as const;
const ATTEMPTS_QUERY_KEY = ["call-attempts"] as const;
const VOICE_SESSIONS_QUERY_KEY = ["voice-sessions"] as const;
const HANDOFFS_QUERY_KEY = ["handoffs"] as const;
const ANALYTICS_QUERY_KEY = ["analytics"] as const;

export function useVoiceDashboard() {
  const queryClient = useQueryClient();

  const healthQuery = useQuery({
    queryKey: HEALTH_QUERY_KEY,
    queryFn: fetchHealth,
    retry: 1,
    refetchInterval: 15_000,
  });

  const readinessQuery = useQuery({
    queryKey: READINESS_QUERY_KEY,
    queryFn: fetchReadiness,
    retry: 1,
    refetchInterval: 15_000,
  });

  const agentsQuery = useQuery({
    queryKey: AGENTS_QUERY_KEY,
    queryFn: () => fetchAgents(100),
    retry: 1,
    refetchInterval: 10_000,
  });

  const leadsQuery = useQuery({
    queryKey: LEADS_QUERY_KEY,
    queryFn: () => fetchLeads(100),
    retry: 1,
    refetchInterval: 7_000,
  });

  const callAttemptsQuery = useQuery({
    queryKey: ATTEMPTS_QUERY_KEY,
    queryFn: () => fetchCallAttempts(100),
    retry: 1,
    refetchInterval: 7_000,
  });

  const voiceSessionsQuery = useQuery({
    queryKey: VOICE_SESSIONS_QUERY_KEY,
    queryFn: () => fetchVoiceSessions(100),
    retry: 1,
    refetchInterval: 7_000,
  });

  const handoffsQuery = useQuery({
    queryKey: HANDOFFS_QUERY_KEY,
    queryFn: () => fetchHandoffs(100),
    retry: 1,
    refetchInterval: 7_000,
  });

  const analyticsQuery = useQuery({
    queryKey: ANALYTICS_QUERY_KEY,
    queryFn: fetchAnalytics,
    retry: 1,
    refetchInterval: 10_000,
  });

  const dispatchMutation = useMutation({
    mutationFn: dispatchCallAttempt,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: LEADS_QUERY_KEY }),
        queryClient.invalidateQueries({ queryKey: ATTEMPTS_QUERY_KEY }),
      ]);
    },
  });

  const runDemoSessionMutation = useMutation({
    mutationFn: runDemoVoiceSession,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: LEADS_QUERY_KEY }),
        queryClient.invalidateQueries({ queryKey: ATTEMPTS_QUERY_KEY }),
        queryClient.invalidateQueries({ queryKey: VOICE_SESSIONS_QUERY_KEY }),
        queryClient.invalidateQueries({ queryKey: HANDOFFS_QUERY_KEY }),
      ]);
    },
  });

  const retryFailedMutation = useMutation({
    mutationFn: retryFailedAttempts,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: LEADS_QUERY_KEY }),
        queryClient.invalidateQueries({ queryKey: ATTEMPTS_QUERY_KEY }),
      ]);
    },
  });

  const createAgentMutation = useMutation({
    mutationFn: (payload: AgentCreate) => createAgent(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: AGENTS_QUERY_KEY });
    },
  });

  const updateAgentMutation = useMutation({
    mutationFn: ({ agentId, payload }: { agentId: number; payload: AgentUpdate }) =>
      updateAgent(agentId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: AGENTS_QUERY_KEY });
    },
  });

  const webhookMutation = useMutation({
    mutationFn: (payload: MetaWebhookPayload) => sendMetaWebhook(payload),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: LEADS_QUERY_KEY }),
        queryClient.invalidateQueries({ queryKey: ATTEMPTS_QUERY_KEY }),
        queryClient.invalidateQueries({ queryKey: VOICE_SESSIONS_QUERY_KEY }),
        queryClient.invalidateQueries({ queryKey: HANDOFFS_QUERY_KEY }),
      ]);
    },
  });

  async function refreshAll(): Promise<void> {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: HEALTH_QUERY_KEY }),
      queryClient.invalidateQueries({ queryKey: READINESS_QUERY_KEY }),
      queryClient.invalidateQueries({ queryKey: AGENTS_QUERY_KEY }),
      queryClient.invalidateQueries({ queryKey: LEADS_QUERY_KEY }),
      queryClient.invalidateQueries({ queryKey: ATTEMPTS_QUERY_KEY }),
      queryClient.invalidateQueries({ queryKey: VOICE_SESSIONS_QUERY_KEY }),
      queryClient.invalidateQueries({ queryKey: HANDOFFS_QUERY_KEY }),
      queryClient.invalidateQueries({ queryKey: ANALYTICS_QUERY_KEY }),
    ]);
  }

  return {
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
  };
}
