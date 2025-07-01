"""Language detection callback used in *before_model_callback*.

The callback inspects the incoming user message (present in the `CallbackContext`)
and sets a language flag in the session state (``ctx.state["lang"]``)
so that downstream agents/prompts can localise their responses. Uses Google
Cloud Translation API for reliable language detection.

Signature accepted by ADK for *before_model_callback*:

    Callable[[CallbackContext, LlmRequest], Awaitable[LlmResponse | None]

We do **not** alter or short-circuit the model request, therefore we always
return ``None``.
"""

from __future__ import annotations

import os
from typing import ClassVar

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.cloud import translate_v2 as translate  # type: ignore[import-untyped]


class LangCallback:
    _ES_CHARS: ClassVar[set[str]] = set("áéíóúÁÉÍÓÚñÑ¿¡üÜçÇ")
    _translate_client = None

    @classmethod
    def _get_translate_client(cls) -> translate.Client | None:
        """Lazy initialize the translate client."""
        if cls._translate_client is None and os.environ.get("GOOGLE_API_KEY"):
            cls._translate_client = translate.Client()
        return cls._translate_client

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
        """Detect language using Google Cloud Translation API with fallback.

        Returns language code ('es' or 'en'). Falls back to character-based
        detection if API is unavailable or fails.
        """
        # Try Google Translate API first
        client = cls._get_translate_client()
        if client:
            try:
                # Detect language
                result = client.detect_language(text)
                detected_lang = result.get("language", "")
                confidence = result.get("confidence", 0)

                # Map detected language to our supported languages
                if detected_lang == "es" and confidence > 0.7:
                    return "es"
                if detected_lang == "en" and confidence > 0.7:
                    return "en"
                # If detected but not es/en with high confidence,
                # fall through to character detection
            except Exception:
                # API failure, fall back to character detection
                pass

        # Fallback: Character-based detection
        for ch in text:
            if ch in cls._ES_CHARS:
                return "es"
        return "en"
