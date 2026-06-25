from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.models.entities import QualificationOutcome
from app.providers.llm.base import DialogueCompletion
from app.services import llm_dialogue


def _speaker(value: str) -> SimpleNamespace:
    return SimpleNamespace(value=value)


def _fixtures():
    agent = SimpleNamespace(
        opening_line="Namaskaram",
        qualification_goal="Capture intent and budget.",
        vertical="clinics",
        language="te-IN",
        script_key="clinic_telugu_v1",
    )
    lead = SimpleNamespace(
        full_name="Ravi Teja",
        phone_number="+919876543210",
        preferred_language="te-IN",
        city="Hyderabad",
        campaign=None,
    )
    turns = [
        _turn("agent", "Namaskaram, appointment gurinchi maatladadam."),
        _turn("lead", "Haan, naaku appointment book cheyali."),
    ]
    return agent, lead, turns


def _turn(speaker: str, text: str) -> SimpleNamespace:
    return SimpleNamespace(speaker=_speaker(speaker), text=text)


class _FakeProvider:
    name = "fake"

    def __init__(self, text: str) -> None:
        self._text = text

    def complete(self, *, system_prompt: str, user_prompt: str) -> DialogueCompletion:
        return DialogueCompletion(text=self._text, provider_payload={})


def _live_settings() -> Settings:
    return Settings(
        llm_provider="openai_compatible",
        llm_base_url="http://example.test",
        llm_api_key="key",
    )


def test_qualify_with_llm_parses_json(monkeypatch: pytest.MonkeyPatch):
    canned = (
        'Here is the result: {"outcome": "qualified", "score": 91, '
        '"summary": "Lead wants an appointment.", "fields": {"intent": "appointment"}}'
    )
    monkeypatch.setattr(llm_dialogue, "build_dialogue_provider", lambda settings: _FakeProvider(canned))
    agent, lead, turns = _fixtures()

    decision = llm_dialogue.qualify_with_llm(_live_settings(), agent=agent, lead=lead, turns=turns)

    assert decision.outcome is QualificationOutcome.QUALIFIED
    assert decision.score == 91
    assert decision.fields["intent"] == "appointment"
    assert decision.fields["human_follow_up_required"] is True


def test_qualify_with_llm_falls_back_on_bad_json(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        llm_dialogue,
        "build_dialogue_provider",
        lambda settings: _FakeProvider("They sound interested but no JSON here."),
    )
    agent, lead, turns = _fixtures()

    decision = llm_dialogue.qualify_with_llm(_live_settings(), agent=agent, lead=lead, turns=turns)

    # rule-based path: "appointment" keyword -> qualified, score 82
    assert decision.outcome is QualificationOutcome.QUALIFIED
    assert decision.score == 82


def test_generate_agent_reply_uses_llm_text(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        llm_dialogue,
        "build_dialogue_provider",
        lambda settings: _FakeProvider('  "Meeru when free unnaru?"  '),
    )
    agent, lead, turns = _fixtures()

    reply = llm_dialogue.generate_agent_reply(_live_settings(), agent=agent, lead=lead, turns=turns)

    assert reply == "Meeru when free unnaru?"


def test_mock_provider_uses_rule_based(monkeypatch: pytest.MonkeyPatch):
    agent, lead, turns = _fixtures()
    settings = Settings(llm_provider="mock")

    decision = llm_dialogue.qualify_with_llm(settings, agent=agent, lead=lead, turns=turns)

    # deterministic rule-based outcome (appointment keyword)
    assert decision.outcome is QualificationOutcome.QUALIFIED
