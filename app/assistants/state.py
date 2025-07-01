from __future__ import annotations

"""Session-scoped shared state for the AURA Assistants pipeline."""

from dataclasses import dataclass, field
from enum import Enum
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


class Phase(Enum):
    """Orchestrator state phases."""

    S0_START = "start"
    S1_INTAKE = "intake"
    S2_CRISIS_CHECK = "crisis_check"
    S3_ANALYST_QA = "analyst_qa"
    S4_REFRAME = "reframe"
    S5_PDF_OFFER = "pdf_offer"
    S6_UPLOAD_PDF = "upload_pdf"
    S7_DONE = "done"


# State transition mapping: (current_phase, event) -> next_phase
TRANSITIONS: dict[tuple[Phase, str], Phase] = {
    # Initial user message starts intake
    (Phase.S0_START, "user_message"): Phase.S1_INTAKE,

    # Intake complete triggers crisis check
    (Phase.S1_INTAKE, "complete"): Phase.S2_CRISIS_CHECK,

    # Crisis check outcomes
    (Phase.S2_CRISIS_CHECK, "safe"): Phase.S3_ANALYST_QA,
    (Phase.S2_CRISIS_CHECK, "crisis"): Phase.S7_DONE,

    # Analyst Q&A outcomes
    (Phase.S3_ANALYST_QA, "complete"): Phase.S4_REFRAME,
    (Phase.S3_ANALYST_QA, "crisis"): Phase.S7_DONE,

    # Reframe complete offers PDF
    (Phase.S4_REFRAME, "complete"): Phase.S5_PDF_OFFER,

    # PDF offer outcomes
    (Phase.S5_PDF_OFFER, "accept"): Phase.S6_UPLOAD_PDF,
    (Phase.S5_PDF_OFFER, "decline"): Phase.S7_DONE,

    # Upload complete ends session
    (Phase.S6_UPLOAD_PDF, "complete"): Phase.S7_DONE,
}


def get_next_phase(current_phase: Phase, event: str) -> Phase:
    """Get the next phase based on current phase and event.
    
    Args:
        current_phase: Current state phase
        event: Event triggering the transition
        
    Returns:
        Next phase, or current phase if no valid transition
    """
    return TRANSITIONS.get((current_phase, event), current_phase)
