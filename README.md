# Telugu-First AI Voice Agent

This workspace now contains the first backend scaffold for the MVP described in the brief:

- Meta Lead Ads webhook ingestion
- lead persistence and deduplication
- queued call-attempt creation
- telephony provider abstraction
- mock dispatch flow for local development
- Exotel callback handling scaffold

## Project layout

```text
AI_voice/
  backend/
    app/
      api/
      core/
      db/
      models/
      providers/
      schemas/
      services/
    tests/
  AI_Voice_Agent_Brief.docx
  APPLICATION_DEVELOPMENT_PLAN.md
```

## Quick start

```bash
cd /Users/apple/Alphha/AI_voice/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open:

- API docs: `http://127.0.0.1:8000/docs`
- health: `http://127.0.0.1:8000/api/v1/health`

## Frontend quick start

```bash
cd /Users/apple/Alphha/AI_voice/frontend
npm install
cp .env.example .env
npm run dev
```

Open:

- frontend: `http://127.0.0.1:5173`

The frontend expects the backend at `http://127.0.0.1:8000/api/v1` by default.
The backend now includes CORS defaults for local Vite development and can synthesize mock Meta lead details in non-production environments when no `META_ACCESS_TOKEN` is set.

Local operator login defaults:

- username: `admin`
- password: `admin123`

## Current implementation status

Implemented:

1. FastAPI application and configuration
2. SQLite-backed SQLAlchemy models for clients, campaigns, leads, and call attempts
3. Meta webhook verification and ingestion route
4. lead dedupe by external `leadgen_id`
5. background call dispatch through a telephony provider abstraction
6. mock telephony provider for local development
7. Exotel outbound-call adapter scaffold
8. Exotel status callback ingestion scaffold
9. tests for health, webhook verification, ingestion, and idempotency
10. React dashboard for live leads, call attempts, backend health, and webhook simulation
11. Voice-agent registry with create, list, activate, and pause flows
12. voice sessions with transcript turns and qualification results
13. mock-safe Telugu conversation demo flow
14. handoff events with mock or webhook delivery
15. CRM sync adapter with mock or webhook mode
16. provider adapters for Sarvam speech and OpenAI-compatible dialogue endpoints
17. failed-call retry creation
18. integration readiness checks
19. login-first React landing page
20. bearer-token API auth for operational dashboard routes
21. optional Meta `X-Hub-Signature-256` webhook verification
22. Docker-based production deployment scaffold
23. real-time browser voice loop: live STT → LLM → TTS over a WebSocket
24. Sarvam REST speech-to-text client (utterance transcription)
25. LLM-driven agent replies and qualification (OpenRouter / any OpenAI-compatible endpoint), with rule-based fallback
26. browser-microphone "Live call" demo wired into the operator dashboard

## Agents

Agents are reusable voice-call configurations. Each agent stores:

- `name`
- `script_key`
- `vertical`
- `language`
- `voice_provider`
- `telephony_provider`
- `opening_line`
- `qualification_goal`
- `is_active`

When a new Meta form/campaign is first seen, the backend assigns the most recently updated active agent's `script_key` to the created campaign. This makes the frontend agent studio useful immediately for local webhook simulation.

The live voice loop runs today in the browser via a WebSocket (mic → STT → LLM → TTS).
Wiring that same loop to real phone audio over Exotel media streaming is the next step.

Not implemented yet:

1. live bidirectional Exotel audio streaming into the WebSocket voice endpoint (phone calls)
2. low-latency Sarvam STT **WebSocket** streaming from phone audio (browser demo uses REST STT)
3. streaming TTS audio back into the phone call
4. role-based access control beyond a single operator account
5. production observability stack
6. managed production database migrations

## Environment variables

See [backend/.env.example](/Users/apple/Alphha/AI_voice/backend/.env.example).

For local development, the defaults use:

- SQLite
- `mock` telephony provider
- background-task dispatch
- single-operator auth with `admin` / `admin123`

Before exposing the app publicly, change:

