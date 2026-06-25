# Telugu-First AI Voice Agent

## 1. What the brief defines well

The source brief clearly defines the business case:

- A Telugu-first outbound voice agent should call Instagram lead-ad prospects within seconds.
- The first target market is Hyderabad and Telangana SMBs in fast-response verticals such as real estate, clinics, education, insurance, and automotive.
- The business goal is not generic AI calling. It is faster lead conversion through better Telugu conversation quality and tighter local-market fit.
- The recommended thin slice is correct: prove webhook -> call -> live voice loop -> CRM handoff before building anything broader.

The brief also gives a usable starter stack:

- Lead source: Meta Lead Ads webhooks + Graph API lead retrieval
- Telephony: Exotel or Plivo
- Voice orchestration: Pipecat or LiveKit Agents
- Telugu STT/TTS: Sarvam AI
- Backend: FastAPI + Redis-backed async workers
- Storage / CRM: Postgres plus Zoho or HubSpot integration

## 2. Gaps in the brief that must become product requirements

The document is a strong strategy brief, but it is not yet a build spec. The following are missing and should be defined before coding:

1. Exact conversation design
   - Greeting
   - Consent / disclosure language
   - Qualification questions by vertical
   - Retry / fallback responses
   - Transfer / callback / voicemail behavior

2. Compliance workflow
   - What consent language appears on the lead form
   - How opt-out is handled during the call
   - What numbers and DLT/telemarketing setup are required
   - Call recording disclosure and retention policy

3. Operational workflow
   - How humans see new qualified leads
   - Who gets notified and where
   - What happens when the AI cannot understand the user
   - What happens after no-answer, busy, or failed calls

4. Production quality requirements
   - Lead-to-dial SLA
   - Max acceptable voice-turn latency
   - Concurrency target
   - Monitoring, alerting, and replay tooling

5. Commercial packaging
   - Single-client service deployment vs multi-tenant SaaS
   - Per-client custom script support
   - Billing model per call, per client, or per qualified lead

## 3. Recommended product scope

Build this as a **service-first MVP for one vertical**, not as a generic SaaS from day one.

Recommended first vertical:

- Clinics, if you want simpler qualification and appointment outcomes
- Real estate, if you want larger upside but harder call flows

Recommended MVP capabilities:

1. Receive Meta lead webhook in real time
2. Fetch full lead details from Graph API
3. Persist lead and attempt state in Postgres
4. Trigger outbound call within seconds
5. Run one Telugu conversation script
6. Capture structured qualification result
7. Push outcome to CRM or operator dashboard
8. Notify a human for qualified leads
9. Store transcript, summary, call result, and recording metadata

Do not include in MVP:

- Multi-tenant billing
- Full self-serve client onboarding
- Complex workflow builders
- Advanced analytics for clients
- Multiple vertical playbooks at once
- Voice cloning or highly customized persona tooling

## 4. Recommended architecture

### 4.1 Core decision

For the first build, prefer:

- `FastAPI` for APIs and webhook handling
- `Redis` for queueing and job orchestration
- `Postgres` for durable state
- `Pipecat` for the real-time voice pipeline
- `Exotel` as the primary India telephony provider
- `Sarvam AI` for Telugu STT/TTS

Reasoning:

- Meta officially supports Lead Ads webhooks plus Graph API retrieval for real-time lead capture and test-lead validation.
- Pipecat's official telephony docs explicitly list `Plivo` and `Exotel` under supported WebSocket telephony providers, which makes it a good fit for an India-first prototype.
- Sarvam's official speech docs support Telugu STT over WebSocket, including `8kHz` input, which matters for phone audio, and also support code-mixed output modes.
- Exotel's official Voice v1 docs are simple for outbound automation and list a `200 calls/minute` API limit, which is enough for early pilots.

Use `LiveKit` later only if you specifically need:

- stronger managed observability
- agent deployment tooling
- richer room/session primitives

But do not make it the first dependency for Indian outbound telephony unless you have already validated the SIP path. LiveKit's native phone number product is US-focused, and its Build plan documentation shows only `5` concurrent agent sessions plus `10-20` second cold starts on that plan. That is acceptable for a lab setup, not for an instant-callback production promise.

### 4.2 Service layout

