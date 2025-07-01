from unittest.mock import MagicMock

from google.adk.agents.callback_context import CallbackContext  # type: ignore
from google.adk.models.llm_response import LlmResponse  # type: ignore
from google.genai.types import Content, Part  # type: ignore

from app.callbacks.transcript_acc import TranscriptAccumulator


def test_transcript_accumulator_appends_user_and_assistant_messages() -> None:
    callback = TranscriptAccumulator()
    ctx = MagicMock(spec=CallbackContext)
    ctx.state = {}
    ctx.user_content = Content(parts=[Part(text="Hello")])
    llm_response = LlmResponse(content=Content(parts=[Part(text="Hi there!")]))

    callback(callback_context=ctx, llm_response=llm_response)

    assert ctx.state["conv_raw"] == [
        {"role": "user", "text": "Hello"},
        {"role": "assistant", "text": "Hi there!"},
    ]


def test_transcript_accumulator_appends_to_existing_transcript() -> None:
    callback = TranscriptAccumulator()
    ctx = MagicMock(spec=CallbackContext)
    ctx.state = {"conv_raw": [{"role": "user", "text": "Initial message"}]}
    ctx.user_content = Content(parts=[Part(text="Another message")])
    llm_response = LlmResponse(content=Content(parts=[Part(text="Another response")]))

    callback(callback_context=ctx, llm_response=llm_response)

    assert ctx.state["conv_raw"] == [
        {"role": "user", "text": "Initial message"},
        {"role": "user", "text": "Another message"},
        {"role": "assistant", "text": "Another response"},
    ]


def test_transcript_accumulator_no_user_content() -> None:
    callback = TranscriptAccumulator()
    ctx = MagicMock(spec=CallbackContext)
    ctx.state = {}
    ctx.user_content = None
    llm_response = LlmResponse(content=Content(parts=[Part(text="Hi there!")]))

    callback(callback_context=ctx, llm_response=llm_response)

    assert ctx.state["conv_raw"] == [
        {"role": "assistant", "text": "Hi there!"},
    ]


def test_transcript_accumulator_no_llm_response() -> None:
    callback = TranscriptAccumulator()
    ctx = MagicMock(spec=CallbackContext)
    ctx.state = {}
    ctx.user_content = Content(parts=[Part(text="Hello")])
    llm_response = LlmResponse(content=Content(parts=[Part(text="")]))

    callback(callback_context=ctx, llm_response=llm_response)

    assert ctx.state["conv_raw"] == [
        {"role": "user", "text": "Hello"},
    ]
