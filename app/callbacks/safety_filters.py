# app/callbacks/safety_filters.py
from __future__ import annotations
import re
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

_SSN_REGEXES = [
    re.compile(r"\bssn\b", re.IGNORECASE),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # 123‑45‑6789
    re.compile(r"\b\d{9}\b"),              # 123456789
]

# Very conservative crisis phrases (lower‑case inputs)
_CRISIS_PHRASES = [
    r"kill myself",                # en
    r"end my life",
    r"suicide\s*(?:attempt|plan)?",
    r"self[-\s]?harm",
    r"me quiero suicidar",         # es
    r"quiero quitarme la vida",
    r"no quiero vivir",
]

_CRISIS_REGEX = re.compile("|".join(_CRISIS_PHRASES), re.IGNORECASE)

# ---------------------------------------------------------------------------

class SafetyGuard:
    """
    before_model_callback that blocks:
      • obvious PII (US SSN)      → escalate
      • self‑harm / suicide cues  → escalate & crisis flag
    """

    def __call__(
        self, *, callback_context: CallbackContext, llm_request: LlmRequest
    ) -> LlmResponse | None:
        user_content = callback_context.user_content
        if not user_content or not user_content.parts:
            return None

        text = " ".join(part.text for part in user_content.parts if part.text).strip()
        if not text:
            return None

        # ------------------------------------------------------------------ #
        # 1. Crisis check                                                     #
        # ------------------------------------------------------------------ #
        if _CRISIS_REGEX.search(text):
            if callback_context.actions:  # type: ignore[attr-defined]
                callback_context.actions.escalate = True  # type: ignore[attr-defined]
            # Flag for downstream agents so they can skip normal processing
            callback_context.state["crisis"] = True

            crisis_msg = (
                "Parece que estás pasando por un momento muy difícil y "
                "podrías estar pensando en hacerte daño. "
                "Por favor, llama inmediatamente al **024** (línea de ayuda "
                "en España, 24 h, gratuita) o al **112** si tu vida está en "
                "peligro. Si te encuentras fuera de España, marca el número de "
                "emergencias local o consulta https://findahelpline.com. "
                "Un profesional se pondrá en contacto contigo en breve."
            )
            return LlmResponse(content=types.Content(parts=[types.Part(text=crisis_msg)]))

        # ------------------------------------------------------------------ #
        # 2. PII (SSN) check                                                 #
        # ------------------------------------------------------------------ #
        if any(r.search(text) for r in _SSN_REGEXES):
            if callback_context.actions:  # type: ignore[attr-defined]
                callback_context.actions.escalate = True  # type: ignore[attr-defined]

            pii_msg = (
                "I'm sorry, but I can't process personal data like Social "
                "Security Numbers. A team member will review your last "
                "message shortly."
            )
            return LlmResponse(content=types.Content(parts=[types.Part(text=pii_msg)]))

        # No issues – let the model run
        return None