1. `api-gateway`
   - FastAPI app
   - Meta webhook verification endpoint
   - health checks
   - admin APIs

2. `lead-service`
   - fetch lead details from Meta Graph API
   - normalize phone numbers and campaign metadata
   - deduplicate repeated webhook events

3. `call-orchestrator`
   - enqueue call attempts
   - enforce retry policy
   - rate-limit per client and provider
   - choose script / campaign / provider

4. `voice-agent-service`
   - Pipecat pipeline
   - VAD
   - Sarvam STT
   - dialogue manager / LLM integration
   - Sarvam TTS
   - interruption and fallback handling

5. `crm-adapter`
   - write structured result to Postgres
   - sync to Zoho / HubSpot / Google Sheets for pilot customers
   - send handoff notification

6. `ops-dashboard`
   - lead queue
   - call status
   - transcript summary
   - qualified lead review
   - retry / handoff controls

7. `observability`
   - logs
   - metrics
   - tracing
   - call replay metadata
   - alerting

### 4.3 Data model

Minimum tables:

- `clients`
- `campaigns`
- `lead_forms`
- `leads`
- `call_attempts`
- `call_sessions`
- `transcripts`
- `qualification_results`
- `notifications`
- `consent_records`
- `provider_events`

Key lead fields:

- source lead ID
- campaign ID
- client ID
- name
- phone
- preferred language
- location
- consent timestamp
- current status
- qualification score
- assigned human owner

## 5. Conversation design requirements

Treat the conversation as product logic, not prompt text.

Every script should define:

1. Opening
   - identify business
   - confirm this is a callback for the submitted form
   - capture consent to continue

2. Qualification
   - collect 3-5 fields only
   - budget / intent / location / timeframe / interest area

3. Outcome
   - qualified
   - unqualified
   - no response
   - callback requested
   - human escalation required

4. Failure handling
   - low STT confidence
   - repeated interruptions
   - silence
   - user asks for human
   - user says wrong number / not interested / stop

5. Handoff
   - book callback window or transfer to human queue

Important implementation note:

- Sarvam STT supports `codemix` and `translit` modes. Use those deliberately during testing because Hyderabad leads will often mix Telugu and English.

## 6. Delivery plan

Convert the brief's 4-week thin slice into a more realistic **8-week MVP plan**.

### Phase 0: Product definition and compliance

Duration: 4-5 days

Deliverables:

- target vertical chosen
- final call script v1
- qualification schema
- retry policy
- compliance checklist
- CRM destination decided

Exit criteria:

- one approved script and one approved qualification outcome schema
- lead form consent copy reviewed
- pilot client workflow documented

### Phase 1: Lead capture foundation

Duration: Week 1

Deliverables:

- FastAPI service scaffold
- webhook verification endpoint
- Meta webhook receiver
- lead fetch worker
- Postgres schema
- Redis queue

Exit criteria:

- test leads from Meta create persisted lead records within seconds
- duplicate webhook events do not create duplicate leads

### Phase 2: Outbound telephony thin slice

Duration: Week 2

Deliverables:

- Exotel or Plivo integration
- outbound call trigger
- call attempt state machine
- static Telugu audio playback flow
- no-answer / busy / failed handling

Exit criteria:

- system can place outbound calls to real Indian mobile numbers
- call result and provider callback events are recorded correctly

### Phase 3: Real-time Telugu voice loop

Duration: Weeks 3-4

Deliverables:

- Pipecat voice pipeline
- Sarvam streaming STT
- LLM dialogue manager
- Sarvam TTS
- interruption handling
- call transcript capture

Exit criteria:

- live Telugu conversation works end to end on phone audio
- one script completes with acceptable turn-taking and transcript quality

### Phase 4: Qualification and human handoff

Duration: Week 5

Deliverables:

- structured extraction of qualification fields
- summary generation
- CRM sync
- Slack / WhatsApp / email notification
- operator review screen

Exit criteria:

- qualified leads are visible to a human within one minute of call completion
- transcript summary matches the structured qualification result

### Phase 5: Reliability and pilot readiness

Duration: Week 6

Deliverables:

- retry scheduler
- provider fallback hooks
- latency and error dashboards
- call recording metadata
- admin controls
- prompt/script tuning

Exit criteria:

