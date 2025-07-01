from __future__ import annotations

"""Session-scoped shared state for the AURA Assistants pipeline."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SessionState:
    """Container passed between the Intake → Parser → Reframe stages."""

    transcript: List[Dict[str, str]] = field(default_factory=list)
    intake_json: Optional[Dict[str, Any]] = None
    reframe_json: Optional[Dict[str, Any]] = None

    def add_user_message(self, content: str) -> None:
        """Append a user message to the transcript."""

        self.transcript.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        """Append an assistant message to the transcript."""

        self.transcript.append({"role": "assistant", "content": content}) 