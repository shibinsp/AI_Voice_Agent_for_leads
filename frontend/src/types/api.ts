export type LeadStatus =
  | "new"
  | "call_queued"
  | "calling"
  | "contacted"
  | "qualified"
  | "not_qualified"
  | "callback_requested"
  | "failed";

export type CallAttemptStatus =
  | "queued"
  | "initiated"
  | "in_progress"
  | "completed"
  | "busy"
  | "no_answer"
  | "failed";

export type VoiceSessionStatus = "created" | "in_progress" | "completed" | "failed";

export type TranscriptSpeaker = "agent" | "lead" | "system";

export type QualificationOutcome =
  | "qualified"
  | "not_qualified"
  | "callback_requested"
  | "needs_review";

export type HandoffStatus = "pending" | "sent" | "failed" | "skipped";

export interface HealthResponse {
  status: string;
  app: string;
  environment: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  username: string;
}

export interface CurrentUser {
  username: string;
}

export interface AgentRead {
  id: number;
  name: string;
  script_key: string;
  vertical: string | null;
  language: string;
  voice_provider: string;
  telephony_provider: string;
  description: string | null;
  opening_line: string | null;
  qualification_goal: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AgentCreate {
  name: string;
  script_key: string;
  vertical: string | null;
  language: string;
  voice_provider: string;
  telephony_provider: string;
  description: string | null;
  opening_line: string | null;
  qualification_goal: string | null;
  is_active: boolean;
}

export interface AgentUpdate {
  name?: string;
  script_key?: string;
  vertical?: string | null;
  language?: string;
  voice_provider?: string;
  telephony_provider?: string;
  description?: string | null;
  opening_line?: string | null;
  qualification_goal?: string | null;
  is_active?: boolean;
}

export interface AgentListResponse {
  items: AgentRead[];
  total: number;
}

export interface LeadRead {
  id: number;
  client_id: number | null;
  campaign_id: number | null;
  external_lead_id: string;
  external_page_id: string | null;
  full_name: string | null;
  phone_number: string | null;
  email: string | null;
  preferred_language: string;
  city: string | null;
  raw_fields: Record<string, unknown>;
  status: LeadStatus;
  created_at: string;
  updated_at: string;
}

export interface LeadListResponse {
  items: LeadRead[];
  total: number;
}

export interface CallAttemptRead {
  id: number;
  lead_id: number;
  provider: string;
  script_key: string;
  phone_number: string;
  provider_call_id: string | null;
  status: CallAttemptStatus;
  failure_reason: string | null;
  provider_payload: Record<string, unknown>;
  requested_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface CallAttemptListResponse {
  items: CallAttemptRead[];
  total: number;
}

export interface TranscriptTurnRead {
  id: number;
  voice_session_id: number;
  speaker: TranscriptSpeaker;
  text: string;
  confidence: number | null;
  turn_metadata: Record<string, unknown>;
  created_at: string;
}

export interface QualificationResultRead {
  id: number;
  voice_session_id: number;
  lead_id: number;
  outcome: QualificationOutcome;
  score: number;
  summary: string;
  fields: Record<string, unknown>;
  created_at: string;
}

export interface VoiceSessionRead {
  id: number;
  call_attempt_id: number;
  lead_id: number;
  agent_id: number | null;
  status: VoiceSessionStatus;
  language: string;
  audio_stream_url: string | null;
  session_metadata: Record<string, unknown>;
  started_at: string | null;
  ended_at: string | null;
  created_at: string;
  transcript_turns: TranscriptTurnRead[];
  qualification_result: QualificationResultRead | null;
}

export interface VoiceSessionListResponse {
  items: VoiceSessionRead[];
  total: number;
}

export interface HandoffEventRead {
  id: number;
  qualification_result_id: number;
  lead_id: number;
  channel: string;
  destination: string;
  status: HandoffStatus;
  payload: Record<string, unknown>;
  response_payload: Record<string, unknown>;
  failure_reason: string | null;
  created_at: string;
  sent_at: string | null;
}

export interface HandoffListResponse {
  items: HandoffEventRead[];
  total: number;
}

export interface IntegrationReadiness {
  auth: boolean;
  meta: boolean;
  telephony: boolean;
  sarvam: boolean;
  llm: boolean;
  crm: boolean;
  handoff: boolean;
  missing: string[];
}

export interface RetryFailedResponse {
  created_attempt_ids: number[];
  skipped_lead_ids: number[];
}

export interface EnquiryCreate {
  full_name: string;
  phone_number: string;
  requirement: string;
  email?: string | null;
  city?: string | null;
  source: "linkedin" | "instagram" | "other";
  language?: string;
}

export interface EnquiryStartResponse {
  lead_id: number;
  session_id: number;
  token: string;
  language: string;
  opening_line: string;
}

export interface StreamReadyMessage {
  type: "ready";
  session_id: number;
  language: string;
}

export interface StreamTurnMessage {
  type: "turn";
  lead_text: string;
  lead_confidence: number | null;
  agent_text: string;
  // present only when speech is synthesized server-side (Sarvam); absent for browser TTS
  agent_audio_base64?: string;
  mime_type?: string;
}

export interface StreamCompletedMessage {
  type: "completed";
  session_id: number;
  qualification: {
    outcome: QualificationOutcome;
    score: number;
    summary: string;
  } | null;
}

export interface StreamErrorMessage {
  type: "error";
  detail: string;
}

export type VoiceStreamMessage =
  | StreamReadyMessage
  | StreamTurnMessage
  | StreamCompletedMessage
  | StreamErrorMessage;

export interface MetaWebhookResponse {
  received: number;
  created: number;
  duplicates: number;
  scheduled_call_attempt_ids: number[];
}

export interface MetaWebhookPayload {
  object: "page";
  entry: Array<{
    id: string;
    time: number;
    changes: Array<{
      field: "leadgen";
      value: {
        leadgen_id: string;
        form_id: string;
        campaign_id: string;
        page_id: string;
        created_time: number;
      };
    }>;
  }>;
}
