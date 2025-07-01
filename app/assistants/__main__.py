"""Minimal CLI driver that stitches the Assistant function tools together.

Usage (interactive demo)::

    python -m app.assistants  # then type user messages, end with EOF / blank line

The same orchestration logic is reusable by integration tests via
:func:`run_pipeline` so we avoid duplicating flow control.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any, Dict, List

from app.assistants.functions.analyse import analyse_and_reframe
from app.assistants.functions.collect import collect_context
from app.assistants.functions.escalate import escalate_crisis
from app.assistants.functions.pdf import generate_pdf

# Shared session state
from app.assistants.state import SessionState


async def run_pipeline(user_messages: List[str]) -> Dict[str, Any]:
    """Run the full collect → analyse → pdf pipeline synchronously.

    Parameters
    ----------
    user_messages
        List of raw user message strings in chronological order.
    """

    state = SessionState()
    # Simulate Intake phase: we already have final user messages, so we store transcript.
    state.transcript = [{"role": "user", "content": m} for m in user_messages]

    # 1. Parser agent – build intake_json from transcript
    parser_out = await collect_context(messages=state.transcript)

    if parser_out.get("crisis"):
        return escalate_crisis()

    if not parser_out.get("goal_reached"):
        missing = ", ".join(parser_out.get("missing", []))
        raise RuntimeError(f"Missing required intake fields: {missing}")

    state.intake_json = parser_out["intake_data"]

    # 2. Reframe agent – generate therapeutic assessment
    analysis = await analyse_and_reframe(state.intake_json)  # type: ignore[arg-type]

    if analysis.get("crisis"):
        return escalate_crisis()

    state.reframe_json = analysis

    # 3. PDF generation
    pdf_payload = {
        "intake_data": state.intake_json,
        "analysis_output": json.dumps(state.reframe_json, ensure_ascii=False),
    }
    pdf_out = generate_pdf(pdf_payload)

    return {"pdf_url": pdf_out["pdf_url"], "analysis": analysis}


# ---------------------------------------------------------------------------
# CLI helper
# ---------------------------------------------------------------------------


def _parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Reframe-APD Assistants demo")
    parser.add_argument(
        "--messages",
        nargs="*",
        help="User messages passed as arguments; if omitted, read from stdin",
    )
    return parser.parse_args(argv)


async def _main(argv: List[str]) -> None:  # pragma: no cover – CLI entry
    args = _parse_args(argv)
    if args.messages:
        user_msgs = args.messages
    else:
        print("Enter user messages (end with empty line):", file=sys.stderr)
        user_msgs = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if not line.strip():
                break
            user_msgs.append(line)

    result = await run_pipeline(user_msgs)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(_main(sys.argv[1:])) 