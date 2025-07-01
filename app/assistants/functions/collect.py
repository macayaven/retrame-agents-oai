"""collect_context – Assistant function that conducts ≤ 4-turn structured intake.

The goal is to capture **name**, **age**, and **reason for consulting** in at
most ``max_turns`` user messages (FR-1).  The function can operate in two
modes:

1. **Runtime** – OpenAI Assistants passes the current ``thread_id``; we fetch
   messages via the API.
2. **Unit-test** – A list of ``messages`` can be injected directly to avoid
   network calls.
"""

from __future__ import annotations

import re
from typing import Any

from app.assistants.client import get_openai_client
from app.callbacks.lang_detect import LangCallback

# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------

_NAME_RE = re.compile(r"\b(?:my name is|me llamo|i am|soy)\s+([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑñ'\- ]{1,40})",
                      re.IGNORECASE)

_AGE_RE = re.compile(r"\b(\d{1,3})\s*(?:years?\s*old|yo|años?)", re.IGNORECASE)

# A *very* broad crisis phrase detector (re-uses the same phrases as
# SafetyGuard but without ADK dependencies).

_CRISIS_PHRASES = [
    r"kill myself",
    r"end my life",
    r"suicide\s*(?:attempt|plan)?",
    r"self[-\s]?harm",
    r"me quiero suicidar",
    r"quiero quitarme la vida",
    r"no quiero vivir",
]

_CRISIS_RE = re.compile("|".join(_CRISIS_PHRASES), re.IGNORECASE)


# ---------------------------------------------------------------------------
# Public entry-point
# ---------------------------------------------------------------------------


async def collect_context(
    *,
    thread_id: str | None = None,
    messages: list[dict[str, Any]] | None = None,
    max_turns: int = 5,
) -> dict[str, Any]:
    """Return a JSON payload with ``goal_reached`` and ``intake_data`` keys.

    On success::

        {
            "goal_reached": true,
            "intake_data": {"name": "Alice", "age": 29, "reason": "…"},
            "lang": "en"
        }

    The function considers only the last *max_turns* user messages (default 5).
    If some fields are missing we return ``goal_reached: false`` together with
    the list of missing keys so the Assistant can keep asking.
    """

    # ---------------------------------------------------------------------
    # 1. Fetch messages if not supplied (runtime path)
    # ---------------------------------------------------------------------
    if messages is None:
        if thread_id is None:
            raise ValueError("Either `thread_id` or `messages` must be provided")

        client = get_openai_client()
        # We request in ascending order so the first element is the earliest.
        resp = await client.beta.threads.messages.list(thread_id, order="asc")
        messages = [m.model_dump() for m in resp.data]  # type: ignore[attr-defined]

    # Keep only *user* messages (role=="user") and trim to the last max_turns
    user_msgs = [m for m in messages if m.get("role") == "user"][-max_turns:]

    # Intake fields (see design.md §C)
    trigger_situation: str | None = None
    automatic_thought: str | None = None
    emotion_label: str | None = None
    emotion_intensity: int | None = None
    reason: str | None = None  # ≤35-word help-seek description

    # Optional demographic
    name: str | None = None
    age: int | None = None

    # ---------------------------------------------------------------------
    # 2. Extract fields from user messages (naïve regex heuristic)
    # ---------------------------------------------------------------------
    for msg in user_msgs:
        text = _normalise(msg)

        if name is None and (_m := _NAME_RE.search(text)):
            name = _m.group(1).strip().title()

        if age is None and (_a := _AGE_RE.search(text)):
            try:
                age_val = int(_a.group(1))
                if 5 <= age_val <= 120:
                    age = age_val
            except ValueError:
                pass

        # -----------------------------------------------------------------
        # 2.1 Detect *reason* – heuristic: first message with "because|ya que"
        # -----------------------------------------------------------------
        if reason is None and ("because" in text or "porque" in text or "ya que" in text):
            reason = text

        # -----------------------------------------------------------------
        # 2.2 Detect *trigger situation* – look for contextual markers: when/where
        # -----------------------------------------------------------------
        if trigger_situation is None and any(w in text for w in ["when", "where", "during", "en", "mientras"]):
            trigger_situation = msg.get("content", "").strip()

        # -----------------------------------------------------------------
        # 2.3 Detect *automatic thought* – quoted text or "i thought" …
        # -----------------------------------------------------------------
        if automatic_thought is None:
            # Ignore apostrophes used in contractions (e.g. I'm, don't) by
            # requiring the opening quote to *not* be immediately preceded by
            # an alphabetic character.
            if (
                _q := re.search(
                    # Corrected pattern: match opening straight/curly double or «, capture 3–120 chars until matching closing quote.
                    r'"([^\"]{3,120})"',
                    msg.get("content", ""),
                )
            ):
                automatic_thought = _q.group(1).strip()
            elif (_t := re.search(r"i (?:just )?(?:thought|think) (?:that )?([^\.]{3,120})", text)):
                automatic_thought = _t.group(1).strip()

        # -----------------------------------------------------------------
        # 2.4 Detect *emotion label + intensity* – e.g. "shame 8/10"
        # -----------------------------------------------------------------
        if emotion_label is None or emotion_intensity is None:
            if (_e := re.search(r"(sad|shame|guilt|anxiety|angry|fear|miedo|triste|verg[üu]enza)(?:[^0-9]{0,20})?(\d{1,2})(?:/10)?", text)):
                emotion_label = emotion_label or _e.group(1).strip()
                try:
                    val = int(_e.group(2))
                    if 0 <= val <= 10:
                        emotion_intensity = emotion_intensity or val
                except ValueError:
                    pass

    # Fallbacks ----------------------------------------------------------------

    # If reason missing, assume last user message expresses their help-seek motive
    if reason is None and user_msgs:
        reason = _normalise(user_msgs[-1])

    # If trigger_situation still None, use *first* message (contextual guess)
    if trigger_situation is None and user_msgs:
        trigger_situation = user_msgs[0].get("content", "").strip()

    # ---------------------------------------------------------------------
    # 3. Detect language + crisis phrases
    # ---------------------------------------------------------------------
    lang = LangCallback._detect_lang(" ".join(_normalise(m) for m in user_msgs))  # type: ignore

    crisis_detected = any(_CRISIS_RE.search(_normalise(m)) for m in user_msgs)

    # ---------------------------------------------------------------------
    # 4. Produce response
    # ---------------------------------------------------------------------
    missing: list[str] = []
    # Required fields per spec
    if trigger_situation is None:
        missing.append("trigger_situation")
    if automatic_thought is None:
        missing.append("automatic_thought")
    if emotion_label is None or emotion_intensity is None:
        missing.append("emotion_data")
    if reason is None:
        missing.append("reason")

    goal_reached = not missing

    payload: dict[str, Any] = {
        "goal_reached": goal_reached,
        "lang": lang,
        "crisis": crisis_detected,
    }

    if goal_reached:
        payload["intake_data"] = {
            "trigger_situation": trigger_situation,
            "automatic_thought": automatic_thought,
            "emotion_data": {"emotion": emotion_label, "intensity": emotion_intensity},
            "reason": reason,
            "name": name,
            "age": age,
        }
    else:
        payload["missing"] = missing

    return payload


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _normalise(msg: dict[str, Any] | str) -> str:
    """Return lowercase trimmed text from a message dict or string."""

    if isinstance(msg, str):
        return msg.strip().lower()

    text = msg.get("content") or ""
    if isinstance(text, list):  # OpenAI may return list of content parts
        text = " ".join(str(p) for p in text)
    return str(text).strip().lower()
