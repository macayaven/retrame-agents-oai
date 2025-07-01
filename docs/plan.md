Below is a work‑breakdown structure (WBS) that dissects the three‑hour MVP sprint into 30 atomic tasks.
They are grouped into two parallel streams—Stream α (Core Logic) and Stream β (Platform & UX)—so two small teams can work side‑by‑side without blocking each other.

⸻

⎯⎯ Stream α – Core Logic & Tests (Python)

Lead: Backend/AI team

ID	Task	Inputs / Prereq	Definition of Done (DoD)	Est.
α‑1	Create feat/orchestrator-mvp branch	none	Branch pushed to origin	2 m
α‑2	Add app/assistants/state.py with Phase enum + TRANSITIONS dict	design doc	Unit test test_state.py asserts all intended transitions	10 m
α‑3	Scaffold orchestrator_assistant.py (class shell, no logic yet)	α‑1	File imports, passes python -m pip check	5 m
α‑4	Write JSON tool‑schemas for 5 tools in orchestrator_assistant.py	design	pytest tests/schema/test_tools.py validates JSONSchema	10 m
α‑5	Implement decide_next_action(session, user_msg) core function	α‑2, α‑4	Doctest in file passes; returns dict with "phase" & "tool" fields	20 m
α‑6	Build offline stubs for the 5 tools (return deterministic values)	α‑4	OFFLINE=1 pytest tests/tools/test_stubs.py green	15 m
α‑7	Integrate OpenAI calls (real path; behind OFFLINE flag)	α‑5	Manual call to demo_cli.py streams tokens	15 m
α‑8	Create demo_cli.py REPL harness	α‑5	Running python -m app.assistants.demo_cli prompts and exits clean	10 m
α‑9	Unit tests – happy path	α‑6	3 tests green, cover phases S0‒S7, ≥ 95 % branch cov in file	12 m
α‑10	Unit tests – crisis path	α‑6	Crisis keyword triggers safe_complete; assert hotline text	8 m
α‑11	Implement gcs_upload() tool (real)	bucket info from β‑3	python -m app.tools.gcs_upload --help works; test uploads 1 KB file	15 m
α‑12	Refactor generate_pdf to call gcs_upload when OFFLINE=0	α‑11	Integration test produces signed URL matching regex ^https?://.*googleapis.com/	10 m
α‑13	Update coverage badge script	α‑9, α‑10	CI passes with ≥ 90 % overall	5 m
α‑Σ	Stream α finish	—	pytest -q 25/25 tests, ruff, black, mypy all clean	2 h 7 m


⸻

⎯⎯ Stream β – Platform, Infra & UX (DevOps + Front‑End)

Lead: DevOps/FE team

ID	Task	Inputs / Prereq	Definition of Done (DoD)	Est.
β‑1	Pull latest code & switch to feat/orchestrator-mvp	none	Local up‑to‑date; no merge conflicts	2 m
β‑2	Create GCS bucket reframe-apd-pdf (eu‑west1)	gcloud CLI	gsutil ls shows bucket; lifecycle default = Standard	5 m
β‑3	Create service account reframe-edge-sa & grant objectCreator	β‑2	gcloud iam service-accounts list displays SA; policy binding verified	5 m
β‑4	Store SA key in Secret Manager (local JSON kept out of repo)	β‑3	gcloud secrets versions access latest --secret edge-sa dumps key	3 m
β‑5	Add bucket & SA vars to app/settings.py and .env.example	β‑3	Values appear in diff; no hard‑coded secrets	4 m
β‑6	Patch backend/app/main.py: add /chat/{session_id} ws route	design	Locally uvicorn app.main:app --reload; websocket handshake 101 ok	15 m
β‑7	Swap Supabase client → google-cloud-storage in PDF service	β‑5	pytest tests/services/test_pdf.py passes (stubbed)	10 m
β‑8	Build multi‑stage Dockerfile (distroless run stage)	β‑5	`docker images	grep reframe-edge` size < 220 MB
β‑9	Local container smoke: curl localhost:8000/health returns 200	β‑8	Healthcheck responds in container	3 m
β‑10	Cloud Build push to Artifact Registry	β‑8	Image …/edge:<sha> visible in console	7 m
β‑11	Cloud Run deploy (reframe-edge) with SA	β‑10	gcloud run services describe status ACTIVE, URL copied	8 m
β‑12	Update frontend .env.local VITE_API_URL with Cloud‑Run URL	β‑11	pnpm dev uses prod edge; CORS check passes	4 m
β‑13	Update lib/socket.ts event map (phase_change, pdf_ready)	design	Front‑end compiles; ESLint clean	12 m
β‑14	Add PdfChip.tsx that appears when pdf_ready event fires	β‑13	Manual UX: clicking chip downloads a dummy PDF (OFFLINE mode)	10 m
β‑15	Commit PR template & GitHub workflow badge	none	CI triggers on push, shows pending	3 m
β‑Σ	Stream β finish	—	Cloud‑Run reachable, FE streams chat, dummy PDF downloads	1 h 51 m

