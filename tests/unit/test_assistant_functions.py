import base64

import pytest

from app.assistants.functions.analyse import analyse_and_reframe
from app.assistants.functions.collect import collect_context
from app.assistants.functions.escalate import escalate_crisis
from app.assistants.functions.pdf import generate_pdf_legacy as generate_pdf


@pytest.mark.asyncio
async def test_collect_context_happy_path():
    fake_messages = [
        {"role": "user", "content": "I'm reaching out because I'm anxious about work."},
        {"role": "user", "content": "During yesterday's team meeting with my boss I thought, \"Everyone thinks I'm incompetent\"."},
        {"role": "user", "content": "Emotion: Shame 8/10"},
        {"role": "user", "content": "By the way, my name is Alice and I'm 29 years old."},
    ]

    result = await collect_context(messages=fake_messages)

    assert result["goal_reached"] is True
    assert result["intake_data"]["trigger_situation"].lower().startswith("during yesterday's team meeting")
    assert result["intake_data"]["automatic_thought"] == "Everyone thinks I'm incompetent"
    assert result["intake_data"]["emotion_data"] == {"emotion": "shame", "intensity": 8}
    assert result["intake_data"]["reason"] == "i'm reaching out because i'm anxious about work."


@pytest.mark.asyncio
async def test_analyse_stub():
    output = await analyse_and_reframe({"name": "Alice", "reason": "I think everyone hates me."})
    assert "balanced_thought" in output
    assert output["certainty_before"] < output["certainty_after"]


@pytest.mark.parametrize("in_memory", [True])
def test_generate_pdf_stub(monkeypatch, in_memory, supabase_env_vars):
    # Provide fake Supabase env so the fallback path triggers (supabase lib absent).


    pdf_link = generate_pdf({"intake_data": {}, "analysis_output": ""})["pdf_url"]
    assert pdf_link.startswith("data:application/pdf;base64,")
    # quick decode sanity check
    encoded = pdf_link.split(",", 1)[1]
    decoded = base64.b64decode(encoded)
    assert decoded.startswith(b"%PDF")


def test_escalate_crisis():
    resp = escalate_crisis()
    assert resp["crisis"] is True
    assert "024" in str(resp["message"])
