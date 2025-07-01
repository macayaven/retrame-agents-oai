Below is a self‑contained roadmap that you can hand to any senior engineer (or follow yourself) and keep the migration moving without stalls.  It is broken into five sections: (1) Target Architecture, (2) Orchestrator Design, (3) Front‑End/Back‑End Contract, (4) Implementation Work‑Plan (Gantt‑style narrative), and (5) Risk & Quality Gates. Nothing here depends on seeing the private repos, so you can start immediately; where code review is required I note the exact files or snippets I will need you to paste or share.

⸻

1. Target Architecture — 50 k‑ft view

┌──────────────┐   1  WebSocket/SSE stream       ┌────────────────┐
│   Front‑end  │◀───────────────────────────────▶│  FastAPI Edge   │
│  (re‑frame)  │   JSON events & binary PDF      │  (Cloud Run)    │
└──────────────┘                                └─▲───────────────┘
                                                  │2 REST/tool call
                             ┌────────────────────┴──────────────┐
  Supabase Storage <────────▶   Orchestrator Assistant (OAI)     │
   (signed URLs)             │  – statemachine & function tools  │
                             └────▲──────────────┬───────────────┘
                                  │3 invoke     │4 safe‑complete
                                  │             │
                     ┌────────────┴──────┐ ┌────┴─────────────┐
                     │Python tool:       │ │Python tool:      │
                     │analyse_reframe.py │ │generate_pdf.py   │
                     └───────────────────┘ └──────────────────┘

	•	Edge = your thin FastAPI server. It validates the socket, relays user messages to the Assistant, streams back assistant_response events, and can serve PDFs directly from Supabase via presigned public URLs.
	•	Assistant = OpenAI “function‑calling” assistant that owns the conversational workflow but delegates heavy work to your local python tools (already wired in CI).
	•	Tools = pure‑python, deterministic, network‑free implementations that satisfy CI and run identically in prod.

⸻

2. Orchestrator Design

2.1  State Machine (SessionState)

State	Entry Trigger	Exit Condition	Tool Invoked	Notes
S0: START	socket init event	first user message	—	Assign session_id (UUIDv7).
S1: INTAKE	user message	≤ 5 user turns or crisis detected	collect_context	Persist raw text + extracted slots.
S2: CRISIS_CHECK	after each assistant turn	crisis regex / model flag	safe_complete tool (no pdf)	Returns hotline 024 for 🇪🇸; 988 for 🇺🇸.
S3: ANALYST_QA	Intake done & no crisis	≤ 5 analyst turns	—	Use v0.3 Analyst prompt.
S4: REFRAME	analyst satisfied	reframe drafted	analyse_and_reframe	Generates structured {"frames": [...], "summary": ""}.
S5: PDF_OFFER	reframe ready	user says yes	generate_pdf	If no, skip to DONE.
S6: UPLOAD_PDF	pdf bytes ready	upload URL returned	supabase_upload	Returns public_url.
S7: DONE	any terminal path	—	—	Emit complete event.

All transitions happen inside the Assistant’s system prompt via short JSON replies.
If any unexpected error occurs, jump to S7 with error=true flag and explanatory message.

2.2  Assistant configuration

{
  "name": "reframe_apd_orchestrator",
  "model": "gpt-4o-mini",
  "tools": [
    { "name": "collect_context", "parameters": { "type": "object", "properties": { "text": {"type": "string"}}, "required": ["text"]}},
    { "name": "analyse_and_reframe", ... },
    { "name": "generate_pdf", ... },
    { "name": "supabase_upload", ... },
    { "name": "safe_complete", ... }
  ],
  "temperature": 0.3,
  "system_prompt": "<SEE BELOW>"
}

System Prompt (sketch)

You are the orchestrator for Re‑frame‑APD, a mental‑health self‑help assistant.
Follow this deterministic state machine:
<S0‑S7 table embedded here>.
Use Spanish or English according to the user.
Crisis detection: if user intent suggests self‑harm, call safe_complete immediately.
...
Emit all actions as JSON:
{ "state": "Sx", "thought": "...", "tool": "collect_context", "arguments": { ... } }

Keep the prompt in repo (app/assistants/prompts/orchestrator.txt) and load it at runtime; tests use the stub.

2.3  Crisis safe‑completion
	•	Maintains compliance and tackles Risk R‑1.
	•	Returns hotline list object:

{ "hotline": {"es": "024", "en": "988"}, "message": "...", "pdf_generated": false }



⸻