Parallel overlap: α‑11 depends on β‑3, but everything before that is independent, so both teams work simultaneously for nearly two hours before the single hand‑off.

⸻

➊➋ Cross‑stream Integration “Handshake” (5 min)
	•	When β‑3 completes, post bucket & SA names in Slack.
	•	α‑team plugs values into env, runs α‑11/α‑12.
No other blockages.

⸻

Final Hardening & PR (both teams, 15 min)

Who	Task	DoD
α + β	Merge backend & FE hooks, run make ci locally	All linters/tests green
β	gcloud run deploy one final time with image that includes α‑code	SHA in Slack
α	Smoke test via demo front‑end; PDF signed URL downloads real file	“✅ MVP live” message
β	Open PR titled feat: orchestrator MVP (backend+infra+FE)	CI green, one reviewer assigned


⸻

How to run truly in parallel

Timeline	Stream α	Stream β
11:05‑11:45	α‑1 → α‑8 (logic scaffolds)	β‑1 → β‑7 (infra & route)
11:45‑12:15	α‑9 α‑10 (tests)	β‑8 β‑9 (Docker)
12:15	β‑team sends bucket & SA vars	
12:15‑12:45	α‑11 α‑12 (GCS upload)	β‑10 β‑11 (Cloud Run)
12:45‑13:15	α‑13 (coverage)	β‑12 β‑13 (FE socket)
13:15‑13:35	α‑14 manual smoke	β‑14 UX chip
13:35‑14:00	Joint hardening & PR	Joint hardening & PR

Both teams clock off inside the 3‑hour window with a clean, running MVP.

⸻

Quick reference of Task IDs per deliverable

Deliverable	Task IDs
state.py & transitions	α‑2
orchestrator_assistant.py logic	α‑4 → α‑7
Offline & real tools	α‑6, α‑11
Tests (25 total)	α‑9, α‑10
FastAPI WS route	β‑6
GCS bucket + SA	β‑2, β‑3
Docker + Cloud Run	β‑8 → β‑11
Front‑end socket & PDF UI	β‑13, β‑14


⸻

“Definition of Done” cheat‑sheet
	•	Code quality: ruff, black, mypy show 0 errors.
	•	Tests: pytest -q all green, coverage ≥ 90 %.
	•	Security: no secrets committed; bucket & SA in Secret Manager.
	•	Performance: Image < 220 MB; Cloud Run cold‑start < 5 s (manual curl).
	•	UX: Front‑end streams phases; clicking “Download PDF” downloads a valid file.
	•	Docs/CI: PR template present, CI passes automatically on PR.

With this WBS each small task has a crisp DoD, minimal cross‑team blocking, and clear checkpoints to know you’re still on schedule.