from unittest.mock import MagicMock, PropertyMock

from google.adk.agents.callback_context import CallbackContext  # type: ignore
from google.adk.events import EventActions  # type: ignore
from google.adk.models.llm_response import LlmResponse  # type: ignore
from google.genai.types import Content, Part  # type: ignore
import pytest  # type: ignore

from app.callbacks.safety_filters import SafetyGuard


@pytest.mark.parametrize(
    "text",
    [
        "My SSN is 123-45-6789",
        "My ssn is 123-45-6789",
        "My social security number is 123456789",
    ],
)
def test_safety_guard_detects_ssn_and_escalates(text: str) -> None:
    callback = SafetyGuard()
    ctx = MagicMock(spec=CallbackContext)
    type(ctx).user_content = PropertyMock(return_value=Content(parts=[Part(text=text)]))
    ctx.actions = EventActions()

    response = callback(callback_context=ctx, llm_request=MagicMock())

    assert ctx.actions.escalate is True
    assert isinstance(response, LlmResponse)
    assert response and response.content
    text = response.content.parts[0].text
    assert text and "I'm sorry" in text  # message wording may evolve, check keyword


def test_safety_guard_does_not_escalate_for_safe_message() -> None:
    callback = SafetyGuard()
    ctx = MagicMock(spec=CallbackContext)
    type(ctx).user_content = PropertyMock(
        return_value=Content(parts=[Part(text="This is a safe message.")])
    )
    ctx.actions = EventActions()

    response = callback(callback_context=ctx, llm_request=MagicMock())

    assert not ctx.actions.escalate
    assert response is None


def test_safety_guard_no_user_content() -> None:
    callback = SafetyGuard()
    ctx = MagicMock(spec=CallbackContext)
    type(ctx).user_content = PropertyMock(return_value=None)
    ctx.actions = EventActions()

    response = callback(callback_context=ctx, llm_request=MagicMock())

    assert not ctx.actions.escalate
    assert response is None
