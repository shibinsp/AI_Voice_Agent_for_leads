# Go-Live Runbook — Real Telugu Phone Voice Agent

This checklist covers the steps that require **your accounts, credentials, and a deployed host** —
the parts that cannot be done from the codebase alone. The application code is already wired for
all of them; this is the operational sequence to switch it on.

---

## 1. Sarvam (speech) — `SARVAM_API_KEY`

1. Create an account at https://www.sarvam.ai and open the Developer Dashboard → API Keys.
2. Generate a production key and store it in your secret manager.
3. Set in the backend environment:
   ```
   SARVAM_API_KEY=sk_live_xxxxxxxx
   # optional low-latency phone STT (falls back to REST automatically on error):
   SARVAM_STT_STREAMING=true
   ```
   Until this key is set, STT/TTS run in **mock** mode (canned text + silent audio).

## 2. Exotel (telephony) — account + credentials

1. Get an Exotel account and an **Exophone** (virtual number).
2. From the Exotel dashboard collect: API Key, API Token, Account SID, Caller ID, From number.
3. Set in the backend environment:
   ```
   TELEPHONY_PROVIDER=exotel
   EXOTEL_API_KEY=...
   EXOTEL_API_TOKEN=...
   EXOTEL_ACCOUNT_SID=...
   EXOTEL_CALLER_ID=...
   EXOTEL_FROM_NUMBER=...
   EXOTEL_REGION=in
   ```

## 3. DLT-approved caller ID (regulatory — India)

1. Register on a DLT platform (e.g. via your operator) and complete entity/sender verification.
2. Ensure the **caller ID / Exophone is DLT-approved** for outbound commercial calls (TRAI).
3. Keep call-consent + recording disclosure in the enquiry flow (already shown on `/enquiry`).
   This step is mandatory before dialing real customers and is handled with Exotel/your telecom.

## 4. Deploy the backend to a public HTTPS endpoint

Exotel must reach a **public** URL — `localhost` will not work.

1. Deploy the production stack (Postgres + Redis + backend + RQ worker + frontend):
   ```
   cp .env.production.example .env.production   # fill in real secrets
   docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
   ```
2. Run database migrations on first deploy (instead of relying on create_all):
   ```
   docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
   ```
3. Put the backend behind HTTPS (managed platform, or a reverse proxy terminating TLS) and set:
   ```
   ENVIRONMENT=production
   PUBLIC_BASE_URL=https://api.yourdomain.com
   CORS_ORIGINS=https://app.yourdomain.com
   ADMIN_PASSWORD=<strong>   AUTH_SECRET_KEY=<32+ random bytes>
   META_VERIFY_TOKEN=<...>   META_APP_SECRET=<...>
   ```
   Production startup refuses insecure defaults when `PRODUCTION_REQUIRE_SECURE_CONFIG=true`.

## 5. Secure WebSocket (`wss://`) for media streaming

1. Set a strong shared secret and point the Exotel media StreamUrl at the public WSS endpoint:
   ```
   EXOTEL_STREAM_SECRET=<random-secret>
   EXOTEL_STREAM_URL=wss://api.yourdomain.com/api/v1/telephony/exotel/stream?token=<EXOTEL_STREAM_SECRET>
   EXOTEL_STATUS_CALLBACK_URL=https://api.yourdomain.com/api/v1/webhooks/exotel/status
   ```
2. Configure the Exotel Voicebot / Voice Streaming applet to stream call audio to that StreamUrl.

## 6. End-to-end phone call test

1. In the dashboard, create/activate an agent (sets the script + opening line).
2. Trigger a call: either auto-dispatch from a Meta lead, the enquiry link, or **Call now** on a
   queued call attempt.
3. Answer the call on a real mobile and hold a Telugu conversation.
4. Verify in the dashboard:
   - a Voice Session with transcript turns,
   - a qualification outcome, and
   - a **handoff** for genuine leads.
5. Watch `GET /api/v1/metrics` and the structured JSON logs (each line carries a `request_id`)
   for latency and errors. Review ~20 test calls before onboarding a client (per the brief).

---

## Quick reference — what's already built

| Capability | Where |
|---|---|
| Exotel outbound dial + status callbacks | `app/providers/telephony/exotel.py`, `app/services/providers.py` |
| Exotel media WebSocket → STT→LLM→TTS bridge | `app/api/routes/telephony_stream.py`, `app/services/exotel_stream.py` |
| Sarvam STT/TTS (REST) + streaming STT option | `app/providers/speech/sarvam.py`, `sarvam_stream.py` |
| LLM dialogue + qualification (OpenRouter) | `app/services/llm_dialogue.py` |
| Postgres + Redis (RQ) + worker | `docker-compose.prod.yml`, `app/services/queue.py` |
| Migrations | `alembic upgrade head` (`migrations/`) |
| Metrics + structured logging | `GET /api/v1/metrics`, `app/core/logging.py` |
| Analytics | `GET /api/v1/analytics/summary` + dashboard Analytics panel |
