from __future__ import annotations

import json
import re

from app.core.config import Settings
from app.models.entities import Agent, Lead, QualificationOutcome, TranscriptTurn
from app.providers.llm.factory import build_dialogue_provider
from app.services.dialogue import (
    QualificationDecision,
    next_agent_reply,
    opening_line_for,
    qualify_conversation,
)

_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def llm_enabled(settings: Settings) -> bool:
    """Whether a real LLM should drive dialogue. Mock keeps the deterministic rule-based path."""
    return settings.llm_provider != "mock"


def _vertical(agent: Agent | None) -> str:
    return (agent.vertical if agent and agent.vertical else "general") or "general"


def _language(agent: Agent | None, lead: Lead) -> str:
    if agent and agent.language:
        return agent.language
    return lead.preferred_language


def _enquiry_requirement(lead: Lead) -> str | None:
    raw = getattr(lead, "raw_fields", None)
    if isinstance(raw, dict):
        requirement = raw.get("requirement")
        if isinstance(requirement, str) and requirement.strip():
            return requirement.strip()
    return None


def _system_prompt(agent: Agent | None, lead: Lead) -> str:
    goal = (
        agent.qualification_goal
        if agent and agent.qualification_goal
        else "Confirm interest, capture intent and budget, and book the next step."
    )
    opening = opening_line_for(agent, lead)
    requirement = _enquiry_requirement(lead)
    enquiry_context = (
        f"The prospect submitted this enquiry through your link: \"{requirement}\". "
        "Confirm the details of that requirement, then naturally assess whether they are a "
        "genuine, serious prospect (real intent and contactable) versus a casual or fake enquiry. "
        if requirement
        else ""
    )
    return (
        "You are a warm, professional outbound voice agent for an Indian small business. "
        f"Speak Telugu-first and tolerate natural Telugu-English code-mixing (the {_language(agent, lead)} "
        f"caller is from Hyderabad). Vertical: {_vertical(agent)}. "
        "Keep every reply to one or two short spoken sentences and ask only one question at a time. "
        "Never invent facts about the business. Be respectful if the lead is not interested and "
        "offer to stop. "
        f"{enquiry_context}"
        f"Conversation goal: {goal} "
        f"Your opening line was: \"{opening}\"."
    )


def _render_transcript(turns: list[TranscriptTurn]) -> str:
    lines = []
    for turn in turns:
        speaker = turn.speaker.value.upper()
        lines.append(f"{speaker}: {turn.text}")
    return "\n".join(lines) if lines else "(no turns yet)"


def generate_agent_reply(
    settings: Settings,
    *,
    agent: Agent | None,
    lead: Lead,
    turns: list[TranscriptTurn],
) -> str:
    """LLM-generated next agent utterance, falling back to the rule-based reply on any failure."""
    if not llm_enabled(settings):
        return next_agent_reply(agent, lead, turns)

    user_prompt = (
        "Here is the call transcript so far:\n"
        f"{_render_transcript(turns)}\n\n"
        "Reply with ONLY the agent's next spoken line (no labels, no quotes)."
    )
    try:
        provider = build_dialogue_provider(settings)
        completion = provider.complete(
            system_prompt=_system_prompt(agent, lead),
            user_prompt=user_prompt,
        )
        reply = completion.text.strip().strip('"')
        return reply or next_agent_reply(agent, lead, turns)
    except Exception:
        return next_agent_reply(agent, lead, turns)


def qualify_with_llm(
    settings: Settings,
    *,
    agent: Agent | None,
    lead: Lead,
    turns: list[TranscriptTurn],
) -> QualificationDecision:
    """LLM qualification with strict-JSON output; falls back to rule-based on any failure."""
    if not llm_enabled(settings):
        return qualify_conversation(agent=agent, lead=lead, turns=turns)

    allowed = ", ".join(o.value for o in QualificationOutcome)
    user_prompt = (
        "Classify this prospect from the call transcript. Decide if they are a GENUINE, serious "
        "prospect worth sending to the client.\n"
        "  - qualified: genuine intent, contactable, send to client.\n"
        "  - callback_requested: genuine but wants a callback at a specific time.\n"
        "  - not_qualified: not genuine, wrong number, spam, or clearly not interested.\n"
        "  - needs_review: unclear; a human should review.\n\n"
        f"Transcript:\n{_render_transcript(turns)}\n\n"
        "Respond with ONLY a JSON object, no prose, of the form:\n"
        '{"outcome": "<one of: ' + allowed + '>", '
        '"score": <integer 0-100, higher = more genuine>, '
        '"summary": "<one-sentence summary of the requirement and genuineness>", '
        '"fields": {"requirement": "...", "intent": "...", "budget": "...", '
        '"timeframe": "...", "genuine": true|false, "next_step": "..."}}'
    )
    try:
        provider = build_dialogue_provider(settings)
        completion = provider.complete(
            system_prompt=_system_prompt(agent, lead),
            user_prompt=user_prompt,
        )
        return _parse_qualification(completion.text, agent=agent, lead=lead, turns=turns)
    except Exception:
        return qualify_conversation(agent=agent, lead=lead, turns=turns)


def _parse_qualification(
    raw: str,
    *,
    agent: Agent | None,
    lead: Lead,
    turns: list[TranscriptTurn],
) -> QualificationDecision:
    match = _JSON_BLOCK.search(raw or "")
    if match is None:
        return qualify_conversation(agent=agent, lead=lead, turns=turns)
    try:
        data = json.loads(match.group(0))
    except (ValueError, json.JSONDecodeError):
        return qualify_conversation(agent=agent, lead=lead, turns=turns)

    try:
        outcome = QualificationOutcome(str(data["outcome"]).strip().lower())
    except (KeyError, ValueError):
        return qualify_conversation(agent=agent, lead=lead, turns=turns)

    score = data.get("score", 0)
    try:
        score = max(0, min(100, int(score)))
    except (TypeError, ValueError):
        score = 0

    summary = str(data.get("summary") or f"{lead.full_name or 'Lead'} classified as {outcome.value}.")
    fields = data.get("fields")
    if not isinstance(fields, dict):
        fields = {}
    fields.setdefault("lead_name", lead.full_name)
    fields.setdefault("phone_number", lead.phone_number)
    fields.setdefault("turn_count", len(turns))
    fields["human_follow_up_required"] = outcome in {
        QualificationOutcome.QUALIFIED,
        QualificationOutcome.CALLBACK_REQUESTED,
    }
    return QualificationDecision(outcome=outcome, score=score, summary=summary, fields=fields)
