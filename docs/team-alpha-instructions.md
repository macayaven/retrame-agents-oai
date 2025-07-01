# Team α (Backend/AI) Instructions

## Mission
You are the Backend/AI Engineer responsible for implementing the core orchestrator logic and tests for the Reframe-APD MVP. Your work focuses on Python development, state management, and OpenAI integration.

## Timeline: 3-Hour Sprint (11:05 - 14:00)

### Your Tasks
All tasks are tracked as GitHub issues in [Project 5](https://github.com/users/macayaven/projects/5). Work through them in order:

1. **α-1** (2m): Create `feat/orchestrator-mvp` branch
2. **α-2** (10m): Implement state machine in `app/assistants/state.py`
3. **α-3** (5m): Scaffold `orchestrator_assistant.py`
4. **α-4** (10m): Define JSON schemas for 5 tools
5. **α-5** (20m): Implement `decide_next_action()` core logic
6. **α-6** (15m): Build offline stubs for testing
7. **α-7** (15m): Integrate OpenAI API calls
8. **α-8** (10m): Create CLI demo harness
9. **α-9** (12m): Write happy path unit tests
10. **α-10** (8m): Write crisis path unit tests
11. **α-11** (15m): Implement GCS upload tool **[WAIT FOR TEAM β AT 12:15]**
12. **α-12** (10m): Integrate PDF generation with GCS
13. **α-13** (5m): Update coverage badge

### Critical Handshake Point
**At 12:15**: Team β will provide GCS credentials via issue comment on α-11:
- Bucket name: `reframe-apd-pdf`
- Service account: `reframe-edge-sa`
- Project ID

### Technical Specifications

#### State Machine (α-2)
```python
from enum import Enum

class Phase(Enum):
    S0_START = "start"
    S1_INTAKE = "intake"
    S2_CRISIS_CHECK = "crisis_check"
    S3_ANALYST_QA = "analyst_qa"
    S4_REFRAME = "reframe"
    S5_PDF_OFFER = "pdf_offer"
    S6_UPLOAD_PDF = "upload_pdf"
    S7_DONE = "done"

TRANSITIONS = {
    (Phase.S0_START, "user_message"): Phase.S1_INTAKE,
    (Phase.S1_INTAKE, "complete"): Phase.S2_CRISIS_CHECK,
    (Phase.S2_CRISIS_CHECK, "safe"): Phase.S3_ANALYST_QA,
    (Phase.S2_CRISIS_CHECK, "crisis"): Phase.S7_DONE,
    # ... etc
}
```

#### Tool Schemas (α-4)
Define these 5 tools with proper JSON schemas:
1. `collect_context` - Extract name, age, reason from user input
2. `analyse_and_reframe` - Generate cognitive reframing
3. `generate_pdf` - Create PDF report
4. `gcs_upload` - Upload to Google Cloud Storage (renamed from supabase_upload)
5. `safe_complete` - Handle crisis situations

#### Quality Standards
- All code must pass: `poe fix` (ruff, black, mypy)
- Tests must achieve ≥70% coverage
- Use existing patterns from `app/assistants/functions/`
- Follow async patterns throughout

### Environment Setup
```bash
# Ensure you're in the backend directory
cd /Users/carlos/workspace/retrame-agents-oai

# Create and checkout feature branch
git checkout -b feat/orchestrator-mvp
git push -u origin feat/orchestrator-mvp

# Install dependencies
uv pip install -e .[dev]

# Run tests frequently
poe test-watch
```

### Testing Strategy
- Use `StubLLM` from `tests/unit/conftest.py` for deterministic tests
- Test all state transitions
- Ensure crisis detection works in both Spanish and English
- Mock external services (OpenAI, GCS) in unit tests

### Communication
- Update issue status as you progress
- Comment on blockers immediately
- At 12:15, check issue α-11 for GCS credentials
- Coordinate with Team β for final integration at 13:35

### Definition of Done
- All 13 tasks completed
- `pytest -q` shows 25/25 tests passing
- Coverage ≥70%
- `poe check` passes all quality gates
- Ready to merge into PR by 14:00

## Questions?
Contact the Project Manager immediately if you encounter any blockers or need clarification.

Good luck! 🚀