3. Back‑End ↔︎ Front‑End Contract

Event	Direction	Payload shape	When
init	FE → BE	{lang, anonymous, user_agent}	On socket open
user_msg	FE → BE	{id, text}	Each user message
assistant_stream	BE → FE	{id, delta, phase}	Token streaming (SSE / ws)
phase_change	BE → FE	{from, to}	On state transition
pdf_ready	BE → FE	{url}	When Supabase upload done
complete	BE → FE	{status}	Terminal

Binary PDF transfer: the BE never sends raw bytes; it only returns the presigned URL from Supabase.

Front‑end repo integration steps:
	1.	Expose env vars in Vite/Next config:
VITE_API_URL, VITE_EVENT_STREAM_URL, VITE_PROJECT_NAME.
	2.	Socket wrapper at src/lib/socket.ts implements the table above.
	3.	Phase visual components in src/components/phases/*.

⸻

4. Implementation Plan (chronological)

Phase 0 — Access & Bootstrap (½ day)

Task	Owner	Artifact
Share GitHub read‑only token or add me/chatGPT as collaborator	You	—
Clone both repos into mono‑worktree (repo‑root/frontend, backend)	Dev	local

Phase 1 — Orchestrator MVP (3 days)
	1.	Write state.py – pure‑python enum + transition table.
	2.	Implement orchestrator_assistant.py
Functions: next_action(session: SessionState, user_event) -> AssistantMessage.
	3.	CLI harness (demo_cli.py) using readline for manual testing.
	4.	Unit tests: parametrize all happy paths + crisis path (pytest, 90 %+).
	5.	Refactor existing tools to match new JSON schema.

Phase 2 — Edge FastAPI (2 days)
	1.	Endpoint POST /chat/{session_id} for initial socket upgrade.
	2.	WebSocket loop:
	•	read FE events → post to Assistant via openai.beta.threads.messages.create.
	•	stream delta tokens back (ServerSentEvents mod or raw ws JSON).
	3.	Middleware for offline stub mode activated when OFFLINE=1 (CI).

Phase 3 — Front‑End Wiring (2 days concurrent)
	1.	Add useConversation() React hook using socket wrapper.
	2.	Progress bar component keyed to phase_change.
	3.	PDF download chip once pdf_ready.

Phase 4 — DevOps & Perf (2 days)
	1.	Dockerfile (multi‑stage, python‑slim, pip‑cache‑trimmer).
Target: < 250 MB compressed.
	2.	Gunicorn + Uvicorn workers; benchmark cold‑start locally (hyperfine).
	3.	Cloud Run deploy (gcloud run deploy --source .) staging trigger.

Phase 5 — Observability & Langfuse (1 day)
	•	Wrap every phase exit in langfuse.track() with tags phase=Sx, session_id, user_id?.

Phase 6 — Test Matrix & Docs (1 day)
	•	Integration tests hitting /chat with prerecorded user scripts.
	•	Update README.md and design.md diagrams.
	•	Coverage badge gate (fails if < 90 %).

Total ~11 calendar days assuming 1 engineer; parallelisation can cut to 7‑8.

⸻

5. Risk Register Alignment & Quality Gates

Risk	Plan item addressing it	Acceptance criterion
R‑1 Policy reject	Crisis flow, disclaimers hard‑coded	Moderation dry‑run passes
R‑2 Orchestrator TBD	Phases 0‑1 deliver tested statemachine	All tests green
R‑3 FE undefined	Contract table & Phase 3 tasks	End‑to‑end demo video
R‑4 Cold‑start	Phase 4 multi‑stage build + async PDF worker	≤ 5 s p95 startup
R‑5 Secrets in CI	.env.example + GitHub OIDC secrets	No clear‑text keys on GH

Quality gates in CI: ruff + black → mypy → pytest → coverage → docker‑build‑size.

⸻

How to give me access

If you’d like me to inspect or generate code directly:
	1.	Preferred: Add my GitHub handle macayaven‑chatgpt as Reporter in both private repos.
	2.	Alternative: Paste critical files (≤ 200 lines each) here and I’ll annotate.

Once access is set, I can supply diff‑ready PRs or patch files.

⸻

Immediate Next Action for You
	1.	Decide on access method and share token/invite. (nor token, nor invite)
	2.	Confirm or tweak the state‑machine table (especially crisis wording).
	3.	Assign owners/dates to Phase 1 tasks and kick‑off.

I’ll be ready to review code, generate skeletons, or refine any piece of this plan as you progress.