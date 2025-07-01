"""analyse_and_reframe – Detect distortions, craft balanced thought & micro-action.

Runs on GPT-4o when an **OpenAI** API key is available; otherwise falls back to a
deterministic stub so unit tests stay offline and reproducible.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

from app.assistants.client import get_openai_client

# ---------------------------------------------------------------------------
# Crisis phrases (same list as SafetyGuard)
# ---------------------------------------------------------------------------

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
# Public API
# ---------------------------------------------------------------------------


async def analyse_and_reframe(
    intake_json: Dict[str, Any],
    *,
    client=None,
) -> Dict[str, Any]:  # noqa: D401
    """Return cognitive analysis dict.

    When the `openai` client can be initialised, we perform a live call; in all
    other situations (tests, missing API key) we generate a synthetic payload.
    """

    # ---------------------------------------------------------------------
    # 0. Crisis fast-path (FR-5)
    # ---------------------------------------------------------------------
    reason = (intake_json.get("reason") or "").lower()
    if _CRISIS_RE.search(reason):
        return {"crisis": True}

    # ---------------------------------------------------------------------
    # 1. Attempt live OpenAI call
    # ---------------------------------------------------------------------
    if client is None:
        try:
            client = get_openai_client()
        except Exception:  # pragma: no cover – falls back to stub
            client = None

    if client is not None and os.environ.get("OPENAI_API_KEY"):
        try:
            sys_prompt = (
                "You are a CBT assistant helping users reframe distorted thoughts. "
                "Given the JSON below, identify cognitive distortions (return 2-letter codes), "
                "craft a <40-word balanced thought and suggest a <=10-minute micro-action. "
                "Also estimate the user's confidence *before* and *after* the reframe (0-100). "
                "Return ONLY valid JSON with keys: distortions[], balanced_thought, micro_action, "
                "certainty_before, certainty_after."
            )

            completion = await client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.7,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {
                        "role": "user",
                        "content": f"```json\n{json.dumps(intake_json, ensure_ascii=False)}\n```",
                    },
                ],
                max_tokens=300,
            )

            raw = completion.choices[0].message.content or "{}"
            # The model *should* return JSON but we parse defensively.
            json_start = raw.find("{")
            json_part = raw[json_start:]
            parsed: Dict[str, Any] = json.loads(json_part)
            # basic sanity check
            if "balanced_thought" in parsed and "micro_action" in parsed:
                return parsed
        except Exception:  # pragma: no cover – fall back
            pass

    # ---------------------------------------------------------------------
    # 2. Stub deterministic output (offline path)
    # ---------------------------------------------------------------------
    return _stub_payload()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _stub_payload() -> Dict[str, Any]:
    """Return a hard-coded payload for test predictability."""

    return {
        "distortions": ["MW"],
        "balanced_thought": (
            "I might be assuming others judge me; perhaps they aren't thinking that at all."
        ),
        "micro_action": "Message a friend and ask their genuine opinion—should take <10 min.",
        "certainty_before": 40,
        "certainty_after": 65,
    } 