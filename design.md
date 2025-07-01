# Reframe-APD Migration – High-Level Design

> **Goal** Migrate the existing Google ADK 0.8 pipeline to the **OpenAI Assistants API** (o4-series) while preserving 100 % functional parity and test coverage.

---

## 1 Context

The current implementation uses a chain of ADK `LoopAgent`/`ToolAgent` classes orchestrated by a `SequentialAgent`. Google-hosted models (Gemini 1.5 Pro/Flash) are called under the hood. We want to publish the therapy assistant on the GPT Marketplace, which requires running purely on the OpenAI Assistants API.

---

## 2 Target Architecture (Assistants API)

One **Assistant** registered on the marketplace with four function tools:

| Function Name | Purpose | Back-end Model |
| ------------- | ------- | -------------- |
| `collect_context()` | Conduct ≤ 4-turn structured intake | `gpt-4o-mini` |
| `analyse_and_reframe(json)` | Parse JSON → detect distortions, craft balanced thought & 10-min micro-action | `gpt-4o` |
| `generate_pdf(session_dict)` | Build final PDF using existing ReportLab logic | No model (server-side execution) |
| `escalate_crisis(msg)` | Immediate safe completion with crisis message | `o3` (deterministic)

### Flow

1. Request hits safety guard & language detector (executed server-side, *before* Assistant).
2. Chat passes to `collect_context` tool until `{goal_reached: true}` returned.
3. Assistant calls `analyse_and_reframe` with conversation JSON.
4. If self-harm cue found → Assistant calls `escalate_crisis` and session ends.
5. Otherwise Assistant calls `generate_pdf`; link returned to user; session closed.

---

## 3 Codebase Mapping

| ADK Component | Replacement | File |
| ------------- | ----------- | ---- |
| `collect_loop` + `collector_llm` | `collect_context` function | `app/assistants/functions/collect.py` |
| `JsonParser` + `AnalystLLM` + `analysis_loop` | `analyse_and_reframe` | `app/assistants/functions/analyse.py` |
| `PdfAgent` | `generate_pdf` | `app/assistants/functions/pdf.py` |
| `SafetyGuard` | `safety_filters.safe_guard()` | `app/callbacks/safety_filters.py` (re-used) |
| `LangCallback` | `lang_detect.detect_lang()` | `app/callbacks/lang_detect.py` (re-used) |
| `TranscriptAccumulator` | Re-used as middleware for logging | `app/callbacks/transcript_acc.py` |

The legacy ADK agents remain until all tests are ported; new code lives under `app/assistants/`.

---

## 4 Assumptions & Decisions

1. **Assistant Metadata**: Spanish + English locale; public name "Reframe-APD CBT Coach".
2. **Model Selection**: `gpt-4o-mini` for collection (cost vs. latency), `gpt-4o` for cognitive analysis.
3. **Session State**: Stored in `assistant.thread.metadata` as JSON (mirrors previous `state`).
4. **PDF Hosting**: Still Supabase Storage; credentials via `SUPABASE_URL` / `SUPABASE_KEY` env vars.
5. **Safety**: Crisis phrases detected both by `SafetyGuard` middleware **and** model output guardrails.
6. **Testing**: Maintain ≥ 90 % unit coverage; new tests use `pytest-asyncio` and OpenAI test-double stubs.

---

## 5 Open Risks

| ID | Risk | Mitigation |
|----|------|-----------|
| R-1 | Marketplace policy rejects mental-health content | Align safe-completion flow + disclaimers |
| R-2 | Higher latency vs. Gemini-Flash | Use streaming + mini model for intake |
| R-3 | Cost overruns | Tool functions minimise model turns; caching web search |
| R-4 | Supabase outage | Graceful fallback: return PDF bytes inline |

---

*Document version*: v0.1 • 1 Jul 2025 