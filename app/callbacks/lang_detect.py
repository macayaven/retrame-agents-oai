"""Language detection callback used in *before_model_callback*.

The callback inspects the incoming user message (present in the `CallbackContext`)
and sets a lightweight language flag in the session state (``ctx.state["lang"]``)
so that downstream agents/prompts can localise their responses.  The detection
itself purposefully stays **naïve** - we only differentiate between Spanish and
English because those are the two languages the therapeutic POC currently
supports.

Signature accepted by ADK for *before_model_callback*:

    Callable[[CallbackContext, LlmRequest], Awaitable[LlmResponse | None]

We do **not** alter or short-circuit the model request, therefore we always
return ``None``.
"""

from __future__ import annotations

from typing import ClassVar

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest


class LangCallback:
    _ES_CHARS: ClassVar[set[str]] = set("áéíóúÁÉÍÓÚñÑ¿¡üÜçÇ")

    def __call__(
        self, *, callback_context: CallbackContext, llm_request: LlmRequest
    ) -> None:  # type: ignore[override]
        """Detect language of the **user message** and store it in state.

        We examine the *latest* user message only - available on
        ``callback_context.user_content``.  If the language was already
        detected in a previous turn (``state['lang']``), we exit early.
        """

        # Exit early if language is already detected for this session.
        if "lang" in callback_context.state:
            return

        user_content = callback_context.user_content
        if not user_content or not user_content.parts:
            # Nothing to analyse - default to English.
            callback_context.state["lang"] = "en"
            return

        text_segments: list[str] = []
        for part in user_content.parts:
            if part.text:
                text_segments.append(part.text)

        joined = " ".join(text_segments)

        detected = self._detect_lang(joined)
        callback_context.state["lang"] = detected or "en"

        # We don't need to modify the request or return custom LLM output.
        return

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    @classmethod
    def _detect_lang(cls, text: str) -> str | None:
        """Very lightweight language heuristic (Spanish vs. English).

        Returns ``'es'`` if we find *any* Spanish-specific character, otherwise
        returns ``'en'``.  The heuristic is **good enough** for the current POC
        and has no external dependencies.
        """

        for ch in text:
            if ch in cls._ES_CHARS:
                return "es"
        return "en"
