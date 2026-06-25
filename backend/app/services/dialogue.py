from __future__ import annotations

from dataclasses import dataclass

from app.models.entities import Agent, Lead, QualificationOutcome, TranscriptTurn


@dataclass(slots=True)
class QualificationDecision:
    outcome: QualificationOutcome
    score: int
    summary: str
    fields: dict[str, str | int | bool | None]


def opening_line_for(agent: Agent | None, lead: Lead) -> str:
    if agent and agent.opening_line:
        return agent.opening_line
    name = lead.full_name or "there"
    return f"Namaskaram {name}, I am calling about the inquiry you submitted."


def next_agent_reply(agent: Agent | None, lead: Lead, turns: list[TranscriptTurn]) -> str:
    lead_turns = [turn.text for turn in turns if turn.speaker.value == "lead"]
    if not lead_turns:
        return opening_line_for(agent, lead)
    if len(lead_turns) == 1:
        return "Thank you. May I confirm your preferred time for a human callback?"
    return "Got it. I will share this with our team for follow-up."


def qualify_conversation(
    *,
    agent: Agent | None,
    lead: Lead,
    turns: list[TranscriptTurn],
) -> QualificationDecision:
    transcript = " ".join(turn.text.lower() for turn in turns)
    positive_terms = ("interested", "appointment", "visit", "budget", "today", "tomorrow", "call")
    negative_terms = ("not interested", "wrong number", "stop", "do not call")

    if any(term in transcript for term in negative_terms):
        outcome = QualificationOutcome.NOT_QUALIFIED
        score = 15
    elif "callback" in transcript or "call back" in transcript:
        outcome = QualificationOutcome.CALLBACK_REQUESTED
        score = 72
    elif any(term in transcript for term in positive_terms):
        outcome = QualificationOutcome.QUALIFIED
        score = 82
    else:
        outcome = QualificationOutcome.NEEDS_REVIEW
        score = 48

    fields = {
        "lead_name": lead.full_name,
        "phone_number": lead.phone_number,
        "city": lead.city,
        "vertical": agent.vertical if agent else None,
        "script_key": agent.script_key if agent else lead.campaign.script_key if lead.campaign else None,
        "turn_count": len(turns),
        "human_follow_up_required": outcome
        in {QualificationOutcome.QUALIFIED, QualificationOutcome.CALLBACK_REQUESTED},
    }
    summary = (
        f"{lead.full_name or 'Lead'} was classified as {outcome.value.replace('_', ' ')} "
        f"with score {score}. "
        f"Goal: {agent.qualification_goal if agent and agent.qualification_goal else 'standard qualification'}."
    )
    return QualificationDecision(outcome=outcome, score=score, summary=summary, fields=fields)