- 20-30 internal test calls reviewed
- no major failures in no-answer, silence, interruption, and code-switch cases

### Phase 6: Pilot launch

Duration: Weeks 7-8

Deliverables:

- first live client configuration
- campaign onboarding checklist
- pilot success dashboard
- weekly ROI report format

Exit criteria:

- 1 live pilot client onboarded
- measurable lead-response improvement vs client's current process

## 7. Non-functional requirements

Define these before implementation:

1. Performance
   - lead webhook to dial attempt start: target `< 15s`
   - average AI turn latency: target `< 1.2s`, stretch goal `< 800ms`
   - CRM update after call end: target `< 60s`

2. Reliability
   - webhook ingestion is idempotent
   - every call state transition is persisted
   - provider callbacks can be replayed safely

3. Observability
   - per-call trace ID
   - provider event log
   - transcript confidence / STT error visibility
   - latency breakdown per stage

4. Security and privacy
   - encrypted secrets
   - scoped API keys
   - access control for transcripts and recordings
   - retention policy for personal data and recordings

5. Compliance
   - consent capture recorded
   - DND / opt-out handling
   - audit trail for commercial communications

## 8. Risks and mitigation

### Latency risk

Risk:

- conversational lag makes the bot feel synthetic

Mitigation:

- keep prompts short
- minimize model hops
- stream STT and TTS
- cache static responses
- test on real 8kHz mobile audio from day one

### Telugu quality risk

Risk:

- poor handling of Telugu-English switching causes broken conversations

Mitigation:

- maintain a phrase bank from real calls
- test Sarvam STT modes for `transcribe`, `codemix`, and `translit`
- keep qualification logic narrow in MVP

### Telephony quality risk

Risk:

- packet loss and weak carrier audio degrade STT accuracy

Mitigation:

- run all testing on real mobile networks
- add silence handling and confidence thresholds
- keep scripted confirmation steps for critical values

### Compliance risk

Risk:

- automated commercial calling in India without correct consent and setup creates legal and operator problems

Mitigation:

- finalize compliance checklist before pilot
- use registered sender setup and consent records
- involve telecom provider support early

### Product risk

Risk:

- building generic SaaS before validating one repeatable service motion

Mitigation:

- sell one vertical first
- keep client configuration manual
- productize only after 3-5 repeat deployments

## 9. Immediate build checklist

Do these next, in order:

1. Pick the first vertical
2. Write the exact Telugu call script
3. Define the qualification fields and final lead statuses
4. Choose the telephony provider: Exotel first, Plivo fallback
5. Confirm Meta Lead Ads test environment and tokens
6. Create the Postgres schema and event model
7. Build webhook -> lead fetch -> DB logging
8. Build outbound call with static Telugu audio
9. Add live STT/LLM/TTS
10. Add CRM and human handoff

## 10. Final recommendation

The application should be built as a **narrow vertical operating system for instant lead response**, not as a generic AI caller.

Best path:

- start with one client profile
- keep the architecture event-driven and provider-swappable
- optimize for speed, Telugu quality, and human handoff
- treat compliance and observability as core features, not polish

If executed well, the brief supports a credible MVP. The biggest blockers are not model choice or framework choice. They are:

- script quality
- telecom compliance
- real-call testing
- pilot sales execution

## 11. Current-source notes

These current official references were used to validate the plan:

- Meta Lead Ads and lead webhooks: https://developers.facebook.com/documentation/ads-commerce/marketing-api/guides/lead-ads and https://developers.facebook.com/docs/graph-api/webhooks/getting-started/webhooks-for-leadgen/
- Pipecat telephony overview: https://docs.pipecat.ai/pipecat/telephony/overview
- LiveKit telephony and deployment limits: https://docs.livekit.io/telephony/ and https://docs.livekit.io/deploy/admin/quotas-and-limits/
- Sarvam STT/TTS docs: https://docs.sarvam.ai/api-reference-docs/speech-to-text/transcribe/ws and https://docs.sarvam.ai/api-reference-docs/api-guides-tutorials/text-to-speech/rest-api
- Exotel voice docs: https://developer.exotel.com/docs/voice-v1/overview
- TRAI commercial communication guidance: https://trai.gov.in/tcccpr and https://trai.gov.in/advice-to-senders
