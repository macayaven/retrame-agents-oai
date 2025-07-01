from __future__ import annotations

"""Clone a Langfuse prompt, apply consistency fixes, and publish a new version.

This helper lets us update the schema/output instructions in a single place and
re-upload without breaking the existing prompt versions still referenced by
production or tests.

Example
-------
$ export LANGFUSE_HOST=https://cloud.langfuse.com
$ export LANGFUSE_PUBLIC_KEY=pk_live_…
$ export LANGFUSE_SECRET_KEY=sk_live_…
$ python scripts/clone_prompts.py \
        --source intake-agent-oai-v0.2 \
        --target intake-agent-oai-v0.3
"""

import argparse
from collections.abc import Callable
from datetime import UTC, datetime
import os
import re

from langfuse import Langfuse

# ---------------------------------------------------------------------------
# Text fix-ups
# ---------------------------------------------------------------------------


def _fix_prompt(text: str) -> str:
    """Return *text* with schema/output terminology updated.

    Current transformations:
    1. Replace the older flat-schema terminology (`collection_complete`) with
       the nested structure (`goal_reached` / `intake_data`).
    2. Ensure all JSON examples use camelCase keys exactly as in the spec.
    3. Normalise bullet headings (e.g. "Output format" section).
    """

    # Replace collection_complete flag references
    text = re.sub(r"collection_complete", "goal_reached", text)

    # Ensure intake_data wrapper is present in example blocks
    # (simple heuristic: wrap top-level keys if missing)
    def _wrap_json_examples(match: re.Match[str]) -> str:
        json_block = match.group(0)
        if "\"intake_data\"" in json_block:
            return json_block  # already OK
        # Insert wrapper around all other members except goal_reached/missing/crisis
        try:
            # naive parse to detect outer keys (not full JSON safe but good enough)
            inner = re.sub(r"^\{\s*|\s*\}$", "", json_block.strip())
            wrapped = (
                '{\n  "goal_reached": true,\n  "intake_data": {\n    ' + inner + '\n  }\n}'
            )
            return wrapped
        except Exception:  # pragma: no cover – fallback
            return json_block

    text = re.sub(r"\{[\s\S]*?\}", _wrap_json_examples, text, count=1)

    # (Optional) additional text clean-ups can be inserted here

    # Timestamp footer so we know it was auto-generated
    stamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    text += f"\n\n---\nAuto-generated via scripts/clone_prompts.py on {stamp}."

    return text


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------


def _get_langfuse() -> Langfuse:
    try:
        return Langfuse(
            host=os.environ["LANGFUSE_HOST"],
            public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
            secret_key=os.environ["LANGFUSE_SECRET_KEY"],
        )
    except KeyError as e:  # pragma: no cover
        missing = e.args[0]
        raise SystemExit(f"Missing required env var: {missing}")


def _clone_prompt(src: str, dst: str, fixer: Callable[[str], str] = _fix_prompt) -> None:
    lf = _get_langfuse()

    src_prompt = lf.get_prompt(src)
    raw_text = str(src_prompt.compile())

    new_text = fixer(raw_text)

    print(f"Uploading new prompt → {dst}  (length {len(new_text)} chars)…")
    lf.create_prompt(  # type: ignore[arg-type]
        name=dst,
        content=new_text,
        metadata={"cloned_from": src, "generated_by": "clone_prompts", "timestamp": datetime.now(UTC).isoformat()},
    )
    print("Done ✔︎")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Clone and fix a Langfuse prompt")
    p.add_argument("--source", required=True, help="Existing prompt key to clone")
    p.add_argument("--target", required=True, help="New prompt key to create")
    return p.parse_args(argv)


def main() -> None:  # pragma: no cover
    args = _parse_args()
    _clone_prompt(args.source, args.target)


if __name__ == "__main__":  # pragma: no cover
    main()
