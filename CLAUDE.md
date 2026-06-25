# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

Telugu-first AI voice agent for Instagram/LinkedIn lead conversion. FastAPI backend
(`backend/`) + React/Vite operator dashboard (`frontend/`). Capabilities: live STT→LLM→TTS
voice loop (browser Web Speech + OpenRouter LLM + Sarvam speech), a public enquiry-link funnel,
and real outbound phone calls via Exotel media streaming.

## Rules

- **Commit each file as its own separate commit (one commit per file).** Do not batch multiple
  files into a single commit.
- **Never commit secrets.** `.env` files are gitignored — keep API keys (OpenRouter, Sarvam,
  Exotel, Meta) out of version control. Only `.env.example` files are tracked.

## Common commands

- Backend tests: `cd backend && .venv/bin/python -m pytest -q`
- Backend dev server: `cd backend && .venv/bin/uvicorn app.main:app --reload`
- Frontend dev: `cd frontend && npm run dev`
- Frontend typecheck/build: `cd frontend && npx tsc --noEmit && npx vite build`
