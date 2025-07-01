# Implementation Plan – Reframe-APD Assistants API Migration

_This document refines the **High-Level Design** into concrete steps, interfaces and tasks. Once all check-boxes are ticked the migration is considered code-complete._

---

## 1. Repository Additions

- `[x]` `app/assistants/__init__.py`
- `[x]` `app/assistants/client.py` – thin OpenAI wrapper (lazy-init `openai.AsyncClient`).
- `[ ]` `app/assistants/functions/collect.py`
- `[ ]` `app/assistants/functions/analyse.py`
- `[ ]` `app/assistants/functions/pdf.py`
- `[ ]` `app/assistants/functions/escalate.py`
- `[ ]` `app/assistants/__main__.py` – CLI helper for local runs.
- `[ ]` `tests/unit/test_collect_function.py`
- `[ ]` `tests/unit/test_analyse_function.py`
- `[ ]` `tests/unit/test_pdf_function.py`
- `[ ]` `tests/unit/test_escalate_function.py`
- `[ ]` `tests/integration/test_full_marketplace_flow.py`

---

## 2. Detailed Steps

### 2.1 Dependency Updates

1. Add `openai>=1.14.0` to **pyproject.toml**.
2. Pin `pytest-asyncio` for async unit tests.

### 2.2 Environment Variables (supersets)

| Variable | Purpose | Required |
|----------|---------|----------|
| `OPENAI_API_KEY` | Auth for Assistants API | ✅ |
| `OPENAI_ASSISTANT_ID` | Production Assistant ID (overrides local build) | 🚫 (auto-provision if absent) |
| `SUPABASE_URL` / `SUPABASE_KEY` | PDF hosting | ✅ |

### 2.3 Helper: `app/assistants/client.py`

```python
from functools import lru_cache
import os
from openai import AsyncOpenAI

@lru_cache(maxsize=1)
def get_openai_client() -> AsyncOpenAI:
    api_key = os.environ["OPENAI_API_KEY"]
    return AsyncOpenAI(api_key=api_key)
```

### 2.4 Function – collect_context

*File*: `app/assistants/functions/collect.py`

```python
from openai.types.beta.threads import Message
from app.callbacks import lang_detect, safety_filters, transcript_acc

MAX_TURNS = 4

async def collect_context(thread_id: str, client=None):
    client = client or get_openai_client()
    # executed via function-tool; thread is provided by Assistants runtime
    messages: list[Message] = await client.beta.threads.messages.list(thread_id)
    # apply before-callbacks to last user message
    ...
    # if goal reached → return dict
    return {"goal_reached": True, "intake_data": {...}}
```

Key points:
- The function receives `thread_id` (Assistants passes current thread automatically).
- We iterate last messages to harvest data; if not enough, raise `NeedsMoreInteraction` (custom error) so the Assistant continues asking.
- Once goal reached, we persist into `metadata['intake_data']` and return JSON.

### 2.5 Function – analyse_and_reframe

*File*: `app/assistants/functions/analyse.py`

- Input: `{ "intake_json": { ... } }`
- Uses `gpt-4o` completion with system prompt (port existing Gemini prompt).
- Detects cognitive distortions (list of codes), balanced thought, micro-action, certainty shift.
- On crisis cue returns `{ "crisis": true }`.
- Persists to `metadata['analysis']`.

### 2.6 Function – generate_pdf

Re-use existing `build_pdf_bytes` then upload to Supabase Storage (via existing helper). Returns public URL.

### 2.7 Function – escalate_crisis

Returns safe completion Spanish/English crisis message.

---

## 3. Test Strategy

| Layer | Focus | Framework |
|-------|-------|-----------|
| Unit | Each function toolkit – deterministic outputs given faked client | `pytest`, `pytest-asyncio`, `httpx_mock` |
| Integration | End-to-end thread simulation via OpenAI test-double | `vcrpy` cassettes |

Coverage gates remain in *pyproject.toml*.

---

## 4. Migration Checklist

- [ ] All new unit tests passing ✅
- [ ] Integration happy path ✅
- [ ] Old ADK path removed / flagged deprecated
- [ ] CI coverage ≥ 90 % / 80 %
- [ ] README updated with new run instructions
- [ ] Marketplace review checklist satisfied

---

*Last updated*: 1 Jul 2025 