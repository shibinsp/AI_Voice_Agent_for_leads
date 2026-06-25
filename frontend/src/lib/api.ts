import type {
  AgentCreate,
  AgentListResponse,
  AgentRead,
  AgentUpdate,
  CallAttemptListResponse,
  CallAttemptRead,
  CurrentUser,
  EnquiryCreate,
  EnquiryStartResponse,
  HealthResponse,
  HandoffListResponse,
  IntegrationReadiness,
  LeadListResponse,
  LoginResponse,
  MetaWebhookPayload,
  MetaWebhookResponse,
  RetryFailedResponse,
  VoiceSessionListResponse,
  VoiceSessionRead,
} from "../types/api";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";
const SESSION_STORAGE_KEY = "ai_voice_session";

export const AUTH_EXPIRED_EVENT = "ai-voice-auth-expired";

export interface StoredSession {
  token: string | null;
  username: string | null;
}

export function getApiBaseUrl(): string {
  return API_BASE_URL;
}

export function getStoredSession(): StoredSession {
  if (typeof window === "undefined") {
    return { token: null, username: null };
  }

  const rawSession = window.localStorage.getItem(SESSION_STORAGE_KEY);
  if (!rawSession) {
    return { token: null, username: null };
  }

  try {
    const parsed = JSON.parse(rawSession) as Partial<StoredSession>;
    return {
      token: typeof parsed.token === "string" ? parsed.token : null,
      username: typeof parsed.username === "string" ? parsed.username : null,
    };
  } catch {
    window.localStorage.removeItem(SESSION_STORAGE_KEY);
    return { token: null, username: null };
  }
}

export function setStoredSession(session: StoredSession): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
}

export function clearStoredSession(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(SESSION_STORAGE_KEY);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const { token } = getStoredSession();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    const detail = await response.text();
    const message = parseErrorMessage(detail, response.status);
    if (response.status === 401 && path !== "/auth/login" && typeof window !== "undefined") {
      window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

function parseErrorMessage(detail: string, statusCode: number): string {
  if (!detail) {
    return `Request failed with ${statusCode}`;
  }

  try {
    const parsed = JSON.parse(detail) as { detail?: unknown };
    if (typeof parsed.detail === "string") {
      return parsed.detail;
    }
  } catch {
    return detail;
  }

  return detail;
}

export function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export function login(username: string, password: string): Promise<LoginResponse> {
  return request<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function fetchCurrentUser(): Promise<CurrentUser> {
  return request<CurrentUser>("/auth/me");
}

export function fetchReadiness(): Promise<IntegrationReadiness> {
  return request<IntegrationReadiness>("/integrations/readiness");
}

export function fetchAgents(limit = 100): Promise<AgentListResponse> {
  return request<AgentListResponse>(`/agents?limit=${limit}`);
}

export function createAgent(payload: AgentCreate): Promise<AgentRead> {
  return request<AgentRead>("/agents", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateAgent(
  agentId: number,
  payload: AgentUpdate,
): Promise<AgentRead> {
  return request<AgentRead>(`/agents/${agentId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function fetchLeads(limit = 100): Promise<LeadListResponse> {
  return request<LeadListResponse>(`/leads?limit=${limit}`);
}

export function fetchCallAttempts(limit = 100): Promise<CallAttemptListResponse> {
  return request<CallAttemptListResponse>(`/call-attempts?limit=${limit}`);
}

export function dispatchCallAttempt(attemptId: number): Promise<CallAttemptRead> {
  return request<CallAttemptRead>(`/call-attempts/${attemptId}/dispatch`, {
    method: "POST",
  });
}

export function retryFailedAttempts(): Promise<RetryFailedResponse> {
  return request<RetryFailedResponse>("/call-attempts/retry-failed", {
    method: "POST",
  });
}

export function fetchVoiceSessions(limit = 100): Promise<VoiceSessionListResponse> {
  return request<VoiceSessionListResponse>(`/voice-sessions?limit=${limit}`);
}

export function runDemoVoiceSession(attemptId: number): Promise<VoiceSessionRead> {
  return request<VoiceSessionRead>(`/voice-sessions/from-call-attempt/${attemptId}/demo`, {
    method: "POST",
  });
}

export function createVoiceSession(attemptId: number): Promise<VoiceSessionRead> {
  return request<VoiceSessionRead>(`/voice-sessions/from-call-attempt/${attemptId}`, {
    method: "POST",
  });
}

/** WebSocket URL for the live STT->LLM->TTS loop, carrying the bearer token as a query param. */
export function getVoiceStreamUrl(sessionId: number): string {
  const { token } = getStoredSession();
  return getVoiceStreamUrlWithToken(sessionId, token);
}

/** WebSocket URL with an explicit token (used by the public enquiry call). */
export function getVoiceStreamUrlWithToken(sessionId: number, token: string | null): string {
  const wsBase = API_BASE_URL.replace(/^http/, "ws");
  const query = token ? `?token=${encodeURIComponent(token)}` : "";
  return `${wsBase}/voice-sessions/${sessionId}/stream${query}`;
}

/** Public enquiry-link submission. No auth; returns a session-scoped token for the web call. */
export function submitEnquiry(payload: EnquiryCreate): Promise<EnquiryStartResponse> {
  return request<EnquiryStartResponse>("/enquiries", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchHandoffs(limit = 100): Promise<HandoffListResponse> {
  return request<HandoffListResponse>(`/handoffs?limit=${limit}`);
}

export function sendMetaWebhook(
  payload: MetaWebhookPayload,
): Promise<MetaWebhookResponse> {
  return request<MetaWebhookResponse>("/webhooks/meta/leadgen", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
