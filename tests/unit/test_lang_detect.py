from unittest.mock import MagicMock

from google.adk.agents.callback_context import CallbackContext  # type: ignore
from google.genai.types import Content, Part  # type: ignore
import pytest  # type: ignore

from app.callbacks.lang_detect import LangCallback


@pytest.mark.parametrize(
    "text, expected_lang",
    [
        ("Hello, how are you?", "en"),
        ("Hola, ¿cómo estás?", "es"),
        ("This is a test.", "en"),
        ("áéíóúÁÉÍÓÚñÑ¿¡üÜçÇ", "es"),
    ],
)
def test_lang_detect_callback(text: str, expected_lang: str) -> None:
    callback = LangCallback()
    ctx = MagicMock(spec=CallbackContext)
    ctx.state = {}
    ctx.user_content = Content(parts=[Part(text=text)])

    callback(callback_context=ctx, llm_request=MagicMock())

    assert ctx.state["lang"] == expected_lang


def test_lang_detect_callback_no_user_content() -> None:
    callback = LangCallback()
    ctx = MagicMock(spec=CallbackContext)
    ctx.state = {}
    ctx.user_content = None

    callback(callback_context=ctx, llm_request=MagicMock())

    assert ctx.state["lang"] == "en"


def test_lang_detect_callback_lang_already_detected() -> None:
    callback = LangCallback()
    ctx = MagicMock(spec=CallbackContext)
    ctx.state = {"lang": "fr"}
    ctx.user_content = Content(parts=[Part(text="Hello")])

    callback(callback_context=ctx, llm_request=MagicMock())

    assert ctx.state["lang"] == "fr"
