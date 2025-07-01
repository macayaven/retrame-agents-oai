# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a cognitive reframing support tool for Avoidant Personality Disorder (AvPD) migrating from Google ADK to OpenAI Assistants API. The system collects user information through structured intake, analyzes cognitive distortions, and generates PDF reports.

## Development Commands

### Package Management
This project uses `uv` as the package manager.

### Essential Commands
```bash
# Install dependencies
uv pip install -e .[dev]

# Run the assistant CLI demo
python -m app.assistants --messages "Hola, necesito ayuda" "Me llamo Ana y tengo 32 años"

# Development servers
poe web    # ADK web interface
poe cli    # ADK CLI
poe api    # API server

# Testing
poe test              # Run all tests
poe test-unit         # Unit tests only
poe test-integration  # Integration tests only
poe test-watch        # Watch mode
poe test-cov          # With coverage

# Run specific test
pytest tests/unit/test_assistant_functions.py::test_collect_context_basic

# Code quality (run before committing)
poe fix    # Auto-fix formatting and linting
poe check  # Run all CI checks (lint, format, type-check, test)

# Individual quality commands
poe lint          # Run linter
poe lint-fix      # Fix linting issues
poe format        # Format code
poe type-check    # Type checking
```

## Architecture & Key Patterns

### Pipeline Flow
1. **Intake** (`collect.py`): Structured conversation to gather name, age, and reason (≤5 turns)
2. **Analysis** (`analyse.py`): Cognitive reframing based on collected data
3. **PDF Generation** (`pdf.py`): Creates anonymized summary report
4. **Crisis Escalation** (`escalate.py`): Triggered on safety concerns at any stage

### State Coordination
- Uses `SessionState` to coordinate between pipeline stages
- State includes: name, age, reason, analysis, pdf_base64, escalation status
- Functions read/write state to enable seamless transitions

### Testing Strategy
- Unit tests use `StubLLM` for deterministic responses (see `tests/unit/conftest.py`)
- Integration tests verify full pipeline behavior
- Spanish/English language support tested throughout
- Crisis detection scenarios must be thoroughly tested

### Prompt Management
- Prompts are managed in Langfuse (v0.3)
- Access via `app.services.prompts.get_prompt(name, version)`
- Current prompts: collect, analyse, pdf, escalate

### Key Implementation Details
- **Async-first**: All assistant functions are async
- **Regex extraction**: Parse user data from natural language (see patterns in collect.py)
- **Multi-language**: Built-in Spanish/English support
- **Safety-first**: Crisis detection integrated at every stage
- **PDF encoding**: Generated PDFs are base64-encoded for API transmission

### Environment Configuration
Required environment variables:
```bash
GOOGLE_API_KEY      # For Gemini (being phased out) and Google Cloud Translation
OPENAI_API_KEY      # For OpenAI Assistants
LANGFUSE_HOST       # Prompt management
LANGFUSE_PUBLIC_KEY
LANGFUSE_SECRET_KEY
```

### Current Migration Status
The project is 60% migrated from Google ADK to OpenAI Assistants. The core assistant functions are complete with passing tests, but the conversational orchestrator and OpenAI Assistant deployment are pending.

## Development Guidelines

### Critical Operational Notes
- Critical: all python interpreter dependant commands should start with `uv run`