"""Happy path unit tests for the orchestrator assistant."""

import pytest

from app.assistants.orchestrator_assistant import OrchestratorAssistant
from app.assistants.state import Phase


@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test orchestrator initializes with correct state."""
    orchestrator = OrchestratorAssistant(use_stubs=True)

    assert orchestrator.current_phase == Phase.S0_START
    assert orchestrator.session_state.transcript == []
    assert orchestrator.tool_results == {}
    assert orchestrator.use_stubs is True


@pytest.mark.asyncio
async def test_initial_greeting():
    """Test orchestrator provides initial greeting."""
    orchestrator = OrchestratorAssistant(use_stubs=True)

    # Get initial action without user message
    action = await orchestrator.decide_next_action()

    assert action["action"] == "message"
    assert "Hola" in action["message"]
    assert orchestrator.current_phase == Phase.S0_START


@pytest.mark.asyncio
async def test_start_to_intake_transition():
    """Test transition from START to INTAKE phase."""
    orchestrator = OrchestratorAssistant(use_stubs=True)

    # User sends first message
    action = await orchestrator.decide_next_action("Hola, necesito ayuda")

    assert orchestrator.current_phase == Phase.S1_INTAKE
    assert action["action"] == "message"
    assert "nombre" in action["message"].lower()
    assert "edad" in action["message"].lower()


@pytest.mark.asyncio
async def test_intake_collect_context():
    """Test context collection during intake."""
    orchestrator = OrchestratorAssistant(use_stubs=True)
    orchestrator.current_phase = Phase.S1_INTAKE

    # Add user info to transcript
    orchestrator.session_state.add_user_message("Me llamo Ana, tengo 32 años y tengo ansiedad social")

    # Should trigger collect_context tool
    action = await orchestrator.decide_next_action()

    assert action["action"] == "tool_call"
    assert action["tool"] == "collect_context"

    # Simulate tool execution
    result = await orchestrator.execute_tool_with_stubs("collect_context", {})

    assert result["name"] == "Ana"
    assert result["age"] == 32
    assert "ansiedad" in result["reason"]


@pytest.mark.asyncio
async def test_crisis_check_safe_path():
    """Test crisis check with safe content."""
    orchestrator = OrchestratorAssistant(use_stubs=True)
    orchestrator.current_phase = Phase.S2_CRISIS_CHECK
    orchestrator.tool_results["collect_context"] = {
        "name": "Ana",
        "age": 32,
        "reason": "ansiedad social"
    }

    # Should proceed to analyst QA
    action = await orchestrator.decide_next_action()

    assert orchestrator.current_phase == Phase.S3_ANALYST_QA
    assert action["action"] == "tool_call"
    assert action["tool"] == "analyse_and_reframe"


@pytest.mark.asyncio
async def test_analysis_and_reframe():
    """Test analysis and reframing phase."""
    orchestrator = OrchestratorAssistant(use_stubs=True)
    orchestrator.current_phase = Phase.S3_ANALYST_QA
    orchestrator.tool_results["collect_context"] = {
        "name": "Ana",
        "age": 32,
        "reason": "ansiedad social"
    }

    # Trigger analysis
    action = await orchestrator.decide_next_action()
    assert action["action"] == "tool_call"
    assert action["tool"] == "analyse_and_reframe"

    # Execute analysis
    result = await orchestrator.execute_tool_with_stubs(
        "analyse_and_reframe",
        orchestrator.tool_results["collect_context"]
    )

    assert "Ana" in result["analysis"]
    assert len(result["distortions_identified"]) > 0
    assert len(result["reframes"]) > 0


@pytest.mark.asyncio
async def test_pdf_offer_accept():
    """Test PDF offer acceptance flow."""
    orchestrator = OrchestratorAssistant(use_stubs=True)
    orchestrator.current_phase = Phase.S5_PDF_OFFER
    orchestrator.tool_results = {
        "collect_context": {"name": "Ana", "age": 32, "reason": "ansiedad"},
        "analyse_and_reframe": {
            "analysis": "Test analysis",
            "distortions_identified": ["test"],
            "reframes": ["test reframe"]
        }
    }

    # User accepts PDF
    action = await orchestrator.decide_next_action("Sí, por favor")

    assert orchestrator.current_phase == Phase.S6_UPLOAD_PDF
    assert action["action"] == "tool_call"
    assert action["tool"] == "generate_pdf"


@pytest.mark.asyncio
async def test_pdf_generation_and_upload():
    """Test PDF generation and upload flow."""
    orchestrator = OrchestratorAssistant(use_stubs=True)
    orchestrator.current_phase = Phase.S6_UPLOAD_PDF
    orchestrator.tool_results = {
        "collect_context": {"name": "Ana", "age": 32, "reason": "ansiedad"},
        "analyse_and_reframe": {
            "analysis": "Test analysis",
            "distortions_identified": ["test"],
            "reframes": ["test reframe"]
        }
    }

    # Generate PDF
    pdf_result = await orchestrator.execute_tool_with_stubs(
        "generate_pdf",
        {
            "context": orchestrator.tool_results["collect_context"],
            "analysis": orchestrator.tool_results["analyse_and_reframe"]
        }
    )

    assert "pdf_base64" in pdf_result
    assert "filename" in pdf_result

    # Should trigger upload
    action = await orchestrator.decide_next_action()
    assert action["action"] == "tool_call"
    assert action["tool"] == "gcs_upload"


@pytest.mark.asyncio
async def test_complete_happy_path_flow():
    """Test complete happy path from start to finish."""
    orchestrator = OrchestratorAssistant(use_stubs=True)

    # Initial greeting
    action = await orchestrator.decide_next_action()
    assert action["action"] == "message"

    # User starts conversation
    action = await orchestrator.decide_next_action("Hola, necesito ayuda")
    assert orchestrator.current_phase == Phase.S1_INTAKE

    # User provides info
    orchestrator.session_state.add_user_message("Me llamo Ana, tengo 32 años, tengo ansiedad social")
    action = await orchestrator.decide_next_action()
    assert action["action"] == "tool_call"
    assert action["tool"] == "collect_context"

    # Execute context collection
    await orchestrator.execute_tool_with_stubs("collect_context", {})

    # Should move through crisis check to analysis
    action = await orchestrator.decide_next_action()
    assert orchestrator.current_phase == Phase.S3_ANALYST_QA

    # Execute analysis
    await orchestrator.execute_tool_with_stubs(
        "analyse_and_reframe",
        orchestrator.tool_results["collect_context"]
    )

    # Should present reframe and offer PDF
    action = await orchestrator.decide_next_action()
    assert orchestrator.current_phase == Phase.S5_PDF_OFFER
    assert "PDF" in action["message"]

    # Accept PDF
    action = await orchestrator.decide_next_action("Sí")
    assert action["tool"] == "generate_pdf"

    # Generate and upload
    await orchestrator.execute_tool_with_stubs("generate_pdf", action["arguments"])
    action = await orchestrator.decide_next_action()
    assert action["tool"] == "gcs_upload"

    await orchestrator.execute_tool_with_stubs("gcs_upload", action["arguments"])

    # Check that gcs_upload result is stored
    assert "gcs_upload" in orchestrator.tool_results

    # The orchestrator should now transition to DONE and provide download link
    action = await orchestrator.decide_next_action()
    assert action["action"] == "message"
    assert orchestrator.current_phase == Phase.S7_DONE
    assert "descargarlo" in action["message"] or "resumen" in action["message"]
