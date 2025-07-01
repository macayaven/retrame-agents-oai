"""After-model callback that keeps a raw conversation transcript in the session state.

The callback appends **two** entries per turn:
    1. The user message (role == ``"user"``)
    2. The assistant/model reply (role == ``"assistant"``)

The entire transcript lives under ``state["conv_raw"]`` as a simple list so it
can be easily serialised or displayed later on.
"""

from __future__ import annotations

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse


class TranscriptAccumulator:
    def __call__(
        self,
        *,
        callback_context: CallbackContext,
        llm_response: LlmResponse,
    ) -> LlmResponse | None:  # type: ignore[override]
        state = callback_context.state

        transcript: list[dict[str, str]] = state.get("conv_raw", [])  # type: ignore[assignment]

        # --------------------------- user message --------------------------- #
        user_content = callback_context.user_content
        if user_content and user_content.parts:
            user_text = "".join(
                part.text or "" for part in user_content.parts if hasattr(part, "text")
            ).strip()
            if user_text:
                transcript.append({"role": "user", "text": user_text})

        # ------------------------ assistant message ------------------------ #
        if llm_response and llm_response.content and llm_response.content.parts:
            assistant_text = "".join(
                part.text or "" for part in llm_response.content.parts if hasattr(part, "text")
            ).strip()
            if assistant_text:
                transcript.append({"role": "assistant", "text": assistant_text})

        # Persist back to state - the object returned by ``state[...]`` is delta-aware
        # so direct mutation registers a state_delta in the event.
        state["conv_raw"] = transcript

        # We do **not** modify the model response, therefore return ``None``.
        return None