- `ADMIN_PASSWORD`
- `AUTH_SECRET_KEY`
- `META_VERIFY_TOKEN`
- `META_APP_SECRET`

To use live Meta lead retrieval, set:

- `META_ACCESS_TOKEN`
- `META_API_VERSION`
- `META_APP_SECRET`

To use Exotel, set:

- `TELEPHONY_PROVIDER=exotel`
- `EXOTEL_API_KEY`
- `EXOTEL_API_TOKEN`
- `EXOTEL_ACCOUNT_SID`
- `EXOTEL_CALLER_ID`
- `EXOTEL_FROM_NUMBER`
- `EXOTEL_REGION`
- `EXOTEL_STREAM_URL` or `EXOTEL_FLOW_URL`

To use live speech, dialogue, CRM, and handoff integrations, set:

- `SARVAM_API_KEY`
- `LLM_PROVIDER=openai_compatible`
- `LLM_BASE_URL` (e.g. `https://openrouter.ai/api/v1` for OpenRouter)
- `LLM_API_KEY`
- `LLM_MODEL` (e.g. `mistralai/mistral-small-3.1-24b-instruct`)
- `LLM_REFERER`, `LLM_TITLE` (optional OpenRouter attribution headers)
- `CRM_PROVIDER=webhook`
- `CRM_WEBHOOK_URL`
- `HANDOFF_CHANNEL=webhook`
- `HANDOFF_WEBHOOK_URL`
- `OPERATOR_DESTINATION`

## Demo flow

With local mock settings:

1. Create or activate an agent in the frontend.
2. Use the webhook simulator to create a lead.
3. Confirm a call attempt appears.
4. Click `Run Demo` on an initiated attempt.
5. Review the created voice session, transcript preview, qualification score, and handoff event.

## Live voice loop

Each initiated call attempt also has a `Live call` action that opens a real STT → LLM → TTS
conversation in the browser:

1. Click `Live call` on an initiated/in-progress attempt.
2. Hold the mic button and speak (Telugu or Telugu-English code-mix), then release.
3. Each utterance is transcribed (STT), answered by the dialogue LLM, and the reply is spoken
   back (TTS); transcript turns stream into the panel.
4. Click `End call` to qualify the conversation and create a handoff.

The browser opens a WebSocket to
`/api/v1/voice-sessions/{session_id}/stream?token=<bearer>` (browsers cannot set WebSocket
headers, so the token is passed as a query param).

With local mock settings this works **without any API keys**: mock STT returns a canned
Telugu utterance and mock TTS returns silent audio, so the full loop, qualification, and
handoff are exercised end to end. Set `SARVAM_API_KEY` and an OpenRouter
(`LLM_PROVIDER=openai_compatible`) configuration to make it speak real Telugu.

> Latency note: the browser demo uses Sarvam REST STT (utterance-at-a-time). The brief's
> sub-800ms telephony target needs Sarvam WebSocket streaming STT + a Pipecat/Exotel media
> path, which is the documented follow-up.

## Enquiry-link funnel (P1)

The primary flow is a self-serve enquiry link the client shares on LinkedIn/Instagram:

1. A client copies their **Enquiry Link** from the dashboard (e.g. `https://app.example.com/enquiry?src=linkedin`)
   and pastes it into a social post.
2. A prospect clicks the link and submits a short form (name, phone, "what are you looking for").
   This hits the public `POST /api/v1/enquiries` endpoint (no login) which creates a lead, a web
   call attempt, and an in-progress voice session, and returns a short-lived **session-scoped token**.
3. The prospect immediately talks to the AI agent **in their browser** (Web Speech STT/TTS over the
   WebSocket). The agent confirms the submitted requirement and assesses whether the prospect is genuine.
4. On finish, the conversation is qualified. **Genuine** prospects (`qualified` / `callback_requested`)
   are routed to the client as a handoff and appear under "Genuine enquiries → client" in the dashboard;
   spam / not-genuine (`not_qualified`) are dropped.

Security: the enquiry token's subject is `enquiry:<session_id>`, and the WebSocket only accepts that
token for its own session — so the public call works without an operator login but can't access any
other session. Operator API routes still require a bearer token.

