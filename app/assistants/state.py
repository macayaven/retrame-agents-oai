from __future__ import annotations

"""Session-scoped shared state for the AURA Assistants pipeline."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionState:
    """Container passed between the Intake → Parser → Reframe stages."""

    transcript: list[dict[str, str]] = field(default_factory=list)
    intake_json: dict[str, Any] | None = None
    reframe_json: dict[str, Any] | None = None

    def add_user_message(self, content: str) -> None:
        """Append a user message to the transcript."""

        self.transcript.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        """Append an assistant message to the transcript."""

        self.transcript.append({"role": "assistant", "content": content})
