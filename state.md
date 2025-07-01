# State – Reframe-APD Migration

| Date | Milestone | % Complete | Notes |
|------|-----------|------------|-------|
| 2025-07-01 | Legacy ADK code removed, Assistants scaffolding + unit tests added | 35 % | Core migration skeleton in place; test suite adjusted |
| 2025-07-01 | v0.3 prompts integrated; shared SessionState + full pipeline refactor; tests green | 60 % | 21 unit/integration tests pass; PDF generation restored |

---

## Technical Progress

- design.md & implementation.md drafted.
- New Assistants package scaffolded (`app/assistants/*`).
- Legacy ADK agents, tools, and tests deleted.
- Unit tests for new stub functions passing locally.
- **SessionState** dataclass introduced to coordinate agent hand-offs.
- `collect_context`, `analyse_and_reframe`, `generate_pdf` wired into a synchronous `run_pipeline`.
- **v0.3** Intake / Parser / Reframe prompts fetched via Langfuse pre-fetch; prompts stored under `/tmp/reframe_prompts`.
- Regex extraction in `collect_context` updated (straight quotes only).
- 21 unit & integration tests green (`pytest -q`).
- CLI demo (`python -m app.assistants --messages …`) produces PDF end-to-end.

## Constraints & Requirements

- ≤ 5-turn Intake; ≤ 5-turn Analyst follow-up.
- Crisis detection must interrupt flow and return safe-completion.
- Spanish & English locality; default crisis hotline 🇪🇸 (024).
- PDF must be deliverable via Supabase Storage (env: `SUPABASE_URL`, `SUPABASE_KEY`).
- Offline&nbsp;stub path keeps tests deterministic – no network in CI.
- Maintain ≥ 90 % unit coverage; lint/format clean (ruff, black).
- Deployment target: Cloud Run; container image ≤ 1 GB; cold-start < 5 s.

## Open Risks

| ID | Risk | Mitigation |
|----|------|-----------|
| R-1 | Marketplace policy rejects mental-health content | Align safe-completion & disclaimer wording; follow OpenAI content rules |
| R-2 | Conversational orchestrator not yet implemented | Design state-machine; test with Assistants sandbox |
| R-3 | Front-end integration path undefined | Define JSON contract & websocket streaming |
| R-4 | Cloud-run cold-start vs. PDF generation latency | Investigate concurrent PDF workers / caching |
| R-5 | API key & Langfuse env-vars in CI | Use dummy vars; secrets manager in prod |

## Next Steps

1. Draft orchestrator design (Assistant system prompt + tool schema).
2. Implement interactive state-machine CLI (`demo_cli.py`) mirroring production dialogue.
3. Expose tools in an Assistant via OpenAI management script.
4. Define FE contract (likely websocket stream events: `phase`, `payload`).
5. Create Dockerfile & Cloud Run deploy workflow; test staging env.
6. Inject real Langfuse env-vars; remove fallback prompt defaults.
7. Extend tests to cover conversational flow & PDF opt-in/out. 