Open the public page directly at `/enquiry` (use **Chrome** for speech support). Real outbound phone
dialing (Exotel) is a later phase; today the "call" happens in the prospect's browser.

## Real phone calls (Exotel)

The agent can place a **real outbound phone call** through Exotel and hold the live Telugu
STT→LLM→TTS conversation over the phone, reusing the same voice-session/qualification/handoff
pipeline as the browser call.

How it works:

1. A call attempt is dialed via Exotel — auto-dispatched for Meta leads, or by clicking
   **Call now** on a queued attempt in the dashboard (`POST /call-attempts/{id}/dispatch` with
   `TELEPHONY_PROVIDER=exotel`).
2. `ExotelProvider.place_call` requests the call with `StreamUrl` pointing at the public media
   endpoint `/api/v1/telephony/exotel/stream`.
3. When the lead answers, Exotel streams the call's 8 kHz audio to that WebSocket. The server
   segments utterances with VAD, runs **Sarvam STT → LLM → Sarvam TTS**, and streams the agent's
   Telugu audio back.
4. On hangup the conversation is qualified; genuine leads become a handoff to the client.

Going live (requires your infrastructure — not testable on localhost, since Exotel can only reach
a public HTTPS/WSS URL):

1. Deploy the backend to a public HTTPS host.
2. Set `TELEPHONY_PROVIDER=exotel`, the `EXOTEL_*` credentials, `SARVAM_API_KEY`, and an
   OpenRouter LLM config.
3. Set a strong `EXOTEL_STREAM_SECRET` and
   `EXOTEL_STREAM_URL=wss://<host>/api/v1/telephony/exotel/stream?token=<EXOTEL_STREAM_SECRET>`.
4. Configure your Exotel Voicebot/Stream applet/caller ID (and DLT registration) for the call flow.
5. Dial a real number (Call now / auto-dispatch), answer, and watch the session + handoff appear
   in the dashboard.

Notes / current limits:

- This version is **half-duplex** (it transcribes a full utterance, then replies) using Sarvam
  REST STT per utterance. Sarvam **WebSocket streaming** STT + full barge-in for sub-800 ms latency
  is the documented follow-up.
- Exotel's exact media-frame key names are read defensively in `app/services/exotel_stream.py`;
  confirm them against Exotel's current bidirectional-streaming docs at integration time.
- The browser web-call (`/enquiry`, "Live call") still works key-free for demos; the phone path is
  the production channel.

## Production deployment

The repo includes Docker production scaffolding:

- [backend/Dockerfile](/Users/apple/Alphha/AI_voice/backend/Dockerfile)
- [frontend/Dockerfile](/Users/apple/Alphha/AI_voice/frontend/Dockerfile)
- [frontend/nginx.conf](/Users/apple/Alphha/AI_voice/frontend/nginx.conf)
- [docker-compose.prod.yml](/Users/apple/Alphha/AI_voice/docker-compose.prod.yml)
- [.env.production.example](/Users/apple/Alphha/AI_voice/.env.production.example)

Production startup rejects unsafe local defaults when `ENVIRONMENT=production` and `PRODUCTION_REQUIRE_SECURE_CONFIG=true`.

Run locally in production mode:

```bash
cd /Users/apple/Alphha/AI_voice
cp .env.production.example .env.production
# edit .env.production with real domains and secrets
docker compose --env-file .env.production -f docker-compose.prod.yml up --build
```

The compose file serves:

- frontend: `http://127.0.0.1:8080`
- backend: `http://127.0.0.1:8000`

For real production, terminate HTTPS at a reverse proxy or managed platform, point `PUBLIC_BASE_URL`, `FRONTEND_BASE_URL`, `CORS_ORIGINS`, and `VITE_API_BASE_URL` at the public domains, and use a managed database instead of the bundled SQLite volume for multi-instance deployments.

## Running tests

```bash
cd /Users/apple/Alphha/AI_voice/backend
pytest
```
